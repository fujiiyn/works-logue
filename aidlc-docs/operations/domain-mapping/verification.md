# 疎通確認・検証手順

> Phase 5（実行プラン参照）で実施。**全項目 PASS** で本ステージ完了とする。

---

## 1. DNS 解決の確認

```bash
# apex
dig +short workslogue.com A
dig +short workslogue.com AAAA

# subdomain
dig +short api.workslogue.com CNAME
dig +short api.workslogue.com A   # CNAME 追跡後の最終 IP
```

**期待**:
- apex: A / AAAA とも 4 件返る（gcloud 出力の値と一致）
- api: CNAME = `ghs.googlehosted.com.`、追跡後 A レコードが返る

---

## 2. SSL 証明書の確認

```bash
# 証明書発行元 / 有効期限
echo | openssl s_client -servername workslogue.com -connect workslogue.com:443 2>/dev/null | openssl x509 -noout -issuer -dates -subject
echo | openssl s_client -servername api.workslogue.com -connect api.workslogue.com:443 2>/dev/null | openssl x509 -noout -issuer -dates -subject
```

**期待**:
- `issuer` が Let's Encrypt または GTS（Google Trust Services）
- `subject` の CN が対応するドメイン
- 有効期限が約 90 日後

PowerShell の代替:

```powershell
# 簡易: HTTPS でレスポンスが返るか
Invoke-WebRequest https://workslogue.com -Method Head
Invoke-WebRequest https://api.workslogue.com/healthz -Method Head
```

---

## 3. Cloud Run mapping の状態

```bash
gcloud run domain-mappings list --region=asia-northeast1
```

**期待**: 両ドメインが `READY: True` で表示される。

---

## 4. アプリケーション疎通

### 4.1 API ヘルスチェック

```bash
curl -sS https://api.workslogue.com/healthz
# → {"status":"ok"} 等の正常レスポンス
```

### 4.2 Web トップページ

```bash
curl -sS -o /dev/null -w "%{http_code}\n" https://workslogue.com/
# → 200
```

### 4.3 Web → API CORS 確認

ブラウザで `https://workslogue.com/` を開き、開発者ツール → Network タブで:

- API リクエスト先が `https://api.workslogue.com/...` になっている
- `Access-Control-Allow-Origin: https://workslogue.com` がレスポンスヘッダにある
- CORS エラー（コンソール赤）が出ていない

---

## 5. E2E ゴールデンパス

ブラウザで以下を順に実行:

1. **未ログイン**: `https://workslogue.com/` を開き、Home フィードが表示される
2. **Login**: `tanaka@test.works-logue.com / TestPass123!` でログイン成功（Supabase Auth リダイレクトが新ドメインに戻る）
3. **Seed 投稿**: `/seed/new` から新規 Seed を投稿し、`/p/{id}` に遷移して表示される
4. **Log 投稿**: 同 Seed に Log を投稿し、リアルタイムにスコアが更新される
5. **Logout**: 右上メニューからログアウトし、未ログイン状態に戻る

**期待**: 全ステップでエラーなく動作。コンソールに CORS / 401 / 500 が出ない。

---

## 6. 構造化ログの確認

```
gcloud logging read 'resource.labels.service_name="works-logue-api" AND jsonPayload.path="/healthz"' --limit=5 --format=json
```

**期待**: `request_id` が付与され、構造化 JSON で出力されている（U7 の RequestIdMiddleware が機能）。

---

## 7. Supabase Auth リダイレクト

1. `https://workslogue.com/login` で「マジックリンクで送る」を実行
2. メール本文のリンク URL が `https://workslogue.com/...` で始まる
3. クリック後、`https://workslogue.com/` にログイン状態で着地

**NG パターン**: リンクが `*.run.app` に向いている → Supabase Auth の Site URL 設定が古い。Phase 4.4 を再確認。

---

## 8. パフォーマンス / 体感

- Web 初回表示の TTFB が 1 秒以内（CDN なし、Cold start 考慮）
- API レスポンス（GET /seeds 等）が 500 ms 以内

問題があれば `min-instances` を 1 に上げて Cold start を回避することを検討（料金とのトレードオフ）。

---

## 検証結果テンプレート

| 項目 | 結果 | 備考 |
|---|---|---|
| 1. DNS 解決 | ☐ |  |
| 2. SSL 証明書 | ☐ |  |
| 3. mapping 状態 | ☐ |  |
| 4.1 API healthz | ☐ |  |
| 4.2 Web トップ | ☐ |  |
| 4.3 CORS | ☐ |  |
| 5. E2E ゴールデンパス | ☐ |  |
| 6. 構造化ログ | ☐ |  |
| 7. Auth リダイレクト | ☐ |  |
| 8. パフォーマンス | ☐ |  |
