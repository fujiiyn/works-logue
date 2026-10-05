-- 20261005_rename_logue_title_c208e75e.sql
-- 手動実行用（マイグレーションではない）。Supabase ダッシュボードの SQL Editor で実行する。
--
-- 対象: Seed「とにかく時間がない」の Logue（planter_id = c208e75e-0791-40ee-8a8a-d66da5151cd8）
-- 変更: パターン名（logue_title）だけを置き換える。本文（logue_content）は変えない
--   旧: 限られた時間での業務効率化
--   新: 雑務はAIに、時間は本質に
--
-- 新しい名前は、パターン名プロンプト v5 の試し生成（2026-10-04）の候補から選んだもの。
-- 元に戻すときは 20261005_rename_logue_title_c208e75e_revert.sql を実行する。
--
-- 現在の名前が旧名と一致する場合だけ更新する。実行結果が UPDATE 0 なら、既に変更済みか、別の名前になっている。

UPDATE planters
SET logue_title = '雑務はAIに、時間は本質に'
WHERE id = 'c208e75e-0791-40ee-8a8a-d66da5151cd8'
  AND status = 'logue'
  AND logue_title = '限られた時間での業務効率化';

-- 確認
SELECT id, title, logue_title, updated_at
FROM planters
WHERE id = 'c208e75e-0791-40ee-8a8a-d66da5151cd8';
