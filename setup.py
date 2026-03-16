import os, sys

def w(path, content):
    os.makedirs(os.path.dirname(path) if "/" in path else ".", exist_ok=True)
    open(path, "w").write(content)
    print(f"✓ {path}")

# Routes
w("src/interfaces/http/routes/__init__.py", "")

w("src/interfaces/http/routes/auth.py", '''
from __future__ import annotations
import secrets, re
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.infrastructure.persistence.database import get_db
from src.infrastructure.persistence.models.orm_models import User, Organization, RefreshToken
from src.infrastructure.email.email_service import EmailService
from src.interfaces.http.dependencies.container import get_email
from src.shared.security.auth import hash_password, verify_password, create_access_token, create_refresh_token, decode_access_token

router = APIRouter(prefix="/auth", tags=["auth"])
bearer = HTTPBearer(auto_error=False)

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    org_name: str = ""

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

def _make_slug(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return f"{slug}-{secrets.token_hex(4)}"

async def _get_current_user(creds: HTTPAuthorizationCredentials = Depends(bearer), db: AsyncSession = Depends(get_db)) -> User:
    if not creds:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = decode_access_token(creds.credentials)
        user_id = payload["sub"]
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found")
    return user

@router.post("/register", response_model=TokenResponse)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db), email_svc: EmailService = Depends(get_email)):
    existing = await db.execute(select(User).where(User.email == body.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Email already registered")
    org_name = body.org_name or f"{body.full_name.split()[0]}\'s Workspace"
    org = Organization(name=org_name, slug=_make_slug(org_name))
    db.add(org)
    await db.flush()
    verify_token = secrets.token_urlsafe(32)
    user = User(org_id=org.id, email=body.email, full_name=body.full_name, hashed_password=hash_password(body.password), role="owner", metadata_={"verify_token": verify_token})
    db.add(user)
    await db.flush()
    try:
        email_svc.send_verification_email(body.email, verify_token)
    except Exception:
        pass
    access = create_access_token(user.id, {"org_id": org.id, "role": user.role})
    refresh = create_refresh_token()
    db.add(RefreshToken(user_id=user.id, token_hash=hash_password(refresh), expires_at=datetime.utcnow() + timedelta(days=30)))
    return TokenResponse(access_token=access, refresh_token=refresh)

@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account disabled")
    access = create_access_token(user.id, {"org_id": user.org_id, "role": user.role})
    refresh = create_refresh_token()
    db.add(RefreshToken(user_id=user.id, token_hash=hash_password(refresh), expires_at=datetime.utcnow() + timedelta(days=30)))
    return TokenResponse(access_token=access, refresh_token=refresh)

@router.get("/me")
async def me(user: User = Depends(_get_current_user), db: AsyncSession = Depends(get_db)):
    org = await db.get(Organization, user.org_id)
    return {"id": user.id, "email": user.email, "full_name": user.full_name, "role": user.role, "is_verified": user.is_verified, "org": {"id": org.id if org else None, "name": org.name if org else None, "plan_tier": org.plan_tier if org else "free"}}

@router.post("/verify-email")
async def verify_email(token: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User))
    users = result.scalars().all()
    user = next((u for u in users if u.metadata_ and u.metadata_.get("verify_token") == token), None)
    if not user:
        raise HTTPException(status_code=400, detail="Invalid token")
    user.is_verified = True
    user.metadata_ = {k: v for k, v in user.metadata_.items() if k != "verify_token"}
    return {"message": "Email verified"}

@router.post("/logout")
async def logout(user: User = Depends(_get_current_user)):
    return {"message": "Logged out"}
''')

