from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    original_filename: str
    mime_type: str
    size_bytes: int
    status: str
    doc_type: str | None
    confidence: float | None
    is_duplicate_of: str | None
    created_at: datetime


class DocumentList(BaseModel):
    items: list[DocumentRead]
    total: int
