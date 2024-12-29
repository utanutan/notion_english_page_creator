import os
import logging
from datetime import datetime
from typing import Dict, List

from dotenv import load_dotenv
from notion_client import Client
from openai import OpenAI

# ロギングの設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 環境変数の読み込み
load_dotenv()
NOTION_TOKEN = os.getenv("NOTION_API_KEY")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# APIクライアントの初期化
notion = Client(auth=NOTION_TOKEN)
client = OpenAI(api_key=OPENAI_API_KEY)

def get_unprocessed_words() -> List[Dict]:
    """
    未処理の単語を取得
    """
    try:
        response = notion.databases.query(
            database_id=NOTION_DATABASE_ID,
            filter={
                "and": [
                    {
                        "property": "ページ作成",
                        "checkbox": {
                            "equals": False
                        }
                    }
                ]
            }
        )
        
        words = []
        for page in response["results"]:
            title = page["properties"]["単語"]["title"]
            if title:
                words.append({
                    "word": title[0]["text"]["content"],
                    "page_id": page["id"]
                })
        return words
    except Exception as e:
        logger.error(f"Notionからの単語取得に失敗: {str(e)}")
        return []

def generate_explanation_from_chatgpt(word: str) -> str:
    """
    ChatGPTを使用して単語の解説を生成
    """
    # 単語を小文字に変換し、前後の空白を削除
    word = word.lower().strip()
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "あなたは英語を教える優秀な教師です。"},
                {"role": "user", "content": f"""以下の形式で「{word}」を解説してください。
各項目は必ず「項目名:」で始めてください：

品詞: 単語の品詞を記述
意味: 簡潔な日本語の意味
語源: 語源の説明（50文字以内）
例文: 英文と日本語訳のペア
関連語: 関連する単語や表現の説明（100文字以内）"""}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"ChatGPTでの解説生成に失敗: {str(e)}")
        return None

def delete_notion_page(page_id: str) -> bool:
    """
    Notionページを削除
    """
    try:
        notion.pages.update(
            page_id=page_id,
            archived=True
        )
        logger.info(f"ページを削除しました: {page_id}")
        return True
    except Exception as e:
        logger.error(f"ページの削除に失敗: {str(e)}")
        return False

def create_or_update_notion_page(word: str, explanation: str, page_id: str = None) -> bool:
    """
    Notionページを作成または更新し、フラグを更新
    """
    try:
        # デバッグ用にChatGPTの出力を表示
        logger.info(f"ChatGPTの出力:\n{explanation}")
        
        # 解説を各セクションに分割
        sections = {
            '品詞': '形容詞',  # デフォルト値を設定
            '意味': '',
            '語源': '',
            '例文': '',
            '関連語': ''
        }
        
        current_section = None
        current_content = []
        
        for line in explanation.split('\n'):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            # セクションの開始を検出
            for section in sections.keys():
                if line.startswith(f"{section}:"):
                    current_section = section
                    content = line.replace(f"{section}:", "").strip()
                    if content:
                        current_content = [content]
                    else:
                        current_content = []
                    break
            else:
                # セクションの開始でない場合は、現在のセクションの内容として追加
                if current_section and line:
                    current_content.append(line)
            
            # 現在のセクションの内容を更新
            if current_section:
                sections[current_section] = ' '.join(current_content)

        # デバッグ用にパース結果を表示
        logger.info("パース結果:")
        for key, value in sections.items():
            logger.info(f"{key}: {value}")

        page_properties = {
            "単語": {"title": [{"text": {"content": word.lower()}}]},
            "ページ作成": {"checkbox": True}
        }

        if page_id:
            # 既存のページを削除して新規作成
            if not delete_notion_page(page_id):
                return False
            
        # 新規ページを作成
        response = notion.pages.create(
            parent={"database_id": NOTION_DATABASE_ID},
            properties=page_properties,
            children=[
                {
                    "object": "block",
                    "type": "heading_1",
                    "heading_1": {
                        "rich_text": [{"type": "text", "text": {"content": f"{word} ({sections['品詞']})"}}]
                    }
                },
                {
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [{"type": "text", "text": {"content": "意味"}}]
                    }
                },
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"type": "text", "text": {"content": sections['意味']}}]
                    }
                },
                {
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [{"type": "text", "text": {"content": "語源"}}]
                    }
                },
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"type": "text", "text": {"content": sections['語源']}}]
                    }
                },
                {
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [{"type": "text", "text": {"content": "例文"}}]
                    }
                },
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"type": "text", "text": {"content": sections['例文']}}]
                    }
                },
                {
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [{"type": "text", "text": {"content": "関連語"}}]
                    }
                },
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"type": "text", "text": {"content": sections['関連語']}}]
                    }
                }
            ]
        )

        logger.info(f"ページを作成しました: {word}")
        return True
    except Exception as e:
        logger.error(f"ページの作成に失敗: {str(e)}")
        return False

def main():
    """
    メイン処理
    """
    logger.info("英単語解説ページの生成を開始します")
    
    # 未処理の単語を取得
    words = get_unprocessed_words()
    
    for word_data in words:
        word = word_data["word"]
        page_id = word_data["page_id"]
        
        logger.info(f"解説を生成中: {word}")
        explanation = generate_explanation_from_chatgpt(word)
        
        if explanation:
            create_or_update_notion_page(word, explanation, page_id)
    
    logger.info("すべての処理が完了しました")

if __name__ == "__main__":
    main()
