import os, sys, subprocess

def w(path, content):
    os.makedirs(os.path.dirname(path) if "/" in path else ".", exist_ok=True)
    open(path, "w").write(content)
    print(f"Created: {path}")

w("src/__init__.py", "")

w("src/shared/__init__.py", "")
w("src/shared/config/__init__.py", "")
w("src/shared/security/__init__.py", "")
w("src/shared/exceptions/__init__.py", "")
w("src/shared/observability/__init__.py", "")
w("src/shared/logging/__init__.py", "")
w("src/domain/__init__.py", "")
w("src/domain/entities/__init__.py", "")
w("src/application/__init__.py", "")
w("src/application/use_cases/__init__.py", "")
w("src/application/use_cases/website/__init__.py", "")
w("src/infrastructure/__init__.py", "")
w("src/infrastructure/ai_providers/__init__.py", "")
w("src/infrastructure/email/__init__.py", "")
w("src/infrastructure/cache/__init__.py", "")
w("src/infrastructure/storage/__init__.py", "")
w("src/infrastructure/persistence/__init__.py", "")
w("src/infrastructure/persistence/models/__init__.py", "")
w("src/infrastructure/persistence/repositories/__init__.py", "")
w("src/infrastructure/billing/__init__.py", "")
w("src/infrastructure/media/__init__.py", "")
w("src/interfaces/__init__.py", "")
w("src/interfaces/http/__init__.py", "")
w("src/interfaces/http/middleware/__init__.py", "")
w("src/interfaces/http/dependencies/__init__.py", "")
w("src/interfaces/http/routes/__init__.py", "")

w("src/shared/config/settings.py", """
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    APP_NAME: str = "Dacexy Enterprise AI Platform"
    APP_VERSION: str = "10.0.0"
    ENVIRONMENT: str = "production"
    DEBUG: bool = False
    API_PREFIX: str = "/api/v1"
    LOG_LEVEL: str = "INFO"
    ALLOWED_ORIGINS: str = "http://localhost:3000"
    SECRET_KEY: str = "changeme"
    DATABASE_URL: str = ""
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    UPSTASH_REDIS_REST_URL: str = ""
    UPSTASH_REDIS_REST_TOKEN: str = ""
    CELERY_BROKER_URL: str = ""
    CELERY_RESULT_BACKEND: str = ""
    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""
    SUPABASE_STORAGE_BUCKET: str = "dacexy-files"
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_TIMEOUT: int = 180
    DEEPSEEK_MAX_RETRIES: int = 3
    BYTEZ_API_KEY: str = ""
    SMTP_HOST: str = "smtp-relay.brevo.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASS: str = ""
    SMTP_USE_TLS: bool = True
    EMAIL_FROM: str = "noreply@dacexy.ai"
    EMAIL_FROM_NAME: str = "Dacexy"
    APP_BASE_URL: str = "https://app.dacexy.ai"
    PLATFORM_URL: str = "https://api.dacexy.ai"
    RAZORPAY_KEY_ID: str = ""
    RAZORPAY_KEY_SECRET: str = ""
    RAZORPAY_WEBHOOK_SECRET: str = ""
    VERCEL_TOKEN: str = ""
    VERCEL_TEAM_ID: str = ""
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_DEFAULT_RPM: int = 60
    RATE_LIMIT_AUTH_RPM: int = 10
    RATE_LIMIT_AI_RPM: int = 30
    AGENT_MAX_STEPS: int = 30
    AGENT_MAX_EXECUTION_SECS: int = 600
    SENTRY_DSN: str = ""
    OTLP_ENDPOINT: str = ""
    PROMETHEUS_ENABLED: bool = True

    @property
    def allowed_origins_list(self):
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]

    @property
    def async_database_url(self):
        url = self.DATABASE_URL
        if url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        return url

    @property
    def payments_enabled(self):
        return bool(self.RAZORPAY_KEY_ID and self.RAZORPAY_KEY_SECRET)

settings = Settings()
""")

w("src/shared/security/auth.py", """
import secrets
from datetime import datetime, timedelta
from jose import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from src.shared.config.settings import settings

ph = PasswordHasher()

def hash_password(password):
    return ph.hash(password)

def verify_password(plain, hashed):
    try:
        return ph.verify(hashed, plain)
    except VerifyMismatchError:
        return False

def create_access_token(subject, extra=None, expires_minutes=60):
    data = {"sub": subject, "type": "access"}
    if extra:
        data.update(extra)
    data["exp"] = datetime.utcnow() + timedelta(minutes=expires_minutes)
    return jwt.encode(data, settings.SECRET_KEY, algorithm="HS256")

def create_refresh_token():
    return secrets.token_urlsafe(64)

def decode_access_token(token):
    return jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
""")

w("src/shared/exceptions/__init__.py", """
from fastapi import HTTPException

def not_found(detail="Not found"):
    raise HTTPException(status_code=404, detail=detail)

def unauthorized(detail="Unauthorized"):
    raise HTTPException(status_code=401, detail=detail)

def bad_request(detail="Bad request"):
    raise HTTPException(status_code=400, detail=detail)
""")

w("src/infrastructure/persistence/database.py", """
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from src.shared.config.settings import settings

engine = create_async_engine(settings.async_database_url, pool_size=settings.DATABASE_POOL_SIZE, max_overflow=settings.DATABASE_MAX_OVERFLOW, pool_pre_ping=True, echo=False, connect_args={"ssl": "require"})
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
""")

