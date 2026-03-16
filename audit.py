from __future__ import annotations
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.infrastructure.persistence.database import get_db
from src.infrastructure.persistence.models.orm_models import User, AuditEvent
from src.interfaces.http.routes.auth import _get_current_user

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("/logs")
async def list_audit_logs(
    limit: int = Query(50, le=200),
    user: User = Depends(_get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(AuditEvent)
        .where(AuditEvent.org_id == user.org_id)
        .order_by(AuditEvent.created_at.desc())
        .limit(limit)
    )
    events = result.scalars().all()
    return {
        "events": [
            {
                "id": e.id, "action": e.action,
                "resource_type": e.resource_type,
                "resource_id": e.resource_id,
                "user_id": e.user_id,
                "ip_address": e.ip_address,
                "created_at": str(e.created_at),
            }
            for e in events
        ],
        "total": len(events),
    }
