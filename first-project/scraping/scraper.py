from bs4 import BeautifulSoup
import requests
from typing import Dict

def scrape_content(url: str) -> Dict[str, str]:
    """BeautifulSoupを使用してURLからコンテンツをスクレイピング"""
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 不要な要素を削除
        for element in soup(['script', 'style', 'nav', 'footer']):
            element.decompose()
        
        # テキストコンテンツを取得
        text = ' '.join(soup.stripped_strings)
        
        # 画像URLを収集
        images = [img['src'] for img in soup.find_all('img') if img.get('src')]
        
        return {
            'text': text,
            'images': images
        }
    except Exception as e:
        raise Exception(f"スクレイピングに失敗しました: {str(e)}")