w("src/infrastructure/persistence/models/orm_models.py", """
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Integer, Text, JSON, ForeignKey, BigInteger
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy.sql import func

class Base(DeclarativeBase):
    pass

def new_uuid():
    return str(uuid.uuid4())

class Organization(Base):
    __tablename__ = "organizations"
    id = Column(UUID(as_uuid=False), primary_key=True, default=new_uuid)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False)
    plan_tier = Column(String(50), default="free")
    credits_balance = Column(BigInteger, default=0)
    monthly_ai_calls = Column(Integer, default=0)
    monthly_ai_calls_reset = Column(DateTime, nullable=True)
    metadata_ = Column("metadata", JSON, default=dict)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    users = relationship("User", back_populates="org")
    api_keys = relationship("ApiKey", back_populates="org")

class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=False), primary_key=True, default=new_uuid)
    org_id = Column(UUID(as_uuid=False), ForeignKey("organizations.id"), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    full_name = Column(String(255), nullable=False)
    hashed_password = Column(Text, nullable=False)
    role = Column(String(50), default="member")
    is_verified = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    metadata_ = Column("metadata", JSON, default=dict)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    org = relationship("Organization", back_populates="users")

class ApiKey(Base):
    __tablename__ = "api_keys"
    id = Column(UUID(as_uuid=False), primary_key=True, default=new_uuid)
    org_id = Column(UUID(as_uuid=False), ForeignKey("organizations.id"), nullable=False)
    name = Column(String(255), nullable=False)
    key_hash = Column(Text, nullable=False, unique=True)
    key_prefix = Column(String(20), nullable=False)
    is_active = Column(Boolean, default=True)
    last_used_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now())
    org = relationship("Organization", back_populates="api_keys")

class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    id = Column(UUID(as_uuid=False), primary_key=True, default=new_uuid)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)
    token_hash = Column(Text, nullable=False, unique=True)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=func.now())

class ConversationSession(Base):
    __tablename__ = "conversation_sessions"
    id = Column(UUID(as_uuid=False), primary_key=True, default=new_uuid)
    org_id = Column(UUID(as_uuid=False), ForeignKey("organizations.id"), nullable=False)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)
    title = Column(String(500), default="New Chat")
    messages = Column(JSON, default=list)
    total_tokens = Column(Integer, default=0)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class AuditEvent(Base):
    __tablename__ = "audit_events"
    id = Column(UUID(as_uuid=False), primary_key=True, default=new_uuid)
    org_id = Column(UUID(as_uuid=False), ForeignKey("organizations.id"), nullable=False)
    user_id = Column(UUID(as_uuid=False), nullable=True)
    action = Column(String(100), nullable=False)
    resource_type = Column(String(100), nullable=True)
    resource_id = Column(String(255), nullable=True)
    metadata_ = Column("metadata", JSON, default=dict)
    ip_address = Column(String(45), nullable=True)
    created_at = Column(DateTime, default=func.now())

class Subscription(Base):
    __tablename__ = "subscriptions"
    id = Column(UUID(as_uuid=False), primary_key=True, default=new_uuid)
    org_id = Column(UUID(as_uuid=False), ForeignKey("organizations.id"), unique=True)
    plan_tier = Column(String(50), default="free")
    status = Column(String(50), default="active")
    razorpay_subscription_id = Column(String(255), nullable=True)
    current_period_start = Column(DateTime, nullable=True)
    current_period_end = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class Invoice(Base):
    __tablename__ = "invoices"
    id = Column(UUID(as_uuid=False), primary_key=True, default=new_uuid)
    org_id = Column(UUID(as_uuid=False), ForeignKey("organizations.id"), nullable=False)
    amount_paise = Column(BigInteger, nullable=False)
    currency = Column(String(10), default="INR")
    status = Column(String(50), default="pending")
    razorpay_order_id = Column(String(255), nullable=True)
    razorpay_payment_id = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())

class UsageRecord(Base):
    __tablename__ = "usage_records"
    id = Column(UUID(as_uuid=False), primary_key=True, default=new_uuid)
    org_id = Column(UUID(as_uuid=False), ForeignKey("organizations.id"), nullable=False)
    user_id = Column(UUID(as_uuid=False), nullable=True)
    feature = Column(String(100), nullable=False)
    quantity = Column(Integer, default=1)
    metadata_ = Column("metadata", JSON, default=dict)
    created_at = Column(DateTime, default=func.now())

class GeneratedImage(Base):
    __tablename__ = "generated_images"
    id = Column(UUID(as_uuid=False), primary_key=True, default=new_uuid)
    org_id = Column(UUID(as_uuid=False), ForeignKey("organizations.id"), nullable=False)
    user_id = Column(UUID(as_uuid=False), nullable=True)
    prompt = Column(Text, nullable=False)
    url = Column(Text, nullable=True)
    status = Column(String(50), default="pending")
    created_at = Column(DateTime, default=func.now())

class GeneratedVideo(Base):
    __tablename__ = "generated_videos"
    id = Column(UUID(as_uuid=False), primary_key=True, default=new_uuid)
    org_id = Column(UUID(as_uuid=False), ForeignKey("organizations.id"), nullable=False)
    user_id = Column(UUID(as_uuid=False), nullable=True)
    prompt = Column(Text, nullable=False)
    url = Column(Text, nullable=True)
    status = Column(String(50), default="pending")
    created_at = Column(DateTime, default=func.now())

class GeneratedWebsite(Base):
    __tablename__ = "generated_websites"
    id = Column(UUID(as_uuid=False), primary_key=True, default=new_uuid)
    org_id = Column(UUID(as_uuid=False), ForeignKey("organizations.id"), nullable=False)
    user_id = Column(UUID(as_uuid=False), nullable=True)
    prompt = Column(Text, nullable=False)
    html_content = Column(Text, nullable=True)
    status = Column(String(50), default="pending")
    created_at = Column(DateTime, default=func.now())

class MemoryEntry(Base):
    __tablename__ = "memory_entries"
    id = Column(UUID(as_uuid=False), primary_key=True, default=new_uuid)
    org_id = Column(UUID(as_uuid=False), ForeignKey("organizations.id"), nullable=False)
    user_id = Column(UUID(as_uuid=False), nullable=True)
    content = Column(Text, nullable=False)
    embedding = Column(JSON, nullable=True)
    metadata_ = Column("metadata", JSON, default=dict)
    created_at = Column(DateTime, default=func.now())

class AiTask(Base):
    __tablename__ = "ai_tasks"
    id = Column(UUID(as_uuid=False), primary_key=True, default=new_uuid)
    org_id = Column(UUID(as_uuid=False), ForeignKey("organizations.id"), nullable=False)
    user_id = Column(UUID(as_uuid=False), nullable=True)
    task_type = Column(String(100), nullable=False)
    status = Column(String(50), default="pending")
    input_data = Column(JSON, default=dict)
    output_data = Column(JSON, nullable=True)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
""")

