import os

from aiohttp import web


async def api_ping(request):
    return web.json_response({'msg': 'pong'}, status=200)


async def api_dir_list(request):
    # returns a list of files and folders of the current directory
    # for a file - relative path, date created, last modified, file size
    # for a folder - relative path
    pass


async def api_dir_download(request):
    # download a directory from the server as .zip
    pass


async def api_file_download(request):
    # download a file from the server
    pass


async def api_get_file(request):
    # # returns a file from the server to display in the browser
    pass


async def api_path_new(request):
    # create a new file or directory
    pass


async def api_path_copy(request):
    # create a copy of the file or directory
    pass


async def api_path_move(request):
    # move a file to a new directory,
    #  if the directory is the same and the file has a new name, just rename it
    #  otherwise we will return an error
    pass


async def api_path_remove(request):
    # remove a path from the server
    data = await request.json()
    file_path = data['path']
    pass


app = web.Application()
app.router.add_route('GET', '/api/ping', api_ping)

app.router.add_route('GET', '/api/dir/list', api_dir_list)
app.router.add_route('GET', '/api/dir/download', api_dir_download)


app.router.add_route('POST', '/api/path/new', api_path_new)
app.router.add_route('POST', '/api/path/copy', api_path_copy)
app.router.add_route('POST', '/api/path/move', api_path_move)

app.router.add_route('DELETE', '/api/path/remove', api_path_remove)


if __name__ == '__main__':
    web.run_app(app, host='0.0.0.0', port=3000)
