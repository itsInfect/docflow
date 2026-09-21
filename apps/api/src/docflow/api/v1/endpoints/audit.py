from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from docflow.api.v1.schemas.documents import AuditEventList, AuditEventRead
from docflow.infrastructure.db.models import Document, StatusTransition
from docflow.infrastructure.db.session import get_session

router = APIRouter(prefix="/audit")
SessionDependency = Annotated[AsyncSession, Depends(get_session)]


@router.get("/events", response_model=AuditEventList)
async def list_audit_events(
    session: SessionDependency,
    limit: Annotated[int, Query(ge=1, le=200)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> AuditEventList:
    total = await session.scalar(select(func.count()).select_from(StatusTransition))
    rows = (
        await session.execute(
            select(StatusTransition, Document.original_filename)
            .join(Document, Document.id == StatusTransition.document_id)
            .order_by(StatusTransition.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
    ).all()
    return AuditEventList(
        items=[
            AuditEventRead(
                id=event.id,
                document_id=event.document_id,
                original_filename=filename,
                from_status=event.from_status,
                to_status=event.to_status,
                actor_type=event.actor_type,
                reason=event.reason,
                created_at=event.created_at,
            )
            for event, filename in rows
        ],
        total=total or 0,
    )
