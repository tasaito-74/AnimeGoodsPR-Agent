import requests
import os
from typing import Optional, List
import mimetypes
from pathlib import Path
from bs4 import BeautifulSoup

class WordPressPoster:
    def __init__(self):
        base = os.getenv("WORDPRESS_API_URL", "").rstrip("/")
        self.base_url = base
        self.auth = (
            os.getenv("WORDPRESS_USERNAME"),
            os.getenv("WORDPRESS_PASSWORD")
        )

    async def upload_image(self, image_path: str) -> Optional[str]:
        """画像をWordPressにアップロードし、アップロードされた画像のURLを返す"""
        try:
            # 画像のMIMEタイプを取得
            mime_type, _ = mimetypes.guess_type(image_path)
            if not mime_type:
                mime_type = 'image/jpeg'

            # 画像ファイルを読み込む
            with open(image_path, 'rb') as img_file:
                files = {
                    'file': (os.path.basename(image_path), img_file, mime_type)
                }
                
                # WordPress REST APIを使用して画像をアップロード
                response = requests.post(
                    f"{self.base_url}/media",
                    files=files,
                    auth=self.auth
                )
                response.raise_for_status()
                
                # アップロードされた画像のURLを返す
                return response.json().get('source_url')
        except Exception as e:
            print(f"画像のアップロードに失敗しました: {e}")
            return None

    async def replace_local_images_with_wordpress(self, html_content: str) -> str:
        """HTML内のローカル画像パスをWordPressの画像URLに置き換える"""
        soup = BeautifulSoup(html_content, 'html.parser')
        local_images = soup.find_all('img', src=lambda x: x and x.startswith('/static/images/'))
        
        for img in local_images:
            local_path = img['src'].lstrip('/')
            if os.path.exists(local_path):
                # WordPressに画像をアップロード
                wp_image_url = await self.upload_image(local_path)
                if wp_image_url:
                    # 画像URLを置き換え
                    img['src'] = wp_image_url
                    # ローカル画像を削除
                    try:
                        os.remove(local_path)
                    except Exception as e:
                        print(f"ローカル画像の削除に失敗しました: {e}")
        
        return str(soup)

    async def post_article(self, html_content: str, title: str = "自動生成記事", status: str = "draft") -> Optional[int]:
        """WordPressに記事を投稿"""
        try:
            # 画像をWordPressにアップロードし、HTMLを更新
            updated_html = await self.replace_local_images_with_wordpress(html_content)
            
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json"
            }

            data = {
                "title": title,
                "content": updated_html,
                "status": status
            }

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
        try:
            # 画像をWordPressにアップロードし、HTMLを更新
            updated_html = await self.replace_local_images_with_wordpress(html_content)
            
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json"
            }

            data = {
                "content": updated_html
            }

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
