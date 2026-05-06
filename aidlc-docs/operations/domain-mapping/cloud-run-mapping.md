# Cloud Run domain mappings — 操作手順

> **対象**: `works-logue-api` / `works-logue-web`（asia-northeast1）
>
> **方式**: `gcloud run domain-mappings` コマンドで作成。Google managed certificate（Let's Encrypt + GTS）を自動発行。

---

## 1. ドメイン所有権の検証

Cloud Run domain mappings はマッピング作成前に **Search Console でドメイン所有権を検証する** 必要がある。

### 手順

1. https://search.google.com/search-console を開き、Google アカウント（GCP プロジェクトのオーナー）でログイン
2. 「プロパティを追加」→「ドメイン」を選択し `workslogue.com` を入力
3. 表示される TXT レコード（例: `google-site-verification=xxxxxxxxxx`）を DNS の `@`（apex）に追加
4. `dig workslogue.com TXT +short` で伝播確認
5. Search Console で「確認」をクリック

検証が完了すると、`gcloud` から domain mappings を作成できるようになる。

---

## 2. domain mapping の作成

### 2.1 API（`api.workslogue.com`）

```bash
gcloud run domain-mappings create \
  --service=works-logue-api \
  --domain=api.workslogue.com \
  --region=asia-northeast1
```

出力例:

```
Mapping for [api.workslogue.com] to [works-logue-api] created.

To complete the mapping, please add the following DNS records:
  NAME              TYPE    DATA
  api               CNAME   ghs.googlehosted.com.
```

### 2.2 Web (apex `workslogue.com`)

```bash
gcloud run domain-mappings create \
  --service=works-logue-web \
  --domain=workslogue.com \
  --region=asia-northeast1
```

出力例:

```
Mapping for [workslogue.com] to [works-logue-web] created.

To complete the mapping, please add the following DNS records:
  NAME    TYPE    DATA
  @       A       216.239.32.21
  @       A       216.239.34.21
  @       A       216.239.36.21
  @       A       216.239.38.21
  @       AAAA    2001:4860:4802:32::15
  @       AAAA    2001:4860:4802:34::15
  @       AAAA    2001:4860:4802:36::15
  @       AAAA    2001:4860:4802:38::15
```

> **注意**: 上記の値は出力例。実際は環境ごとに微妙に異なる場合があるので **必ず gcloud の出力値を使うこと**。

---

## 3. DNS への登録

`aidlc-docs/operations/domain-mapping/dns-records.md` の表に従い、ドメインレジストラ / DNS プロバイダの管理画面から登録する。

---

## 4. SSL 証明書の発行確認

DNS 伝播後、Google が自動で Let's Encrypt 証明書を発行する。発行完了まで通常 15〜60 分かかる。

```bash
gcloud run domain-mappings describe \
  --domain=workslogue.com \
  --region=asia-northeast1 \
  --format='value(status.conditions)'

gcloud run domain-mappings describe \
  --domain=api.workslogue.com \
  --region=asia-northeast1 \
  --format='value(status.conditions)'
```

`CertificateProvisioned: True` かつ `Ready: True` になればマッピング完了。

ブラウザで `https://workslogue.com` にアクセスして錠アイコンが緑なら成功。

---

## 5. トラブルシューティング

### ❌ `Domain ownership verification required`

→ Section 1 の Search Console での検証が完了していない。検証完了後に mapping を再実行。

### ❌ DNS 伝播後も `CertificateProvisioned: False` のまま

- CAA レコードが `letsencrypt.org` / `pki.goog` を拒否していないか確認
- AAAA レコードが間違っていないか確認（IPv6 が誤っていると証明書発行に失敗するケースあり）
- `gcloud run domain-mappings describe` で `Reason` フィールドを確認

### ❌ apex に CNAME を設定してしまった

apex に CNAME は設定不可（DNS RFC 違反 / プロバイダによっては許可するが推奨されない）。A/AAAA レコードに直す。

### ❌ Cloudflare の orange cloud が ON

Cloudflare のプロキシを通すと SSL 発行が失敗する。**DNS only（grey cloud）** に変更。

---

## 6. mapping の削除（ロールバック）

```bash
gcloud run domain-mappings delete \
  --domain=workslogue.com \
  --region=asia-northeast1

gcloud run domain-mappings delete \
  --domain=api.workslogue.com \
  --region=asia-northeast1
```

DNS レコードも合わせて削除 / 旧値に戻す。詳細: `rollback.md`
