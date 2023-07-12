import pytest

import aiohttp


def file(size: int = 1024 ** 2):
    with open("/dev/urandom", "rb") as f:
        yield f.read(256 * 1024)


async def test_api_file_mix(p, j, tmp, session):
    async with session.get("/api/dir/list", params=p(tmp)) as resp:
        assert await resp.json() == {"result": []}

    d1 = j(tmp, "d1")
    f1 = j(d1, "d2", "d3", "f1")
    with aiohttp.MultipartWriter("x69") as mpw:
        mpw.append(f1)
        mpw.append(b"<3" * 1024 ** 2)

        async with session.post("/api/file/upload", data=mpw) as resp:
            assert resp.status == 201

    async with session.get("/api/dir/list", params=p(tmp)) as resp:
        assert await resp.json() == {"result": [{"path": d1, "type": "d"}]}

    d3 = j(d1, "d2", "d3")
    async with session.get("/api/dir/list", params=p(d3)) as resp:
        assert await resp.json() == {"result": [{"path": f1, "type": "f"}]}

    async with session.get("/api/file/download", params=p(f1)) as resp:
        #TODO
        pass


async def test_api_file_new(p, j, tmp, session):
    async with session.get("/api/dir/list", params=p(tmp)) as resp:
        assert await resp.json() == {"result": []}

    f1 = j(tmp, "f1")
    async with session.post("/api/file/new", json=p(f1)) as resp:
        assert resp.status == 201

    f2 = j(tmp, "f2")
    async with session.post("/api/file/new", json=p(f2)) as resp:
        assert resp.status == 201

    async with session.get("/api/dir/list", params=p(tmp)) as resp:
        assert await resp.json() == {"result":
                 [{"path": f1, "type": "f"}, {"path": f2, "type":"f"}]}


async def test_api_file_copy(p, j, sd, tmp, session):
    async with session.get("/api/dir/list", params=p(tmp)) as resp:
        assert await resp.json() == {"result": []}

    f1 = j(tmp, "f1")
    async with session.post("/api/file/new", json=p(f1)) as resp:
        assert resp.status == 201

    f2 = j(tmp, "f2")
    async with session.post("/api/file/copy", json=sd(f1, f2)) as resp:
        assert resp.status == 200

    async with session.get("/api/dir/list", params=p(tmp)) as resp:
        assert await resp.json() == {"result":
                 [{"path": f1, "type": "f"}, {"path": f2, "type":"f"}]}


async def test_api_file_move(p, j, sd, tmp, session):
    async with session.get("/api/dir/list", params=p(tmp)) as resp:
        assert await resp.json() == {"result": []}

    f1 = j(tmp, "f1")
    async with session.post("/api/file/new", json=p(f1)) as resp:
        assert resp.status == 201

    f2 = j(tmp, "f2")
    async with session.post("/api/file/move", json=sd(f1, f2)) as resp:
        assert resp.status == 200

    async with session.get("/api/dir/list", params=p(tmp)) as resp:
        assert await resp.json() == {"result": [{"path": f2, "type": "f"}]}


async def test_api_file_remove(p, j, tmp, session):
    async with session.get("/api/dir/list", params=p(tmp)) as resp:
        assert await resp.json() == {"result": []}

    f1 = j(tmp, "f1")
    async with session.post("/api/file/new", json=p(f1)) as resp:
        assert resp.status == 201

    async with session.post("/api/file/remove", json=p(f1)) as resp:
        assert resp.status == 200

    async with session.get("/api/dir/list", params=p(tmp)) as resp:
        assert await resp.json() == {"result": []}
