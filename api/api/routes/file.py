import mimetypes
import contextlib
import os
import urllib.parse

from typing import Dict

import aiohttp
import aiohttp.multipart
from aiohttp import web
from aiohttp import hdrs

from api import storage
from api import exceptions
from api.responses import messages

Headers = Dict[str, str]
routes = web.RouteTableDef()


async def create_chunked_response(req: web.Request, h: Headers) -> web.StreamResponse:
    resp = web.StreamResponse(headers=h)
    resp.enable_chunked_encoding()
    await resp.prepare(req)

    return resp


async def stream_chunks(real_path: str, chunk_size: int = 256 * 1024):
    with open(real_path, "rb") as f:
        chunk = f.read(chunk_size)

        while chunk:
            yield chunk
            chunk = f.read(chunk_size)


@contextlib.asynccontextmanager
async def acquire_rlocked_existing_file(req: web.Request):
    try:
        path: str = req.query["path"]
    except KeyError:
        raise exceptions.NoQueryParameter("path")

    try:
        real_path: str = req.app["S"].resolve(path)
    except storage.DangerousPath:
        raise exceptions.InvalidQueryParameter("path")

    with req.app["S"].acquire_rlocked_file(real_path):
        if not os.path.exists(real_path):
            raise storage.NotFound(path)
        if not os.path.isfile(real_path):
            raise storage.NotAFile(path)

        yield real_path


@routes.get("/api/file/view")
async def api_file_view(req: web.Request):
    async with acquire_rlocked_existing_file(req) as real_path:
        headers: Headers = {}
        content_type, encoding = mimetypes.guess_type(real_path)

        if content_type:
            headers[hdrs.CONTENT_TYPE] = content_type
            headers[hdrs.CONTENT_DISPOSITION] = "inline"
        else:
            filename = urllib.parse.quote(os.path.basename(real_path))
            headers[hdrs.CONTENT_TYPE] = "application/octet-stream"
            headers[hdrs.CONTENT_DISPOSITION] = f'attachment; filename="{filename}"'

        if encoding:
            headers[hdrs.CONTENT_ENCODING] = encoding

        resp = await create_chunked_response(req, headers)

        async for chunk in stream_chunks(real_path):
            await resp.write(chunk)

        return resp


@routes.get("/api/file/download")
async def api_file_download(req: web.Request):
    async with acquire_rlocked_existing_file(req) as real_path:
        content_type, encoding = mimetypes.guess_type(real_path)
        filename = urllib.parse.quote(os.path.basename(real_path))

        headers: Headers = {
            hdrs.CONTENT_DISPOSITION: f'attachment; filename="{filename}"',
            hdrs.CONTENT_TYPE: content_type or "application/octet-stream",
        }

        if encoding:
            headers[hdrs.CONTENT_ENCODING] = encoding

        resp = await create_chunked_response(req, headers)
        async for chunk in stream_chunks(real_path):
            await resp.write(chunk)

        return resp


async def retrieve_json_key(req: web.Request, key: str) -> str:
    data = await req.json()

    try:
        return data[key]
    except KeyError:
        raise exceptions.NoJsonKey(key)

@routes.post("/api/file/new")
async def api_file_new(req: web.Request):
    path = await retrieve_json_key(req, "path")

    try:
        await req.app["S"].new_file(path)
    except storage.DangerousPath:
        return exceptions.InvalidJsonKey("path")

    return messages.Created()


async def retrieve_bpr(
        mpr: aiohttp.MultipartReader, key: str) -> aiohttp.BodyPartReader:
    reader = await mpr.next()

    if not isinstance(reader, aiohttp.BodyPartReader):
        raise exceptions.NoMultipart(key)

    return reader


@routes.post("/api/file/upload")
async def api_file_upload(req: web.Request):
    reader = await req.multipart()

    path_reader = await retrieve_bpr(reader, "path")
    path: str = await path_reader.text()
    data_reader = await retrieve_bpr(reader, "data")

    try:
        await req.app["S"].save_multipart_file(data_reader, path)
    except storage.DangerousPath as e:
        raise exceptions.InvalidMultipart("path")

    return messages.Created()


@routes.post("/api/file/copy")
async def api_file_copy(req: web.Request):
    src = await retrieve_json_key(req, "src")
    dest = await retrieve_json_key(req, "dest")

    try:
        await req.app["S"].copy_file(src, dest)
    except storage.DangerousPath as e:
        raise exceptions.InvalidJsonKey(e.path == src and "src" or "dest")

    return messages.OK()


@routes.post("/api/file/move")
async def api_file_move(req: web.Request):
    src = await retrieve_json_key(req, "src")
    dest = await retrieve_json_key(req, "dest")

    try:
        await req.app["S"].move_file(src, dest)
    except storage.DangerousPath as e:
        raise exceptions.InvalidJsonKey(e.path == src and "src" or "dest")

    return messages.OK()


@routes.post("/api/file/remove")
async def api_file_remove(req: web.Request):
    path = await retrieve_json_key(req, "path")

    try:
        await req.app["S"].remove_file(path)
    except storage.DangerousPath:
        raise exceptions.InvalidJsonKey("path")

    return messages.OK()
