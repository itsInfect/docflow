from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from docflow.api.v1.schemas.documents import DocumentList, DocumentRead
from docflow.application.documents import ingest_document
from docflow.core.config import Settings
from docflow.infrastructure.db.models import Document
from docflow.infrastructure.db.session import get_session
from docflow.infrastructure.storage.local import (
    InvalidUploadError,
    LocalDocumentStorage,
    UnsupportedDocumentTypeError,
    UploadTooLargeError,
)

router = APIRouter(prefix="/documents")
SessionDependency = Annotated[AsyncSession, Depends(get_session)]


@router.post("", response_model=DocumentRead, status_code=status.HTTP_201_CREATED)
async def upload_document(
    request: Request,
    session: SessionDependency,
    file: Annotated[UploadFile, File(description="PDF, JPEG, PNG, or TIFF document")],
) -> Document:
    settings: Settings = request.app.state.settings
    storage = LocalDocumentStorage(settings.storage_root)

    try:
        return await ingest_document(
            upload=file,
            session=session,
            storage=storage,
            max_size_bytes=settings.max_upload_size_mb * 1024 * 1024,
        )
    except UploadTooLargeError as exc:
        raise HTTPException(status_code=status.HTTP_413_CONTENT_TOO_LARGE, detail=str(exc)) from exc
    except UnsupportedDocumentTypeError as exc:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail=str(exc)
        ) from exc
    except InvalidUploadError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("", response_model=DocumentList)
async def list_documents(
    session: SessionDependency,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> DocumentList:
    total = await session.scalar(select(func.count()).select_from(Document))
    documents = (
        await session.scalars(
            select(Document).order_by(Document.created_at.desc()).offset(offset).limit(limit)
        )
    ).all()
    return DocumentList(
        items=[DocumentRead.model_validate(document) for document in documents],
        total=total or 0,
    )


@router.get("/{document_id}", response_model=DocumentRead)
async def get_document(document_id: str, session: SessionDependency) -> Document:
    document = await session.get(Document, document_id)
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return document
