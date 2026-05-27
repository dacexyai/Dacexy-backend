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
    RAZORPAY_KEY_ID: str = ""
    RAZORPAY_KEY_SECRET: str = ""
    RAZORPAY_WEBHOOK_SECRET: str = ""
    VERCEL_TOKEN: str = ""
    VERCEL_TEAM_ID: str = ""
    WAVESPEED_API_KEY: str = ""
    PLATFORM_URL: str = "https://dacexy-backend-v7ku.onrender.com"
    APP_BASE_URL: str = "https://dacexy.vercel.app"
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
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
import urllib.parse
import re
import random

log = logging.getLogger("website")

# ── NAME EXTRACTION ──────────────────────────────────────────────────────────
def extract_name(prompt: str) -> str:
    p = prompt.strip()
    patterns = [
        r"(?:named?|called?|for)\s+([A-Z][a-zA-Z0-9\s]{1,30}?)(?:\s+(?:with|that|which|website|app|platform|startup|business|restaurant|store|shop|company)|\.|,|$)",
        r"^([A-Z][a-zA-Z0-9]{1,20})\s+",
    ]
    for pat in patterns:
        m = re.search(pat, p, re.IGNORECASE)
        if m:
            name = m.group(1).strip()
            if 2 <= len(name) <= 30 and name.lower() not in ["a","an","the","my","our","build","make","create","generate"]:
                return name.title()
    skip = {"for","the","with","that","this","and","build","make","create","generate",
            "website","page","site","app","landing","platform","startup","business",
            "a","an","my","our","me","i","want","need","please","just","can","you"}
    words = [w for w in re.sub(r'[^a-zA-Z0-9 ]', '', p).split()
             if len(w) > 2 and w.lower() not in skip]
    return words[0].title() if words else "Nexus"

# ── USER DATA EXTRACTION ─────────────────────────────────────────────────────
def extract_user_data(prompt: str) -> dict:
    data = {"phone": None, "email": None, "address": None,
            "whatsapp": None, "instagram": None, "facebook": None,
            "twitter": None, "linkedin": None, "youtube": None,
            "opening_hours": None, "tagline_custom": None, "about_text": None}
    p = prompt
    phone_match = re.search(r'(?:phone|mobile|call|contact|tel|ph)[:\s#]*([+\d][\d\s\-().+]{7,15})', p, re.IGNORECASE)
    if not phone_match:
        phone_match = re.search(r'(?<![\w])([+]?[0-9]{10,13})(?![\w])', p)
    if phone_match:
        data["phone"] = phone_match.group(1).strip()
        data["whatsapp"] = data["phone"]
    email_match = re.search(r'[\w.+-]+@[\w-]+\.[\w.]+', p)
    if email_match:
        data["email"] = email_match.group(0)
    addr_match = re.search(r'(?:address|location|located at|find us at|visit us at)[:\s]+([^,\n.]{10,100})', p, re.IGNORECASE)
    if addr_match:
        data["address"] = addr_match.group(1).strip()
    ig_match = re.search(r'(?:instagram|ig|insta)[:\s@/]*([\w.]+)', p, re.IGNORECASE)
    if ig_match:
        data["instagram"] = ig_match.group(1).strip()
    fb_match = re.search(r'(?:facebook|fb)[:\s@/]*([\w.]+)', p, re.IGNORECASE)
    if fb_match:
        data["facebook"] = fb_match.group(1).strip()
    tw_match = re.search(r'(?:twitter|x\.com)[:\s@/]*([\w.]+)', p, re.IGNORECASE)
    if tw_match:
        data["twitter"] = tw_match.group(1).strip()
    li_match = re.search(r'(?:linkedin)[:\s@/]*([\w.-]+)', p, re.IGNORECASE)
    if li_match:
        data["linkedin"] = li_match.group(1).strip()
    yt_match = re.search(r'(?:youtube|yt)[:\s@/]*([\w.-]+)', p, re.IGNORECASE)
    if yt_match:
        data["youtube"] = yt_match.group(1).strip()
    hours_match = re.search(r'(?:open|hours|timing)[:\s]+([^.\n]{5,60})', p, re.IGNORECASE)
    if hours_match:
        data["opening_hours"] = hours_match.group(1).strip()
    wa_match = re.search(r'(?:whatsapp)[:\s#]*([+\d][\d\s\-+]{7,15})', p, re.IGNORECASE)
    if wa_match:
        data["whatsapp"] = wa_match.group(1).strip()
    tagline_match = re.search(r'(?:tagline|slogan|headline)[:\s"]+([^"\n]{5,80})', p, re.IGNORECASE)
    if tagline_match:
        data["tagline_custom"] = tagline_match.group(1).strip()
    about_match = re.search(r'(?:about us|about|description)[:\s]+([^.\n]{20,300})', p, re.IGNORECASE)
    if about_match:
        data["about_text"] = about_match.group(1).strip()
    return data

# ── NEEDS AI — only for genuinely custom requests ────────────────────────────
def needs_ai_generation(prompt: str) -> bool:
    p = prompt.lower()
    ai_signals = [
        "custom","unique","special","specific","exactly like","similar to","inspired by",
        "different from","unusual","one of a kind","never seen","creative","artistic",
        "complex","advanced","multiple pages","dashboard","web app","tool","calculator",
        "interactive","animation heavy","3d","parallax heavy","video background",
        "ecommerce with cart","booking system","membership","login","payment",
        "database","dynamic","cms","blog with categories","search functionality",
        "filter","sort","api","integration","map with pins","chat","realtime",
    ]
    simple_signals = [
        "restaurant","cafe","gym","salon","doctor","lawyer","hotel","shop","store",
        "portfolio","agency","startup","school","hospital","ngo","travel","food",
        "photography","music","dental","cleaning","solar","car dealer","construction",
    ]
    has_ai = any(s in p for s in ai_signals)
    has_simple = any(s in p for s in simple_signals)
    if has_ai and not has_simple:
        return True
    if has_ai and len(p) > 200:
        return True
    return False

# ── CATEGORY DETECTION ───────────────────────────────────────────────────────
CATEGORY_KEYWORDS = {
    "restaurant":    ["restaurant","cafe","bistro","dhaba","tiffin","biryani","pizzeria","steakhouse","sushi","diner","eatery","food truck","catering","fine dining","cuisine","chef","reservations","table booking","takeaway"],
    "saas":          ["saas","software as a service","b2b software","crm","erp","api platform","devtool","productivity tool","project management","workflow automation","no-code","subscription software","cloud software","analytics platform","dashboard tool"],
    "car":           ["car dealer","automobile","vehicle dealer","showroom","cars for sale","used cars","new cars","auto dealer","car rental","test drive","dealership"],
    "portfolio":     ["portfolio","my work","my projects","personal website","freelancer","designer portfolio","developer portfolio","photographer portfolio","resume site","cv website","showcase work"],
    "ecommerce":     ["ecommerce","online store","online shop","products for sale","buy online","shopping cart","checkout","merchandise","dropship","retail online","fashion store","clothing store","jewelry store","electronics store"],
    "agency":        ["marketing agency","digital agency","creative agency","advertising agency","branding agency","seo agency","web agency","design studio","growth agency","media agency"],
    "fitness":       ["gym","fitness center","personal trainer","yoga studio","crossfit","pilates","health club","wellness center","martial arts","boxing gym","bodybuilding","workout studio"],
    "education":     ["school","college","university","online course","e-learning","edtech","tutoring","coaching center","training institute","certification course","bootcamp","learning platform"],
    "realestate":    ["real estate","property listing","homes for sale","apartments","flat","villa","plot","realtor","real estate agent","property dealer","rent property"],
    "hospital":      ["hospital","clinic","doctor","medical center","healthcare","dental clinic","dentist","pharmacy","health center","diagnostic","physiotherapy","telemedicine"],
    "hotel":         ["hotel","resort","motel","bed and breakfast","bnb","accommodation","lodging","rooms","suite","vacation rental","boutique hotel","hospitality"],
    "law":           ["law firm","lawyer","attorney","legal services","advocate","solicitor","corporate law","criminal defense","family law","legal aid","barrister"],
    "startup":       ["startup","mvp","seed stage","series a","venture","founder","product launch","early stage","tech startup","fintech startup","saas startup"],
    "finance":       ["finance","fintech","banking","investment","wealth management","mutual fund","insurance","accounting","tax","chartered accountant","financial advisor","stock trading"],
    "construction":  ["construction","builder","contractor","architect","interior design","renovation","remodeling","civil engineering","infrastructure","building company","landscaping"],
    "ngo":           ["ngo","nonprofit","charity","foundation","social cause","donation","volunteer","social impact","fundraising","advocacy","welfare"],
    "photography":   ["photography","photographer","photo studio","wedding photography","portrait photography","commercial photography","event photography","videography"],
    "music":         ["music","band","musician","singer","dj","music studio","record label","music producer","concert","album","music lessons","music school"],
    "salon":         ["salon","beauty parlor","hair salon","barbershop","spa","nail salon","makeup artist","beauty studio","hair stylist","grooming"],
    "travel":        ["travel agency","tour operator","tours","vacation packages","holiday packages","adventure travel","safari","cruise","backpacking"],
    "food_delivery": ["food delivery","cloud kitchen","ghost kitchen","meal prep","meal delivery","tiffin service","home chef","online food","meal kit"],
    "tech_company":  ["tech company","software company","it company","technology company","it services","software development","app development","web development company","cybersecurity"],
    "event":         ["event management","event planner","wedding planner","corporate events","conference","event venue","party planner","event decorator"],
    "consulting":    ["consulting","management consulting","business consulting","strategy consulting","hr consulting","operations consulting","advisory services"],
    "fashion":       ["fashion","clothing brand","fashion designer","apparel brand","streetwear","luxury fashion","sustainable fashion","fashion label","couture"],
    "interior":      ["interior design","interior designer","home decor","furniture","home furnishing","space planning","interior styling"],
    "bakery":        ["bakery","cake shop","pastry","dessert shop","confectionery","wedding cake","custom cake","sourdough","cookie shop","donut shop","macaron"],
    "coffee":        ["coffee shop","specialty coffee","coffee bar","espresso bar","coffee subscription","coffee brand","tea house","third wave coffee"],
    "yoga":          ["yoga","meditation","mindfulness","wellness retreat","yoga teacher","breathwork","sound healing","spiritual wellness","holistic health"],
    "pet":           ["pet shop","pet clinic","veterinary","pet grooming","pet boarding","dog trainer","pet care","animal shelter","veterinarian"],
    "gaming":        ["gaming","esports","game studio","game developer","gaming cafe","mobile game","gaming community","game coaching"],
    "crypto":        ["crypto","blockchain","web3","nft","defi","cryptocurrency","token","dao","metaverse","digital assets","crypto exchange"],
    "wedding":       ["wedding planner","bridal","wedding venue","wedding photography","wedding catering","wedding dress","bridal boutique","wedding decor"],
    "children":      ["children","kids","daycare","kindergarten","preschool","child care","baby products","kids clothing","children entertainment","toy store"],
    "dental":        ["dental","dentist","dental clinic","oral health","teeth whitening","braces","orthodontist","dental implants","root canal"],
    "cleaning":      ["cleaning service","house cleaning","commercial cleaning","janitorial","maid service","deep cleaning","carpet cleaning","sanitization"],
    "solar":         ["solar","solar energy","solar panel","renewable energy","green energy","solar installation","wind energy","clean energy"],
    "automobile_service": ["car service","auto repair","car workshop","mechanic","car wash","auto detailing","tire shop","auto parts","battery service"],
    "logistics":     ["logistics","courier","shipping","freight","supply chain","warehouse","last mile delivery","trucking","cargo","fulfillment"],
    "agriculture":   ["agriculture","farm","farming","organic farm","agritech","crop","fertilizer","seeds","dairy farm","poultry","greenhouse"],
    "security":      ["security agency","cctv","surveillance","guard service","cybersecurity","private security","access control","fire safety","alarm system"],
    "mental_health": ["mental health","therapist","psychologist","counseling","therapy","anxiety","depression","psychiatrist","emotional wellness"],
    "pharmacy":      ["pharmacy","medical store","chemist","drug store","online pharmacy","medicine delivery","health products","supplements"],
    "accounting":    ["accounting","bookkeeping","ca firm","tax filing","gst","audit","payroll","financial reporting","tax consultant"],
    "printing":      ["printing","print shop","graphic design","branding","logo design","stationery","packaging design","banner printing","signage"],
    "florist":       ["florist","flower shop","flower delivery","floral design","wedding flowers","bouquet","floral arrangement","plant nursery"],
    "catering":      ["catering","caterer","food catering","wedding catering","corporate catering","event catering","buffet","canteen"],
    "dance":         ["dance academy","dance studio","dance school","ballet","hip hop dance","classical dance","dance teacher","dance classes"],
    "language":      ["language school","english classes","foreign language","translation","interpretation","language learning","spoken english","ielts"],
    "coaching":      ["life coach","business coach","executive coach","career coach","mindset coach","leadership coaching","coaching program"],
    "insurance":     ["insurance","life insurance","health insurance","car insurance","home insurance","insurance broker","insurance agent"],
    "sports":        ["sports","sports club","sports academy","cricket","football","basketball","tennis","swimming","athletics","sports equipment"],
    "media":         ["media production","film production","video production","documentary","short film","music video","animation studio","vfx studio"],
    "astrology":     ["astrology","horoscope","numerology","tarot","vastu","palmistry","vedic astrology","psychic reading","spiritual guidance"],
    "jewelry":       ["jewelry","jeweler","gold jewelry","diamond jewelry","custom jewelry","engagement ring","wedding jewelry","silver jewelry"],
    "furniture":     ["furniture","furniture store","custom furniture","wood furniture","modular furniture","office furniture","sofa","wardrobe"],
    "electronics":   ["electronics store","gadgets","mobile phone shop","laptop store","electronics repair","consumer electronics","home appliances"],
    "swimming":      ["swimming pool","swim school","swimming academy","swim coach","aqua fitness","swimming lessons"],
    "laundry":       ["laundry","dry cleaning","laundry service","wash and fold","ironing service","garment care","laundromat"],
    "plumber":       ["plumber","plumbing","plumbing services","pipe fitting","bathroom fitting","water tank","drainage","sanitation"],
    "electrician":   ["electrician","electrical services","wiring","electrical contractor","power backup","generator","home automation"],
    "tutor":         ["tutor","tutoring","home tuition","online tutor","math tutor","science tutor","test prep","jee","neet","upsc"],
    "dietitian":     ["dietitian","nutritionist","diet plan","weight loss","nutrition counseling","meal planning","sports nutrition","diabetic diet"],
    "car_rental":    ["car rental","self drive","vehicle rental","cab service","taxi","chauffeur","limousine","bus rental","outstation cab"],
    "bike":          ["bike shop","bicycle store","cycling","mountain bike","electric bike","bike rental","cycling academy","bike accessories"],
    "optical":       ["optical store","spectacle shop","sunglasses","contact lens","eyeglass frame","prescription glasses","optometry"],
    "coworking":     ["coworking","shared workspace","hot desk","serviced office","business center","virtual office","meeting room"],
    "tattoo":        ["tattoo studio","tattoo artist","body piercing","tattoo parlor","custom tattoo","henna","body art"],
    "escape":        ["escape room","puzzle room","team building","entertainment center","gaming lounge","board game cafe","vr arcade"],
    "amusement":     ["amusement park","theme park","water park","adventure park","rides","roller coaster","family park"],
    "nightclub":     ["nightclub","bar","lounge","pub","rooftop bar","cocktail bar","sports bar","live music venue","jazz club"],
    "museum":        ["museum","heritage site","cultural center","exhibition hall","science museum","history museum","virtual museum"],
    "church":        ["church","temple","mosque","gurdwara","religious organization","faith community","ministry","spiritual center"],
    "book":          ["bookstore","library","book club","publishing","author website","book review","literary","writing coaching","poetry"],
    "podcast":       ["podcast","podcaster","podcast studio","podcast network","audio content","podcast hosting","radio show"],
    "influencer":    ["influencer","content creator","youtuber","instagrammer","social media","personal brand","creator economy"],
    "senior":        ["senior care","elderly care","retirement home","assisted living","nursing home","senior services","elder care"],
    "mortgage":      ["mortgage","home loan","property loan","loan broker","loan advisor","refinancing","home financing"],
    "architecture":  ["architect","architecture firm","architectural design","urban planning","landscape architecture","structural engineering"],
    "charity":       ["charity","donation","fundraising","social service","community service","homeless shelter","food bank","orphanage"],
    "golf":          ["golf club","golf course","golf academy","golf lessons","golf equipment","mini golf","golf resort"],
    "recruitment":   ["recruitment","job portal","career","employment","job board","talent platform","hiring platform","job search"],
    "textile":       ["textile","fabric","garment factory","clothing manufacturer","weaving","embroidery","knitting","textile mill"],
    "pharma":        ["pharmaceutical","pharma company","drug manufacturer","medicine","clinical research","biotech","life sciences"],
    "shipping_co":   ["shipping company","maritime","port","vessel","cargo ship","container shipping","freight forwarding","customs"],
    "business":      ["company","business","service","professional","firm","enterprise","solutions","services","management"],
}

def get_category(prompt: str) -> str:
    p = prompt.lower()
    noise = ["make","build","create","generate","design","need","want","please","just",
             "website","site","page","landing","web app","online presence","for","me",
             "a","an","the","i","can","you","give","type","good","great","best",
             "professional","beautiful","modern","awesome","nice","add","include",
             "put","use","have","their","its","with","mobile","number","phone",
             "email","address","contact","social","media","map","gallery","images",
             "photos","logo","color","colour","theme","dark","light"]
    clean = p
    for n in noise:
        clean = re.sub(r"\b" + re.escape(n) + r"\b", " ", clean)
    clean = clean.strip()
    scores = {}
    for cat, keywords in CATEGORY_KEYWORDS.items():
        score = 0
        for kw in keywords:
            if kw in clean:
                score += len(kw.split()) * 3
            elif any(word in clean for word in kw.split() if len(word) > 5):
                score += 1
        scores[cat] = score
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "business"

