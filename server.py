import asyncio
import logging
import os
from pathlib import Path

from aiohttp import web
import aiofiles

from aiohttp.abc import StreamResponse, BaseRequest
from aiohttp.web_exceptions import HTTPNotFound


logging.basicConfig(format='%(levelname)-8s [%(asctime)s] %(message)s', level=logging.INFO)


async def archivate(request: BaseRequest) -> StreamResponse:
    archive_hash = request.match_info.get('archive_hash')
    root_photos_dir = 'test_photos'

    photos_dir_path = Path(root_photos_dir, archive_hash)
    if not os.path.exists(photos_dir_path):
        logging.error(f'Photos archive "{archive_hash}" doesn\'t exist')
        raise HTTPNotFound(
            reason=f'Архив "{archive_hash}" не существует или был удален',
        )

    response = web.StreamResponse()
    archive_filename = 'archive.zip'

    response.headers['Content-Disposition'] = f'attachment; filename="{archive_filename}"'
    await response.prepare(request)

    cmd = ('zip', '-r', '-', archive_hash)

    logging.info(f'Start archiving "{archive_hash}" folder')

    archiving = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=root_photos_dir,
    )

    chunk_size_in_bytes = 200 * 2024

    try:
        while not archiving.stdout.at_eof():
            logging.info('Sending archive chunk...')
            await response.write(await archiving.stdout.read(n=chunk_size_in_bytes))
        logging.info(f'"{archive_hash}" folder successfully archived and sent')
    except (asyncio.CancelledError, Exception, BaseException):
        logging.error("Download was interrupted")
        raise
    finally:
        archiving.kill()
        response.force_close()

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
