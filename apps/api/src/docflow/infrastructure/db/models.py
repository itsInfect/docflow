from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import (
    JSON,
    BigInteger,
    DateTime,
    Float,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from docflow.domain.documents import DocumentStatus, ProcessingRunStatus
from docflow.infrastructure.db.base import Base


def utc_now() -> datetime:
    return datetime.now(UTC)


def new_id() -> str:
    return str(uuid4())


class Document(Base):
    __tablename__ = "documents"
    __table_args__ = (
        Index("ix_documents_status_created_at", "status", "created_at"),
        Index("ix_documents_sha256", "sha256"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    original_filename: Mapped[str] = mapped_column(String(255))
    storage_key: Mapped[str] = mapped_column(String(512))
    sha256: Mapped[str] = mapped_column(String(64))
    mime_type: Mapped[str] = mapped_column(String(100))
    size_bytes: Mapped[int] = mapped_column(BigInteger)
    page_count: Mapped[int | None] = mapped_column(nullable=True)
    status: Mapped[str] = mapped_column(String(32), default=DocumentStatus.UPLOADED.value)
    doc_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_duplicate_of: Mapped[str | None] = mapped_column(
        ForeignKey("documents.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )

    transitions: Mapped[list[StatusTransition]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )
    processing_runs: Mapped[list[ProcessingRun]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )
    revisions: Mapped[list[ResultRevision]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )


class StatusTransition(Base):
    __tablename__ = "status_transitions"
    __table_args__ = (Index("ix_status_transitions_document_created", "document_id", "created_at"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    document_id: Mapped[str] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), nullable=False
    )
    from_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    to_status: Mapped[str] = mapped_column(String(32))
    actor_type: Mapped[str] = mapped_column(String(32), default="system")
    actor_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    document: Mapped[Document] = relationship(back_populates="transitions")


class ProcessingRun(Base):
    __tablename__ = "processing_runs"
    __table_args__ = (
        UniqueConstraint("document_id", "run_number", name="uq_processing_runs_document_number"),
        Index("ix_processing_runs_document_created", "document_id", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    document_id: Mapped[str] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), nullable=False
    )
    run_number: Mapped[int] = mapped_column(nullable=False)
    processor_version: Mapped[str] = mapped_column(String(64), default="preprocess-v1")
    status: Mapped[str] = mapped_column(String(32), default=ProcessingRunStatus.RUNNING.value)
    page_count: Mapped[int | None] = mapped_column(nullable=True)
    text_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    text_char_count: Mapped[int] = mapped_column(default=0)
    text_layer_pages: Mapped[int] = mapped_column(default=0)
    ocr_pages: Mapped[int] = mapped_column(default=0)
    ocr_pending_pages: Mapped[int] = mapped_column(default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    document: Mapped[Document] = relationship(back_populates="processing_runs")
    revision: Mapped[ResultRevision | None] = relationship(back_populates="processing_run")


class ResultRevision(Base):
    __tablename__ = "result_revisions"
    __table_args__ = (
        UniqueConstraint("document_id", "revision_number", name="uq_revisions_document_number"),
        UniqueConstraint("processing_run_id", name="uq_revisions_processing_run"),
        Index("ix_revisions_document_created", "document_id", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    document_id: Mapped[str] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), nullable=False
    )
    processing_run_id: Mapped[str] = mapped_column(
        ForeignKey("processing_runs.id", ondelete="CASCADE"), nullable=False
    )
    revision_number: Mapped[int] = mapped_column(nullable=False)
    schema_code: Mapped[str] = mapped_column(String(64), nullable=False)
    schema_version: Mapped[int] = mapped_column(nullable=False)
    extraction_model: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    fields_json: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)
    validation_json: Mapped[list[dict[str, object]]] = mapped_column(JSON, nullable=False)
    is_valid: Mapped[bool] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    document: Mapped[Document] = relationship(back_populates="revisions")
    processing_run: Mapped[ProcessingRun] = relationship(back_populates="revision")