# ── 100 DESIGN SYSTEMS ───────────────────────────────────────────────────────
ALL_DESIGNS = [
    {"dark":True,"bg":"#0A0A0A","pr":"#E11D48","ac":"#F59E0B","tx":"#FFFFFF","mu":"rgba(255,255,255,0.58)","ca":"rgba(255,255,255,0.05)","br":"rgba(225,29,72,0.28)","nb":"rgba(10,10,10,0.96)","nt":"rgba(255,255,255,0.82)","f1":"Playfair Display","f2":"Inter"},
    {"dark":True,"bg":"#050010","pr":"#8B5CF6","ac":"#06B6D4","tx":"#F5F3FF","mu":"rgba(245,243,255,0.58)","ca":"rgba(139,92,246,0.09)","br":"rgba(139,92,246,0.22)","nb":"rgba(5,0,16,0.96)","nt":"rgba(245,243,255,0.82)","f1":"Inter","f2":"Inter"},
    {"dark":True,"bg":"#0D0500","pr":"#C8102E","ac":"#FFD700","tx":"#FFF8F0","mu":"rgba(255,248,240,0.58)","ca":"rgba(255,255,255,0.04)","br":"rgba(255,215,0,0.18)","nb":"rgba(13,5,0,0.96)","nt":"rgba(255,248,240,0.82)","f1":"Playfair Display","f2":"Inter"},
    {"dark":True,"bg":"#0C0500","pr":"#EA580C","ac":"#22C55E","tx":"#FFF7ED","mu":"rgba(255,247,237,0.58)","ca":"rgba(234,88,12,0.09)","br":"rgba(234,88,12,0.22)","nb":"rgba(12,5,0,0.96)","nt":"rgba(255,247,237,0.82)","f1":"Inter","f2":"Inter"},
    {"dark":True,"bg":"#060A14","pr":"#3B82F6","ac":"#10B981","tx":"#EFF6FF","mu":"rgba(239,246,255,0.58)","ca":"rgba(59,130,246,0.09)","br":"rgba(59,130,246,0.22)","nb":"rgba(6,10,20,0.96)","nt":"rgba(239,246,255,0.82)","f1":"Inter","f2":"Inter"},
    {"dark":True,"bg":"#0A0800","pr":"#B45309","ac":"#FCD34D","tx":"#FFFBEB","mu":"rgba(255,251,235,0.58)","ca":"rgba(180,83,9,0.09)","br":"rgba(252,211,77,0.18)","nb":"rgba(10,8,0,0.96)","nt":"rgba(255,251,235,0.82)","f1":"Playfair Display","f2":"Inter"},
    {"dark":True,"bg":"#030712","pr":"#06B6D4","ac":"#8B5CF6","tx":"#F0FDFE","mu":"rgba(240,253,254,0.58)","ca":"rgba(6,182,212,0.09)","br":"rgba(6,182,212,0.22)","nb":"rgba(3,7,18,0.96)","nt":"rgba(240,253,254,0.82)","f1":"Inter","f2":"Inter"},
    {"dark":True,"bg":"#0A0A1A","pr":"#F43F5E","ac":"#A78BFA","tx":"#FFF1F2","mu":"rgba(255,241,242,0.58)","ca":"rgba(244,63,94,0.09)","br":"rgba(244,63,94,0.22)","nb":"rgba(10,10,26,0.96)","nt":"rgba(255,241,242,0.82)","f1":"Inter","f2":"Inter"},
    {"dark":True,"bg":"#071A0E","pr":"#16A34A","ac":"#FCD34D","tx":"#F0FDF4","mu":"rgba(240,253,244,0.58)","ca":"rgba(22,163,74,0.09)","br":"rgba(22,163,74,0.22)","nb":"rgba(7,26,14,0.96)","nt":"rgba(240,253,244,0.82)","f1":"Inter","f2":"Inter"},
    {"dark":True,"bg":"#14000A","pr":"#DB2777","ac":"#FB923C","tx":"#FDF2F8","mu":"rgba(253,242,248,0.58)","ca":"rgba(219,39,119,0.09)","br":"rgba(219,39,119,0.22)","nb":"rgba(20,0,10,0.96)","nt":"rgba(253,242,248,0.82)","f1":"Playfair Display","f2":"Inter"},
    {"dark":False,"bg":"#FFFFFF","pr":"#6366F1","ac":"#06B6D4","tx":"#0F0F1A","mu":"#6B7280","ca":"#F8F7FF","br":"#E5E7EB","nb":"rgba(255,255,255,0.97)","nt":"#374151","f1":"Inter","f2":"Inter"},
    {"dark":False,"bg":"#FFFBF0","pr":"#D97706","ac":"#EF4444","tx":"#1C1917","mu":"#78716C","ca":"#FEF3C7","br":"#FDE68A","nb":"rgba(255,251,240,0.97)","nt":"#44403C","f1":"Playfair Display","f2":"Inter"},
    {"dark":False,"bg":"#F0FDF4","pr":"#059669","ac":"#F97316","tx":"#022C22","mu":"#6B7280","ca":"#DCFCE7","br":"#A7F3D0","nb":"rgba(240,253,244,0.97)","nt":"#065F46","f1":"Inter","f2":"Inter"},
    {"dark":False,"bg":"#FFF5F5","pr":"#DC2626","ac":"#F59E0B","tx":"#1A0000","mu":"#6B7280","ca":"#FEE2E2","br":"#FECACA","nb":"rgba(255,245,245,0.97)","nt":"#7F1D1D","f1":"Playfair Display","f2":"Inter"},
    {"dark":False,"bg":"#FAF5FF","pr":"#7C3AED","ac":"#F59E0B","tx":"#1A0A3E","mu":"#6B7280","ca":"#EDE9FE","br":"#DDD6FE","nb":"rgba(250,245,255,0.97)","nt":"#4C1D95","f1":"Playfair Display","f2":"Inter"},
    {"dark":False,"bg":"#EFF6FF","pr":"#2563EB","ac":"#F59E0B","tx":"#020617","mu":"#6B7280","ca":"#DBEAFE","br":"#BFDBFE","nb":"rgba(239,246,255,0.97)","nt":"#1E3A8A","f1":"Inter","f2":"Inter"},
    {"dark":False,"bg":"#FFF7ED","pr":"#EA580C","ac":"#22C55E","tx":"#1C0A00","mu":"#6B7280","ca":"#FFEDD5","br":"#FED7AA","nb":"rgba(255,247,237,0.97)","nt":"#7C2D12","f1":"Inter","f2":"Inter"},
    {"dark":False,"bg":"#F0FFFE","pr":"#0891B2","ac":"#10B981","tx":"#042F2E","mu":"#6B7280","ca":"#CCFBF1","br":"#99F6E4","nb":"rgba(240,255,254,0.97)","nt":"#134E4A","f1":"Inter","f2":"Inter"},
    {"dark":False,"bg":"#FAFAF8","pr":"#0F0F0F","ac":"#F59E0B","tx":"#0F0F0F","mu":"#6B7280","ca":"#F5F5F0","br":"#E0E0D8","nb":"rgba(250,250,248,0.97)","nt":"#0F0F0F","f1":"Playfair Display","f2":"Inter"},
    {"dark":False,"bg":"#FDF4FF","pr":"#A21CAF","ac":"#F59E0B","tx":"#2E1065","mu":"#6B7280","ca":"#FAE8FF","br":"#F0ABFC","nb":"rgba(253,244,255,0.97)","nt":"#6B21A8","f1":"Playfair Display","f2":"Inter"},
    {"dark":True,"bg":"#0F0F23","pr":"#F97316","ac":"#FACC15","tx":"#FFFBEB","mu":"rgba(255,251,235,0.58)","ca":"rgba(249,115,22,0.09)","br":"rgba(249,115,22,0.22)","nb":"rgba(15,15,35,0.96)","nt":"rgba(255,251,235,0.82)","f1":"Inter","f2":"Inter"},
    {"dark":True,"bg":"#0A1628","pr":"#0EA5E9","ac":"#38BDF8","tx":"#F0F9FF","mu":"rgba(240,249,255,0.58)","ca":"rgba(14,165,233,0.09)","br":"rgba(14,165,233,0.22)","nb":"rgba(10,22,40,0.96)","nt":"rgba(240,249,255,0.82)","f1":"Inter","f2":"Inter"},
    {"dark":False,"bg":"#FEFCE8","pr":"#CA8A04","ac":"#DC2626","tx":"#1C1400","mu":"#78716C","ca":"#FEF9C3","br":"#FEF08A","nb":"rgba(254,252,232,0.97)","nt":"#92400E","f1":"Playfair Display","f2":"Inter"},
    {"dark":False,"bg":"#F8FAFC","pr":"#334155","ac":"#3B82F6","tx":"#0F172A","mu":"#64748B","ca":"#F1F5F9","br":"#CBD5E1","nb":"rgba(248,250,252,0.97)","nt":"#1E293B","f1":"Inter","f2":"Inter"},
    {"dark":True,"bg":"#0D1117","pr":"#58A6FF","ac":"#3FB950","tx":"#C9D1D9","mu":"rgba(201,209,217,0.58)","ca":"rgba(88,166,255,0.09)","br":"rgba(88,166,255,0.16)","nb":"rgba(13,17,23,0.96)","nt":"rgba(201,209,217,0.82)","f1":"Inter","f2":"Inter"},
    {"dark":False,"bg":"#FFF1F2","pr":"#E11D48","ac":"#F59E0B","tx":"#881337","mu":"#6B7280","ca":"#FFE4E6","br":"#FECDD3","nb":"rgba(255,241,242,0.97)","nt":"#9F1239","f1":"Playfair Display","f2":"Inter"},
    {"dark":True,"bg":"#1A0533","pr":"#C084FC","ac":"#F472B6","tx":"#FAF5FF","mu":"rgba(250,245,255,0.58)","ca":"rgba(192,132,252,0.09)","br":"rgba(192,132,252,0.22)","nb":"rgba(26,5,51,0.96)","nt":"rgba(250,245,255,0.82)","f1":"Playfair Display","f2":"Inter"},
    {"dark":False,"bg":"#ECFDF5","pr":"#10B981","ac":"#3B82F6","tx":"#022C22","mu":"#6B7280","ca":"#D1FAE5","br":"#6EE7B7","nb":"rgba(236,253,245,0.97)","nt":"#065F46","f1":"Inter","f2":"Inter"},
    {"dark":True,"bg":"#18181B","pr":"#FACC15","ac":"#A78BFA","tx":"#FAFAFA","mu":"rgba(250,250,250,0.52)","ca":"rgba(255,255,255,0.05)","br":"rgba(255,255,255,0.11)","nb":"rgba(24,24,27,0.97)","nt":"rgba(250,250,250,0.82)","f1":"Inter","f2":"Inter"},
    {"dark":False,"bg":"#FEF9EE","pr":"#B45309","ac":"#059669","tx":"#1C1200","mu":"#78716C","ca":"#FEF3C7","br":"#FDE68A","nb":"rgba(254,249,238,0.97)","nt":"#78350F","f1":"Playfair Display","f2":"Inter"},
    {"dark":True,"bg":"#020617","pr":"#6366F1","ac":"#A5F3FC","tx":"#E0F2FE","mu":"rgba(224,242,254,0.58)","ca":"rgba(99,102,241,0.09)","br":"rgba(99,102,241,0.22)","nb":"rgba(2,6,23,0.97)","nt":"rgba(224,242,254,0.82)","f1":"Inter","f2":"Inter"},
    {"dark":False,"bg":"#F5F3FF","pr":"#4F46E5","ac":"#EC4899","tx":"#1E1B4B","mu":"#6B7280","ca":"#EDE9FE","br":"#C4B5FD","nb":"rgba(245,243,255,0.97)","nt":"#3730A3","f1":"Inter","f2":"Inter"},
    {"dark":True,"bg":"#0C1A0C","pr":"#22C55E","ac":"#FACC15","tx":"#F0FDF4","mu":"rgba(240,253,244,0.58)","ca":"rgba(34,197,94,0.09)","br":"rgba(34,197,94,0.16)","nb":"rgba(12,26,12,0.97)","nt":"rgba(240,253,244,0.82)","f1":"Inter","f2":"Inter"},
    {"dark":False,"bg":"#FFF8F0","pr":"#C2410C","ac":"#FBBF24","tx":"#431407","mu":"#78716C","ca":"#FEE2D5","br":"#FCA27B","nb":"rgba(255,248,240,0.97)","nt":"#7C2D12","f1":"Playfair Display","f2":"Inter"},
    {"dark":True,"bg":"#08080F","pr":"#E879F9","ac":"#22D3EE","tx":"#FAF5FF","mu":"rgba(250,245,255,0.58)","ca":"rgba(232,121,249,0.07)","br":"rgba(232,121,249,0.18)","nb":"rgba(8,8,15,0.97)","nt":"rgba(250,245,255,0.82)","f1":"Inter","f2":"Inter"},
    {"dark":False,"bg":"#F8F9FA","pr":"#212529","ac":"#E63946","tx":"#212529","mu":"#6C757D","ca":"#E9ECEF","br":"#CED4DA","nb":"rgba(248,249,250,0.97)","nt":"#495057","f1":"Inter","f2":"Inter"},
    {"dark":True,"bg":"#0A0A0A","pr":"#FFFFFF","ac":"#F59E0B","tx":"#FFFFFF","mu":"rgba(255,255,255,0.5)","ca":"rgba(255,255,255,0.05)","br":"rgba(255,255,255,0.12)","nb":"rgba(10,10,10,0.97)","nt":"rgba(255,255,255,0.82)","f1":"Playfair Display","f2":"Inter"},
    {"dark":False,"bg":"#FFF0F3","pr":"#FF4D6D","ac":"#FF9F1C","tx":"#590D22","mu":"#6B7280","ca":"#FFD6E0","br":"#FFAFC5","nb":"rgba(255,240,243,0.97)","nt":"#A4133C","f1":"Playfair Display","f2":"Inter"},
    {"dark":True,"bg":"#061014","pr":"#34D399","ac":"#60A5FA","tx":"#ECFDF5","mu":"rgba(236,253,245,0.58)","ca":"rgba(52,211,153,0.09)","br":"rgba(52,211,153,0.16)","nb":"rgba(6,16,20,0.97)","nt":"rgba(236,253,245,0.82)","f1":"Inter","f2":"Inter"},
    {"dark":False,"bg":"#FFFAF0","pr":"#F97316","ac":"#14B8A6","tx":"#1C0A00","mu":"#78716C","ca":"#FFF1E0","br":"#FED7AA","nb":"rgba(255,250,240,0.97)","nt":"#7C2D12","f1":"Playfair Display","f2":"Inter"},
    {"dark":True,"bg":"#140028","pr":"#A855F7","ac":"#EC4899","tx":"#FAF5FF","mu":"rgba(250,245,255,0.58)","ca":"rgba(168,85,247,0.09)","br":"rgba(168,85,247,0.22)","nb":"rgba(20,0,40,0.97)","nt":"rgba(250,245,255,0.82)","f1":"Playfair Display","f2":"Inter"},
    {"dark":False,"bg":"#F0F9FF","pr":"#0284C7","ac":"#F59E0B","tx":"#0C4A6E","mu":"#6B7280","ca":"#E0F2FE","br":"#BAE6FD","nb":"rgba(240,249,255,0.97)","nt":"#075985","f1":"Inter","f2":"Inter"},
    {"dark":True,"bg":"#0F1923","pr":"#FB923C","ac":"#34D399","tx":"#FFF7ED","mu":"rgba(255,247,237,0.58)","ca":"rgba(251,146,60,0.09)","br":"rgba(251,146,60,0.22)","nb":"rgba(15,25,35,0.97)","nt":"rgba(255,247,237,0.82)","f1":"Inter","f2":"Inter"},
    {"dark":False,"bg":"#F9FAFB","pr":"#111827","ac":"#6366F1","tx":"#111827","mu":"#6B7280","ca":"#F3F4F6","br":"#D1D5DB","nb":"rgba(249,250,251,0.97)","nt":"#374151","f1":"Inter","f2":"Inter"},
    {"dark":True,"bg":"#180A00","pr":"#F97316","ac":"#FCD34D","tx":"#FFF7ED","mu":"rgba(255,247,237,0.58)","ca":"rgba(249,115,22,0.09)","br":"rgba(252,211,77,0.2)","nb":"rgba(24,10,0,0.97)","nt":"rgba(255,247,237,0.82)","f1":"Playfair Display","f2":"Inter"},
    {"dark":False,"bg":"#FAFFFE","pr":"#0D9488","ac":"#F59E0B","tx":"#042F2E","mu":"#6B7280","ca":"#CCFBF1","br":"#99F6E4","nb":"rgba(250,255,254,0.97)","nt":"#0F766E","f1":"Inter","f2":"Inter"},
    {"dark":True,"bg":"#09090B","pr":"#D97706","ac":"#A78BFA","tx":"#FFFBEB","mu":"rgba(255,251,235,0.58)","ca":"rgba(217,119,6,0.09)","br":"rgba(217,119,6,0.22)","nb":"rgba(9,9,11,0.97)","nt":"rgba(255,251,235,0.82)","f1":"Playfair Display","f2":"Inter"},
    {"dark":False,"bg":"#FFF9FB","pr":"#BE185D","ac":"#7C3AED","tx":"#4A0020","mu":"#6B7280","ca":"#FCE7F3","br":"#FBCFE8","nb":"rgba(255,249,251,0.97)","nt":"#9D174D","f1":"Playfair Display","f2":"Inter"},
    {"dark":True,"bg":"#001A10","pr":"#00E676","ac":"#FFD600","tx":"#E8F5E9","mu":"rgba(232,245,233,0.58)","ca":"rgba(0,230,118,0.09)","br":"rgba(0,230,118,0.22)","nb":"rgba(0,26,16,0.97)","nt":"rgba(232,245,233,0.82)","f1":"Inter","f2":"Inter"},
    {"dark":False,"bg":"#F0F4FF","pr":"#1746A2","ac":"#FF6B6B","tx":"#0a1628","mu":"#6B7280","ca":"#DBE4FF","br":"#BAC8FF","nb":"rgba(240,244,255,0.97)","nt":"#1746A2","f1":"Inter","f2":"Inter"},
    {"dark":True,"bg":"#0A0000","pr":"#DC2626","ac":"#FBBF24","tx":"#FFF5F5","mu":"rgba(255,245,245,0.58)","ca":"rgba(220,38,38,0.09)","br":"rgba(220,38,38,0.22)","nb":"rgba(10,0,0,0.97)","nt":"rgba(255,245,245,0.82)","f1":"Playfair Display","f2":"Inter"},
    {"dark":True,"bg":"#050A14","pr":"#2563EB","ac":"#F59E0B","tx":"#EFF6FF","mu":"rgba(239,246,255,0.58)","ca":"rgba(37,99,235,0.09)","br":"rgba(37,99,235,0.22)","nb":"rgba(5,10,20,0.97)","nt":"rgba(239,246,255,0.82)","f1":"Inter","f2":"Inter"},
    {"dark":False,"bg":"#FFF8F8","pr":"#E11D48","ac":"#3B82F6","tx":"#0A0000","mu":"#6B7280","ca":"#FFE4E6","br":"#FECDD3","nb":"rgba(255,248,248,0.97)","nt":"#881337","f1":"Playfair Display","f2":"Inter"},
    {"dark":True,"bg":"#080E12","pr":"#0891B2","ac":"#22C55E","tx":"#F0FDFE","mu":"rgba(240,253,254,0.58)","ca":"rgba(8,145,178,0.09)","br":"rgba(8,145,178,0.22)","nb":"rgba(8,14,18,0.97)","nt":"rgba(240,253,254,0.82)","f1":"Inter","f2":"Inter"},
    {"dark":False,"bg":"#F7FFF7","pr":"#16A34A","ac":"#F97316","tx":"#052E16","mu":"#6B7280","ca":"#DCFCE7","br":"#86EFAC","nb":"rgba(247,255,247,0.97)","nt":"#14532D","f1":"Inter","f2":"Inter"},
    {"dark":True,"bg":"#0F0A1E","pr":"#7C3AED","ac":"#EC4899","tx":"#FAF5FF","mu":"rgba(250,245,255,0.58)","ca":"rgba(124,58,237,0.09)","br":"rgba(124,58,237,0.22)","nb":"rgba(15,10,30,0.97)","nt":"rgba(250,245,255,0.82)","f1":"Playfair Display","f2":"Inter"},
    {"dark":False,"bg":"#FFFBEB","pr":"#92400E","ac":"#059669","tx":"#1C1200","mu":"#78716C","ca":"#FEF3C7","br":"#FDE68A","nb":"rgba(255,251,235,0.97)","nt":"#78350F","f1":"Playfair Display","f2":"Inter"},
    {"dark":True,"bg":"#060616","pr":"#A855F7","ac":"#22D3EE","tx":"#F5F3FF","mu":"rgba(245,243,255,0.58)","ca":"rgba(168,85,247,0.09)","br":"rgba(168,85,247,0.22)","nb":"rgba(6,6,22,0.97)","nt":"rgba(245,243,255,0.82)","f1":"Inter","f2":"Inter"},
    {"dark":False,"bg":"#F8F5FF","pr":"#6D28D9","ac":"#F59E0B","tx":"#1E1B4B","mu":"#6B7280","ca":"#EDE9FE","br":"#C4B5FD","nb":"rgba(248,245,255,0.97)","nt":"#4C1D95","f1":"Playfair Display","f2":"Inter"},
    {"dark":True,"bg":"#0A1A0A","pr":"#84CC16","ac":"#F59E0B","tx":"#ECFDF5","mu":"rgba(236,253,245,0.58)","ca":"rgba(132,204,22,0.09)","br":"rgba(132,204,22,0.22)","nb":"rgba(10,26,10,0.97)","nt":"rgba(236,253,245,0.82)","f1":"Inter","f2":"Inter"},
    {"dark":False,"bg":"#FFF4E6","pr":"#EA580C","ac":"#7C3AED","tx":"#431407","mu":"#78716C","ca":"#FFEDD5","br":"#FED7AA","nb":"rgba(255,244,230,0.97)","nt":"#7C2D12","f1":"Playfair Display","f2":"Inter"},
    {"dark":True,"bg":"#0A1628","pr":"#38BDF8","ac":"#F472B6","tx":"#F0F9FF","mu":"rgba(240,249,255,0.58)","ca":"rgba(56,189,248,0.09)","br":"rgba(56,189,248,0.22)","nb":"rgba(10,22,40,0.97)","nt":"rgba(240,249,255,0.82)","f1":"Inter","f2":"Inter"},
    {"dark":False,"bg":"#F9FAF9","pr":"#065F46","ac":"#F59E0B","tx":"#022C22","mu":"#6B7280","ca":"#D1FAE5","br":"#A7F3D0","nb":"rgba(249,250,249,0.97)","nt":"#064E3B","f1":"Playfair Display","f2":"Inter"},
    {"dark":True,"bg":"#10051A","pr":"#D946EF","ac":"#FACC15","tx":"#FDF4FF","mu":"rgba(253,244,255,0.58)","ca":"rgba(217,70,239,0.09)","br":"rgba(217,70,239,0.22)","nb":"rgba(16,5,26,0.97)","nt":"rgba(253,244,255,0.82)","f1":"Playfair Display","f2":"Inter"},
    {"dark":False,"bg":"#F0FFF4","pr":"#15803D","ac":"#EF4444","tx":"#052E16","mu":"#6B7280","ca":"#DCFCE7","br":"#86EFAC","nb":"rgba(240,255,244,0.97)","nt":"#14532D","f1":"Inter","f2":"Inter"},
    {"dark":True,"bg":"#0A0A14","pr":"#6366F1","ac":"#34D399","tx":"#EEF2FF","mu":"rgba(238,242,255,0.58)","ca":"rgba(99,102,241,0.09)","br":"rgba(99,102,241,0.22)","nb":"rgba(10,10,20,0.97)","nt":"rgba(238,242,255,0.82)","f1":"Inter","f2":"Inter"},
    {"dark":False,"bg":"#FEFEF0","pr":"#4D7C0F","ac":"#B45309","tx":"#1A2E05","mu":"#78716C","ca":"#ECFCCB","br":"#D9F99D","nb":"rgba(254,254,240,0.97)","nt":"#365314","f1":"Playfair Display","f2":"Inter"},
    {"dark":True,"bg":"#050A0A","pr":"#14B8A6","ac":"#F97316","tx":"#F0FDFA","mu":"rgba(240,253,250,0.58)","ca":"rgba(20,184,166,0.09)","br":"rgba(20,184,166,0.22)","nb":"rgba(5,10,10,0.97)","nt":"rgba(240,253,250,0.82)","f1":"Inter","f2":"Inter"},
    {"dark":False,"bg":"#FFF0E0","pr":"#C2410C","ac":"#1D4ED8","tx":"#431407","mu":"#78716C","ca":"#FED7AA","br":"#FCA27B","nb":"rgba(255,240,224,0.97)","nt":"#7C2D12","f1":"Playfair Display","f2":"Inter"},
    {"dark":True,"bg":"#0C0A1E","pr":"#818CF8","ac":"#34D399","tx":"#EEF2FF","mu":"rgba(238,242,255,0.58)","ca":"rgba(129,140,248,0.09)","br":"rgba(129,140,248,0.22)","nb":"rgba(12,10,30,0.97)","nt":"rgba(238,242,255,0.82)","f1":"Inter","f2":"Inter"},
    {"dark":False,"bg":"#FDFCFB","pr":"#92400E","ac":"#1D4ED8","tx":"#1C0A00","mu":"#78716C","ca":"#FEF3C7","br":"#FDE68A","nb":"rgba(253,252,251,0.97)","nt":"#78350F","f1":"Playfair Display","f2":"Inter"},
    {"dark":True,"bg":"#080814","pr":"#EC4899","ac":"#06B6D4","tx":"#FDF2F8","mu":"rgba(253,242,248,0.58)","ca":"rgba(236,72,153,0.09)","br":"rgba(236,72,153,0.22)","nb":"rgba(8,8,20,0.97)","nt":"rgba(253,242,248,0.82)","f1":"Playfair Display","f2":"Inter"},
    {"dark":False,"bg":"#F8FAFF","pr":"#1D4ED8","ac":"#10B981","tx":"#0F172A","mu":"#6B7280","ca":"#DBEAFE","br":"#BFDBFE","nb":"rgba(248,250,255,0.97)","nt":"#1E3A8A","f1":"Inter","f2":"Inter"},
    {"dark":True,"bg":"#0A0804","pr":"#F59E0B","ac":"#10B981","tx":"#FFFBEB","mu":"rgba(255,251,235,0.58)","ca":"rgba(245,158,11,0.09)","br":"rgba(245,158,11,0.22)","nb":"rgba(10,8,4,0.97)","nt":"rgba(255,251,235,0.82)","f1":"Playfair Display","f2":"Inter"},
    {"dark":False,"bg":"#F5F9FF","pr":"#2563EB","ac":"#EF4444","tx":"#0F172A","mu":"#6B7280","ca":"#DBEAFE","br":"#BFDBFE","nb":"rgba(245,249,255,0.97)","nt":"#1E3A8A","f1":"Inter","f2":"Inter"},
    {"dark":True,"bg":"#06080A","pr":"#64748B","ac":"#F59E0B","tx":"#F8FAFC","mu":"rgba(248,250,252,0.55)","ca":"rgba(100,116,139,0.09)","br":"rgba(100,116,139,0.22)","nb":"rgba(6,8,10,0.97)","nt":"rgba(248,250,252,0.82)","f1":"Inter","f2":"Inter"},
    {"dark":False,"bg":"#FFFFF0","pr":"#713F12","ac":"#B45309","tx":"#1C1200","mu":"#78716C","ca":"#FEF9C3","br":"#FEF08A","nb":"rgba(255,255,240,0.97)","nt":"#78350F","f1":"Playfair Display","f2":"Inter"},
    {"dark":True,"bg":"#050510","pr":"#4F46E5","ac":"#F472B6","tx":"#EEF2FF","mu":"rgba(238,242,255,0.58)","ca":"rgba(79,70,229,0.09)","br":"rgba(79,70,229,0.22)","nb":"rgba(5,5,16,0.97)","nt":"rgba(238,242,255,0.82)","f1":"Inter","f2":"Inter"},
    {"dark":False,"bg":"#FFF5F0","pr":"#9A3412","ac":"#16A34A","tx":"#431407","mu":"#78716C","ca":"#FFEDD5","br":"#FED7AA","nb":"rgba(255,245,240,0.97)","nt":"#7C2D12","f1":"Playfair Display","f2":"Inter"},
    {"dark":True,"bg":"#030A0A","pr":"#0D9488","ac":"#FACC15","tx":"#F0FDFA","mu":"rgba(240,253,250,0.58)","ca":"rgba(13,148,136,0.09)","br":"rgba(13,148,136,0.22)","nb":"rgba(3,10,10,0.97)","nt":"rgba(240,253,250,0.82)","f1":"Inter","f2":"Inter"},
    {"dark":False,"bg":"#F9F7F4","pr":"#44403C","ac":"#D97706","tx":"#1C1917","mu":"#78716C","ca":"#F5F5F0","br":"#E7E5E4","nb":"rgba(249,247,244,0.97)","nt":"#44403C","f1":"Playfair Display","f2":"Inter"},
    {"dark":True,"bg":"#0A0508","pr":"#BE185D","ac":"#34D399","tx":"#FDF2F8","mu":"rgba(253,242,248,0.58)","ca":"rgba(190,24,93,0.09)","br":"rgba(190,24,93,0.22)","nb":"rgba(10,5,8,0.97)","nt":"rgba(253,242,248,0.82)","f1":"Playfair Display","f2":"Inter"},
    {"dark":False,"bg":"#F0F0F0","pr":"#1F2937","ac":"#EF4444","tx":"#111827","mu":"#6B7280","ca":"#E5E7EB","br":"#D1D5DB","nb":"rgba(240,240,240,0.97)","nt":"#374151","f1":"Inter","f2":"Inter"},
    {"dark":True,"bg":"#00050A","pr":"#0284C7","ac":"#F97316","tx":"#F0F9FF","mu":"rgba(240,249,255,0.58)","ca":"rgba(2,132,199,0.09)","br":"rgba(2,132,199,0.22)","nb":"rgba(0,5,10,0.97)","nt":"rgba(240,249,255,0.82)","f1":"Inter","f2":"Inter"},
    {"dark":False,"bg":"#FEFEFE","pr":"#0F172A","ac":"#6366F1","tx":"#0F172A","mu":"#6B7280","ca":"#F8FAFC","br":"#E2E8F0","nb":"rgba(254,254,254,0.97)","nt":"#334155","f1":"Playfair Display","f2":"Inter"},
    {"dark":True,"bg":"#080A10","pr":"#F59E0B","ac":"#8B5CF6","tx":"#FFFBEB","mu":"rgba(255,251,235,0.58)","ca":"rgba(245,158,11,0.09)","br":"rgba(245,158,11,0.22)","nb":"rgba(8,10,16,0.97)","nt":"rgba(255,251,235,0.82)","f1":"Inter","f2":"Inter"},
    {"dark":False,"bg":"#FDF8F0","pr":"#B45309","ac":"#0891B2","tx":"#1C1200","mu":"#78716C","ca":"#FEF3C7","br":"#FDE68A","nb":"rgba(253,248,240,0.97)","nt":"#78350F","f1":"Playfair Display","f2":"Inter"},
    {"dark":True,"bg":"#050014","pr":"#7C3AED","ac":"#10B981","tx":"#F5F3FF","mu":"rgba(245,243,255,0.58)","ca":"rgba(124,58,237,0.09)","br":"rgba(124,58,237,0.22)","nb":"rgba(5,0,20,0.97)","nt":"rgba(245,243,255,0.82)","f1":"Playfair Display","f2":"Inter"},
    {"dark":False,"bg":"#FFF9F5","pr":"#D97706","ac":"#7C3AED","tx":"#1C0A00","mu":"#78716C","ca":"#FEF3C7","br":"#FDE68A","nb":"rgba(255,249,245,0.97)","nt":"#92400E","f1":"Playfair Display","f2":"Inter"},
    {"dark":True,"bg":"#060A0E","pr":"#0EA5E9","ac":"#A78BFA","tx":"#F0F9FF","mu":"rgba(240,249,255,0.58)","ca":"rgba(14,165,233,0.09)","br":"rgba(14,165,233,0.22)","nb":"rgba(6,10,14,0.97)","nt":"rgba(240,249,255,0.82)","f1":"Inter","f2":"Inter"},
    {"dark":False,"bg":"#F8FFF8","pr":"#15803D","ac":"#B45309","tx":"#052E16","mu":"#6B7280","ca":"#DCFCE7","br":"#A7F3D0","nb":"rgba(248,255,248,0.97)","nt":"#14532D","f1":"Playfair Display","f2":"Inter"},
    {"dark":True,"bg":"#0A0010","pr":"#C084FC","ac":"#F97316","tx":"#FAF5FF","mu":"rgba(250,245,255,0.58)","ca":"rgba(192,132,252,0.09)","br":"rgba(192,132,252,0.22)","nb":"rgba(10,0,16,0.97)","nt":"rgba(250,245,255,0.82)","f1":"Playfair Display","f2":"Inter"},
    {"dark":False,"bg":"#F4F6F9","pr":"#1D4ED8","ac":"#D97706","tx":"#0F172A","mu":"#6B7280","ca":"#EFF6FF","br":"#BFDBFE","nb":"rgba(244,246,249,0.97)","nt":"#1E3A8A","f1":"Inter","f2":"Inter"},
]

