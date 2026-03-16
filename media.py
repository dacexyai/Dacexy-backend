from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
import httpx

from src.infrastructure.persistence.database import get_db
from src.infrastructure.persistence.models.orm_models import User, GeneratedImage, GeneratedVideo
from src.interfaces.http.routes.auth import _get_current_user
from src.shared.config.settings import settings

router = APIRouter(prefix="/media", tags=["media"])


class ImageRequest(BaseModel):
    prompt: str
    width: int = 512
    height: int = 512


class VideoRequest(BaseModel):
    prompt: str


@router.post("/image")
async def generate_image(
    body: ImageRequest,
    user: User = Depends(_get_current_user),
    db: AsyncSession = Depends(get_db),
):
    record = GeneratedImage(
        org_id=user.org_id, user_id=user.id,
        prompt=body.prompt, status="processing"
    )
    db.add(record)
    await db.flush()

    if not settings.BYTEZ_API_KEY:
        record.status = "failed"
        raise HTTPException(400, "Media API key not configured")

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            r = await client.post(
                "https://api.bytez.com/v2/generate/image",
                headers={"Authorization": f"Key {settings.BYTEZ_API_KEY}"},
                json={"prompt": body.prompt, "width": body.width, "height": body.height},
            )
            r.raise_for_status()
            data = r.json()
            url = data.get("url") or data.get("image_url") or ""
            record.url = url
            record.status = "completed"
            return {"id": record.id, "url": url, "status": "completed"}
    except Exception as e:
        record.status = "failed"
        raise HTTPException(500, f"Image generation failed: {str(e)}")


@router.post("/video")
async def generate_video(
    body: VideoRequest,
    user: User = Depends(_get_current_user),
    db: AsyncSession = Depends(get_db),
):
    record = GeneratedVideo(
        org_id=user.org_id, user_id=user.id,
        prompt=body.prompt, status="processing"
    )
    db.add(record)
    await db.flush()

    if not settings.BYTEZ_API_KEY:
        record.status = "failed"
        raise HTTPException(400, "Media API key not configured")

    try:
        async with httpx.AsyncClient(timeout=120) as client:
            r = await client.post(
                "https://api.bytez.com/v2/generate/video",
                headers={"Authorization": f"Key {settings.BYTEZ_API_KEY}"},
                json={"prompt": body.prompt},
            )
            r.raise_for_status()
            data = r.json()
            url = data.get("url") or data.get("video_url") or ""
            record.url = url
            record.status = "completed"
            return {"id": record.id, "url": url, "status": "completed"}
    except Exception as e:
        record.status = "failed"
        raise HTTPException(500, f"Video generation failed: {str(e)}")
