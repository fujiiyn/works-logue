-- 00003_seed_tags.sql
-- Seed all tags from docs/tags.md hierarchy

DO $$
DECLARE
    -- =========================================================
    -- industry (業界) parent IDs
    -- =========================================================
    v_it UUID;
    v_consulting UUID;
    v_manufacturer UUID;
    v_mfr_hitech UUID;
    v_mfr_material UUID;
    v_mfr_lifestyle UUID;
    v_trading UUID;
    v_finance UUID;
    v_realestate UUID;
    v_media UUID;
    v_medical UUID;
    v_service UUID;
    v_public UUID;

    -- =========================================================
    -- occupation (職種) parent IDs
    -- =========================================================
    v_occ_mgmt UUID;
    v_occ_corp UUID;
    v_occ_corp_hr UUID;
    v_occ_corp_acct UUID;
    v_occ_corp_legal UUID;
    v_occ_corp_ga UUID;
    v_occ_corp_supply UUID;
    v_occ_sales UUID;
    v_occ_sales_front UUID;
    v_occ_sales_strategy UUID;
    v_occ_sales_retain UUID;
    v_occ_marketing UUID;
    v_occ_mkt_marketing UUID;
    v_occ_mkt_research UUID;
    v_occ_mkt_product UUID;
    v_occ_consultant UUID;
    v_occ_consul_consul UUID;
    v_occ_consul_pro UUID;
    v_occ_it UUID;
    v_occ_it_pm UUID;
    v_occ_it_dev UUID;
    v_occ_it_data UUID;
    v_occ_it_infra UUID;
    v_occ_it_ops UUID;
    v_occ_creative UUID;
    v_occ_creative_design UUID;
    v_occ_creative_edit UUID;
    v_occ_monozukuri UUID;
    v_occ_mono_design UUID;
    v_occ_mono_prod UUID;
    v_occ_mono_field UUID;
    v_occ_fin_re UUID;
    v_occ_fin_re_fin UUID;
    v_occ_fin_re_re UUID;
    v_occ_fin_re_con UUID;
    v_occ_med UUID;
    v_occ_med_sales UUID;
    v_occ_med_dev UUID;
    v_occ_med_pro UUID;

BEGIN

-- =============================================================
-- CATEGORY: industry (業界)
-- =============================================================

-- -- Level 1: IT・インターネット
INSERT INTO tags (name, category, parent_tag_id, sort_order, is_active)
VALUES ('IT・インターネット', 'industry', NULL, 1, TRUE) RETURNING id INTO v_it;

INSERT INTO tags (name, category, parent_tag_id, sort_order, is_active) VALUES
('インターネットサービス・EC', 'industry', v_it, 1, TRUE),
('SaaS・ソフトウェア',         'industry', v_it, 2, TRUE),
('デジタルマーケティング',     'industry', v_it, 3, TRUE),
('AI・データサイエンス',       'industry', v_it, 4, TRUE),
('通信・インフラ',             'industry', v_it, 5, TRUE);

-- -- Level 1: コンサルティング・専門サービス
INSERT INTO tags (name, category, parent_tag_id, sort_order, is_active)
VALUES ('コンサルティング・専門サービス', 'industry', NULL, 2, TRUE) RETURNING id INTO v_consulting;

INSERT INTO tags (name, category, parent_tag_id, sort_order, is_active) VALUES
('戦略・経営コンサルティング', 'industry', v_consulting, 1, TRUE),
('業務・ITコンサルティング',   'industry', v_consulting, 2, TRUE),
('リサーチ・シンクタンク',     'industry', v_consulting, 3, TRUE),
('監査法人・税理士法人',       'industry', v_consulting, 4, TRUE),
('法律事務所・知財特許事務所', 'industry', v_consulting, 5, TRUE);

-- -- Level 1: メーカー（製造業）
INSERT INTO tags (name, category, parent_tag_id, sort_order, is_active)
VALUES ('メーカー（製造業）', 'industry', NULL, 3, TRUE) RETURNING id INTO v_manufacturer;

-- -- Level 2: ハイテク・機械
INSERT INTO tags (name, category, parent_tag_id, sort_order, is_active)
VALUES ('ハイテク・機械', 'industry', v_manufacturer, 1, TRUE) RETURNING id INTO v_mfr_hitech;

INSERT INTO tags (name, category, parent_tag_id, sort_order, is_active) VALUES
('電気・電子・半導体', 'industry', v_mfr_hitech, 1, TRUE),
('自動車・輸送機器',   'industry', v_mfr_hitech, 2, TRUE),
('精密機器・工作機械', 'industry', v_mfr_hitech, 3, TRUE);

-- -- Level 2: 素材・エネルギー
INSERT INTO tags (name, category, parent_tag_id, sort_order, is_active)
VALUES ('素材・エネルギー', 'industry', v_manufacturer, 2, TRUE) RETURNING id INTO v_mfr_material;

INSERT INTO tags (name, category, parent_tag_id, sort_order, is_active) VALUES
('化学・石油・素材', 'industry', v_mfr_material, 1, TRUE),
('電力・ガス・水道', 'industry', v_mfr_material, 2, TRUE);

