import contextlib
import os
import urllib.parse
import shutil
from typing import Dict
from typing import List
from datetime import datetime

from aiohttp import web
from aiohttp import hdrs
from stream_zip import ZIP_32
from stream_zip import stream_zip

from api import storage
from api import exceptions
from api.responses import messages

Headers = Dict[str, str]
routes = web.RouteTableDef()


async def retrieve_json_key(req: web.Request, key: str) -> str:
    data = await req.json()

    try:
        return data[key]
    except KeyError:
        raise exceptions.NoJsonKey(key)


@contextlib.asynccontextmanager
async def acquire_rlocked_existing_dir(req: web.Request):
    try:
        path: str = req.query["path"]
    except KeyError:
        raise exceptions.NoQueryParameter("path")

    try:
        real_path: str = req.app["S"].resolve(path)
    except storage.DangerousPath:
        raise exceptions.InvalidQueryParameter("path")

    with req.app["S"].acquire_rlocked_dir(real_path):
        if not os.path.exists(real_path):
            raise storage.NotFound(path)
        if not os.path.isdir(real_path):
            raise storage.NotADir(path)

        yield real_path


def get_pathtype(path: str) -> str:
    if os.path.isdir(path): return "d"
    if os.path.isfile(path): return "f"
    return "?"


def iterate_over_absolute_paths(path: str):
    def normalize_path(e: str):
        return os.path.abspath(os.path.join(path, e))


    for e in map(normalize_path, os.listdir(path)):
        yield e
        


@routes.get("/api/dir/list")
async def api_dir_list(req: web.Request):
    async with acquire_rlocked_existing_dir(req) as real_path:
        result: List = []

        for path in iterate_over_absolute_paths(real_path):
            trimmed_path = req.app["S"].trim_root(path)

            result.append({
                "path": trimmed_path,
                "type": get_pathtype(path),
            })

        return messages.result(result, 200)


def recursively_iterate_over_directory(path: str):
    for p in iterate_over_absolute_paths(path):
        if os.path.isdir(p):
            yield from recursively_iterate_over_directory(p)
        else:
            yield p


def bytesgen(path: str, chunk_size: int = 8 * 1024):
    with open(path, "rb") as f:
        yield f.read(chunk_size)
    

async def create_chunked_response(req: web.Request, h: Headers) -> web.StreamResponse:
    resp = web.StreamResponse(headers=h)
    resp.enable_chunked_encoding()
    await resp.prepare(req)

    return resp


def member_files(path: str, path_trimmer):
    modified_at = datetime.now()
    perms = 0o600

    for p in recursively_iterate_over_directory(path):
        yield path_trimmer(p), modified_at, perms, ZIP_32, bytesgen(p)


def startswith(s: str, prefix: str) -> bool:
    return s[:len(prefix)] == prefix


def remove_prefix(s: str, prefix: str) -> str:
    if startswith(s, prefix):
        s = s[len(prefix):]

    return s


@routes.get("/api/dir/download")
async def api_dir_download(req: web.Request):
    async with acquire_rlocked_existing_dir(req) as real_path:
        filename = f"{urllib.parse.quote(os.path.basename(real_path))}.zip"

        headers: Headers = {
            hdrs.CONTENT_DISPOSITION: f'attachment; filename="{filename}"',
            hdrs.CONTENT_TYPE: "application/zip",
        }

        def root_trimmer(p: str) -> str:
            return remove_prefix(req.app["S"].trim_root(p), "/")

        resp = await create_chunked_response(req, headers)

        for chunk in stream_zip(member_files(real_path, root_trimmer)):
            await resp.write(chunk)

        return resp



@routes.post("/api/dir/new")
async def api_dir_new(req: web.Request):
    path = await retrieve_json_key(req, "path")

    try:
        await req.app["S"].new_dir(path)
    except storage.DangerousPath:
        return exceptions.InvalidJsonKey("path")

    return messages.Created()


@routes.post("/api/dir/copy")
async def api_dir_copy(req: web.Request):
    src = await retrieve_json_key(req, "src")
    dest = await retrieve_json_key(req, "dest")

    try:
        await req.app["S"].copy_dir(src, dest)
    except storage.DangerousPath as e:
        raise exceptions.InvalidJsonKey(e.path == src and "src" or "dest")

    return messages.OK()


@routes.post("/api/dir/move")
async def api_dir_move(req: web.Request):
    src = await retrieve_json_key(req, "src")
    dest = await retrieve_json_key(req, "dest")

    try:
        await req.app["S"].move_dir(src, dest)
    except storage.DangerousPath as e:
        raise exceptions.InvalidJsonKey(e.path == src and "src" or "dest")

    return messages.OK()


@routes.post("/api/dir/remove")
async def api_dir_remove(req: web.Request):
    path = await retrieve_json_key(req, "path")

    try:
        await req.app["S"].remove_dir(path)
    except storage.DangerousPath:
        raise exceptions.InvalidJsonKey("path")

    return messages.OK()