w("src/interfaces/http/routes/ai_chat.py", '''
from __future__ import annotations
import json
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from src.infrastructure.persistence.database import get_db
from src.infrastructure.persistence.models.orm_models import User, ConversationSession
from src.infrastructure.ai_providers.deepseek import DeepSeekProvider
from src.interfaces.http.dependencies.container import get_deepseek
from src.interfaces.http.routes.auth import _get_current_user

router = APIRouter(prefix="/ai", tags=["ai"])

class MessageItem(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: list[MessageItem]
    session_id: Optional[str] = None
    stream: bool = True
    model: str = "deepseek-chat"

@router.post("/chat")
async def chat(body: ChatRequest, user: User = Depends(_get_current_user), db: AsyncSession = Depends(get_db), ai: DeepSeekProvider = Depends(get_deepseek)):
    messages = [{"role": m.role, "content": m.content} for m in body.messages]
    session = None
    if body.session_id:
        result = await db.execute(select(ConversationSession).where(ConversationSession.id == body.session_id, ConversationSession.org_id == user.org_id))
        session = result.scalar_one_or_none()
    if not session:
        title = body.messages[0].content[:60] if body.messages else "New Chat"
        session = ConversationSession(org_id=user.org_id, user_id=user.id, title=title, messages=messages)
        db.add(session)
        await db.flush()
    if body.stream:
        async def event_stream():
            full = ""
            yield f"data: {json.dumps({"type":"session_id","session_id":session.id})}\n\n"
            async for chunk in await ai.chat(messages, model=body.model, stream=True):
                full += chunk
                yield f"data: {json.dumps({"type":"chunk","content":chunk})}\n\n"
            yield f"data: {json.dumps({"type":"done"})}\n\n"
            session.messages = messages + [{"role": "assistant", "content": full}]
        return StreamingResponse(event_stream(), media_type="text/event-stream")
    response = await ai.chat(messages, model=body.model, stream=False)
    session.messages = messages + [{"role": "assistant", "content": response}]
    return {"content": response, "session_id": session.id}

@router.get("/sessions")
async def list_sessions(user: User = Depends(_get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ConversationSession).where(ConversationSession.org_id == user.org_id).order_by(ConversationSession.updated_at.desc()).limit(50))
    sessions = result.scalars().all()
    return {"sessions": [{"id": s.id, "title": s.title, "created_at": str(s.created_at)} for s in sessions], "total": len(sessions)}

@router.get("/sessions/{session_id}/messages")
async def get_messages(session_id: str, user: User = Depends(_get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ConversationSession).where(ConversationSession.id == session_id, ConversationSession.org_id == user.org_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(404, "Session not found")
    return {"messages": session.messages, "session_id": session.id, "title": session.title}
''')

w("src/interfaces/http/routes/orgs.py", '''
from __future__ import annotations
import secrets
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.infrastructure.persistence.database import get_db
from src.infrastructure.persistence.models.orm_models import User, Organization, ApiKey
from src.interfaces.http.routes.auth import _get_current_user
from src.shared.security.auth import hash_password

router = APIRouter(prefix="/orgs", tags=["orgs"])

@router.get("/me")
async def get_my_org(user: User = Depends(_get_current_user), db: AsyncSession = Depends(get_db)):
    org = await db.get(Organization, user.org_id)
    if not org: raise HTTPException(404, "Org not found")
    return {"id": org.id, "name": org.name, "slug": org.slug, "plan_tier": org.plan_tier, "credits_balance": org.credits_balance, "is_active": org.is_active}

@router.get("/members")
async def list_members(user: User = Depends(_get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.org_id == user.org_id))
    members = result.scalars().all()
    return {"members": [{"id": m.id, "email": m.email, "full_name": m.full_name, "role": m.role, "is_verified": m.is_verified} for m in members], "total": len(members)}

@router.get("/api-keys")
async def list_api_keys(user: User = Depends(_get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ApiKey).where(ApiKey.org_id == user.org_id, ApiKey.is_active == True))
    keys = result.scalars().all()
    return {"api_keys": [{"id": k.id, "name": k.name, "key_prefix": k.key_prefix, "created_at": str(k.created_at)} for k in keys]}

class CreateApiKeyRequest(BaseModel):
    name: str

@router.post("/api-keys")
async def create_api_key(body: CreateApiKeyRequest, user: User = Depends(_get_current_user), db: AsyncSession = Depends(get_db)):
    raw_key = f"dacexy_{secrets.token_urlsafe(32)}"
    key = ApiKey(org_id=user.org_id, name=body.name, key_hash=hash_password(raw_key), key_prefix=raw_key[:12])
    db.add(key)
    await db.flush()
    return {"id": key.id, "name": key.name, "key": raw_key, "key_prefix": key.key_prefix}
''')

