from typing import Literal

from fastapi import APIRouter, Request
from pydantic import BaseModel
from sqlalchemy import text

from docflow import __version__
from docflow.core.config import Settings
from docflow.infrastructure.preprocessing import TesseractOcrEngine

router = APIRouter()


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"
    service: str = "docflow-api"
    version: str
    environment: str


class CapabilitiesResponse(BaseModel):
    environment: str
    llm_provider: str
    llm_model: str | None
    demo_mode: bool
    ocr_available: bool
    ocr_command: str | None
    ocr_languages_requested: str
    ocr_languages_installed: list[str]
    max_upload_size_mb: int
    auto_accept_threshold: float
    storage_backend: str = "local"
    document_types: list[str] = ["invoice", "service_act"]


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


@router.get("/capabilities", response_model=CapabilitiesResponse)
async def capabilities(request: Request) -> CapabilitiesResponse:
    settings: Settings = request.app.state.settings
    ocr = TesseractOcrEngine(
        language=settings.ocr_languages,
        command=settings.tesseract_cmd,
    )
    return CapabilitiesResponse(
        environment=settings.environment,
        llm_provider=settings.llm_provider,
        llm_model=settings.anthropic_model,
        demo_mode=settings.llm_provider == "mock",
        ocr_available=ocr.is_available(),
        ocr_command=str(ocr.command) if ocr.command is not None else None,
        ocr_languages_requested=settings.ocr_languages,
        ocr_languages_installed=ocr.installed_languages(),
        max_upload_size_mb=settings.max_upload_size_mb,
        auto_accept_threshold=settings.auto_accept_threshold,
    )