w("src/infrastructure/ai_providers/deepseek.py", """
import json
import httpx
from src.shared.config.settings import settings

class DeepSeekProvider:
    BASE_URL = "https://api.deepseek.com/v1"

    def __init__(self):
        self.client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            headers={"Authorization": "Bearer " + settings.DEEPSEEK_API_KEY},
            timeout=settings.DEEPSEEK_TIMEOUT,
        )

    async def chat(self, messages, model="deepseek-chat", stream=False, search=False):
        payload = {
            "model": model,
            "messages": messages,
            "stream": stream,
        }
        if search:
            payload["model"] = "deepseek-chat"
        if stream:
            return self._stream(payload)
        r = await self.client.post("/chat/completions", json=payload)
        r.raise_for_status()
        data = r.json()
        msg = data["choices"][0]["message"]
        return msg.get("content") or ""

    async def _stream(self, payload):
        async with self.client.stream("POST", "/chat/completions", json=payload) as r:
            r.raise_for_status()
            async for line in r.aiter_lines():
                if line.startswith("data: "):
                    raw = line[6:]
                    if raw == "[DONE]":
                        break
                    try:
                        chunk = json.loads(raw)
                        choice = chunk["choices"][0]
                        delta = choice.get("delta", {})
                        content = delta.get("content", "")
                        if content:
                            yield content
                        tool_calls = delta.get("tool_calls", [])
                        for tc in tool_calls:
                            if tc.get("type") == "web_search":
                                yield "\\n🔍 *Searching the web...*\\n"
                    except Exception:
                        pass
                

    async def aclose(self):
        await self.client.aclose()
""")

w("src/infrastructure/email/email_service.py", """
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from src.shared.config.settings import settings

log = logging.getLogger("email")

class EmailService:
    def _send(self, to, subject, html):
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = settings.EMAIL_FROM_NAME + " <" + settings.EMAIL_FROM + ">"
            msg["To"] = to
            msg.attach(MIMEText(html, "html"))
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as s:
                if settings.SMTP_USE_TLS:
                    s.starttls()
                s.login(settings.SMTP_USER, settings.SMTP_PASS)
                s.sendmail(settings.EMAIL_FROM, to, msg.as_string())
            log.info("Email sent to %s", to)
        except Exception as e:
            log.error("Email failed: %s", e)

    def send_verification_email(self, to, token):
        url = settings.APP_BASE_URL + "/verify-email?token=" + token
        self._send(to, "Verify your Dacexy account", "<h2>Welcome to Dacexy!</h2><p><a href='" + url + "'>Verify Email</a></p>")

    def send_password_reset(self, to, token):
        url = settings.APP_BASE_URL + "/reset-password?token=" + token
        self._send(to, "Reset your Dacexy password", "<h2>Password Reset</h2><p><a href='" + url + "'>Reset Password</a></p>")
""")

w("src/infrastructure/cache/upstash.py", """
import logging
import httpx
from src.shared.config.settings import settings

log = logging.getLogger("cache")

class UpstashRedis:
    def __init__(self):
        self.url = settings.UPSTASH_REDIS_REST_URL
        self.token = settings.UPSTASH_REDIS_REST_TOKEN

    def _headers(self):
        return {"Authorization": "Bearer " + self.token}

    async def get(self, key):
        if not self.url: return None
        try:
            async with httpx.AsyncClient() as c:
                r = await c.get(self.url + "/get/" + key, headers=self._headers(), timeout=5)
                return r.json().get("result")
        except Exception:
            return None

    async def set(self, key, value, ex=3600):
        if not self.url: return False
        try:
            async with httpx.AsyncClient() as c:
                r = await c.get(self.url + "/set/" + key + "/" + str(value) + "/ex/" + str(ex), headers=self._headers(), timeout=5)
                return r.json().get("result") == "OK"
        except Exception:
            return False

    async def ping(self):
        if not self.url: return False
        try:
            async with httpx.AsyncClient() as c:
                r = await c.get(self.url + "/ping", headers=self._headers(), timeout=5)
                return r.json().get("result") == "PONG"
        except Exception:
            return False
""")