-- -- Level 2: ライフスタイル
INSERT INTO tags (name, category, parent_tag_id, sort_order, is_active)
VALUES ('ライフスタイル', 'industry', v_manufacturer, 3, TRUE) RETURNING id INTO v_mfr_lifestyle;

INSERT INTO tags (name, category, parent_tag_id, sort_order, is_active) VALUES
('食品・飲料',     'industry', v_mfr_lifestyle, 1, TRUE),
('日用品・化粧品', 'industry', v_mfr_lifestyle, 2, TRUE),
('アパレル・雑貨', 'industry', v_mfr_lifestyle, 3, TRUE);

-- -- Level 1: 商社・流通・小売
INSERT INTO tags (name, category, parent_tag_id, sort_order, is_active)
VALUES ('商社・流通・小売', 'industry', NULL, 4, TRUE) RETURNING id INTO v_trading;

INSERT INTO tags (name, category, parent_tag_id, sort_order, is_active) VALUES
('総合商社',           'industry', v_trading, 1, TRUE),
('専門商社',           'industry', v_trading, 2, TRUE),
('小売・流通',         'industry', v_trading, 3, TRUE),
('外食',               'industry', v_trading, 4, TRUE),
('店舗ビジネス',       'industry', v_trading, 5, TRUE),
('Eコマース・通販',    'industry', v_trading, 6, TRUE);

-- -- Level 1: 金融・保険
INSERT INTO tags (name, category, parent_tag_id, sort_order, is_active)
VALUES ('金融・保険', 'industry', NULL, 5, TRUE) RETURNING id INTO v_finance;

INSERT INTO tags (name, category, parent_tag_id, sort_order, is_active) VALUES
('銀行',                       'industry', v_finance, 1, TRUE),
('証券',                       'industry', v_finance, 2, TRUE),
('信託',                       'industry', v_finance, 3, TRUE),
('信用金庫・信用組合',         'industry', v_finance, 4, TRUE),
('投資銀行・VC・PEファンド',   'industry', v_finance, 5, TRUE),
('決済・FinTech',              'industry', v_finance, 6, TRUE),
('生命保険',                   'industry', v_finance, 7, TRUE),
('損害保険',                   'industry', v_finance, 8, TRUE);

-- -- Level 1: 不動産・建設・インフラ
INSERT INTO tags (name, category, parent_tag_id, sort_order, is_active)
VALUES ('不動産・建設・インフラ', 'industry', NULL, 6, TRUE) RETURNING id INTO v_realestate;

INSERT INTO tags (name, category, parent_tag_id, sort_order, is_active) VALUES
('デベロッパー',               'industry', v_realestate, 1, TRUE),
('ハウスメーカー',             'industry', v_realestate, 2, TRUE),
('不動産仲介',                 'industry', v_realestate, 3, TRUE),
('管理',                       'industry', v_realestate, 4, TRUE),
('建設・土木・設計',           'industry', v_realestate, 5, TRUE),
('プラント・エンジニアリング', 'industry', v_realestate, 6, TRUE),
('物流・倉庫・運輸',           'industry', v_realestate, 7, TRUE);

-- -- Level 1: 広告・メディア・エンタメ
INSERT INTO tags (name, category, parent_tag_id, sort_order, is_active)
VALUES ('広告・メディア・エンタメ', 'industry', NULL, 7, TRUE) RETURNING id INTO v_media;

INSERT INTO tags (name, category, parent_tag_id, sort_order, is_active) VALUES
('広告代理店・PR',         'industry', v_media, 1, TRUE),
('テレビ・新聞・出版',     'industry', v_media, 2, TRUE),
('映画・音楽・映像制作',   'industry', v_media, 3, TRUE),
('ゲーム・アニメ・イベント','industry', v_media, 4, TRUE);

-- -- Level 1: メディカル・ヘルスケア
INSERT INTO tags (name, category, parent_tag_id, sort_order, is_active)
VALUES ('メディカル・ヘルスケア', 'industry', NULL, 8, TRUE) RETURNING id INTO v_medical;

INSERT INTO tags (name, category, parent_tag_id, sort_order, is_active) VALUES
('医薬品',                 'industry', v_medical, 1, TRUE),
('バイオ',                 'industry', v_medical, 2, TRUE),
('医療機器メーカー',       'industry', v_medical, 3, TRUE),
('病院・クリニック',       'industry', v_medical, 4, TRUE),
('介護施設',               'industry', v_medical, 5, TRUE),
('ドラッグストア・調剤薬局','industry', v_medical, 6, TRUE);

-- -- Level 1: サービス・人材
INSERT INTO tags (name, category, parent_tag_id, sort_order, is_active)
VALUES ('サービス・人材', 'industry', NULL, 9, TRUE) RETURNING id INTO v_service;

INSERT INTO tags (name, category, parent_tag_id, sort_order, is_active) VALUES
('人材紹介',                             'industry', v_service, 1, TRUE),
('派遣',                                 'industry', v_service, 2, TRUE),
('HRサービス',                           'industry', v_service, 3, TRUE),
('教育',                                 'industry', v_service, 4, TRUE),
('ホテル',                               'industry', v_service, 5, TRUE),
('旅行・観光',                           'industry', v_service, 6, TRUE),
('アウトソーシング・BPO・コールセンター', 'industry', v_service, 7, TRUE);

