from pydantic import BaseModel, HttpUrl
from typing import Optional

class ArticleRequest(BaseModel):
    """記事生成リクエストのモデル"""
    url: str
    format_type: str  # "popup", "news", "event"
    category: str     # "POP UP", "NEWS", "EVENT"
    
    class Config:
        schema_extra = {
            "example": {
                "url": "https://example.com/anime-popup-store",
                "format_type": "popup",
                "category": "POP UP"
            }
        } 