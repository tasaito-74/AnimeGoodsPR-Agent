# プロジェクト名

アニメ記事生成支援サービス

---

# 目的

アニメグッズ販売やイベント情報を扱うポータルサイト向けに、クライアントが公式URL（例：公式Xポスト、公式Webサイト）を貼り付けるだけで、対象ページをスクレイピングし、**生成AIを活用して構造と文体を含めた完全自動の記事生成**を行うサービスを開発する。

取得した画像と生成された記事本文は、**Google Docs上に自動で整理・格納**され、以降の編集や共有が容易に行えるようにする。

なお、**従来のWordPressフォーマットは使用せず、テンプレート構造も含めてAIにより自動生成**される。タグ付け・WordPress連携などの処理は行わない。

---

# 目標

1. URLの貼り付けのみで、記事生成からGoogle Docs反映までを完結させる。
2. 人手によるテンプレート整形やタグ付けを不要にする。
3. クライアントのオペレーションコストを最小化する。
4. 記事構成・文体・テンプレート設計まで、生成AIによる統合出力を可能にする。

---

# 処理順序

1. **フロントエンド**でURLを取得（HTMLまたはReactベース）。　- 「POP UP」「NEWS」「EVENT」の種別選択UIあり
2. URL内のHTML構造から**画像・文章をスクレイピング**（BeautifulSoupまたはPlaywright使用）。
3. スクレイピング結果（画像・文章・構造）を、プロンプトテンプレートに変換し、**生成AIへ入力**。
4. 生成AIが、文面・構成・セクションを自動生成（テンプレート整形含む）。
5. **画像と生成文をGoogle Docsへ自動で挿入・保存**（1記事1ファイル構成）。　- Docs APIを用いて文面・画像をプログラム的に配置
6. 作成されたGoogle Docsリンクをクライアントに返却。

---

# 技術項目

- **バックエンド**：Python（FastAPI）
- **スクレイピング**：BeautifulSoup4（静的） / Playwright（動的）
- **生成AI連携**：OpenAI GPT-4 API / DeepSeek / Claude（用途に応じて切り替え）
- **プロンプト設計**：POPUP/NEWSなどのカテゴリごとに設計したテンプレートを基に自動生成
- **Google Docs連携**：Google Drive API + Google Docs API
- **フロントエンド**：HTML / CSS（初期） → React対応予定
- **CMS連携**：**非対応（WordPress連携は行わない）**
- **タグ・メタ情報整形**：**非対応（タグ付けは実施しない）**
- **補完検索**：必要に応じてGoogle検索で不足情報を補完

---

# フロー図（テキスト形式）

\[URL入力] ↓ \[スクレイピング（画像 + テキスト）] ↓ \[生成AIプロンプトに変換して入力] ↓ \[テンプレート構造と文面をAIが一括生成] ↓ \[Google Docsに記事 & 画像を自動挿入] ↓ \[クライアントにGoogle Docsリンクを返却]

---

# 出力形式（POP UPの場合）

- タイトル：〇〇（イベント名）、〇月〇日（開催日）より、〇〇（開催場所）にて開催！
- メタディスクリプション（描き下ろしイラストの有無で分岐）
- リード文（描き下ろしイラストの有無で分岐）
- グッズ情報（元URLのグッズ情報が掲載された画像を正確に引用）
- ノベルティ情報（元URLのノベルティ情報が掲載された画像を正確に引用）
- 正確な開催情報（リスト形式で、公式サイト、開催場所、開催期間、お問い合わせを掲載）

## メタディスクリプション
### メタディスクリプション (描き下ろしイラスト時)
{author}先生による人気漫画を原作としたアニメ「XXX」× (メーカー名)のポップアップストアが、店舗名にて2025年N月NN日〜NNN月NNNN日まで開催される。アニメ「XXX」ポップアップストアでは、描き下ろしイラストを使用した新作グッズが多数ラインナップ!

### メタディスクリプション (描き下ろしイラストじゃない時)
OOO先生による人気漫画を原作としたアニメ「XXX」× (メーカー名)のポップアップストアが、店舗名にて2025年N月NN日〜NNN月NNNN日まで開催される。アニメ「XXX」ポップアップストアでは、(キャラ名)・(キャラ名)・(キャラ名)らの描き下ろしイラストを使用した新作グッズが多数ラインナップ！

---

## リード文

**描き下ろしイラストの場合**
OOO先生による人気漫画を原作としたアニメ「XXX」× メーカー名のポップアップストアが、店舗名にて2025年N月NN日〜NNN月NNNN日まで開催される。
アニメ「XXX」ポップアップストアでは、イベント限定の描き下ろしイラストを使用した新作グッズが多数販売される他、グッズをお買い上げ●,●●●円(税込)ごとに特典として描き下ろしノベルティ「●●● 全●種」をランダムに1枚プレゼント!

