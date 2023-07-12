from aiohttp import web


def generic_json(status_code: int, message: str) -> web.Response:
    return web.json_response({'error': message}, status=status_code)


def exception(e: Exception, status_code: int = 400) -> web.Response:
    return generic_json(status_code, f"{type(e).__name__}: '{e}'")


def path_is_busy(path: str, status_code: int = 400) -> web.Response:
    return generic_json(status_code, f"'{path}' is busy")


# normally we should never see this response
def dangerous_path(path: str, status_code: int = 400) -> web.Response:
    return generic_json(status_code, f"'DANGER: {path}'")


def path_not_a_file(path: str, status_code: int = 400) -> web.Response:
    return generic_json(status_code, f"'{path}' is not a file")


def path_not_a_dir(path: str, status_code: int = 400) -> web.Response:
    return generic_json(status_code, f"'{path}' is not a dir")


def path_not_found(path: str, status_code: int = 400) -> web.Response:
    return generic_json(status_code, f"'{path}' not found")


def path_already_exists(path: str, status_code: int = 400) -> web.Response:
    return generic_json(status_code, f"'{path}' already exists")


def src_dest_same(src: str, dest: str, status_code: int = 400) -> web.Response:
    return generic_json(status_code, f"'{src}' and '{dest}' are the same")


def missing_query_parameter(name: str, status_code: int = 400) -> web.Response:
    return generic_json(status_code, f"missing query parameter '{name}'")


def invalid_query_parameter(name: str, status_code: int = 400) -> web.Response:
    return generic_json(status_code, f"invalid query parameter '{name}'")


def missing_json_key(name: str, status_code: int = 400) -> web.Response:
    return generic_json(status_code, f"missing json key '{name}'")


def invalid_json_key(name: str, status_code: int = 400) -> web.Response:
    return generic_json(status_code, f"invalid json key '{name}'")


def missing_multipart(name: str, status_code: int = 400) -> web.Response:
    return generic_json(status_code, f"missing multipart value '{name}'")


def invalid_multipart(name: str, status_code: int = 400) -> web.Response:
    return generic_json(status_code, f"invalid multipart value '{name}'")
