import asyncio
from aiohttp import web
import aiofiles

from aiohttp.abc import StreamResponse, BaseRequest


async def archivate(request: BaseRequest) -> StreamResponse:
    response = web.StreamResponse()

    archive_hash = request.match_info.get('archive_hash')
    root_photos_dir = 'test_photos'
    archive_filename = 'archive.zip'

    response.headers['Content-Disposition'] = f'attachment; filename="{archive_filename}"'
    await response.prepare(request)

    cmd = ('zip', '-r', '-', archive_hash)

    archiving = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=root_photos_dir,
    )

    chunk_size_in_bytes = 200 * 2024

    while not archiving.stdout.at_eof():
        await response.write(await archiving.stdout.read(n=chunk_size_in_bytes))

    return response


async def handle_index_page(request):
    async with aiofiles.open('index.html', mode='r') as index_file:
        index_contents = await index_file.read()
    return web.Response(text=index_contents, content_type='text/html')


if __name__ == '__main__':
    app = web.Application()
    app.add_routes([
        web.get('/', handle_index_page),
        web.get('/archive/{archive_hash}/', archivate),
    ])
    web.run_app(app)
