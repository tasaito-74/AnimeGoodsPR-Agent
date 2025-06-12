from typing import List, Optional
from dataclasses import dataclass
from .format_types import ArticleInfo, StoreType, IllustrationType

@dataclass
class ArticleContent:
    """記事の各セクションの内容を保持するクラス"""
    meta_description: str
    lead: str
    goods_section: str
    novelty_section: str
    summary_section: str
    footer: str

class TemplateGenerator:
    @staticmethod
    def generate_meta_description(info: ArticleInfo) -> str:
        """メタディスクリプションを生成"""
        base = f"{info.author}先生による人気漫画を原作としたアニメ「{info.anime_name}」× {info.maker_name}のポップアップストアが、{info.store_info.name}にて{info.store_info.start_date}〜{info.store_info.end_date}まで開催される。"
        
        if info.store_info.illustration_type == IllustrationType.ORIGINAL:
            if info.character_names:
                characters = "・".join(info.character_names)
                return f"{base}アニメ「{info.anime_name}」ポップアップストアでは、{characters}らの描き下ろしイラストを使用した新作グッズが多数ラインナップ!"
            return f"{base}アニメ「{info.anime_name}」ポップアップストアでは、描き下ろしイラストを使用した新作グッズが多数ラインナップ!"
        else:
            return f"{base}「{info.anime_name}」に登場する人気キャラクターたちのアニメビジュアルを使用したグッズが多数ラインナップ!"

    @staticmethod
    def generate_lead(info: ArticleInfo) -> str:
        """リード文を生成"""
        base = f"{info.author}先生による人気漫画を原作としたアニメ「{info.anime_name}」× {info.maker_name}のポップアップストアが、{info.store_info.name}にて{info.store_info.start_date}〜{info.store_info.end_date}まで開催される。\n"
        
        if info.store_info.illustration_type == IllustrationType.ORIGINAL:
            if info.store_info.type in [StoreType.A3, StoreType.TSUTAYA]:
                return f"{base}アニメ「{info.anime_name}」新商品を含めて関連商品を{info.novelty_info.price:,}円(税込)以上お買い上げの方に、特典として描き下ろしノベルティ「{info.novelty_info.name} 全{info.novelty_info.total_types}種」を1会計につき1枚プレゼント!"
            return f"{base}アニメ「{info.anime_name}」ポップアップストアでは、イベント限定の描き下ろしイラストを使用した新作グッズが多数販売される他、グッズをお買い上げ{info.novelty_info.price:,}円(税込)ごとに特典として描き下ろしノベルティ「{info.novelty_info.name} 全{info.novelty_info.total_types}種」をランダムに1枚プレゼント!"
        else:
            return f"{base}「{info.anime_name}」ポップアップストアでは、作品に登場する人気キャラクターたちのアニメビジュアルを使用したグッズが多数販売される他、「{info.anime_name}」関連商品を含めて、{info.novelty_info.price:,}円(税込)お買い上げ毎に特典として「{info.novelty_info.name} (全{info.novelty_info.total_types}種)」をランダムに1枚プレゼント!"

    @staticmethod
    def generate_goods_section(info: ArticleInfo) -> str:
        """グッズセクションを生成"""
        if info.store_info.illustration_type == IllustrationType.ORIGINAL:
            return f"""<h2 id="pop-up-goods">{info.anime_name} ポップアップストア in {info.store_info.name}のグッズ</h2>
{info.store_info.start_date}より「{info.store_info.name}」にて、アニメ「{info.anime_name}」の描き下ろしグッズを販売するポップアップストアを開催!"""
        else:
            return f"""<h2 id="pop-up-goods">{info.anime_name} ポップアップストア in {info.store_info.name}のグッズ</h2>
{info.store_info.start_date}より「{info.store_info.name}」にて、「{info.anime_name}」のポップアップストアを開催!"""

    @staticmethod
    def generate_novelty_section(info: ArticleInfo) -> str:
        """ノベルティセクションを生成"""
        if info.store_info.type in [StoreType.A3, StoreType.TSUTAYA]:
            return f"""<h2 id="pop-up-novelty">{info.anime_name} ポップアップストア in {info.store_info.name}のノベルティー</h2>
「{info.anime_name}」ポップアップストアにて新商品を含めて関連商品を{info.novelty_info.price:,}円(税込)以上お買い上げの方に、特典として描き下ろしノベルティ「{info.novelty_info.name} 全{info.novelty_info.total_types}種」が1会計につき1枚ランダムにプレゼントされる。"""
        else:
            return f"""<h2 id="pop-up-novelty">{info.anime_name} ポップアップストア in {info.store_info.name}のノベルティー</h2>
「{info.anime_name}」ポップアップストアにて、グッズをお買い上げ{info.novelty_info.price:,}円毎に特典として「{info.novelty_info.name} 全{info.novelty_info.total_types}種」がランダムに1枚プレゼントされる。"""

    @staticmethod
    def generate_summary_section(info: ArticleInfo) -> str:
        """サマリーセクションを生成"""
        return f"""<h2 id="pop-up-summary">{info.anime_name} ポップアップストア in {info.store_info.name} {info.store_info.start_date}より開催!</h2>
<div class="table__container">
 <table class="cc-table l-margin-b-2em">
  <tr>
   <th class="l-width-30percent">公式サイト</th>
   <td><a href="{info.store_info.official_url}?utm_source=collabo_cafe_dot_com&amp;utm_medium=collabo_cafe_dot_com&amp;utm_campaign=collabo_cafe_dot_com&amp;utm_id=collabo_cafe_dot_com" target="_blank" class="cc__officiallink" rel="noopener noreferrer">特設ページ</a></td>
  </tr>
  <tr>
   <th>開催場所</th>
   <td>{info.store_info.name}</td>
  </tr>
  <tr>
   <th>開催期間</th>
   <td>{info.store_info.start_date}〜{info.store_info.end_date}</td>
  </tr>
  <tr>
   <th>アクセス・地図</th>
   <td><a href="{info.store_info.google_maps_url}" target="_blank" rel="noopener noreferrer">Googleマップ</a>で見る</td>
  </tr>
  <tr>
   <th>お問い合わせ</th>
   <td><a href="{info.store_info.contact_url}?utm_source=collabo_cafe_dot_com&amp;utm_medium=collabo_cafe_dot_com&amp;utm_campaign=collabo_cafe_dot_com&amp;utm_id=collabo_cafe_dot_com" target="_blank" class="cc__officiallink" rel="noopener noreferrer">{info.maker_name}</a>にお問い合わせください。</td>
  </tr>
 </table>
</div>"""

    @staticmethod
    def generate_footer(info: ArticleInfo) -> str:
        """フッターを生成"""
        footer = """<div class="l-center l-padding-t-1em l-margin-b-1em">
<span class="f-size12px">以下広告のあとに記事が続きます</span>
</div>
<moreads></moreads>
[sc name="anime_store_common_html"][/sc]"""

        if info.store_info.twitter_url:
            footer += f"""
<div class="l-center l-padding-t-1em l-width-80percent l-margin-b-1em">
{info.store_info.twitter_url}
</div>"""

        if info.store_info.category_url:
            footer += f"""
<div class="btn-wrap aligncenter"><a href="{info.store_info.category_url}">{info.anime_name}の記事一覧</a></div>"""

        footer += """
詳細は公式サイトをご確認ください。
<span class="f-size12px">※記事の情報が古い場合がありますのでお手数ですが公式サイトの情報をご確認下さい。</span>
<p class="f-size12px"><small>&copy; {info.anime_name}</small></p>"""

        return footer

    @classmethod
    def generate_article(cls, info: ArticleInfo) -> ArticleContent:
        """記事全体を生成"""
        return ArticleContent(
            meta_description=cls.generate_meta_description(info),
            lead=cls.generate_lead(info),
            goods_section=cls.generate_goods_section(info),
            novelty_section=cls.generate_novelty_section(info),
            summary_section=cls.generate_summary_section(info),
            footer=cls.generate_footer(info)
        ) 