# Domain Mapping — 実行プラン

> **目的**: Cloud Run の `*.run.app` URL から本番ドメイン `workslogue.com` への切替を、ダウンタイムなく安全に実施する。
>
> **方式**: Cloud Run domain mappings（asia-northeast1 GA）。Google managed certificate（Let's Encrypt 自動更新）を利用する。

---

## 決定事項（2026-05-04）

| 項目 | 値 |
|---|---|
| ベースドメイン | `workslogue.com` |
| Web (apex) | `https://workslogue.com` → `works-logue-web` |
| API (subdomain) | `https://api.workslogue.com` → `works-logue-api` |
| `www.workslogue.com` | 301 リダイレクト → apex（後続検討） |
| GCP Region | `asia-northeast1` |
| GCP Project | `${GCP_PROJECT_ID}`（GitHub Secrets 参照） |
| SSL | Cloud Run 自動発行・更新（Google managed） |
| ロードバランサ | 採用しない（MVP コスト最適化） |

---

## 前提条件チェック

- [ ] `workslogue.com` を所有しており、DNS の権威ネームサーバーを操作できる
- [ ] GCP プロジェクトで Cloud Run / Cloud DNS（任意）への権限を持つ IAM が利用可能
- [ ] Cloud Run domain mappings を使う前提で、ドメイン所有権を Search Console で検証済み（または検証可能）
- [ ] 既存サービスは稼働中: `works-logue-api`, `works-logue-web`（asia-northeast1）
- [ ] Supabase プロジェクトのコンソールにアクセス可能（Auth Site URL の更新が必要なため）

---

## 実行ステップ

### Phase 1: 事前準備

- [ ] **1.1** `workslogue.com` の所有権を Google Search Console で検証
  - 参照: `aidlc-docs/operations/domain-mapping/cloud-run-mapping.md` §1
- [ ] **1.2** DNS の現在の TTL を確認し、必要なら 300 秒に下げて伝播を高速化
- [ ] **1.3** Supabase Auth → Authentication → URL Configuration の現値をスクリーンショット保存（ロールバック用）
- [ ] **1.4** GitHub Secrets に既存値（CORS_ORIGINS / NEXT_PUBLIC_API_URL に相当する値）が無いこと、もしくは現行値を控える

### Phase 2: Cloud Run domain mapping 作成

- [ ] **2.1** API: `gcloud run domain-mappings create --service=works-logue-api --domain=api.workslogue.com --region=asia-northeast1`
- [ ] **2.2** Web (apex): `gcloud run domain-mappings create --service=works-logue-web --domain=workslogue.com --region=asia-northeast1`
- [ ] **2.3** 上記コマンドの出力に表示される DNS レコード（A/AAAA × 4 + CNAME）を控える
  - 詳細: `aidlc-docs/operations/domain-mapping/dns-records.md`

### Phase 3: DNS レコード設定

- [ ] **3.1** apex 用 A レコード 4 本（IPv4）を登録
- [ ] **3.2** apex 用 AAAA レコード 4 本（IPv6）を登録
- [ ] **3.3** `api` の CNAME → `ghs.googlehosted.com.` を登録
- [ ] **3.4** `dig +short workslogue.com A` / `dig +short api.workslogue.com CNAME` で伝播を確認
- [ ] **3.5** `gcloud run domain-mappings describe` で `CertificateProvisioned: True` になるまで待機（最大30〜60分）

### Phase 4: アプリ側の環境変数切替

> **重要**: DNS が伝播し SSL 証明書が発行された後に実施する。先に切ると CORS で失敗してダウンする。

- [ ] **4.1** `.github/workflows/cd.yml` の `CORS_ORIGINS` を `https://workslogue.com` に変更（必要なら `https://www.workslogue.com` も追加）
- [ ] **4.2** 同 workflow の `--build-arg NEXT_PUBLIC_API_URL=https://api.workslogue.com` に変更
- [ ] **4.3** `git commit && git push origin main` で CD を起動し、Cloud Run に反映
- [ ] **4.4** Supabase Auth → URL Configuration:
  - Site URL: `https://workslogue.com`
  - Redirect URLs に `https://workslogue.com/**` を追加
  - 旧 `https://works-logue-web-369619150476.asia-northeast1.run.app/**` は **移行期間中は残す**

