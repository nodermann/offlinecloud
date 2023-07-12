from aiohttp import web

from api.responses import messages

routes = web.RouteTableDef()


@routes.get("/api/ping")
async def api_ping(request):
    return messages.pong()
