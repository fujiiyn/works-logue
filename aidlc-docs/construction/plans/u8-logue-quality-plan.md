# U8 Logue 品質改善 — 計画

- **作成日**: 2026-10-03
- **ブランチ**: `feat/logue-quality-improvements`
- **位置づけ**: U1〜U7 完了後の改善。既存ユニットの境界内の変更なので、Application Design と Units Generation は省略する。要件と計画をこの 1 ファイルにまとめ、承認後に実装する。

---

## 1. 要件

| # | 要件 | 背景 |
|---|---|---|
| R1 | 開花の成熟度基準を 0.85 から 0.9 に上げる | Log が少ないうちに開花すると記事の内容が薄くなり、AI が一般論で埋める余地が大きくなる |
| R2 | 開花済みの Logue ページを開いたとき、ページ上部（タイトル）から表示する | 現在はページ下部までスクロールした状態で表示される |
| R3 | スマホで Log 投稿ボックスを使いやすくする（入力量に応じて高さが伸びる、下部の余白を詰める） | 検証で「スマホでは投稿画面が小さく使いづらい」という声があった |
| R4 | Logue のパターン名を、テーマの言い換えではなく解決の本質を表す名前にする | 現在は「限られた時間での業務効率化」のようなテーマ名になっている |

### 対象外

- 既存 Logue を再生成する仕組みと、Logue の版の履歴管理（別途検討）
- 「限られた時間での業務効率化」以外の既存 Logue のパターン名変更

---

## 2. 決定事項

| 項目 | 決定 | 理由 |
|---|---|---|
| R1 の方式 | 成熟度の基準値を上げる。最低 Log 数の条件は追加しない | ユーザー判断 |
| R1 の副作用 | 投稿者が 1 人だけの Seed は開花しなくなる（多様性スコアが 0.7〜0.8 で頭打ちになるため。00012 で 0.85 に戻した理由と同じ） | 複数人の Log が集まってから開花させることが今回の意図なので、この挙動を受け入れる |
| R1 の既存 Logue | 開花済みの Logue はそのまま。開花判定のやり直しはしない | 付与済みのインサイトスコアや通知と矛盾させないため |
| R2 の範囲 | Logue ページでだけ、最新 Log への自動スクロールを止める。Seed ページは最新 Log から表示する現在の挙動のまま | Seed ページはチャット形式なので最新 Log から読む方が自然 |
| R3 の進め方 | 本番サイトをスマホ幅で開いてスクリーンショットを撮り、余白の箇所を特定してから直し方を決める | 余白がどこを指すかが未確定のため |
| R4 の置き換え対象 | 「限られた時間での業務効率化」の 1 件だけ。パターン名（`planters.logue_title`）だけを置き換え、本文は変えない | ユーザー判断。パターン名は本文と別の列なので、名前だけ変えても本文とずれない |
| R4 の置き換え条件 | 試し生成の候補をユーザーが確認し、承認した場合だけ置き換える。Claude が無断で変更しない | ユーザー判断 |
| R4 の元の名前の残し方 | 置き換え用 SQL と元に戻す SQL をセットで作り、リポジトリに残す | DB の構造を変えずに戻せる |
| R4 の試し生成の環境 | ローカルから本番 DB を SELECT だけで読み、個人用 ADC（`~/.config/gcloud-private/`）で `works-logue-493118` の Vertex AI を呼ぶ | 2026-10-03 に接続確認済み。会社用 ADC には触れない |

---

## 3. 実行ステップ

### Phase 1: R1 開花基準の引き上げ（完了）

- [x] Step 1: `test_settings_repository.py` の初期値の期待値を 0.9 に変更（Red を確認済み）
- [x] Step 2: `settings_repository.py` の `bloom_threshold` 初期値を 0.9 に変更
- [x] Step 3: `supabase/migrations/00017_bloom_threshold_to_0_9.sql` を新規作成（本番 DB の値を 0.9 に更新）
- [x] Step 4: `test_scores.py` の期待値を 0.9 に変更
- [x] Step 5: API テスト全件を実行して Pass を確認
- [x] Step 6: `docs/bloom-logic.md`（未コミット）の 0.85 の記載を 0.9 に更新し、副作用を追記する

### Phase 2: R2 Logue ページをタイトルから表示

- [x] Step 7: `components/log/LogThread.tsx` に、初回表示時に最新 Log へスクロールするかを指定する prop を追加する（初期値は現在の挙動と同じ「スクロールする」）
- [x] Step 8: `app/p/[id]/planter-detail-client.tsx` の Logue 表示側の `LogThread` で、スクロールしない指定を渡す
- [x] Step 9: Playwright E2E を追加する。Logue ページを開いたとき `window.scrollY` が 0 であること、Seed ページでは従来どおり下部にスクロールすることを確認する。テストデータの用意方法は、既存 E2E の実行環境を確認して決める

Phase 2 の E2E 結果（2026-10-05）: `apps/web/e2e/planter-initial-scroll.spec.ts` を追加。ローカルの API（本番 DB）と Web（ポート 3100）で実行し 2 件 Pass。修正前のコードでは Logue ページが 7594px 下までスクロールされて失敗することを確認。対象の Planter は環境変数 `E2E_LOGUE_PLANTER_ID` / `E2E_SEED_PLANTER_ID` で渡し、閲覧記録の POST はテスト内で横取りして DB に書き込まない。

