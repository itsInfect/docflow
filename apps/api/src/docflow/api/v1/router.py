from fastapi import APIRouter

from docflow.api.v1.endpoints import documents, health

api_router = APIRouter()
api_router.include_router(health.router, tags=["system"])
api_router.include_router(documents.router, tags=["documents"])
