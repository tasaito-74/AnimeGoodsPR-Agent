import os
import openai
from models.scraped_data import ScrapedData
from typing import Dict, Any
import json
import asyncio

class AIGenerator:
    """AI生成サービス（POP UP専用）"""
    
    def __init__(self):
        """AIコンテンツ生成サービスの初期化"""
        self.client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    
    async def generate_article(self, scraped_data: ScrapedData, format_type: str, category: str) -> Dict[str, Any]:
        """記事を生成（POP UP専用）"""
        try:
            print(f"AI生成開始: format_type={format_type}, category={category}")
            print(f"スクレイピングデータ確認: url={scraped_data.url}, text_length={len(scraped_data.text_content or '')}, images={len(scraped_data.images)}")
            
            # POP UPプロンプトを構築
            prompt = self._build_popup_prompt(scraped_data)
            print(f"プロンプト構築完了: {len(prompt)}文字")
            
            # OpenAI APIで記事生成
            print("OpenAI API呼び出し開始...")
            response = await self._generate_with_openai(prompt)
            print(f"OpenAI API呼び出し完了: {len(response)}文字")
            
            # 生成されたコンテンツを構造化
            structured_content = self._structure_content(response, scraped_data)
            
            print(f"AI生成完了: title={structured_content.get('title', 'N/A')}")
            return structured_content
            
        except Exception as e:
            print(f"AI生成エラー（詳細）: {type(e).__name__}: {str(e)}")
            import traceback
            print(f"エラートレースバック: {traceback.format_exc()}")
            return self._create_fallback_content(scraped_data)
    
    def _build_popup_prompt(self, scraped_data: ScrapedData) -> str:
        """POP UP専用プロンプト"""
        
        # サイト全体のテキストを取得
        full_content = scraped_data.text_content or ""
        
        # URLの取得（urlフィールドまたはmetadataから）
        source_url = scraped_data.url or scraped_data.metadata.get('source_url', '')
        
        print(f"全文テキスト長: {len(full_content)}文字")
        print(f"POP UPプロンプト構築中...")
        print(f"ソースURL: {source_url}")
        
        return f"""
あなたは日本のアニメポップアップストア専門のライターです。

以下のサイト情報から、ポップアップストアの記事を生成してください。

【出力指示】
以下のHTML構成で記事を作成してください：

<h2>メタディスクリプション</h2>
<p>（描き下ろしイラスト時）
[作者名]先生による人気漫画を原作としたアニメ「[作品名]」× [メーカー名]のポップアップストアが、[店舗名]にて2025年N月NN日〜NNN月NNNN日まで開催される。アニメ「[作品名]」ポップアップストアでは、描き下ろしイラストを使用した新作グッズが多数ラインナップ!</p>

<p>（描き下ろしイラストじゃない時）
[作者名]先生による人気漫画を原作としたアニメ「[作品名]」× [メーカー名]のポップアップストアが、[店舗名]にて2025年N月NN日〜NNN月NNNN日まで開催される。アニメ「[作品名]」ポップアップストアでは、[キャラ名]・[キャラ名]・[キャラ名]らの描き下ろしイラストを使用した新作グッズが多数ラインナップ！</p>

<h2>リード文</h2>
<p>（描き下ろしイラストの場合）
[作者名]先生による人気漫画を原作としたアニメ「[作品名]」× [メーカー名]のポップアップストアが、[店舗名]にて2025年N月NN日〜NNN月NNNN日まで開催される。
アニメ「[作品名]」ポップアップストアでは、イベント限定の描き下ろしイラストを使用した新作グッズが多数販売される他、グッズをお買い上げ[価格]円(税込)ごとに特典として描き下ろしノベルティ「[ノベルティ名] 全[種類数]種」をランダムに1枚プレゼント!</p>

<p>（描き下ろしイラストではない場合）
[作者名]先生による人気漫画を原作としたアニメ「[作品名]」× [メーカー名]のポップアップストアが、[店舗名]にて2025年N月NN日〜NNN月NNNN日まで開催される。
「[イベント名]」ポップアップストアでは、作品に登場する人気キャラクターたちのアニメビジュアルを使用したグッズが多数販売される他、「[作品名]」関連商品を含めて、[価格]円(税込)お買い上げ毎に特典として「[ノベルティ名] (全[種類数]種)」をランダムに1枚プレゼント!</p>

<h2>[イベント名] ポップアップストア in [店舗名]のグッズ</h2>
<p>[開催日]より「[店舗名]」にて、「[作品名]」のポップアップストアを開催!</p>

<h3>グッズラインナップ</h3>
<div>-適切な画像を挿入ー</div>

<p>以下広告のあとに記事が続きます</p>

<h2>[作品名] ポップアップストア in [店舗名]のノベルティー</h2>
<p>「[作品名]」ポップアップストアにて、グッズをお買い上げ[価格]円毎に特典として「[ノベルティ名] 全[種類数]種」がランダムに1枚プレゼントされる。</p>

<h3>お買い上げ特典 - [ノベルティ名] 全[種類数]種/ランダム</h3>
<div>-適切な画像を挿入ー</div>

<h2 id="pop-up-summary">[作品名] ポップアップストア in [店舗名] [開催日]より開催!</h2>
<div>-適切な画像を挿入ー</div>

<h3>開催情報</h3>
<p>公式サイト：<a href="{source_url}" target="_blank">特設ページ</a></p>
<p>開催場所：[店舗名]</p>
<p>開催期間：[開催期間]</p>
<p>お問い合わせ：<a href="{source_url}" target="_blank">[メーカー名]</a>にお問い合わせください。</p>

<p>以下広告のあとに記事が続きます</p>

<p>詳細は公式サイトをご確認ください。</p>
<p>※記事の情報が古い場合がありますのでお手数ですが公式サイトの情報をご確認下さい。</p>

【重要】
- サイト情報から具体的な情報を抽出し、[作品名]、[店舗名]、[開催日]、[価格]などを実際の情報に置き換えてください
- 画像プレースホルダー「-適切な画像を挿入ー」を3箇所に配置してください
- 推測や創作はせず、実際の情報のみを使用してください
- HTMLタグは正しく閉じてください

【元サイト情報】
URL: {source_url}
サイト全文: {full_content}
"""
    
    async def _generate_with_openai(self, prompt: str) -> str:
        """OpenAI APIを使用してコンテンツを生成"""
        try:
            print("OpenAI API呼び出し準備中...")
            
            # APIキーの確認
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                print("OPENAI_API_KEYが設定されていません。フォールバックコンテンツを生成します。")
                return self._generate_fallback_html_content()
            
            print(f"APIキー確認OK (先頭10文字: {api_key[:10]}...)")
            
            def call_openai_api():
                print("同期的なAPI呼び出し開始...")
                response = self.client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "あなたは日本のアニメポップアップストア専門のライターです。"},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=2000,
                    temperature=0.7
                )
                print("同期的なAPI呼び出し完了")
                return response.choices[0].message.content
            
            # 同期的なAPI呼び出しを非同期で実行
            print("asyncio.to_thread実行開始...")
            result = await asyncio.to_thread(call_openai_api)
            print(f"asyncio.to_thread実行完了: {len(result)}文字")
            return result
            
        except Exception as e:
            print(f"OpenAI API エラー（詳細）: {type(e).__name__}: {str(e)}")
            print("フォールバックコンテンツを生成します...")
            return self._generate_fallback_html_content()
    
    def _generate_fallback_html_content(self) -> str:
        """OpenAI APIが利用できない場合のフォールバックHTMLコンテンツ"""
        return """
<h1>メタディスクリプション</h1>
<p>人気アニメのポップアップストアが開催されます。詳細は公式サイトをご確認ください。</p>

<h2>リード文</h2>
<p>アニメポップアップストアでは、作品に関連したグッズが多数販売される予定です。</p>

<h2>ポップアップストアのグッズ</h2>
<p>ポップアップストアを開催!</p>

<h3>グッズラインナップ</h3>
<div>-適切な画像を挿入ー</div>

<p>以下広告のあとに記事が続きます</p>

<h2>ポップアップストアのノベルティー</h2>
<p>グッズをお買い上げの方に特典をプレゼント。</p>

<h3>お買い上げ特典</h3>
<div>-適切な画像を挿入ー</div>

<h2>ポップアップストア開催!</h2>
<div>-適切な画像を挿入ー</div>

<h3>開催情報</h3>
<p>詳細は公式サイトをご確認ください。</p>

<p>以下広告のあとに記事が続きます</p>

<p>詳細は公式サイトをご確認ください。</p>
<p>※記事の情報が古い場合がありますのでお手数ですが公式サイトの情報をご確認下さい。</p>
"""
    
    def _structure_content(self, response: str, scraped_data: ScrapedData) -> Dict[str, Any]:
        """生成されたコンテンツを構造化"""
        try:
            # URLの取得（urlフィールドまたはmetadataから）
            source_url = scraped_data.url or scraped_data.metadata.get('source_url', '')
            
            # スクレイピングした画像データを取得
            images = scraped_data.images or []
            
            print(f"構造化: {len(images)}枚の画像を含む")
            
            return {
                "title": f"ポップアップストア記事 - {source_url}",
                "content": response,
                "images": images,  # 画像データを追加
                "source_url": source_url,
                "generated_at": "2024-01-01T00:00:00Z"
            }
        except Exception as e:
            print(f"コンテンツ構造化エラー: {e}")
            return self._create_fallback_content(scraped_data)
    
    def _create_fallback_content(self, scraped_data: ScrapedData) -> Dict[str, Any]:
        """フォールバックコンテンツを作成"""
        # URLの取得（urlフィールドまたはmetadataから）
        source_url = scraped_data.url or scraped_data.metadata.get('source_url', '')
        
        # スクレイピングした画像データを取得
        images = scraped_data.images or []
        
        return {
            "title": f"ポップアップストア記事 - {source_url}",
            "content": f"<p>記事の生成中にエラーが発生しました。詳細は<a href='{source_url}' target='_blank'>公式サイト</a>をご確認ください。</p>",
            "images": images,  # 画像データを追加
            "source_url": source_url,
            "generated_at": "2024-01-01T00:00:00Z",
            "error": True
        }