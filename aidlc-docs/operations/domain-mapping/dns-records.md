# DNS レコード仕様

## 前提

`workslogue.com` の権威 DNS（例: お名前.com / Cloudflare / Route 53 / Cloud DNS など）に、以下のレコードを設定する。具体的な IP アドレスや CNAME ターゲットは Cloud Run 側で決まるため、**`gcloud run domain-mappings create` の出力で示された値を必ず使うこと**。本ドキュメントは構造とサンプル値の説明用。

---

## レコード一覧

### apex (`workslogue.com`) → `works-logue-web`

apex（zone apex / root domain）は CNAME を使えない（RFC 1034 / 2181）ため、A/AAAA レコードを直接設定する。Cloud Run domain mappings は IPv4 4 件 + IPv6 4 件の anycast IP を返す。

| Type | Name | TTL | Value（例 — 実際は gcloud 出力に従う） |
|---|---|---|---|
| A | `@` (apex) | 300 | `216.239.32.21` |
| A | `@` | 300 | `216.239.34.21` |
| A | `@` | 300 | `216.239.36.21` |
| A | `@` | 300 | `216.239.38.21` |
| AAAA | `@` | 300 | `2001:4860:4802:32::15` |
| AAAA | `@` | 300 | `2001:4860:4802:34::15` |
| AAAA | `@` | 300 | `2001:4860:4802:36::15` |
| AAAA | `@` | 300 | `2001:4860:4802:38::15` |

> **TTL**: 移行期間は 300 秒（5 分）に下げる。安定後 3600〜86400 秒に戻して可。

### `api.workslogue.com` → `works-logue-api`

サブドメインは CNAME 可能。Cloud Run の標準 CNAME ターゲットは `ghs.googlehosted.com.` だが、これも `gcloud` 出力で必ず確認すること。

| Type | Name | TTL | Value |
|---|---|---|---|
| CNAME | `api` | 300 | `ghs.googlehosted.com.` |

### `www.workslogue.com`（任意・推奨）

`www` 経由のアクセスを apex に集約する。

**選択肢 A — DNS の URL 転送機能で 301**（プロバイダ依存。お名前.com 等が提供）

**選択肢 B — もう 1 つの Cloud Run domain mapping**

Cloud Run の追加 mapping を `www.workslogue.com` で作成し、Web 側で middleware（Next.js `middleware.ts`）で `host === 'www.workslogue.com'` なら 301 で apex に飛ばす。MVP では選択肢 A の DNS 転送で十分。

| Type | Name | TTL | Value |
|---|---|---|---|
| CNAME | `www` | 300 | `ghs.googlehosted.com.`（選択肢 B の場合） |

---

## 検証コマンド

```bash
# A レコード
dig +short workslogue.com A

# AAAA レコード
dig +short workslogue.com AAAA

# CNAME
dig +short api.workslogue.com CNAME

# 名前解決一気通貫（CNAME → A まで追跡）
dig +trace api.workslogue.com
```

PowerShell の場合:

```powershell
Resolve-DnsName workslogue.com -Type A
Resolve-DnsName api.workslogue.com -Type CNAME
```

---

## 既存レコードの確認・退避

新ドメインを設定する前に、既存の TXT/MX/SPF レコードを退避する（メール運用や SPF 設定がある場合は壊さない）。

```bash
dig workslogue.com TXT +short
dig workslogue.com MX +short
```

特に以下は壊さないように残す:
- メール用 `MX`、`TXT (SPF)`、`TXT (DKIM)`、`TXT (DMARC)`
- ドメイン認証用 `TXT`（Search Console 等）

---

## 注意点

- **CAA レコード**: 既存に `CAA` がある場合、`letsencrypt.org` を許可する必要がある。Google managed cert は Let's Encrypt + GTS の混合のため、空（CAA なし）か `0 issue "letsencrypt.org"` `0 issue "pki.goog"` を含めること。
- **DNSSEC**: Cloud Run domain mappings は DNSSEC でも問題なく動くが、設定変更時は鍵のロールに注意。
- **CDN を後段に挟む場合**: Cloudflare をオレンジクラウド（プロキシ ON）にすると、Cloud Run 側の SSL 証明書発行が失敗する。MVP は **DNS only（グレークラウド）** で運用する。