-- -- Level 1: 公共・その他
INSERT INTO tags (name, category, parent_tag_id, sort_order, is_active)
VALUES ('公共・その他', 'industry', NULL, 10, TRUE) RETURNING id INTO v_public;

INSERT INTO tags (name, category, parent_tag_id, sort_order, is_active) VALUES
('官公庁・自治体',         'industry', v_public, 1, TRUE),
('非営利団体（NPO等）',   'industry', v_public, 2, TRUE),
('農林水産・鉱業',         'industry', v_public, 3, TRUE);


-- =============================================================
-- CATEGORY: occupation (職種)
-- =============================================================

-- -- Level 1: 経営・事業開発
INSERT INTO tags (name, category, parent_tag_id, sort_order, is_active)
VALUES ('経営・事業開発', 'occupation', NULL, 1, TRUE) RETURNING id INTO v_occ_mgmt;

INSERT INTO tags (name, category, parent_tag_id, sort_order, is_active) VALUES
('経営者・取締役・役員',     'occupation', v_occ_mgmt, 1, TRUE),
('経営企画・事業統括',       'occupation', v_occ_mgmt, 2, TRUE),
('新規事業企画・事業開発',   'occupation', v_occ_mgmt, 3, TRUE),
('DX推進',                   'occupation', v_occ_mgmt, 4, TRUE),
('業務変革',                 'occupation', v_occ_mgmt, 5, TRUE),
('M&A・事業提携・PMI',      'occupation', v_occ_mgmt, 6, TRUE);

-- -- Level 1: コーポレート（管理部門）
INSERT INTO tags (name, category, parent_tag_id, sort_order, is_active)
VALUES ('コーポレート（管理部門）', 'occupation', NULL, 2, TRUE) RETURNING id INTO v_occ_corp;

-- -- Level 2: 人事・採用
INSERT INTO tags (name, category, parent_tag_id, sort_order, is_active)
VALUES ('人事・採用', 'occupation', v_occ_corp, 1, TRUE) RETURNING id INTO v_occ_corp_hr;

INSERT INTO tags (name, category, parent_tag_id, sort_order, is_active) VALUES
('採用（新卒/中途）', 'occupation', v_occ_corp_hr, 1, TRUE),
('人材開発・研修',     'occupation', v_occ_corp_hr, 2, TRUE),
('制度設計',           'occupation', v_occ_corp_hr, 3, TRUE),
('組織開発（OD）',     'occupation', v_occ_corp_hr, 4, TRUE),
('労務・給与',         'occupation', v_occ_corp_hr, 5, TRUE),
('HRBP',               'occupation', v_occ_corp_hr, 6, TRUE);

-- -- Level 2: 経理・財務
INSERT INTO tags (name, category, parent_tag_id, sort_order, is_active)
VALUES ('経理・財務', 'occupation', v_occ_corp, 2, TRUE) RETURNING id INTO v_occ_corp_acct;

INSERT INTO tags (name, category, parent_tag_id, sort_order, is_active) VALUES
('経理',     'occupation', v_occ_corp_acct, 1, TRUE),
('財務',     'occupation', v_occ_corp_acct, 2, TRUE),
('管理会計', 'occupation', v_occ_corp_acct, 3, TRUE),
('税務',     'occupation', v_occ_corp_acct, 4, TRUE),
('IR',       'occupation', v_occ_corp_acct, 5, TRUE);

-- -- Level 2: 法務・知財
INSERT INTO tags (name, category, parent_tag_id, sort_order, is_active)
VALUES ('法務・知財', 'occupation', v_occ_corp, 3, TRUE) RETURNING id INTO v_occ_corp_legal;

INSERT INTO tags (name, category, parent_tag_id, sort_order, is_active) VALUES
('法務・コンプライアンス', 'occupation', v_occ_corp_legal, 1, TRUE),
('知的財産・特許',         'occupation', v_occ_corp_legal, 2, TRUE);

-- -- Level 2: 総務・庶務
INSERT INTO tags (name, category, parent_tag_id, sort_order, is_active)
VALUES ('総務・庶務', 'occupation', v_occ_corp, 4, TRUE) RETURNING id INTO v_occ_corp_ga;

INSERT INTO tags (name, category, parent_tag_id, sort_order, is_active) VALUES
('総務',     'occupation', v_occ_corp_ga, 1, TRUE),
('秘書',     'occupation', v_occ_corp_ga, 2, TRUE),
('広報・PR', 'occupation', v_occ_corp_ga, 3, TRUE);

-- -- Level 2: サプライチェーン
INSERT INTO tags (name, category, parent_tag_id, sort_order, is_active)
VALUES ('サプライチェーン', 'occupation', v_occ_corp, 5, TRUE) RETURNING id INTO v_occ_corp_supply;