w("src/infrastructure/storage/supabase_storage.py", """
import logging
import httpx
from src.shared.config.settings import settings

log = logging.getLogger("storage")

class SupabaseStorage:
    def __init__(self):
        self.url = settings.SUPABASE_URL
        self.key = settings.SUPABASE_SERVICE_ROLE_KEY
        self.bucket = settings.SUPABASE_STORAGE_BUCKET

    def _headers(self):
        return {"Authorization": "Bearer " + self.key, "apikey": self.key}

    async def upload(self, path, content, content_type="application/octet-stream"):
        if not self.url or not self.key: return None
        try:
            async with httpx.AsyncClient() as c:
                headers = self._headers()
                headers["Content-Type"] = content_type
                r = await c.post(self.url + "/storage/v1/object/" + self.bucket + "/" + path, headers=headers, content=content, timeout=30)
                if r.status_code in (200, 201):
                    return self.url + "/storage/v1/object/public/" + self.bucket + "/" + path
        except Exception as e:
            log.error("Storage error: %s", e)
        return None
""")

w("src/interfaces/http/dependencies/container.py", """
from src.infrastructure.ai_providers.deepseek import DeepSeekProvider
from src.infrastructure.email.email_service import EmailService
from src.infrastructure.cache.upstash import UpstashRedis
from src.infrastructure.storage.supabase_storage import SupabaseStorage

_deepseek = None
_email = None
_redis = None
_storage = None

def get_deepseek():
    global _deepseek
    if _deepseek is None:
        _deepseek = DeepSeekProvider()
    return _deepseek

def get_email():
    global _email
    if _email is None:
        _email = EmailService()
    return _email

def get_redis():
    global _redis
    if _redis is None:
        _redis = UpstashRedis()
    return _redis

def get_storage():
    global _storage
    if _storage is None:
        _storage = SupabaseStorage()
    return _storage
""")

w("src/interfaces/http/middleware/rate_limit.py", """
import time
from collections import defaultdict
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from src.shared.config.settings import settings

_counters = defaultdict(lambda: {"count": 0, "reset_at": 0})

class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        if not settings.RATE_LIMIT_ENABLED:
            return await call_next(request)
        ip = request.client.host if request.client else "unknown"
        path = request.url.path
        if "/auth/" in path:
            limit = settings.RATE_LIMIT_AUTH_RPM
        elif "/ai/" in path:
            limit = settings.RATE_LIMIT_AI_RPM
        else:
            limit = settings.RATE_LIMIT_DEFAULT_RPM
        now = time.time()
        bucket = _counters[ip + ":" + path]
        if now > bucket["reset_at"]:
            bucket["count"] = 0
            bucket["reset_at"] = now + 60
        bucket["count"] += 1
        if bucket["count"] > limit:
            return Response(content='{"detail":"Rate limit exceeded"}', status_code=429, media_type="application/json")
        return await call_next(request)
""")

w("src/application/use_cases/website/website_engine.py", '''
import logging
import asyncio
from src.infrastructure.ai_providers.deepseek import DeepSeekProvider

log = logging.getLogger("website")

SYSTEM_PROMPT = (
    "You are an expert senior web developer. Your job is to generate a COMPLETE, BEAUTIFUL, PRODUCTION-READY single page HTML website.\\n\\n"
    "MANDATORY RULES - FOLLOW EXACTLY:\\n"
    "1. Return ONLY raw HTML. Zero explanations. Zero markdown. Zero backticks.\\n"
    "2. Start with <!DOCTYPE html> and end with </html>\\n"
    "3. Use a <style> tag with extensive CSS - minimum 150 lines of CSS\\n"
    "4. Include Google Fonts via @import in the style tag\\n"
    "5. Use beautiful gradients, shadows, hover effects, animations\\n"
    "6. Include ALL these sections: navigation, hero, features/menu/services, about, gallery, testimonials, pricing/contact, footer\\n"
    "7. Use real placeholder content relevant to the prompt\\n"
    "8. Use https://picsum.photos for images e.g. https://picsum.photos/800/400\\n"
    "9. Make it fully responsive with mobile CSS\\n"
    "10. Add smooth scroll, hover animations, fade-in effects with JavaScript\\n"
    "11. The HTML must be COMPLETE - do not cut off or truncate"
)

FALLBACK_HTML = (
    "<!DOCTYPE html><html lang=\\"en\\"><head><meta charset=\\"UTF-8\\"><title>Error</title>"
    "<style>body{font-family:sans-serif;background:#0f0f0f;color:#fff;display:flex;"
    "align-items:center;justify-content:center;min-height:100vh;margin:0}"
    ".box{text-align:center;padding:40px}h1{font-size:2rem;color:#7c3aed;margin-bottom:16px}"
    "p{color:#9e9e9e;margin-bottom:24px}a{background:#7c3aed;color:#fff;padding:12px 28px;"
    "border-radius:10px;text-decoration:none}</style></head><body>"
    "<div class=\\"box\\"><h1>Generation Failed</h1><p>Please try again.</p>"
    "<a href=\\"javascript:history.back()\\">Try Again</a></div></body></html>"
)

async def generate_website(prompt: str, ai: DeepSeekProvider) -> str:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": "Build a COMPLETE beautiful website for: " + prompt + ". Include ALL sections with real content. Use picsum.photos for images. Return complete HTML from <!DOCTYPE html> to </html>. Do NOT truncate."}
    ]
    try:
        html = await asyncio.wait_for(
            ai.chat(messages, model="deepseek-chat", stream=False),
            timeout=120.0
        )
        if not html or len(html.strip()) < 500:
            return FALLBACK_HTML
        html = html.strip()
        if "```html" in html:
            html = html.split("```html")[1].split("```")[0].strip()
        elif "```" in html:
            html = html.split("```")[1].split("```")[0].strip()
        if not html.startswith("<!") and not html.lower().startswith("<html"):
            html = "<!DOCTYPE html><html><head><meta charset=\\"UTF-8\\"></head><body>" + html + "</body></html>"
        if not html.rstrip().endswith("</html>"):
            html = html + "</body></html>"
        return html
    except asyncio.TimeoutError:
        log.error("Website generation timed out")
        return FALLBACK_HTML
    except Exception as e:
        log.error("Website generation failed: %s", e)
        return FALLBACK_HTML
''')

