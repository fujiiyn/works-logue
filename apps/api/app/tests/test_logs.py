import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.log import Log
from app.models.planter import Planter
from app.models.seed_type import SeedType
from app.models.user import User


@pytest.fixture
async def seed_type(db_session: AsyncSession) -> SeedType:
    st = SeedType(
        slug="query", name="疑問", description="疑問", sort_order=1, is_active=True
    )
    db_session.add(st)
    await db_session.commit()
    await db_session.refresh(st)
    return st


@pytest.fixture
async def test_user(db_session: AsyncSession, mock_auth_user_sub) -> User:
    user = User(auth_id=mock_auth_user_sub, display_name="Test User")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def planter(db_session: AsyncSession, test_user, seed_type) -> Planter:
    p = Planter(
        user_id=test_user.id,
        title="Test Seed",
        body="Test body for seed",
        seed_type_id=seed_type.id,
    )
    db_session.add(p)
    await db_session.commit()
    await db_session.refresh(p)
    return p


@pytest.fixture
async def louge_planter(db_session: AsyncSession, test_user, seed_type) -> Planter:
    p = Planter(
        user_id=test_user.id,
        title="Bloomed",
        body="Already bloomed",
        seed_type_id=seed_type.id,
        status="louge",
    )
    db_session.add(p)
    await db_session.commit()
    await db_session.refresh(p)
    return p


