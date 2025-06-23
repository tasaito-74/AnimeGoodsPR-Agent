# アニメ記事生成支援サービス

URLを入力するだけで、AIが自動でアニメ記事を生成しGoogle Docsに保存するサービスです。

## 機能

- **自動スクレイピング**: 公式URLから画像・テキストを自動取得
- **AI記事生成**: OpenAI GPT-4を使用した自動記事生成
- **Google Docs連携**: 生成された記事をGoogle Docsに自動保存
- **フォーマット選択**: ポップアップストア、ニュース、イベントのカテゴリ対応
- **モダンUI**: レスポンシブデザインの美しいインターフェース

## セットアップ

### 1. 依存関係のインストール

```bash
pip3 install -r requirements.txt
```

### 2. Playwrightのセットアップ

```bash
playwright install chromium
```

### 3. 環境変数の設定

`.env.example`を`.env`にコピーして、必要なAPIキーを設定してください：

```bash
cp .env.example .env
```

#### 必要な環境変数

- `OPENAI_API_KEY`: OpenAI APIキー
- `GOOGLE_CLIENT_ID`: Google OAuth クライアントID
- `GOOGLE_CLIENT_SECRET`: Google OAuth クライアントシークレット
- `APP_SECRET_KEY`: アプリケーションの秘密鍵（任意の文字列）

### 4. Google API設定

1. [Google Cloud Console](https://console.cloud.google.com/)でプロジェクトを作成
2. Google Drive APIとGoogle Docs APIを有効化
3. OAuth 2.0クライアントIDを作成
4. 認証情報を`.env`ファイルに設定

## 使用方法

### アプリケーションの起動

```bash
python app.py
```

または

```bash
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

### Webインターフェース

1. ブラウザで `http://localhost:8000` にアクセス
2. 公式URLを入力
3. カテゴリとフォーマットを選択
4. 「記事を生成」ボタンをクリック
5. 生成されたGoogle Docsのリンクを確認

## プロジェクト構造

```
AI-BASE/
├── app.py                 # メインアプリケーション
├── requirements.txt       # Python依存関係
├── .env.example          # 環境変数テンプレート
├── README.md             # このファイル
├── models/               # データモデル
│   ├── __init__.py
│   ├── article_request.py
│   ├── article_response.py
│   └── scraped_data.py
├── services/             # ビジネスロジック
│   ├── __init__.py
│   ├── scraper.py        # Webスクレイピング
│   ├── ai_generator.py   # AI記事生成
│   └── google_docs.py    # Google Docs連携
├── templates/            # HTMLテンプレート
│   └── index.html
├── static/               # 静的ファイル
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── script.js
└── format-for-popup.md   # ポップアップストアフォーマット
```

## API エンドポイント

- `GET /`: メインページ
- `POST /generate-article`: 記事生成API
- `GET /health`: ヘルスチェック

## 技術スタック

- **バックエンド**: FastAPI (Python)
- **フロントエンド**: HTML, CSS, JavaScript
- **スクレイピング**: BeautifulSoup4, Playwright
- **AI生成**: OpenAI GPT-4
- **Google連携**: Google Drive API, Google Docs API

## トラブルシューティング

### よくある問題

1. **OpenAI APIエラー**
   - APIキーが正しく設定されているか確認
   - クレジット残高を確認

2. **Google API認証エラー**
   - OAuth認証情報が正しく設定されているか確認
   - 必要なAPIが有効化されているか確認

3. **スクレイピングエラー**
   - URLが正しく入力されているか確認
   - 対象サイトがアクセス可能か確認

### ログの確認

アプリケーションのログを確認して、詳細なエラー情報を取得できます。

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。

## 貢献

プルリクエストやイシューの報告を歓迎します。 