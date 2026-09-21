from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from docflow.ai.factory import build_llm_provider
from docflow.api.v1.schemas.documents import (
    DocumentList,
    DocumentRead,
    DuplicateDecisionRequest,
    ProcessingRunList,
    ProcessingRunRead,
    ResultRevisionList,
    ResultRevisionRead,
    RevisionApprovalRequest,
    RevisionCorrectionRequest,
)
from docflow.application.documents import ingest_document
from docflow.application.processing import process_document, transition_document
from docflow.application.review import approve_revision, create_corrected_revision
from docflow.core.config import Settings
from docflow.domain.documents import TERMINAL_STATUSES, DocumentStatus
from docflow.infrastructure.db.models import Document, ProcessingRun, ResultRevision
from docflow.infrastructure.db.session import get_session
from docflow.infrastructure.document_types import DocumentTypeCatalog
from docflow.infrastructure.preprocessing import DocumentPreprocessor, TesseractOcrEngine
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


@router.post("/{document_id}/duplicate-decision", response_model=DocumentRead)
async def resolve_exact_duplicate(
    document_id: str,
    payload: DuplicateDecisionRequest,
    session: SessionDependency,
) -> Document:
    document = await session.get(Document, document_id)
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    if document.status != DocumentStatus.DUPLICATE_FILE.value:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Document is not waiting for an exact duplicate decision",
        )
    transition_document(
        session=session,
        document=document,
        to_status=(
            DocumentStatus.UPLOADED if payload.decision == "keep" else DocumentStatus.REJECTED
        ),
        reason=(
            "Operator kept exact duplicate as a separate document"
            if payload.decision == "keep"
            else "Operator rejected exact duplicate"
        ),
        actor_type="operator",
    )
    await session.commit()
    await session.refresh(document)
    return document


@router.post("/{document_id}/process", response_model=ProcessingRunRead)
async def start_processing(
    document_id: str,
    request: Request,
    session: SessionDependency,
) -> ProcessingRun:
    document = await session.get(Document, document_id)
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    if document.status in {item.value for item in TERMINAL_STATUSES}:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Document status does not allow processing",
        )

    settings: Settings = request.app.state.settings
    return await process_document(
        document=document,
        session=session,
        storage=LocalDocumentStorage(settings.storage_root),
        preprocessor=DocumentPreprocessor(
            TesseractOcrEngine(
                language=settings.ocr_languages,
                command=settings.tesseract_cmd,
            )
        ),
        provider=build_llm_provider(settings),
        catalog=DocumentTypeCatalog(
            schemas_root=settings.schemas_root,
            prompts_root=settings.prompts_root,
        ),
        auto_accept_threshold=settings.auto_accept_threshold,
    )


@router.get("/{document_id}/runs", response_model=ProcessingRunList)
async def list_processing_runs(
    document_id: str,
    session: SessionDependency,
) -> ProcessingRunList:
    if await session.get(Document, document_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    runs = (
        await session.scalars(
            select(ProcessingRun)
            .where(ProcessingRun.document_id == document_id)
            .order_by(ProcessingRun.run_number.desc())
        )
    ).all()
    return ProcessingRunList(
        items=[ProcessingRunRead.model_validate(run) for run in runs],
        total=len(runs),
    )


@router.get("/{document_id}/revisions", response_model=ResultRevisionList)
async def list_result_revisions(
    document_id: str,
    session: SessionDependency,
) -> ResultRevisionList:
    if await session.get(Document, document_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    revisions = (
        await session.scalars(
            select(ResultRevision)
            .where(ResultRevision.document_id == document_id)
            .order_by(ResultRevision.revision_number.desc())
        )
    ).all()
    return ResultRevisionList(
        items=[ResultRevisionRead.model_validate(revision) for revision in revisions],
        total=len(revisions),
    )


@router.post(
    "/{document_id}/revisions/{revision_id}/corrections",
    response_model=ResultRevisionRead,
    status_code=status.HTTP_201_CREATED,
)
async def correct_result_revision(
    document_id: str,
    revision_id: str,
    payload: RevisionCorrectionRequest,
    request: Request,
    session: SessionDependency,
) -> ResultRevision:
    document = await session.get(Document, document_id)
    revision = await session.get(ResultRevision, revision_id)
    if document is None or revision is None or revision.document_id != document_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Revision not found")
    settings: Settings = request.app.state.settings
    return await create_corrected_revision(
        document=document,
        source_revision=revision,
        corrected_fields=payload.fields,
        session=session,
        catalog=DocumentTypeCatalog(
            schemas_root=settings.schemas_root,
            prompts_root=settings.prompts_root,
        ),
    )


@router.post(
    "/{document_id}/revisions/{revision_id}/approve",
    response_model=ResultRevisionRead,
)
async def approve_result_revision(
    document_id: str,
    revision_id: str,
    payload: RevisionApprovalRequest,
    session: SessionDependency,
) -> ResultRevision:
    document = await session.get(Document, document_id)
    revision = await session.get(ResultRevision, revision_id)
    if document is None or revision is None or revision.document_id != document_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Revision not found")
    return await approve_revision(
        document=document,
        revision=revision,
        reason=payload.reason,
        session=session,
    )
