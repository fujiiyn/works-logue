import uuid
from collections.abc import AsyncIterator
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import JSON, event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.models.base import Base

# In-memory SQLite for tests
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


def _adapt_schema_for_sqlite(base: type) -> None:
    """Replace PostgreSQL-specific types with SQLite-compatible ones."""
    from sqlalchemy.dialects.postgresql import JSONB

    for table in base.metadata.tables.values():
        for column in table.columns:
            if isinstance(column.type, JSONB):
                column.type = JSON()
            if column.server_default is not None:
                try:
                    text = str(column.server_default.arg) if hasattr(column.server_default, "arg") else ""
                except Exception:
                    text = ""
                if "gen_random_uuid" in text:
                    column.server_default = None


@pytest.fixture
async def db_engine():
    engine = create_async_engine(TEST_DATABASE_URL)
    _adapt_schema_for_sqlite(Base)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def db_session(db_engine) -> AsyncIterator[AsyncSession]:
    session_maker = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    async with session_maker() as session:
        yield session


@pytest.fixture
def mock_auth_user_sub() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def mock_verify_token(mock_auth_user_sub):
    from app.services.supabase_auth import AuthUser

    mock = AsyncMock(
        return_value=AuthUser(
            sub=mock_auth_user_sub,
            email="test@example.com",
            user_metadata={"full_name": "Test User"},
        )
    )
    return mock


@pytest.fixture
def mock_get_user_metadata():
    return AsyncMock(
        return_value={
            "display_name": "Test User",
            "email": "test@example.com",
            "avatar_url": None,
        }
    )


@pytest.fixture
async def client(db_engine, mock_verify_token, mock_get_user_metadata) -> AsyncIterator[AsyncClient]:
    from app.database import get_db
    from app.main import app

    session_maker = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)

    async def override_get_db() -> AsyncIterator[AsyncSession]:
        async with session_maker() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    with (
        patch(
            "app.dependencies.SupabaseAuthClient.verify_token",
            mock_verify_token,
        ),
        patch(
            "app.dependencies.SupabaseAuthClient.get_user_metadata",
            mock_get_user_metadata,
        ),
    ):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as ac:
            yield ac

    app.dependency_overrides.clear()
