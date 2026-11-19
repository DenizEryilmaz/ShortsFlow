"""Standalone FastAPI entrypoint for ShortsFlow."""
import os
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .models import ROOT
from .routes import router as studio_router
from .worker import start as start_worker

load_dotenv(ROOT / '.env')


def create_app(data_root: Path | None = None, *, start_background_worker: bool = True) -> FastAPI:
    resolved_data = Path(data_root or os.getenv('STUDIO_DATA_DIR') or (ROOT / 'data')).resolve()
    api_router, store = studio_router(resolved_data)

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        if start_background_worker:
            start_worker(store.root)
        yield

    app = FastAPI(title='ShortsFlow', version='1.0.0', lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=['http://127.0.0.1:5173', 'http://localhost:5173'],
        allow_methods=['*'],
        allow_headers=['*'],
    )
    app.include_router(api_router)

    @app.get('/api/health')
    async def health():
        return {'status': 'ok', 'data_dir': str(store.root)}

    dist = ROOT / 'frontend' / 'dist'
    if (dist / 'index.html').is_file():
        assets_dir = dist / 'assets'
        if assets_dir.is_dir():
            app.mount('/assets', StaticFiles(directory=assets_dir), name='assets')

        @app.get('/{full_path:path}')
        async def spa(full_path: str):
            candidate = (dist / full_path).resolve()
            if full_path and candidate.is_relative_to(dist.resolve()) and candidate.is_file():
                return FileResponse(candidate)
            return FileResponse(dist / 'index.html')

    return app


app = create_app()


if __name__ == '__main__':
    host = os.getenv('STUDIO_HOST', '127.0.0.1')
    port = int(os.getenv('STUDIO_PORT', '8010'))
    uvicorn.run('studio.app:app', host=host, port=port, reload=False)
