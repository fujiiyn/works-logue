# U4 Louge - Business Rules

---

## BR-01: 開花条件

| ルール | 内容 |
|---|---|
| BR-01-1 | 条件A（構造充足率 = 1.0）AND 条件B（成熟度スコア >= bloom_threshold）を両方満たした時点で開花する |
| BR-01-2 | 開花は Planter ごとに1回のみ。`louge` 状態からの逆遷移は不可 |
| BR-01-3 | 開花トリガーは ScorePipeline 内で自動判定。手動トリガーは MVP では不要 |

---

## BR-02: Louge 記事生成

| ルール | 内容 |
|---|---|
| BR-02-1 | 記事はパターンランゲージ形式: パターン名 / 状況 / 問題 / 解決策 / 反論・例外 / 出典 |
| BR-02-2 | 出典は脚注方式。記事本文中に `[1]` `[2]` 等の番号を振り、文末に引用元 Log を一覧表示 |
| BR-02-3 | 出典には投稿者名と Log のスニペット（抜粋）を含める |
| BR-02-4 | 記事は Markdown 形式で `planters.louge_content` に保存 |
| BR-02-5 | 反論/例外セクションは必須（条件B の counterarguments で担保済み） |
| BR-02-6 | AI が議論の性質に応じて最適な構成を判断してよいが、6セクション構造は維持する |

---

## BR-03: 状態遷移（Louge 開花）

| ルール | 内容 |
|---|---|
| BR-03-1 | `sprout` → `louge`: 条件A AND 条件B 突破時に即座に遷移 |
| BR-03-2 | 状態遷移時に `progress` を 1.0 に設定 |
| BR-03-3 | 状態遷移後、`louge_content` が `NULL` の間は「開花処理中」（bloom_pending）|
| BR-03-4 | `louge_generated_at` は記事生成完了時刻を記録 |
| BR-03-5 | `louge` → 他の状態への逆遷移は不可（archived を除く） |

---

## BR-04: 開花後の Log 投稿制限

| ルール | 内容 |
|---|---|
| BR-04-1 | Planter が `louge` 状態の場合、新規 Log 投稿を禁止する |
| BR-04-2 | API で `status == "louge"` のチェックを行い、403 を返す |
| BR-04-3 | フロントエンドでは Log 投稿バーを非表示にする |

---

## BR-05: インサイトスコア計算

| ルール | 内容 |
|---|---|
| BR-05-1 | Louge 開花時に1回のみ計算。開花後の再計算は行わない |
| BR-05-2 | AI（Vertex AI）が各 Log の Louge 記事への貢献度を 0.0〜1.0 で評価 |
| BR-05-3 | Seed 投稿者には固定ボーナス 1.0 を付与（reason: `seed_author`） |
| BR-05-4 | AI 生成 Log（`is_ai_generated=True`）は評価対象外 |
| BR-05-5 | 同一ユーザーの複数 Log は各 Log ごとに個別評価し、合算 |
| BR-05-6 | `insight_score_events` に各評価を個別レコードとして記録 |
| BR-05-7 | `users.insight_score` に score_delta を加算（累積値） |

---

## BR-06: 通知イベント

| ルール | 内容 |
|---|---|
| BR-06-1 | 開花時に `louge_bloomed` タイプの通知を `notifications` テーブルに記録 |
| BR-06-2 | 通知の対象: Planter の Seed 投稿者 + 全 Log 投稿者（重複排除） |
| BR-06-3 | 通知送信（メール・プッシュ等）は MVP では行わない。DB 記録のみ |

---

## BR-07: 開花中 UX（ポーリング）

| ルール | 内容 |
|---|---|
| BR-07-1 | フロントエンドは `status == "louge"` かつ `louge_content == null` を「bloom_pending」と判定 |
| BR-07-2 | bloom_pending 時にポーリング開始（間隔: 3秒 → 5秒 → 10秒） |
| BR-07-3 | 60秒タイムアウト後、ポーリング停止しメッセージ表示 |
| BR-07-4 | `louge_content` が存在するようになったら記事を表示しポーリング停止 |

---

## BR-08: Louge コピー機能

| ルール | 内容 |
|---|---|
| BR-08-1 | Louge 記事本文（Markdown）のみをクリップボードにコピー |
| BR-08-2 | Seed 本文・Log 一覧はコピー対象に含めない |
| BR-08-3 | コピー完了時にトースト通知を表示 |
