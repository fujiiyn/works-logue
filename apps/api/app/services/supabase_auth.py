import time
import uuid
from dataclasses import dataclass

import httpx
from jose import JWTError, jwt


@dataclass
class AuthUser:
    sub: uuid.UUID
    email: str | None
    user_metadata: dict


class SupabaseAuthError(Exception):
    pass


class SupabaseAuthClient:
    def __init__(self, supabase_url: str, anon_key: str, service_role_key: str) -> None:
        self._supabase_url = supabase_url
        self._anon_key = anon_key
        self._service_role_key = service_role_key
        self._jwks_url = f"{supabase_url}/auth/v1/.well-known/jwks.json"
        self._jwks_cache: dict | None = None
        self._jwks_cache_time: float = 0.0
        self._jwks_ttl: float = 3600.0  # 1 hour

    async def _get_jwks(self) -> dict:
        now = time.monotonic()
        if self._jwks_cache and (now - self._jwks_cache_time) < self._jwks_ttl:
            return self._jwks_cache

        async with httpx.AsyncClient() as client:
            resp = await client.get(self._jwks_url)
            resp.raise_for_status()
            self._jwks_cache = resp.json()
            self._jwks_cache_time = now
            return self._jwks_cache

    async def verify_token(self, token: str) -> AuthUser:
        jwks = await self._get_jwks()
        try:
            payload = jwt.decode(
                token,
                jwks,
                algorithms=["RS256"],
                audience="authenticated",
            )
        except JWTError as e:
            raise SupabaseAuthError(f"JWT verification failed: {e}") from e

        return AuthUser(
            sub=uuid.UUID(payload["sub"]),
            email=payload.get("email"),
            user_metadata=payload.get("user_metadata", {}),
        )

    async def get_user_metadata(self, auth_id: uuid.UUID) -> dict:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self._supabase_url}/auth/v1/admin/users/{auth_id}",
                headers={
                    "apikey": self._service_role_key,
                    "Authorization": f"Bearer {self._service_role_key}",
                },
            )
            resp.raise_for_status()
            data = resp.json()
            meta = data.get("user_metadata", {})
            return {
                "display_name": meta.get("full_name") or meta.get("name") or "",
                "email": data.get("email", ""),
                "avatar_url": meta.get("avatar_url"),
            }
