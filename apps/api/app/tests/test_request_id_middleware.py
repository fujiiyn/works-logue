"""U7 Step 2: tests for RequestIdMiddleware + structlog contextvar binding."""
from __future__ import annotations

import pytest
import structlog
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from starlette.middleware.cors import CORSMiddleware

from app.middleware.request_id import RequestIdMiddleware, get_request_id


@pytest.fixture(autouse=True)
def _restore_structlog_config():
    """structlog.configure mutates global state; reset after each test."""
    yield
    structlog.reset_defaults()


def _build_app() -> tuple[FastAPI, list[dict]]:
    captured: list[dict] = []

    def _capture(_logger, _method_name, event_dict):
        captured.append(dict(event_dict))
        # Drop the event so the default PrintLogger isn't asked to render it.
        raise structlog.DropEvent

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            _capture,
        ],
        wrapper_class=structlog.make_filtering_bound_logger(0),
        cache_logger_on_first_use=False,
    )

    app = FastAPI()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RequestIdMiddleware)

    log = structlog.get_logger()

    @app.get("/probe")
    async def probe() -> dict:
        # Two log calls within the same request must share request_id.
        log.info("probe.first")
        log.info("probe.second")
        return {"request_id": get_request_id()}

    return app, captured


async def test_same_request_shares_request_id() -> None:
    app, captured = _build_app()
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        resp = await ac.get("/probe")

    assert resp.status_code == 200
    rid_in_response = resp.json()["request_id"]
    assert rid_in_response is not None
    assert resp.headers["X-Request-ID"] == rid_in_response

    # Both log entries must have the same request_id, equal to the body.
    rids = [
        e["request_id"]
        for e in captured
        if e.get("event") in {"probe.first", "probe.second"}
    ]
    assert len(rids) == 2
    assert rids[0] == rids[1] == rid_in_response


async def test_different_requests_have_different_ids() -> None:
    app, captured = _build_app()
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        r1 = await ac.get("/probe")
        r2 = await ac.get("/probe")

    rid1 = r1.json()["request_id"]
    rid2 = r2.json()["request_id"]
    assert rid1 != rid2
    assert r1.headers["X-Request-ID"] == rid1
    assert r2.headers["X-Request-ID"] == rid2


async def test_inbound_x_request_id_is_honored() -> None:
    """If the caller already supplies X-Request-ID, propagate it through."""
    app, _captured = _build_app()
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        resp = await ac.get("/probe", headers={"X-Request-ID": "trace-abc-123"})

    assert resp.status_code == 200
    assert resp.json()["request_id"] == "trace-abc-123"
    assert resp.headers["X-Request-ID"] == "trace-abc-123"


async def test_context_is_cleared_between_requests() -> None:
    """After a request finishes, the contextvar must not leak."""
    app, _captured = _build_app()
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        await ac.get("/probe")

    # Outside any request, the ContextVar default is None.
    assert get_request_id() is None