INSERT INTO tags (name, category, parent_tag_id, sort_order, is_active) VALUES
('購買・資材調達',   'occupation', v_occ_corp_supply, 1, TRUE),
('物流企画・在庫管理','occupation', v_occ_corp_supply, 2, TRUE),
('国際・貿易事務',   'occupation', v_occ_corp_supply, 3, TRUE);

-- -- Level 1: 営業・カスタマーサクセス
INSERT INTO tags (name, category, parent_tag_id, sort_order, is_active)
VALUES ('営業・カスタマーサクセス', 'occupation', NULL, 3, TRUE) RETURNING id INTO v_occ_sales;

-- -- Level 2: フロント営業
INSERT INTO tags (name, category, parent_tag_id, sort_order, is_active)
VALUES ('フロント営業', 'occupation', v_occ_sales, 1, TRUE) RETURNING id INTO v_occ_sales_front;

INSERT INTO tags (name, category, parent_tag_id, sort_order, is_active) VALUES
('法人営業（大手/中堅）',         'occupation', v_occ_sales_front, 1, TRUE),
('個人営業',                       'occupation', v_occ_sales_front, 2, TRUE),
('海外営業',                       'occupation', v_occ_sales_front, 3, TRUE),
('代理店営業・パートナーセールス', 'occupation', v_occ_sales_front, 4, TRUE);

-- -- Level 2: 営業戦略・支援
INSERT INTO tags (name, category, parent_tag_id, sort_order, is_active)
VALUES ('営業戦略・支援', 'occupation', v_occ_sales, 2, TRUE) RETURNING id INTO v_occ_sales_strategy;

INSERT INTO tags (name, category, parent_tag_id, sort_order, is_active) VALUES
('営業企画',               'occupation', v_occ_sales_strategy, 1, TRUE),
('インサイドセールス',     'occupation', v_occ_sales_strategy, 2, TRUE),
('営業事務・アシスタント', 'occupation', v_occ_sales_strategy, 3, TRUE),
('プリセールス（技術営業）','occupation', v_occ_sales_strategy, 4, TRUE);

-- -- Level 2: 顧客維持・支援
INSERT INTO tags (name, category, parent_tag_id, sort_order, is_active)
VALUES ('顧客維持・支援', 'occupation', v_occ_sales, 3, TRUE) RETURNING id INTO v_occ_sales_retain;

INSERT INTO tags (name, category, parent_tag_id, sort_order, is_active) VALUES
('カスタマーサクセス（CS）', 'occupation', v_occ_sales_retain, 1, TRUE),
('カスタマーサポート',       'occupation', v_occ_sales_retain, 2, TRUE),
('コールセンター運営',       'occupation', v_occ_sales_retain, 3, TRUE);

-- -- Level 1: マーケティング・企画
INSERT INTO tags (name, category, parent_tag_id, sort_order, is_active)
VALUES ('マーケティング・企画', 'occupation', NULL, 4, TRUE) RETURNING id INTO v_occ_marketing;

-- -- Level 2: マーケティング
INSERT INTO tags (name, category, parent_tag_id, sort_order, is_active)
VALUES ('マーケティング', 'occupation', v_occ_marketing, 1, TRUE) RETURNING id INTO v_occ_mkt_marketing;

INSERT INTO tags (name, category, parent_tag_id, sort_order, is_active) VALUES
('デジタルマーケティング',       'occupation', v_occ_mkt_marketing, 1, TRUE),
('広告運用・SEO',                 'occupation', v_occ_mkt_marketing, 2, TRUE),
('SNSマーケティング',             'occupation', v_occ_mkt_marketing, 3, TRUE),
('広報・PR（マーケティング系）',  'occupation', v_occ_mkt_marketing, 4, TRUE);

-- -- Level 2: リサーチ・分析
INSERT INTO tags (name, category, parent_tag_id, sort_order, is_active)
VALUES ('リサーチ・分析', 'occupation', v_occ_marketing, 2, TRUE) RETURNING id INTO v_occ_mkt_research;

INSERT INTO tags (name, category, parent_tag_id, sort_order, is_active) VALUES
('市場調査・リサーチ',     'occupation', v_occ_mkt_research, 1, TRUE),
('データ分析（アナリスト）','occupation', v_occ_mkt_research, 2, TRUE);

-- -- Level 2: 商品・サービス企画
INSERT INTO tags (name, category, parent_tag_id, sort_order, is_active)
VALUES ('商品・サービス企画', 'occupation', v_occ_marketing, 3, TRUE) RETURNING id INTO v_occ_mkt_product;

INSERT INTO tags (name, category, parent_tag_id, sort_order, is_active) VALUES
('商品企画・開発',       'occupation', v_occ_mkt_product, 1, TRUE),
('販促・プロモーション', 'occupation', v_occ_mkt_product, 2, TRUE),
('MD・VMD',              'occupation', v_occ_mkt_product, 3, TRUE);

-- -- Level 1: コンサルタント・専門職
INSERT INTO tags (name, category, parent_tag_id, sort_order, is_active)
VALUES ('コンサルタント・専門職', 'occupation', NULL, 5, TRUE) RETURNING id INTO v_occ_consultant;

