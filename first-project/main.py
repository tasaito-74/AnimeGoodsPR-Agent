from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import os
from dotenv import load_dotenv
from scraping.scraper import scrape_content
from ai.generator import ArticleGenerator
from wordpress.poster import WordPressPoster
import logging
from pathlib import Path

load_dotenv()

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="AnimeGoodsPR_Agent")

# 静的ファイルとテンプレートの設定
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

article_generator = ArticleGenerator()
wordpress_poster = WordPressPoster()

class ArticleRequest(BaseModel):
    url: str
    format_pattern: str = "A"

@app.post("/generate-article")
async def generate_article(request: ArticleRequest):
    """
    公式URLから記事を生成しWordPressに投稿する
    """
    try:
        # 1. URLからコンテンツをスクレイピング
        scraped_data = scrape_content(request.url)
        
        # 2. AIで記事生成
        article_html = generate_ai_article(scraped_data, request.format_pattern)
        
        # 3. WordPressに投稿
        post_id = post_to_wordpress(article_html)
        
        return {
            "status": "success",
            "article_id": post_id,
            "message": "Article successfully generated and posted"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/health-check")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}

def scrape_content(url: str) -> dict:
    """URLからテキストと画像をスクレイピング"""
    try:
        logger.info(f"Scraping content from: {url}")
        from scraping.scraper import scrape_content as _scrape_content
        return _scrape_content(url)
    except Exception as e:
        logger.error(f"Scraping failed: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"Failed to scrape content from URL: {str(e)}"
        )

async def generate_ai_article(scraped_data: dict, format_pattern: str) -> str:
    """AIを使用して記事を生成"""
    try:
        logger.info("Generating article with AI")
        return await article_generator.generate_article(scraped_data, format_pattern)
    except Exception as e:
        logger.error(f"AI generation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate article: {str(e)}"
        )

async def post_to_wordpress(article_html: str) -> int:
    """WordPressに記事を投稿"""
    try:
        logger.info("Posting to WordPress")
        post_id = await wordpress_poster.post_article(article_html)
        if not post_id:
            raise ValueError("Failed to get post ID from WordPress")
        logger.info(f"Successfully posted to WordPress. Post ID: {post_id}")
        return post_id
    except Exception as e:
        logger.error(f"WordPress posting failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to post to WordPress: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
