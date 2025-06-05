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
        images_html = "\n".join([
            f"<img src='{url}' width='100%' style='max-width:600px; height:auto; display:block; margin:16px auto;'>"
            for url in data['images']
        ])
        goods_html = ""
        if 'goods' in data and data['goods']:
            goods_html = "<ul style=\"font-family:'Noto Sans JP', 'Meiryo', sans-serif;\">"
            for item in data['goods']:
                goods_html += (
                    "<li>"
                    f"<b>商品名：</b>{item.get('name', '')}　"
                    f"<b>価格：</b>{item.get('price', '')}　"
                    f"<b>発売日：</b>{item.get('date', '')}"
                    "</li>"
                )
            goods_html += "</ul>"
        else:
            goods_html = (
                "<ul style=\"font-family:'Noto Sans JP', 'Meiryo', sans-serif;\">"
                "<li><b>商品名：</b>　<b>価格：</b>　<b>発売日：</b></li>"
                "</ul>"
            )
        return f"""
以下の情報をもとに、アニメグッズのPR記事をHTML形式で作成してください。

【重要な指示】
- 出力はHTML本文のみで、冒頭に'''htmlや\"html\"などの前置きやコードブロック記号は絶対に付けないこと。
- グッズ名・価格・発売日などは必ずul/liでリスト化し、ラベル部分は<b>太字</b>にすること。
- スクレイピングデータに存在しない情報（価格・日程など）は絶対に推測せず、空欄または記載しないこと。
- タイトルや区分ごとにh2/h3や<b>太字</b>、色分け（style属性）で装飾し、本文も適宜<b>太字</b>や色を使って強調すること。

フォーマット例:
<h1 style="font-family:'Noto Sans JP', 'Meiryo', sans-serif; background:#e91e63; color:#fff; padding:12px; border-radius:8px;">記事タイトル</h1>
<p style="font-family:'Noto Sans JP', 'Meiryo', sans-serif;">リード文（50文字程度）</p>
<h2 style="font-family:'Noto Sans JP', 'Meiryo', sans-serif; color:#5eead4;">商品情報</h2>
{goods_html}
<h2 style="font-family:'Noto Sans JP', 'Meiryo', sans-serif; color:#f093fb;">詳細・おすすめポイント</h2>
<p style="font-family:'Noto Sans JP', 'Meiryo', sans-serif;">本文テキスト。重要な語句やポイントは<b>太字</b>や<span style='color:#f093fb;'>色</span>で強調。</p>
{images_html}
<p style="font-family:'Noto Sans JP', 'Meiryo', sans-serif; font-weight:bold;">まとめ・CTA</p>

スクレイピングデータ:
テキスト: {data['text']}
画像HTML:
{images_html}
グッズ情報: {data.get('goods', '（本文中からグッズ名・価格・発売日を抽出してリスト化してください。無い場合は空欄でOK）')}
"""
