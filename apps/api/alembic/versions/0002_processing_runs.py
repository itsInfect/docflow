"""Add versioned document processing runs.

Revision ID: 0002_processing_runs
Revises: 0001_document_intake
Create Date: 2026-09-20
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0002_processing_runs"
down_revision: str | None = "0001_document_intake"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "processing_runs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("document_id", sa.String(length=36), nullable=False),
        sa.Column("run_number", sa.Integer(), nullable=False),
        sa.Column("processor_version", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("page_count", sa.Integer(), nullable=True),
        sa.Column("text_content", sa.Text(), nullable=True),
        sa.Column("text_char_count", sa.Integer(), nullable=False),
        sa.Column("text_layer_pages", sa.Integer(), nullable=False),
        sa.Column("ocr_pages", sa.Integer(), nullable=False),
        sa.Column("ocr_pending_pages", sa.Integer(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("document_id", "run_number", name="uq_processing_runs_document_number"),
    )
    op.create_index(
        "ix_processing_runs_document_created",
        "processing_runs",
        ["document_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_processing_runs_document_created", table_name="processing_runs")
    op.drop_table("processing_runs")
