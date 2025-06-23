import asyncio
import requests
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from models.scraped_data import ScrapedData
import re
from typing import List, Optional, Dict, Any
import json

class WebScraper:
    """Webスクレイピングサービス（Google検索機能付き）"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    async def scrape_url(self, url: str) -> ScrapedData:
        """URLからコンテンツをスクレイピング（情報補完機能付き）"""
        try:
            print(f"スクレイピング開始: {url}")
            
            # まず静的スクレイピングを試行
            scraped_data = await self._static_scrape(url)
            print(f"静的スクレイピング完了: {len(scraped_data.images)}枚の画像を取得")
            
            # 画像が少ない場合は動的スクレイピングを試行
            if len(scraped_data.images) < 3:
                print("画像が少ないため動的スクレイピングを実行...")
                dynamic_data = await self._dynamic_scrape(url)
                if dynamic_data.images:
                    scraped_data.images.extend(dynamic_data.images)
                    scraped_data.images = list(set(scraped_data.images))  # 重複除去
                    print(f"動的スクレイピング完了: 合計{len(scraped_data.images)}枚の画像")
            
            # 作品タイプを判別
            content_type = self._determine_content_type(scraped_data)
            scraped_data.metadata['content_type'] = content_type
            print(f"作品タイプ判別: {content_type}")
            
            # 不足情報をGoogle検索で補完
            enhanced_data = await self._enhance_with_google_search(scraped_data)
            
            # 画像URLをログ出力
            print(f"最終的に取得した画像: {len(enhanced_data.images)}枚")
            for i, img_url in enumerate(enhanced_data.images[:5]):  # 最初の5枚をログ出力
                print(f"  画像{i+1}: {img_url}")
            
            return enhanced_data
            
        except Exception as e:
            print(f"スクレイピングエラー: {e}")
            return ScrapedData()
    
    async def _static_scrape(self, url: str) -> ScrapedData:
        """静的スクレイピング（BeautifulSoup使用）"""
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # タイトルの取得
            title = self._extract_title(soup)
            
            # 説明の取得
            description = self._extract_description(soup)
            
            # 画像の取得
            images = self._extract_images(soup, url)
            
            # テキストコンテンツの取得
            text_content = self._extract_text_content(soup)
            
            # メタデータの取得
            metadata = self._extract_metadata(soup, url)
            
            # ベースURLをメタデータに追加
            from urllib.parse import urlparse
            parsed_url = urlparse(url)
            metadata['base_url'] = f"{parsed_url.scheme}://{parsed_url.netloc}"
            metadata['source_url'] = url
            
            return ScrapedData(
                url=url,
                title=title or metadata.get('page_title', ''),
                description=description or metadata.get('meta_description', ''),
                text_content=metadata.get('full_content', text_content or ''),
                images=images,
                metadata=metadata
            )
            
        except Exception as e:
            print(f"静的スクレイピングエラー: {e}")
            return ScrapedData()
    
    async def _dynamic_scrape(self, url: str) -> ScrapedData:
        """動的スクレイピング（Playwright使用）"""
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                
                await page.goto(url, wait_until='networkidle')
                
                # ページの内容を取得
                content = await page.content()
                soup = BeautifulSoup(content, 'html.parser')
                
                # 画像の取得
                images = self._extract_images(soup, url)
                
                await browser.close()
                
                return ScrapedData(images=images)
                
        except Exception as e:
            print(f"動的スクレイピングエラー: {e}")
            return ScrapedData()
    
    def _extract_title(self, soup: BeautifulSoup) -> Optional[str]:
        """タイトルの抽出"""
        # 優先順位: h1 > title > og:title
        h1 = soup.find('h1')
        if h1:
            return h1.get_text().strip()
        
        title_tag = soup.find('title')
        if title_tag:
            return title_tag.get_text().strip()
        
        og_title = soup.find('meta', property='og:title')
        if og_title:
            return og_title.get('content', '').strip()
        
        return None
    
    def _extract_description(self, soup: BeautifulSoup) -> Optional[str]:
        """説明の抽出"""
        # 優先順位: og:description > meta description > 最初のpタグ
        og_desc = soup.find('meta', property='og:description')
        if og_desc:
            return og_desc.get('content', '').strip()
        
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc:
            return meta_desc.get('content', '').strip()
        
        first_p = soup.find('p')
        if first_p:
            return first_p.get_text().strip()[:200] + "..."
        
        return None
    
    def _extract_images(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """画像URLの抽出（強化版）- 元サイトでの位置と重要度を考慮"""
        images = []
        seen_urls = set()
        
        # 画像を重要度とソースごとに分類
        main_content_images = []
        article_images = []
        general_images = []
        meta_images = []
        
        # メインコンテンツエリアを特定
        main_content_selectors = [
            'main',
            'article', 
            '.content',
            '.main-content',
            '.article-content',
            '.post-content',
            '.entry-content',
            '#content',
            '#main',
            '#article',
            '.container .content',
            '.wrapper .content'
        ]
        
        main_content = None
        for selector in main_content_selectors:
            try:
                main_content = soup.select_one(selector)
                if main_content:
                    print(f"メインコンテンツエリアを発見: {selector}")
                    break
            except:
                continue
        
        # メインコンテンツエリア内の画像を優先的に取得
        if main_content:
            for img in main_content.find_all('img'):
                src = self._extract_image_src(img, base_url)
                if src and self._is_valid_image_url(src) and src not in seen_urls:
                    seen_urls.add(src)
                    main_content_images.append(src)
                    print(f"メインコンテンツ画像: {src}")
        
        # 記事・商品関連の特定エリアの画像
        article_selectors = [
            '.goods', '.product', '.item', '.merchandise',
            '.gallery', '.photos', '.images',
            '.character', '.anime', '.collaboration',
            '.popup', '.store', '.campaign',
            '.novelty', '.special', '.limited',
            '.featured', '.highlight'
        ]
        
        for selector in article_selectors:
            try:
                areas = soup.select(selector)
                for area in areas:
                    for img in area.find_all('img'):
                        src = self._extract_image_src(img, base_url)
                        if src and self._is_valid_image_url(src) and src not in seen_urls:
                            seen_urls.add(src)
                            article_images.append(src)
                            print(f"記事関連画像: {src}")
            except:
                continue
        
        # 一般的なimgタグから画像を取得（メインコンテンツ以外）
        for img in soup.find_all('img'):
            # メインコンテンツ内の画像は既に処理済みなのでスキップ
            if main_content and img in main_content.find_all('img'):
                continue
            
            src = self._extract_image_src(img, base_url)
            if src and self._is_valid_image_url(src) and src not in seen_urls:
                # 画像の親要素から重要度を判定
                importance = self._calculate_image_importance(img)
                if importance > 0:  # 重要度が正の場合のみ追加
                    seen_urls.add(src)
                    general_images.append((src, importance))
        
        # メタデータから画像を取得
        meta_selectors = [
            ('meta[property="og:image"]', 'content'),
            ('meta[name="twitter:image"]', 'content'),
            ('meta[name="twitter:image:src"]', 'content')
        ]
        
        for selector, attr in meta_selectors:
            try:
                meta_tag = soup.select_one(selector)
                if meta_tag:
                    src = meta_tag.get(attr, '')
                    if src and self._is_valid_image_url(src) and src not in seen_urls:
                        seen_urls.add(src)
                        meta_images.append(src)
                        print(f"メタ画像: {src}")
            except:
                continue
        
        # 背景画像も取得（CSS style属性から）
        bg_images = []
        for element in soup.find_all(attrs={'style': True}):
            style = element.get('style', '')
            if 'background-image' in style:
                import re
                bg_matches = re.findall(r'background-image:\s*url\(["\']?([^"\']+)["\']?\)', style)
                for bg_url in bg_matches:
                    if self._is_valid_image_url(bg_url) and bg_url not in seen_urls:
                        seen_urls.add(bg_url)
                        bg_images.append(bg_url)
        
        # 画像を重要度順に統合
        final_images = []
        
        # 1. メインコンテンツの画像（最重要）
        final_images.extend(main_content_images[:5])  # 最大5枚
        
        # 2. 記事関連エリアの画像
        final_images.extend(article_images[:3])  # 最大3枚
        
        # 3. 一般画像（重要度でソート）
        general_images.sort(key=lambda x: x[1], reverse=True)
        final_images.extend([img[0] for img in general_images[:3]])  # 最大3枚
        
        # 4. メタ画像（補完用）
        if len(final_images) < 3:
            final_images.extend(meta_images[:2])
        
        # 5. 背景画像（最後の手段）
        if len(final_images) < 2:
            final_images.extend(bg_images[:1])
        
        # 最終的な品質フィルタリング
        quality_images = []
        for img_url in final_images:
            if img_url not in [qi[0] for qi in quality_images]:  # 重複除去
                quality_score = self._calculate_image_quality_score(img_url)
                if quality_score > 0:  # スコアが正の場合のみ
                    quality_images.append((img_url, quality_score))
        
        # 品質スコアでソートして返す
        quality_images.sort(key=lambda x: x[1], reverse=True)
        result = [img[0] for img in quality_images[:10]]  # 最大10枚まで
        
        print(f"最終選択画像: {len(result)}枚")
        for i, img_url in enumerate(result):
            print(f"  選択画像{i+1}: {img_url}")
        
        return result

    def _extract_image_src(self, img_tag, base_url: str) -> Optional[str]:
        """imgタグから画像URLを抽出"""
        # 様々な属性から画像URLを取得
        src_candidates = [
            img_tag.get('src'),
            img_tag.get('data-src'),
            img_tag.get('data-original'),
            img_tag.get('data-lazy-src'),
            img_tag.get('data-lazy'),
            img_tag.get('data-srcset'),
            img_tag.get('srcset')
        ]
        
        for src in src_candidates:
            if src:
                # srcsetの場合は最初のURLを取得
                if ',' in src:
                    src = src.split(',')[0].strip().split(' ')[0]
                
                # 相対URLを絶対URLに変換
                src = self._resolve_url(src, base_url)
                
                if src:
                    return src
        
        return None
    
    def _resolve_url(self, url: str, base_url: str) -> Optional[str]:
        """相対URLを絶対URLに変換"""
        if not url:
            return None
        
        # すでに絶対URLの場合
        if url.startswith('http'):
            return url
        
        # プロトコル相対URL
        if url.startswith('//'):
            from urllib.parse import urlparse
            parsed_base = urlparse(base_url)
            return f"{parsed_base.scheme}:{url}"
        
        # 相対URL
        if url.startswith('/'):
            from urllib.parse import urljoin
            return urljoin(base_url, url)
        else:
            from urllib.parse import urljoin
            return urljoin(base_url, url)
    
    def _calculate_image_importance(self, img_tag) -> int:
        """画像の重要度を計算（DOM位置、クラス、親要素から判定）"""
        importance = 0
        
        # alt属性の内容
        alt_text = img_tag.get('alt', '').lower()
        if alt_text:
            important_alt_keywords = [
                'goods', 'product', 'item', 'merchandise',
                'character', 'anime', 'collaboration', 'collab',
                'popup', 'store', 'campaign', 'event',
                'novelty', 'special', 'limited', 'exclusive',
                'new', 'latest', 'featured', 'main'
            ]
            
            for keyword in important_alt_keywords:
                if keyword in alt_text:
                    importance += 3
                    break
        
        # クラス名から判定
        class_names = ' '.join(img_tag.get('class', [])).lower()
        if class_names:
            important_class_keywords = [
                'main', 'hero', 'featured', 'primary',
                'goods', 'product', 'item', 'gallery',
                'character', 'anime', 'artwork',
                'campaign', 'special', 'highlight'
            ]
            
            unimportant_class_keywords = [
                'thumb', 'thumbnail', 'small', 'mini',
                'icon', 'logo', 'brand', 'header', 'footer',
                'nav', 'menu', 'ad', 'banner', 'sidebar'
            ]
            
            for keyword in important_class_keywords:
                if keyword in class_names:
                    importance += 2
            
            for keyword in unimportant_class_keywords:
                if keyword in class_names:
                    importance -= 3
        
        # 親要素から判定
        parent = img_tag.parent
        if parent:
            parent_class = ' '.join(parent.get('class', [])).lower()
            parent_id = parent.get('id', '').lower()
            
            important_parent_patterns = [
                'gallery', 'photos', 'images', 'slideshow',
                'goods', 'products', 'items', 'merchandise',
                'main', 'content', 'article', 'featured',
                'hero', 'banner', 'highlight'
            ]
            
            for pattern in important_parent_patterns:
                if pattern in parent_class or pattern in parent_id:
                    importance += 2
                    break
        
        # 画像サイズ（width, height属性）
        width = img_tag.get('width')
        height = img_tag.get('height')
        
        if width and height:
            try:
                w, h = int(width), int(height)
                if w >= 400 or h >= 300:
                    importance += 2
                elif w >= 200 or h >= 150:
                    importance += 1
                elif w < 100 and h < 100:
                    importance -= 2
            except ValueError:
                pass
        
        return importance

    def _is_valid_image_url(self, url: str) -> bool:
        """画像URLの有効性をチェック（緩和版）"""
        if not url or len(url) < 10:
            return False
        
        url_lower = url.lower()
        
        # 重要：除外パターンを大幅に緩和
        exclude_patterns = [
            'data:image',  # base64画像
            'placeholder',
            'loading',
            'spinner',
            '.svg',  # SVGは除外
            '1x1',   # トラッキングピクセル
            'pixel',  # トラッキングピクセル
            'spacer',  # スペーサー画像
            'blank',  # 空白画像
            'transparent',  # 透明画像
            'favicon',  # ファビコン
            'noimage',  # 画像なし
            'analytics',  # アナリティクス
            'tracking',  # トラッキング
        ]
        
        # URLパスから除外パターンをチェック（緩和）
        if any(pattern in url_lower for pattern in exclude_patterns):
            print(f"除外対象画像: {url}")
            return False
        
        # ファイル名から除外パターンをチェック（緩和）
        filename = url_lower.split('/')[-1].split('?')[0]  # クエリパラメータを除去
        filename_exclude_patterns = [
            'btn_',  # ボタン画像
            'spacer_',  # スペーサー
            'blank_',  # 空白画像
        ]
        
        if any(pattern in filename for pattern in filename_exclude_patterns):
            print(f"ファイル名による除外: {url}")
            return False
        
        # 有効な拡張子をチェック
        valid_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp']
        if any(ext in url_lower for ext in valid_extensions):
            print(f"有効な画像URL: {url}")
            return True
        
        # 拡張子がない場合でも、画像っぽいパスなら有効とする
        image_keywords = ['image', 'img', 'photo', 'picture', 'gallery', 'media']
        if any(keyword in url_lower for keyword in image_keywords):
            print(f"画像キーワードマッチ: {url}")
            return True
        
        return False

    def _calculate_image_quality_score(self, url: str) -> int:
        """画像の品質スコアを計算（緩和版）"""
        score = 10  # ベーススコアを上げる
        url_lower = url.lower()
        
        # 高品質を示すキーワード（スコア上昇）
        quality_keywords = {
            'large': 4,
            'big': 3,
            'full': 4,
            'original': 5,
            'high': 3,
            'main': 4,
            'hero': 5,
            'featured': 4,
            'gallery': 3,
            'photo': 3,
            'image': 2,
            'picture': 2,
            'visual': 2,
            'artwork': 4,
            'character': 4,  # キャラクター画像
            'anime': 4,  # アニメ関連
            'goods': 4,  # グッズ画像
            'product': 4,  # 商品画像
            'item': 3,   # アイテム画像
            'merchandise': 3,  # 商品
            'collaboration': 3,  # コラボ関連
            'event': 3,  # イベント関連
            'popup': 4,  # ポップアップ関連
            'store': 2,  # ストア関連
            'campaign': 3,  # キャンペーン
            'special': 3,  # 特別な
            'limited': 3,  # 限定
            'exclusive': 3,  # 限定
            'new': 2,    # 新商品
            'latest': 2,  # 最新
            'banner': 2,  # バナー（緩和）
            'logo': 1,   # ロゴ（完全除外から緩和）
            'icon': 1,   # アイコン（完全除外から緩和）
        }
        
        for keyword, points in quality_keywords.items():
            if keyword in url_lower:
                score += points
        
        # 低品質を示すキーワード（減点を緩和）
        low_quality_keywords = {
            'thumb': -2,  # -4から-2に緩和
            'thumbnail': -2,  # -4から-2に緩和
            'small': -1,  # -3から-1に緩和
            'mini': -1,   # -3から-1に緩和
            'tiny': -2,   # -4から-2に緩和
            'pixel': -5,  # トラッキングピクセルは厳格に
            'tracking': -5,  # トラッキングは厳格に
            'spacer': -5,    # スペーサーは厳格に
            'blank': -5,     # 空白画像は厳格に
            'placeholder': -3,  # プレースホルダーは減点
            'default': -1,      # デフォルト画像は軽減点
        }
        
        for keyword, points in low_quality_keywords.items():
            if keyword in url_lower:
                score += points
        
        # URLの構造による判定
        path_parts = url_lower.split('/')
        
        # 深い階層にある画像は詳細画像の可能性が高い
        if len(path_parts) > 5:
            score += 2
        
        # CDNやメディアサーバーの画像は品質が高い可能性
        if any(cdn in url_lower for cdn in ['cdn', 'media', 'assets', 'static', 'images']):
            score += 2
        
        # ファイル名に数字が多い場合（商品コードなど）
        filename = path_parts[-1].split('?')[0] if path_parts else ''
        if len([c for c in filename if c.isdigit()]) >= 3:
            score += 1
        
        # URLの長さ（長いURLは詳細な画像の可能性）
        if len(url) > 100:
            score += 1
        elif len(url) > 150:
            score += 2
        
        # 画像サイズの推測（URLに含まれるサイズ情報）
        size_patterns = [
            r'(\d{3,4})x(\d{3,4})',  # 640x480のような形式
            r'w(\d{3,4})',  # w640のような形式
            r'h(\d{3,4})',  # h480のような形式
        ]
        
        import re
        for pattern in size_patterns:
            matches = re.findall(pattern, url_lower)
            if matches:
                if isinstance(matches[0], tuple):
                    width, height = int(matches[0][0]), int(matches[0][1])
                    # 大きな画像にボーナス
                    if width >= 800 or height >= 600:
                        score += 3
                    elif width >= 400 or height >= 300:
                        score += 1
                else:
                    size = int(matches[0])
                    if size >= 800:
                        score += 3
                    elif size >= 400:
                        score += 1
        
        return max(5, score)  # 最低スコアを5に設定（0から変更）
    
    def _extract_text_content(self, soup: BeautifulSoup) -> Optional[str]:
        """テキストコンテンツの抽出"""
        # メインコンテンツエリアを探す
        main_content = (
            soup.find('main') or 
            soup.find('article') or 
            soup.find('div', class_=re.compile(r'content|main|article', re.I)) or
            soup.find('div', id=re.compile(r'content|main|article', re.I))
        )
        
        if main_content:
            # 不要なタグを削除
            for tag in main_content.find_all(['script', 'style', 'nav', 'header', 'footer']):
                tag.decompose()
            
            return main_content.get_text().strip()
        
        return None
    
    def _extract_metadata(self, soup, url: str) -> Dict[str, str]:
        """メタデータと全文テキストを抽出（シンプル版）"""
        metadata = {'source_url': url}
        
        try:
            print("全文テキスト抽出開始...")
            
            # 基本的なメタデータのみ抽出
            title_tag = soup.find('title')
            if title_tag:
                metadata['page_title'] = title_tag.get_text().strip()
                print(f"ページタイトル: {metadata['page_title']}")
            
            # メタディスクリプション
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc:
                metadata['meta_description'] = meta_desc.get('content', '').strip()
            
            # サイト全体のテキストを取得（情報を絞らない）
            full_text = soup.get_text()
            
            # 不要な空白・改行を整理するだけ
            clean_text = re.sub(r'\s+', ' ', full_text).strip()
            metadata['full_content'] = clean_text
            
            print(f"全文テキスト取得完了: {len(clean_text)}文字")
            print(f"テキスト冒頭: {clean_text[:200]}...")
            
            return metadata
            
        except Exception as e:
            print(f"メタデータ抽出エラー: {e}")
            return metadata
    
    def _determine_content_type(self, scraped_data: ScrapedData) -> str:
        """作品タイプの簡易判別"""
        text = scraped_data.text_content.lower() if scraped_data.text_content else ""
        
        # シンプルなキーワードベース判別
        if any(keyword in text for keyword in ['カフェ', 'cafe', 'ドリンク', 'メニュー']):
            return 'cafe'
        elif any(keyword in text for keyword in ['ノベルゲーム', 'ゲーム', 'game']):
            return 'novel_game'
        elif any(keyword in text for keyword in ['アニメ', 'anime']):
            return 'anime'
        else:
            return 'general'
    
    async def _enhance_with_google_search(self, scraped_data: ScrapedData) -> ScrapedData:
        """Google検索による情報補完は不要になったため、そのまま返す"""
        return scraped_data
    

    
 