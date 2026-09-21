from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class DocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    original_filename: str
    mime_type: str
    size_bytes: int
    page_count: int | None
    status: str
    doc_type: str | None
    confidence: float | None
    is_duplicate_of: str | None
    created_at: datetime


class DocumentList(BaseModel):
    items: list[DocumentRead]
    total: int


class ProcessingRunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    document_id: str
    run_number: int
    processor_version: str
    status: str
    page_count: int | None
    text_char_count: int
    text_layer_pages: int
    ocr_pages: int
    ocr_pending_pages: int
    error_message: str | None
    created_at: datetime
    completed_at: datetime | None


class ProcessingRunList(BaseModel):
    items: list[ProcessingRunRead]
    total: int


class ResultRevisionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    document_id: str
    processing_run_id: str
    revision_number: int
    schema_code: str
    schema_version: int
    extraction_model: str
    status: str
    fields_json: dict[str, object]
    validation_json: list[dict[str, object]]
    is_valid: bool
    created_at: datetime
    approved_at: datetime | None


class ResultRevisionList(BaseModel):
    items: list[ResultRevisionRead]
    total: int


class RevisionCorrectionRequest(BaseModel):
    fields: dict[str, object]


class RevisionApprovalRequest(BaseModel):
    reason: str = Field(min_length=3, max_length=500)


class DuplicateDecisionRequest(BaseModel):
    decision: Literal["keep", "reject"]


class AuditEventRead(BaseModel):
    id: str
    document_id: str
    original_filename: str
    from_status: str | None
    to_status: str
    actor_type: str
    reason: str | None
    created_at: datetime


class AuditEventList(BaseModel):
    items: list[AuditEventRead]
    total: int
