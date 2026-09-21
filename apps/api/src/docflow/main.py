from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from docflow import __version__
from docflow.api.v1.router import api_router
from docflow.core.config import Settings, get_settings
from docflow.infrastructure.db import models as _models  # noqa: F401
from docflow.infrastructure.db.base import Base


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved_settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        resolved_settings.storage_root.mkdir(parents=True, exist_ok=True)
        engine = create_async_engine(resolved_settings.database_url, pool_pre_ping=True)
        app.state.session_factory = async_sessionmaker(engine, expire_on_commit=False)

        if resolved_settings.auto_create_schema:
            async with engine.begin() as connection:
                await connection.run_sync(Base.metadata.create_all)

        yield
        await engine.dispose()

    app = FastAPI(
        title="Docflow API",
        description="Extraction, validation, and human review of accounting documents.",
        version=__version__,
        lifespan=lifespan,
    )
    app.state.settings = resolved_settings
    app.add_middleware(
        CORSMiddleware,
        allow_origins=resolved_settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(api_router, prefix=resolved_settings.api_prefix)

    web_root = resolved_settings.web_dist_root
    if web_root is not None:
        resolved_web_root = web_root.resolve()
        index_file = resolved_web_root / "index.html"
        assets_root = resolved_web_root / "assets"
        if index_file.is_file():
            if assets_root.is_dir():
                app.mount("/assets", StaticFiles(directory=assets_root), name="web-assets")

            @app.get("/{full_path:path}", include_in_schema=False)
            async def serve_web_app(full_path: str) -> FileResponse:
                if full_path.startswith(resolved_settings.api_prefix.lstrip("/")):
                    raise HTTPException(status_code=404, detail="Not found")
                candidate = (resolved_web_root / full_path).resolve()
                if candidate.is_relative_to(resolved_web_root) and candidate.is_file():
                    return FileResponse(candidate)
                return FileResponse(index_file)

    return app


app = create_app()