class TestCreateLog:
    """POST /api/v1/planters/{planter_id}/logs"""

    async def test_create_log_success(self, client: AsyncClient, planter):
        """正常系: 201 + LogCreateResponse が返る"""
        resp = await client.post(
            f"/api/v1/planters/{planter.id}/logs",
            json={"body": "This is my log comment"},
            headers={"Authorization": "Bearer test-token"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["log"]["body"] == "This is my log comment"
        assert data["log"]["planter_id"] == str(planter.id)
        assert data["log"]["is_ai_generated"] is False
        assert data["log"]["parent_log_id"] is None
        assert data["score_pending"] is True
        assert data["planter"]["id"] == str(planter.id)

    async def test_create_log_updates_counts(self, client: AsyncClient, planter):
        """Log投稿後に log_count, contributor_count が更新される"""
        resp = await client.post(
            f"/api/v1/planters/{planter.id}/logs",
            json={"body": "First log"},
            headers={"Authorization": "Bearer test-token"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["planter"]["log_count"] == 1
        assert data["planter"]["contributor_count"] == 1

    async def test_create_log_seed_to_sprout_transition(
        self, client: AsyncClient, planter
    ):
        """初回Log投稿で status が seed -> sprout に遷移する"""
        assert planter.status == "seed"
        resp = await client.post(
            f"/api/v1/planters/{planter.id}/logs",
            json={"body": "First log triggers sprout"},
            headers={"Authorization": "Bearer test-token"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["planter"]["status"] == "sprout"

    async def test_create_log_unauthenticated(self, client: AsyncClient, planter):
        """未認証: 401"""
        resp = await client.post(
            f"/api/v1/planters/{planter.id}/logs",
            json={"body": "Should fail"},
        )
        assert resp.status_code == 401

    async def test_create_log_planter_not_found(self, client: AsyncClient):
        """存在しないPlanter: 404"""
        fake_id = uuid.uuid4()
        resp = await client.post(
            f"/api/v1/planters/{fake_id}/logs",
            json={"body": "No planter"},
            headers={"Authorization": "Bearer test-token"},
        )
        assert resp.status_code == 404
        assert resp.json()["detail"] == "planter_not_found"

    async def test_create_log_planter_already_bloomed(
        self, client: AsyncClient, louge_planter
    ):
        """status=louge のPlanterへのLog投稿: 400"""
        resp = await client.post(
            f"/api/v1/planters/{louge_planter.id}/logs",
            json={"body": "Too late"},
            headers={"Authorization": "Bearer test-token"},
        )
        assert resp.status_code == 400
        assert resp.json()["detail"] == "planter_already_bloomed"

    async def test_create_log_invalid_parent_log(
        self, client: AsyncClient, planter
    ):
        """存在しないparent_log_id: 400"""
        fake_log_id = uuid.uuid4()
        resp = await client.post(
            f"/api/v1/planters/{planter.id}/logs",
            json={"body": "Reply", "parent_log_id": str(fake_log_id)},
            headers={"Authorization": "Bearer test-token"},
        )
        assert resp.status_code == 400
        assert resp.json()["detail"] == "invalid_parent_log"

    async def test_create_log_nested_reply_not_allowed(
        self, client: AsyncClient, planter, db_session: AsyncSession, test_user
    ):
        """2段ネスト返信: 400"""
        # Create parent log
        parent = Log(
            planter_id=planter.id,
            user_id=test_user.id,
            body="Parent log",
            is_ai_generated=False,
        )
        db_session.add(parent)
        await db_session.commit()
        await db_session.refresh(parent)

        # Create reply to parent
        reply = Log(
            planter_id=planter.id,
            user_id=test_user.id,
            body="Reply",
            parent_log_id=parent.id,
            is_ai_generated=False,
        )
        db_session.add(reply)
        await db_session.commit()
        await db_session.refresh(reply)

        # Try to reply to the reply (nested)
        resp = await client.post(
            f"/api/v1/planters/{planter.id}/logs",
            json={"body": "Nested reply", "parent_log_id": str(reply.id)},
            headers={"Authorization": "Bearer test-token"},
        )
        assert resp.status_code == 400
        assert resp.json()["detail"] == "nested_reply_not_allowed"

    async def test_create_log_empty_body(self, client: AsyncClient, planter):
        """空body: 422"""
        resp = await client.post(
            f"/api/v1/planters/{planter.id}/logs",
            json={"body": ""},
            headers={"Authorization": "Bearer test-token"},
        )
        assert resp.status_code == 422

    async def test_create_log_body_too_long(self, client: AsyncClient, planter):
        """5000文字超: 422"""
        resp = await client.post(
            f"/api/v1/planters/{planter.id}/logs",
            json={"body": "a" * 5001},
            headers={"Authorization": "Bearer test-token"},
        )
        assert resp.status_code == 422

    async def test_create_log_with_valid_reply(
        self, client: AsyncClient, planter, db_session: AsyncSession, test_user
    ):
        """有効なparent_log_idへの返信: 201"""
        parent = Log(
            planter_id=planter.id,
            user_id=test_user.id,
            body="Parent",
            is_ai_generated=False,
        )
        db_session.add(parent)
        await db_session.commit()
        await db_session.refresh(parent)

        resp = await client.post(
            f"/api/v1/planters/{planter.id}/logs",
            json={"body": "Reply to parent", "parent_log_id": str(parent.id)},
            headers={"Authorization": "Bearer test-token"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["log"]["parent_log_id"] == str(parent.id)


class TestListLogs:
    """GET /api/v1/planters/{planter_id}/logs"""

    async def test_list_logs_empty(self, client: AsyncClient, planter):
        """Logなし: 空リスト"""
        resp = await client.get(f"/api/v1/planters/{planter.id}/logs")
        assert resp.status_code == 200
        data = resp.json()
        assert data["items"] == []
        assert data["has_next"] is False

    async def test_list_logs_with_items(
        self, client: AsyncClient, planter, db_session: AsyncSession, test_user
    ):
        """Logあり: リストが返る"""
        for i in range(3):
            log = Log(
                planter_id=planter.id,
                user_id=test_user.id,
                body=f"Log {i}",
                is_ai_generated=False,
            )
            db_session.add(log)
            await db_session.flush()
        await db_session.commit()

        resp = await client.get(f"/api/v1/planters/{planter.id}/logs")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) == 3
        bodies = {item["body"] for item in data["items"]}
        assert bodies == {"Log 0", "Log 1", "Log 2"}

    async def test_list_logs_with_replies(
        self, client: AsyncClient, planter, db_session: AsyncSession, test_user
    ):
        """返信がrepliesにネストされる"""
        parent = Log(
            planter_id=planter.id,
            user_id=test_user.id,
            body="Parent log",
            is_ai_generated=False,
        )
        db_session.add(parent)
        await db_session.flush()
        await db_session.refresh(parent)

        reply = Log(
            planter_id=planter.id,
            user_id=test_user.id,
            body="Reply to parent",
            parent_log_id=parent.id,
            is_ai_generated=False,
        )
        db_session.add(reply)
        await db_session.commit()

        resp = await client.get(f"/api/v1/planters/{planter.id}/logs")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) == 1  # Only top-level
        assert data["items"][0]["body"] == "Parent log"
        assert len(data["items"][0]["replies"]) == 1
        assert data["items"][0]["replies"][0]["body"] == "Reply to parent"

    async def test_list_logs_unauthenticated(self, client: AsyncClient, planter):
        """非認証でも取得可能"""
        resp = await client.get(f"/api/v1/planters/{planter.id}/logs")
        assert resp.status_code == 200

    async def test_list_logs_planter_not_found(self, client: AsyncClient):
        """存在しないPlanter: 404"""
        fake_id = uuid.uuid4()
        resp = await client.get(f"/api/v1/planters/{fake_id}/logs")
        assert resp.status_code == 404

    async def test_list_logs_pagination(
        self, client: AsyncClient, planter, db_session: AsyncSession, test_user
    ):
        """カーソルページネーション (時刻をずらして検証)"""
        from datetime import datetime, timedelta, timezone

        base_time = datetime(2026, 1, 1, tzinfo=timezone.utc)
        for i in range(5):
            log = Log(
                planter_id=planter.id,
                user_id=test_user.id,
                body=f"Log {i}",
                is_ai_generated=False,
                created_at=base_time + timedelta(minutes=i),
            )
            db_session.add(log)
        await db_session.commit()

        # First page
        resp = await client.get(
            f"/api/v1/planters/{planter.id}/logs", params={"limit": 3}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) == 3
        assert data["has_next"] is True
        assert data["next_cursor"] is not None

        # Second page
        resp2 = await client.get(
            f"/api/v1/planters/{planter.id}/logs",
            params={"limit": 3, "cursor": data["next_cursor"]},
        )
        assert resp2.status_code == 200
        data2 = resp2.json()
        assert len(data2["items"]) == 2
        assert data2["has_next"] is False

        # All 5 logs returned across both pages
        all_bodies = {item["body"] for item in data["items"] + data2["items"]}
        assert len(all_bodies) == 5
