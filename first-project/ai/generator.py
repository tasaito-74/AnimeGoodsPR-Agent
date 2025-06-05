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
        """フォーマットパターンA用のプロンプト生成（全画像・画像サイズ・フォント指定）"""
        images_html = "\n".join([
            f"<img src='{url}' width='100%' style='max-width:600px; height:auto; display:block; margin:16px auto;'>"
            for url in data['images']
        ])
        return f"""
        以下の情報をもとに、アニメグッズのPR記事をHTML形式で作成してください。
        フォーマット:
        <h1 style=\"font-family:'Noto Sans JP', 'Meiryo', sans-serif;\">記事タイトル</h1>
        <p style=\"font-family:'Noto Sans JP', 'Meiryo', sans-serif;\">リード文（50文字程度）</p>
        <h2 style=\"font-family:'Noto Sans JP', 'Meiryo', sans-serif;\">見出し1</h2>
        <p style=\"font-family:'Noto Sans JP', 'Meiryo', sans-serif;\">本文テキスト</p>
        画像は本文の流れに合わせて適切な位置に、下記のstyle属性付きで挿入してください。
        <p style=\"font-family:'Noto Sans JP', 'Meiryo', sans-serif;\">まとめ・CTA</p>

        スクレイピングデータ:
        テキスト: {data['text']}
        画像HTML:
        {images_html}

        注意: 各テキスト要素にはWordPressで推奨される日本語フォント（例: 'Noto Sans JP', 'Meiryo', sans-serif）をstyle属性で指定し、画像はstyle属性でサイズ・中央寄せを指定してください。
        """

    def _format_pattern_b(self, data: Dict[str, List[str]]) -> str:
        """フォーマットパターンB用のプロンプト生成（全画像・画像サイズ・フォント指定）"""
        images_html = "\n".join([
            f"<img src='{url}' width='100%' style='max-width:600px; height:auto; display:block; margin:16px auto;'>"
            for url in data['images']
        ])
        return f"""
        以下の情報をもとに、アニメグッズのPR記事をHTML形式で作成してください。
        フォーマット:
        <h1 style=\"font-family:'Noto Sans JP', 'Meiryo', sans-serif;\">記事タイトル</h1>
        <h3 style=\"font-family:'Noto Sans JP', 'Meiryo', sans-serif;\">サブヘッド</h3>
        <p style=\"font-family:'Noto Sans JP', 'Meiryo', sans-serif;\">本文テキスト（段落分割）</p>
        画像は本文の流れに合わせて適切な位置に、下記のstyle属性付きで挿入してください。

        スクレイピングデータ:
        テキスト: {data['text']}
        画像HTML:
        {images_html}

        注意: 各テキスト要素にはWordPressで推奨される日本語フォント（例: 'Noto Sans JP', 'Meiryo', sans-serif）をstyle属性で指定し、画像はstyle属性でサイズ・中央寄せを指定してください。
        """

    def _format_pattern_c(self, data: Dict[str, List[str]]) -> str:
        """フォーマットパターンC用のプロンプト生成（全画像・画像サイズ・フォント指定）"""
        images_html = "\n".join([
            f"<img src='{url}' width='100%' style='max-width:600px; height:auto; display:block; margin:16px auto;'>"
            for url in data['images']
        ])
        return f"""
        以下の情報をもとに、アニメグッズのPR記事をHTML形式で作成してください。
        フォーマット:
        <h1 style=\"font-family:'Noto Sans JP', 'Meiryo', sans-serif;\">記事タイトル</h1>
        <h2 style=\"font-family:'Noto Sans JP', 'Meiryo', sans-serif;\">特徴</h2>
        <ul style=\"font-family:'Noto Sans JP', 'Meiryo', sans-serif;\"><li>特徴リスト</li></ul>
        <p style=\"font-family:'Noto Sans JP', 'Meiryo', sans-serif;\">本文テキスト</p>
        画像は本文の流れに合わせて適切な位置に、下記のstyle属性付きで挿入してください。
        <p style=\"font-family:'Noto Sans JP', 'Meiryo', sans-serif;\">まとめ・CTA</p>

        スクレイピングデータ:
        テキスト: {data['text']}
        画像HTML:
        {images_html}

        注意: 各テキスト要素にはWordPressで推奨される日本語フォント（例: 'Noto Sans JP', 'Meiryo', sans-serif）をstyle属性で指定し、画像はstyle属性でサイズ・中央寄せを指定してください。
        """

    def _format_pattern_d(self, data: Dict[str, List[str]]) -> str:
        """フォーマットパターンD用のプロンプト生成（全画像・画像サイズ・フォント指定）"""
        images_html = "\n".join([
            f"<img src='{url}' width='100%' style='max-width:600px; height:auto; display:block; margin:16px auto;'>"
            for url in data['images']
        ])
        return f"""
        以下の情報をもとに、アニメグッズのPR記事をHTML形式で作成してください。
        フォーマット:
        <h1 style=\"font-family:'Noto Sans JP', 'Meiryo', sans-serif;\">記事タイトル</h1>
        <h2 style=\"font-family:'Noto Sans JP', 'Meiryo', sans-serif;\">概要</h2>
        <p style=\"font-family:'Noto Sans JP', 'Meiryo', sans-serif;\">本文テキスト</p>
        <h2 style=\"font-family:'Noto Sans JP', 'Meiryo', sans-serif;\">おすすめポイント</h2>
        <ul style=\"font-family:'Noto Sans JP', 'Meiryo', sans-serif;\"><li>ポイントリスト</li></ul>
        画像は本文の流れに合わせて適切な位置に、下記のstyle属性付きで挿入してください。
        <p style=\"font-family:'Noto Sans JP', 'Meiryo', sans-serif;\">まとめ・CTA</p>

        スクレイピングデータ:
        テキスト: {data['text']}
        画像HTML:
        {images_html}

        注意: 各テキスト要素にはWordPressで推奨される日本語フォント（例: 'Noto Sans JP', 'Meiryo', sans-serif）をstyle属性で指定し、画像はstyle属性でサイズ・中央寄せを指定してください。
        """