-- -- Level 2: コンサル
INSERT INTO tags (name, category, parent_tag_id, sort_order, is_active)
VALUES ('コンサル', 'occupation', v_occ_consultant, 1, TRUE) RETURNING id INTO v_occ_consul_consul;

INSERT INTO tags (name, category, parent_tag_id, sort_order, is_active) VALUES
('戦略',                 'occupation', v_occ_consul_consul, 1, TRUE),
('財務・会計',           'occupation', v_occ_consul_consul, 2, TRUE),
('組織・人事',           'occupation', v_occ_consul_consul, 3, TRUE),
('業務プロセス（BPR）', 'occupation', v_occ_consul_consul, 4, TRUE),
('ITコンサル',           'occupation', v_occ_consul_consul, 5, TRUE);

-- -- Level 2: 士業・専門職
INSERT INTO tags (name, category, parent_tag_id, sort_order, is_active)
VALUES ('士業・専門職', 'occupation', v_occ_consultant, 2, TRUE) RETURNING id INTO v_occ_consul_pro;

INSERT INTO tags (name, category, parent_tag_id, sort_order, is_active) VALUES
('公認会計士', 'occupation', v_occ_consul_pro, 1, TRUE),
('税理士',     'occupation', v_occ_consul_pro, 2, TRUE),
('弁護士',     'occupation', v_occ_consul_pro, 3, TRUE),
('弁理士',     'occupation', v_occ_consul_pro, 4, TRUE),
('行政書士',   'occupation', v_occ_consul_pro, 5, TRUE),
('講師・教諭', 'occupation', v_occ_consul_pro, 6, TRUE);

-- -- Level 1: IT・テクノロジー
INSERT INTO tags (name, category, parent_tag_id, sort_order, is_active)
VALUES ('IT・テクノロジー', 'occupation', NULL, 6, TRUE) RETURNING id INTO v_occ_it;

-- -- Level 2: PM・企画
INSERT INTO tags (name, category, parent_tag_id, sort_order, is_active)
VALUES ('PM・企画', 'occupation', v_occ_it, 1, TRUE) RETURNING id INTO v_occ_it_pm;

INSERT INTO tags (name, category, parent_tag_id, sort_order, is_active) VALUES
('プロジェクトマネージャー（PM）',  'occupation', v_occ_it_pm, 1, TRUE),
('プロダクトマネージャー（PdM）',   'occupation', v_occ_it_pm, 2, TRUE),
('ITアーキテクト',                   'occupation', v_occ_it_pm, 3, TRUE);

-- -- Level 2: 開発
INSERT INTO tags (name, category, parent_tag_id, sort_order, is_active)
VALUES ('開発', 'occupation', v_occ_it, 2, TRUE) RETURNING id INTO v_occ_it_dev;

INSERT INTO tags (name, category, parent_tag_id, sort_order, is_active) VALUES
('フロントエンド',               'occupation', v_occ_it_dev, 1, TRUE),
('バックエンド（Web/オープン系）','occupation', v_occ_it_dev, 2, TRUE),
('スマートフォンアプリ',         'occupation', v_occ_it_dev, 3, TRUE),
('ゲーム開発',                   'occupation', v_occ_it_dev, 4, TRUE),
('組み込み・制御',               'occupation', v_occ_it_dev, 5, TRUE);

-- -- Level 2: データ・AI
INSERT INTO tags (name, category, parent_tag_id, sort_order, is_active)
VALUES ('データ・AI', 'occupation', v_occ_it, 3, TRUE) RETURNING id INTO v_occ_it_data;

INSERT INTO tags (name, category, parent_tag_id, sort_order, is_active) VALUES
('データサイエンティスト', 'occupation', v_occ_it_data, 1, TRUE),
('機械学習エンジニア',     'occupation', v_occ_it_data, 2, TRUE),
('データベースエンジニア', 'occupation', v_occ_it_data, 3, TRUE);

-- -- Level 2: インフラ・セキュリティ
INSERT INTO tags (name, category, parent_tag_id, sort_order, is_active)
VALUES ('インフラ・セキュリティ', 'occupation', v_occ_it, 4, TRUE) RETURNING id INTO v_occ_it_infra;

INSERT INTO tags (name, category, parent_tag_id, sort_order, is_active) VALUES
('インフラエンジニア',     'occupation', v_occ_it_infra, 1, TRUE),
('サーバー・ネットワーク', 'occupation', v_occ_it_infra, 2, TRUE),
('セキュリティエンジニア', 'occupation', v_occ_it_infra, 3, TRUE);

-- -- Level 2: 運用・保守
INSERT INTO tags (name, category, parent_tag_id, sort_order, is_active)
VALUES ('運用・保守', 'occupation', v_occ_it, 5, TRUE) RETURNING id INTO v_occ_it_ops;

INSERT INTO tags (name, category, parent_tag_id, sort_order, is_active) VALUES
('社内SE・情報システム', 'occupation', v_occ_it_ops, 1, TRUE),
('テクニカルサポート',   'occupation', v_occ_it_ops, 2, TRUE),
('QA・テスト',           'occupation', v_occ_it_ops, 3, TRUE);

