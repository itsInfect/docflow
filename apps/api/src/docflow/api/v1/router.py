from fastapi import APIRouter

from docflow.api.v1.endpoints import audit, documents, exports, health, quality

api_router = APIRouter()
api_router.include_router(health.router, tags=["system"])
api_router.include_router(documents.router, tags=["documents"])
api_router.include_router(quality.router, tags=["quality"])
api_router.include_router(exports.router, tags=["exports"])
api_router.include_router(audit.router, tags=["audit"])
