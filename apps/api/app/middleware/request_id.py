import uuid
from contextvars import ContextVar

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

_request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)


def get_request_id() -> str | None:
    return _request_id_var.get()


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Generate a per-request UUID, expose it via ContextVar and structlog.

    Registered AFTER CORSMiddleware in main.py so it runs as the OUTER layer:
    every request (including CORS preflight) receives a request_id, and the
    structlog contextvar is bound for the entire request lifecycle.
    """

    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        incoming = request.headers.get("X-Request-ID")
        request_id = incoming if incoming else str(uuid.uuid4())

        token = _request_id_var.set(request_id)
        structlog.contextvars.bind_contextvars(request_id=request_id)
        try:
            response: Response = await call_next(request)
        finally:
            structlog.contextvars.unbind_contextvars("request_id")
            _request_id_var.reset(token)

        response.headers["X-Request-ID"] = request_id
        return response
