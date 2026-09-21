from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from docflow.application.processing import find_business_duplicate, transition_document
from docflow.domain.documents import DocumentStatus, ProcessingRunStatus, RevisionStatus
from docflow.domain.invoice import normalize_fields, validate_invoice
from docflow.infrastructure.db.models import Document, ProcessingRun, ResultRevision, utc_now
from docflow.infrastructure.document_types import DocumentTypeCatalog


async def create_corrected_revision(
    *,
    document: Document,
    source_revision: ResultRevision,
    corrected_fields: dict[str, object],
    session: AsyncSession,
    catalog: DocumentTypeCatalog,
) -> ResultRevision:
    source_run = await session.get(ProcessingRun, source_revision.processing_run_id)
    if source_run is None:
        raise ValueError("Source processing run not found")

    definition = catalog.load(source_revision.schema_code, source_revision.schema_version)
    merged_fields = {**source_revision.fields_json, **corrected_fields}
    normalized = normalize_fields(merged_fields, definition.schema)
    validation = validate_invoice(
        fields=normalized,
        raw_fields=merged_fields,
        schema=definition.schema,
        source_text=source_run.text_content or "",
    )
    duplicate = await find_business_duplicate(
        session=session,
        document_id=document.id,
        schema_code=definition.code,
        fields=normalized,
        dedup_keys=definition.schema.get("dedup_key", []),
    )
    if duplicate is not None:
        validation.append(
            {
                "code": "business_duplicate",
                "passed": False,
                "message": (
                    "Совпали ключевые реквизиты с ревизией "
                    f"{duplicate.id[:8]} документа {duplicate.document_id[:8]}"
                ),
                "field": None,
                "severity": "error",
                "matched_revision_id": duplicate.id,
            }
        )
    is_valid = all(bool(item["passed"]) for item in validation)

    latest_run_number = await session.scalar(
        select(func.max(ProcessingRun.run_number)).where(ProcessingRun.document_id == document.id)
    )
    run = ProcessingRun(
        document_id=document.id,
        run_number=(latest_run_number or 0) + 1,
        processor_version="human-correction-v1",
        status=ProcessingRunStatus.SUCCEEDED.value,
        page_count=source_run.page_count,
        text_content=source_run.text_content,
        text_char_count=source_run.text_char_count,
        text_layer_pages=source_run.text_layer_pages,
        ocr_pages=source_run.ocr_pages,
        ocr_pending_pages=source_run.ocr_pending_pages,
        completed_at=utc_now(),
    )
    session.add(run)
    await session.flush()

    latest_revision_number = await session.scalar(
        select(func.max(ResultRevision.revision_number)).where(
            ResultRevision.document_id == document.id
        )
    )
    revision = ResultRevision(
        document_id=document.id,
        processing_run_id=run.id,
        revision_number=(latest_revision_number or 0) + 1,
        schema_code=definition.code,
        schema_version=definition.version,
        extraction_model="human/operator-v1",
        status=RevisionStatus.NEEDS_REVIEW.value,
        fields_json=normalized,
        validation_json=validation,
        is_valid=is_valid,
    )
    session.add(revision)
    transition_document(
        session=session,
        document=document,
        to_status=DocumentStatus.NEEDS_REVIEW,
        reason=f"Operator created corrected revision {(latest_revision_number or 0) + 1}",
        record_same_status=True,
        actor_type="operator",
    )
    await session.commit()
    await session.refresh(revision)
    return revision


async def approve_revision(
    *,
    document: Document,
    revision: ResultRevision,
    reason: str,
    session: AsyncSession,
) -> ResultRevision:
    revision.status = RevisionStatus.APPROVED.value
    revision.approved_at = utc_now()
    transition_document(
        session=session,
        document=document,
        to_status=DocumentStatus.APPROVED,
        reason=f"Operator approved revision {revision.revision_number}: {reason}",
        actor_type="operator",
    )
    await session.commit()
    await session.refresh(revision)
    return revision
