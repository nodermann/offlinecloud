import pytest


async def test_api_ping(session):
    async with session.get("/api/ping") as resp:
        assert resp.status == 200
        assert await resp.json() == {"message": "pong"}
