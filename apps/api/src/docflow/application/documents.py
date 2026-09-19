from __future__ import annotations

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from docflow.domain.documents import DocumentStatus
from docflow.infrastructure.db.models import Document, StatusTransition
from docflow.infrastructure.storage.local import LocalDocumentStorage


async def ingest_document(
    *,
    upload: UploadFile,
    session: AsyncSession,
    storage: LocalDocumentStorage,
    max_size_bytes: int,
) -> Document:
    stored = await storage.store_upload(upload, max_size_bytes=max_size_bytes)

    existing = await session.scalar(
        select(Document)
        .where(Document.sha256 == stored.sha256, Document.is_duplicate_of.is_(None))
        .order_by(Document.created_at.asc())
        .limit(1)
    )
    status = DocumentStatus.DUPLICATE_FILE if existing is not None else DocumentStatus.UPLOADED
    original_filename = storage.safe_filename(upload.filename)
    document = Document(
        original_filename=original_filename,
        storage_key=stored.storage_key,
        sha256=stored.sha256,
        mime_type=stored.mime_type,
        size_bytes=stored.size_bytes,
        status=status.value,
        is_duplicate_of=existing.id if existing is not None else None,
    )
    session.add(document)
    await session.flush()

    transition = StatusTransition(
        document_id=document.id,
        from_status=None,
        to_status=status.value,
        actor_type="system",
        reason="Exact file duplicate" if existing is not None else "Document uploaded",
    )
    session.add(transition)
    await session.commit()
    await session.refresh(document)
    return document
