from bs4 import BeautifulSoup
import requests
from typing import Dict, List
import os
from urllib.parse import urljoin, urlparse
import hashlib
from pathlib import Path
import re
from utils.image_processor import resize_image
import logging

logger = logging.getLogger(__name__)

class Scraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def is_relevant_image(self, img_tag) -> bool:
        """画像が記事本文に関連するものかどうかを判定"""
        # 関連記事や広告などの画像を除外
        excluded_classes = [
            'related', 'recommend', 'advertisement', 'banner',
            'sidebar', 'footer', 'header', 'nav', 'menu',
            'thumbnail', 'icon', 'logo', 'social'
        ]
        
        # 除外すべきクラス名やIDを含む画像をスキップ
        if img_tag.get('class'):
            for cls in img_tag['class']:
                if any(excluded in cls.lower() for excluded in excluded_classes):
                    return False
        
        if img_tag.get('id'):
            if any(excluded in img_tag['id'].lower() for excluded in excluded_classes):
                return False
        
        # 画像サイズが小さすぎるもの（アイコンなど）を除外
        if img_tag.get('width') and int(img_tag['width']) < 200:
            return False
        if img_tag.get('height') and int(img_tag['height']) < 200:
            return False
        
        # alt属性が空または一般的すぎるものを除外
        alt_text = img_tag.get('alt', '').lower()
        if not alt_text or any(generic in alt_text for generic in ['icon', 'logo', 'banner', 'ad']):
            return False
        
        return True

    def get_highest_quality_image_url(self, url: str) -> str:
        """可能な限り高品質な画像URLを取得"""
        # 一般的な画像サイズパラメータを削除
        url = re.sub(r'[?&](?:w|width|h|height|size|quality|q)=\d+', '', url)
        
        # 画像URLのパターンに基づいて高品質版のURLを生成
        if 'wp-content/uploads' in url:
            # WordPressの場合、サイズ指定を削除
            url = re.sub(r'-\d+x\d+\.', '.', url)
        elif 'pixiv' in url:
            # Pixivの場合、master版を取得
            url = url.replace('_master1200', '_master')
        elif 'twitter' in url:
            # Twitterの場合、オリジナルサイズを取得
            url = url.replace('&name=small', '&name=large')
            url = url.replace('&name=medium', '&name=large')
        
        return url

    def download_image(self, url: str, save_dir: str = "static/images") -> str:
        """画像をダウンロードして保存し、保存先のパスを返す"""
        try:
            # 保存先ディレクトリの作成
            os.makedirs(save_dir, exist_ok=True)
            
            # 高品質な画像URLを取得
            url = self.get_highest_quality_image_url(url)
            
            # URLからファイル名を生成
            parsed_url = urlparse(url)
            file_extension = os.path.splitext(parsed_url.path)[1]
            if not file_extension:
                file_extension = '.jpg'
            
            # URLのハッシュをファイル名として使用
            file_hash = hashlib.md5(url.encode()).hexdigest()
            filename = f"{file_hash}{file_extension}"
            save_path = os.path.join(save_dir, filename)
            
            # 画像が既に存在する場合はスキップ
            if os.path.exists(save_path):
                return f"/static/images/{filename}"
            
            # 画像をダウンロード
            response = requests.get(url, stream=True, headers=self.headers)
            response.raise_for_status()
            
            # 画像を保存
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # 画像をリサイズ
            resized_path = resize_image(save_path)
            
            return f"/static/images/{os.path.basename(resized_path)}"
        except Exception as e:
            logger.error(f"画像のダウンロードに失敗しました: {url} - {str(e)}")
            return url

    def get_absolute_url(self, base_url: str, relative_url: str) -> str:
        """相対URLを絶対URLに変換"""
        return urljoin(base_url, relative_url)

    def _extract_store_info(self, soup: BeautifulSoup, text: str) -> Dict[str, str]:
        """店舗情報を抽出"""
        store_info = {
            'name': '',
            'type': 'normal',
            'illustration_type': 'original',
            'start_date': '',
            'end_date': '',
            'location': ''
        }

        # 店舗名の抽出
        # 例: 「XXX ポップアップストア」「XXX 期間限定ショップ」などのパターン
        store_patterns = [
            r'([^「」]+?)\s*(?:ポップアップストア|期間限定ショップ|ショップ)',
            r'([^「」]+?)\s*(?:A3|TSUTAYA)\s*(?:ポップアップストア|期間限定ショップ|ショップ)'
        ]
        
        for pattern in store_patterns:
            match = re.search(pattern, text)
            if match:
                store_info['name'] = match.group(1).strip()
                # 店舗タイプの判定
                if 'A3' in match.group(0):
                    store_info['type'] = 'a3'
                elif 'TSUTAYA' in match.group(0):
                    store_info['type'] = 'tsutaya'
                break

        # 日付情報の抽出
        date_pattern = r'(\d{4})年(\d{1,2})月(\d{1,2})日'
        date_matches = list(re.finditer(date_pattern, text))
        if len(date_matches) >= 2:
            store_info['start_date'] = date_matches[0].group(0)
            store_info['end_date'] = date_matches[1].group(0)

        # 場所の抽出
        location_patterns = [
            r'場所[：:]\s*([^\n]+)',
            r'会場[：:]\s*([^\n]+)',
            r'([^「」]+?)\s*(?:店|支店|ショップ)'
        ]
        
        for pattern in location_patterns:
            match = re.search(pattern, text)
            if match:
                store_info['location'] = match.group(1).strip()
                break

        return store_info

    def _extract_novelty_info(self, soup: BeautifulSoup, text: str) -> Dict[str, any]:
        """ノベルティ情報を抽出"""
        novelty_info = {
            'name': '',
            'price': 0,
            'total_types': 0,
            'is_random': False,
            'is_original': False
        }

        # ノベルティ名の抽出
        novelty_patterns = [
            r'特典[：:]\s*([^\n]+)',
            r'ノベルティ[：:]\s*([^\n]+)',
            r'お買い上げ特典[：:]\s*([^\n]+)'
        ]
        
        for pattern in novelty_patterns:
            match = re.search(pattern, text)
            if match:
                novelty_info['name'] = match.group(1).strip()
                break

        # 価格の抽出
        price_pattern = r'(\d{1,3}(?:,\d{3})*)円'
        price_match = re.search(price_pattern, text)
        if price_match:
            price_str = price_match.group(1).replace(',', '')
            novelty_info['price'] = int(price_str)

        # 種類数の抽出
        types_pattern = r'全(\d+)種'
        types_match = re.search(types_pattern, text)
        if types_match:
            novelty_info['total_types'] = int(types_match.group(1))

        # ランダム配布の判定
        random_keywords = ['ランダム', 'おまかせ', 'お楽しみ']
        novelty_info['is_random'] = any(keyword in text for keyword in random_keywords)

        # 描き下ろしの判定
        original_keywords = ['描き下ろし', '書き下ろし', 'オリジナル']
        novelty_info['is_original'] = any(keyword in text for keyword in original_keywords)

        return novelty_info

    def _extract_character_info(self, soup: BeautifulSoup, text: str) -> List[str]:
        """キャラクター情報を抽出"""
        characters = []
        
        # キャラクター名の抽出パターン
        character_patterns = [
            r'([^「」]+?)(?:ちゃん|くん|さん|様)',
            r'「([^「」]+?)」'
        ]
        
        for pattern in character_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                char_name = match.group(1).strip()
                if char_name and len(char_name) > 1:  # 1文字の名前は除外
                    characters.append(char_name)

        return list(set(characters))  # 重複を除去

    def scrape(self, url: str) -> Dict[str, str]:
        """BeautifulSoupを使用してURLからコンテンツをスクレイピング"""
        try:
            logger.info(f"Scraping content from: {url}")
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            logger.debug(f"HTML content length: {len(response.text)}")
            
            # 不要な要素を削除
            for element in soup(['script', 'style', 'nav', 'footer', 'aside', 'header']):
                element.decompose()
            
            # メインコンテンツを特定（より詳細なログを追加）
            main_content = soup.find('main')
            if main_content:
                logger.debug("Found main content using 'main' tag")
            else:
                main_content = soup.find('article')
                if main_content:
                    logger.debug("Found main content using 'article' tag")
                else:
                    main_content = soup.find('div', class_=re.compile(r'content|main|article', re.I))
                    if main_content:
                        logger.debug(f"Found main content using div with class: {main_content.get('class', [])}")
                    else:
                        logger.warning("No main content found using standard selectors")
                        # 代替のコンテンツ検索
                        main_content = soup.find('div', id=re.compile(r'content|main|article', re.I))
                        if main_content:
                            logger.debug(f"Found main content using div with id: {main_content.get('id', '')}")
            
            text = ""
            images = []
            
            if main_content:
                # メインコンテンツ内のテキストを取得
                text = ' '.join(main_content.stripped_strings)
                logger.debug(f"Main content text length: {len(text)}")
                logger.debug(f"First 100 characters of text: {text[:100]}")
                
                # メインコンテンツ内の画像のみを収集
                for img in main_content.find_all('img'):
                    if img.get('src') and self.is_relevant_image(img):
                        absolute_url = self.get_absolute_url(url, img['src'])
                        saved_path = self.download_image(absolute_url)
                        images.append(saved_path)
            else:
                logger.warning("Main content not found, using entire page")
                # メインコンテンツが見つからない場合は全体から取得
                text = ' '.join(soup.stripped_strings)
                logger.debug(f"Full page text length: {len(text)}")
                logger.debug(f"First 100 characters of text: {text[:100]}")
                
                # 画像の収集
                for img in soup.find_all('img'):
                    if img.get('src') and self.is_relevant_image(img):
                        absolute_url = self.get_absolute_url(url, img['src'])
                        saved_path = self.download_image(absolute_url)
                        images.append(saved_path)
            
            if not text:
                logger.warning("No text content found")
                text = "テキストが見つかりませんでした"  # デフォルトテキスト
            
            # タイトルを取得
            title = soup.find('title')
            title_text = title.text.strip() if title else ""
            logger.debug(f"Found title: {title_text}")

            # メタディスクリプションを取得
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            description = meta_desc.get('content', '') if meta_desc else ""
            logger.debug(f"Found description: {description}")

            # 各種情報を抽出
            store_info = self._extract_store_info(soup, text)
            novelty_info = self._extract_novelty_info(soup, text)
            characters = self._extract_character_info(soup, text)

            result = {
                'text': text,
                'images': images,
                'source_url': url,
                'title': title_text,
                'description': description,
                'store_name': store_info['name'],
                'store_type': store_info['type'],
                'illustration_type': store_info['illustration_type'],
                'start_date': store_info['start_date'],
                'end_date': store_info['end_date'],
                'location': store_info['location'],
                'novelty_name': novelty_info['name'],
                'novelty_price': novelty_info['price'],
                'novelty_total_types': novelty_info['total_types'],
                'novelty_is_random': novelty_info['is_random'],
                'novelty_is_original': novelty_info['is_original'],
                'character_names': characters
            }

            # 結果の検証
            if not isinstance(result, dict):
                raise ValueError(f"Result is not a dictionary: {type(result)}")
            
            if 'text' not in result:
                raise ValueError("'text' key is missing from result")
            
            if not result['text']:
                raise ValueError("'text' value is empty")

            logger.debug(f"Scraped data keys: {list(result.keys())}")
            logger.debug(f"Text length in result: {len(result['text'])}")
            logger.debug(f"Result content: {result}")  # 結果の内容を出力
            return result

        except requests.RequestException as e:
            logger.error(f"Network error during scraping: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during scraping: {str(e)}")
            logger.error(f"Error type: {type(e)}")
            logger.error(f"Error details: {str(e)}")
            raise
