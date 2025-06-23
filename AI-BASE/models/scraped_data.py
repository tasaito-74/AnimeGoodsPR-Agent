from pydantic import BaseModel
from typing import List, Optional

class ScrapedData(BaseModel):
    """スクレイピングされたデータのモデル"""
    url: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    images: List[str] = []
    text_content: Optional[str] = None
    metadata: dict = {}
    
    class Config:
        schema_extra = {
            "example": {
                "url": "https://example.com/anime-popup-store",
                "title": "アニメ「XXX」ポップアップストア開催",
                "description": "人気アニメのポップアップストアが開催されます",
                "images": ["https://example.com/image1.jpg", "https://example.com/image2.jpg"],
                "text_content": "詳細な記事内容...",
                "metadata": {"author": "メーカー名", "date": "2025-01-01"}
            }
        } 