### Phase 5: 検証

詳細手順: `aidlc-docs/operations/domain-mapping/verification.md`

- [ ] **5.1** `curl -I https://workslogue.com` が 200 / SSL 有効
- [ ] **5.2** `curl -I https://api.workslogue.com/healthz` が 200
- [ ] **5.3** ブラウザで Login → Seed 投稿 → Log 投稿の golden path E2E
- [ ] **5.4** 開発者ツール Network タブで CORS エラーが出ないこと
- [ ] **5.5** Supabase Auth でメールマジックリンクのリダイレクト先が新ドメインに到達

### Phase 6: 旧 URL のクリーンアップ（任意・1〜2週間後）

- [ ] **6.1** Supabase Auth Redirect URLs から旧 `*.run.app` を削除
- [ ] **6.2** `cd.yml` の `CORS_ORIGINS` から旧 URL を削除（4.1 で残していた場合）
- [ ] **6.3** Cloud Run サービスは残す（domain mapping のバックエンドのため削除不可）

---

## ロールバック条件と手順

詳細: `aidlc-docs/operations/domain-mapping/rollback.md`

- **Phase 3 まで**: DNS レコードを未登録 / 旧値に戻すだけ。切替前の状態に瞬時に復旧可能。
- **Phase 4 以降**: `cd.yml` を revert + `git push` で旧 URL に戻す。Supabase Auth の Site URL も旧値に戻す。

---

## ステージ完了条件

- 上記 Phase 1〜5 のチェックボックスが全て `[x]`
- `https://workslogue.com` と `https://api.workslogue.com` が安定稼働
- aidlc-state.md の Domain Mapping を `[x]` にマーク
- audit.md にステージ完了ログを追記

---

## 付録 A: Phase 4.1 / 4.2 — `cd.yml` 差分（cutover 時に適用）

> **適用タイミング**: Phase 3（DNS 伝播 + SSL 発行）完了後。先に適用すると Web→API の CORS が落ちて本番ダウン。

### A.1 API ジョブの `CORS_ORIGINS` 切替

`.github/workflows/cd.yml` の `deploy-api` ジョブ:

```diff
           CORS_ORIGINS=https://works-logue-web-369619150476.asia-northeast1.run.app"
+          CORS_ORIGINS=https://workslogue.com,https://works-logue-web-369619150476.asia-northeast1.run.app"
```

> **移行期間中**は新旧両方を許可（カンマ区切り）。Phase 6 のクリーンアップで旧 URL を削除。
> `www.workslogue.com` を 301 でなく実体として運用する場合はそれも追加する。

### A.2 Web ジョブの `NEXT_PUBLIC_API_URL` 切替

`.github/workflows/cd.yml` の `deploy-web` ジョブ:

```diff
-            --build-arg NEXT_PUBLIC_API_URL=https://works-logue-api-369619150476.asia-northeast1.run.app \
+            --build-arg NEXT_PUBLIC_API_URL=https://api.workslogue.com \
```

> こちらは build-time の値（`NEXT_PUBLIC_*` は静的に焼き込まれる）。1 つに切替で OK。

### A.3 適用後の確認

1. `git push origin main` → CD のログを確認（API ジョブ → Web ジョブの順に成功）
2. Cloud Run コンソールで `works-logue-api` の環境変数 `CORS_ORIGINS` が新値になっている
3. `https://workslogue.com` をブラウザで開き、Network タブで API リクエストが `https://api.workslogue.com/...` に飛び、200 で返る

---

## 付録 B: Supabase Auth URL Configuration の更新値

Supabase Console → Authentication → URL Configuration:

| 項目 | 旧 | 新（cutover 後） |
|---|---|---|
| Site URL | `https://works-logue-web-369619150476.asia-northeast1.run.app` | `https://workslogue.com` |
| Redirect URLs | `https://works-logue-web-369619150476.asia-northeast1.run.app/**` | `https://workslogue.com/**`<br>（移行期間中は旧も併記） |

> Redirect URLs は配列なので、移行期間中は新旧両方を登録。Phase 6 で旧を削除。
