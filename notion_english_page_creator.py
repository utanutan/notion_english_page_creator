import os
import logging
from datetime import datetime
from typing import Dict, List

import openai
from dotenv import load_dotenv
from notion_client import Client

# ロギングの設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 環境変数の読み込み
load_dotenv()
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# APIクライアントの初期化
notion = Client(auth=NOTION_TOKEN)
openai.api_key = OPENAI_API_KEY

def get_unprocessed_words() -> List[Dict]:
    """
    ページ作成フラグがfalseの単語を取得
    """
    try:
        response = notion.databases.query(
            database_id=NOTION_DATABASE_ID,
            filter={
                "property": "ページ作成",
                "checkbox": {
                    "equals": False
                }
            }
        )
        return response["results"]
    except Exception as e:
        logger.error(f"Notionからの単語取得に失敗: {e}")
        return []

def generate_explanation_from_chatgpt(word: str) -> str:
    """
    ChatGPTを使用して単語の解説を生成
    """
    prompt = f"""あなたは英語教師で、単語を英語学習者向けに解説する役割です。
単語や熟語の**意味**と**使い方**、**語源**、品詞を簡単に説明してください。

単語: {word}"""

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "あなたは英語教師です。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"ChatGPTでの解説生成に失敗: {e}")
        return ""

def create_notion_page(word: str, explanation: str) -> bool:
    """
    Notionページを作成し、フラグを更新
    """
    try:
        # ページの作成
        new_page = notion.pages.create(
            parent={"database_id": NOTION_DATABASE_ID},
            properties={
                "単語": {
                    "title": [
                        {
                            "text": {
                                "content": word
                            }
                        }
                    ]
                },
                "ページ作成": {
                    "checkbox": True
                },
                "作成日時": {
                    "date": {
                        "start": datetime.utcnow().isoformat()
                    }
                }
            },
            children=[
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": explanation
                                }
                            }
                        ]
                    }
                }
            ]
        )
        logger.info(f"ページを作成しました: {word}")
        return True
    except Exception as e:
        logger.error(f"Notionページの作成に失敗: {e}")
        return False

def main():
    """
    メイン処理
    """
    logger.info("英単語解説ページの生成を開始します")

    # 未処理の単語を取得
    words = get_unprocessed_words()
    if not words:
        logger.info("新規作成が必要な単語はありません")
        return

    # 各単語に対して処理を実行
    for word_data in words:
        try:
            # 単語を取得
            word = word_data["properties"]["単語"]["title"][0]["text"]["content"]
            
            # ChatGPTで解説を生成
            logger.info(f"解説を生成中: {word}")
            explanation = generate_explanation_from_chatgpt(word)
            if not explanation:
                continue

            # Notionページを作成
            if create_notion_page(word, explanation):
                logger.info(f"ページを作成しました: {word}")
            else:
                logger.error(f"ページの作成に失敗: {word}")

        except Exception as e:
            logger.error(f"処理中にエラーが発生: {e}")
            continue

    logger.info("すべての処理が完了しました")

if __name__ == "__main__":
    main()