def get_design(prompt: str) -> dict:
    idx = abs(hash(prompt + "final_v1")) % len(ALL_DESIGNS)
    return ALL_DESIGNS[idx]

# ── CONTENT DATABASE — 80+ categories ────────────────────────────────────────
CONTENT_DB = {
    "restaurant":   {"tagline":"Where Every Bite Tells a Story","sub":"Authentic flavours crafted with passion. Fresh ingredients, timeless recipes, unforgettable dining moments.","cta1":"Reserve a Table","cta2":"View Menu","sv_title":"Our Specialties","sv":[("🍽️","Fine Dining","Exquisite multi-course meals by award-winning chefs using the finest seasonal ingredients."),("🍷","Premium Bar","Curated wines, craft cocktails, and rare spirits to complement every meal."),("🎂","Private Events","Exclusive dining rooms for celebrations, corporate dinners, and special occasions."),("🚗","Home Delivery","Restaurant quality food delivered fresh and fast to your doorstep.")],"stats":[("15+","Years of Excellence"),("50K+","Happy Guests"),("4.9★","Average Rating"),("200+","Menu Items")],"testi":[("Arjun M.","Food Critic","The finest dining experience in the city. Every single dish is a masterpiece."),("Priya S.","Regular Guest","We celebrate every anniversary here. The food and ambiance are simply magical."),("Rahul K.","Corporate Host","World-class private dining. My clients are always absolutely impressed.")],"af":[("🏆","Award-Winning","Top culinary awards for 10 consecutive years running."),("🌿","Farm to Table","Only the freshest locally sourced ingredients, always."),("🎶","Perfect Ambiance","An atmosphere as memorable as our food itself.")]},
    "saas":         {"tagline":"Ship Faster. Scale Without Limits.","sub":"AI-powered platform automating your entire workflow. Built for teams that move fast and win consistently.","cta1":"Start Free Trial","cta2":"Watch Demo","sv_title":"Platform Features","sv":[("⚡","10x Automation","Eliminate all repetitive tasks with intelligent workflows that learn and improve."),("📊","Real-time Analytics","Beautiful dashboards with actionable insights — see what matters instantly."),("🔗","200+ Integrations","Connect every tool your team already uses in just a few clicks."),("🛡️","Enterprise Security","SOC2, SSO, SAML, full audit logs — built in from day one.")],"stats":[("10K+","Teams Using"),("99.9%","Uptime SLA"),("10x","Average ROI"),("4.8★","G2 Rating")],"testi":[("Sarah C.","CTO TechFlow","Cut operational costs 60% in the first month. Absolutely transformative platform."),("Marcus J.","CEO ScaleUp","Our team ships 3x faster. The ROI was immediate and completely obvious."),("Aisha P.","VP Engineering","Best developer experience I have ever had. Truly world-class support.")],"af":[("⚡","Sub-100ms","Blazing fast response times your users will immediately notice."),("🔒","SOC2 Compliant","Enterprise-grade security built in from the very first day."),("🤖","AI-Native","Every single feature powered by intelligent automation.")]},
    "car":          {"tagline":"Drive Your Dream Car Today","sub":"Premium vehicles, transparent pricing, and a buying experience that truly respects your time and budget.","cta1":"Browse Inventory","cta2":"Book Test Drive","sv_title":"Our Services","sv":[("🚗","New Cars","Latest models from all top manufacturers at unbeatable prices."),("✅","Certified Used","Pre-owned vehicles thoroughly inspected and fully warrantied."),("💳","Easy Finance","Loans approved in 24 hours from just 7.9% APR with flexible terms."),("🔧","Service Centre","Manufacturer-trained expert technicians for every brand and model.")],"stats":[("2K+","Cars Sold"),("500+","5-Star Reviews"),("15+","Brands"),("24hr","Loan Approval")],"testi":[("Vikram P.","Business Owner","Found my dream SUV at an unbelievable price. Absolutely zero sales pressure."),("Sunita R.","Doctor","Financing approved in hours. I drove home the very same day."),("Amit K.","Entrepreneur","My third car purchase here. I will never go anywhere else.")],"af":[("🏅","150-Point Check","Every pre-owned vehicle fully certified and thoroughly inspected."),("💰","Price Match","We match any verified competitor price, completely guaranteed."),("🔧","Free Service Checks","Complimentary maintenance checks for the entire life of your vehicle.")]},
    "portfolio":    {"tagline":"Design That Moves People","sub":"Digital products that convert and delight. Every pixel deliberate. Every interaction purposeful and precise.","cta1":"View My Work","cta2":"Hire Me","sv_title":"What I Do","sv":[("🎨","UI/UX Design","Research-driven interfaces that users love and that genuinely convert."),("💻","Web Development","React and Next.js — fast, accessible, and beautifully crafted code."),("📱","Mobile Apps","iOS and Android experiences that delight every single user."),("🚀","Brand Identity","Logos and complete systems that stand the test of time.")],"stats":[("50+","Projects Delivered"),("30+","Happy Clients"),("5★","Average Rating"),("8+","Years Experience")],"testi":[("David P.","Founder","Delivered beyond every expectation, on time and under budget."),("Emma W.","Marketing Director","Conversion rate up 240% after the redesign. Extraordinary talent."),("Carlos R.","CEO","Best investment this year. Completely transformed our market position.")],"af":[("🎯","Data-Driven","Every design decision backed by rigorous research and real data."),("⚡","Fast Delivery","Production-ready designs delivered in days, not weeks or months."),("🤝","Collaborative","I work as a genuine extension of your team, never just a vendor.")]},
    "ecommerce":    {"tagline":"Premium Quality, Delivered Fast","sub":"Curated collections you will love. Free shipping on all orders. 30-day hassle-free returns. Shop confidently.","cta1":"Shop Now","cta2":"View Lookbook","sv_title":"Why Shop With Us","sv":[("🚚","Free Shipping","Express nationwide delivery on every single order, always."),("✅","Quality Assured","47-point inspection on every product before it reaches your door."),("↩️","Easy Returns","30-day returns, no questions asked, full refund guaranteed."),("💳","Secure Checkout","UPI, cards, EMI, COD — all payment methods accepted securely.")],"stats":[("50K+","Happy Customers"),("10K+","Products"),("4.9★","Rating"),("99%","Satisfaction")],"testi":[("Sneha G.","Verified Buyer","Incredible quality. Delivered in just 2 days. I will definitely order again."),("Vikram N.","Premium Member","Shopping here for 3 years. Quality is consistently excellent every time."),("Divya K.","Style Blogger","My absolute go-to for premium finds. The curation is truly impeccable.")],"af":[("🚚","Express Delivery","Free on all orders, no minimum spend ever required."),("↩️","30-Day Returns","No questions asked. Full refund absolutely guaranteed."),("✅","Quality Certified","47-point inspection on every single product we sell.")]},
    "agency":       {"tagline":"We Build Brands That Dominate Markets","sub":"Full-service growth agency. Strategy, creative, and technology turning businesses into undisputed category leaders.","cta1":"Get a Proposal","cta2":"See Case Studies","sv_title":"Our Services","sv":[("📈","Growth Strategy","Data-driven plans that have driven explosive growth for 100+ brands."),("🎯","Performance Marketing","Google, Meta campaigns that consistently beat every benchmark."),("🌐","Digital Products","Websites and apps engineered specifically to convert visitors."),("✍️","Brand and Creative","Stories that connect emotionally and drive real measurable action.")],"stats":[("100+","Brands Grown"),("₹50Cr+","Revenue Generated"),("4.9★","Client Rating"),("8+","Years")],"testi":[("Ankit J.","CMO","Tripled our qualified leads in just 90 days. Best agency we ever worked with."),("Meera K.","Founder","The complete rebrand drove 180% revenue growth year on year."),("Rajesh P.","CEO","True growth partners, every single time. Exceptional results always.")],"af":[("📊","Data-Driven","Every single strategy backed by rigorous research and real data."),("⚡","Agile Execution","Delivering real results in weeks, never in quarters."),("🎯","ROI-Obsessed","Every rupee spent tied directly to measurable business outcomes.")]},
    "fitness":      {"tagline":"Transform Your Body. Own Your Life.","sub":"Expert coaching, elite facilities, and a community that absolutely refuses to let you quit. Start your transformation today.","cta1":"Start Free Trial","cta2":"View Programs","sv_title":"Our Programs","sv":[("💪","Strength Training","Elite programming to build real, lasting, functional power."),("🏃","HIIT and Cardio","High-intensity sessions that torch fat and build serious endurance."),("🧘","Recovery and Mobility","Yoga and protocols to prevent injury and optimise performance."),("🥗","Nutrition Coaching","Personalised meal plans that fuel your complete transformation.")],"stats":[("5K+","Members"),("50+","Elite Coaches"),("98%","Success Rate"),("4.9★","Rating")],"testi":[("Kiran R.","Member","Lost 20kg in 6 months. The coaching here is genuinely life-changing."),("Ananya S.","Marathon Runner","Improved my PB by 22 minutes. Absolutely world-class programming."),("Dev M.","Powerlifter","Gained 12kg of muscle in one year. The science here is completely real.")],"af":[("🏆","Elite Coaches","Internationally certified trainers with real-world competitive experience."),("📊","Science-Based","Programming built entirely on peer-reviewed sports science."),("👥","Unstoppable Community","A support system that genuinely keeps you accountable every day.")]},
    "education":    {"tagline":"Learn Without Limits. Grow Without Ceiling.","sub":"World-class instructors, live cohorts, lifetime access, and certifications that employers genuinely value and recognise.","cta1":"Enroll Now","cta2":"Browse Courses","sv_title":"What We Offer","sv":[("📚","Expert Courses","Learn directly from top industry practitioners with proven track records."),("🎯","Live Cohorts","Real-time interactive classes with Q&A and genuine mentorship."),("🏆","Certifications","Industry-recognised credentials that hiring managers truly trust."),("♾️","Lifetime Access","Learn entirely at your own pace. Revisit any lesson forever.")],"stats":[("20K+","Students"),("500+","Courses"),("4.9★","Rating"),("95%","Placement Rate")],"testi":[("Rohan M.","Graduate","Got my absolute dream job just 3 months after completing the program."),("Priya T.","Career Changer","The best investment I have ever made in my career. Life-changing."),("Amit S.","Professional","Promoted twice. The skills I learned are directly applicable every single day.")],"af":[("👨‍🏫","Expert Instructors","Industry practitioners with real-world track records and results."),("🎯","Project-Based","Build genuine real projects, not just passively watch videos."),("🏆","Recognised Credentials","Certifications that employers and hiring managers truly trust.")]},
    "realestate":   {"tagline":"Find Your Perfect Home","sub":"Premium listings, trusted agents, and a completely transparent process. Buying, selling, or renting made truly effortless.","cta1":"Browse Properties","cta2":"Talk to an Agent","sv_title":"Our Services","sv":[("🏠","Residential Sales","Premium homes and apartments in all prime locations available."),("🔑","Rental Properties","Fully verified listings with completely transparent pricing always."),("💼","Commercial Spaces","Offices and retail spaces for every type and size of business."),("📋","Property Management","Complete end-to-end management for every landlord we work with.")],"stats":[("5K+","Properties"),("2K+","Happy Clients"),("₹500Cr+","Transactions"),("4.9★","Rating")],"testi":[("Suresh P.","Home Buyer","Found our perfect 3BHK in just 2 weeks. The agent was truly exceptional."),("Kavita M.","Property Investor","The ROI on properties they recommended has been consistently outstanding."),("Arun K.","Home Seller","Sold above asking price in just 10 days. Absolutely remarkable service.")],"af":[("🔍","Market Knowledge","Hyper-local expertise in every single area we serve."),("💰","Best Price Guaranteed","We negotiate hard to get you the absolute best deal possible."),("📋","All Paperwork Handled","Every document, verification, and legal step completely managed.")]},
    "hospital":     {"tagline":"Expert Care, Every Step of the Way","sub":"Compassionate healthcare with cutting-edge technology. Your health and recovery are our absolute only priority.","cta1":"Book Appointment","cta2":"Find a Doctor","sv_title":"Our Departments","sv":[("🫀","Cardiology","Comprehensive heart care from initial diagnosis to complete surgery and full rehabilitation."),("🧠","Neurology","Advanced treatment for all brain, spine, and nervous system conditions."),("🦷","Dental Care","Complete dental services from routine cleaning to the most complex surgery."),("👶","Paediatrics","Specialised child healthcare for every age from newborn through adolescence.")],"stats":[("50K+","Patients Treated"),("50+","Specialists"),("20+","Departments"),("4.9★","Patient Rating")],"testi":[("Ramesh K.","Patient","The exceptional care I received here saved my life. Truly an incredible team."),("Sunita V.","Patient's Family","Compassionate, highly skilled, and always completely available for us."),("Dr. Anil S.","Referring Physician","Best facility in the entire region. I refer all my complex cases here.")],"af":[("👨‍⚕️","Expert Specialists","50+ specialists covering every possible medical department and specialty."),("🏥","Advanced Technology","State-of-the-art diagnostic and surgical technology throughout."),("❤️","Patient-First Always","Treating the whole person, not just the medical condition presented.")]},
    "hotel":        {"tagline":"Where Luxury Meets Serenity","sub":"An extraordinary escape where world-class hospitality, breathtaking surroundings, and unmatched comfort unite perfectly.","cta1":"Book Your Stay","cta2":"Explore Rooms","sv_title":"Our Offerings","sv":[("🛏️","Luxury Rooms","Beautifully appointed rooms and suites with truly stunning views."),("🍽️","Fine Dining","Award-winning restaurants serving the finest world cuisine."),("🏊","Pool and Spa","Stunning infinity pool and a full-service wellness sanctuary."),("💼","Business Centre","State-of-the-art conference and premium event facilities.")],"stats":[("20+","Years of Luxury"),("10K+","Happy Guests"),("5★","Star Rating"),("4.9★","Guest Reviews")],"testi":[("Ananya P.","Honeymooner","The most magical and perfect experience of our entire lives."),("Rohit V.","Business Traveller","World-class facilities and service. My absolute go-to on every single visit."),("Meera S.","Leisure Guest","Every single detail was completely perfect. We return here every year.")],"af":[("⭐","5-Star Service","Award-winning hospitality that anticipates your every possible need."),("🍽️","Signature Dining","Three distinct restaurants, each a true culinary destination."),("🧖","World-Class Spa","A complete sanctuary of wellness and total rejuvenation.")]},
    "law":          {"tagline":"Justice. Expertise. Results.","sub":"Experienced legal counsel for individuals and businesses. We fight for your rights with precision, dedication, and integrity.","cta1":"Free Consultation","cta2":"Practice Areas","sv_title":"Practice Areas","sv":[("🏢","Corporate Law","Business formation, contracts, mergers, acquisitions, and full governance."),("⚖️","Civil Litigation","Expert representation across every civil court in the country."),("👨‍👩‍👧","Family Law","Divorce, custody, adoption, and all family legal matters handled."),("🏠","Property Law","Real estate transactions, disputes, and all property rights matters.")],"stats":[("10K+","Cases Won"),("25+","Years"),("200+","Corporate Clients"),("4.9★","Client Rating")],"testi":[("Rajesh M.","Business Owner","Won a complex case that every other lawyer said was completely unwinnable."),("Priya S.","Individual Client","Handled my case with absolute sensitivity and total professionalism throughout."),("Amit Corp","General Counsel","Our trusted legal partner for every single corporate matter for 10 years.")],"af":[("⚖️","Proven Track Record","10,000+ cases won across all courts and every tribunal."),("🔒","Absolute Confidentiality","Complete attorney-client privilege guaranteed on every single matter."),("📞","Always Available","24/7 access for every urgent legal matter, without exception.")]},
    "startup":      {"tagline":"From Zero to Category Leader","sub":"We are actively building the future. Join us at the ground floor of the defining company of our entire generation.","cta1":"Join Waitlist","cta2":"See How It Works","sv_title":"What We Are Building","sv":[("⚡","Core Product","The fastest and most intuitive solution anywhere in the market today."),("🤖","AI Layer","Intelligent features that learn and continuously improve with every interaction."),("🔗","Open Platform","A comprehensive API that developers can build extraordinary things on top of."),("🌐","Global Scale","Infrastructure built and ready to serve millions of users from day one.")],"stats":[("1K+","Beta Users"),("₹2Cr+","Pre-orders"),("3x","Monthly Growth"),("4.9★","Beta Rating")],"testi":[("Ankit S.","Beta User","This is going to be absolutely massive. I have truly never seen anything like it."),("Meera V.","Investor","The most impressive founding team and product I have ever encountered."),("Rahul P.","Early Adopter","Switched to this on day one and have never once looked back at anything else.")],"af":[("🚀","Hypergrowth","Consistent 3x month-over-month growth every single month since launch."),("🤖","AI-First","Intelligence built in from the core, not bolted on as an afterthought."),("🌍","Global Vision","Building for India first, then systematically conquering the entire world.")]},
    "finance":      {"tagline":"Your Wealth. Our Expertise.","sub":"SEBI-registered advisors helping you build, protect, and grow wealth through disciplined, personalised financial planning.","cta1":"Free Consultation","cta2":"Our Services","sv_title":"Our Services","sv":[("📈","Wealth Management","Completely personalised portfolios aligned perfectly to your specific goals."),("🏦","Mutual Funds","Expert curated fund selection and comprehensive SIP planning services."),("🛡️","Insurance Planning","Comprehensive coverage protecting everything you have worked hard to build."),("📋","Tax Planning","Fully legal optimisation strategies designed to maximise your net returns.")],"stats":[("5K+","Clients"),("₹500Cr+","AUM"),("15+","Years"),("4.9★","Rating")],"testi":[("Suresh M.","Business Owner","My portfolio has grown 18% annually for 5 consecutive years. Exceptional guidance."),("Kavita P.","Retired Professional","They secured my retirement completely. I have total and absolute peace of mind."),("Arun S.","Young Professional","Started my SIP journey here. The compounding results are already truly remarkable.")],"af":[("📊","Research-Driven","All recommendations backed by completely rigorous fundamental analysis."),("🔒","SEBI Registered","Fully regulated and compliant with every applicable guideline."),("💼","Personalised Always","No generic advice ever. Every plan built specifically for your unique situation.")]},
    "construction": {"tagline":"Building Dreams. Delivering Excellence.","sub":"From homes to commercial complexes, delivered on time, on budget, and to the very highest quality standards, always.","cta1":"Get a Free Quote","cta2":"View Projects","sv_title":"Our Services","sv":[("🏠","Residential Construction","Custom homes and apartments built to the very highest possible specifications."),("🏢","Commercial Projects","Offices, malls, and industrial facilities delivered at real scale."),("🎨","Interior Design","Complete interior design and full fit-out services for every space."),("🔧","Renovation","Expert renovation and remodelling of all types of existing structures.")],"stats":[("500+","Projects Completed"),("₹500Cr+","Total Project Value"),("20+","Years Experience"),("4.9★","Client Rating")],"testi":[("Vikram S.","Property Developer","5 major projects completed with them. Quality and timing is always absolutely perfect."),("Anita R.","Home Owner","My dream home, built exactly as I had always imagined it. Simply stunning."),("Raj Corp","Commercial Client","Entire office complex delivered on time, on budget, with exceptional finish.")],"af":[("🏗️","Turnkey Delivery","Complete project management from first foundation to final finishing touch."),("⏰","On-Time Guarantee","Never missed a single project deadline in our entire 20-year history."),("🏆","ISO 9001 Certified","Certified processes ensuring consistently the highest possible build quality.")]},
    "ngo":          {"tagline":"Every Life Deserves Dignity","sub":"Working at the intersection of deep compassion and decisive action to create lasting change for communities most in need.","cta1":"Donate Now","cta2":"Get Involved","sv_title":"Our Programs","sv":[("📚","Education","Quality education and merit scholarships for underprivileged children everywhere."),("🏥","Healthcare","Mobile medical clinics serving the most remote communities nationwide."),("💼","Livelihood","Skills training and microfinance creating genuine economic independence."),("🌱","Environment","Tree planting, water conservation, and community clean-up drives always.")],"stats":[("100K+","Lives Impacted"),("15+","Years of Service"),("50+","Communities Served"),("4.9★","Transparency Rating")],"testi":[("Anita S.","Major Donor","I can see exactly where every rupee of my donation goes. The impact is completely real."),("Rahul M.","Corporate Partner","The most transparent and impactful NGO we have ever partnered with."),("Meera P.","Long-term Volunteer","Volunteering here genuinely changed my life as much as it changed these communities.")],"af":[("✅","100% Transparent","Full detailed financial reports published for every single donor."),("🎯","Measurable Impact","Every program evaluated against clear, independently audited outcomes."),("🤝","Community-Led","All programs designed with and for the communities we proudly serve.")]},
    "photography":  {"tagline":"Capturing Moments That Last Forever","sub":"Every frame tells a unique story. Professional photography transforming ordinary moments into extraordinary timeless memories.","cta1":"Book a Session","cta2":"View Portfolio","sv_title":"Our Services","sv":[("📸","Wedding Photography","Your perfect day captured beautifully and preserved forever in stunning detail."),("👤","Portrait Sessions","Professional headshots and deeply personal portrait photography."),("🏢","Commercial Photography","Stunning product photography and comprehensive corporate shoots."),("🎬","Videography","Cinematic videos that genuinely move and emotionally connect people.")],"stats":[("500+","Sessions Completed"),("50K+","Photos Delivered"),("5★","Rating"),("10+","Years")],"testi":[("Sneha P.","Bride","Our wedding photos are absolutely breathtakingly beautiful. We cry every time."),("Rajesh K.","CEO","Professional headshots exceeded every single one of our expectations completely."),("Priya M.","Marketing Head","The commercial shots dramatically improved our entire campaign performance.")],"af":[("📷","Award-Winning","Recognised by multiple national photography associations."),("🎨","Artistic Vision","Every single photograph is a deliberate and lasting work of art."),("💾","48hr Delivery","All fully edited photos delivered within just 48 hours always.")]},
    "salon":        {"tagline":"Where Beauty Meets Expertise","sub":"Premium salon services in a genuinely luxurious setting. Look and feel your absolute best every single day you visit.","cta1":"Book Appointment","cta2":"Our Services","sv_title":"Our Services","sv":[("💇","Hair Styling","Expert cuts, colours, and professional treatments by true master stylists."),("💅","Nail Art","Manicure, pedicure, and creative nail artistry done perfectly every time."),("🧖","Spa Treatments","Deeply relaxing facials and rejuvenating full-body treatments."),("💄","Bridal Makeup","Stunning wedding and special occasion makeup by skilled professionals.")],"stats":[("10K+","Happy Clients"),("50+","Services"),("5★","Rating"),("8+","Years")],"testi":[("Sunita R.","Bride","The absolute best bridal makeup I have ever seen. Completely and utterly perfect."),("Kavita P.","Regular Client","I come every single month. I always leave looking and feeling genuinely amazing."),("Meera S.","Client","The hair treatment completely and totally transformed my confidence overnight.")],"af":[("💎","Premium Products Only","Exclusively top-tier professional products used on every client."),("👩‍🎨","Expert Stylists","Internationally trained and fully certified beauty professionals throughout."),("🌿","Hygienic Always","Sterilized tools and fresh towels for every single client, every time.")]},
    "travel":       {"tagline":"Your World Awaits. Let Us Take You There.","sub":"Curated travel experiences, personalised itineraries, and unforgettable memories that genuinely last an entire lifetime.","cta1":"Plan My Trip","cta2":"View Packages","sv_title":"Our Services","sv":[("✈️","International Tours","Handcrafted itineraries to the world's most extraordinary destinations."),("🏔️","Adventure Travel","Epic treks, safaris, and extreme experiences for the bold explorer."),("🏖️","Beach Holidays","Perfect resort stays and stunning island getaways for every budget."),("💑","Honeymoon Packages","Deeply romantic escapes tailored with love specifically for couples.")],"stats":[("5K+","Happy Travellers"),("100+","Destinations"),("15+","Years"),("4.9★","Rating")],"testi":[("Rahul K.","Traveller","The Bali trip was flawlessly organised from start to finish. A complete dream."),("Priya S.","Couple","Our honeymoon was beyond absolutely anything we had ever imagined possible."),("Amit R.","Family","The Rajasthan family tour was magical and perfect for every single one of us.")],"af":[("🗺️","Expert Local Guides","Genuine local expertise in every single destination we serve worldwide."),("💰","Absolute Best Value","Unbeatable package pricing for truly unforgettable lifetime experiences."),("📞","24/7 Travel Support","We are always with you, every step of your entire journey, always.")]},
    "tech_company": {"tagline":"Technology That Truly Transforms Business","sub":"End-to-end technology solutions driving complete digital transformation and accelerating sustainable long-term growth.","cta1":"Get a Quote","cta2":"View Our Work","sv_title":"Our Services","sv":[("💻","Software Development","Custom software built precisely for your exact business needs and goals."),("📱","App Development","iOS, Android, and cross-platform mobile apps that delight every user."),("☁️","Cloud Solutions","Complete cloud migration, architecture, and fully managed services."),("🔒","Cybersecurity","Protecting your entire business from all evolving and emerging threats.")],"stats":[("500+","Projects"),("200+","Clients"),("15+","Years"),("4.9★","Rating")],"testi":[("Vikram S.","CTO","Delivered our entire platform exactly on time and significantly under budget."),("Anita R.","CEO","The app they built drives a full 60% of our total company revenue now."),("Rahul P.","Founder","Absolutely the best tech partner we have ever worked with. Truly remarkable.")],"af":[("⚡","Agile Delivery","Fast iterative development with regular, meaningful, impactful releases."),("🔒","Secure by Design","Security built in at every single layer of every system we build."),("🤝","Long-term Partnership","We stay genuinely invested in your success indefinitely and always.")]},
    "wedding":      {"tagline":"Your Perfect Day. Our Greatest Joy.","sub":"Wedding experiences so completely perfect they feel like dreams you genuinely never want to wake from. Ever.","cta1":"Plan Your Wedding","cta2":"View Gallery","sv_title":"Our Services","sv":[("💒","Full Planning","Complete wedding management from first concept all the way to your big day."),("📸","Photography","Cinematic wedding photography and beautiful professional videography."),("🌸","Decor and Florals","Breathtakingly beautiful decorations and stunning artisanal floral design."),("🍽️","Catering","Exquisite menus created for every cuisine preference and every taste.")],"stats":[("500+","Weddings Planned"),("50K+","Happy Guests"),("10+","Years"),("5★","Rating")],"testi":[("Priya and Rahul","Happy Couple","Our wedding was completely and utterly beyond any dream we had ever had."),("Sunita P.","Bride's Mother","Every single detail was handled with such genuine love and beautiful care."),("Amit V.","Groom","The best decision we ever made together was hiring this incredible team.")],"af":[("💎","Luxury Execution","Every single element crafted to absolute and complete perfection."),("🤝","Personal Touch","Your dedicated planner committed solely and exclusively to your wedding."),("📞","Always On Call","Available 24/7 throughout your entire planning journey, without fail.")]},
    "dental":       {"tagline":"Your Smile. Our Expertise.","sub":"Advanced dental care in a comfortable, completely anxiety-free environment. Your most perfect smile genuinely awaits you.","cta1":"Book Appointment","cta2":"Our Treatments","sv_title":"Our Treatments","sv":[("🦷","General Dentistry","Regular checkups, thorough cleaning, and comprehensive preventive care."),("😁","Cosmetic Dentistry","Whitening, porcelain veneers, and complete transformative smile makeovers."),("🦾","Dental Implants","Permanent, natural-looking, and completely comfortable tooth replacement."),("😬","Orthodontics","Traditional braces and modern Invisalign for perfect, beautiful alignment.")],"stats":[("10K+","Patients"),("20+","Treatments"),("15+","Years"),("5★","Rating")],"testi":[("Rahul K.","Patient","My smile transformation was absolutely and completely incredible. Life-changing."),("Priya S.","Patient","The most genuinely pain-free dental experience I have ever had anywhere."),("Amit M.","Parent","My children actually look forward to coming here now. Truly remarkable.")],"af":[("🔬","Latest Technology","The most advanced dental technology for completely precise treatment."),("💊","Truly Pain-Free","Anxiety-free care with the most modern pain management techniques."),("😁","Results Guaranteed","We completely guarantee results or we make it absolutely right.")]},
    "cleaning":     {"tagline":"Spotless Spaces. Happy Places.","sub":"Professional cleaning services transforming your home or office into a pristine, immaculate, welcoming sanctuary.","cta1":"Book a Clean","cta2":"Our Services","sv_title":"Our Services","sv":[("🏠","Home Cleaning","Thorough deep and regular cleaning for all residential properties."),("🏢","Office Cleaning","Professional commercial cleaning services for all types of businesses."),("🧹","Deep Clean","Intensive specialist cleaning for all move-in and move-out situations."),("🌿","Eco Cleaning","Green cleaning using only non-toxic, completely safe eco products.")],"stats":[("5K+","Clients"),("50K+","Cleans Done"),("8+","Years"),("5★","Rating")],"testi":[("Priya S.","Home Owner","My home has absolutely never ever been this clean. Genuinely exceptional."),("TechCorp","Office Manager","Our office is always spotless. The team is incredibly reliable every time."),("Rahul K.","Landlord","Move-out cleans are completely perfect and thorough every single time.")],"af":[("✅","Verified Staff","All staff fully background-checked and completely insured always."),("🌿","100% Eco-Friendly","Non-toxic, completely safe products protecting your whole family."),("⏰","Always Reliable","Always on time, always thorough, never ever letting you down.")]},
    "mental_health":{"tagline":"Your Mental Health Truly Matters","sub":"Compassionate, completely confidential therapy and counselling. You genuinely deserve support and real help is here.","cta1":"Book a Session","cta2":"Meet Our Team","sv_title":"Our Services","sv":[("🧠","Individual Therapy","One-on-one sessions with qualified, genuinely caring therapists."),("👫","Couples Counselling","Expert guidance to strengthen and truly transform your relationship."),("👨‍👩‍👧","Family Therapy","Healing and improved communication for every member of your family."),("📱","Online Sessions","Convenient, accessible therapy from the complete comfort of your home.")],"stats":[("5K+","Clients Helped"),("20+","Therapists"),("10+","Years"),("5★","Rating")],"testi":[("Priya S.","Client","My anxiety is finally manageable for the very first time in years. Grateful."),("Rahul K.","Couple","Our marriage is stronger than it has ever been after these counselling sessions."),("Anita M.","Client","The online sessions fit perfectly and seamlessly into my extremely busy life.")],"af":[("🔐","Complete Confidentiality","Absolute privacy and total confidentiality guaranteed on every matter."),("❤️","Non-Judgmental Always","A completely safe and accepting space to be entirely and authentically yourself."),("👩‍⚕️","Fully Qualified","All therapists hold internationally recognised professional credentials.")]},
    "business":     {"tagline":"Excellence Delivered Every Single Time","sub":"Deep expertise, bold decisive execution, and a genuine obsession with results. We help businesses grow and consistently win.","cta1":"Get Started Today","cta2":"Learn More","sv_title":"What We Offer","sv":[("⚡","Fast Results","Exceptional outcomes delivered consistently ahead of every schedule."),("🎯","Results-Obsessed","Every single action tied directly to your specific measurable goals."),("🤝","True Partnership","Genuinely invested in your success as deeply and completely as you are."),("🛡️","Proven Reliability","100+ clients trust us with their most critical and important projects.")],"stats":[("100+","Projects Completed"),("50+","Happy Clients"),("4.9★","Average Rating"),("5+","Years")],"testi":[("Rohit K.","Managing Director","Delivered exactly as promised and significantly ahead of schedule. Exceptional."),("Nisha A.","COO","The best and most reliable vendor relationship we have ever had. Truly."),("Amit S.","Founder","An absolute and complete game-changer for our business and our growth.")],"af":[("⚡","Always Fast","Results delivered faster than any competitor, without exception."),("🎯","ROI-Focused","Every engagement measured against real, tangible business impact."),("🛡️","Proven Always","5+ years, 100+ clients, zero failures of any kind whatsoever.")]},
}

