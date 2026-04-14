# U4 Louge - Business Logic Model

## 概要

U4 は以下の3つのフローで構成される:
1. **開花フロー**: ScorePipeline から LougeGenerator を起動し、Louge 記事を生成
2. **インサイトスコア計算フロー**: 開花時に各 Log 投稿者の貢献度を算出
3. **Louge 表示フロー**: Planter が `louge` 状態のときの表示切替・ポーリング

---

## フロー1: 開花フロー（ScorePipeline → LougeGenerator）

### トリガー

ScorePipeline の `_execute_inner()` で `passed_maturity=True`（条件A AND 条件B 突破）が確定した時点。

### シーケンス

```
BackgroundTasks: ScorePipeline._execute_inner()
    |-> ScoreEngine.evaluate_structure()         ← 条件A
    |-> ScoreEngine.evaluate_maturity()           ← 条件B（条件A充足時のみ）
    |-> passed_maturity == True?
    |     |-> YES:
    |     |     |-> Planter.status = "louge" に更新（bloom_pending = True）
    |     |     |-> Planter.progress = 1.0
    |     |     |-> Snapshot 保存 + Planter 更新 + commit
    |     |     |-> LougeGenerator.bloom(planter_id)    ← 新規: 開花処理
    |     |         |-> LougeGenerator.generate()       ← Vertex AI で記事生成
    |     |         |-> Planter.louge_content = 記事    ← Markdown 保存
    |     |         |-> Planter.louge_generated_at = now
    |     |         |-> InsightScoreCalculator.calculate()
    |     |         |-> InsightScoreCalculator.apply()
    |     |         |-> NotificationRepository.create()  ← louge_bloomed 通知
    |     |         |-> commit
    |     |-> NO: （既存: AIFacilitator or スナップショット保存のみ）
```

### 設計判断

- ScorePipeline 内で `passed_maturity=True` を検知した時点で、同一 BackgroundTask 内で LougeGenerator.bloom() を呼ぶ
- Planter の `status` を先に `louge` に更新し、`louge_content` が `None` の間はフロントエンドで「開花中...」を表示（bloom_pending 状態）
- LougeGenerator.bloom() が完了すると `louge_content` が埋まり、フロントエンドのポーリングで検知される
- LougeGenerator.bloom() が失敗しても Planter の status は `louge` のまま。`louge_content` が `None` のままなので再試行可能

---

## フロー2: Louge 記事生成（LougeGenerator.generate）

### 入力

- Planter（Seed: タイトル + 本文）
- Log 群（全 Log、ユーザー情報付き）
- 条件A の構造パーツ情報

### Vertex AI 呼び出し

- **モデル**: `gemini-2.5-flash`（MODEL_STANDARD）
- **レスポンス形式**: JSON（`response_mime_type: application/json`）
- **出力構造**:

```json
{
  "pattern_name": "パターン名",
  "context": "状況セクション（Markdown）",
  "problem": "問題セクション（Markdown）",
  "solution": "解決策セクション（Markdown）",
  "counterarguments": "反論/例外セクション（Markdown）",
  "references": [
    {
      "log_index": 3,
      "user_name": "@田中",
      "excerpt": "引用スニペット"
    }
  ]
}
```

### Markdown 組み立て

LougeGenerator が JSON レスポンスから Markdown 記事を組み立てる:

```markdown
# {pattern_name}

## 状況（Context）
{context}

## 問題（Problem）
{problem}

## 解決策（Solution）
{solution}

## 反論・例外（Counterarguments）
{counterarguments}

---

## 出典
[1] @田中 - 「引用スニペット...」
[2] @佐藤 - 「引用スニペット...」
...
```

- 脚注方式で出典を文末にまとめる（Q6 回答: C）
- AI に記事本文中で `[1]` `[2]` のように脚注番号を使わせる

### エラーハンドリング

- Vertex AI 呼び出し失敗時: ログ出力のみ。`louge_content` は `None` のまま
- JSON パースエラー: 同上
- リトライは行わない（次回ページ表示時に管理者が手動再実行する想定）

---

## フロー3: インサイトスコア計算（InsightScoreCalculator）

### トリガー

LougeGenerator.bloom() 内、記事生成完了後に実行。

### calculate(planter_id)

1. Planter の全 Log を取得（AI 生成 Log は除外）
2. 生成された Louge 記事（Markdown）と各 Log を Vertex AI に送信
3. AI が各 Log の貢献度を 0.0〜1.0 で評価

**Vertex AI 呼び出し**:
- **モデル**: `gemini-2.5-flash`（MODEL_STANDARD）
- **出力形式**:

```json
{
  "evaluations": [
    {"log_id": "xxx", "score": 0.85, "reason": "解決策の核心を提供"},
    {"log_id": "yyy", "score": 0.4, "reason": "状況説明に貢献"},
    ...
  ]
}
```

4. 各 Log の `score` を `InsightScoreEvent` として記録

### apply(events)

1. `InsightScoreEvent` を `insight_score_events` テーブルに一括 INSERT
2. ユーザーごとに `score_delta` を集計
3. 各ユーザーの `users.insight_score` に加算（`UPDATE users SET insight_score = insight_score + delta`）

### スコア算出ルール

- Seed 投稿者: 固定ボーナス 1.0（Louge 開花のきっかけを作った貢献）
- Log 投稿者: AI 評価スコア（0.0〜1.0）をそのまま加算
- AI 生成 Log は対象外（`is_ai_generated=True` を除外）
- 同一ユーザーが複数 Log を投稿した場合、各 Log ごとに個別評価

---

## フロー4: Planter 詳細取得（Louge 状態）

### API: `GET /api/v1/planters/{id}`

既存の Planter 詳細取得エンドポイントを拡張。

**レスポンスに追加するフィールド**:

```json
{
  "status": "louge",
  "louge_content": "# パターン名\n## 状況...",
  "louge_generated_at": "2026-04-15T12:00:00Z",
  "bloom_pending": false
}
```

- `bloom_pending` の判定: `status == "louge" AND louge_content IS NULL`
- フロントエンドは `bloom_pending=true` の場合にポーリングを開始

### API: `GET /api/v1/planters/{id}/contributors`（新規）

開花した Planter の貢献者一覧を取得。

```json
{
  "contributors": [
    {
      "user_id": "xxx",
      "display_name": "田中太郎",
      "avatar_url": "...",
      "insight_score_earned": 0.85,
      "log_count": 3,
      "is_seed_author": false
    }
  ]
}
```

- `insight_score_events` テーブルから当該 Planter の貢献者を集計
- Seed 投稿者は `is_seed_author=true` で区別
- `insight_score_earned` はその Planter での獲得スコア合計

---

## フロー5: 開花ポーリング

### フロントエンド動作

1. Log 投稿後、スコアポーリング開始（既存 U3 の仕組み）
2. スコアポーリングの結果で `status: "louge"` かつ `bloom_pending: true` を検知
3. **開花ポーリングに切替**: `GET /api/v1/planters/{id}` を定期的にチェック
4. `bloom_pending: false`（= `louge_content` が存在）になったら記事を表示
5. ポーリング間隔: 3秒 → 5秒 → 10秒（U3 と同じ戦略）

### タイムアウト

- 60秒経過しても `bloom_pending` が解消しない場合、「記事生成に時間がかかっています。しばらく後にもう一度アクセスしてください」のメッセージを表示
- ポーリングを停止