w("src/interfaces/http/routes/auth.py", """
import secrets
import re
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

def _make_slug(name):
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug + "-" + secrets.token_hex(4)

async def _get_current_user(creds: HTTPAuthorizationCredentials = Depends(bearer), db: AsyncSession = Depends(get_db)):
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
    org_name = body.org_name or (body.full_name.split()[0] + "'s Workspace")
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
""")
w("src/interfaces/http/routes/ai_chat.py", """
import json
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from src.infrastructure.persistence.database import get_db
from src.infrastructure.persistence.models.orm_models import User, ConversationSession, MemoryEntry, GeneratedWebsite
from src.infrastructure.ai_providers.deepseek import DeepSeekProvider
from src.interfaces.http.dependencies.container import get_deepseek
from src.interfaces.http.routes.auth import _get_current_user

router = APIRouter(prefix="/ai", tags=["ai"])

SEARCH_KEYWORDS = [
    "search", "latest", "current", "today", "news", "recent", "now",
    "price", "weather", "who is", "what is the", "2025", "2026",
    "trending", "happening", "live", "update", "score", "stock",
    "find", "look up", "research", "browse", "internet"
]

def needs_search(messages: list) -> bool:
    if not messages:
        return False
    last = messages[-1]["content"].lower()
    return any(kw in last for kw in SEARCH_KEYWORDS)

def needs_website(messages: list) -> bool:
    if not messages:
        return False
    last = messages[-1]["content"].lower()
    has_build = any(w in last for w in ["build", "make", "create", "generate", "design"])
    has_site = any(w in last for w in ["website", "landing page", "webpage", "site", "web app", "homepage"])
    return has_build and has_site

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

    search = needs_search(messages)
    website = needs_website(messages)

    memory_result = await db.execute(select(MemoryEntry).where(MemoryEntry.org_id == user.org_id).order_by(MemoryEntry.created_at.desc()).limit(20))
    memories = memory_result.scalars().all()
    if memories:
        memory_context = "\\n".join([f"- {m.content}" for m in memories])
        system_msg = {"role": "system", "content": f"You are Dacexy AI, a helpful enterprise AI assistant. Here is important context about this user and their business:\\n{memory_context}\\n\\nUse this context to personalize your responses."}
        messages = [system_msg] + messages

    last_content = body.messages[-1].content if body.messages else ""
    memory_keywords = ["my company", "my business", "we are", "i am", "our product", "my name is", "we sell", "our team", "my startup", "remember that", "remember this", "save this"]
    if any(kw in last_content.lower() for kw in memory_keywords):
        new_memory = MemoryEntry(org_id=user.org_id, user_id=user.id, content=last_content[:500])
        db.add(new_memory)
        await db.flush()

    if website and body.stream:
        from src.application.use_cases.website.website_engine import generate_website
        prompt = body.messages[-1].content
        record = GeneratedWebsite(org_id=user.org_id, user_id=user.id, prompt=prompt, status="generating")
        db.add(record)
        await db.flush()
        record_id = record.id
        session_id = session.id
        async def website_stream():
            yield "data: " + json.dumps({"type": "session_id", "session_id": session_id}) + "\\n\\n"
            yield "data: " + json.dumps({"type": "chunk", "content": "🌐 Building your website...\\n\\n"}) + "\\n\\n"
            try:
                html = await generate_website(prompt, ai)
                record.html_content = html
                record.status = "completed"
                await db.commit()
                preview_url = "/api/v1/websites/" + record_id + "/preview"
                msg = "✅ Your website is ready!\\n\\nPreview: " + preview_url + "\\n\\nClick Open full screen to see your website."
                yield "data: " + json.dumps({"type": "chunk", "content": msg}) + "\\n\\n"
            except Exception as e:
                record.status = "failed"
                yield "data: " + json.dumps({"type": "chunk", "content": "Website generation failed: " + str(e)}) + "\\n\\n"
            yield "data: " + json.dumps({"type": "done"}) + "\\n\\n"
        return StreamingResponse(website_stream(), media_type="text/event-stream")

    if body.stream:
        session_id = session.id
        async def event_stream():
            full = ""
            yield "data: " + json.dumps({"type": "session_id", "session_id": session_id}) + "\\n\\n"
            if search:
                yield "data: " + json.dumps({"type": "chunk", "content": "🔍 Searching the web...\\n\\n"}) + "\\n\\n"
            async for chunk in await ai.chat(messages, model=body.model, stream=True, search=search):
                full += chunk
                yield "data: " + json.dumps({"type": "chunk", "content": chunk}) + "\\n\\n"
            yield "data: " + json.dumps({"type": "done"}) + "\\n\\n"
            session.messages = messages + [{"role": "assistant", "content": full}]
        return StreamingResponse(event_stream(), media_type="text/event-stream")

    response = await ai.chat(messages, model=body.model, stream=False, search=search)
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
    """)
    