-- -- Level 1: クリエイティブ・デザイン
INSERT INTO tags (name, category, parent_tag_id, sort_order, is_active)
VALUES ('クリエイティブ・デザイン', 'occupation', NULL, 7, TRUE) RETURNING id INTO v_occ_creative;

-- -- Level 2: デザイン
INSERT INTO tags (name, category, parent_tag_id, sort_order, is_active)
VALUES ('デザイン', 'occupation', v_occ_creative, 1, TRUE) RETURNING id INTO v_occ_creative_design;

INSERT INTO tags (name, category, parent_tag_id, sort_order, is_active) VALUES
('UI/UXデザイナー',       'occupation', v_occ_creative_design, 1, TRUE),
('Webデザイナー',         'occupation', v_occ_creative_design, 2, TRUE),
('アートディレクター',   'occupation', v_occ_creative_design, 3, TRUE),
('グラフィックデザイナー','occupation', v_occ_creative_design, 4, TRUE);

-- -- Level 2: 編集・制作
INSERT INTO tags (name, category, parent_tag_id, sort_order, is_active)
VALUES ('編集・制作', 'occupation', v_occ_creative, 2, TRUE) RETURNING id INTO v_occ_creative_edit;

INSERT INTO tags (name, category, parent_tag_id, sort_order, is_active) VALUES
('Webディレクター',       'occupation', v_occ_creative_edit, 1, TRUE),
('コンテンツ企画・編集',  'occupation', v_occ_creative_edit, 2, TRUE),
('ライター・記者',        'occupation', v_occ_creative_edit, 3, TRUE),
('映像制作・編集',        'occupation', v_occ_creative_edit, 4, TRUE),
('コピーライター',        'occupation', v_occ_creative_edit, 5, TRUE);

-- -- Level 1: モノづくり（製造・エンジニアリング）
INSERT INTO tags (name, category, parent_tag_id, sort_order, is_active)
VALUES ('モノづくり（製造・エンジニアリング）', 'occupation', NULL, 8, TRUE) RETURNING id INTO v_occ_monozukuri;

-- -- Level 2: 設計・開発
INSERT INTO tags (name, category, parent_tag_id, sort_order, is_active)
VALUES ('設計・開発', 'occupation', v_occ_monozukuri, 1, TRUE) RETURNING id INTO v_occ_mono_design;

INSERT INTO tags (name, category, parent_tag_id, sort_order, is_active) VALUES
('研究・開発（R&D）', 'occupation', v_occ_mono_design, 1, TRUE),
('回路・実装設計',     'occupation', v_occ_mono_design, 2, TRUE),
('機械・筐体設計',     'occupation', v_occ_mono_design, 3, TRUE),
('制御設計',           'occupation', v_occ_mono_design, 4, TRUE);

-- -- Level 2: 生産・品質
INSERT INTO tags (name, category, parent_tag_id, sort_order, is_active)
VALUES ('生産・品質', 'occupation', v_occ_monozukuri, 2, TRUE) RETURNING id INTO v_occ_mono_prod;

INSERT INTO tags (name, category, parent_tag_id, sort_order, is_active) VALUES
('生産技術・プロセス開発', 'occupation', v_occ_mono_prod, 1, TRUE),
('生産管理',               'occupation', v_occ_mono_prod, 2, TRUE),
('品質管理・品質保証',     'occupation', v_occ_mono_prod, 3, TRUE),
('工場長・プラント管理',   'occupation', v_occ_mono_prod, 4, TRUE);

-- -- Level 2: フィールド
INSERT INTO tags (name, category, parent_tag_id, sort_order, is_active)
VALUES ('フィールド', 'occupation', v_occ_monozukuri, 3, TRUE) RETURNING id INTO v_occ_mono_field;

INSERT INTO tags (name, category, parent_tag_id, sort_order, is_active) VALUES
('セールスエンジニア',               'occupation', v_occ_mono_field, 1, TRUE),
('サービスエンジニア（保守・修理）', 'occupation', v_occ_mono_field, 2, TRUE);

-- -- Level 1: 金融・不動産・建設
INSERT INTO tags (name, category, parent_tag_id, sort_order, is_active)
VALUES ('金融・不動産・建設', 'occupation', NULL, 9, TRUE) RETURNING id INTO v_occ_fin_re;

-- -- Level 2: 金融専門
INSERT INTO tags (name, category, parent_tag_id, sort_order, is_active)
VALUES ('金融専門', 'occupation', v_occ_fin_re, 1, TRUE) RETURNING id INTO v_occ_fin_re_fin;

INSERT INTO tags (name, category, parent_tag_id, sort_order, is_active) VALUES
('ディーラー・トレーダー', 'occupation', v_occ_fin_re_fin, 1, TRUE),
('ファンドマネージャー',   'occupation', v_occ_fin_re_fin, 2, TRUE),
('アナリスト',             'occupation', v_occ_fin_re_fin, 3, TRUE),
('融資審査・リスク管理',   'occupation', v_occ_fin_re_fin, 4, TRUE);

-- -- Level 2: 不動産
INSERT INTO tags (name, category, parent_tag_id, sort_order, is_active)
VALUES ('不動産', 'occupation', v_occ_fin_re, 2, TRUE) RETURNING id INTO v_occ_fin_re_re;

