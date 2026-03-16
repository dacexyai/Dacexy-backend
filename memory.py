from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.infrastructure.persistence.database import get_db
from src.infrastructure.persistence.models.orm_models import User, MemoryEntry
from src.interfaces.http.routes.auth import _get_current_user

router = APIRouter(prefix="/memory", tags=["memory"])


class MemoryCreateRequest(BaseModel):
    content: str
    metadata: dict = {}


@router.post("/")
async def add_memory(
    body: MemoryCreateRequest,
    user: User = Depends(_get_current_user),
    db: AsyncSession = Depends(get_db),
):
    entry = MemoryEntry(
        org_id=user.org_id,
        user_id=user.id,
        content=body.content,
        metadata_=body.metadata,
    )
    db.add(entry)
    await db.flush()
    return {"id": entry.id, "content": entry.content, "created_at": str(entry.created_at)}


@router.get("/")
async def list_memories(
    user: User = Depends(_get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(MemoryEntry)
        .where(MemoryEntry.org_id == user.org_id)
        .order_by(MemoryEntry.created_at.desc())
        .limit(100)
    )
    entries = result.scalars().all()
    return {
        "memories": [
            {"id": e.id, "content": e.content[:200],
             "metadata": e.metadata_, "created_at": str(e.created_at)}
            for e in entries
        ],
        "total": len(entries),
    }


@router.delete("/{memory_id}")
async def delete_memory(
    memory_id: str,
    user: User = Depends(_get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(MemoryEntry).where(
            MemoryEntry.id == memory_id,
            MemoryEntry.org_id == user.org_id,
        )
    )
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(404, "Memory not found")
    await db.delete(entry)
    return {"message": "Deleted"}
