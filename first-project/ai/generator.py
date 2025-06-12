import os
import requests
from typing import Dict, List, Optional, Any
import re
from utils.html_processor import HTMLProcessor, ArticleContent
from utils.format_types import ArticleInfo, StoreType, IllustrationType, StoreInfo, NoveltyInfo
from utils.template_generator import TemplateGenerator
import logging
from scraping.scraper import Scraper

logger = logging.getLogger(__name__)

class ArticleGenerator:
    def __init__(self, template_path: Optional[str] = None):
        """
        ArticleGeneratorの初期化
        Args:
            template_path: HTMLテンプレートのパス。Noneの場合はデフォルトテンプレートを使用
        """
        self.api_key = os.getenv("DEEPSEEK_API_KEY")
        self.api_url = "https://api.deepseek.com/v1/chat/completions"
        self.formats = {
            "A": self._format_pattern_a,
        }
        self.html_processor = HTMLProcessor(template_path)
        self.template_generator = TemplateGenerator()
        self.scraper = Scraper()

    def set_template(self, template_path: str) -> None:
        """
        テンプレートを動的に変更
        Args:
            template_path: 新しいHTMLテンプレートのパス
        """
        self.html_processor.set_template(template_path)

    def generate_article(self, url: str) -> str:
        """URLから記事を生成する"""
        try:
            # 1. スクレイピング
            logger.info(f"Scraping content from: {url}")
            scraped_data = self.scraper.scrape(url)
            logger.debug(f"Scraped data received: {scraped_data}")
            
            # スクレイピングデータの検証
            if not scraped_data:
                raise ValueError("スクレイピングデータが取得できませんでした")
            
            if not isinstance(scraped_data, dict):
                raise ValueError(f"スクレイピングデータが辞書型ではありません: {type(scraped_data)}")
            
            if 'text' not in scraped_data:
                raise ValueError("スクレイピングデータに'text'キーが含まれていません")
            
            if not scraped_data['text']:
                raise ValueError("スクレイピングデータの'text'が空です")

            # 2. 文章生成
            logger.info("Generating article with AI")
            article_info = self._create_article_info(scraped_data)
            logger.debug(f"Created article info: {article_info}")
            article_content = self.template_generator.generate_article(article_info)
            logger.debug(f"Generated article content: {article_content}")

            # 3. HTML整形
            logger.info("Formatting article with HTML template")
            formatted_article = self._format_pattern_a({
                'title': [article_info.title],
                'meta_description': [article_content.meta_description],
                'lead': [article_content.lead],
                'goods_section': [article_content.goods_section],
                'novelty_section': [article_content.novelty_section],
                'summary_section': [article_content.summary_section],
                'footer': [article_content.footer]
            })
            logger.debug(f"Formatted article length: {len(formatted_article)}")

            return formatted_article

        except Exception as e:
            logger.error(f"AI generation failed: {str(e)}")
            logger.error(f"Error type: {type(e)}")
            logger.error(f"Error details: {str(e)}")
            raise

    def _create_article_info(self, scraped_data: Dict[str, Any]) -> ArticleInfo:
        """スクレイピングデータからArticleInfoを作成"""
        try:
            # テキストから情報を抽出
            text = scraped_data.get('text', '')
            title = scraped_data.get('title', '')
            description = scraped_data.get('description', '')
            
            # 日付情報の抽出
            date_pattern = r'(\d{1,2}月\d{1,2}日（[^）]+）)～(\d{1,2}月\d{1,2}日（[^）]+）)'
            date_matches = re.findall(date_pattern, text)
            start_date = date_matches[0][0] if date_matches else ''
            end_date = date_matches[0][1] if date_matches else ''
            
            # 店舗情報の抽出
            store_pattern = r'開催場所\s+([^（]+)（([^）]+)）'
            store_matches = re.findall(store_pattern, text)
            store_name = store_matches[0][0].strip() if store_matches else ''
            location = store_matches[0][1].strip() if store_matches else ''
            
            # グッズ情報の抽出
            goods_pattern = r'([^（]+)（全(\d+)種[^）]*）\s+(\d+)円'
            goods_matches = re.findall(goods_pattern, text)
            goods_info = []
            for name, types, price in goods_matches:
                goods_info.append({
                    'name': name.strip(),
                    'types': int(types),
                    'price': int(price)
                })
            
            # ノベルティ情報の抽出
            novelty_pattern = r'([^（]+)（全(\d+)種[^）]*）\s+(\d+)円'
            novelty_matches = re.findall(novelty_pattern, text)
            novelty_name = novelty_matches[0][0].strip() if novelty_matches else ''
            novelty_total_types = int(novelty_matches[0][1]) if novelty_matches else 0
            novelty_price = int(novelty_matches[0][2]) if novelty_matches else 0
            
            # キャラクター名の抽出（重複を除去し、1文字の名前を除外）
            character_names = list(set([
                name for name in scraped_data.get('character_names', [])
                if len(name) > 1 and not any(x in name for x in ['開催', 'グッズ', '詳細'])
            ]))
            
            # タイトルからアニメ名を抽出
            anime_name = title.split('×')[0].strip() if '×' in title else title
            
            # メーカー名を抽出
            maker_name = 'サンリオ' if 'サンリオ' in title else 'メーカー名'
            
            # 作者名を抽出（可能な場合）
            author = '作者名'  # 実際のデータから抽出する必要がある場合は修正
            
            # StoreInfoの作成
            store_info = StoreInfo(
                name=store_name,
                type=StoreType.NORMAL,
                illustration_type=IllustrationType.ORIGINAL,
                start_date=start_date,
                end_date=end_date,
                location=location,
                google_maps_url='https://goo.gl/maps/...',  # 実際のURLを設定
                official_url=scraped_data.get('source_url', ''),
                contact_url=scraped_data.get('source_url', ''),
                twitter_url=None,
                category_url=None
            )
            
            # NoveltyInfoの作成
            novelty_info = NoveltyInfo(
                price=novelty_price,
                name=novelty_name,
                total_types=novelty_total_types,
                is_random=True,  # ランダム配布の場合はTrue
                is_original=True  # オリジナルイラストの場合はTrue
            )
            
            # ArticleInfoの作成
            return ArticleInfo(
                title=title,
                author=author,
                anime_name=anime_name,
                maker_name=maker_name,
                store_info=store_info,
                novelty_info=novelty_info,
                character_names=character_names
            )
            
        except Exception as e:
            logger.error(f"Error creating ArticleInfo: {str(e)}")
            raise

    def _determine_store_type(self, store_name: str) -> StoreType:
        """店舗名から店舗タイプを判定する"""
        store_name = store_name.lower()
        if 'a3' in store_name:
            return StoreType.A3
        elif 'tsutaya' in store_name:
            return StoreType.TSUTAYA
        return StoreType.NORMAL

    def _determine_illustration_type(self, scraped_data: dict) -> IllustrationType:
        """スクレイピングデータからイラストタイプを判定する"""
        if scraped_data.get('novelty_is_original', False):
            return IllustrationType.ORIGINAL
        return IllustrationType.ANIME

    def _format_pattern_a(self, data: Dict[str, List[str]]) -> str:
        """記事をフォーマットAのパターンで整形"""
        # 記事の本文を構築
        article_text = f"""
{data['title'][0]}

{data['meta_description'][0]}

{data['lead'][0]}

{data['goods_section'][0]}

{data['novelty_section'][0]}

{data['summary_section'][0]}

{data['footer'][0]}
"""
        return article_text
