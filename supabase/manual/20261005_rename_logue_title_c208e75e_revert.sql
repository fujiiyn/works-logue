-- 20261005_rename_logue_title_c208e75e_revert.sql
-- 20261005_rename_logue_title_c208e75e.sql を元に戻す。手動実行用（マイグレーションではない）。
--
-- 対象: Seed「とにかく時間がない」の Logue（planter_id = c208e75e-0791-40ee-8a8a-d66da5151cd8）
--   戻す前: 雑務はAIに、時間は本質に
--   戻した後: 限られた時間での業務効率化
--
-- 現在の名前が新名と一致する場合だけ戻す。実行結果が UPDATE 0 なら、まだ置き換えていないか、別の名前になっている。

UPDATE planters
SET logue_title = '限られた時間での業務効率化'
WHERE id = 'c208e75e-0791-40ee-8a8a-d66da5151cd8'
  AND status = 'logue'
  AND logue_title = '雑務はAIに、時間は本質に';

-- 確認
SELECT id, title, logue_title, updated_at
FROM planters
WHERE id = 'c208e75e-0791-40ee-8a8a-d66da5151cd8';
