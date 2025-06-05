import os
import requests
from typing import Dict, List

class ArticleGenerator:
    def __init__(self):
        self.api_key = os.getenv("DEEPSEEK_API_KEY")
        self.api_url = "https://api.deepseek.com/v1/chat/completions"
        self.formats = {
            "A": self._format_pattern_a,
            "B": self._format_pattern_b,
            "C": self._format_pattern_c,
            "D": self._format_pattern_d
        }

    async def generate_article(self, scraped_data: Dict[str, List[str]], format_pattern: str = "A") -> str:
        """スクレイピングデータから記事を生成"""
        format_func = self.formats.get(format_pattern, self._format_pattern_a)
        prompt = format_func(scraped_data)
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": "You are a professional copywriter for anime goods."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7
        }
        
        response = requests.post(self.api_url, json=data, headers=headers)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]

    def _format_pattern_a(self, data: Dict[str, List[str]]) -> str:
        """フォーマットパターンA用のプロンプト生成"""
        return f"""
        以下の情報をもとに、アニメグッズのPR記事をHTML形式で作成してください。
        フォーマット:
        <h1>記事タイトル</h1>
        <p>リード文（50文字程度）</p>
        <h2>見出し1</h2>
        <p>本文テキスト</p>
        <img src='画像URL'>
        <p>まとめ・CTA</p>

        スクレイピングデータ:
        テキスト: {data['text']}
        画像URL: {data['images'][0] if data['images'] else ''}
        """

    def _format_pattern_b(self, data: Dict[str, List[str]]) -> str:
        """フォーマットパターンB用のプロンプト生成"""
        return f"""
        以下の情報をもとに、アニメグッズのPR記事をHTML形式で作成してください。
        フォーマット:
        <h1>記事タイトル</h1>
        <h3>サブヘッド</h3>
        <p>本文テキスト（段落分割）</p>
        <img src='画像URL'>

        スクレイピングデータ:
        テキスト: {data['text']}
        画像URL: {data['images'][0] if data['images'] else ''}
        """

    def _format_pattern_c(self, data: Dict[str, List[str]]) -> str:
        """フォーマットパターンC用のプロンプト生成"""
        # 同様に実装
        pass

    def _format_pattern_d(self, data: Dict[str, List[str]]) -> str:
        """フォーマットパターンD用のプロンプト生成"""
        # 同様に実装
        pass
