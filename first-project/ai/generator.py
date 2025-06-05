import os
import requests
from typing import Dict, List

class ArticleGenerator:
    def __init__(self):
        self.api_key = os.getenv("DEEPSEEK_API_KEY")
        self.api_url = "https://api.deepseek.com/v1/chat/completions"
        self.formats = {
            "A": self._format_pattern_a,
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
        """フォーマットパターンA用のプロンプト生成（全画像・画像サイズ・フォント指定・タイトル強調・価格リスト）"""
        images_html = "\n".join([
            f"<img src='{url}' width='100%' style='max-width:600px; height:auto; display:block; margin:16px auto;'>"
            for url in data['images']
        ])
        # グッズリストHTML生成（goodsがあれば）
        goods_html = ""
        if 'goods' in data and data['goods']:
            goods_html = "<ul style=\"font-family:'Noto Sans JP', 'Meiryo', sans-serif;\">"
            for item in data['goods']:
                goods_html += f"<li>{item.get('name', '')}：{item.get('price', '')}</li>"
            goods_html += "</ul>"
        return f"""
        以下の情報をもとに、アニメグッズのPR記事をHTML形式で作成してください。
        フォーマット:
        <h1 style=\"font-family:'Noto Sans JP', 'Meiryo', sans-serif; background:#e91e63; color:#fff; padding:12px; border-radius:8px;\">記事タイトル</h1>
        <p style=\"font-family:'Noto Sans JP', 'Meiryo', sans-serif;\">リード文（50文字程度）</p>
        <h2 style=\"font-family:'Noto Sans JP', 'Meiryo', sans-serif;\">見出し1</h2>
        <p style=\"font-family:'Noto Sans JP', 'Meiryo', sans-serif;\">本文テキスト</p>
        グッズごとの価格リストを以下のように挿入してください。
        {goods_html if goods_html else '<ul style="font-family:\'Noto Sans JP\', \'Meiryo\', sans-serif;"> <li>グッズ名：価格</li> ... </ul>'}
        画像は本文の流れに合わせて適切な位置に、下記のstyle属性付きで挿入してください。
        <p style=\"font-family:'Noto Sans JP', 'Meiryo', sans-serif;\">まとめ・CTA</p>

        スクレイピングデータ:
        テキスト: {data['text']}
        画像HTML:
        {images_html}
        グッズ情報: {data.get('goods', '（本文中からグッズ名と価格を抽出してリスト化してください）')}

        注意: タイトルはピンク色の塗りつぶし＋白文字で強調し、グッズごとの価格リストをul/liで表示してください。各テキスト要素にはWordPressで推奨される日本語フォント（例: 'Noto Sans JP', 'Meiryo', sans-serif）をstyle属性で指定し、画像はstyle属性でサイズ・中央寄せを指定してください。
        """
