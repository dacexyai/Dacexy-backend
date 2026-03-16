from __future__ import annotations
import secrets
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.persistence.database import get_db
from src.infrastructure.persistence.models.orm_models import User
from src.interfaces.http.routes.auth import _get_current_user
from src.shared.config.settings import settings

router = APIRouter(prefix="/referral", tags=["referral"])


@router.get("/link")
async def get_referral_link(user: User = Depends(_get_current_user)):
    code = secrets.token_urlsafe(8)
    link = f"{settings.APP_BASE_URL}/register?ref={code}"
    return {"referral_link": link, "code": code}


@router.get("/stats")
async def get_referral_stats(user: User = Depends(_get_current_user)):
    return {
        "total_referrals": 0,
        "credits_earned": 0,
        "message": "Referral tracking coming soon"
    }
