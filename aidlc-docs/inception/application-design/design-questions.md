# Application Design Questions

以下の質問に回答してください。各質問の `[Answer]:` タグの後に選択肢の記号を記入してください。
選択肢にない場合は最後の「Other」を選び、説明を追記してください。

---

## Question 1
FastAPI の API エンドポイント設計方針はどちらが良いですか？

A) RESTful リソースベース（`/api/planters`, `/api/planters/{id}/logs` など）
B) ユースケースベース（`/api/post-seed`, `/api/post-log`, `/api/get-feed` など）
C) Other (please describe after [Answer]: tag below)

[Answer]: A

---

## Question 2
Next.js（Frontend）から FastAPI（Backend）への通信方式はどちらを想定していますか？

A) Next.js Server Actions / Route Handlers → FastAPI（サーバーサイドで API 呼び出し）
B) Next.js クライアントコンポーネントから直接 FastAPI を呼ぶ（ブラウザ → FastAPI）
C) 混合（ページロード時は Server Components 経由、ユーザー操作時はクライアント直接）
D) Other (please describe after [Answer]: tag below)

[Answer]: C

---

## Question 3
Supabase の利用範囲について。FastAPI から Supabase DB に接続する方法はどちらが良いですか？

A) Supabase クライアントライブラリ（supabase-py）経由でアクセス
B) 直接 PostgreSQL 接続（SQLAlchemy / asyncpg 等の ORM / ドライバ）
C) Other (please describe after [Answer]: tag below)

[Answer]: C（SQLAlchemy メイン + Auth/Storage のみ supabase-py） 

---

## Question 4
Supabase Auth のトークン検証をどこで行いますか？

A) FastAPI 側で JWT を検証する（FastAPI がゲートキーパー）
B) Next.js 側（middleware）で検証し、FastAPI には認証済みユーザーID をヘッダーで渡す
C) 両方で検証する（Next.js middleware + FastAPI 依存関係注入）
D) Other (please describe after [Answer]: tag below)

[Answer]: A

---

## Question 5
Louge 開花時の AI 記事生成・スコアリング等のバックグラウンドジョブ方式は？

A) FastAPI BackgroundTasks（シンプル、プロセス内非同期）
B) Cloud Tasks / Cloud Pub/Sub（外部キュー、スケーラブル）
C) Celery + Redis（定番のタスクキュー）
D) MVP は A（BackgroundTasks）で開始し、スケール時に B へ移行
E) Other (please describe after [Answer]: tag below)

[Answer]: D

---

## Question 6
フィード（ホーム画面の Planter 一覧）の「注目」タブのランキングロジックはどう定義しますか？

A) 条件A 構造充足率の高い順（開花に近い順）
B) 直近 N 時間の閲覧数（planter_views）が多い順
C) 直近 N 時間の Log 投稿数が多い順（議論の活発さ）
D) 複合スコア（閲覧数 + Log 投稿速度 + 構造充足率）
E) Other (please describe after [Answer]: tag below)

[Answer]: D

---

## Question 7
検索機能（FR-09）の初期実装の範囲はどこまでですか？

A) タグフィルタリングのみ（業界・職種・スキルのタグで絞り込み）
B) タグフィルタリング + キーワード全文検索（Supabase full-text search）
C) タグフィルタリング + キーワード検索 + Planter 状態フィルタ（Seed/Sprout/Louge）
D) Other (please describe after [Answer]: tag below)

[Answer]: C

---

## Question 8
Planter ページ（個別の Seed/Sprout/Louge 詳細画面）のURL設計について。

A) `/planter/{id}` — 状態に関係なく統一 URL
B) `/seed/{id}` で表示し、開花後も同一 URL（"seed" は起源を表す）
C) 状態に応じた URL（`/seed/{id}` → 開花後は `/louge/{id}` にリダイレクト）
D) Other (please describe after [Answer]: tag below)

[Answer]: D（/p/{id}）

---

## Question 9
Figma デザインの参照範囲について。現在ホーム画面のデザインが Figma にありますが、他の画面（Planter詳細・プロフィール・Seed投稿フォーム等）のデザインは？

A) 実装前に全画面を Figma で作成する
B) ホーム画面のデザインシステム（カラー・カード・レイアウト）を基に、他の画面は実装時にデザインも生成する
C) 重要な画面（Planter詳細・Seed投稿）のみ事前に Figma で作成し、残りは実装時
D) Other (please describe after [Answer]: tag below)

[Answer]: A
