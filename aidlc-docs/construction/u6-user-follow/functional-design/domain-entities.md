# U6 User & Follow — Domain Entities

## 既存エンティティ（U1で定義済み）

### User
| フィールド | 型 | 説明 |
|---|---|---|
| id | UUID | PK |
| auth_id | UUID | Supabase Auth ID (unique) |
| display_name | string(100) | 表示名 |
| bio | string | 自己紹介文 (200文字制限) |
| avatar_url | string | アバター画像URL (Supabase Storage) |
| insight_score | float | 総合インサイトスコア |
| role | string(10) | "user" / "admin" |
| is_banned | bool | BAN状態 |
| onboarded_at | datetime | オンボーディング完了日時 |
| created_at | datetime | 作成日時 |
| deleted_at | datetime | 論理削除日時 |

### U6 で追加するフィールド

| フィールド | 型 | 説明 |
|---|---|---|
| headline | string(60) | プロフェッショナル・ヘッドライン（一行の肩書き） |
| cover_url | string | カバー画像URL (Supabase Storage) |
| location | string(100) | 居住地（自由テキスト、例: 「東京都」） |
| social_links | jsonb | SNSリンク（`{ x?: url, linkedin?: url, wantedly?: url, website?: url }`） |

### PlanterFollow（既存）
| フィールド | 型 | 説明 |
|---|---|---|
| user_id | UUID | FK → users.id (PK) |
| planter_id | UUID | FK → planters.id (PK) |
| created_at | datetime | フォロー日時 |

### UserFollow（既存）
| フィールド | 型 | 説明 |
|---|---|---|
| follower_id | UUID | FK → users.id (PK) |
| followee_id | UUID | FK → users.id (PK) |
| created_at | datetime | フォロー日時 |
| CHECK | | follower_id != followee_id |

## リレーション

```
User 1──N PlanterFollow N──1 Planter
User(follower) 1──N UserFollow N──1 User(followee)
User 1──N Planter (author)
User 1──N Log (author)
User N──M Tag (user_tags中間テーブル)
```

## 集計ビュー（APIレスポンス用）

### UserProfileStats
| 値 | 算出方法 |
|---|---|
| insight_score | users.insight_score |
| louge_count | Seed投稿 or Log投稿で開花したPlanter数 |
| follower_count | user_follows WHERE followee_id = user_id の COUNT |
| following_count | user_follows WHERE follower_id = user_id の COUNT |

### ContributionGraph（貢献グラフ）
| 値 | 算出方法 |
|---|---|
| date | 日付 |
| count | Seed投稿数 + Log投稿数（その日の合計） |

公開プロフィールに表示。1年分の日別ヒートマップ（GitHub草風）。

### FeaturedContribution
| 値 | 算出方法 |
|---|---|
| planter | 最高スコアの Louge 貢献 Planter |
| insight_score_earned | insight_score_events の合計 |

## ストレージ

| バケット | 用途 | パス規則 |
|---|---|---|
| avatars | アバター画像 | `{user_id}/{timestamp}.{ext}` |
| covers | カバー画像 | `{user_id}/{timestamp}.{ext}` |

- Supabase Storage（S3互換）。将来GCSに移行可能（クライアント差し替えのみ）
- Public バケット（URLで直接アクセス可能）