INSERT INTO tags (name, category, parent_tag_id, sort_order, is_active) VALUES
('不動産企画・開発',       'occupation', v_occ_fin_re_re, 1, TRUE),
('用地仕入',               'occupation', v_occ_fin_re_re, 2, TRUE),
('アセットマネジメント',   'occupation', v_occ_fin_re_re, 3, TRUE),
('プロパティマネジメント', 'occupation', v_occ_fin_re_re, 4, TRUE);

-- -- Level 2: 建設・土木
INSERT INTO tags (name, category, parent_tag_id, sort_order, is_active)
VALUES ('建設・土木', 'occupation', v_occ_fin_re, 3, TRUE) RETURNING id INTO v_occ_fin_re_con;

INSERT INTO tags (name, category, parent_tag_id, sort_order, is_active) VALUES
('建築設計・積算',               'occupation', v_occ_fin_re_con, 1, TRUE),
('施工管理（建築/土木/設備）',   'occupation', v_occ_fin_re_con, 2, TRUE),
('測量・構造解析',               'occupation', v_occ_fin_re_con, 3, TRUE);

-- -- Level 1: 医療・医薬・バイオ
INSERT INTO tags (name, category, parent_tag_id, sort_order, is_active)
VALUES ('医療・医薬・バイオ', 'occupation', NULL, 10, TRUE) RETURNING id INTO v_occ_med;

-- -- Level 2: 営業・企画
INSERT INTO tags (name, category, parent_tag_id, sort_order, is_active)
VALUES ('営業・企画', 'occupation', v_occ_med, 1, TRUE) RETURNING id INTO v_occ_med_sales;

INSERT INTO tags (name, category, parent_tag_id, sort_order, is_active) VALUES
('MR（医薬情報担当者）', 'occupation', v_occ_med_sales, 1, TRUE),
('医療機器営業',         'occupation', v_occ_med_sales, 2, TRUE),
('MSL',                   'occupation', v_occ_med_sales, 3, TRUE),
('薬事・市販後調査',     'occupation', v_occ_med_sales, 4, TRUE);

-- -- Level 2: 開発・研究
INSERT INTO tags (name, category, parent_tag_id, sort_order, is_active)
VALUES ('開発・研究', 'occupation', v_occ_med, 2, TRUE) RETURNING id INTO v_occ_med_dev;

INSERT INTO tags (name, category, parent_tag_id, sort_order, is_active) VALUES
('非臨床・臨床開発（CRA）', 'occupation', v_occ_med_dev, 1, TRUE),
('統計解析',                 'occupation', v_occ_med_dev, 2, TRUE),
('薬理研究',                 'occupation', v_occ_med_dev, 3, TRUE);

-- -- Level 2: 専門職
INSERT INTO tags (name, category, parent_tag_id, sort_order, is_active)
VALUES ('専門職', 'occupation', v_occ_med, 3, TRUE) RETURNING id INTO v_occ_med_pro;

INSERT INTO tags (name, category, parent_tag_id, sort_order, is_active) VALUES
('医師',   'occupation', v_occ_med_pro, 1, TRUE),
('看護師', 'occupation', v_occ_med_pro, 2, TRUE),
('薬剤師', 'occupation', v_occ_med_pro, 3, TRUE);


-- =============================================================
-- CATEGORY: role (役割) -- flat, no hierarchy
-- =============================================================

INSERT INTO tags (name, category, parent_tag_id, sort_order, is_active) VALUES
('経営者・役員',                   'role', NULL, 1,  TRUE),
('事業責任者/部門長',              'role', NULL, 2,  TRUE),
('部長',                           'role', NULL, 3,  TRUE),
('マネージャー/課長',              'role', NULL, 4,  TRUE),
('店長',                           'role', NULL, 5,  TRUE),
('係長',                           'role', NULL, 6,  TRUE),
('リーダー',                       'role', NULL, 7,  TRUE),
('プロジェクトマネージャー/リーダー','role', NULL, 8,  TRUE),
('中堅',                           'role', NULL, 9,  TRUE),
('スペシャリスト',                 'role', NULL, 10, TRUE),
('若手',                           'role', NULL, 11, TRUE),
('フリーランス・個人事業主',       'role', NULL, 12, TRUE),
('副業・パートナー',               'role', NULL, 13, TRUE),
('後継者',                         'role', NULL, 14, TRUE),
('その他（特殊・状況的な立場）',   'role', NULL, 15, TRUE);


-- =============================================================
-- CATEGORY: situation (状況) -- flat, no hierarchy
-- =============================================================