w("src/interfaces/http/routes/orgs.py", """
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
    raw_key = "dacexy_" + secrets.token_urlsafe(32)
    key = ApiKey(org_id=user.org_id, name=body.name, key_hash=hash_password(raw_key), key_prefix=raw_key[:12])
    db.add(key)
    await db.flush()
    return {"id": key.id, "name": key.name, "key": raw_key, "key_prefix": key.key_prefix}
""")

w("src/interfaces/http/routes/billing.py", """
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
        db.add(Invoice(org_id=user.org_id, amount_paise=plan["price_inr"] * 100, razorpay_order_id=order["id"], description="Upgrade to " + plan["name"]))
        return {"order_id": order["id"], "amount": plan["price_inr"] * 100, "currency": "INR", "key": settings.RAZORPAY_KEY_ID}
    except Exception as e:
        raise HTTPException(500, "Payment error: " + str(e))

@router.get("/usage")
async def get_usage(user: User = Depends(_get_current_user), db: AsyncSession = Depends(get_db)):
    org = await db.get(Organization, user.org_id)
    return {"plan_tier": org.plan_tier if org else "free", "credits_balance": org.credits_balance if org else 0, "monthly_ai_calls": org.monthly_ai_calls if org else 0}
""")

w("src/interfaces/http/routes/agent.py", """
from __future__ import annotations
import json
import asyncio
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, Dict
from src.infrastructure.persistence.database import get_db
from src.infrastructure.persistence.models.orm_models import User, AiTask
from src.infrastructure.ai_providers.deepseek import DeepSeekProvider
from src.interfaces.http.dependencies.container import get_deepseek
from src.interfaces.http.routes.auth import _get_current_user
from src.shared.config.settings import settings

router = APIRouter(prefix="/agent", tags=["agent"])

active_agents: Dict[str, WebSocket] = {}
agent_results: Dict[str, dict] = {}

class AgentRunRequest(BaseModel):
    task: str
    context: Optional[str] = None
    max_steps: int = 10

class DesktopCommandRequest(BaseModel):
    action: str
    x: Optional[int] = None
    y: Optional[int] = None
    text: Optional[str] = None
    key: Optional[str] = None
    keys: Optional[list] = None
    url: Optional[str] = None
    command: Optional[str] = None
    clicks: Optional[int] = 3
    app: Optional[str] = None
    button: Optional[str] = "left"
    duration: Optional[float] = 0.3

@router.post("/run")
async def run_agent(body: AgentRunRequest, user: User = Depends(_get_current_user), db: AsyncSession = Depends(get_db), ai: DeepSeekProvider = Depends(get_deepseek)):
    system_prompt = "You are an autonomous AI agent for Dacexy. Break down tasks into steps and execute them systematically."
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Task: {body.task}" + (f"\\nContext: {body.context}" if body.context else "")}
    ]
    task_record = AiTask(org_id=user.org_id, user_id=user.id, task_type="agent_run", status="running", input_data={"task": body.task})
    db.add(task_record)
    await db.flush()
    try:
        result = await ai.chat(messages, model="deepseek-chat", stream=False)
        task_record.status = "completed"
        task_record.output_data = {"result": result}
        await db.commit()
        return {"task_id": task_record.id, "status": "completed", "result": result}
    except Exception as e:
        task_record.status = "failed"
        await db.commit()
        raise HTTPException(500, f"Agent error: {str(e)}")

@router.get("/tasks")
async def list_tasks(user: User = Depends(_get_current_user), db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select
    result = await db.execute(select(AiTask).where(AiTask.org_id == user.org_id).order_by(AiTask.created_at.desc()).limit(20))
    tasks = result.scalars().all()
    return {"tasks": [{"id": t.id, "task_type": t.task_type, "status": t.status, "created_at": str(t.created_at)} for t in tasks]}

@router.get("/desktop/status")
async def desktop_status(user: User = Depends(_get_current_user)):
    user_id = str(user.id)
    return {"connected": user_id in active_agents, "user_id": user_id}

@router.get("/desktop/last_result")
async def get_last_result(user: User = Depends(_get_current_user)):
    user_id = str(user.id)
    return {"result": agent_results.get(user_id), "connected": user_id in active_agents}

@router.post("/desktop/command")
async def send_desktop_command(body: DesktopCommandRequest, user: User = Depends(_get_current_user)):
    user_id = str(user.id)
    if user_id not in active_agents:
        raise HTTPException(400, "Desktop agent not connected. Run the agent on your computer first.")
    ws = active_agents[user_id]
    try:
        await ws.send_text(json.dumps(body.dict()))
        return {"status": "sent", "action": body.action}
    except Exception as e:
        active_agents.pop(user_id, None)
        raise HTTPException(500, f"Failed to send command: {str(e)}")

@router.websocket("/desktop/ws")
async def desktop_websocket(websocket: WebSocket):
    await websocket.accept()
    user_id = None
    try:
        auth_raw = await asyncio.wait_for(websocket.receive_text(), timeout=30)
        try:
            auth_data = json.loads(auth_raw)
            token = auth_data.get("token", "")
        except Exception:
            token = auth_raw.strip()

        try:
            from jose import jwt
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            user_id = str(payload.get("sub") or payload.get("user_id") or "")
            if not user_id:
                await websocket.send_text(json.dumps({"type": "error", "message": "Invalid token payload"}))
                await websocket.close()
                return
        except Exception as e:
            await websocket.send_text(json.dumps({"type": "error", "message": "Authentication failed"}))
            await websocket.close()
            return

        active_agents[user_id] = websocket
        await websocket.send_text(json.dumps({"type": "connected", "message": "Desktop agent connected", "user_id": user_id}))

        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=60)
                msg = json.loads(data)
                msg_type = msg.get("type", "")
                if msg_type == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
                elif msg_type in ["result", "screenshot_before", "screenshot_after", "system_info", "error", "voice_result"]:
                    agent_results[user_id] = msg
            except asyncio.TimeoutError:
                try:
                    await websocket.send_text(json.dumps({"type": "ping"}))
                except Exception:
                    break
            except WebSocketDisconnect:
                break
            except Exception:
                break
    except Exception:
        pass
    finally:
        if user_id:
            active_agents.pop(user_id, None)
            agent_results.pop(user_id, None)
""")



