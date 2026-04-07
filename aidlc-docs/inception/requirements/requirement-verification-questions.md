# Works Logue — 要件確認質問

`docs/business-plan.md` から事業概要・ドメイン知識は把握済みです。
技術実装の詳細を確認するため、以下の質問にお答えください。
各質問の `[Answer]:` タグの後にアルファベット（A, B, C ...）を記入してください。

---

## Question 1
**MVP（最初の開発イテレーション）のスコープをどこまで設定しますか？**

A) 最小限（Seed投稿 + Log投稿 + 基本的な認証のみ）
B) 標準（A + Sproutステータス表示 + Louge開花 + ユーザープロフィール）
C) 広め（B + インサイトスコア + バッジ + Fork機能）
D) Other (please describe after [Answer]: tag below)

[Answer]: B

---

## Question 2
**Supabase プロジェクトは既に作成済みですか？**

A) まだ作成していない（新規で作成する）
B) 既に作成済み（プロジェクトURLとAPIキーは手元にある）
C) Other (please describe after [Answer]: tag below)

[Answer]: A

---

## Question 3
**Google Cloud Platform（Vertex AI用）プロジェクトは既に作成済みですか？**

A) まだ作成していない（GCPプロジェクトの作成から必要）
B) 既に作成済み（プロジェクトIDは手元にある）
C) 当面はVertex AIを使わず、OpenAI / Anthropic APIで代替する
D) Other (please describe after [Answer]: tag below)

[Answer]: A

---

## Question 4
**Louge開花の判定ロジックについて、初期実装の方針を教えてください。**

A) シンプルな閾値判定（例：Log数 >= 10 かつ 参加者数 >= 3）
B) AI（LLM）による品質評価を含む複合スコアリング
C) まず閾値判定で実装し、後でAI評価を追加する
D) Other (please describe after [Answer]: tag below)

[Answer]: B

---

## Question 5
**認証方法について教えてください（Supabase Auth を使用）**

A) メール＋パスワードのみ
B) メール＋パスワード ＋ Googleログイン
C) Googleログインのみ（ビジネスSNS想定なのでGoogleで十分）
D) Other (please describe after [Answer]: tag below)

[Answer]: B

---

## Question 6
**フロントエンド（Next.js）のスタイリングライブラリを教えてください**

A) Tailwind CSS（推奨）
B) CSS Modules
C) shadcn/ui + Tailwind CSS
D) Other (please describe after [Answer]: tag below)

[Answer]: C

---

## Question 7
**Cloud Run へのデプロイは初期フェーズから行いますか？**

A) Yes — 最初からCloud Runに継続的デプロイ（CI/CD）を設定する
B) No — まずローカル開発 → 動くものができてからデプロイを考える
C) Other (please describe after [Answer]: tag below)

[Answer]: A

---

## Question 8 (Extension: Security Baseline)
**セキュリティ拡張ルールを適用しますか？**

A) Yes — セキュリティルールをブロッキング制約として適用する（本番グレード推奨）
B) No — スキップする（MVP・プロトタイプフェーズ向け）
C) Other (please describe after [Answer]: tag below)

[Answer]: B

---

## Question 9 (Extension: Property-Based Testing)
**プロパティベーステストを適用しますか？**

A) Yes — PBTルールをブロッキング制約として適用する
B) Partial — 純粋関数とシリアライゼーションのみに適用する
C) No — スキップする（シンプルなCRUD中心のMVPフェーズ向け）
D) Other (please describe after [Answer]: tag below)

[Answer]: C

---

回答が完了したら「done」とお知らせください。
