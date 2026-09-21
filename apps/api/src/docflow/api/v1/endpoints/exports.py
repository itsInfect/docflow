from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Query
from fastapi.responses import Response
from sqlalchemy import select

from docflow.api.v1.endpoints.documents import SessionDependency
from docflow.domain.documents import RevisionStatus
from docflow.infrastructure.db.models import ResultRevision
from docflow.infrastructure.export import render_csv, render_xlsx

router = APIRouter(prefix="/exports")


@router.get("/revisions")
async def export_approved_revisions(
    session: SessionDependency,
    format: Literal["csv", "xlsx"] = Query(default="xlsx"),
) -> Response:
    revisions = (
        await session.scalars(
            select(ResultRevision)
            .where(ResultRevision.status == RevisionStatus.APPROVED.value)
            .order_by(ResultRevision.document_id, ResultRevision.revision_number.desc())
        )
    ).all()
    latest_by_document: dict[str, ResultRevision] = {}
    for revision in revisions:
        latest_by_document.setdefault(revision.document_id, revision)
    rows = [revision_row(revision) for revision in latest_by_document.values()]

    if format == "csv":
        content = render_csv(rows)
        media_type = "text/csv; charset=utf-8"
        filename = "docflow-approved-revisions.csv"
    else:
        content = render_xlsx(rows)
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        filename = "docflow-approved-revisions.xlsx"
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def revision_row(revision: ResultRevision) -> dict[str, object]:
    return {
        "revision_id": revision.id,
        "document_id": revision.document_id,
        "revision_number": revision.revision_number,
        "schema_code": revision.schema_code,
        "approved_at": revision.approved_at.isoformat() if revision.approved_at else "",
        **revision.fields_json,
    }