INSERT INTO tags (name, category, parent_tag_id, sort_order, is_active) VALUES
('大手',                 'situation', NULL, 1,  TRUE),
('中堅',                 'situation', NULL, 2,  TRUE),
('ベンチャー',           'situation', NULL, 3,  TRUE),
('スタートアップ',       'situation', NULL, 4,  TRUE),
('ブラック環境',         'situation', NULL, 5,  TRUE),
('ホワイト過ぎる',       'situation', NULL, 6,  TRUE),
('同族経営 / オーナー企業','situation', NULL, 7,  TRUE),
('大企業病',             'situation', NULL, 8,  TRUE),
('炎上',                 'situation', NULL, 9,  TRUE),
('社内紛争 / 政治',      'situation', NULL, 10, TRUE),
('ハラスメント',         'situation', NULL, 11, TRUE),
('リストラ',             'situation', NULL, 12, TRUE),
('事業撤退',             'situation', NULL, 13, TRUE),
('事業再生 / 立て直し',  'situation', NULL, 14, TRUE),
('就職',                 'situation', NULL, 15, TRUE),
('転職活動',             'situation', NULL, 16, TRUE),
('退職',                 'situation', NULL, 17, TRUE),
('出向',                 'situation', NULL, 18, TRUE),
('転籍',                 'situation', NULL, 19, TRUE),
('天下り',               'situation', NULL, 20, TRUE),
('異動',                 'situation', NULL, 21, TRUE),
('駐在',                 'situation', NULL, 22, TRUE),
('海外勤務',             'situation', NULL, 23, TRUE),
('出張',                 'situation', NULL, 24, TRUE),
('メンタルヘルス',       'situation', NULL, 25, TRUE),
('燃え尽き',             'situation', NULL, 26, TRUE),
('過労死',               'situation', NULL, 27, TRUE),
('限界突破',             'situation', NULL, 28, TRUE),
('窓際社員',             'situation', NULL, 29, TRUE),
('社畜',                 'situation', NULL, 30, TRUE),
('思考停止',             'situation', NULL, 31, TRUE),
('ソルジャー / 使い捨て','situation', NULL, 32, TRUE),
('社内恋愛',             'situation', NULL, 33, TRUE),
('世代間ギャップ',       'situation', NULL, 34, TRUE),
('老害',                 'situation', NULL, 35, TRUE),
('忖度 / 同調圧力',      'situation', NULL, 36, TRUE),
('ワンオペ',             'situation', NULL, 37, TRUE),
('属人化',               'situation', NULL, 38, TRUE);


-- =============================================================
-- CATEGORY: skill (スキル/メソッド) -- flat, no hierarchy
-- =============================================================

INSERT INTO tags (name, category, parent_tag_id, sort_order, is_active) VALUES
('営業',                           'skill', NULL, 1,  TRUE),
('ロジカルシンキング',             'skill', NULL, 2,  TRUE),
('構造化',                         'skill', NULL, 3,  TRUE),
('仮説構築',                       'skill', NULL, 4,  TRUE),
('クリティカルシンキング',         'skill', NULL, 5,  TRUE),
('デザイン思考',                   'skill', NULL, 6,  TRUE),
('言語化',                         'skill', NULL, 7,  TRUE),
('交渉',                           'skill', NULL, 8,  TRUE),
('ファシリテーション',             'skill', NULL, 9,  TRUE),
('調整',                           'skill', NULL, 10, TRUE),
('プレゼンテーション',             'skill', NULL, 11, TRUE),
('マネジメント',                   'skill', NULL, 12, TRUE),
('教育・育成',                     'skill', NULL, 13, TRUE),
('コーチング',                     'skill', NULL, 14, TRUE),
('意思決定',                       'skill', NULL, 15, TRUE),
('巻き込み',                       'skill', NULL, 16, TRUE),
('分析',                           'skill', NULL, 17, TRUE),
('プロジェクトマネジメント',       'skill', NULL, 18, TRUE),
('新規事業',                       'skill', NULL, 19, TRUE),
('起業',                           'skill', NULL, 20, TRUE),
('振り返り',                       'skill', NULL, 21, TRUE),
('経営',                           'skill', NULL, 22, TRUE),
('タスクマネジメント',             'skill', NULL, 23, TRUE),
('リスク管理',                     'skill', NULL, 24, TRUE),
('リーダーシップ',                 'skill', NULL, 25, TRUE),
('社内政治力',                     'skill', NULL, 26, TRUE),
('目標設定、評価・フィードバック', 'skill', NULL, 27, TRUE),
('語学',                           'skill', NULL, 28, TRUE);


-- =============================================================
-- CATEGORY: knowledge (ナレッジ) -- flat, no hierarchy
-- =============================================================

INSERT INTO tags (name, category, parent_tag_id, sort_order, is_active) VALUES
('職種ナレッジ', 'knowledge', NULL, 1, TRUE),
('トレンド',     'knowledge', NULL, 2, TRUE),
('業界ナレッジ', 'knowledge', NULL, 3, TRUE),
('競合ナレッジ', 'knowledge', NULL, 4, TRUE),
('法規制',       'knowledge', NULL, 5, TRUE),
('IT',           'knowledge', NULL, 6, TRUE),
('AI',           'knowledge', NULL, 7, TRUE),
('資格知識',     'knowledge', NULL, 8, TRUE);

END $$;

-- Set is_leaf = FALSE for all parent tags (tags that have children)
UPDATE tags SET is_leaf = FALSE
WHERE id IN (
    SELECT DISTINCT parent_tag_id FROM tags WHERE parent_tag_id IS NOT NULL
);