w("src/interfaces/http/routes/websites.py", """
import httpx
import re
import random
import string
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from src.infrastructure.persistence.database import get_db
from src.infrastructure.persistence.models.orm_models import User, GeneratedWebsite
from src.infrastructure.ai_providers.deepseek import DeepSeekProvider
from src.interfaces.http.dependencies.container import get_deepseek
from src.interfaces.http.routes.auth import _get_current_user
from src.application.use_cases.website.website_engine import generate_website
from src.shared.config.settings import settings

router = APIRouter(prefix="/websites", tags=["websites"])

class WebsiteRequest(BaseModel):
    prompt: str

class DeployRequest(BaseModel):
    website_id: str
    subdomain: Optional[str] = None

def random_subdomain():
    return 'site-' + ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))

@router.post("/generate")
async def create_website(body: WebsiteRequest, user: User = Depends(_get_current_user), db: AsyncSession = Depends(get_db), ai: DeepSeekProvider = Depends(get_deepseek)):
    record = GeneratedWebsite(org_id=user.org_id, user_id=user.id, prompt=body.prompt, status="generating")
    db.add(record)
    await db.flush()
    try:
        html = await generate_website(body.prompt, ai)
        record.html_content = html
        record.status = "completed"
        await db.commit()
        return {"id": record.id, "status": "completed", "preview_url": "/api/v1/websites/" + str(record.id) + "/preview"}
    except Exception as e:
        record.status = "failed"
        await db.commit()
        raise HTTPException(500, "Website generation failed: " + str(e))

@router.post("/deploy")
async def deploy_website(body: DeployRequest, user: User = Depends(_get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(GeneratedWebsite).where(GeneratedWebsite.id == body.website_id, GeneratedWebsite.org_id == user.org_id))
    site = result.scalar_one_or_none()
    if not site or not site.html_content:
        raise HTTPException(404, "Website not found")
    subdomain = body.subdomain or random_subdomain()
    subdomain = re.sub(r'[^a-z0-9-]', '-', subdomain.lower()).strip('-')
    if len(subdomain) < 3:
        subdomain = random_subdomain()
    try:
        vercel_token = getattr(settings, 'VERCEL_TOKEN', None)
        if not vercel_token:
            raise HTTPException(500, "Vercel token not configured")
        files = [{"file": "index.html", "data": site.html_content}]
        async with httpx.AsyncClient(timeout=60) as client:
            deploy_res = await client.post(
                "https://api.vercel.com/v13/deployments",
                headers={"Authorization": "Bearer " + vercel_token, "Content-Type": "application/json"},
                json={
                    "name": "dacexy-" + subdomain,
                    "files": files,
                    "projectSettings": {"framework": None},
                    "target": "production"
                }
            )
            if deploy_res.status_code not in [200, 201]:
                raise HTTPException(500, "Deployment failed: " + deploy_res.text)
            deploy_data = deploy_res.json()
            deploy_url = "https://" + deploy_data.get("url", "")
            site.deployed_url = deploy_url
            await db.commit()
            return {"url": deploy_url, "subdomain": subdomain, "status": "deployed"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, "Deployment error: " + str(e))

@router.get("/{website_id}/preview", response_class=HTMLResponse)
async def preview_website(website_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(GeneratedWebsite).where(GeneratedWebsite.id == website_id))
    site = result.scalar_one_or_none()
    if not site or not site.html_content:
        raise HTTPException(404, "Website not found")
    return HTMLResponse(content=site.html_content)

@router.get("/")
async def list_websites(user: User = Depends(_get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(GeneratedWebsite).where(GeneratedWebsite.org_id == user.org_id).order_by(GeneratedWebsite.created_at.desc()).limit(20))
    sites = result.scalars().all()
    return {"websites": [{"id": str(s.id), "prompt": s.prompt[:80], "status": s.status, "created_at": str(s.created_at), "deployed_url": getattr(s, 'deployed_url', None)} for s in sites]}
""")

w("src/interfaces/http/routes/voice.py", """
import io
import base64
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
""")

w("src/interfaces/http/routes/audit.py", """
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
""")

w("src/interfaces/http/routes/referral.py", """
import secrets
from fastapi import APIRouter, Depends
from src.infrastructure.persistence.models.orm_models import User
from src.interfaces.http.routes.auth import _get_current_user
from src.shared.config.settings import settings

router = APIRouter(prefix="/referral", tags=["referral"])

@router.get("/link")
async def get_referral_link(user: User = Depends(_get_current_user)):
    code = secrets.token_urlsafe(8)
    return {"referral_link": settings.APP_BASE_URL + "/register?ref=" + code, "code": code}

@router.get("/stats")
async def get_referral_stats(user: User = Depends(_get_current_user)):
    return {"total_referrals": 0, "credits_earned": 0}
""")