w("src/interfaces/http/routes/billing.py", '''
from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from src.infrastructure.persistence.database import get_db
from src.infrastructure.persistence.models.orm_models import User, Organization, Invoice
from src.interfaces.http.routes.auth import _get_current_user
from src.shared.config.settings import settings

router = APIRouter(prefix="/billing", tags=["billing"])

PLANS = [
    {"id": "free", "name": "Free", "price_inr": 0, "ai_calls": 100, "features": ["100 AI calls/mo", "1 user", "Basic chat"]},
    {"id": "starter", "name": "Starter", "price_inr": 999, "ai_calls": 1000, "features": ["1,000 AI calls/mo", "3 users", "Image generation"]},
    {"id": "growth", "name": "Growth", "price_inr": 2999, "ai_calls": 10000, "features": ["10,000 AI calls/mo", "10 users", "All features"]},
    {"id": "enterprise", "name": "Enterprise", "price_inr": 9999, "ai_calls": -1, "features": ["Unlimited AI calls", "Unlimited users", "Custom integrations"]},
]

@router.get("/plans")
async def get_plans():
    return {"plans": PLANS}

class OrderRequest(BaseModel):
    plan_tier: str

@router.post("/order")
async def create_order(body: OrderRequest, user: User = Depends(_get_current_user), db: AsyncSession = Depends(get_db)):
    plan = next((p for p in PLANS if p["id"] == body.plan_tier), None)
    if not plan: raise HTTPException(400, "Invalid plan")
    if not settings.payments_enabled:
        return {"message": "Payment processing coming soon.", "plan": plan}
    try:
        import razorpay
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        order = client.order.create({"amount": plan["price_inr"] * 100, "currency": "INR"})
        db.add(Invoice(org_id=user.org_id, amount_paise=plan["price_inr"] * 100, razorpay_order_id=order["id"], description=f"Upgrade to {plan[\'name\']}"))
        return {"order_id": order["id"], "amount": plan["price_inr"] * 100, "currency": "INR", "key": settings.RAZORPAY_KEY_ID}
    except Exception as e:
        raise HTTPException(500, f"Payment error: {str(e)}")

@router.get("/usage")
async def get_usage(user: User = Depends(_get_current_user), db: AsyncSession = Depends(get_db)):
    org = await db.get(Organization, user.org_id)
    return {"plan_tier": org.plan_tier if org else "free", "credits_balance": org.credits_balance if org else 0, "monthly_ai_calls": org.monthly_ai_calls if org else 0}
''')

w("src/interfaces/http/routes/agent.py", '''
from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from src.infrastructure.persistence.database import get_db
from src.infrastructure.persistence.models.orm_models import User, AiTask
from src.infrastructure.ai_providers.deepseek import DeepSeekProvider
from src.interfaces.http.dependencies.container import get_deepseek
from src.interfaces.http.routes.auth import _get_current_user

router = APIRouter(prefix="/agent", tags=["agent"])

class AgentRunRequest(BaseModel):
    task: str
    context: Optional[str] = None

@router.post("/run")
async def run_agent(body: AgentRunRequest, user: User = Depends(_get_current_user), db: AsyncSession = Depends(get_db), ai: DeepSeekProvider = Depends(get_deepseek)):
    messages = [{"role": "system", "content": "You are an autonomous AI agent. Break down tasks and execute them step by step."}, {"role": "user", "content": f"Task: {body.task}" + (f"\nContext: {body.context}" if body.context else "")}]
    task_record = AiTask(org_id=user.org_id, user_id=user.id, task_type="agent_run", status="running", input_data={"task": body.task})
    db.add(task_record)
    await db.flush()
    try:
        result = await ai.chat(messages, stream=False)
        task_record.status = "completed"
        task_record.output_data = {"result": result}
        return {"task_id": task_record.id, "status": "completed", "result": result}
    except Exception as e:
        task_record.status = "failed"
        task_record.error = str(e)
        raise HTTPException(500, f"Agent error: {str(e)}")

@router.get("/tasks")
async def list_tasks(user: User = Depends(_get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AiTask).where(AiTask.org_id == user.org_id).order_by(AiTask.created_at.desc()).limit(20))
    tasks = result.scalars().all()
    return {"tasks": [{"id": t.id, "task_type": t.task_type, "status": t.status, "created_at": str(t.created_at)} for t in tasks]}
''')

