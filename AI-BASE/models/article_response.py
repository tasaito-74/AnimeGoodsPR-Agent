from pydantic import BaseModel
from typing import Optional

class ArticleResponse(BaseModel):
    """記事生成レスポンスのモデル"""
    success: bool
    docs_url: Optional[str] = None
    message: str
    error: Optional[str] = None
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "docs_url": "https://docs.google.com/document/d/example",
                "message": "記事が正常に生成されました",
                "error": None
            }
        } 