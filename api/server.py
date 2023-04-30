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


async def api_file_view(request):
    # view the file in the browser
    pass


async def api_file_download(request):
    # download a file from the server
    pass


async def api_dir_new(request):
    # create a new directory
    pass


async def api_dir_upload(request):
    # upload a directory with files
    pass


async def api_dir_copy(request):
    # copy a directory with files
    pass


async def api_dir_move(request):
    # move a directory with files
    pass


async def api_dir_remove(request):
    # remove the whole directory with all files
    pass


async def api_file_new(request):
    # create an empty file
    pass


async def api_file_upload(request):
    # upload a file to the server
    pass


async def api_file_copy(request):
    # create a copy of the file
    pass


async def api_file_move(request):
    # move a file to a new directory,
    #  if the directory is the same and the file has a new name, just rename it
    #  otherwise we will return an error
    pass


async def api_file_remove(request):
    # remove a file from the server
    pass


app = web.Application()
app.router.add_route('GET', '/api/ping', api_ping)

app.router.add_route('GET', '/api/dir/list', api_dir_list)
app.router.add_route('GET', '/api/dir/download', api_dir_download)

app.router.add_route('GET', '/api/file/view', api_file_view)
app.router.add_route('GET', '/api/file/download', api_file_download)

app.router.add_route('POST', '/api/dir/new', api_dir_new)
app.router.add_route('POST', '/api/dir/upload', api_dir_upload)
app.router.add_route('POST', '/api/dir/copy', api_dir_copy)
app.router.add_route('POST', '/api/dir/move', api_dir_move)
app.router.add_route('POST', '/api/dir/remove', api_dir_remove)

app.router.add_route('POST', '/api/file/new', api_file_new)
app.router.add_route('POST', '/api/file/upload', api_file_upload)
app.router.add_route('POST', '/api/file/copy', api_file_copy)
app.router.add_route('POST', '/api/file/move', api_file_move)
app.router.add_route('POST', '/api/file/remove', api_file_remove)


if __name__ == '__main__':
    web.run_app(app, host='0.0.0.0', port=3000)