w("src/interfaces/http/routes/media.py", '''
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
async def generate_image(body: ImageRequest, user: User = Depends(_get_current_user), db: AsyncSession = Depends(get_db)):
    record = GeneratedImage(org_id=user.org_id, user_id=user.id, prompt=body.prompt, status="processing")
    db.add(record)
    await db.flush()
    if not settings.BYTEZ_API_KEY:
        record.status = "failed"
        raise HTTPException(400, "Media API key not configured")
    try:
        async with httpx.AsyncClient(timeout=60) as c:
            r = await c.post("https://api.bytez.com/v2/generate/image", headers={"Authorization": f"Key {settings.BYTEZ_API_KEY}"}, json={"prompt": body.prompt, "width": body.width, "height": body.height})
            r.raise_for_status()
            url = r.json().get("url") or r.json().get("image_url") or ""
            record.url = url
            record.status = "completed"
            return {"id": record.id, "url": url, "status": "completed"}
    except Exception as e:
        record.status = "failed"
        raise HTTPException(500, f"Image generation failed: {str(e)}")

@router.post("/video")
async def generate_video(body: VideoRequest, user: User = Depends(_get_current_user), db: AsyncSession = Depends(get_db)):
    record = GeneratedVideo(org_id=user.org_id, user_id=user.id, prompt=body.prompt, status="processing")
    db.add(record)
    await db.flush()
    if not settings.BYTEZ_API_KEY:
        record.status = "failed"
        raise HTTPException(400, "Media API key not configured")
    try:
        async with httpx.AsyncClient(timeout=120) as c:
            r = await c.post("https://api.bytez.com/v2/generate/video", headers={"Authorization": f"Key {settings.BYTEZ_API_KEY}"}, json={"prompt": body.prompt})
            r.raise_for_status()
            url = r.json().get("url") or r.json().get("video_url") or ""
            record.url = url
            record.status = "completed"
            return {"id": record.id, "url": url, "status": "completed"}
    except Exception as e:
        record.status = "failed"
        raise HTTPException(500, f"Video generation failed: {str(e)}")
''')

w("src/interfaces/http/routes/websites.py", '''
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
async def create_website(body: WebsiteRequest, user: User = Depends(_get_current_user), db: AsyncSession = Depends(get_db), ai: DeepSeekProvider = Depends(get_deepseek)):
    record = GeneratedWebsite(org_id=user.org_id, user_id=user.id, prompt=body.prompt, status="generating")
    db.add(record)
    await db.flush()
    try:
        html = await generate_website(body.prompt, ai)
        record.html_content = html
        record.status = "completed"
        return {"id": record.id, "status": "completed", "preview_url": f"/api/v1/websites/{record.id}/preview"}
    except Exception as e:
        record.status = "failed"
        raise HTTPException(500, f"Website generation failed: {str(e)}")

@router.get("/{website_id}/preview", response_class=HTMLResponse)
async def preview_website(website_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(GeneratedWebsite).where(GeneratedWebsite.id == website_id))
    site = result.scalar_one_or_none()
    if not site or not site.html_content: raise HTTPException(404, "Website not found")
    return HTMLResponse(content=site.html_content)

@router.get("/")
async def list_websites(user: User = Depends(_get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(GeneratedWebsite).where(GeneratedWebsite.org_id == user.org_id).order_by(GeneratedWebsite.created_at.desc()).limit(20))
    sites = result.scalars().all()
    return {"websites": [{"id": s.id, "prompt": s.prompt[:80], "status": s.status, "created_at": str(s.created_at)} for s in sites]}
''')

