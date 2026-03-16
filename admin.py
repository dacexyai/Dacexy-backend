from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from src.infrastructure.persistence.database import get_db
from src.infrastructure.persistence.models.orm_models import User, Organization
from src.interfaces.http.routes.auth import _get_current_user

router = APIRouter(prefix="/admin", tags=["admin"])


def _require_admin(user: User = Depends(_get_current_user)) -> User:
    if user.role not in ("owner", "admin"):
        raise HTTPException(403, "Admin access required")
    return user


@router.get("/stats")
async def platform_stats(
    user: User = Depends(_require_admin),
    db: AsyncSession = Depends(get_db),
):
    org_count = await db.scalar(select(func.count(Organization.id)))
    user_count = await db.scalar(select(func.count(User.id)))
    return {
        "total_organizations": org_count,
        "total_users": user_count,
        "version": "10.0.0",
    }


@router.get("/users")
async def list_users(
    user: User = Depends(_require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(User).order_by(User.created_at.desc()).limit(100)
    )
    users = result.scalars().all()
    return {
        "users": [
            {"id": u.id, "email": u.email, "full_name": u.full_name,
             "role": u.role, "is_verified": u.is_verified,
             "org_id": u.org_id, "created_at": str(u.created_at)}
            for u in users
        ]
    }
