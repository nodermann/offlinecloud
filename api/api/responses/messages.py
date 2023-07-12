from aiohttp import web


def generic_json(status_code: int, message: str) -> web.Response:
    return web.json_response({"message": message}, status=status_code)


def pong() -> web.Response:
    return generic_json(200, "pong")


def OK() -> web.Response:
    return generic_json(200, "OK")


def Created() -> web.Response:
    return generic_json(201, "OK")


def result(json_encodable, status_code: int) -> web.Response:
    return web.json_response({"result": json_encodable}, status=200)
