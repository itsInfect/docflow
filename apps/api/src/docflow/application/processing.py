from __future__ import annotations

import asyncio

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from docflow.ai.base import LLMProvider
from docflow.domain.documents import (
    DocumentStatus,
    ProcessingRunStatus,
    RevisionStatus,
)
from docflow.domain.invoice import normalize_fields, validate_invoice
from docflow.infrastructure.db.models import (
    Document,
    ProcessingRun,
    ResultRevision,
    StatusTransition,
    utc_now,
)
from docflow.infrastructure.document_types import DocumentTypeCatalog
from docflow.infrastructure.preprocessing import DocumentPreprocessor
from docflow.infrastructure.storage.local import LocalDocumentStorage


async def process_document(
    *,
    document: Document,
    session: AsyncSession,
    storage: LocalDocumentStorage,
    preprocessor: DocumentPreprocessor,
    provider: LLMProvider,
    catalog: DocumentTypeCatalog,
    auto_accept_threshold: float,
) -> ProcessingRun:
    latest_number = await session.scalar(
        select(func.max(ProcessingRun.run_number)).where(ProcessingRun.document_id == document.id)
    )
    run = ProcessingRun(document_id=document.id, run_number=(latest_number or 0) + 1)
    session.add(run)
    transition_document(
        session=session,
        document=document,
        to_status=DocumentStatus.PREPROCESSING,
        reason=f"Processing run {run.run_number} started",
    )
    await session.commit()

    try:
        source = storage.path_for(document.storage_key)
        output_dir = storage.derived_run_path(document.sha256, run.run_number)
        result = await asyncio.to_thread(
            preprocessor.process,
            source=source,
            mime_type=document.mime_type,
            output_dir=output_dir,
        )
        run.page_count = result.page_count
        run.text_content = result.text
        run.text_char_count = len(result.text)
        run.text_layer_pages = result.text_layer_pages
        run.ocr_pages = result.ocr_pages
        run.ocr_pending_pages = result.ocr_pending_pages
        document.page_count = result.page_count

        if result.ocr_pending_pages:
            run.status = ProcessingRunStatus.AWAITING_OCR.value
            run.completed_at = utc_now()
            transition_document(
                session=session,
                document=document,
                to_status=DocumentStatus.PREPROCESSING,
                reason=f"{result.ocr_pending_pages} page(s) are waiting for OCR",
                record_same_status=True,
            )
        else:
            await extract_and_validate(
                document=document,
                run=run,
                session=session,
                provider=provider,
                catalog=catalog,
                auto_accept_threshold=auto_accept_threshold,
            )
    except Exception as exc:  # processing failures must become auditable run results
        run.status = ProcessingRunStatus.FAILED.value
        run.error_message = str(exc)[:2000]
        run.completed_at = utc_now()
        transition_document(
            session=session,
            document=document,
            to_status=DocumentStatus.FAILED,
            reason=f"Preprocessing failed: {run.error_message}",
        )

    await session.commit()
    await session.refresh(run)
    return run


async def extract_and_validate(
    *,
    document: Document,
    run: ProcessingRun,
    session: AsyncSession,
    provider: LLMProvider,
    catalog: DocumentTypeCatalog,
    auto_accept_threshold: float,
) -> None:
    source_text = run.text_content or ""
    transition_document(
        session=session,
        document=document,
        to_status=DocumentStatus.CLASSIFYING,
        reason="Preprocessing completed",
    )
    classification = await provider.classify(text=source_text)
    if classification.document_type is None:
        run.status = ProcessingRunStatus.SUCCEEDED.value
        run.completed_at = utc_now()
        transition_document(
            session=session,
            document=document,
            to_status=DocumentStatus.NEEDS_REVIEW,
            reason="Document type could not be determined",
        )
        return

    document.doc_type = classification.document_type
    document.confidence = classification.confidence
    definition = catalog.load(classification.document_type)
    transition_document(
        session=session,
        document=document,
        to_status=DocumentStatus.EXTRACTING,
        reason=f"Document classified as {classification.document_type}",
    )
    extraction = await provider.extract(
        text=source_text,
        schema=definition.schema,
        prompt=catalog.render_prompt(definition, document_text=source_text),
    )

    transition_document(
        session=session,
        document=document,
        to_status=DocumentStatus.VALIDATING,
        reason="Fields extracted",
    )
    normalized = normalize_fields(extraction.fields, definition.schema)
    validation = validate_invoice(
        fields=normalized,
        raw_fields=extraction.fields,
        schema=definition.schema,
        source_text=source_text,
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
    is_approved = is_valid and classification.confidence >= auto_accept_threshold
    revision_number = await session.scalar(
        select(func.max(ResultRevision.revision_number)).where(
            ResultRevision.document_id == document.id
        )
    )
    revision = ResultRevision(
        document_id=document.id,
        processing_run_id=run.id,
        revision_number=(revision_number or 0) + 1,
        schema_code=definition.code,
        schema_version=definition.version,
        extraction_model=extraction.model,
        status=(RevisionStatus.APPROVED if is_approved else RevisionStatus.NEEDS_REVIEW).value,
        fields_json=normalized,
        validation_json=validation,
        is_valid=is_valid,
        approved_at=utc_now() if is_approved else None,
    )
    session.add(revision)

    run.status = ProcessingRunStatus.SUCCEEDED.value
    run.completed_at = utc_now()
    transition_document(
        session=session,
        document=document,
        to_status=DocumentStatus.APPROVED if is_approved else DocumentStatus.NEEDS_REVIEW,
        reason=(
            "Revision passed deterministic validation and acceptance threshold"
            if is_approved
            else "Revision requires operator review"
        ),
    )


async def find_business_duplicate(
    *,
    session: AsyncSession,
    document_id: str,
    schema_code: str,
    fields: dict[str, object],
    dedup_keys: object,
) -> ResultRevision | None:
    if not isinstance(dedup_keys, list) or not dedup_keys:
        return None
    keys = [key for key in dedup_keys if isinstance(key, str)]
    if not keys or any(fields.get(key) in {None, ""} for key in keys):
        return None
    candidates = (
        await session.scalars(
            select(ResultRevision)
            .where(
                ResultRevision.document_id != document_id,
                ResultRevision.schema_code == schema_code,
            )
            .order_by(ResultRevision.created_at.desc())
        )
    ).all()
    for candidate in candidates:
        if all(candidate.fields_json.get(key) == fields.get(key) for key in keys):
            return candidate
    return None


def transition_document(
    *,
    session: AsyncSession,
    document: Document,
    to_status: DocumentStatus,
    reason: str,
    record_same_status: bool = False,
    actor_type: str = "system",
) -> None:
    previous_status = document.status
    if previous_status == to_status.value and not record_same_status:
        return
    document.status = to_status.value
    session.add(
        StatusTransition(
            document_id=document.id,
            from_status=previous_status,
            to_status=to_status.value,
            actor_type=actor_type,
            reason=reason,
        )
    )
