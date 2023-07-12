import pytest


async def test_dir_list(p, tmp, session):
    async with session.get("/api/dir/list", params=p(tmp)) as resp:
        assert resp.status == 200
        assert await resp.json() == {"result": []}


async def test_api_dir_new(p, j, tmp, session):
    async with session.get("/api/dir/list", params=p(tmp)) as resp:
        assert await resp.json() == {"result": []}

    d1 = j(tmp, "d1")
    async with session.post("/api/dir/new", json=p(d1)) as resp:
        assert resp.status == 201

    d2 = j(tmp, "d2")
    async with session.post("/api/dir/new", json=p(d2)) as resp:
        assert resp.status == 201

    async with session.get("/api/dir/list", params=p(tmp)) as resp:
        assert await resp.json() == {"result":
                 [{"path": d1, "type": "d"}, {"path": d2, "type":"d"}]}


async def test_api_dir_copy(p, j, sd, tmp, session):
    async with session.get("/api/dir/list", params=p(tmp)) as resp:
        assert await resp.json() == {"result": []}

    d1 = j(tmp, "d1")
    async with session.post("/api/dir/new", json=p(d1)) as resp:
        assert resp.status == 201

    d2 = j(tmp, "d2")
    async with session.post("/api/dir/copy", json=sd(d1, d2)) as resp:
        assert resp.status == 200

    async with session.get("/api/dir/list", params=p(tmp)) as resp:
        assert await resp.json() == {"result":
                 [{"path": d1, "type": "d"}, {"path": d2, "type":"d"}]}


async def test_api_dir_move(p, j, sd, tmp, session):
    async with session.get("/api/dir/list", params=p(tmp)) as resp:
        assert await resp.json() == {"result": []}

    d1 = j(tmp, "d1")
    async with session.post("/api/dir/new", json=p(d1)) as resp:
        assert resp.status == 201

    d2 = j(tmp, "d2")
    async with session.post("/api/dir/move", json=sd(d1, d2)) as resp:
        assert resp.status == 200

    async with session.get("/api/dir/list", params=p(tmp)) as resp:
        assert await resp.json() == {"result": [{"path": d2, "type": "d"}]}


async def test_api_dir_remove(p, j, tmp, session):
    async with session.get("/api/dir/list", params=p(tmp)) as resp:
        assert await resp.json() == {"result": []}

    d1 = j(tmp, "d1")
    async with session.post("/api/dir/new", json=p(d1)) as resp:
        assert resp.status == 201

    async with session.post("/api/dir/remove", json=p(d1)) as resp:
        assert resp.status == 200

    async with session.get("/api/dir/list", params=p(tmp)) as resp:
        assert await resp.json() == {"result": []}
