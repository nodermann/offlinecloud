import pytest

import os
import uuid

import aiohttp


@pytest.fixture
def base_url():
    return os.getenv("OFFCLOUD_BASEURL", "http://127.0.0.1:3000")


@pytest.fixture
async def session(base_url):
    async with aiohttp.ClientSession(base_url=base_url) as session:
        yield session


@pytest.fixture
def random_string():
    return f"/{uuid.uuid4()}"


@pytest.fixture
async def tmp(session, random_string):
    async with session.post("/api/dir/new", json={"path": random_string}) as resp:
        assert resp.status == 201

    try:
        yield random_string
    finally:
        async with session.post("/api/dir/remove", json={"path": random_string}) as resp:
            assert resp.status == 200


@pytest.fixture
def j():
    def join(*paths: str):
        return os.path.join(*paths)

    return join


@pytest.fixture
def p():
    def path(path_: str):
        return {"path": path_}

    return path


@pytest.fixture
def sd():
    def srcdest(src: str, dest: str):
        return {"src": src, "dest": dest}

    return srcdest
