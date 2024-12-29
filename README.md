# Notion 英単語解説ページ自動生成ツール

Notion のデータベースから単語リストを取得し、ChatGPT（GPT-4o）を利用して英語学習用のページを自動生成するPythonツールです。

## 主な機能

- Notion データベースからの英単語取得
- ChatGPT による詳細な解説生成
  - 品詞
  - 意味（簡潔な日本語訳）
  - 語源（50文字以内の簡潔な説明）
  - 例文（英文と日本語訳のペア）
  - 関連語（100文字以内の説明）
- Notion ページの自動作成
  - 見出しと段落を使用した構造化されたページレイアウト
  - 既存ページの自動削除と再作成
- ページ作成状態の管理

## セットアップ

1. 必要なパッケージをインストール：
```bash
pip install -r requirements.txt
```

2. 環境変数の設定：
`.env`ファイルを作成し、以下の情報を設定：
```
NOTION_TOKEN=your_notion_api_token
NOTION_DATABASE_ID=your_notion_database_id
OPENAI_API_KEY=your_openai_api_key
```

## 使用方法

### ローカルでの実行

```bash
python notion_english_page_creator.py
```

### GitHub Actionsでの自動実行

このツールはGitHub Actionsを使用して自動実行することができます。

1. GitHubリポジトリの Settings > Secrets and variables > Actions で以下の環境変数を設定：
   - `NOTION_TOKEN`: Notion APIトークン
   - `NOTION_DATABASE_ID`: NotionデータベースのID
   - `OPENAI_API_KEY`: OpenAI APIキー

2. 自動実行スケジュール：
   - 毎日午前10時（日本時間）に自動実行
   - GitHubリポジトリの "Actions" タブから手動実行も可能

## 必要な環境

- Python 3.10.7
- 必要なパッケージ：
  - python-dotenv==1.0.0
  - requests==2.31.0
  - openai==1.6.1
  - notion-client==2.2.1

## Notionデータベースの設定

以下のプロパティを持つデータベースを作成：
- 単語（タイトル）: 解説する英単語
- ページ作成（チェックボックス）: 解説ページが作成されたかどうか
- 作成日時（日付）: 解説ページが作成された日付

## システム要件

### 必要なパッケージ
```
python-dotenv==1.0.0
requests==2.31.0
openai==1.6.1
notion-client==2.2.1
```

### 環境変数
```
NOTION_TOKEN=your_notion_api_token
NOTION_DATABASE_ID=your_database_id
OPENAI_API_KEY=your_openai_api_key
```

## 処理フロー

1. **データベースのクエリ**
   - 「ページ作成フラグ」が false の単語を取得

2. **ChatGPTによる解説生成**
   - 取得した単語ごとに以下の形式で解説を生成：
     - 品詞: 単語の品詞
     - 意味: 簡潔な日本語訳
     - 語源: 語源の説明（50文字以内）
     - 例文: 英文と日本語訳のペア
     - 関連語: 関連する単語や表現（100文字以内）

3. **Notion ページの作成**
   - 既存のページがある場合は削除
   - 新規ページを作成：
     - 見出し1: 単語と品詞
     - 見出し2: 各セクション（意味、語源、例文、関連語）
     - 段落: 各セクションの内容
   - ページ作成フラグを true に更新
