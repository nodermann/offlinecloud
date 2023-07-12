import os

from aiohttp import web

from api import storage
from api import exceptions
from api.responses import errors
from api.responses import messages
from api.routes import dir
from api.routes import file
from api.routes import ping


@web.middleware
async def exception_handler(request, handler):
    try:
        resp = await handler(request)

    # storage exceptions
    except storage.BusyPath as e:
        return errors.path_is_busy(e.path)
    except storage.DangerousPath as e:
        return errors.dangerous_path(e.path)
    except storage.NotFound as e:
        return errors.path_not_found(e.path)
    except storage.AlreadyExists as e:
        return errors.path_already_exists(e.path)
    except storage.NotAFile as e:
        return errors.path_not_a_file(e.path)
    except storage.NotADir as e:
        return errors.path_not_a_dir(e.path)
    except storage.SameSrcDest as e:
        return errors.src_dest_same(e.src, e.dest)

    # arguments validation specific exceptions
    except exceptions.NoQueryParameter as e:
        return errors.missing_query_parameter(e.name)
    except exceptions.InvalidQueryParameter as e:
        return errors.invalid_query_parameter(e.name)
    except exceptions.NoJsonKey as e:
        return errors.missing_json_key(e.name)
    except exceptions.InvalidJsonKey as e:
        return errors.invalid_json_key(e.name)
    except exceptions.NoMultipart as e:
        return errors.missing_multipart(e.name)
    except exceptions.InvalidMultipart as e:
        return errors.invalid_multipart(e.name)

    # clients must know all internal errors!
    except Exception as e:
        return errors.exception(e)

    return resp


async def create_app() -> web.Application:
    app = web.Application(middlewares=[exception_handler])

    app["S"] = storage.Storage(
            os.path.abspath(os.getenv("OFFCLOUD_DATAROOT", "/tmp")))

    app.router.add_routes(dir.routes)
    app.router.add_routes(file.routes)
    app.router.add_routes(ping.routes)

    app.router.add_static("/data/", path=app["S"].root, name="static")

    return app