w("src/interfaces/http/routes/admin.py", """
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from src.infrastructure.persistence.database import get_db
from src.infrastructure.persistence.models.orm_models import User, Organization
from src.interfaces.http.routes.auth import _get_current_user

router = APIRouter(prefix="/admin", tags=["admin"])

def _require_admin(user: User = Depends(_get_current_user)):
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
""")
w("src/interfaces/http/routes/upload.py", """
import io
import logging
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from src.infrastructure.persistence.database import get_db
from src.infrastructure.persistence.models.orm_models import User
from src.interfaces.http.routes.auth import _get_current_user

router = APIRouter(prefix="/upload", tags=["upload"])
log = logging.getLogger("routes.upload")

def extract_text_from_pdf(content: bytes) -> str:
    try:
        import PyPDF2
        reader = PyPDF2.PdfReader(io.BytesIO(content))
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\\n"
        return text[:50000]
    except Exception as e:
        log.error("PDF extraction failed: %s", e)
        return ""

def extract_text_from_txt(content: bytes) -> str:
    try:
        return content.decode("utf-8", errors="ignore")[:50000]
    except Exception:
        return ""

@router.post("/file")
async def upload_file(
    file: UploadFile = File(...),
    user: User = Depends(_get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not file.filename:
        raise HTTPException(400, "No file provided")
    
    max_size = 10 * 1024 * 1024  # 10MB
    content = await file.read()
    
    if len(content) > max_size:
        raise HTTPException(400, "File too large. Maximum size is 10MB")
    
    filename = file.filename.lower()
    extracted_text = ""
    file_type = "unknown"
    
    if filename.endswith(".pdf"):
        extracted_text = extract_text_from_pdf(content)
        file_type = "pdf"
    elif filename.endswith(".txt") or filename.endswith(".md"):
        extracted_text = extract_text_from_txt(content)
        file_type = "text"
    elif filename.endswith(".py") or filename.endswith(".js") or filename.endswith(".ts") or filename.endswith(".tsx") or filename.endswith(".jsx"):
        extracted_text = extract_text_from_txt(content)
        file_type = "code"
    elif filename.endswith(".csv"):
        extracted_text = extract_text_from_txt(content)
        file_type = "csv"
    else:
        raise HTTPException(400, "Unsupported file type. Supported: PDF, TXT, MD, CSV, code files")
    
    if not extracted_text.strip():
        raise HTTPException(400, "Could not extract text from file")
    
    word_count = len(extracted_text.split())
    
    return {
        "filename": file.filename,
        "file_type": file_type,
        "word_count": word_count,
        "extracted_text": extracted_text,
        "message": f"Successfully extracted {word_count} words from {file.filename}"
    }
""")
w("src/interfaces/http/routes/memory.py", """
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
""")

w("src/main.py", """
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import make_asgi_app
from src.shared.config.settings import settings

logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL, logging.INFO), format="%(asctime)s %(name)s %(levelname)s %(message)s")
log = logging.getLogger("app")

@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("Dacexy %s starting", settings.APP_VERSION)
    if settings.SENTRY_DSN:
        try:
            import sentry_sdk
            sentry_sdk.init(dsn=settings.SENTRY_DSN, environment=settings.ENVIRONMENT)
        except Exception:
            pass
    log.info("Startup complete")
    yield
    log.info("Shutdown complete")

app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION, docs_url="/docs", redoc_url="/redoc", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.add_middleware(GZipMiddleware, minimum_size=1000)

from src.interfaces.http.middleware.rate_limit import RateLimitMiddleware
app.add_middleware(RateLimitMiddleware)

if settings.PROMETHEUS_ENABLED:
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)

from src.interfaces.http.routes import auth, ai_chat, orgs, billing, agent, media, websites, voice, audit, referral, admin, memory, upload
app.include_router(auth.router, prefix=settings.API_PREFIX)
app.include_router(ai_chat.router, prefix=settings.API_PREFIX)
app.include_router(orgs.router, prefix=settings.API_PREFIX)
app.include_router(billing.router, prefix=settings.API_PREFIX)
app.include_router(agent.router, prefix=settings.API_PREFIX)
app.include_router(media.router, prefix=settings.API_PREFIX)
app.include_router(websites.router, prefix=settings.API_PREFIX)
app.include_router(voice.router, prefix=settings.API_PREFIX)
app.include_router(audit.router, prefix=settings.API_PREFIX)
app.include_router(referral.router, prefix=settings.API_PREFIX)
app.include_router(admin.router, prefix=settings.API_PREFIX)
app.include_router(memory.router, prefix=settings.API_PREFIX)
app.include_router(upload.router, prefix=settings.API_PREFIX)
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    log.error("Unhandled: %s %s %s", request.method, request.url.path, exc)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})

@app.get("/health")
async def health():
    return {"status": "ok", "version": settings.APP_VERSION, "environment": settings.ENVIRONMENT}

@app.get("/config")
async def config():
    return {"app_name": settings.APP_NAME, "version": settings.APP_VERSION, "features": {"ai_chat": bool(settings.DEEPSEEK_API_KEY), "media": bool(settings.BYTEZ_API_KEY), "payments": settings.payments_enabled}}

@app.get("/")
async def root():
    return {"message": "Welcome to " + settings.APP_NAME, "docs": "/docs", "health": "/health"}
""")

print("\n✅ ALL FILES CREATED SUCCESSFULLY!")
import os, sys, subprocess
port = os.environ.get('PORT', '8000')
print('Starting uvicorn on port:', port, flush=True)
proc = subprocess.Popen(
    [sys.executable, '-m', 'uvicorn', 'src.main:app', '--host', '0.0.0.0', '--port', port, '--log-level', 'info'],
    stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
)
for line in proc.stdout:
    print(line, end='', flush=True)
proc.wait()
sys.exit(proc.returncode)
