from bs4 import BeautifulSoup
import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from jinja2 import Template
import os

@dataclass
class ArticleContent:
    title: str
    lead: str
    goods: List[Dict[str, str]]
    content_paragraphs: List[str]
    images: List[str]
    conclusion: str

class HTMLProcessor:
    def __init__(self, template_path: Optional[str] = None):
        """
        HTMLProcessorの初期化
        Args:
            template_path: HTMLテンプレートのパス。Noneの場合はデフォルトテンプレートを使用
        """
        if template_path and os.path.exists(template_path):
            self.template_path = template_path
        else:
            self.template_path = os.path.join('templates', 'article_template.html')
        
        with open(self.template_path, 'r', encoding='utf-8') as f:
            self.template = Template(f.read())

    def set_template(self, template_path: str) -> None:
        """
        テンプレートを動的に変更
        Args:
            template_path: 新しいHTMLテンプレートのパス
        """
        if not os.path.exists(template_path):
            raise FileNotFoundError(f"テンプレートファイルが見つかりません: {template_path}")
        
        self.template_path = template_path
        with open(template_path, 'r', encoding='utf-8') as f:
            self.template = Template(f.read())

    def extract_content(self, html_content: str) -> ArticleContent:
        """AIが生成したHTMLから必要なコンテンツを抽出"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # タイトルを抽出
        title = self._extract_title(soup)
        
        # リード文を抽出
        lead = self._extract_lead(soup)
        
        # 商品情報を抽出
        goods = self._extract_goods(soup)
        
        # 本文を段落ごとに抽出
        content_paragraphs = self._extract_paragraphs(soup)
        
        # 結論を抽出
        conclusion = self._extract_conclusion(soup)
        
        return ArticleContent(
            title=title,
            lead=lead,
            goods=goods,
            content_paragraphs=content_paragraphs,
            images=[],  # 画像は別途設定
            conclusion=conclusion
        )

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """タイトルを抽出"""
        title_tag = soup.find('h1')
        if not title_tag:
            raise ValueError("タイトルが見つかりません")
        return title_tag.get_text(strip=True)

    def _extract_lead(self, soup: BeautifulSoup) -> str:
        """リード文を抽出"""
        # 最初の段落をリード文として扱う
        first_p = soup.find('p')
        if not first_p:
            raise ValueError("リード文が見つかりません")
        return first_p.get_text(strip=True)

    def _extract_goods(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """商品情報を抽出"""
        goods = []
        goods_list = soup.find('ul')
        if goods_list:
            for li in goods_list.find_all('li'):
                text = li.get_text(strip=True)
                # 商品情報をパース
                name_match = re.search(r'商品名：(.+?)(?=　価格：|$)', text)
                price_match = re.search(r'価格：(.+?)(?=　発売日：|$)', text)
                date_match = re.search(r'発売日：(.+?)$', text)
                
                goods.append({
                    'name': name_match.group(1) if name_match else '',
                    'price': price_match.group(1) if price_match else '',
                    'date': date_match.group(1) if date_match else ''
                })
        return goods

    def _extract_paragraphs(self, soup: BeautifulSoup) -> List[str]:
        """本文を段落ごとに抽出"""
        paragraphs = []
        # 商品情報の後、結論の前の段落を本文として扱う
        content_section = soup.find('h2', string=re.compile('詳細・おすすめポイント'))
        if content_section:
            current = content_section.find_next('p')
            while current and not current.find_previous('h2') == content_section:
                if current.name == 'p':
                    paragraphs.append(str(current))
                current = current.find_next()
        return paragraphs

    def _extract_conclusion(self, soup: BeautifulSoup) -> str:
        """結論を抽出"""
        # 最後の段落を結論として扱う
        last_p = soup.find_all('p')[-1]
        if not last_p:
            raise ValueError("結論が見つかりません")
        return last_p.get_text(strip=True)

    def validate_html(self, html_content: str) -> Tuple[bool, List[str]]:
        """HTMLの構造を検証"""
        errors = []
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 必須要素のチェック
        required_elements = {
            'h1': 'タイトル',
            'h2': 'セクションタイトル',
            'p': '段落',
            'ul': '商品リスト'
        }
        
        for tag, name in required_elements.items():
            if not soup.find(tag):
                errors.append(f"{name}が見つかりません")
        
        # 商品情報の形式チェック
        goods_list = soup.find('ul')
        if goods_list:
            for li in goods_list.find_all('li'):
                if not re.search(r'商品名：.+価格：.+発売日：', li.get_text()):
                    errors.append("商品情報の形式が正しくありません")
        
        return len(errors) == 0, errors

    def format_article(self, content: ArticleContent) -> str:
        """テンプレートを使用して記事をフォーマット"""
        return self.template.render(
            title=content.title,
            lead=content.lead,
            goods=content.goods,
            content_paragraphs=content.content_paragraphs,
            images=content.images,
            conclusion=content.conclusion
        ) 