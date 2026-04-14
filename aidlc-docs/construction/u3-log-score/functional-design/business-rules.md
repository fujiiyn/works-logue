# U3 Log & Score - Business Rules

## BR-01: Log 投稿の制約

| ルール | 内容 |
|---|---|
| 認証必須 | ログインユーザーのみ Log 投稿可能 |
| BAN チェック | BAN ユーザーは投稿不可（403） |
| Planter 状態チェック | `status='louge'` の Planter には投稿不可（開花済み） |
| Planter 状態チェック | `status='archived'` の Planter には投稿不可 |
| 本文制限 | 1〜5000文字 |
| ネスト制限 | 返信は1段のみ。parent_log_id の Log が既に返信の場合は拒否 |
| 返信の所属チェック | parent_log_id は同一 Planter 内の Log でなければならない |
| 自動フォロー | Log 投稿者はその Planter を自動フォロー（既存なら無視） |

---

## BR-02: Planter 状態遷移

### 遷移ルール

```
seed ──[BR-02a]--> sprout ──[BR-02b]--> louge
```

| ルール ID | 条件 | 遷移 |
|---|---|---|
| BR-02a | log_count >= 1（初回 Log 投稿時） | seed -> sprout |
| BR-02b | 条件A 完全充足 AND 条件B >= bloom_threshold | sprout -> louge（U4 で実装） |

### 不可逆ルール

- 状態遷移は一方向のみ（巻き戻し不可）
- `louge` -> `sprout` や `sprout` -> `seed` への逆遷移はシステムが許可しない

### Sprout サブステート

UI のビジュアル表現のみ。DB カラムとしては保存しない（progress から算出）。

| サブステート | 条件 | progress 範囲 |
|---|---|---|
| Sprout 1（芽） | Log あり、条件A 進行中 | 0% 〜 50% |
| Sprout 2（成長） | 条件A 充足、条件B 進行中 | 50% 〜 80% |
| Sprout 3（蕾） | progress >= bud_threshold (0.8) | 80% 〜 99% |

---

## BR-03: 条件A（構造判定）

### 判定対象パーツ

| パーツ | 内容 | AI が判定する基準 |
|---|---|---|
| Context（状況） | どのような前提条件・環境で起きる事象か | Seed または Log に具体的な状況説明がある |
| Problem（問題） | そこで発生するジレンマや障害は何か | 課題・困難が明確に言語化されている |
| Solution（解決策） | 具体的にどういう行動・仕組みで突破したか | 実行可能なアクションが提示されている |
| Name（パターン名） | このノウハウに名前を付けられる状態か | 上記3つが揃い、汎用化可能な知見として成立 |

### 充足率計算

```python
fulfillment = sum(1 for part in parts.values() if part) / 4
# 例: Context=true, Problem=true, Solution=false, Name=false → 0.5
```

### AI プロンプト設計（条件A）

```
あなたはビジネスナレッジの構造分析の専門家です。

以下の Seed（問い）とそれに対する Log（コメント）群を分析し、
ビジネスノウハウとしての構造パーツがどれだけ揃っているかを判定してください。

## 判定する構造パーツ
1. Context（状況）: 具体的な前提条件や環境の説明があるか
2. Problem（問題）: ジレンマや障害が明確に言語化されているか
3. Solution（解決策）: 実行可能な具体的アクションが提示されているか
4. Name（パターン名）: 上記3つが揃い、汎用ノウハウとして命名可能か

## Seed
タイトル: {title}
本文: {body}

## Log 一覧
{logs}

## 出力形式（JSON のみ）
{
  "context": true/false,
  "problem": true/false,
  "solution": true/false,
  "name": true/false
}
```

### 実行タイミング

- **毎回**: Log 投稿のたびに Vertex AI (Gemini Flash) を呼び出す
- Seed 本文 + 全 Log 本文をコンテキストとして送信

---

## BR-04: 条件B（成熟度スコア）

### 実行前提条件

以下の **全て** を満たす場合のみ条件B を実行:
1. 条件A が完全充足（structure_fulfillment == 1.0）
2. contributor_count >= min_contributors（設定値、デフォルト 3）
3. log_count >= min_logs（設定値、デフォルト 5）

### 4観点スコアリング

| 観点 | キー | 判定基準 |
|---|---|---|
| 網羅度 | comprehensiveness | テーマ全体を俯瞰できているか |
| 多様性 | diversity | 異なる背景のユーザーが参加しているか |
| 反論/例外 | counterarguments | 逆の視点や例外ケースが含まれるか |
| 具体性 | specificity | 明日から実行可能なアクションが抽出可能か |

