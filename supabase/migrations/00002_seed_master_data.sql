-- 00002_seed_master_data.sql
-- seed_types + ai_configs initial data

INSERT INTO seed_types (slug, name, description, sort_order) VALUES
('query',       '疑問',     '現場で感じた「なぜ？」「どうすれば？」を投げかける', 1),
('pain',        '悩み',     '解決策が見つからない業務課題や困りごと', 2),
('failure',     '失敗',     '実際に経験した失敗事例とその教訓', 3),
('hypothesis',  '仮説',     '「こうすればうまくいくのでは？」という仮説の検証を求める', 4),
('comparison',  '比較',     'ツール・手法・アプローチの比較検討', 5),
('observation', '違和感',   '「これおかしくない？」という現場の気づき', 6),
('knowledge',   'シェア',   '知見やノウハウの共有', 7),
('practice',    '実践報告', '実際に試した結果の報告とフィードバック募集', 8);

INSERT INTO ai_configs (key, value, description) VALUES
('scoring_model',            'gemini-2.0-flash',        'スコアリング用AIモデル（軽量・高頻度）'),
('louge_model',              'gemini-2.0-pro',          'Louge記事生成用AIモデル（高品質）'),
('facilitator_model',        'gemini-2.0-flash',        'AIファシリテート用モデル'),
('scoring_structure_prompt', '(placeholder)',            '条件A 構造パーツ判定プロンプト'),
('scoring_maturity_prompt',  '(placeholder)',            '条件B 成熟度スコアリングプロンプト'),
('louge_generation_prompt',  '(placeholder)',            'Louge記事生成プロンプト'),
('facilitator_prompt',       '(placeholder)',            'AIファシリテートLog生成プロンプト'),
('structure_threshold',      '0.8',                     '条件A 充足率の閾値（これ以上でSprout2へ）'),
('maturity_threshold',       '100',                     '条件B 完全充足スコア（これ以上でLouge開花）'),
('bud_threshold',            '80',                      '条件B スコアの蕾しきい値（これ以上でSprout3へ）'),
('min_participants',         '5',                       '条件B 発動の最低参加者数'),
('min_logs',                 '10',                      '条件B 発動の最低Log数');
