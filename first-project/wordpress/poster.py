import requests
import os
from typing import Optional

class WordPressPoster:
    def __init__(self):
        self.base_url = os.getenv("WORDPRESS_API_URL")
        self.auth = (
            os.getenv("WORDPRESS_USERNAME"),
            os.getenv("WORDPRESS_PASSWORD")
        )

    async def post_article(self, html_content: str, title: str = "自動生成記事", status: str = "draft") -> Optional[int]:
        """WordPressに記事を投稿"""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        data = {
            "title": title,
            "content": html_content,
            "status": status
        }

        try:
            response = requests.post(
                f"{self.base_url}/posts",
                json=data,
                headers=headers,
                auth=self.auth
            )
            response.raise_for_status()
            return response.json().get("id")
        except Exception as e:
            print(f"WordPress投稿エラー: {e}")
            return None

    async def update_article(self, post_id: int, html_content: str) -> bool:
        """既存記事を更新"""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        data = {
            "content": html_content
        }

        try:
            response = requests.post(
                f"{self.base_url}/posts/{post_id}",
                json=data,
                headers=headers,
                auth=self.auth
            )
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"WordPress更新エラー: {e}")
            return False