### Phase 3: R3 スマホの投稿ボックス（保留: 後日 HTML モックで仕様を決める）

2026-10-03 の本番確認結果（Claude in Chrome、閲覧のみ）:
- 入力欄は初期 1 行（42px）、最大 5 行（120px）。文字サイズ 13px
- iPhone の Safari は 16px 未満の入力欄をタップすると自動で拡大するため、スマホで使いづらい原因の候補
- PC 幅では、Log が少ないページで最後の内容と投稿ボックスの間に約 170px の空白がある
- スマホ幅（Chrome で 500px）では目立つ余白はなかった。iPhone 実機特有の表示は未確認


- [x] Step 10: 本番サイトの Seed ページをスマホ幅（390px）で開き、スクリーンショットを撮る。閲覧のみで投稿はしない
- [ ] Step 11: 余白の箇所と直し方の案をスクリーンショット付きで提示し、ユーザーの承認を得る
- [ ] Step 12: `components/log/LogComposer.tsx` を修正する（入力欄の最大高さ、文字サイズ、余白）
- [ ] Step 13: Playwright でスマホ幅とPC幅のスクリーンショットを撮り、ユーザーが確認する

### Phase 4: R4 パターン名のプロンプト変更と試し生成

- [x] Step 14: `test_logue_generator.py` に、命名方針がプロンプトに含まれることのテストを追加する（Red）
- [x] Step 15: `services/logue_generator.py` の `LOGUE_SYSTEM_INSTRUCTION` に、パターン名の付け方を追加する（Green）
  - テーマの言い換えにしない。議論から導かれた解決の本質を名前にする
  - 短く、記憶に残る名前にする
  - 他のパターンと並べたときに違いがわかる名前にする
  - 例: 「限られた時間での業務効率化」ではなく「完璧より、届けるスピード」
- [x] Step 16: 試し生成スクリプト `apps/api/scripts/trial_pattern_name.py` を作る。対象 Logue の Seed と Log を本番 DB から SELECT だけで読み、新しいプロンプトで 3 回生成し、現在の名前と候補を並べて表示する。DB には書き込まない
- [x] Step 17: スクリプトを実行し、候補をユーザーに提示する
- [x] Step 18: ユーザーが候補を採用した場合、置き換え用 SQL と元に戻す SQL を `supabase/manual/` に作る。実行はユーザーが Supabase ダッシュボードで行う。不採用ならプロンプトを見直して Step 17 に戻る

Phase 4 の結果（2026-10-05）:
- プロンプトは v1〜v5 を試し、v5（解決策の考え方をキャッチーな一言で表す。「AよりB」の対比と読点を許可。命令形・禁止形は禁止）で確定
- 各版の比較は、試し生成スクリプトで本番の開花済み Logue 6 件に 3 回ずつ生成して行った（DB は読み取りのみ）
- 「限られた時間での業務効率化」は「雑務はAIに、時間は本質に」に置き換えることをユーザーが承認。SQL は `supabase/manual/20261005_rename_logue_title_c208e75e.sql`、戻す SQL は同名の `_revert.sql`。実行はユーザー
- 試し生成中に、Vertex AI の応答停止と JSON 読み取り失敗が見つかった。本番にも影響するため Issue #1 に記録（今回の範囲外）

### Phase 5: レビューと差分確認

- [x] Step 19: （ユーザー判断で省略、2026-10-05）`/pr-review-toolkit:review-pr`（code errors tests）でローカル差分をレビューし、信頼度 80 以上の指摘を解消する
- [x] Step 20: `aidlc-state.md` を更新する
- [ ] Step 21: 差分を hunk で表示し、ユーザーが確認する

---

## 4. 変更予定ファイル

| ファイル | 変更 |
|---|---|
| `apps/api/app/repositories/settings_repository.py` | 修正（実装済み） |
| `apps/api/app/tests/test_settings_repository.py` | 修正（実装済み） |
| `apps/api/app/tests/test_scores.py` | 修正（実装済み） |
| `supabase/migrations/00017_bloom_threshold_to_0_9.sql` | 新規（実装済み） |
| `docs/bloom-logic.md` | 数値の更新 |
| `apps/web/components/log/LogThread.tsx` | 修正 |
| `apps/web/app/p/[id]/planter-detail-client.tsx` | 修正 |
| `apps/web/components/log/LogComposer.tsx` | 修正 |
| `apps/web/e2e/` | E2E 追加 |
| `apps/api/app/services/logue_generator.py` | 修正 |
| `apps/api/app/tests/test_logue_generator.py` | 修正 |
| `apps/api/scripts/trial_pattern_name.py` | 新規 |
| `supabase/manual/`（採用時のみ） | 新規 |

---

## 5. デプロイ時の注意

- マイグレーション 00017 を本番に適用するまで、本番の基準値は 0.85 のまま。基準値は管理画面からも変更できる
- プロンプトの変更は、デプロイ後に開花する Logue にだけ効く
