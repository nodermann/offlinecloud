import os
import shutil
from aiohttp import web
from datetime import datetime
import asyncio
from aiofile import async_open
import cgi


PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'dir')  
os.chdir(PATH)

FILE_SERVICE_CHUNK = 65_536


async def api_ping(request):
    return web.json_response({'msg': 'pong'}, status=200)


async def api_dir_list(request):
    # returns a list of files and folders of the current directory
    # for a file - relative path, date created, last modified, file size
    # for a folder - relative path
    data = await request.json()
    path = data['path']
    if os.path.exists(path):
        listdir = os.listdir(path)
        responce = dict()
        for fpath in listdir:
            real_fpath = os.path.join(os.path.dirname(path, fpath))
            if os.path.isfile(real_fpath):
                stat = os.stat(real_fpath)
                last_modified = datetime.fromtimestamp(os.path.getctime(real_fpath)).strftime('%Y-%m-%dT%H:%M')
                date_created = datetime.fromtimestamp(stat.st_atime).strftime('%Y-%m-%dT%H:%M')
                responce[fpath] = {
                    'path': real_fpath,
                    'date created': date_created,
                    'last modified': last_modified,
                    'size': stat.st_size
                }
            else:
                responce[fpath] = {'path': real_fpath}
        return web.json_response({'files': listdir}, status=200)
    else:
        return web.json_response({'error': 'path not found'}, status=400)


async def api_dir_download(request):
    # download a directory from the server as .zip
    data = await request.json()
    path = data['path']
    if not os.path.exists(path):
        return web.json_response({'error': 'path not found'}, status=400)
    if os.path.isfile(path):
        return web.json_response({'error': "it's not dir"}, status=400)

    _, zipname = os.path.split(path)
    zipname += '.zip'

    response = web.StreamResponse(
        status=200,
        reason='OK',
        headers={
            'Content-Type': 'application/zip',
            'CONTENT-DISPOSITION': f'attachment;filename={zipname}'
        }
    )
    await response.prepare(request)

    zipfile = os.path.join(os.path.dirname(os.path.realpath(__file__)), zipname)  
    shutil.make_archive(zipfile.replace('.zip', ''), 'zip', path)
    try:
        async with async_open(zipfile, 'rb') as f:
            chunk = await f.read(FILE_SERVICE_CHUNK)
            while chunk:
                await response.write(chunk)
                chunk = await f.read(FILE_SERVICE_CHUNK)
    except asyncio.CancelledError:
        # Download was interrupted
        os.remove(zipfile)
        raise

    os.remove(zipfile)
    return response


async def api_file_view(request):
    # view the file in the browser
    data = await request.json()
    path = data['path']
    if not os.path.exists(path):
        return web.json_response({'error': 'path not found'}, status=400)
    if os.path.isdir(path):
        return web.json_response({'error': "it's not a file"}, status=400)

    return web.FileResponse(path)


async def api_file_download(request):
    # download a file from the server
    data = await request.json()
    path = data['path']
    _, filename = os.path.split(path)
    if not os.path.exists(path):
        return web.json_response({'error': 'path not found'}, status=400)
    if os.path.isdir(path):
        return web.json_response({'error': "it's not a file"}, status=400)

    response = web.StreamResponse(
        status=200,
        reason='OK',
        headers={
            'Content-Type': '*/*',
            'CONTENT-DISPOSITION': f'attachment;filename={filename}'
        }
    )
    await response.prepare(request)

    try:
        async with async_open(path, 'rb') as f:
            chunk = await f.read(FILE_SERVICE_CHUNK)
            while chunk:
                await response.write(chunk)
                chunk = await f.read(FILE_SERVICE_CHUNK)
    except asyncio.CancelledError:
        # Download was interrupted
        raise

    return response


async def api_dir_new(request):
    # create a new directory
    data = await request.json()
    path = data['path']
    dirname = data['dirname']
    if os.path.exists(path):
        dir_path = os.path.join(os.path.dirname(path, dirname))
        if os.path.exists(dir_path):
            return web.json_response({'error': 'dir already exists'}, status=400)
        os.mkdir(dir_path)
        return web.json_response(status=200, reason='OK')
    else:
        return web.json_response({'error': 'path not found'}, status=400)


async def api_dir_copy(request):
    # copy a directory with files
    data = await request.json()
    src = data['src']
    dst = data['dist']
    if os.path.exists(src):
        shutil.copytree(src, dst)
    else:
        return web.json_response({'error': 'path not found'}, status=400)


async def api_dir_move(request):
    # move a directory with files
    data = await request.json()
    src = data['src']
    dst = data['dist']
    if os.path.exists(src):
        os.replace(src, dst)
        return web.json_response(status=200, reason='OK')
    else:
        return web.json_response({'error': 'path not found'}, status=400)


async def api_dir_remove(request):
    # remove the whole directory with all files
    data = await request.json()
    path = data['path']
    if os.path.exists(path):
        if os.listdir(path) == []:
            os.rmdir(path)
        else:
            shutil.rmtree(path)
        return web.json_response(status=200, reason='OK')
    else:
        return web.json_response({'error': 'path not found'}, status=400)


async def api_file_new(request):
    # create an empty file
    data = await request.json()
    file_path = data['path']
    filename = data['filename']
    if not '.' in filename:
        filename += '.txt'
        
    if os.path.exists(file_path):
        file_path = os.path.join(os.path.dirname(file_path, filename))
        if os.path.exists(file_path):
            return web.json_response({'error': 'file already exists'}, status=400)
        with open(file_path, 'w') as f:
            pass
        return web.json_response(status=200, reason='OK')
    else:
        return web.json_response({'error': 'path not found'}, status=400)


async def api_file_upload(request):
    # upload a file to the server
    _, params = cgi.parse_header(request.headers['CONTENT-DISPOSITION'])
    file_name = params['filename']
    async with async_open(file_name, 'bw') as afp:
        async for data in request.content.iter_any():
            await afp.write(data)
    return web.Response(status=201, reason='OK')


async def api_file_copy(request):
    # create a copy of the file
    data = await request.json()
    src = data['src']
    dst = data['dist']
    if os.path.exists(src):
        shutil.copy(src, dst)
    else:
        return web.json_response({'error': 'path not found'}, status=400)


async def api_file_move(request):
    # move a file to a new directory,
    #  if the directory is the same and the file has a new name, just rename it
    #  otherwise we will return an error
    data = await request.json()
    src = data['src']
    dst = data['dist']
    if os.path.exists(src):
        os.replace(src, dst)
        return web.json_response(status=200, reason='OK')
    else:
        return web.json_response({'error': 'path not found'}, status=400)


async def api_file_remove(request):
    # remove a file from the server
    data = await request.json()
    file_path = data['path']
    if os.path.exists(file_path):
        os.remove(file_path)
        return web.json_response(status=200, reason='OK')
    else:
        return web.json_response({'error': 'path not found'}, status=400)


app = web.Application()
app.router.add_route('GET', '/api/ping', api_ping)

app.router.add_route('GET', '/api/dir/list', api_dir_list)
app.router.add_route('GET', '/api/dir/download', api_dir_download)

app.router.add_route('GET', '/api/file/view', api_file_view)
app.router.add_route('GET', '/api/file/download', api_file_download)

app.router.add_route('POST', '/api/dir/new', api_dir_new)
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
