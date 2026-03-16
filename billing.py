from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.infrastructure.persistence.database import get_db
from src.infrastructure.persistence.models.orm_models import User, Organization, Invoice
from src.interfaces.http.routes.auth import _get_current_user
from src.shared.config.settings import settings

router = APIRouter(prefix="/billing", tags=["billing"])

PLANS = [
    {"id": "free", "name": "Free", "price_inr": 0, "ai_calls": 100, "features": ["100 AI calls/mo", "1 user", "Basic chat"]},
    {"id": "starter", "name": "Starter", "price_inr": 999, "ai_calls": 1000, "features": ["1,000 AI calls/mo", "3 users", "Image generation", "Priority support"]},
    {"id": "growth", "name": "Growth", "price_inr": 2999, "ai_calls": 10000, "features": ["10,000 AI calls/mo", "10 users", "Video generation", "Website builder", "Agent automation"]},
    {"id": "enterprise", "name": "Enterprise", "price_inr": 9999, "ai_calls": -1, "features": ["Unlimited AI calls", "Unlimited users", "All features", "Dedicated support", "Custom integrations"]},
]


@router.get("/plans")
async def get_plans():
    return {"plans": PLANS}


class OrderRequest(BaseModel):
    plan_tier: str


@router.post("/order")
async def create_order(
    body: OrderRequest,
    user: User = Depends(_get_current_user),
    db: AsyncSession = Depends(get_db),
):
    plan = next((p for p in PLANS if p["id"] == body.plan_tier), None)
    if not plan:
        raise HTTPException(400, "Invalid plan")
    if not settings.payments_enabled:
        return {"message": "Payment processing coming soon. Contact support to upgrade.", "plan": plan}
    try:
        import razorpay
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        order = client.order.create({
            "amount": plan["price_inr"] * 100,
            "currency": "INR",
            "notes": {"org_id": str(user.org_id), "plan_tier": body.plan_tier}
        })
        invoice = Invoice(
            org_id=user.org_id,
            amount_paise=plan["price_inr"] * 100,
            razorpay_order_id=order["id"],
            description=f"Upgrade to {plan['name']}",
        )
        db.add(invoice)
        return {"order_id": order["id"], "amount": plan["price_inr"] * 100, "currency": "INR", "key": settings.RAZORPAY_KEY_ID}
    except Exception as e:
        raise HTTPException(500, f"Payment error: {str(e)}")


@router.get("/usage")
async def get_usage(
    user: User = Depends(_get_current_user),
    db: AsyncSession = Depends(get_db),
):
    org = await db.get(Organization, user.org_id)
    return {
        "plan_tier": org.plan_tier if org else "free",
        "credits_balance": org.credits_balance if org else 0,
        "monthly_ai_calls": org.monthly_ai_calls if org else 0,
    }
