from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.infrastructure.persistence.database import get_db
from src.infrastructure.persistence.models.orm_models import User, GeneratedWebsite
from src.infrastructure.ai_providers.deepseek import DeepSeekProvider
from src.interfaces.http.dependencies.container import get_deepseek
from src.interfaces.http.routes.auth import _get_current_user
from src.application.use_cases.website.website_engine import generate_website

router = APIRouter(prefix="/websites", tags=["websites"])


class WebsiteRequest(BaseModel):
    prompt: str


@router.post("/generate")
async def create_website(
    body: WebsiteRequest,
    user: User = Depends(_get_current_user),
    db: AsyncSession = Depends(get_db),
    ai: DeepSeekProvider = Depends(get_deepseek),
):
    record = GeneratedWebsite(
        org_id=user.org_id,
        user_id=user.id,
        prompt=body.prompt,
        status="generating",
    )
    db.add(record)
    await db.flush()

    try:
        html = await generate_website(body.prompt, ai)
        record.html_content = html
        record.status = "completed"
        return {
            "id": record.id,
            "status": "completed",
            "preview_url": f"/api/v1/websites/{record.id}/preview",
            "html_length": len(html),
        }
    except Exception as e:
        record.status = "failed"
        raise HTTPException(500, f"Website generation failed: {str(e)}")


@router.get("/{website_id}/preview", response_class=HTMLResponse)
async def preview_website(
    website_id: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(GeneratedWebsite).where(GeneratedWebsite.id == website_id)
    )
    site = result.scalar_one_or_none()
    if not site or not site.html_content:
        raise HTTPException(404, "Website not found")
    return HTMLResponse(content=site.html_content)


@router.get("/")
async def list_websites(
    user: User = Depends(_get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(GeneratedWebsite)
        .where(GeneratedWebsite.org_id == user.org_id)
        .order_by(GeneratedWebsite.created_at.desc())
        .limit(20)
    )
    sites = result.scalars().all()
    return {
        "websites": [
            {"id": s.id, "prompt": s.prompt[:80], "status": s.status,
             "created_at": str(s.created_at),
             "preview_url": f"/api/v1/websites/{s.id}/preview" if s.html_content else None}
            for s in sites
        ]
    }
