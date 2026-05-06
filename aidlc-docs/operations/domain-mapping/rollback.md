# ロールバック手順

> ドメイン切替後に致命的な障害（SSL 発行失敗、CORS 全滅、Auth リダイレクトループなど）が発生した場合に、旧 `*.run.app` URL に瞬時に戻す手順。

---

## ロールバック判断基準

以下のいずれかに該当する場合、本手順を即座に実行する:

- `https://workslogue.com` が 5 分以上応答なし
- SSL 証明書エラーで全ブラウザがアクセス不可
- ログインフロー全体が破綻（Supabase Auth リダイレクトループ等）
- API CORS エラーで Web から API が一切叩けない

---

## Phase 別ロールバック

### Phase 3 まで（DNS 設定段階）— 影響なし

DNS にレコードを登録しただけの段階。**何もしなくても旧 URL は生きている**。
DNS レコードを削除 / 旧値に戻すだけで完全復旧。

```bash
# DNS プロバイダの管理画面で:
# - apex の A/AAAA レコード 8 件を削除
# - api の CNAME を削除
```

旧テストアカウント / 開発リンクは `*.run.app` のまま動いているはず。

---

### Phase 4 以降（環境変数切替後）— 要 revert

CD で `cd.yml` を切り替えた後に問題が発覚した場合。

#### 4-A. `cd.yml` の revert

```bash
# 直近の CORS_ORIGINS / NEXT_PUBLIC_API_URL 切替コミットを特定
git log --oneline -- .github/workflows/cd.yml | head -5

# revert コミットを作成
git revert <commit_sha>

# push して CD を起動
git push origin main
```

CD 完了後、Cloud Run のサービスは旧 URL の CORS / API URL に戻る。

#### 4-B. Supabase Auth Site URL を旧値に戻す

Supabase Console → Authentication → URL Configuration:

- Site URL: `https://works-logue-web-369619150476.asia-northeast1.run.app`
- Redirect URLs: 旧 `https://works-logue-web-369619150476.asia-northeast1.run.app/**` を有効化

**重要**: Phase 1.3 で取得したスクリーンショットの設定値を正として戻すこと。

#### 4-C. domain mappings の削除（任意）

問題が DNS / SSL 由来でなくアプリ層なら、mapping は残したままでも OK。
DNS 起因なら mapping を削除して Search Console 検証からやり直す。

```bash
gcloud run domain-mappings delete \
  --domain=workslogue.com \
  --region=asia-northeast1

gcloud run domain-mappings delete \
  --domain=api.workslogue.com \
  --region=asia-northeast1
```

#### 4-D. DNS レコードの後始末（任意）

- 旧 URL に完全に戻す場合: apex の A/AAAA、api の CNAME を全削除
- 後日リトライする場合: DNS は残しておく（mapping 削除済みでも DNS だけなら無害）

---

## ロールバック後の検証

`verification.md` の Section 1〜5 を旧 URL（`*.run.app`）で再実行し、全てパスすることを確認。

---

## 復旧後のフォローアップ

ロールバック後は audit.md に以下を記録:

```markdown
## Operations: Domain Mapping ロールバック
**Timestamp**: {ISO timestamp}
**Trigger**: {ロールバック理由 — どの検証ステップで何が失敗したか}
**Actions**: {実行した手順 — 4-A / 4-B / 4-C / 4-D のうちどれを実施したか}
**Status**: 旧 URL で稼働再開 / domain mapping は {維持 / 削除}
**Next Steps**: {根本原因調査と再切替計画}
```

---

## よくある原因と対処

| 症状 | 原因 | 対処 |
|---|---|---|
| SSL 証明書発行に 1 時間以上かかる | CAA レコードが Let's Encrypt を拒否 | CAA を空にする or `0 issue "letsencrypt.org"` を追加 |
| ブラウザは OK だが API CORS NG | `cd.yml` で旧 URL を `CORS_ORIGINS` に残し忘れた | 旧 URL も `CORS_ORIGINS` にカンマ区切りで追加（移行期間中） |
| Supabase Auth がリダイレクトループ | Site URL が新旧不一致 | Site URL を 1 つに統一、Redirect URLs に両方を許可 |
| apex だけ繋がらない（api は OK） | apex の A/AAAA を CNAME で設定してしまった | A/AAAA に直す（CNAME は apex 不可） |
| Cloudflare 経由で繋がらない | プロキシ ON（orange cloud） | DNS only（grey cloud）に変更 |