### スコア計算

```python
maturity_total = (comprehensiveness + diversity + counterarguments + specificity) / 4
```

### 開花判定

```python
bloomed = passed_structure and (maturity_total >= bloom_threshold)
# bloom_threshold: デフォルト 0.7
```

### AI プロンプト設計（条件B）

```
あなたはビジネスナレッジの品質評価の専門家です。

以下の Seed（問い）とそれに対する Log（コメント）群の「集団知性」としての
成熟度を4つの観点で評価してください。各観点は 0.0〜1.0 のスコアで返してください。

## 評価観点
1. comprehensiveness（網羅度）: 原因・対策・予防策など、テーマ全体を俯瞰できているか
2. diversity（多様性）: 異なる背景を持つ複数ユーザーの視点が含まれているか
3. counterarguments（反論/例外）: 「このケースでは逆効果」等の検証ログが含まれるか
4. specificity（具体性）: 明日から実行できるレベルのアクションが抽出可能か

## Seed
タイトル: {title}
本文: {body}

## Log 一覧（投稿者情報付き）
{logs_with_user_info}

## 出力形式（JSON のみ）
{
  "comprehensiveness": 0.0〜1.0,
  "diversity": 0.0〜1.0,
  "counterarguments": 0.0〜1.0,
  "specificity": 0.0〜1.0
}
```

---

## BR-05: Progress Bar 計算

```python
def calculate_progress(structure_fulfillment: float, maturity_total: float | None) -> float:
    # 前半 50%: 条件A
    structure_progress = min(structure_fulfillment * 0.5, 0.5)

    # 後半 50%: 条件B
    if maturity_total is not None:
        maturity_progress = min(maturity_total * 0.5, 0.5)
    else:
        maturity_progress = 0.0

    return structure_progress + maturity_progress
```

| 状態 | progress 範囲 | 例 |
|---|---|---|
| Seed（Log 0件） | 0.0 | structure=0.0 |
| Sprout 1 | 0.0 〜 0.5 | structure=0.5 → progress=0.25 |
| Sprout 2 | 0.5 〜 0.8 | structure=1.0, maturity=0.4 → progress=0.7 |
| Sprout 3（蕾） | 0.8 〜 0.99 | structure=1.0, maturity=0.7 → progress=0.85 |
| Louge | 1.0 | 開花完了 |

---

## BR-06: AI ファシリテート

### トリガー条件

```python
should_facilitate = (
    maturity_total is not None
    and maturity_total < bloom_threshold
    and user_logs_since_last_facilitation >= 3
)
```

### 不足観点の特定

最もスコアが低い観点を特定し、その観点を補強する問いかけを生成する。

### ファシリテート頻度制限

- 同一 Planter に対して、前回のファシリテート Log 以降に **3件以上のユーザー Log** が投稿されるまで次のファシリテートを抑制
- 初回ファシリテートは制限なし（過去にファシリテート Log がなければ即実行可）

### AI 投稿の表示仕様

- `user_id = NULL`、`is_ai_generated = true`
- UI では「AI アシスタント」名義で表示（通常 Log と同じスタイル）
- アバターは Works Logue ロゴアイコンを使用

---

## BR-07: スコア設定の管理

### 設定値

| キー | デフォルト | 説明 |
|---|---|---|
| score.min_contributors | 3 | 条件B 開始の最低参加者数 |
| score.min_logs | 5 | 条件B 開始の最低 Log 数 |
| score.bloom_threshold | 0.7 | 開花閾値 |
| score.bud_threshold | 0.8 | Sprout 3 の progress 閾値 |

### 管理ルール

- U3 では読み取り専用 API を提供
- 管理者による CRUD は U7（Admin）で実装
- 設定値が DB に存在しない場合はデフォルト値にフォールバック

---

## BR-08: 通知イベントの記録

### Log 投稿時

```python
# Planter のフォロワー全員に通知イベントを作成（投稿者自身は除く）
for follower in planter_followers:
    if follower.user_id != log.user_id:
        Notification(
            user_id=follower.user_id,
            type='new_log',
            planter_id=planter_id,
            data={'log_id': log.id, 'author_name': user.display_name}
        )
```

### 状態遷移時

```python
# seed -> sprout 遷移時
for follower in planter_followers:
    Notification(
        user_id=follower.user_id,
        type='status_changed',
        planter_id=planter_id,
        data={'old_status': 'seed', 'new_status': 'sprout'}
    )
```