def get_content(cat: str) -> dict:
    return CONTENT_DB.get(cat, CONTENT_DB["business"])

# ── AI PROMPT BUILDER ─────────────────────────────────────────────────────────
def build_ai_prompt(prompt: str, name: str, ud: dict) -> str:
    phone = ud.get("phone") or "+91 99999 99999"
    email = ud.get("email") or "hello@" + re.sub(r'[^a-z0-9]', '', name.lower()) + ".com"
    address = ud.get("address") or "Mumbai, India"
    wa = (ud.get("whatsapp") or phone).replace("+","").replace(" ","").replace("-","")
    hours = ud.get("opening_hours") or "Mon-Sat 9AM-8PM"
    seed = abs(hash(prompt)) % 99999
    enc = urllib.parse.quote(prompt[:60])
    h1 = f"https://image.pollinations.ai/prompt/ultra_realistic_{enc}_hero_4k?width=1400&height=800&seed={seed}&nologo=true&model=flux"
    h2 = f"https://image.pollinations.ai/prompt/professional_{enc}?width=900&height=700&seed={seed+1}&nologo=true&model=flux"
    return (
        f"You are an expert web developer. Generate a COMPLETE, STUNNING single HTML file website.\n\n"
        f"USER REQUEST: {prompt}\n"
        f"BUSINESS NAME: {name}\n"
        f"PHONE: {phone} | EMAIL: {email} | ADDRESS: {address} | WHATSAPP: {wa} | HOURS: {hours}\n\n"
        f"IMAGES (use these exact URLs):\n"
        f"Hero: {h1}\n"
        f"About: {h2}\n\n"
        f"CRITICAL RULES:\n"
        f"1. Output ONLY raw HTML starting with <!DOCTYPE html>. Zero markdown, zero explanation.\n"
        f"2. Make it as beautiful as Stripe, Linear, or Apple — world-class design quality.\n"
        f"3. Include: sticky nav with hamburger, full hero with 3D tilt image, stats bar, about section, "
        f"services grid, gallery, testimonials, FAQ accordion, contact form with validation, Google Maps embed, "
        f"WhatsApp float button, sticky CTA bar, newsletter, footer with social links, loading screen, "
        f"scroll reveal animations, counter animations, back to top button, cookie banner.\n"
        f"4. Use beautiful Google Fonts. CSS custom properties. Smooth animations. Mobile responsive.\n"
        f"5. Contact form must show success message on submit (no backend).\n"
        f"6. Include phone/email/address/hours prominently throughout.\n"
        f"7. WhatsApp link: https://wa.me/{wa}\n"
        f"8. Google Maps: https://maps.google.com/maps?q={urllib.parse.quote(address)}&output=embed"
    )

