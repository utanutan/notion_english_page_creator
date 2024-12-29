# Notion 英単語解説ページ自動生成ツール

Notion のデータベースから単語リストを取得し、ChatGPT（GPT-4）を利用して英語学習用のページを自動生成するPythonツールです。

## 主な機能

- Notion データベースからの英単語取得
- ChatGPT による詳細な解説生成
- Notion ページの自動作成
- 単語の意味、語源、使用例、品詞の解説
- ページ作成状態の管理

## システム要件

### 環境変数
```
NOTION_TOKEN=your_notion_api_token
NOTION_DATABASE_ID=your_database_id
OPENAI_API_KEY=your_openai_api_key
```

### Notion データベース構造

データベースには以下のプロパティが必要です：

1. **単語 (テキスト)**
   - 解説対象の英単語
   - 例: "realm", "concept", "analysis"

2. **ページ作成 (チェックボックス)**
   - ページ作成状態の管理
   - `false`: 未作成
   - `true`: 作成済み

3. **作成日時 (日時)**
   - ページ作成日時の記録
   - 未作成の場合は空欄またはnull

## 処理フロー

1. **DB のクエリ**
   - 「ページ作成フラグ (checkbox)」が false のものをフィルタリングして取得

2. **ChatGPTへの問い合わせ**
   - 取得した単語をそれぞれ ChatGPT に問い合わせ
   - レスポンス内容を受け取る（マークダウン形式）

3. **Notion ページ作成**
   - タイトル: 単語名
   - 本文: ChatGPT レスポンスをそのまま格納
   - 作成後、レスポンスから作られた page_id を取得

4. **フラグ更新**
   - 「ページ作成フラグ」を true に更新
   - 「作成日時」に現在日時をセット

5. **ログ出力 / 終了**
   - 作成したページの一覧をロギング
   - スクリプト終了

## ChatGPT 問い合わせ仕様

### 使用モデル
- chatgpt4o（GPT-4 の利用を想定）

### プロンプトテンプレート
```
あなたは英語教師で、単語を英語学習者向けに解説する役割です。
単語や熟語の**意味**と**使い方**、**語源**、品詞を簡単に説明してください。
単語: {word}
```

### レスポンス例
```markdown
### 1. **realm**（名詞）

**意味**：領域、分野、範囲

**語源**：古フランス語の「reaume」（王国）に由来します。現在では物理的な「王国」だけでなく、抽象的な「領域」や「分野」にも使われます。

**例文**："In the realm of science fiction, artificial intelligence often plays a central role."
（SFの領域では、人工知能がしばしば中心的な役割を果たす。）

**解説**：この単語は学術的な文脈でよく使用され、特定の分野や領域を示す際に用いられます。
```

## Notion ページ作成仕様

### ページタイトル
- DB の「単語」プロパティをそのまま使用

### ページ本文
- ChatGPT からのレスポンスをマークダウン形式で格納
- 必要に応じて HTML 変換を検討

### フラグ更新
- ページ作成フラグを true に更新
- 作成日時に現在日時を記録
