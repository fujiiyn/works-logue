# U6 User & Follow — Business Logic Model

## 1. プロフィール表示

### 1a. 公開プロフィール取得 (`GET /users/{user_id}`)

```
Input: user_id (UUID)
Output: UserProfileResponse

1. UserRepository.get_by_id(user_id) で User 取得
2. User が存在しない or deleted_at != null or is_banned → 404
3. 集計クエリで stats を算出:
   - louge_count: planters WHERE (author_id = user_id AND status = 'louge')
                  UNION logs WHERE (author_id = user_id AND planter.status = 'louge') の重複排除件数
   - follower_count: user_follows WHERE followee_id = user_id の COUNT
   - following_count: user_follows WHERE follower_id = user_id の COUNT
4. TagRepository.get_tags_for_user(user_id) でタグ取得
5. FeaturedContribution を取得:
   - insight_score_events WHERE user_id = user_id を planter ごとに集計
   - status = 'louge' の Planter のみ対象
   - 最高スコアの1件を返す
6. 閲覧者が認証済みの場合:
   - UserFollow で is_following を判定
7. UserProfileResponse を構築して返却
```

### 1b. 自分のプロフィール取得 (`GET /users/me`)
- 既存実装を拡張。headline, cover_url, specialty_themes を含める

### 1c. 投稿履歴タブ

**Seed一覧** (`GET /users/{user_id}/planters?tab=seeds`)
```
planters WHERE author_id = user_id ORDER BY created_at DESC
ページネーション: cursor-based (既存の PlanterRepository パターンに準拠)
```

**Log一覧** (`GET /users/{user_id}/logs`)
```
logs WHERE author_id = user_id ORDER BY created_at DESC
各 Log に紐づく Planter のタイトル・状態も返す
```

**参加Louge** (`GET /users/{user_id}/planters?tab=louges`)
```
Seed投稿者として: planters WHERE author_id = user_id AND status = 'louge'
Log貢献者として: planters WHERE id IN (SELECT planter_id FROM logs WHERE author_id = user_id) AND status = 'louge'
UNION → 重複排除 → ORDER BY bloomed_at DESC
```

## 2. プロフィール編集

### 2a. プロフィール更新 (`PATCH /users/me`)

```
Input: UserUpdateRequest (display_name, headline, bio, tag_ids, location, social_links)
Output: UserResponse

1. 認証ユーザー取得
2. バリデーション:
   - display_name: 1〜100文字（必須）
   - headline: 0〜60文字
   - bio: 0〜200文字
   - tag_ids: 存在するタグIDか検証
   - location: 0〜100文字
   - social_links: { x?, linkedin?, wantedly?, website? } 各URL形式
3. UserRepository.update(user, fields)
4. TagRepository.replace_user_tags(user_id, tag_ids)
5. 更新後の UserResponse を返却
```

### 2b. アバターアップロード (`POST /users/me/avatar`)

```
Input: UploadFile (multipart/form-data)
Output: { avatar_url: string }

1. 認証ユーザー取得
2. バリデーション:
   - ファイルサイズ: 2MB以下
   - MIME type: image/jpeg, image/png のみ
3. SupabaseStorageClient.upload(bucket="avatars", path="{user_id}/{timestamp}.{ext}", file)
4. 古いアバターがあれば削除
5. UserRepository.update(user, { avatar_url: public_url })
6. { avatar_url } を返却
```

### 2c. カバー画像アップロード (`POST /users/me/cover`)

```
Input: UploadFile (multipart/form-data)
Output: { cover_url: string }

1〜6: アバターと同じフロー（bucket="covers", フィールド=cover_url）
```

## 3. フォロー機能

### 3a. ユーザーフォロー (`POST /users/{user_id}/follow`)

```
Input: user_id (UUID)
Output: 204 No Content

1. 認証ユーザー取得
2. self-follow チェック（follower_id == followee_id → 400）
3. 対象ユーザー存在チェック（deleted/banned → 404）
4. 既にフォロー済みなら何もしない（冪等）
5. FollowRepository.follow_user(follower_id, followee_id)
```

### 3b. ユーザーアンフォロー (`DELETE /users/{user_id}/follow`)

```
Input: user_id (UUID)
Output: 204 No Content

1. 認証ユーザー取得
2. FollowRepository.unfollow_user(follower_id, followee_id)
3. レコードが存在しなくても 204（冪等）
```

### 3c. Planterフォロー (`POST /planters/{planter_id}/follow`)

```
既存の auto-follow ロジック (FollowRepository.follow_planter) を
手動フォロー用エンドポイントとして公開
```

### 3d. Planterアンフォロー (`DELETE /planters/{planter_id}/follow`)

```
FollowRepository.unfollow_planter(user_id, planter_id)
```

### 3e. 自動フォロー（既存実装の維持）

- Seed 投稿時: 投稿者が自動で Planter をフォロー（実装済み）
- Log 投稿時: 投稿者が自動で Planter をフォロー（実装済み）

## 4. フォロー中フィード

### 4a. フォロー中フィード (`GET /planters?tab=following`)

```
Input: 認証ユーザー
Output: PlanterListResponse

1. フォロー中の Planter を取得:
   planter_follows WHERE user_id = current_user_id → planter_ids
2. フォロー中のユーザーが投稿した Planter を取得:
   user_follows WHERE follower_id = current_user_id → followee_ids
   planters WHERE author_id IN followee_ids → planter_ids
3. 1 + 2 を UNION して重複排除
4. ORDER BY updated_at DESC（最新のアクティビティ順）
5. ページネーション適用
```

## 5. 貢献グラフ

### 5a. 貢献グラフデータ取得 (`GET /users/{user_id}` のレスポンスに含む)

```
Output: ContributionGraphResponse (365日分の日別カウント)

1. 過去1年間の日別 Seed 投稿数を集計:
   planters WHERE user_id = user_id GROUP BY DATE(created_at)
2. 過去1年間の日別 Log 投稿数を集計:
   logs WHERE author_id = user_id GROUP BY DATE(created_at)
3. 日別に合算して返却
```

## 6. SupabaseStorageClient（新規インフラコンポーネント）

```
BC-17 SupabaseStorageClient

Methods:
- upload(bucket, path, file_data, content_type) → public_url
- delete(bucket, path) → None
- get_public_url(bucket, path) → url

実装: supabase-py の storage API を使用
将来: GCSStorageClient に差し替え可能（同じインターフェース）
```
