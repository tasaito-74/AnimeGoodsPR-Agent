import os
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv
import uvicorn
from services.scraper import WebScraper
from services.ai_generator import AIGenerator
from services.google_docs import GoogleDocsService
from models.article_request import ArticleRequest
from models.article_response import ArticleResponse

# 環境変数を読み込み
load_dotenv()

app = FastAPI(title="アニメ記事生成支援サービス", version="1.0.0")

# 静的ファイルとテンプレートの設定
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# サービスの初期化
scraper = WebScraper()
ai_generator = AIGenerator()
google_docs = GoogleDocsService()

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """メインページを表示"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/generate-article")
async def generate_article(
    url: str = Form(...),
    format_type: str = Form(...)
):
    """記事生成エンドポイント"""
    try:
        # リクエストの作成
        article_request = ArticleRequest(
            url=url,
            format_type=format_type,
            category="POP UP"  # デフォルトでPOP UP
        )
        
        # 1. スクレイピング
        scraped_data = await scraper.scrape_url(article_request.url)
        
        # 2. AI生成
        generated_content = await ai_generator.generate_article(
            scraped_data, 
            article_request.format_type,
            article_request.category
        )
        
        # 3. Google Docsに保存
        docs_url = await google_docs.create_document(generated_content)
        
        # レスポンスの作成
        response = ArticleResponse(
            success=True,
            docs_url=docs_url,
            message="記事が正常に生成されました"
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """ヘルスチェックエンドポイント"""
    return {"status": "healthy", "message": "サービスは正常に動作しています"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 