w("src/interfaces/http/routes/voice.py", '''
from __future__ import annotations
import io, base64
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from src.infrastructure.persistence.models.orm_models import User
from src.interfaces.http.routes.auth import _get_current_user

router = APIRouter(prefix="/voice", tags=["voice"])

class TTSRequest(BaseModel):
    text: str
    lang: str = "en"

@router.post("/tts")
async def text_to_speech(body: TTSRequest, user: User = Depends(_get_current_user)):
    try:
        from gtts import gTTS
        tts = gTTS(text=body.text, lang=body.lang)
        buf = io.BytesIO()
        tts.write_to_fp(buf)
        buf.seek(0)
        return {"audio_base64": base64.b64encode(buf.read()).decode(), "format": "mp3"}
    except ImportError:
        raise HTTPException(503, "TTS not available")
    except Exception as e:
        raise HTTPException(500, str(e))
''')

w("src/interfaces/http/routes/audit.py", '''
from __future__ import annotations
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.infrastructure.persistence.database import get_db
from src.infrastructure.persistence.models.orm_models import User, AuditEvent
from src.interfaces.http.routes.auth import _get_current_user

router = APIRouter(prefix="/audit", tags=["audit"])

@router.get("/logs")
async def list_audit_logs(limit: int = Query(50, le=200), user: User = Depends(_get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AuditEvent).where(AuditEvent.org_id == user.org_id).order_by(AuditEvent.created_at.desc()).limit(limit))
    events = result.scalars().all()
    return {"events": [{"id": e.id, "action": e.action, "resource_type": e.resource_type, "created_at": str(e.created_at)} for e in events], "total": len(events)}
''')

w("src/interfaces/http/routes/referral.py", '''
from __future__ import annotations
import secrets
from fastapi import APIRouter, Depends
from src.infrastructure.persistence.models.orm_models import User
from src.interfaces.http.routes.auth import _get_current_user
from src.shared.config.settings import settings

router = APIRouter(prefix="/referral", tags=["referral"])

@router.get("/link")
async def get_referral_link(user: User = Depends(_get_current_user)):
    code = secrets.token_urlsafe(8)
    return {"referral_link": f"{settings.APP_BASE_URL}/register?ref={code}", "code": code}

@router.get("/stats")
async def get_referral_stats(user: User = Depends(_get_current_user)):
    return {"total_referrals": 0, "credits_earned": 0}
''')

w("src/interfaces/http/routes/admin.py", '''
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
async def platform_stats(user: User = Depends(_require_admin), db: AsyncSession = Depends(get_db)):
    org_count = await db.scalar(select(func.count(Organization.id)))
    user_count = await db.scalar(select(func.count(User.id)))
    return {"total_organizations": org_count, "total_users": user_count}

@router.get("/users")
async def list_users(user: User = Depends(_require_admin), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).order_by(User.created_at.desc()).limit(100))
    users = result.scalars().all()
    return {"users": [{"id": u.id, "email": u.email, "full_name": u.full_name, "role": u.role, "org_id": u.org_id} for u in users]}
''')

w("src/interfaces/http/routes/memory.py", '''
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
async def add_memory(body: MemoryCreateRequest, user: User = Depends(_get_current_user), db: AsyncSession = Depends(get_db)):
    entry = MemoryEntry(org_id=user.org_id, user_id=user.id, content=body.content, metadata_=body.metadata)
    db.add(entry)
    await db.flush()
    return {"id": entry.id, "content": entry.content, "created_at": str(entry.created_at)}

@router.get("/")
async def list_memories(user: User = Depends(_get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MemoryEntry).where(MemoryEntry.org_id == user.org_id).order_by(MemoryEntry.created_at.desc()).limit(100))
    entries = result.scalars().all()
    return {"memories": [{"id": e.id, "content": e.content[:200], "created_at": str(e.created_at)} for e in entries], "total": len(entries)}

@router.delete("/{memory_id}")
async def delete_memory(memory_id: str, user: User = Depends(_get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MemoryEntry).where(MemoryEntry.id == memory_id, MemoryEntry.org_id == user.org_id))
    entry = result.scalar_one_or_none()
    if not entry: raise HTTPException(404, "Memory not found")
    await db.delete(entry)
    return {"message": "Deleted"}
''')

print("\n✅ ALL FILES CREATED SUCCESSFULLY!")
print("Now run: python -m uvicorn src.main:app --host 0.0.0.0 --port 8000")
