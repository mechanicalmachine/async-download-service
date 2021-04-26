from aiohttp import web
import aiofiles



async def archivate(request: BaseRequest) -> StreamResponse:
    response = web.StreamResponse()

    response.headers['Content-Disposition'] = 'attachment; filename="archive.zip"'

    await response.prepare(request)

    archive_hash = request.match_info.get('archive_hash')
    archiving_dir_path = Path('test_photos', archive_hash)
    # archiving_dir_path = 'test_photos'

    archiving = await asyncio.create_subprocess_exec(
        'zip',
        '-r',  # recursively
        '--base_dir cwd',
        '-',  # send result to stdout
        archiving_dir_path,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
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
