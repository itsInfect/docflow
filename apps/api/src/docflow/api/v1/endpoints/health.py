from typing import Literal

from fastapi import APIRouter, Request
from pydantic import BaseModel
from sqlalchemy import text

from docflow import __version__
from docflow.core.config import Settings

router = APIRouter()


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"
    service: str = "docflow-api"
    version: str
    environment: str


@router.get("/health", response_model=HealthResponse)
async def health(request: Request) -> HealthResponse:
    settings: Settings = request.app.state.settings
    return HealthResponse(version=__version__, environment=settings.environment)


@router.get("/ready", response_model=HealthResponse)
async def readiness(request: Request) -> HealthResponse:
    settings: Settings = request.app.state.settings
    async with request.app.state.session_factory() as session:
        await session.execute(text("SELECT 1"))
    return HealthResponse(version=__version__, environment=settings.environment)