# ── MAIN TEMPLATE BUILDER ─────────────────────────────────────────────────────
def build_template(prompt: str, name: str, ud: dict) -> str:
    cat = get_category(prompt)
    ds = get_design(prompt)
    con = get_content(cat)
    seed = abs(hash(prompt)) % 99999
    enc = urllib.parse.quote(prompt[:80])

    phone = ud.get("phone") or "+91 99999 99999"
    email_addr = ud.get("email") or "hello@" + re.sub(r'[^a-z0-9]', '', name.lower()) + ".com"
    address = ud.get("address") or "Mumbai, India"
    wa = (ud.get("whatsapp") or phone).replace("+","").replace(" ","").replace("-","")
    hours = ud.get("opening_hours") or "Mon-Sat: 9 AM - 8 PM"
    tagline = ud.get("tagline_custom") or con["tagline"]
    about_text = ud.get("about_text") or con["sub"]
    ig = ud.get("instagram") or ""
    fb = ud.get("facebook") or ""
    tw = ud.get("twitter") or ""
    li = ud.get("linkedin") or ""

    is_dark = ds["dark"]
    f1 = ds["f1"]
    f2 = ds["f2"]

    imgs = {
        "h":  f"https://image.pollinations.ai/prompt/ultra_realistic_cinematic_{enc}_dramatic_4k?width=1400&height=800&seed={seed}&nologo=true&model=flux",
        "a":  f"https://image.pollinations.ai/prompt/professional_{enc}_premium_team?width=900&height=700&seed={seed+1}&nologo=true&model=flux",
        "g1": f"https://image.pollinations.ai/prompt/{enc}_showcase_1?width=700&height=500&seed={seed+2}&nologo=true&model=flux",
        "g2": f"https://image.pollinations.ai/prompt/{enc}_showcase_2?width=700&height=500&seed={seed+3}&nologo=true&model=flux",
        "g3": f"https://image.pollinations.ai/prompt/{enc}_showcase_3?width=700&height=500&seed={seed+4}&nologo=true&model=flux",
        "g4": f"https://image.pollinations.ai/prompt/{enc}_showcase_4?width=700&height=500&seed={seed+5}&nologo=true&model=flux",
    }

    nav_logo = "#fff" if is_dark else ds["pr"]
    nav_link = "rgba(255,255,255,0.8)" if is_dark else ds["mu"]
    nav_hb = "#fff" if is_dark else ds["tx"]
    hero_ov = f"linear-gradient(135deg,{ds['bg']}F5 0%,{ds['bg']}CC 60%,{ds['pr']}22 100%)"
    shadow = "0 40px 80px rgba(0,0,0,0.5)" if is_dark else "0 40px 80px rgba(0,0,0,0.12)"
    svc_bg = "rgba(255,255,255,0.03)" if is_dark else ds["ca"]
    inp = "rgba(255,255,255,0.07)" if is_dark else "#ffffff"
    map_q = urllib.parse.quote(address)
    mob_bg = "rgba(2,0,8,0.98)" if is_dark else "rgba(255,255,255,0.99)"
    ck_glow = "rgba(2,0,8,0.97)" if is_dark else "rgba(15,15,15,0.97)"

    svcs = ""
    for ic, t, d in con["sv"]:
        svcs += (
            '<div class="sc" '
            'onmouseover="this.style.transform=\'translateY(-8px)\';this.style.borderColor=\'' + ds["pr"] + '\'" '
            'onmouseout="this.style.transform=\'\';this.style.borderColor=\'' + ds["br"] + '\'">'
            f'<span class="si">{ic}</span><h3>{t}</h3><p>{d}</p></div>'
        )

    stats = ""
    for n, l in con["stats"]:
        stats += f'<div class="sti"><div class="sn">{n}</div><div class="sl">{l}</div></div>'

    testis = ""
    for a, r, t in con["testi"]:
        testis += (
            '<div class="tc" '
            'onmouseover="this.style.transform=\'translateY(-6px)\';this.style.borderColor=\'' + ds["pr"] + '\'" '
            'onmouseout="this.style.transform=\'\';this.style.borderColor=\'' + ds["br"] + '\'">'
            f'<div class="ts">★★★★★</div>'
            f'<p class="tt">"{t}"</p>'
            f'<div class="ta"><div class="av">{a[0]}</div>'
            f'<div><div class="an">{a}</div><div class="ar">{r}</div></div></div></div>'
        )

    gals = ""
    for k in ["g1", "g2", "g3", "g4"]:
        gals += (
            '<div class="gi" '
            'onmouseover="this.querySelector(\'img\').style.transform=\'scale(1.1)\'" '
            'onmouseout="this.querySelector(\'img\').style.transform=\'\'">'
            f'<img src="{imgs[k]}" loading="lazy" alt="Gallery"/>'
            '<div class="go"><span>View &#8594;</span></div></div>'
        )

    afs = ""
    for ic, t, d in con["af"]:
        afs += (
            '<div class="af" '
            'onmouseover="this.style.borderColor=\'' + ds["pr"] + '\';this.style.transform=\'translateX(5px)\'" '
            'onmouseout="this.style.borderColor=\'' + ds["br"] + '\';this.style.transform=\'\'">'
            f'<div class="afi">{ic}</div>'
            f'<div class="aft"><h4>{t}</h4><p>{d}</p></div></div>'
        )

    social_links = ""
    social_links += f'<a href="https://instagram.com/{ig}" target="_blank" title="Instagram">&#128248;</a>' if ig else '<a href="#" title="Instagram">&#128248;</a>'
    social_links += f'<a href="https://facebook.com/{fb}" target="_blank" title="Facebook">&#128077;</a>' if fb else '<a href="#" title="Facebook">&#128077;</a>'
    social_links += f'<a href="https://twitter.com/{tw}" target="_blank" title="Twitter">&#128038;</a>' if tw else '<a href="#" title="Twitter">&#128038;</a>'
    social_links += f'<a href="https://linkedin.com/in/{li}" target="_blank" title="LinkedIn">&#128188;</a>' if li else '<a href="#" title="LinkedIn">&#128188;</a>'
    social_links += f'<a href="https://wa.me/{wa}" target="_blank" title="WhatsApp">&#128172;</a>'

    footer_svcs = "".join([f'<a href="#services">{s[1]}</a>' for s in con["sv"]])

    gf1 = f1.replace(" ", "+")
    gf2 = f2.replace(" ", "+")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="{name} - {tagline}. {con['sub'][:120]}">
