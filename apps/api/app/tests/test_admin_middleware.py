"""U7 Step 3: tests for require_admin dependency.

Contract:
  - Any failure (unauthenticated, non-admin, banned, deleted) returns 404.
  - On success, structlog emits exactly one event=admin.access with
    actor_user_id, path, method.
"""
from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import UTC, datetime
from unittest.mock import patch

import pytest
import structlog
from fastapi import Depends, FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.database import get_db
from app.dependencies_admin import require_admin
from app.models.user import User


@pytest.fixture(autouse=True)
def _restore_structlog_config():
    yield
    structlog.reset_defaults()


def _configure_capture() -> list[dict]:
    captured: list[dict] = []

    def _capture(_logger, _method_name, event_dict):
        captured.append(dict(event_dict))
        raise structlog.DropEvent

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            _capture,
        ],
        wrapper_class=structlog.make_filtering_bound_logger(0),
        cache_logger_on_first_use=False,
    )
    return captured


@pytest.fixture
async def admin_app(
    db_engine,
    mock_verify_token,
    mock_get_user_metadata,
) -> AsyncIterator[tuple[AsyncClient, list[dict]]]:
    """Tiny FastAPI app exposing a single endpoint guarded by require_admin."""
    captured = _configure_capture()

    test_app = FastAPI()

    @test_app.get("/_admin_test")
    async def admin_test_endpoint(
        user: User = Depends(require_admin),  # noqa: B008  -- canonical FastAPI dependency pattern
    ) -> dict:
        return {"id": str(user.id), "role": user.role}

    session_maker = async_sessionmaker(
        db_engine, class_=AsyncSession, expire_on_commit=False
    )

    async def override_get_db() -> AsyncIterator[AsyncSession]:
        async with session_maker() as session:
            yield session

    test_app.dependency_overrides[get_db] = override_get_db

    try:
        with (
            patch(
                "app.dependencies_admin.get_auth_client",
                lambda: type("Stub", (), {
                    "verify_token": mock_verify_token,
                    "get_user_metadata": mock_get_user_metadata,
                })(),
            ),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=test_app), base_url="http://test"
            ) as ac:
                yield ac, captured
    finally:
        test_app.dependency_overrides.clear()


AUTH_HEADERS = {"Authorization": "Bearer valid-token"}


async def test_unauthenticated_returns_404(admin_app):
    client, _captured = admin_app
    resp = await client.get("/_admin_test")
    assert resp.status_code == 404


async def test_regular_user_returns_404(admin_app, db_session, mock_auth_user_sub):
    client, _captured = admin_app
    db_session.add(
        User(auth_id=mock_auth_user_sub, display_name="Regular", role="user")
    )
    await db_session.commit()

    resp = await client.get("/_admin_test", headers=AUTH_HEADERS)
    assert resp.status_code == 404


async def test_banned_admin_returns_404(admin_app, db_session, mock_auth_user_sub):
    client, _captured = admin_app
    db_session.add(
        User(
            auth_id=mock_auth_user_sub,
            display_name="Banned Admin",
            role="admin",
            is_banned=True,
        )
    )
    await db_session.commit()

    resp = await client.get("/_admin_test", headers=AUTH_HEADERS)
    assert resp.status_code == 404


async def test_soft_deleted_admin_returns_404(
    admin_app, db_session, mock_auth_user_sub
):
    client, _captured = admin_app
    db_session.add(
        User(
            auth_id=mock_auth_user_sub,
            display_name="Deleted Admin",
            role="admin",
            deleted_at=datetime.now(UTC),
        )
    )
    await db_session.commit()

    resp = await client.get("/_admin_test", headers=AUTH_HEADERS)
    assert resp.status_code == 404


async def test_valid_admin_passes_and_logs(
    admin_app, db_session, mock_auth_user_sub
):
    client, captured = admin_app
    db_session.add(
        User(auth_id=mock_auth_user_sub, display_name="Valid Admin", role="admin")
    )
    await db_session.commit()

    resp = await client.get("/_admin_test", headers=AUTH_HEADERS)
    assert resp.status_code == 200
    assert resp.json()["role"] == "admin"

    access_events = [e for e in captured if e.get("event") == "admin.access"]
    assert len(access_events) == 1
    evt = access_events[0]
    assert evt["path"] == "/_admin_test"
    assert evt["method"] == "GET"
    assert "actor_user_id" in evt


async def test_invalid_token_returns_404(admin_app, mock_verify_token):
    """An auth error from Supabase must collapse to 404, not 401."""
    from app.services.supabase_auth import SupabaseAuthError

    client, _captured = admin_app
    mock_verify_token.side_effect = SupabaseAuthError("bad token")
    try:
        resp = await client.get("/_admin_test", headers=AUTH_HEADERS)
        assert resp.status_code == 404
    finally:
        mock_verify_token.side_effect = None


async def test_failure_path_does_not_emit_admin_access(
    admin_app, db_session, mock_auth_user_sub
):
    """admin.access must NOT be logged when authorization fails."""
    client, captured = admin_app
    db_session.add(
        User(auth_id=mock_auth_user_sub, display_name="Regular", role="user")
    )
    await db_session.commit()

    resp = await client.get("/_admin_test", headers=AUTH_HEADERS)
    assert resp.status_code == 404
    assert not any(e.get("event") == "admin.access" for e in captured)
