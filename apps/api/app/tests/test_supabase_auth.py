from unittest.mock import AsyncMock, patch

import pytest

from app.services.supabase_auth import SupabaseAuthClient, SupabaseAuthError


@pytest.fixture
def auth_client():
    return SupabaseAuthClient(
        supabase_url="https://test.supabase.co",
        anon_key="test-anon-key",
        service_role_key="test-service-role-key",
    )


class TestVerifyToken:
    async def test_valid_token_returns_auth_user(self, auth_client):
        """Valid JWT should return AuthUser with sub, email, metadata."""
        mock_payload = {
            "sub": "550e8400-e29b-41d4-a716-446655440000",
            "email": "user@example.com",
            "user_metadata": {"full_name": "Test User"},
            "aud": "authenticated",
        }
        with (
            patch.object(auth_client, "_get_jwks", new_callable=AsyncMock, return_value={"keys": []}),
            patch("app.services.supabase_auth.jwt.decode", return_value=mock_payload),
        ):
            result = await auth_client.verify_token("valid-token")

        assert str(result.sub) == "550e8400-e29b-41d4-a716-446655440000"
        assert result.email == "user@example.com"
        assert result.user_metadata == {"full_name": "Test User"}

    async def test_expired_token_raises_error(self, auth_client):
        """Expired JWT should raise SupabaseAuthError."""
        from jose import JWTError

        with (
            patch.object(auth_client, "_get_jwks", new_callable=AsyncMock, return_value={"keys": []}),
            patch("app.services.supabase_auth.jwt.decode", side_effect=JWTError("Token expired")),
        ):
            with pytest.raises(SupabaseAuthError, match="JWT verification failed"):
                await auth_client.verify_token("expired-token")

    async def test_invalid_signature_raises_error(self, auth_client):
        """JWT with invalid signature should raise SupabaseAuthError."""
        from jose import JWTError

        with (
            patch.object(auth_client, "_get_jwks", new_callable=AsyncMock, return_value={"keys": []}),
            patch("app.services.supabase_auth.jwt.decode", side_effect=JWTError("Invalid signature")),
        ):
            with pytest.raises(SupabaseAuthError, match="JWT verification failed"):
                await auth_client.verify_token("bad-signature-token")

    async def test_jwks_cache_reuses_cached_value(self, auth_client):
        """JWKS should be cached and reused within TTL."""
        mock_jwks = {"keys": [{"kid": "test"}]}
        auth_client._jwks_cache = mock_jwks
        auth_client._jwks_cache_time = __import__("time").monotonic()

        result = await auth_client._get_jwks()
        assert result == mock_jwks