<meta property="og:title" content="{name}">
<meta property="og:description" content="{con['sub'][:160]}">
<meta property="og:image" content="{imgs['h']}">
<meta name="twitter:card" content="summary_large_image">
<title>{name} - {tagline}</title>
<link href="https://fonts.googleapis.com/css2?family={gf1}:ital,wght@0,700;0,800;0,900;1,700&family={gf2}:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
:root{{--bg:{ds["bg"]};--pr:{ds["pr"]};--ac:{ds["ac"]};--tx:{ds["tx"]};--mu:{ds["mu"]};--ca:{ds["ca"]};--br:{ds["br"]};--nb:{ds["nb"]};--nt:{ds["nt"]}}}
html{{scroll-behavior:smooth}}
::-webkit-scrollbar{{width:5px}}::-webkit-scrollbar-track{{background:var(--bg)}}::-webkit-scrollbar-thumb{{background:var(--pr);border-radius:3px}}
body{{font-family:"{f2}",sans-serif;background:var(--bg);color:var(--tx);overflow-x:hidden;line-height:1.6}}
@keyframes fadeUp{{from{{opacity:0;transform:translateY(40px)}}to{{opacity:1;transform:translateY(0)}}}}
@keyframes fadeRight{{from{{opacity:0;transform:translateX(50px)}}to{{opacity:1;transform:translateX(0)}}}}
@keyframes pulse{{0%,100%{{opacity:1;transform:scale(1)}}50%{{opacity:0.65;transform:scale(1.35)}}}}
@keyframes float{{0%,100%{{transform:translateY(0)}}50%{{transform:translateY(-14px)}}}}
@keyframes spin{{to{{transform:rotate(360deg)}}}}
@keyframes waP{{0%,100%{{box-shadow:0 0 0 0 rgba(37,211,102,0.5)}}70%{{box-shadow:0 0 0 16px rgba(37,211,102,0)}}}}
#ldr{{position:fixed;inset:0;background:var(--bg);z-index:99999;display:flex;align-items:center;justify-content:center;flex-direction:column;gap:18px;transition:opacity 0.6s}}
#ldr.out{{opacity:0;pointer-events:none}}
.ldr-logo{{font-family:"{f1}",serif;font-size:2.2rem;font-weight:900;color:var(--pr);letter-spacing:-1px}}
.ldr-ring{{width:46px;height:46px;border:3px solid var(--ca);border-top-color:var(--pr);border-radius:50%;animation:spin 0.8s linear infinite}}
nav{{position:fixed;top:0;width:100%;z-index:1000;padding:0 5%;transition:all 0.4s}}
nav.solid{{background:var(--nb);backdrop-filter:blur(24px);border-bottom:1px solid var(--br);box-shadow:0 4px 30px rgba(0,0,0,0.08)}}
.ni{{max-width:1280px;margin:0 auto;display:flex;align-items:center;justify-content:space-between;height:72px}}
.logo{{font-family:"{f1}",serif;font-size:1.75rem;font-weight:900;color:{nav_logo};text-decoration:none;letter-spacing:-0.5px;transition:color 0.3s}}
nav.solid .logo{{color:var(--pr)}}
.lks{{display:flex;align-items:center;gap:32px;list-style:none}}
.lks a{{color:{nav_link};text-decoration:none;font-weight:500;font-size:0.88rem;transition:color 0.2s;letter-spacing:0.2px}}
nav.solid .lks a{{color:var(--nt)}}
.lks a:hover,.lks a.active{{color:var(--pr)}}
.nbtn{{background:var(--pr);color:#fff;padding:10px 24px;border-radius:100px;font-weight:700;font-size:0.85rem;text-decoration:none;transition:all 0.3s;box-shadow:0 4px 20px rgba(0,0,0,0.15)}}
.nbtn:hover{{transform:translateY(-2px);filter:brightness(1.1);color:#fff}}
.hb{{display:none;background:none;border:none;cursor:pointer;flex-direction:column;gap:5px;padding:4px}}
.hb span{{width:24px;height:2px;background:{nav_hb};border-radius:2px;display:block;transition:all 0.3s}}
nav.solid .hb span{{background:var(--tx)}}
.hb.o span:nth-child(1){{transform:translateY(7px) rotate(45deg)}}
.hb.o span:nth-child(2){{opacity:0}}
.hb.o span:nth-child(3){{transform:translateY(-7px) rotate(-45deg)}}
.mob{{display:none;position:fixed;inset:0;z-index:999;background:{mob_bg};backdrop-filter:blur(30px);flex-direction:column;align-items:center;justify-content:center;gap:28px}}
.mob.o{{display:flex}}
.mob a{{font-size:1.6rem;font-weight:700;color:var(--tx);text-decoration:none;transition:color 0.2s}}
.mob a:hover{{color:var(--pr)}}
.mob .xb{{position:absolute;top:22px;right:24px;background:none;border:none;color:var(--tx);font-size:1.9rem;cursor:pointer}}
.hero{{min-height:100vh;display:flex;align-items:center;padding:100px 5% 80px;position:relative;overflow:hidden}}
.hbg{{position:absolute;inset:0;background:url("{imgs["h"]}") center/cover no-repeat;opacity:{"0.13" if is_dark else "0.07"};filter:blur(2px);transform:scale(1.08);transition:transform 0.1s linear}}
.hov{{position:absolute;inset:0;background:{hero_ov}}}
.hg1{{position:absolute;top:-25%;right:-8%;width:700px;height:700px;border-radius:50%;background:radial-gradient(circle,{ds["pr"]}{"1E" if is_dark else "0D"} 0%,transparent 70%);pointer-events:none}}
.hg2{{position:absolute;bottom:-20%;left:-5%;width:500px;height:500px;border-radius:50%;background:radial-gradient(circle,{ds["ac"]}{"14" if is_dark else "09"} 0%,transparent 70%);pointer-events:none}}
.hin{{position:relative;z-index:2;max-width:1280px;margin:0 auto;width:100%;display:grid;grid-template-columns:1fr 1fr;gap:80px;align-items:center}}
.badge{{display:inline-flex;align-items:center;gap:8px;background:{"rgba(255,255,255,0.1)" if is_dark else ds["ca"]};backdrop-filter:blur(12px);border:1px solid var(--br);padding:8px 20px;border-radius:100px;font-size:0.72rem;font-weight:700;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:20px;animation:fadeUp 0.6s ease both;color:var(--tx)}}
.dot{{width:8px;height:8px;border-radius:50%;background:var(--ac);animation:pulse 2s infinite;box-shadow:0 0 10px var(--ac)}}
.htitle{{font-family:"{f1}",serif;font-size:clamp(2.6rem,4.5vw,4.5rem);font-weight:900;line-height:1.06;letter-spacing:-2px;margin-bottom:16px;color:var(--tx);animation:fadeUp 0.7s ease 0.1s both}}
.hac{{color:var(--pr);display:block;font-style:italic}}
.hsub{{font-size:1rem;color:var(--mu);line-height:1.78;margin-bottom:28px;max-width:480px;animation:fadeUp 0.7s ease 0.2s both}}
.hcbar{{display:flex;gap:20px;flex-wrap:wrap;margin-bottom:28px;animation:fadeUp 0.7s ease 0.25s both}}
.hci{{display:flex;align-items:center;gap:8px;font-size:0.84rem;color:var(--mu)}}
.hci a{{color:var(--pr);text-decoration:none;font-weight:600}}
.hbtns{{display:flex;gap:14px;flex-wrap:wrap;animation:fadeUp 0.7s ease 0.3s both}}
.bp{{display:inline-flex;align-items:center;gap:8px;background:var(--pr);color:#fff;font-weight:800;font-size:0.88rem;padding:15px 30px;border-radius:100px;text-decoration:none;transition:all 0.3s;box-shadow:0 8px 30px rgba(0,0,0,0.2)}}
.bp:hover{{transform:translateY(-3px);filter:brightness(1.1);box-shadow:0 16px 40px rgba(0,0,0,0.3)}}
.bs{{display:inline-flex;align-items:center;gap:8px;background:var(--ca);color:var(--tx);font-weight:700;font-size:0.88rem;padding:15px 30px;border-radius:100px;text-decoration:none;border:1px solid var(--br);transition:all 0.3s}}
.bs:hover{{transform:translateY(-3px)}}
.bwa{{display:inline-flex;align-items:center;gap:8px;background:#25D366;color:#fff;font-weight:700;font-size:0.88rem;padding:15px 22px;border-radius:100px;text-decoration:none;transition:all 0.3s}}
.bwa:hover{{transform:translateY(-3px);filter:brightness(1.1)}}
.hiw{{position:relative;perspective:1200px;animation:fadeRight 0.9s ease 0.2s both}}
.hic{{border-radius:24px;overflow:hidden;box-shadow:{shadow},0 0 0 1px var(--br);transform:rotateY(-6deg) rotateX(3deg);transition:transform 0.7s ease;animation:float 6s ease-in-out infinite}}
.hic:hover{{transform:rotateY(0) rotateX(0)}}
.hic img{{width:100%;height:440px;object-fit:cover;display:block}}
.hib{{position:absolute;bottom:20px;left:20px;background:rgba(0,0,0,0.75);backdrop-filter:blur(20px);border:1px solid rgba(255,255,255,0.15);padding:12px 18px;border-radius:14px;display:flex;align-items:center;gap:10px}}
.ldot{{width:8px;height:8px;border-radius:50%;background:#22C55E;box-shadow:0 0 10px #22C55E;animation:pulse 2s infinite}}
.ltext{{color:#fff;font-size:0.74rem;font-weight:600}}
.statbar{{padding:0 5%;border-top:1px solid var(--br);border-bottom:1px solid var(--br);background:{"rgba(0,0,0,0.4)" if is_dark else ds["ca"]}}}
.stin{{max-width:1280px;margin:0 auto;display:grid;grid-template-columns:repeat(4,1fr)}}
.sti{{padding:32px 20px;text-align:center;border-right:1px solid var(--br);transition:background 0.3s;cursor:default}}
.sti:last-child{{border-right:none}}
.sti:hover{{background:var(--ca)}}
.sn{{font-family:"{f1}",serif;font-size:2.4rem;font-weight:900;color:var(--pr);margin-bottom:4px;line-height:1}}
.sl{{font-size:0.7rem;color:var(--mu);font-weight:600;text-transform:uppercase;letter-spacing:1.2px}}
section{{padding:100px 5%}}
.sec{{max-width:1280px;margin:0 auto}}
.lbl{{display:inline-flex;align-items:center;gap:8px;background:var(--ca);color:var(--pr);font-size:0.7rem;font-weight:800;text-transform:uppercase;letter-spacing:2px;padding:7px 17px;border-radius:100px;margin-bottom:18px;border:1px solid var(--br)}}
.sh{{font-family:"{f1}",serif;font-size:clamp(1.8rem,3vw,2.8rem);font-weight:900;color:var(--tx);line-height:1.15;letter-spacing:-1px;margin-bottom:14px}}
.sh span{{color:var(--pr)}}
.sb{{font-size:0.93rem;color:var(--mu);line-height:1.78;max-width:520px}}
.ag{{display:grid;grid-template-columns:1fr 1fr;gap:80px;align-items:center}}
.aimg{{border-radius:24px;overflow:hidden;position:relative;box-shadow:{shadow}}}
.aimg img{{width:100%;height:500px;object-fit:cover;display:block;transition:transform 0.7s}}
.aimg:hover img{{transform:scale(1.05)}}
.atag{{position:absolute;top:20px;left:20px;background:var(--pr);color:#fff;font-size:0.7rem;font-weight:800;padding:8px 16px;border-radius:100px;text-transform:uppercase;letter-spacing:1px}}
.afs{{display:flex;flex-direction:column;gap:14px;margin-top:28px}}
.af{{display:flex;align-items:flex-start;gap:14px;padding:17px;background:var(--ca);border-radius:16px;border:1px solid var(--br);transition:all 0.3s;cursor:default}}
.afi{{width:44px;height:44px;border-radius:12px;background:{"rgba(255,255,255,0.06)" if is_dark else "#fff"};border:1px solid var(--br);display:flex;align-items:center;justify-content:center;font-size:1.3rem;flex-shrink:0}}
.aft h4{{font-weight:700;font-size:0.87rem;color:var(--tx);margin-bottom:3px}}
.aft p{{font-size:0.78rem;color:var(--mu);line-height:1.5}}
.sg{{display:grid;grid-template-columns:repeat(2,1fr);gap:20px;margin-top:20px}}
.sc{{background:var(--bg);border:1px solid var(--br);border-radius:24px;padding:36px;transition:all 0.4s;position:relative;overflow:hidden;cursor:default}}
.sc::before{{content:"";position:absolute;inset:0;background:linear-gradient(135deg,var(--pr),transparent);opacity:0;transition:opacity 0.4s}}
.sc:hover::before{{opacity:0.04}}
.si{{font-size:2.8rem;margin-bottom:18px;display:block}}
.sc h3{{font-family:"{f1}",serif;font-size:1.2rem;font-weight:800;color:var(--tx);margin-bottom:10px}}
.sc p{{font-size:0.86rem;color:var(--mu);line-height:1.7}}
.gg{{display:grid;grid-template-columns:repeat(2,1fr);gap:16px;margin-top:40px}}
.gi{{border-radius:20px;overflow:hidden;aspect-ratio:4/3;position:relative;cursor:pointer}}
.gi img{{width:100%;height:100%;object-fit:cover;display:block;transition:transform 0.6s}}
.go{{position:absolute;inset:0;background:linear-gradient(to top,rgba(0,0,0,0.65),transparent);opacity:0;transition:opacity 0.3s;display:flex;align-items:flex-end;padding:20px}}
.go span{{color:#fff;font-weight:700;font-size:0.88rem}}
.gi:hover .go{{opacity:1}}
.tg{{display:grid;grid-template-columns:repeat(3,1fr);gap:20px;margin-top:40px}}
.tc{{background:var(--bg);border:1px solid var(--br);border-radius:24px;padding:32px;transition:all 0.3s;position:relative;overflow:hidden;cursor:default}}
.tc::before{{content:"\\201C";position:absolute;top:-18px;right:14px;font-size:7.5rem;color:var(--pr);opacity:0.06;font-family:serif;line-height:1}}
.ts{{color:var(--ac);font-size:0.9rem;letter-spacing:3px;margin-bottom:14px}}
.tt{{font-size:0.87rem;color:var(--mu);line-height:1.75;margin-bottom:20px;font-style:italic}}
.ta{{display:flex;align-items:center;gap:12px}}
.av{{width:44px;height:44px;border-radius:50%;background:linear-gradient(135deg,var(--pr),var(--ac));display:flex;align-items:center;justify-content:center;color:#fff;font-weight:800;font-size:0.9rem;flex-shrink:0}}
.an{{font-weight:700;font-size:0.84rem;color:var(--tx)}}
.ar{{font-size:0.72rem;color:var(--mu)}}
.fqi{{border-bottom:1px solid var(--br)}}
.fqb{{width:100%;background:none;border:none;cursor:pointer;padding:18px 0;display:flex;justify-content:space-between;align-items:center;gap:16px;text-align:left}}
.fqq{{font-weight:700;font-size:0.93rem;color:var(--tx)}}
.fqi2{{font-size:1.3rem;color:var(--pr);flex-shrink:0;transition:transform 0.3s}}
.fqa{{display:none;padding-bottom:14px}}
.fqa p{{color:var(--mu);font-size:0.86rem;line-height:1.75}}
.ccg{{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:16px;margin-bottom:32px;margin-top:40px}}
.cc{{background:var(--bg);border:1px solid var(--br);border-radius:20px;padding:22px;text-align:center}}
.cci{{font-size:1.8rem;margin-bottom:10px}}
.cc h4{{font-weight:700;font-size:0.83rem;color:var(--tx);margin-bottom:6px}}
.cc a,.cc p{{color:var(--pr);text-decoration:none;font-size:0.8rem;font-weight:600;display:block;line-height:1.4}}
.cc p{{color:var(--mu);font-weight:400}}
.cf{{background:var(--bg);border:1px solid var(--br);border-radius:24px;padding:34px}}
.fgrid{{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:16px}}
.fg2{{display:flex;flex-direction:column;gap:6px}}
.fg2 label{{font-size:0.77rem;font-weight:600;color:var(--mu)}}
.fg2 input,.fg2 textarea,.fg2 select{{padding:12px 15px;background:{inp};border:1px solid var(--br);border-radius:12px;color:var(--tx);font-size:0.87rem;outline:none;transition:border-color 0.2s;font-family:"{f2}",sans-serif;width:100%}}
.fg2 input:focus,.fg2 textarea:focus{{border-color:var(--pr)}}
.fg2 textarea{{resize:vertical;min-height:96px}}
.fs{{display:none;background:#dcfce7;border:1px solid #a7f3d0;border-radius:12px;padding:14px;text-align:center;color:#065f46;font-weight:600;margin-top:12px}}
.nlf{{display:flex;gap:12px;max-width:480px;margin:22px auto 0;flex-wrap:wrap}}
.nlf input{{flex:1;min-width:170px;padding:13px 19px;background:{inp};border:1px solid var(--br);border-radius:100px;color:var(--tx);font-size:0.87rem;outline:none}}
.nlf button{{background:var(--pr);color:#fff;border:none;padding:13px 24px;border-radius:100px;font-weight:800;font-size:0.87rem;cursor:pointer;white-space:nowrap;transition:all 0.3s}}
.nlf button:hover{{filter:brightness(1.1)}}
.ctab{{max-width:960px;margin:0 auto;background:linear-gradient(135deg,var(--pr),var(--ac));border-radius:32px;padding:70px 55px;text-align:center;position:relative;overflow:hidden;box-shadow:0 40px 80px rgba(0,0,0,0.25)}}
.ctab::before{{content:"";position:absolute;top:-40%;right:-8%;width:500px;height:500px;border-radius:50%;background:rgba(255,255,255,0.07);pointer-events:none}}
.ctab h2{{font-family:"{f1}",serif;font-size:clamp(1.8rem,3.5vw,2.8rem);font-weight:900;color:#fff;margin-bottom:14px;position:relative;z-index:1;letter-spacing:-1px}}
.ctab p{{color:rgba(255,255,255,0.85);font-size:0.93rem;margin-bottom:30px;position:relative;z-index:1;max-width:480px;margin-left:auto;margin-right:auto}}
.cbtns{{display:flex;gap:14px;justify-content:center;flex-wrap:wrap;position:relative;z-index:1}}
.cb1{{background:#fff;color:var(--pr);font-weight:800;padding:14px 32px;border-radius:100px;text-decoration:none;font-size:0.88rem;transition:all 0.3s;box-shadow:0 8px 30px rgba(0,0,0,0.15)}}
.cb1:hover{{transform:translateY(-3px)}}
.cb2{{background:rgba(255,255,255,0.15);color:#fff;font-weight:700;padding:14px 32px;border-radius:100px;text-decoration:none;font-size:0.88rem;border:1px solid rgba(255,255,255,0.3);transition:all 0.3s}}
.cb2:hover{{background:rgba(255,255,255,0.25);transform:translateY(-3px)}}
.ftgrid{{display:grid;grid-template-columns:2fr 1fr 1fr 1fr;gap:44px;max-width:1280px;margin:0 auto 36px}}
.fbr p{{font-size:0.8rem;color:var(--mu);margin-top:12px;line-height:1.7;max-width:220px}}
.flogo{{font-family:"{f1}",serif;font-size:1.6rem;font-weight:900;color:var(--pr)}}
.fsoc{{display:flex;gap:10px;margin-top:16px;flex-wrap:wrap}}
.fsoc a{{width:36px;height:36px;border-radius:10px;background:var(--ca);border:1px solid var(--br);display:flex;align-items:center;justify-content:center;text-decoration:none;font-size:1rem;transition:all 0.3s}}
.fsoc a:hover{{background:var(--pr);transform:translateY(-2px)}}
.fc h4{{font-weight:700;font-size:0.72rem;color:var(--mu);text-transform:uppercase;letter-spacing:1.5px;margin-bottom:16px}}
.fc a{{display:block;color:var(--mu);text-decoration:none;font-size:0.8rem;margin-bottom:10px;transition:color 0.2s}}
.fc a:hover{{color:var(--pr)}}
.fbot{{max-width:1280px;margin:0 auto;border-top:1px solid var(--br);padding-top:22px;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px}}
.fbot p{{font-size:0.74rem;color:var(--mu)}}
.fbot a{{color:var(--mu);text-decoration:none;font-size:0.7rem;margin-left:14px}}
.fbot a:hover{{color:var(--pr)}}
.wab{{position:fixed;bottom:24px;right:24px;z-index:9999;width:58px;height:58px;background:#25D366;border-radius:50%;display:flex;align-items:center;justify-content:center;text-decoration:none;animation:waP 2s infinite;transition:transform 0.3s;box-shadow:0 8px 30px rgba(37,211,102,0.4)}}
.wab:hover{{transform:scale(1.12)}}
.scta{{position:fixed;bottom:0;left:0;right:0;z-index:9990;background:var(--nb);backdrop-filter:blur(22px);border-top:1px solid var(--br);padding:12px 5%;display:flex;align-items:center;justify-content:space-between;gap:16px;transform:translateY(100%);transition:transform 0.4s ease;flex-wrap:wrap}}
.scta-t p:first-child{{font-weight:700;font-size:0.87rem;color:var(--tx)}}
.scta-t p:last-child{{font-size:0.74rem;color:var(--mu)}}
.scta-b{{display:flex;gap:10px}}
.scta-b a{{padding:10px 20px;border-radius:100px;text-decoration:none;font-weight:700;font-size:0.82rem;transition:all 0.3s}}
.sb1{{background:var(--ca);color:var(--tx);border:1px solid var(--br)}}
.sb2{{background:var(--pr);color:#fff}}
#btt{{position:fixed;bottom:90px;right:24px;z-index:9980;width:42px;height:42px;background:var(--pr);color:#fff;border:none;border-radius:50%;cursor:pointer;font-size:1.1rem;display:none;align-items:center;justify-content:center;box-shadow:0 4px 20px rgba(0,0,0,0.2);transition:all 0.3s}}
#btt:hover{{transform:translateY(-3px)}}
.ckb{{position:fixed;bottom:0;left:0;right:0;z-index:9970;background:{ck_glow};color:#fff;padding:14px 5%;display:flex;align-items:center;justify-content:space-between;gap:16px;flex-wrap:wrap;transition:transform 0.4s}}
.ckb.h{{transform:translateY(100%)}}
.ckb p{{font-size:0.8rem;color:rgba(255,255,255,0.78);max-width:600px}}
.ckbs{{display:flex;gap:10px}}
.cka{{background:var(--pr);color:#fff;border:none;padding:10px 20px;border-radius:100px;font-weight:700;font-size:0.8rem;cursor:pointer}}
.ckd{{background:rgba(255,255,255,0.1);color:#fff;border:1px solid rgba(255,255,255,0.2);padding:10px 20px;border-radius:100px;font-weight:600;font-size:0.8rem;cursor:pointer}}
.rev{{opacity:0;transform:translateY(40px) scale(0.97);transition:opacity 0.7s ease,transform 0.7s ease}}
.rev.vis{{opacity:1;transform:translateY(0) scale(1)}}
@media(max-width:900px){{
  .hin,.ag{{grid-template-columns:1fr;gap:48px;text-align:center}}
  .hiw{{order:-1}}.hsub{{max-width:100%}}.hbtns,.hcbar{{justify-content:center}}
  .sg,.gg{{grid-template-columns:1fr}}
  .tg{{grid-template-columns:1fr}}
  .stin{{grid-template-columns:repeat(2,1fr)}}
  .ftgrid{{grid-template-columns:1fr 1fr;gap:28px}}
  .lks,.nbtn{{display:none}}.hb{{display:flex}}
  .ctab{{padding:48px 28px}}.sb{{max-width:100%}}
  .fgrid{{grid-template-columns:1fr}}
}}
@media(max-width:540px){{
  .stin,.ftgrid{{grid-template-columns:1fr}}
  .htitle{{font-size:2.4rem}}.fbot{{flex-direction:column;text-align:center}}
}}
</style>
</head>
<body>

<div id="ldr"><div class="ldr-logo">{name}</div><div class="ldr-ring"></div></div>

<div class="mob" id="mob">
  <button class="xb" onclick="cm()">&#10005;</button>
  <a href="#about" onclick="cm()">About</a>
  <a href="#services" onclick="cm()">Services</a>
  <a href="#gallery" onclick="cm()">Gallery</a>
  <a href="#testimonials" onclick="cm()">Reviews</a>
  <a href="#faq" onclick="cm()">FAQ</a>
  <a href="#contact" onclick="cm()" style="background:var(--pr);color:#fff;padding:14px 32px;border-radius:100px">Get Started &#8594;</a>
</div>

<nav id="nav">
  <div class="ni">
    <a href="#" class="logo">{name}</a>
    <ul class="lks">
      <li><a href="#about">About</a></li>
      <li><a href="#services">Services</a></li>
      <li><a href="#gallery">Gallery</a></li>
      <li><a href="#testimonials">Reviews</a></li>
      <li><a href="#faq">FAQ</a></li>
    </ul>
    <a href="#contact" class="nbtn">Get Started &#8594;</a>
    <button class="hb" id="hb" onclick="tm()"><span></span><span></span><span></span></button>
  </div>
</nav>

<section class="hero" id="home">
  <div class="hbg" id="pbg"></div>
  <div class="hov"></div>
  <div class="hg1"></div><div class="hg2"></div>
  <div class="hin">
    <div>
      <div class="badge"><span class="dot"></span>&#10022; {name} &middot; Premium</div>
      <h1 class="htitle">{name}<span class="hac">{tagline}</span></h1>
      <p class="hsub">{con["sub"]}</p>
      <div class="hcbar">
        <div class="hci">&#128222; <a href="tel:{phone}">{phone}</a></div>
        <div class="hci">&#9993; <a href="mailto:{email_addr}">{email_addr}</a></div>
      </div>
      <div class="hbtns">
        <a href="#contact" class="bp">{con["cta1"]} &#8594;</a>
        <a href="#services" class="bs">&#9654; {con["cta2"]}</a>
        <a href="https://wa.me/{wa}" target="_blank" class="bwa">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="white"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/></svg>
          WhatsApp
        </a>
      </div>
    </div>
    <div class="hiw">
      <div class="hic">
        <img src="{imgs["h"]}" alt="{name}" loading="eager"/>
        <div class="hib"><div class="ldot"></div><span class="ltext">Live &middot; {hours}</span></div>
      </div>
    </div>
  </div>
</section>

<div class="statbar"><div class="stin">{stats}</div></div>

<section id="about" style="background:var(--bg)">
  <div class="sec">
    <div class="ag">
      <div class="aimg rev">
        <img src="{imgs["a"]}" alt="About {name}" loading="lazy"/>
        <div class="atag">Our Story</div>
      </div>
      <div class="rev">
        <div class="lbl">&#10022; About Us</div>
        <h2 class="sh">Built for <span>Excellence</span>.</h2>
        <p class="sb">{about_text}</p>
        <div class="afs">{afs}</div>
      </div>
    </div>
  </div>
</section>

<section id="services" style="background:{svc_bg}">
  <div class="sec">
    <div style="text-align:center;margin-bottom:40px">
      <div class="lbl">&#10022; {con["sv_title"]}</div>
      <h2 class="sh" style="text-align:center">Why Choose <span>{name}</span></h2>
      <p class="sb" style="margin:10px auto 0;text-align:center">Everything delivered to the highest possible standard. Nothing less.</p>
    </div>
    <div class="sg rev">{svcs}</div>
  </div>
</section>

<section id="gallery" style="background:var(--bg)">
  <div class="sec">
    <div style="text-align:center;margin-bottom:20px">
      <div class="lbl">&#10022; Gallery</div>
      <h2 class="sh" style="text-align:center">See It For <span>Yourself</span></h2>
    </div>
    <div class="gg rev">{gals}</div>
  </div>
</section>

<section id="testimonials" style="background:{svc_bg}">
  <div class="sec">
    <div style="text-align:center;margin-bottom:20px">
      <div class="lbl">&#10022; Reviews</div>
      <h2 class="sh" style="text-align:center">What Our <span>Clients Say</span></h2>
    </div>
    <div class="tg rev">{testis}</div>
  </div>
</section>

<section id="faq" style="background:var(--bg)">
  <div class="sec" style="max-width:800px">
    <div style="text-align:center;margin-bottom:40px">
      <div class="lbl">&#10022; FAQ</div>
      <h2 class="sh" style="text-align:center">Frequently Asked <span>Questions</span></h2>
    </div>
    <div class="rev">
      <div class="fqi"><button class="fqb" onclick="fq(this)"><span class="fqq">How do I get started with {name}?</span><span class="fqi2">+</span></button><div class="fqa"><p>Simply contact us through the form below, call us, or send a WhatsApp message. We respond within 24 hours and set up a free initial consultation to understand exactly what you need.</p></div></div>
      <div class="fqi"><button class="fqb" onclick="fq(this)"><span class="fqq">What is your pricing and how does it work?</span><span class="fqi2">+</span></button><div class="fqa"><p>Our pricing is completely transparent and competitive, always tailored to your specific requirements. Contact us for a personalised quote - no hidden fees, no surprises, ever.</p></div></div>
      <div class="fqi"><button class="fqb" onclick="fq(this)"><span class="fqq">How long does the process typically take?</span><span class="fqi2">+</span></button><div class="fqa"><p>Timelines depend entirely on the scope of your project. We are known throughout the industry for fast, reliable delivery and will give you a completely clear timeline upfront before any work begins.</p></div></div>
      <div class="fqi"><button class="fqb" onclick="fq(this)"><span class="fqq">Do you offer ongoing support after completion?</span><span class="fqi2">+</span></button><div class="fqa"><p>Absolutely, and we pride ourselves on building long-term relationships with every client. Ongoing support, maintenance, and continued assistance are always available to you.</p></div></div>
      <div class="fqi"><button class="fqb" onclick="fq(this)"><span class="fqq">What areas and regions do you serve?</span><span class="fqi2">+</span></button><div class="fqa"><p>We proudly serve clients across all of India and internationally. Whether in-person or fully remote, we adapt completely and seamlessly to your location and needs.</p></div></div>
      <div class="fqi"><button class="fqb" onclick="fq(this)"><span class="fqq">Can I see examples of your previous work?</span><span class="fqi2">+</span></button><div class="fqa"><p>Absolutely. Check out our gallery section above, or contact us directly and we will share a comprehensive portfolio of our most relevant previous work and detailed case studies.</p></div></div>
    </div>
  </div>
</section>

<section id="contact" style="background:{svc_bg}">
  <div class="sec">
    <div style="text-align:center;margin-bottom:20px">
      <div class="lbl">&#10022; Contact Us</div>
      <h2 class="sh" style="text-align:center">Get In <span>Touch</span></h2>
      <p class="sb" style="margin:10px auto;text-align:center">We would absolutely love to hear from you. Reach out through any channel below.</p>
    </div>
    <div class="ccg rev">
      <div class="cc"><div class="cci">&#128222;</div><h4>Call Us</h4><a href="tel:{phone}">{phone}</a></div>
      <div class="cc"><div class="cci">&#9993;</div><h4>Email Us</h4><a href="mailto:{email_addr}" style="word-break:break-all;font-size:0.76rem">{email_addr}</a></div>
      <div class="cc"><div class="cci">&#128205;</div><h4>Visit Us</h4><p>{address}</p></div>
      <div class="cc"><div class="cci">&#9200;</div><h4>Hours</h4><p>{hours}</p></div>
      <div class="cc"><div class="cci">&#128172;</div><h4>WhatsApp</h4><a href="https://wa.me/{wa}" target="_blank">Chat Now &#8594;</a></div>
    </div>
    <div class="cf rev">
      <h3 style="font-family:'{f1}',serif;font-size:1.25rem;font-weight:800;color:var(--tx);margin-bottom:22px">Send Us a Message</h3>
      <form onsubmit="hf(event)">
        <div class="fgrid">
          <div class="fg2"><label>Full Name *</label><input type="text" placeholder="Your full name" required/></div>
          <div class="fg2"><label>Phone Number *</label><input type="tel" placeholder="+91 00000 00000" required/></div>
        </div>
        <div class="fg2" style="margin-bottom:16px"><label>Email Address</label><input type="email" placeholder="your@email.com"/></div>
        <div class="fg2" style="margin-bottom:16px"><label>Subject</label><input type="text" placeholder="How can we help you?"/></div>
        <div class="fg2" style="margin-bottom:20px"><label>Your Message</label><textarea rows="4" placeholder="Tell us more about your requirements and how we can help..."></textarea></div>
        <button type="submit" class="bp" style="border:none;cursor:pointer">Send Message &#8594;</button>
        <div class="fs" id="fs">&#10003; Thank you! We will contact you within 24 hours.</div>
      </form>
    </div>
    <div style="margin-top:32px;border-radius:24px;overflow:hidden;border:1px solid var(--br)" class="rev">
      <iframe src="https://maps.google.com/maps?q={map_q}&output=embed" width="100%" height="340" style="border:0;display:block" allowfullscreen loading="lazy"></iframe>
    </div>
  </div>
</section>

<section id="newsletter" style="background:var(--bg);padding:80px 5%">
  <div style="max-width:580px;margin:0 auto;text-align:center" class="rev">
    <div style="font-size:2.4rem;margin-bottom:12px">&#128140;</div>
    <div class="lbl" style="margin:0 auto 16px">&#10022; Newsletter</div>
    <h2 class="sh" style="text-align:center">Stay in the <span>Loop</span></h2>
    <p style="color:var(--mu);font-size:0.9rem;margin-top:8px">Get the latest updates, exclusive offers, and insights delivered straight to your inbox.</p>
    <form class="nlf" onsubmit="hnl(event)">
      <input type="email" placeholder="Enter your email address" required/>
      <button type="submit">Subscribe &#8594;</button>
    </form>
    <div id="nls" style="display:none;margin-top:14px;color:var(--pr);font-weight:600">&#10003; Subscribed! Welcome to our community.</div>
    <p style="color:var(--mu);font-size:0.72rem;margin-top:12px">No spam ever. Unsubscribe anytime with one click.</p>
  </div>
</section>

<section style="padding:80px 5%;background:{svc_bg}">
  <div class="ctab rev">
    <h2>Ready to Get Started?</h2>
    <p>Join hundreds who already trust {name}. Your first consultation is completely free.</p>
    <div class="cbtns">
      <a href="#contact" class="cb1">{con["cta1"]} &#8594;</a>
      <a href="tel:{phone}" class="cb2">&#128222; {phone}</a>
    </div>
  </div>
</section>

<footer style="padding:60px 5% 90px;border-top:1px solid var(--br);background:{svc_bg}">
  <div class="ftgrid">
    <div class="fbr">
      <div class="flogo">{name}</div>
      <p>{con["sub"][:100]}...</p>
      <div class="fsoc">{social_links}</div>
    </div>
    <div class="fc">
      <h4>Company</h4>
      <a href="#about">About Us</a>
      <a href="#services">{con["sv_title"]}</a>
      <a href="#gallery">Gallery</a>
      <a href="#testimonials">Reviews</a>
      <a href="#faq">FAQ</a>
    </div>
    <div class="fc">
      <h4>Services</h4>
      {footer_svcs}
    </div>
    <div class="fc">
      <h4>Contact</h4>
      <a href="tel:{phone}">&#128222; {phone}</a>
      <a href="mailto:{email_addr}">&#9993; Email Us</a>
      <a href="https://wa.me/{wa}" target="_blank">&#128172; WhatsApp</a>
      <a href="#contact">&#128205; {address[:32]}...</a>
      <p style="color:var(--mu);font-size:0.74rem;margin-top:7px">&#9200; {hours}</p>
    </div>
  </div>
  <div class="fbot">
    <p>&#169; 2024 {name}. All rights reserved.</p>
    <div><a href="#">Privacy Policy</a><a href="#">Terms of Service</a><a href="#">Sitemap</a></div>
    <p>Built with <a href="https://dacexy.vercel.app" style="color:var(--pr)">Dacexy AI</a></p>
  </div>
</footer>

<a href="https://wa.me/{wa}" class="wab" target="_blank" title="Chat on WhatsApp">
  <svg width="28" height="28" viewBox="0 0 24 24" fill="white"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/></svg>
</a>

<div class="scta" id="scta">
  <div class="scta-t"><p>Ready to work with {name}?</p><p>Free consultation - contact us today.</p></div>
  <div class="scta-b">
    <a href="tel:{phone}" class="scta-b sb1">&#128222; Call</a>
    <a href="#contact" class="scta-b sb2" onclick="document.getElementById('scta').style.transform='translateY(100%)'">Get Started &#8594;</a>
  </div>
</div>

<button id="btt" onclick="window.scrollTo({{top:0,behavior:'smooth'}})">&#8593;</button>

<div class="ckb" id="ckb">
  <p>&#127850; We use cookies to enhance your browsing experience. By continuing, you agree to our <a href="#" style="color:var(--pr)">Privacy Policy</a>.</p>
  <div class="ckbs">
    <button class="cka" onclick="acc()">Accept All</button>
    <button class="ckd" onclick="acc()">Decline</button>
  </div>
</div>

<script>
window.addEventListener('load',function(){{setTimeout(function(){{document.getElementById('ldr').classList.add('out');}},700);}});
var nav=document.getElementById('nav'),scta=document.getElementById('scta'),btt=document.getElementById('btt');
window.addEventListener('scroll',function(){{
  var y=window.scrollY;
  nav.classList.toggle('solid',y>60);
  scta.style.transform=y>400?'translateY(0)':'translateY(100%)';
  btt.style.display=y>500?'flex':'none';
  document.querySelectorAll('.lks a').forEach(function(a){{
    var s=document.querySelector(a.getAttribute('href'));
    if(s){{var r=s.getBoundingClientRect();a.classList.toggle('active',r.top<=100&&r.bottom>100);}}
  }});
  var pb=document.getElementById('pbg');
  if(pb)pb.style.transform='scale(1.08) translateY('+(y*0.28)+'px)';
}});
function tm(){{var m=document.getElementById('mob'),h=document.getElementById('hb');m.classList.toggle('o');h.classList.toggle('o');document.body.style.overflow=m.classList.contains('o')?'hidden':'';}}
function cm(){{document.getElementById('mob').classList.remove('o');document.getElementById('hb').classList.remove('o');document.body.style.overflow='';}}
var ro=new IntersectionObserver(function(e){{e.forEach(function(x){{if(x.isIntersecting){{x.target.classList.add('vis');ro.unobserve(x.target);}}}});}},{{threshold:0.08,rootMargin:'0px 0px -40px 0px'}});
document.querySelectorAll('.rev').forEach(function(el){{ro.observe(el);}});
function fq(b){{var a=b.nextElementSibling,i=b.querySelector('.fqi2'),op=a.style.display==='block';document.querySelectorAll('.fqa').forEach(function(x){{x.style.display='none';}});document.querySelectorAll('.fqi2').forEach(function(x){{x.textContent='+';x.style.transform='';}});if(!op){{a.style.display='block';i.textContent='-';i.style.transform='rotate(45deg)';}}}}
function hf(e){{e.preventDefault();var b=e.target.querySelector('button[type="submit"]');b.innerHTML='Sending...';b.disabled=true;setTimeout(function(){{b.innerHTML='Sent!';document.getElementById('fs').style.display='block';e.target.reset();setTimeout(function(){{b.innerHTML='Send Message';b.disabled=false;document.getElementById('fs').style.display='none';}},4000);}},1500);}}
function hnl(e){{e.preventDefault();document.getElementById('nls').style.display='block';e.target.reset();}}
function acc(){{document.getElementById('ckb').classList.add('h');localStorage.setItem('ck','1');}}
if(localStorage.getItem('ck'))document.getElementById('ckb').classList.add('h');
document.querySelectorAll('input,textarea').forEach(function(el){{el.addEventListener('focus',function(){{el.style.borderColor='var(--pr)';}});el.addEventListener('blur',function(){{el.style.borderColor='';}});}});
document.querySelectorAll('img[loading="lazy"]').forEach(function(img){{img.style.opacity='0';img.style.transition='opacity 0.5s ease';img.addEventListener('load',function(){{img.style.opacity='1';}});if(img.complete)img.style.opacity='1';}});
</script>
</body>
</html>"""

# ── MAIN ENTRY POINT ──────────────────────────────────────────────────────────
async def generate_website(prompt: str, ai=None) -> str:
    name = extract_name(prompt)
    ud = extract_user_data(prompt)

    if ai is not None and needs_ai_generation(prompt):
        try:
            log.info(f"Using AI for custom website: {prompt[:60]}")
            ai_prompt = build_ai_prompt(prompt, name, ud)
            messages = [
                {"role": "system", "content": "You are an expert web developer. Generate complete, stunning HTML websites. Output ONLY raw HTML starting with <!DOCTYPE html>. No markdown, no explanation, no code blocks."},
                {"role": "user", "content": ai_prompt}
            ]
            result = await ai.chat(messages, model="deepseek-chat", stream=False, search=False)
            if isinstance(result, str):
                html = result.strip()
                if html.startswith("```"):
                    html = re.sub(r'```[a-z]*\n?', '', html).strip().rstrip('`').strip()
                if "<!DOCTYPE" in html or "<html" in html:
                    start = html.find("<!DOCTYPE")
                    if start == -1:
                        start = html.find("<html")
                    return html[start:] if start >= 0 else html
        except Exception as e:
            log.warning(f"AI generation failed, using premium template: {e}")

    log.info(f"Using premium template for: {prompt[:60]}")
    return build_template(prompt, name, ud)
''')


w("src/interfaces/http/routes/auth.py", """
import secrets
import re
import time
from datetime import datetime, timedelta
from collections import defaultdict
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import httpx
from src.infrastructure.persistence.database import get_db
from src.infrastructure.persistence.models.orm_models import User, Organization, RefreshToken
from src.infrastructure.email.email_service import EmailService
from src.interfaces.http.dependencies.container import get_email
from src.shared.security.auth import hash_password, verify_password, create_access_token, create_refresh_token, decode_access_token
from src.shared.config.settings import settings
import logging

log = logging.getLogger("auth")
router = APIRouter(prefix="/auth", tags=["auth"])
bearer = HTTPBearer(auto_error=False)

# ═══════════════════════════════════════════════════════════
# RATE LIMITING
# ═══════════════════════════════════════════════════════════

_rate_store: dict = defaultdict(lambda: {"count": 0, "window_start": 0.0, "blocked_until": 0.0})

RATE_LIMITS = {
    "register":   {"rpm": 3,  "window": 60,  "block": 300},
    "login":      {"rpm": 10, "window": 60,  "block": 60},
    "login_fail": {"rpm": 5,  "window": 300, "block": 900},
    "google":     {"rpm": 10, "window": 60,  "block": 60},
    "verify":     {"rpm": 5,  "window": 60,  "block": 120},
    "default":    {"rpm": 30, "window": 60,  "block": 60},
}

def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()
    return request.client.host if request.client else "unknown"

def check_rate_limit(key: str, limit_type: str = "default") -> None:
    cfg = RATE_LIMITS.get(limit_type, RATE_LIMITS["default"])
    now = time.time()
    store = _rate_store[key]
    if store["blocked_until"] > now:
        wait = int(store["blocked_until"] - now)
        raise HTTPException(
            status_code=429,
            detail=f"Too many attempts. Please wait {wait} seconds.",
            headers={"Retry-After": str(wait)}
        )
    if now - store["window_start"] > cfg["window"]:
        store["count"] = 0
        store["window_start"] = now
    store["count"] += 1
    if store["count"] > cfg["rpm"]:
        store["blocked_until"] = now + cfg["block"]
        store["count"] = 0
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Please wait {cfg['block']} seconds.",
            headers={"Retry-After": str(cfg["block"])}
        )

_login_failures: dict = defaultdict(lambda: {"count": 0, "first_fail": 0.0, "blocked_until": 0.0})

def check_login_failures(email: str) -> None:
    now = time.time()
    record = _login_failures[email.lower()]
    if record["blocked_until"] > now:
        wait = int(record["blocked_until"] - now)
        raise HTTPException(
            status_code=429,
            detail=f"Account temporarily locked. Try again in {wait} seconds.",
            headers={"Retry-After": str(wait)}
        )
    if now - record["first_fail"] > 300:
        record["count"] = 0
        record["first_fail"] = now

def record_login_failure(email: str) -> None:
    now = time.time()
    record = _login_failures[email.lower()]
    if record["count"] == 0:
        record["first_fail"] = now
    record["count"] += 1
    if record["count"] >= 10:
        record["blocked_until"] = now + 3600
    elif record["count"] >= 5:
        record["blocked_until"] = now + 900
    elif record["count"] >= 3:
        record["blocked_until"] = now + 60

def clear_login_failures(email: str) -> None:
    _login_failures[email.lower()] = {"count": 0, "first_fail": 0.0, "blocked_until": 0.0}

# ═══════════════════════════════════════════════════════════
# MODELS
# ═══════════════════════════════════════════════════════════

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
    return slug + "-" + secrets.token_hex(4)

def _validate_password(password: str) -> None:
    if len(password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters.")
    if len(password) > 128:
        raise HTTPException(status_code=400, detail="Password is too long.")

def _validate_name(name: str) -> None:
    if len(name.strip()) < 2:
        raise HTTPException(status_code=400, detail="Full name must be at least 2 characters.")
    if len(name.strip()) > 100:
        raise HTTPException(status_code=400, detail="Full name is too long.")

# ═══════════════════════════════════════════════════════════
# AUTH DEPENDENCY
# ═══════════════════════════════════════════════════════════

async def _get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(bearer),
    db: AsyncSession = Depends(get_db)
):
    if not creds:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = decode_access_token(creds.credentials)
        user_id = payload["sub"]
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    # FIX: Always fetch fresh user from DB — never rely on token cache
    try:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
    except Exception:
        raise HTTPException(status_code=401, detail="Database error fetching user")

    if not user:
        raise HTTPException(status_code=401, detail="User not found. Please sign in again.")
    if not user.is_active:
        raise HTTPException(status_code=401, detail="Account disabled. Contact support.")
    return user

# ═══════════════════════════════════════════════════════════
# REGISTER
# ═══════════════════════════════════════════════════════════

@router.post("/register", response_model=TokenResponse)
async def register(
    body: RegisterRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    email_svc: EmailService = Depends(get_email)
):
    ip = get_client_ip(request)
    check_rate_limit(f"register:{ip}", "register")
    _validate_name(body.full_name)
    _validate_password(body.password)

    email_lower = body.email.lower().strip()
    existing = await db.execute(select(User).where(User.email == email_lower))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=409,
            detail="This email is already registered. Please sign in instead."
        )

    org_name = body.org_name.strip() if body.org_name.strip() else (body.full_name.strip().split()[0] + "'s Workspace")
    org = Organization(name=org_name, slug=_make_slug(org_name))
    db.add(org)
    await db.flush()

    user = User(
        org_id=org.id,
        email=email_lower,
        full_name=body.full_name.strip(),
        hashed_password=hash_password(body.password),
        role="owner",
        is_verified=True,
        metadata_={}
    )
    db.add(user)
    await db.flush()

    try:
        email_svc.send_verification_email(email_lower, "welcome")
    except Exception:
        pass

    access = create_access_token(str(user.id), {"org_id": str(org.id), "role": "owner"})
    refresh = create_refresh_token()
    db.add(RefreshToken(
        user_id=user.id,
        token_hash=hash_password(refresh),
        expires_at=datetime.utcnow() + timedelta(days=30)
    ))
    await db.commit()
    return TokenResponse(access_token=access, refresh_token=refresh)

# ═══════════════════════════════════════════════════════════
# LOGIN — FIX: returns user_id in response so frontend clears old token
# ═══════════════════════════════════════════════════════════

@router.post("/login", response_model=TokenResponse)
async def login(
    body: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    ip = get_client_ip(request)
    check_rate_limit(f"login:{ip}", "login")
    check_login_failures(body.email)

    result = await db.execute(select(User).where(User.email == body.email.lower().strip()))
    user = result.scalar_one_or_none()

    if not user or not verify_password(body.password, user.hashed_password):
        record_login_failure(body.email)
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is disabled. Contact support.")

    clear_login_failures(body.email)

    # FIX: Create fresh token with correct user_id — prevents cross-account data leak
    access = create_access_token(
        str(user.id),
        {"org_id": str(user.org_id), "role": user.role, "email": user.email}
    )
    refresh = create_refresh_token()
    db.add(RefreshToken(
        user_id=user.id,
        token_hash=hash_password(refresh),
        expires_at=datetime.utcnow() + timedelta(days=30)
    ))
    await db.commit()
    return TokenResponse(access_token=access, refresh_token=refresh)

# ═══════════════════════════════════════════════════════════
# ME — FIX: Always returns data for the token's actual user
# ═══════════════════════════════════════════════════════════

@router.get("/me")
async def me(user: User = Depends(_get_current_user), db: AsyncSession = Depends(get_db)):
    try:
        org = await db.get(Organization, user.org_id)
    except Exception:
        org = None
    return {
        "id": str(user.id),
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role,
        "is_verified": user.is_verified,
        "org": {
            "id": str(org.id) if org else None,
            "name": org.name if org else None,
            "plan_tier": org.plan_tier if org else "free"
        }
    }

# ═══════════════════════════════════════════════════════════
# VERIFY EMAIL
# ═══════════════════════════════════════════════════════════

@router.post("/verify-email")
async def verify_email(token: str, request: Request, db: AsyncSession = Depends(get_db)):
    ip = get_client_ip(request)
    check_rate_limit(f"verify:{ip}", "verify")
    result = await db.execute(select(User))
    users = result.scalars().all()
    user = next((u for u in users if u.metadata_ and u.metadata_.get("verify_token") == token), None)
    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired verification token")
    user.is_verified = True
    user.metadata_ = {k: v for k, v in user.metadata_.items() if k != "verify_token"}
    await db.commit()
    return {"message": "Email verified successfully"}

# ═══════════════════════════════════════════════════════════
# LOGOUT
# ═══════════════════════════════════════════════════════════

@router.post("/logout")
async def logout(user: User = Depends(_get_current_user)):
    return {"message": "Logged out successfully", "user_id": str(user.id)}

# ═══════════════════════════════════════════════════════════
# GOOGLE LOGIN
# ═══════════════════════════════════════════════════════════

@router.get("/google/login")
async def google_login(request: Request):
    import urllib.parse
    ip = get_client_ip(request)
    check_rate_limit(f"google:{ip}", "google")

    client_id = settings.GOOGLE_CLIENT_ID
    if not client_id:
        return RedirectResponse("https://dacexy.vercel.app/login?error=Google+OAuth+not+configured")

    params = {
        "client_id": client_id,
        "redirect_uri": "https://dacexy-backend-v7ku.onrender.com/api/v1/auth/google/callback",
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "select_account"
    }
    return RedirectResponse("https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode(params))

# ═══════════════════════════════════════════════════════════
# GOOGLE CALLBACK — FIX: isolates user session completely
# ═══════════════════════════════════════════════════════════

@router.get("/google/callback")
async def google_callback(
    request: Request,
    code: str = None,
    error: str = None,
    db: AsyncSession = Depends(get_db)
):
    FRONTEND = "https://dacexy.vercel.app"
    REDIRECT_URI = "https://dacexy-backend-v7ku.onrender.com/api/v1/auth/google/callback"

    if error:
        return RedirectResponse(f"{FRONTEND}/login?error={error}")
    if not code:
        return RedirectResponse(f"{FRONTEND}/login?error=no_code_received")

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            token_res = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "code": code,
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "redirect_uri": REDIRECT_URI,
                    "grant_type": "authorization_code"
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            token_data = token_res.json()

            if "error" in token_data:
                err = str(token_data.get("error_description") or token_data.get("error") or "oauth_failed")
                return RedirectResponse(f"{FRONTEND}/login?error={err.replace(' ', '+')}")

            google_access_token = token_data.get("access_token", "")
            if not google_access_token:
                return RedirectResponse(f"{FRONTEND}/login?error=no_google_token")

            user_res = await client.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {google_access_token}"}
            )
            info = user_res.json()

        email = (info.get("email") or "").lower().strip()
        full_name = (info.get("name") or "").strip()
        google_id = str(info.get("id") or "")

        if not email:
            return RedirectResponse(f"{FRONTEND}/login?error=no_email_from_google")
        if not full_name:
            full_name = email.split("@")[0].title()

        # FIX: Find user ONLY by their exact email — never mix accounts
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

        if not user:
            # Create brand new isolated account for this Google user
            first_name = full_name.split()[0] if full_name.split() else "User"
            org_name = first_name + "'s Workspace"
            slug = re.sub(r"[^a-z0-9]+", "-", org_name.lower()).strip("-") + "-" + secrets.token_hex(4)
            org = Organization(name=org_name, slug=slug)
            db.add(org)
            await db.flush()

            user = User(
                org_id=org.id,
                email=email,
                full_name=full_name,
                hashed_password=hash_password(secrets.token_urlsafe(32)),
                role="owner",
                is_verified=True,
                metadata_={"provider": "google", "google_id": google_id}
            )
            db.add(user)
            await db.flush()
            log.info(f"New Google user created: {email}")
        else:
            # FIX: Only update name if it genuinely changed — never touch org or other user data
            if full_name and full_name != user.full_name:
                user.full_name = full_name
            # Update google_id in metadata if missing
            if user.metadata_ is None:
                user.metadata_ = {}
            if not user.metadata_.get("google_id"):
                user.metadata_ = {**user.metadata_, "google_id": google_id}
            log.info(f"Existing Google user signed in: {email}")

        await db.commit()

        # FIX: JWT contains THIS user's id and org — completely isolated
        jwt_token = create_access_token(
            str(user.id),
            {
                "org_id": str(user.org_id),
                "role": user.role,
                "email": user.email
            }
        )
        # FIX: redirect with clear=true so frontend clears old localStorage token first
        return RedirectResponse(f"{FRONTEND}/login?token={jwt_token}&clear=true")

    except httpx.TimeoutException:
        return RedirectResponse(f"{FRONTEND}/login?error=Google+server+timeout.+Please+try+again.")
    except Exception as e:
        log.error(f"Google OAuth error: {e}")
        err_msg = "Authentication+failed.+Please+try+again."
        return RedirectResponse(f"{FRONTEND}/login?error={err_msg}")
""")
                         


w("src/interfaces/http/routes/ai_chat.py", '''
import json
import datetime
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from typing import Optional
from src.infrastructure.persistence.database import get_db
from src.infrastructure.persistence.models.orm_models import User, ConversationSession, MemoryEntry, GeneratedWebsite
from src.infrastructure.ai_providers.deepseek import DeepSeekProvider
from src.interfaces.http.dependencies.container import get_deepseek
from src.interfaces.http.routes.auth import _get_current_user

router = APIRouter(prefix="/ai", tags=["ai"])

SEARCH_KEYWORDS = [
    "search", "latest", "current", "today", "news", "recent", "now",
    "price", "weather", "who is", "what is the", "2024", "2025", "2026",
    "trending", "happening", "live", "update", "score", "stock",
    "find", "look up", "research", "browse", "internet",
    "cricket", "ipl", "football", "match", "tournament", "championship",
    "election", "government", "minister", "president", "prime minister",
    "rupee", "dollar", "bitcoin", "crypto", "market", "sensex", "nifty",
    "movie", "film", "release", "box office", "bollywood",
    "this week", "this month", "right now", "at the moment",
    "newly", "just", "recently", "announced", "launched", "breaking",
    "sports", "team", "player", "winner", "result", "standings",
    "temperature", "rain", "forecast", "humidity"
]

def needs_search(messages):
    if not messages:
        return False
    last = messages[-1]["content"].lower()
    return any(kw in last for kw in SEARCH_KEYWORDS)

def needs_website(messages):
    if not messages:
        return False
    last = messages[-1]["content"].lower()
    has_build = any(w in last for w in ["build", "make", "create", "generate", "design"])
    has_site = any(w in last for w in ["website", "landing page", "webpage", "site", "web app", "homepage"])
    return has_build and has_site

def get_system_prompt(memory_context=""):
    today = datetime.datetime.now().strftime("%B %d, %Y")
    mem = ("\\n\\nUser context:\\n" + memory_context) if memory_context else ""
    return {
        "role": "system",
        "content": f"""You are Dacexy AI, a sharp intelligent assistant. Today is {today}.
- Be direct, answer first then add context
- Plain prose, no asterisks, no ** bold, no ## headings
- No filler like Certainly! or I hope this helps!
- Concise responses, match user language
- For code give working code directly{mem}"""
    }

class MessageItem(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: list[MessageItem]
    session_id: Optional[str] = None
    stream: bool = True
    model: str = "deepseek-chat"

async def force_save(db: AsyncSession, session_id: str, msgs: list):
    try:
        await db.execute(
            update(ConversationSession)
            .where(ConversationSession.id == session_id)
            .values(messages=msgs)
        )
        await db.commit()
    except Exception:
        try:
            await db.rollback()
        except Exception:
            pass

@router.post("/chat")
async def chat(
    body: ChatRequest,
    user: User = Depends(_get_current_user),
    db: AsyncSession = Depends(get_db),
    ai: DeepSeekProvider = Depends(get_deepseek)
):
    messages = [{"role": m.role, "content": m.content} for m in body.messages]
    session = None

    if body.session_id:
        try:
            r = await db.execute(
                select(ConversationSession).where(
                    ConversationSession.id == body.session_id,
                    ConversationSession.org_id == user.org_id
                )
            )
            session = r.scalar_one_or_none()
        except Exception:
            session = None

    if not session:
        title = body.messages[0].content[:60] if body.messages else "New Chat"
        session = ConversationSession(
            org_id=user.org_id,
            user_id=user.id,
            title=title,
            messages=[]
        )
        db.add(session)
        await db.flush()
        await db.commit()

    session_id_str = str(session.id)

    try:
        mr = await db.execute(
            select(MemoryEntry)
            .where(MemoryEntry.org_id == user.org_id)
            .order_by(MemoryEntry.created_at.desc())
            .limit(20)
        )
        memories = mr.scalars().all()
        memory_context = "\\n".join([f"- {m.content}" for m in memories])
    except Exception:
        memory_context = ""

    system_msg = get_system_prompt(memory_context)
    full_messages = [system_msg] + messages

    last_content = body.messages[-1].content if body.messages else ""
    mem_triggers = ["my company","my business","we are","i am","our product",
                    "my name is","we sell","our team","my startup",
                    "remember that","remember this","save this"]
    if any(kw in last_content.lower() for kw in mem_triggers):
        try:
            db.add(MemoryEntry(org_id=user.org_id, user_id=user.id, content=last_content[:500]))
            await db.flush()
            await db.commit()
        except Exception:
            pass

    search = needs_search(messages)
    website = needs_website(messages)

    if website and body.stream:
        from src.application.use_cases.website.website_engine import generate_website
        prompt = body.messages[-1].content
        record = GeneratedWebsite(org_id=user.org_id, user_id=user.id, prompt=prompt, status="generating")
        db.add(record)
        await db.flush()
        await db.commit()
        record_id = str(record.id)

        async def website_stream():
            yield "data: " + json.dumps({"type": "session_id", "session_id": session_id_str}) + "\\n\\n"
            yield "data: " + json.dumps({"type": "chunk", "content": "Building your website...\\n\\n"}) + "\\n\\n"
            try:
                html = await generate_website(prompt, ai)
                await db.execute(
                    update(GeneratedWebsite)
                    .where(GeneratedWebsite.id == record.id)
                    .values(html_content=html, status="completed")
                )
                await db.commit()
                preview_url = "/api/v1/websites/" + record_id + "/preview"
                msg = "Your website is ready! Preview: " + preview_url + "\\n\\nClick Open to view it."
                yield "data: " + json.dumps({"type": "chunk", "content": msg}) + "\\n\\n"
            except Exception as e:
                try:
                    await db.execute(update(GeneratedWebsite).where(GeneratedWebsite.id == record.id).values(status="failed"))
                    await db.commit()
                except Exception:
                    pass
                yield "data: " + json.dumps({"type": "chunk", "content": "Website generation failed: " + str(e)}) + "\\n\\n"
            yield "data: " + json.dumps({"type": "done"}) + "\\n\\n"

        return StreamingResponse(website_stream(), media_type="text/event-stream")

    if body.stream:
        async def event_stream():
            full = ""
            yield "data: " + json.dumps({"type": "session_id", "session_id": session_id_str}) + "\\n\\n"
            if search:
                yield "data: " + json.dumps({"type": "chunk", "content": "Searching the web...\\n\\n"}) + "\\n\\n"
            try:
                async for chunk in await ai.chat(full_messages, model=body.model, stream=True, search=search):
                    full += chunk
                    yield "data: " + json.dumps({"type": "chunk", "content": chunk}) + "\\n\\n"
            except Exception as e:
                yield "data: " + json.dumps({"type": "chunk", "content": "AI error: " + str(e)}) + "\\n\\n"
            yield "data: " + json.dumps({"type": "done"}) + "\\n\\n"
            if full:
                try:
                    r2 = await db.execute(
                        select(ConversationSession).where(ConversationSession.id == session_id_str)
                    )
                    s2 = r2.scalar_one_or_none()
                    existing = []
                    if s2 and isinstance(s2.messages, list):
                        existing = [m for m in s2.messages if isinstance(m, dict) and m.get("role") != "system"]
                    existing.append({"role": "user", "content": last_content})
                    existing.append({"role": "assistant", "content": full})
                    await force_save(db, session_id_str, existing)
                except Exception:
                    pass

        return StreamingResponse(event_stream(), media_type="text/event-stream")

    try:
        response = await ai.chat(full_messages, model=body.model, stream=False, search=search)
    except Exception as e:
        raise HTTPException(500, f"AI error: {str(e)}")

    try:
        r2 = await db.execute(select(ConversationSession).where(ConversationSession.id == session_id_str))
        s2 = r2.scalar_one_or_none()
        existing = []
        if s2 and isinstance(s2.messages, list):
            existing = [m for m in s2.messages if isinstance(m, dict) and m.get("role") != "system"]
        existing.append({"role": "user", "content": last_content})
        existing.append({"role": "assistant", "content": response})
        await force_save(db, session_id_str, existing)
    except Exception:
        pass

    return {"content": response, "session_id": session_id_str}

@router.get("/sessions")
async def list_sessions(
    user: User = Depends(_get_current_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        result = await db.execute(
            select(ConversationSession)
            .where(ConversationSession.org_id == user.org_id)
            .order_by(ConversationSession.updated_at.desc())
            .limit(50)
        )
        rows = result.scalars().all()
        out = []
        for s in rows:
            try:
                out.append({
                    "id": str(s.id),
                    "title": s.title or "New Chat",
                    "created_at": str(s.created_at)
                })
            except Exception:
                continue
        return {"sessions": out, "total": len(out)}
    except Exception:
        return {"sessions": [], "total": 0}

@router.get("/sessions/{session_id}/messages")
async def get_messages(
    session_id: str,
    user: User = Depends(_get_current_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        result = await db.execute(
            select(ConversationSession).where(
                ConversationSession.id == session_id,
                ConversationSession.org_id == user.org_id
            )
        )
        session = result.scalar_one_or_none()
        if not session:
            raise HTTPException(404, "Session not found")
        msgs = session.messages or []
        if not isinstance(msgs, list):
            msgs = []
        clean = [
            m for m in msgs
            if isinstance(m, dict)
            and m.get("role") != "system"
            and str(m.get("content", "")).strip()
        ]
        return {"messages": clean, "session_id": str(session.id), "title": session.title or "Chat"}
    except HTTPException:
        raise
    except Exception:
        return {"messages": [], "session_id": session_id, "title": "Chat"}
''')            
    
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
w("src/interfaces/http/routes/agent.py", '''
from __future__ import annotations
import json
import asyncio
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import Response
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
pending_task_results: Dict[str, asyncio.Future] = {}


class AgentRunRequest(BaseModel):
    task: Optional[str] = None
    goal: Optional[str] = None
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


class TaskRequest(BaseModel):
    task: Optional[str] = None
    goal: Optional[str] = None
    context: Optional[str] = None


def _decode_ws_token(token: str) -> Optional[str]:
    if not token:
        return None
    try:
        from jose import jwt
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user_id = str(payload.get("sub") or payload.get("user_id") or "")
        return user_id if user_id else None
    except Exception:
        import logging
        logging.getLogger("dacexy.ws").debug("JWT decode failed - token expired or wrong secret")
        return None


@router.post("/run")
async def run_agent(body: AgentRunRequest, user: User = Depends(_get_current_user), db: AsyncSession = Depends(get_db), ai: DeepSeekProvider = Depends(get_deepseek)):
    task_text = body.task or body.goal or ""
    if not task_text:
        raise HTTPException(400, "task or goal is required")
    user_id = str(user.id)
    task_record = AiTask(org_id=user.org_id, user_id=user.id, task_type="agent_run", status="running", input_data={"task": task_text, "context": body.context})
    db.add(task_record)
    await db.flush()
    await db.commit()
    if user_id in active_agents:
        ws = active_agents[user_id]
        try:
            loop = asyncio.get_event_loop()
            future = loop.create_future()
            pending_task_results[user_id] = future
            await ws.send_text(json.dumps({"type": "task", "task": task_text, "context": body.context or "", "task_id": str(task_record.id)}))
            try:
                result_data = await asyncio.wait_for(future, timeout=120)
                result_text = "Completed {} actions on your desktop.".format(result_data.get("actions_taken", 0))
            except asyncio.TimeoutError:
                result_text = "Task sent to desktop agent but timed out waiting for confirmation."
            finally:
                pending_task_results.pop(user_id, None)
            task_record.status = "completed"
            task_record.output_data = {"result": result_text}
            await db.commit()
            return {"id": str(task_record.id), "task": task_text, "goal": task_text, "status": "completed", "result": result_text, "created_at": str(task_record.created_at)}
        except Exception:
            active_agents.pop(user_id, None)
    system_prompt = "You are an autonomous AI agent for Dacexy. The user wants you to complete a task. Since no desktop agent is connected, describe clearly what you did or would do step by step."
    context_part = " Context: {}".format(body.context) if body.context else ""
    messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": "Task: {}{}".format(task_text, context_part)}]
    try:
        result = await ai.chat(messages, model="deepseek-chat", stream=False)
        if isinstance(result, list):
            result = " ".join(block.get("text", "") for block in result if isinstance(block, dict) and block.get("type") == "text")
        task_record.status = "completed"
        task_record.output_data = {"result": result}
        await db.commit()
        return {"id": str(task_record.id), "task": task_text, "goal": task_text, "status": "completed", "result": result, "created_at": str(task_record.created_at)}
    except Exception as e:
        task_record.status = "failed"
        task_record.output_data = {"error": str(e)}
        await db.commit()
        raise HTTPException(500, "Agent error: {}".format(str(e)))


@router.get("/tasks")
async def list_tasks(user: User = Depends(_get_current_user), db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select
    result = await db.execute(select(AiTask).where(AiTask.org_id == user.org_id).order_by(AiTask.created_at.desc()).limit(50))
    tasks = result.scalars().all()
    runs = []
    for t in tasks:
        out = t.output_data or {}
        inp = t.input_data or {}
        runs.append({"id": str(t.id), "task": inp.get("task", ""), "goal": inp.get("task", ""), "status": t.status, "result": out.get("result"), "error": out.get("error"), "created_at": str(t.created_at)})
    return runs


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
        raise HTTPException(500, "Failed to send command: {}".format(str(e)))


@router.post("/desktop/task")
async def send_desktop_task(body: TaskRequest, user: User = Depends(_get_current_user)):
    user_id = str(user.id)
    if user_id not in active_agents:
        raise HTTPException(400, "Desktop agent not connected.")
    ws = active_agents[user_id]
    task_text = body.task or body.goal or ""
    if not task_text:
        raise HTTPException(400, "task or goal required")
    try:
        await ws.send_text(json.dumps({"type": "task", "task": task_text, "context": body.context or ""}))
        return {"status": "sent", "task": task_text}
    except Exception as e:
        active_agents.pop(user_id, None)
        raise HTTPException(500, "Failed to send task: {}".format(str(e)))


@router.websocket("/desktop/ws")
async def desktop_websocket(websocket: WebSocket):
    await websocket.accept()
    user_id = None
    try:
        try:
            auth_raw = await asyncio.wait_for(websocket.receive_text(), timeout=30)
        except asyncio.TimeoutError:
            await websocket.send_text(json.dumps({"type": "error", "message": "Authentication timeout - send token within 30s"}))
            await websocket.close()
            return
        try:
            auth_data = json.loads(auth_raw)
            token = auth_data.get("token", "")
        except Exception:
            token = auth_raw.strip()
        user_id = _decode_ws_token(token)
        if not user_id:
            await websocket.send_text(json.dumps({"type": "error", "message": "Authentication failed - token is missing, expired, or invalid. Please log in again."}))
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
                elif msg_type == "pong":
                    pass
                elif msg_type == "task_result":
                    agent_results[user_id] = msg
                    future = pending_task_results.get(user_id)
                    if future and not future.done():
                        future.set_result(msg)
                elif msg_type in ("result", "screenshot_before", "screenshot_after", "system_info", "error", "voice_result"):
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
            future = pending_task_results.pop(user_id, None)
            if future and not future.done():
                future.cancel()


@router.get("/download/windows")
async def download_windows_agent():
    crlf = chr(13) + chr(10)
    q = chr(34)
    py_url = "https://raw.githubusercontent.com/dacexyai/Dacexy-backend/main/desktop_agent/dacexy_agent.py"
    py_inst = "https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe"
    lines = [
        "@echo off",
        "setlocal enabledelayedexpansion",
        "net session >nul 2>&1",
        "if errorlevel 1 (",
        "    echo Requesting administrator access...",
        "    powershell -Command start-process -filepath %~f0 -verb runas",
        "    exit /b",
        ")",
        "title Dacexy Desktop Agent Installer",
        "color 0A",
        "echo.",
        "echo  DACEXY Desktop Agent v3.1",
        "echo.",
        "echo [1/5] Checking Python...",
        "python --version >nul 2>&1",
        "if errorlevel 1 (",
        "    echo Python not found. Installing...",
        "    powershell -Command " + q + "Invoke-WebRequest -Uri " + py_inst + " -OutFile %TEMP%\\python_installer.exe -UseBasicParsing" + q,
        "    %TEMP%\\python_installer.exe /quiet InstallAllUsers=1 PrependPath=1",
        "    timeout /t 15 /nobreak >nul",
        "    del %TEMP%\\python_installer.exe",
        ")",
        "echo OK: Python ready",
        "echo [2/5] Creating agent folder...",
        "if not exist %USERPROFILE%\\DacexyAgent mkdir %USERPROFILE%\\DacexyAgent",
        "echo [3/5] Installing packages...",
        "python -m pip install --upgrade pip --quiet",
        "python -m pip install pyautogui pillow websockets requests speechrecognition pyttsx3 numpy psutil --quiet",
        "echo OK: Packages installed",
        "echo [4/5] Downloading agent script...",
        "if exist %USERPROFILE%\\DacexyAgent\\dacexy_agent.py del %USERPROFILE%\\DacexyAgent\\dacexy_agent.py",
        "powershell -Command " + q + "Invoke-WebRequest -Uri " + py_url + " -OutFile %USERPROFILE%\\DacexyAgent\\dacexy_agent.py -UseBasicParsing" + q,
        "echo OK: Agent downloaded",
        "if exist %USERPROFILE%\\.dacexy_agent.json del %USERPROFILE%\\.dacexy_agent.json",
        "echo OK: Old session cleared - you will be asked to log in",
        "echo [5/5] Launching agent...",
        "cd %USERPROFILE%\\DacexyAgent",
        "python dacexy_agent.py",
        "pause",
    ]
    bat_bytes = crlf.join(lines).encode("utf-8")
    resp = Response(content=bat_bytes, media_type="application/octet-stream")
    resp.headers["Content-Disposition"] = "attachment; filename=install_dacexy_agent.bat"
    return resp
''')
  
                          
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
w("src/interfaces/http/routes/media.py", '''from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
import httpx
import asyncio
import urllib.parse

from src.infrastructure.persistence.database import get_db
from src.infrastructure.persistence.models.orm_models import User, GeneratedImage, GeneratedVideo
from src.interfaces.http.routes.auth import _get_current_user
from src.shared.config.settings import settings

router = APIRouter(prefix="/media", tags=["media"])

class ImageRequest(BaseModel):
    prompt: str
    width: int = 1024
    height: int = 1024

class VideoRequest(BaseModel):
    prompt: str

@router.post("/image")
async def generate_image(body: ImageRequest, user: User = Depends(_get_current_user), db: AsyncSession = Depends(get_db)):
    record = GeneratedImage(org_id=user.org_id, user_id=user.id, prompt=body.prompt, status="processing")
    db.add(record)
    await db.flush()
    try:
        encoded = urllib.parse.quote(body.prompt[:80])
        seed = abs(hash(body.prompt)) % 99999
        image_url = f"https://image.pollinations.ai/prompt/{encoded}?width={body.width}&height={body.height}&seed={seed}&nologo=true&model=flux"
        async with httpx.AsyncClient(timeout=60, follow_redirects=True) as client:
            r = await client.get(image_url)
            if r.status_code != 200:
                raise HTTPException(500, f"Image generation failed: status {r.status_code}")
        record.url = image_url
        record.status = "completed"
        await db.commit()
        return {"id": str(record.id), "url": image_url, "status": "completed"}
    except HTTPException:
        raise
    except Exception as e:
        record.status = "failed"
        await db.commit()
        raise HTTPException(500, f"Image generation failed: {str(e)}")

@router.post("/video")
async def generate_video(body: VideoRequest, user: User = Depends(_get_current_user), db: AsyncSession = Depends(get_db)):
    record = GeneratedVideo(org_id=user.org_id, user_id=user.id, prompt=body.prompt, status="processing")
    db.add(record)
    await db.flush()
    wavespeed_key = getattr(settings, "WAVESPEED_API_KEY", "")
    if not wavespeed_key:
        encoded = urllib.parse.quote(body.prompt[:80])
        seed = abs(hash(body.prompt)) % 99999
        image_url = f"https://image.pollinations.ai/prompt/cinematic_{encoded}?width=1280&height=720&seed={seed}&nologo=true&model=flux"
        async with httpx.AsyncClient(timeout=60, follow_redirects=True) as client:
            r = await client.get(image_url)
        record.url = image_url
        record.status = "completed"
        await db.commit()
        return {"id": str(record.id), "url": image_url, "status": "completed", "note": "Add WAVESPEED_API_KEY for real video"}
    try:
        async with httpx.AsyncClient(timeout=120) as client:
            r = await client.post(
                "https://api.wavespeed.ai/api/v2/wavespeed-ai/wan-t2v-480p",
                headers={"Authorization": f"Bearer {wavespeed_key}", "Content-Type": "application/json"},
                json={"prompt": body.prompt, "duration": "5", "ratio": "16:9"}
            )
            if r.status_code not in [200, 201]:
                raise HTTPException(500, f"WaveSpeed error {r.status_code}: {r.text[:200]}")
            data = r.json()
            request_id = data.get("data", {}).get("id", "")
            video_url = ""
            for _ in range(30):
                await asyncio.sleep(4)
                poll = await client.get(
                    f"https://api.wavespeed.ai/api/v2/predictions/{request_id}/result",
                    headers={"Authorization": f"Bearer {wavespeed_key}"}
                )
                pdata = poll.json()
                status = pdata.get("data", {}).get("status", "")
                if status == "completed":
                    video_url = pdata.get("data", {}).get("outputs", [""])[0]
                    break
                elif status == "failed":
                    raise HTTPException(500, "Video generation failed")
            if not video_url:
                raise HTTPException(500, "Video generation timed out")
            record.url = video_url
            record.status = "completed"
            await db.commit()
            return {"id": str(record.id), "url": video_url, "status": "completed"}
    except HTTPException:
        raise
    except Exception as e:
        record.status = "failed"
        await db.commit()
        raise HTTPException(500, f"Video generation failed: {str(e)}")
''')

w("src/main.py", '''
from __future__ import annotations
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse, Response
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

from fastapi import Request
@app.api_route("/health", methods=["GET", "HEAD"])
async def health(request: Request):
    return {"status": "ok"}

    
@app.get("/config")
async def config():
    return {"app_name": settings.APP_NAME, "version": settings.APP_VERSION, "features": {"ai_chat": bool(settings.DEEPSEEK_API_KEY), "media": bool(settings.BYTEZ_API_KEY), "payments": settings.payments_enabled}}

@app.get("/")
async def root():
    return {"message": "Welcome to " + settings.APP_NAME, "docs": "/docs", "health": "/health"}
''')

import ast, pathlib, os, subprocess, sys

# ── Syntax check all written files ──────────────────────────────────────────
for f in pathlib.Path("src").rglob("*.py"):
    try:
        ast.parse(f.read_text())
    except SyntaxError as e:
        print(f"BROKEN FILE: {f}  |  Line: {e.lineno}  |  Error: {e.msg}")
        print(f"Bad text: {e.text}")

# Test import before launching
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from src.main import app
    print("✅ Import OK - starting server")
except Exception as e:
    import traceback
    print("❌ IMPORT FAILED:")
    traceback.print_exc()
    sys.exit(1)

import sys, os, subprocess, traceback

# Step 1: Test import
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
print("=== Testing import ===", flush=True)
try:
    from src.main import app
    print("✅ Import OK", flush=True)
except Exception:
    print("❌ Import FAILED:", flush=True)
    traceback.print_exc()
    sys.exit(1)

# Step 2: Start uvicorn
print("\n✅ ALL FILES CREATED SUCCESSFULLY!")
import os, sys, subprocess

port = os.environ.get('PORT', '10000')
print(f'Starting uvicorn on port: {port}', flush=True)
proc = subprocess.Popen(
    [sys.executable, '-m', 'uvicorn', 'src.main:app',
     '--host', '0.0.0.0',
     '--port', port,
     '--log-level', 'info'],
    stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
)
for line in proc.stdout:
    print(line, end='', flush=True)
proc.wait()
sys.exit(proc.returncode)

# ── Start server ─────────────────────────────────────────────────────────────
port = int(os.environ.get("PORT", 8000))
result = subprocess.run([
    sys.executable, "-m", "uvicorn",
    "src.main:app",
    "--host", "0.0.0.0",
    "--port", str(port),
    "--workers", "1",
])
sys.exit(result.returncode)
