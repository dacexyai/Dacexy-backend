from __future__ import annotations
import secrets
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from src.infrastructure.persistence.database import get_db
from src.infrastructure.persistence.models.orm_models import User, Organization, ApiKey
from src.interfaces.http.routes.auth import _get_current_user
from src.shared.security.auth import hash_password

router = APIRouter(prefix="/orgs", tags=["orgs"])


@router.get("/me")
async def get_my_org(
    user: User = Depends(_get_current_user),
    db: AsyncSession = Depends(get_db),
):
    org = await db.get(Organization, user.org_id)
    if not org:
        raise HTTPException(404, "Org not found")
    return {
        "id": org.id, "name": org.name, "slug": org.slug,
        "plan_tier": org.plan_tier, "credits_balance": org.credits_balance,
        "is_active": org.is_active,
    }


@router.get("/members")
async def list_members(
    user: User = Depends(_get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.org_id == user.org_id))
    members = result.scalars().all()
    return {
        "members": [
            {"id": m.id, "email": m.email, "full_name": m.full_name,
             "role": m.role, "is_verified": m.is_verified}
            for m in members
        ],
        "total": len(members),
    }


@router.get("/api-keys")
async def list_api_keys(
    user: User = Depends(_get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ApiKey).where(ApiKey.org_id == user.org_id, ApiKey.is_active == True)
    )
    keys = result.scalars().all()
    return {
        "api_keys": [
            {"id": k.id, "name": k.name, "key_prefix": k.key_prefix,
             "created_at": str(k.created_at), "last_used_at": str(k.last_used_at) if k.last_used_at else None}
            for k in keys
        ]
    }


class CreateApiKeyRequest(BaseModel):
    name: str


@router.post("/api-keys")
async def create_api_key(
    body: CreateApiKeyRequest,
    user: User = Depends(_get_current_user),
    db: AsyncSession = Depends(get_db),
):
    raw_key = f"dacexy_{secrets.token_urlsafe(32)}"
    key = ApiKey(
        org_id=user.org_id,
        name=body.name,
        key_hash=hash_password(raw_key),
        key_prefix=raw_key[:12],
    )
    db.add(key)
    await db.flush()
    return {"id": key.id, "name": key.name, "key": raw_key, "key_prefix": key.key_prefix}