**描き下ろしイラストではない場合**
OOO先生による人気漫画を原作としたアニメ「XXX」× (メーカー名)のポップアップストアが、店舗名にて2025年N月NN日〜NNN月NNNN日まで開催される。
「イベント名」ポップアップストアでは、作品に登場する人気キャラクターたちのアニメビジュアルを使用したグッズが多数販売される他、「XXX」関連商品を含めて、●,●●●円(税込)お買い上げ毎に特典として「●●● (全●種)」をランダムに1枚プレゼント!
[sc name="oshibuta-banner"][/sc]

**「株式会社A3」や「TSUTAYA」の場合**
アニメ「XXX」新商品を含めて関連商品を●,●●●円(税込)以上お買い上げの方に、特典として描き下ろしノベルティ「●●● 全●種」を1会計につき1枚プレゼント!

---

<h2>(イベント名) ポップアップストア in (店舗名)のグッズ</h2>

**描き下ろしイラストの場合**
描き下ろしイラスト時2025年N月NN日より「店舗名」にて、アニメ「XXX」の描き下ろしグッズを販売するポップアップストアを開催!

**描き下ろしイラストじゃない場合**
2025年N月NN日より「店舗名」にて、「XXX」のポップアップストアを開催!

<h3>グッズラインナップ</h3>
<div class="l-center l-padding-t-1em l-margin-b-1em">
-適切な画像を挿入ー
</div>
<div class="l-center l-padding-t-1em l-margin-b-1em">
<span class="f-size12px">以下広告のあとに記事が続きます</span>
</div>
<moreads>広告表示</moreads>

---
<h2>XXX ポップアップストア in 店舗名のノベルティー</h2>

**通常の場合**
「XXX」ポップアップストアにて、グッズをお買い上げ●,000円毎に特典として「●●● 全●種」がランダムに1枚プレゼントされる。

**「株式会社A3」や「TSUTAYA」の場合**
「XXX」ポップアップストアにて新商品を含めて関連商品を●,000円(税込)以上お買い上げの方に、特典として描き下ろしノベルティ「●●● 全●種」が1会計につき1枚ランダムにプレゼントされる。

<h3>お買い上げ特典 - ●●● 全●種/ランダム</h3>
<div class="l-center l-padding-t-1em l-margin-b-1em">
-適切な画像を挿入ー
</div>

---

<h2 id="pop-up-summary">XXX ポップアップストア in 店舗名 N月NN日より開催!</h2>
<div class="l-center l-padding-t-1em l-margin-b-1em">
-適切な画像を挿入ー
</div>
<div class="table__container">
 <table class="cc-table l-margin-b-2em">
  <tr>
   <th class="l-width-30percent">公式サイト</th>
   <td><a href="URLを入れる?utm_source=collabo_cafe_dot_com&amp;utm_medium=collabo_cafe_dot_com&amp;utm_campaign=collabo_cafe_dot_com&amp;utm_id=collabo_cafe_dot_com" target="_blank" class="cc__officiallink" rel="noopener noreferrer">特設ページ</a></td>
  </tr>
  <tr>
   <th>開催場所</th>
   <td>店舗名</td>
  </tr>
  <tr>
   <th>開催期間</th>
   <td>2025年N月NN日〜NNN月NNNN日</td>
  </tr>
  <tr>
   <th>アクセス・地図</th>
   <td><a href="https://goo.gl/maps/URLを入れる" target="_blank" rel="noopener noreferrer">Googleマップ</a>で見る</td>
  </tr>
  <tr>
   <th>お問い合わせ</th>
   <td><a href="URLを入れる?utm_source=collabo_cafe_dot_com&amp;utm_medium=collabo_cafe_dot_com&amp;utm_campaign=collabo_cafe_dot_com&amp;utm_id=collabo_cafe_dot_com" target="_blank" class="cc__officiallink" rel="noopener noreferrer">メーカー名</a>にお問い合わせください。</td>
  </tr>
 </table>
</div>
<div class="l-center l-padding-t-1em l-margin-b-1em">
<span class="f-size12px">以下広告のあとに記事が続きます</span>
</div>
<moreads>広告表示</moreads>


<div class="l-center l-padding-t-1em l-width-80percent l-margin-b-1em">
Twitter URLを挿入
</div>
詳細は公式サイトをご確認ください。
<span class="f-size12px">※記事の情報が古い場合がありますのでお手数ですが公式サイトの情報をご確認下さい。</span>
<p class="f-size12px"><small>&copy; XXX</small></p>

# 出力形式（POP UPの場合）