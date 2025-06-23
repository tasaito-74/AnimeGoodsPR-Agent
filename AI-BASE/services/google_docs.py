import os
import requests
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import pickle
import base64
from typing import Dict, Any, List
import tempfile
import urllib.request
import re
from datetime import datetime

class GoogleDocsService:
    """Google Docs連携サービス"""
    
    def __init__(self):
        self.SCOPES = [
            'https://www.googleapis.com/auth/documents',
            'https://www.googleapis.com/auth/drive'
        ]
        self.creds = None
        self.docs_service = None
        self.drive_service = None
        self._authenticate()
    
    def _authenticate(self):
        """Google API認証"""
        try:
            # トークンファイルが存在する場合は読み込み
            if os.path.exists('token.pickle'):
                with open('token.pickle', 'rb') as token:
                    self.creds = pickle.load(token)
            
            # 有効な認証情報がない場合
            if not self.creds or not self.creds.valid:
                if self.creds and self.creds.expired and self.creds.refresh_token:
                    self.creds.refresh(Request())
                else:
                    # 環境変数から認証情報を取得
                    client_id = os.getenv('GOOGLE_CLIENT_ID')
                    client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
                    
                    if client_id and client_secret:
                        # 環境変数から認証フローを作成
                        flow = InstalledAppFlow.from_client_config(
                            {
                                "installed": {
                                    "client_id": client_id,
                                    "client_secret": client_secret,
                                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                                    "token_uri": "https://oauth2.googleapis.com/token",
                                    "redirect_uris": ["http://localhost"]
                                }
                            },
                            self.SCOPES
                        )
                        self.creds = flow.run_local_server(port=0)
                    else:
                        # 認証情報が不足している場合はダミー認証
                        print("警告: Google API認証情報が設定されていません。ダミーモードで動作します。")
                        self.creds = None
                
                # トークンを保存
                if self.creds:
                    with open('token.pickle', 'wb') as token:
                        pickle.dump(self.creds, token)
            
            # サービスを初期化
            if self.creds:
                self.docs_service = build('docs', 'v1', credentials=self.creds)
                self.drive_service = build('drive', 'v3', credentials=self.creds)
            
        except Exception as e:
            print(f"Google API認証エラー: {e}")
            self.creds = None
    
    def _create_safe_folder_name(self, title: str) -> str:
        """安全なフォルダ名を作成"""
        # 日時を追加
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        
        # タイトルをクリーンアップ
        safe_title = re.sub(r'[<>:"/\\|?*]', '', title)  # 無効な文字を削除
        safe_title = safe_title.replace('　', ' ')  # 全角スペースを半角に
        safe_title = re.sub(r'\s+', '_', safe_title)  # スペースをアンダースコアに
        safe_title = safe_title[:50]  # 長さ制限
        
        return f"{timestamp}_{safe_title}"
    
    def _create_folder(self, folder_name: str) -> str:
        """Google Driveにフォルダを作成"""
        try:
            folder_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': ['root']
            }
            
            folder = self.drive_service.files().create(
                body=folder_metadata,
                fields='id'
            ).execute()
            
            folder_id = folder.get('id')
            print(f"フォルダ作成成功: {folder_name} (ID: {folder_id})")
            return folder_id
            
        except Exception as e:
            print(f"フォルダ作成エラー: {e}")
            return 'root'  # フォールバック
    
    async def create_document(self, content: Dict[str, Any]) -> str:
        """Google Docsにドキュメントを作成"""
        try:
            if not self.docs_service:
                # 認証ができない場合はダミーURLを返す
                return "https://docs.google.com/document/d/dummy_document_id"
            
            # 記事タイトルからフォルダ名を作成
            article_title = content.get('title', 'アニメ記事')
            folder_name = self._create_safe_folder_name(article_title)
            
            # フォルダを作成
            folder_id = self._create_folder(folder_name)
            
            # ドキュメントを作成（parentsフィールドは使用しない）
            document = {
                'title': article_title
            }
            
            doc = self.docs_service.documents().create(body=document).execute()
            document_id = doc['documentId']
            
            # ドキュメントを指定フォルダに移動
            await self._move_file_to_folder(document_id, folder_id)
            
            # コンテンツを挿入（フォルダIDも渡す）
            await self._insert_content(content, document_id, folder_id)
            
            return f"https://docs.google.com/document/d/{document_id}"
            
        except Exception as e:
            print(f"Google Docs作成エラー: {e}")
            return "https://docs.google.com/document/d/error_document_id"
    
    async def _move_file_to_folder(self, file_id: str, folder_id: str):
        """ファイルを指定フォルダに移動"""
        try:
            # 現在の親フォルダを取得
            file = self.drive_service.files().get(fileId=file_id, fields='parents').execute()
            previous_parents = ",".join(file.get('parents'))
            
            # ファイルを新しいフォルダに移動
            self.drive_service.files().update(
                fileId=file_id,
                addParents=folder_id,
                removeParents=previous_parents,
                fields='id, parents'
            ).execute()
            
            print(f"ファイルをフォルダに移動: {file_id} → {folder_id}")
            
        except Exception as e:
            print(f"ファイル移動エラー: {e}")
    
    def _get_document_end_index(self, document_id: str) -> int:
        """ドキュメントの最終インデックスを取得"""
        try:
            doc = self.docs_service.documents().get(documentId=document_id).execute()
            # ドキュメントの最後のインデックスを取得
            body = doc.get('body', {})
            content = body.get('content', [])
            
            if content:
                # 最後の要素のendIndexを取得
                last_element = content[-1]
                return last_element.get('endIndex', 1)
            
            return 1
            
        except Exception as e:
            print(f"ドキュメント情報取得エラー: {e}")
            return 1
    
    async def _insert_content(self, content_data: dict, document_id: str, folder_id: str = None) -> dict:
        """コンテンツをGoogle Docsに挿入（HTML構造対応版）"""
        try:
            # まず既存のコンテンツをクリア
            await self._clear_document(document_id)
            
            # HTMLコンテンツと画像データを取得
            content_html = content_data.get('content', '')
            images = content_data.get('images', [])
            
            # 画像データとフォルダIDをインスタンス変数に設定
            self._current_images = images
            self._current_folder_id = folder_id or 'root'
            
            print(f"利用可能な画像: {len(images)}枚")
            for i, img_url in enumerate(images[:5]):  # 最初の5枚をログ出力
                print(f"  画像{i+1}: {img_url}")
            
            # HTMLをパースしてスタイル付きで挿入
            await self._insert_html_with_styles(document_id, content_html)
            
            # インスタンス変数をクリア
            self._current_images = []
            self._current_folder_id = None
            
            print("Google Docsへの挿入が完了しました")
            
            return {
                'success': True,
                'document_id': document_id,
                'content_length': len(content_html),
                'images_processed': len(images)
            }
            
        except Exception as e:
            print(f"Google Docs挿入エラー: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _insert_html_with_styles(self, document_id: str, html_content: str):
        """HTMLコンテンツをスタイル付きでGoogle Docsに挿入"""
        try:
            from bs4 import BeautifulSoup
            import re
            
            # HTMLをパース
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # HTMLを順番に処理
            await self._process_html_elements(document_id, soup)
            
        except Exception as e:
            print(f"HTML挿入エラー: {e}")
            # フォールバック: プレーンテキストとして挿入
            clean_text = self._clean_html_content(html_content)
            await self._insert_text_content(document_id, clean_text)
    
    async def _process_html_elements(self, document_id: str, soup):
        """HTML要素を順番に処理してGoogle Docsに挿入"""
        try:
            # 利用可能な画像リストを取得
            images = getattr(self, '_current_images', [])
            image_index = 0
            
            # トップレベルの要素を順番に処理
            for element in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'div']):
                text_content = element.get_text().strip()
                
                # 空のテキストや短すぎるテキストはスキップ
                if not text_content or len(text_content) < 3:
                    continue
                
                # 特定のクラスや属性を持つ要素はスキップ
                if element.get('class') and any(cls in str(element.get('class')) for cls in ['ads', 'advertisement', 'hidden']):
                    continue
                
                tag_name = element.name.lower()
                
                print(f"処理中: {tag_name} - {text_content[:100]}...")
                
                # 画像プレースホルダーの検出と処理
                if self._is_image_placeholder(text_content):
                    if image_index < len(images):
                        image_url = images[image_index]
                        await self._insert_image_from_url(document_id, image_url, f"image_{image_index + 1}")
                        image_index += 1
                    else:
                        print("利用可能な画像がありません。プレースホルダーをスキップします。")
                    continue
                
                # ヘッダータグの処理
                if tag_name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                    await self._insert_heading(document_id, tag_name, text_content)
                
                # 段落タグの処理
                elif tag_name in ['p', 'div']:
                    # 短すぎる段落はスキップ
                    if len(text_content) > 10:
                        await self._insert_paragraph(document_id, text_content)
                
        except Exception as e:
            print(f"HTML要素処理エラー: {e}")
    
    def _is_image_placeholder(self, text: str) -> bool:
        """テキストが画像プレースホルダーかどうかを判定"""
        placeholder_patterns = [
            '-適切な画像を挿入ー',
            '-適切な画像を挿入-',
            '適切な画像を挿入',
            '[画像',
            'IMAGE_PLACEHOLDER'
        ]
        
        return any(pattern in text for pattern in placeholder_patterns)
    
    async def _insert_image_from_url(self, document_id: str, image_url: str, filename: str):
        """URLから画像をダウンロードしてGoogle Docsに挿入"""
        try:
            print(f"画像挿入開始: {image_url}")
            
            # フォルダIDを取得（現在のドキュメントのフォルダ）
            folder_id = getattr(self, '_current_folder_id', 'root')
            
            # 画像をGoogle Driveにアップロード
            image_id = await self._upload_image_to_drive(image_url, filename, folder_id)
            
            if image_id:
                # Google Docsに画像を挿入
                await self._insert_image_to_docs(document_id, image_id)
                print(f"画像挿入成功: {filename}")
            else:
                # 画像挿入に失敗した場合はテキストで代替（改行付き）
                await self._insert_paragraph(document_id, f"[画像: {image_url}]\n")
                print(f"画像挿入失敗、テキストで代替: {filename}")
                
        except Exception as e:
            print(f"画像挿入エラー: {e}")
            # エラーの場合もテキストで代替（改行付き）
            await self._insert_paragraph(document_id, f"[画像: {image_url}]\n")
    
    async def _insert_heading(self, document_id: str, heading_level: str, text: str):
        """ヘッダーをGoogle Docsに挿入"""
        try:
            # 現在の終了位置を取得
            end_index = await self._get_document_end_index_async(document_id)
            insert_index = max(1, end_index - 1)
            
            # ヘッダーテキストを挿入
            formatted_text = f"{text}\n\n"
            
            # ヘッダーレベルに応じたスタイルを決定
            style_mapping = {
                'h1': 'HEADING_1',
                'h2': 'HEADING_2',
                'h3': 'HEADING_3',
                'h4': 'HEADING_4',
                'h5': 'HEADING_5',
                'h6': 'HEADING_6'
            }
            
            style = style_mapping.get(heading_level, 'HEADING_2')
            text_length = len(text)
            
            requests = [
                {
                    'insertText': {
                        'location': {'index': insert_index},
                        'text': formatted_text
                    }
                },
                {
                    'updateParagraphStyle': {
                        'range': {
                            'startIndex': insert_index,
                            'endIndex': insert_index + text_length
                        },
                        'paragraphStyle': {
                            'namedStyleType': style
                        },
                        'fields': 'namedStyleType'
                    }
                }
            ]
            
            # リクエストを実行
            self.docs_service.documents().batchUpdate(
                documentId=document_id,
                body={'requests': requests}
            ).execute()
            
            print(f"ヘッダー挿入完了: {heading_level} - {text[:50]}...")
            
        except Exception as e:
            print(f"ヘッダー挿入エラー: {e}")
    
    async def _insert_paragraph(self, document_id: str, text: str):
        """段落をGoogle Docsに挿入"""
        try:
            # 現在の終了位置を取得
            end_index = await self._get_document_end_index_async(document_id)
            insert_index = max(1, end_index - 1)
            
            # 段落テキストを挿入
            formatted_text = f"{text}\n\n"
            text_length = len(text)
            
            requests = [
                {
                    'insertText': {
                        'location': {'index': insert_index},
                        'text': formatted_text
                    }
                },
                {
                    'updateParagraphStyle': {
                        'range': {
                            'startIndex': insert_index,
                            'endIndex': insert_index + text_length
                        },
                        'paragraphStyle': {
                            'namedStyleType': 'NORMAL_TEXT'
                        },
                        'fields': 'namedStyleType'
                    }
                }
            ]
            
            # リクエストを実行
            self.docs_service.documents().batchUpdate(
                documentId=document_id,
                body={'requests': requests}
            ).execute()
            
            print(f"段落挿入完了: {text[:50]}...")
            
        except Exception as e:
            print(f"段落挿入エラー: {e}")
    
    async def _get_document_end_index_async(self, document_id: str) -> int:
        """ドキュメントの最終インデックスを非同期で取得"""
        try:
            doc = self.docs_service.documents().get(documentId=document_id).execute()
            body = doc.get('body', {})
            content = body.get('content', [])
            
            if content:
                return content[-1].get('endIndex', 1)
            
            return 1
            
        except Exception as e:
            print(f"ドキュメント情報取得エラー: {e}")
            return 1
    
    async def _clear_document(self, document_id: str):
        """ドキュメントの既存内容をクリア"""
        try:
            # 文書の現在の内容を取得
            doc = self.docs_service.documents().get(documentId=document_id).execute()
            content = doc.get('body', {}).get('content', [])
            
            if content:
                # 最後の要素のendIndexを取得（文書の最後）
                end_index = content[-1].get('endIndex', 1)
                
                # 文書の内容を削除（1文字目から最後まで、ただし最後の1文字は残す）
                # 新規作成されたドキュメントは通常改行文字1つのみ含まれるため、end_index > 2の場合のみ削除
                if end_index > 2:
                    requests = [{
                        'deleteContentRange': {
                            'range': {
                                'startIndex': 1,
                                'endIndex': end_index - 1
                            }
                        }
                    }]
                    
                    self.docs_service.documents().batchUpdate(
                        documentId=document_id,
                        body={'requests': requests}
                    ).execute()
                    
                    print("既存のドキュメント内容をクリアしました")
                else:
                    print("新規ドキュメントのため、クリア処理をスキップします")
                    
        except Exception as e:
            print(f"ドキュメントクリアエラー: {e}")
            # エラーがあっても続行
    
    def _convert_html_tables_to_text(self, html_content: str) -> str:
        """HTML表をテキスト形式に変換"""
        import re
        from bs4 import BeautifulSoup
        
        try:
            # HTMLテーブルを検出
            table_pattern = r'<table[^>]*class="event-info-table"[^>]*>.*?</table>'
            tables = re.findall(table_pattern, html_content, re.DOTALL)
            
            processed_content = html_content
            
            for table_html in tables:
                # BeautifulSoupでテーブルを解析
                soup = BeautifulSoup(table_html, 'html.parser')
                table = soup.find('table')
                
                if table:
                    # テーブルをテキスト形式に変換
                    table_text = "\n【開催情報】\n"
                    
                    rows = table.find_all('tr')
                    for row in rows:
                        th = row.find('th')
                        td = row.find('td')
                        
                        if th and td:
                            th_text = th.get_text().strip()
                            td_text = td.get_text().strip()
                            table_text += f"■ {th_text}: {td_text}\n"
                    
                    table_text += "\n"
                    
                    # HTMLテーブルをテキストに置換
                    processed_content = processed_content.replace(table_html, table_text)
            
            return processed_content
            
        except Exception as e:
            print(f"テーブル変換エラー: {e}")
            return html_content
    
    def _clean_html_content(self, html_content: str) -> str:
        """HTMLコンテンツをクリーンなテキストに変換"""
        import re
        from bs4 import BeautifulSoup
        
        try:
            # HTMLタグを適切なテキストに変換
            content = html_content
            
            # 見出しタグを変換
            content = re.sub(r'<h2[^>]*>(.*?)</h2>', r'\n\n【\1】\n', content, flags=re.DOTALL)
            content = re.sub(r'<h3[^>]*>(.*?)</h3>', r'\n■ \1\n', content, flags=re.DOTALL)
            
            # 段落タグを変換
            content = re.sub(r'<p[^>]*>(.*?)</p>', r'\1\n\n', content, flags=re.DOTALL)
            
            # divタグを変換
            content = re.sub(r'<div[^>]*>(.*?)</div>', r'\1\n', content, flags=re.DOTALL)
            
            # リンクタグを変換
            content = re.sub(r'<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>', r'\2 (\1)', content, flags=re.DOTALL)
            
            # 残りのHTMLタグを除去
            content = re.sub(r'<[^>]+>', '', content)
            
            # 余分な改行を整理
            content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
            content = content.strip()
            
            return content
            
        except Exception as e:
            print(f"HTMLクリーニングエラー: {e}")
            return html_content
    
    async def _insert_text_content(self, document_id: str, text_content: str):
        """テキストコンテンツをGoogle Docsに挿入"""
        try:
            requests = [
                {
                    'insertText': {
                        'location': {'index': 1},
                        'text': text_content
                    }
                }
            ]
            
            body = {'requests': requests}
            
            result = self.docs_service.documents().batchUpdate(
                documentId=document_id,
                body=body
            ).execute()
            
            print(f"テキスト挿入完了: {len(text_content)}文字")
            
        except Exception as e:
            print(f"テキスト挿入エラー: {e}")
    
    def _create_summary_table_text(self, summary_table: dict) -> str:
        """概要表をテキスト形式で作成"""
        table_text = "【開催情報】\n"
        
        # 各項目を整理
        if summary_table.get('official_site'):
            table_text += f"■ 公式サイト: {summary_table['official_site']}\n"
        if summary_table.get('location'):
            table_text += f"■ 開催場所: {summary_table['location']}\n"
        if summary_table.get('period'):
            table_text += f"■ 開催期間: {summary_table['period']}\n"
        if summary_table.get('access'):
            table_text += f"■ アクセス: {summary_table['access']}\n"
        if summary_table.get('contact'):
            table_text += f"■ お問い合わせ: {summary_table['contact']}\n"
        
        return table_text
    
    async def _process_photoswipe_tags(self, content: str, images: List[str]) -> str:
        """Photoswipeタグの処理（複数パターン対応・async版）"""
        if not images:
            return content
        
        import re
        
        # 複数のプレースホルダーパターンに対応
        placeholder_patterns = [
            r'\[single_photoswipe\].*?\[/single_photoswipe\]',  # [single_photoswipe]...[/single_photoswipe]
            r'-適切な画像を挿入ー',  # -適切な画像を挿入ー
            r'-適切な画像を挿入-',  # -適切な画像を挿入-
            r'適切な画像を挿入',  # 適切な画像を挿入
            r'\[IMAGE_PLACEHOLDER_\d+\]',  # [IMAGE_PLACEHOLDER_1]など
            r'\[.*?PLACEHOLDER.*?\]',  # 破損したプレースホルダー
        ]
        
        processed_content = content
        image_index = 0
        
        for pattern in placeholder_patterns:
            matches = list(re.finditer(pattern, processed_content, re.IGNORECASE | re.DOTALL))
            for match in matches:
                if image_index < len(images):
                    # 画像URLを挿入
                    image_url = images[image_index]
                    processed_content = processed_content.replace(match.group(0), f"[画像{image_index + 1}: {image_url}]")
                    image_index += 1
                    print(f"画像プレースホルダーを置換: {match.group(0)} → [画像{image_index}]")
                else:
                    # 画像が足りない場合は空文字に置換
                    processed_content = processed_content.replace(match.group(0), "")
                    print(f"画像プレースホルダーを削除: {match.group(0)}")
        
        return processed_content

    async def _process_image_placeholders(self, document_id: str, text: str, folder_id: str):
        """画像プレースホルダーを処理して実際の画像を挿入（簡略版）"""
        # 簡単にテキストとして挿入
        await self._insert_styled_text(document_id, f"{text}\n\n", 'NORMAL_TEXT')

    async def _process_html_element(self, document_id: str, element):
        """HTML要素を処理"""
        tag_name = element.name.lower()
        text_content = element.get_text().strip()
        
        if not text_content or len(text_content) < 5:
            return
        
        print(f"HTML要素処理: {tag_name} - {text_content[:50]}...")
        
        # タグに応じてスタイルを決定
        style_mapping = {
            'h1': 'HEADING_1',
            'h2': 'HEADING_2', 
            'h3': 'HEADING_3',
            'h4': 'HEADING_4',
            'h5': 'HEADING_5',
            'h6': 'HEADING_6',
            'p': 'NORMAL_TEXT',
            'div': 'NORMAL_TEXT',
            'span': 'NORMAL_TEXT',
            'strong': 'NORMAL_TEXT',
            'b': 'NORMAL_TEXT',
            'em': 'NORMAL_TEXT',
            'i': 'NORMAL_TEXT'
        }
        
        style = style_mapping.get(tag_name, 'NORMAL_TEXT')
        
        # リストの処理
        if tag_name in ['ul', 'ol']:
            # リスト項目を個別に処理
            for li in element.find_all('li'):
                li_text = li.get_text().strip()
                if li_text:
                    await self._insert_styled_text(document_id, f"• {li_text}\n", 'NORMAL_TEXT')
            await self._insert_styled_text(document_id, "\n", 'NORMAL_TEXT')
        elif tag_name == 'li':
            await self._insert_styled_text(document_id, f"• {text_content}\n", 'NORMAL_TEXT')
        elif tag_name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            # ヘッダータグは確実にスタイルを適用
            await self._insert_styled_text(document_id, f"{text_content}\n\n", style)
        else:
            # 段落は改行を追加
            await self._insert_styled_text(document_id, f"{text_content}\n\n", style)

    async def _insert_styled_text(self, document_id: str, text: str, style_type: str):
        """スタイル付きテキストを挿入"""
        try:
            # 毎回最新のドキュメント終了位置を取得
            doc = self.docs_service.documents().get(documentId=document_id).execute()
            content = doc.get('body', {}).get('content', [])
            
            if content:
                end_index = content[-1].get('endIndex', 1)
            else:
                end_index = 1
            
            requests = [{
                'insertText': {
                    'location': {
                        'index': max(1, end_index - 1)
                    },
                    'text': text
                }
            }]
            
            # スタイルを適用
            if style_type != 'NORMAL_TEXT':
                requests.append({
                    'updateParagraphStyle': {
                        'range': {
                            'startIndex': max(1, end_index - 1),
                            'endIndex': max(1, end_index - 1 + len(text))
                        },
                        'paragraphStyle': {
                            'namedStyleType': style_type
                        },
                        'fields': 'namedStyleType'
                    }
                })
            
            self.docs_service.documents().batchUpdate(
                documentId=document_id,
                body={'requests': requests}
            ).execute()
            
            print(f"スタイル付きテキスト挿入成功: {style_type} - {text[:30]}...")
            
        except Exception as e:
            print(f"スタイル付きテキスト挿入エラー: {e}")
            # フォールバック: 通常のテキスト挿入
            await self._insert_text_at_end(document_id, text)
    
    async def _insert_text_at_end(self, document_id: str, text: str):
        """ドキュメントの最後にテキストを挿入"""
        try:
            # 文書の現在の内容を取得して最後の位置を確認
            doc = self.docs_service.documents().get(documentId=document_id).execute()
            content = doc.get('body', {}).get('content', [])
            
            if content:
                # 最後の要素のendIndexを取得（文書の最後）
                end_index = content[-1].get('endIndex', 1) - 1
            else:
                end_index = 1
            
            requests = [{
                'insertText': {
                    'location': {'index': end_index},
                    'text': text
                }
            }]
            
            self.docs_service.documents().batchUpdate(
                documentId=document_id,
                body={'requests': requests}
            ).execute()
            
            print(f"テキストを最後に挿入完了: {len(text)}文字")
            
        except Exception as e:
            print(f"テキスト挿入エラー: {e}")
    
    async def _insert_image_to_docs(self, document_id: str, image_id: str):
        """Google Docsに画像を挿入"""
        try:
            # 毎回最新のドキュメント終了位置を取得
            doc = self.docs_service.documents().get(documentId=document_id).execute()
            content = doc.get('body', {}).get('content', [])
            
            if content:
                end_index = content[-1].get('endIndex', 1)
            else:
                end_index = 1
            
            # 画像挿入と改行を一括で処理
            requests = [
                {
                    'insertInlineImage': {
                        'location': {
                            'index': max(1, end_index - 1)
                        },
                        'uri': f'https://drive.google.com/uc?id={image_id}',
                        'objectSize': {
                            'height': {
                                'magnitude': 300,
                                'unit': 'PT'
                            },
                            'width': {
                                'magnitude': 400,
                                'unit': 'PT'
                            }
                        }
                    }
                },
                {
                    'insertText': {
                        'location': {
                            'index': max(1, end_index)
                        },
                        'text': '\n'
                    }
                }
            ]
            
            self.docs_service.documents().batchUpdate(
                documentId=document_id,
                body={'requests': requests}
            ).execute()
            
            print(f"画像をGoogle Docsに挿入しました（改行付き）: {image_id}")
            
        except Exception as e:
            print(f"Google Docs画像挿入エラー: {e}")
            # エラーが発生した場合は挿入をスキップ
            print(f"画像挿入をスキップします: {image_id}")
    
    async def _upload_image_to_drive(self, image_url: str, filename: str, folder_id: str) -> str:
        """画像をGoogle Driveにアップロード（指定フォルダ内に）"""
        try:
            print(f"画像ダウンロード開始: {image_url}")
            
            # 画像の形式とサイズをチェック
            response = requests.head(image_url, timeout=15, allow_redirects=True)
            content_type = response.headers.get('content-type', '')
            content_length = int(response.headers.get('content-length', 0))
            
            print(f"画像情報: type={content_type}, size={content_length} bytes")
            
            # サポートされている形式かチェック（より柔軟に）
            if content_type and not any(fmt in content_type.lower() for fmt in ['image/', 'jpeg', 'jpg', 'png', 'gif', 'webp']):
                print(f"サポートされていない画像形式: {content_type}")
                return None
            
            # サイズ制限チェック（15MB）
            if content_length > 15 * 1024 * 1024:
                print(f"画像サイズが大きすぎます: {content_length} bytes")
                return None
            
            # 画像をダウンロード
            import tempfile
            import os
            
            # 適切な拡張子を決定
            if 'png' in content_type.lower():
                suffix = '.png'
            elif 'gif' in content_type.lower():
                suffix = '.gif'
            elif 'webp' in content_type.lower():
                suffix = '.webp'
            else:
                suffix = '.jpg'
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
                print(f"画像ダウンロード中...")
                response = requests.get(image_url, timeout=30, allow_redirects=True)
                response.raise_for_status()
                tmp_file.write(response.content)
                tmp_file_path = tmp_file.name
                
                print(f"ダウンロード完了: {len(response.content)} bytes")
                
                # Driveにアップロード（指定フォルダ内に）
                file_metadata = {
                    'name': f'{filename}{suffix}',
                    'parents': [folder_id]  # 指定フォルダに保存
                }
                
                # 適切なMIMEタイプを設定
                mime_mapping = {
                    '.jpg': 'image/jpeg',
                    '.jpeg': 'image/jpeg', 
                    '.png': 'image/png',
                    '.gif': 'image/gif',
                    '.webp': 'image/webp'
                }
                mime_type = mime_mapping.get(suffix, 'image/jpeg')
                
                print(f"Google Driveにアップロード中: {mime_type}")
                media = MediaFileUpload(tmp_file_path, mimetype=mime_type)
                file = self.drive_service.files().create(
                    body=file_metadata,
                    media_body=media,
                    fields='id'
                ).execute()
                
                file_id = file.get('id')
                print(f"Driveアップロード成功: file_id={file_id}")
                
                # ファイルを公開設定にする
                permission = {
                    'type': 'anyone',
                    'role': 'reader'
                }
                self.drive_service.permissions().create(
                    fileId=file_id,
                    body=permission
                ).execute()
                
                print(f"ファイル公開設定完了: {file_id}")
                
                # 一時ファイルを削除
                os.unlink(tmp_file_path)
                
                print(f"画像アップロード成功: {filename}{suffix} → フォルダID: {folder_id}")
                return file_id
                
        except Exception as e:
            print(f"画像アップロードエラー: {e}")
            return None
    
    def create_dummy_document(self, content: Dict[str, Any]) -> str:
        """ダミードキュメント作成（認証なしの場合）"""
        return "https://docs.google.com/document/d/dummy_document_id" 