# U3 Log & Score - Functional Design Plan

## Plan Overview

U3 は Log 投稿、スコアエンジン（条件A/B）、Planter 状態遷移、AI ファシリテートを実装する「成長サイクルのコア」ユニット。

### Checklist

- [x] Step 1: Log 投稿フローのビジネスロジック設計
- [x] Step 2: ScoreEngine（条件A 構造判定）の設計
- [x] Step 3: ScoreEngine（条件B 成熟度スコア）の設計
- [x] Step 4: ScorePipeline オーケストレーションの設計
- [x] Step 5: AIFacilitator の設計
- [x] Step 6: Planter 状態遷移ロジックの設計
- [x] Step 7: Domain Entities 定義
- [x] Step 8: Business Rules 定義
- [x] Step 9: Frontend Components 設計（PlanterDetail + LogThread）

---

## Questions

以下の質問に回答してください。各質問の `[Answer]:` の後に回答を記入してください。

---

### Q1: Log 投稿の本文制限

Log（コメント）の本文の文字数上限をどうしますか？

- A) 500文字（短いコメント重視）
- B) 2000文字（中程度、Stack Overflow のコメント程度）
- C) 5000文字（長文の体験共有も可能）
- D) 10000文字（Seed 本文と同じ上限）

[Answer]:C

---

### Q2: 条件A（構造判定）の AI 呼び出しタイミング

条件A の構造パーツ充足率チェックは Log 投稿のたびに AI を呼び出すとコストがかかります。どの戦略を取りますか？

- A) 毎回 AI 呼び出し（精度重視、Vertex AI の軽量モデルで）
- B) Log が N 件増えるごとに AI 呼び出し（例: 3件ごと）
- C) AI は条件A のみ使い、条件B は別タイミングで実行（要件定義通り）
- D) その他（自由記述）

[Answer]:A

---

### Q3: 条件B の最低参加ライン

要件定義に「最低参加ライン（例: 5人以上参加、10 Log 以上）」とあります。MVP での具体的な閾値はどうしますか？

- A) 参加者3人以上 & Log 5件以上（テストしやすい低閾値）
- B) 参加者5人以上 & Log 10件以上（要件定義の例通り）
- C) 設定ファイルで変更可能にし、初期値は A の低閾値
- D) その他（自由記述）

[Answer]:C,管理者ページから設定できる

---

### Q4: AI ファシリテート Log の表示

AI が投稿するファシリテート Log はどのように表示しますか？

- A) 通常の Log と同じスタイルだが「AI アシスタント」名義で表示
- B) 視覚的に区別されたカード（背景色やアイコンで区別）
- C) Log スレッド内ではなく、別セクション（例: 右サイドバーのヒント）
- D) その他（自由記述）

[Answer]:A

---

### Q5: Log 投稿後のスコア計算の同期/非同期

Log 投稿時のスコア計算をどう処理しますか？

- A) 同期処理（Log 投稿の API レスポンスにスコア結果を含める）
- B) 非同期処理（Log 投稿は即座に返し、スコア計算はバックグラウンドで実行。フロントは polling で更新）
- C) ハイブリッド（Log INSERT は同期、AI 呼び出しのみ非同期。スナップショットは次回ページ読み込みで反映）
- D) その他（自由記述）

[Answer]:A

---

### Q6: PlanterDetail ページの Log 表示順

Log の表示順序はどうしますか？

- A) 古い順（上から下に時系列、チャット風）
- B) 新しい順（最新が上）
- C) スレッドごとにグルーピング、スレッド内は古い順
- D) その他（自由記述）

[Answer]:A

---

### Q7: MVP での Vertex AI モデル選択

ScoreEngine / AIFacilitator で使う Vertex AI のモデルはどうしますか？

- A) Gemini 1.5 Flash（低コスト・高速）
- B) Gemini 1.5 Pro（高精度）
- C) 条件A は Flash、条件B / ファシリテートは Pro
- D) その他（自由記述）

[Answer]:A

---

### Q8: PlanterDetail 右サイドバーの追加情報

前回のフィードバックで「右サイドバーはスコア表示」としましたが、U3 で追加すべき情報はありますか？

- A) 現状のスコアカードのみで十分（構造充足率 + Log数 + 貢献者数 + 開花まで）
- B) 条件A の構造パーツの詳細（Context/Problem/Solution/Name のチェック状態）を追加
- C) 条件B のスコア内訳（網羅度/多様性/反論/具体性）も表示
- D) B + C 両方

[Answer]:B
