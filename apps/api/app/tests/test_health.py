class TestHealthCheck:
    async def test_health_returns_ok(self, client):
        """GET /health should return 200 with status ok."""
        resp = await client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}
