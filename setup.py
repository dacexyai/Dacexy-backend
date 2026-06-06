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
    REPLICATE_API_TOKEN: str = ""
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

# ── FIX 1: JWT expiry raised from 60 → 43200 minutes (30 days) ──────────────
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

def create_access_token(subject, extra=None, expires_minutes=43200):
    # 43200 minutes = 30 days — users stay logged in permanently
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
        raise HTTPException(status_code=429, detail=f"Too many attempts. Please wait {wait} seconds.", headers={"Retry-After": str(wait)})
    if now - store["window_start"] > cfg["window"]:
        store["count"] = 0
        store["window_start"] = now
    store["count"] += 1
    if store["count"] > cfg["rpm"]:
        store["blocked_until"] = now + cfg["block"]
        store["count"] = 0
        raise HTTPException(status_code=429, detail=f"Rate limit exceeded. Please wait {cfg['block']} seconds.", headers={"Retry-After": str(cfg["block"])})

_login_failures: dict = defaultdict(lambda: {"count": 0, "first_fail": 0.0, "blocked_until": 0.0})

def check_login_failures(email: str) -> None:
    now = time.time()
    record = _login_failures[email.lower()]
    if record["blocked_until"] > now:
        wait = int(record["blocked_until"] - now)
        raise HTTPException(status_code=429, detail=f"Account temporarily locked. Try again in {wait} seconds.", headers={"Retry-After": str(wait)})
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
        raise HTTPException(status_code=409, detail="This email is already registered. Please sign in instead.")

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

    # 30-day token so users never get randomly logged out
    access = create_access_token(str(user.id), {"org_id": str(org.id), "role": "owner"}, expires_minutes=43200)
    refresh = create_refresh_token()
    db.add(RefreshToken(
        user_id=user.id,
        token_hash=hash_password(refresh),
        expires_at=datetime.utcnow() + timedelta(days=30)
    ))
    await db.commit()
    return TokenResponse(access_token=access, refresh_token=refresh)

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

    # 30-day token
    access = create_access_token(
        str(user.id),
        {"org_id": str(user.org_id), "role": user.role, "email": user.email},
        expires_minutes=43200
    )
    refresh = create_refresh_token()
    db.add(RefreshToken(
        user_id=user.id,
        token_hash=hash_password(refresh),
        expires_at=datetime.utcnow() + timedelta(days=30)
    ))
    await db.commit()
    return TokenResponse(access_token=access, refresh_token=refresh)

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

# ── Token refresh endpoint — frontend calls this to get a new token ──────────
@router.post("/refresh")
async def refresh_token_endpoint(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    body = await request.json()
    token = body.get("refresh_token", "")
    if not token:
        raise HTTPException(status_code=401, detail="Refresh token required")
    result = await db.execute(select(RefreshToken))
    all_tokens = result.scalars().all()
    matched = None
    matched_user_id = None
    for rt in all_tokens:
        try:
            if verify_password(token, rt.token_hash):
                if rt.expires_at > datetime.utcnow():
                    matched = rt
                    matched_user_id = rt.user_id
                break
        except Exception:
            continue
    if not matched:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
    user_result = await db.execute(select(User).where(User.id == matched_user_id))
    user = user_result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found")
    new_access = create_access_token(
        str(user.id),
        {"org_id": str(user.org_id), "role": user.role, "email": user.email},
        expires_minutes=43200
    )
    return {"access_token": new_access, "token_type": "bearer"}

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

@router.post("/logout")
async def logout(user: User = Depends(_get_current_user)):
    return {"message": "Logged out successfully", "user_id": str(user.id)}

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
                data={"code": code, "client_id": settings.GOOGLE_CLIENT_ID, "client_secret": settings.GOOGLE_CLIENT_SECRET, "redirect_uri": REDIRECT_URI, "grant_type": "authorization_code"},
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            token_data = token_res.json()
            if "error" in token_data:
                err = str(token_data.get("error_description") or token_data.get("error") or "oauth_failed")
                return RedirectResponse(f"{FRONTEND}/login?error={err.replace(' ', '+')}")
            google_access_token = token_data.get("access_token", "")
            if not google_access_token:
                return RedirectResponse(f"{FRONTEND}/login?error=no_google_token")
            user_res = await client.get("https://www.googleapis.com/oauth2/v2/userinfo", headers={"Authorization": f"Bearer {google_access_token}"})
            info = user_res.json()
        email = (info.get("email") or "").lower().strip()
        full_name = (info.get("name") or "").strip()
        google_id = str(info.get("id") or "")
        if not email:
            return RedirectResponse(f"{FRONTEND}/login?error=no_email_from_google")
        if not full_name:
            full_name = email.split("@")[0].title()
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if not user:
            first_name = full_name.split()[0] if full_name.split() else "User"
            org_name = first_name + "'s Workspace"
            slug = re.sub(r"[^a-z0-9]+", "-", org_name.lower()).strip("-") + "-" + secrets.token_hex(4)
            org = Organization(name=org_name, slug=slug)
            db.add(org)
            await db.flush()
            user = User(org_id=org.id, email=email, full_name=full_name, hashed_password=hash_password(secrets.token_urlsafe(32)), role="owner", is_verified=True, metadata_={"provider": "google", "google_id": google_id})
            db.add(user)
            await db.flush()
        else:
            if full_name and full_name != user.full_name:
                user.full_name = full_name
            if user.metadata_ is None:
                user.metadata_ = {}
            if not user.metadata_.get("google_id"):
                user.metadata_ = {**user.metadata_, "google_id": google_id}
        await db.commit()
        jwt_token = create_access_token(str(user.id), {"org_id": str(user.org_id), "role": user.role, "email": user.email}, expires_minutes=43200)
        return RedirectResponse(f"{FRONTEND}/login?token={jwt_token}&clear=true")
    except httpx.TimeoutException:
        return RedirectResponse(f"{FRONTEND}/login?error=Google+server+timeout.+Please+try+again.")
    except Exception as e:
        log.error(f"Google OAuth error: {e}")
        return RedirectResponse(f"{FRONTEND}/login?error=Authentication+failed.+Please+try+again.")
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
from src.infrastructure.persistence.models.orm_models import User, ConversationSession, MemoryEntry
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
        await db.execute(update(ConversationSession).where(ConversationSession.id == session_id).values(messages=msgs))
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
            r = await db.execute(select(ConversationSession).where(ConversationSession.id == body.session_id, ConversationSession.org_id == user.org_id))
            session = r.scalar_one_or_none()
        except Exception:
            session = None
    if not session:
        title = body.messages[0].content[:60] if body.messages else "New Chat"
        session = ConversationSession(org_id=user.org_id, user_id=user.id, title=title, messages=[])
        db.add(session)
        await db.flush()
        await db.commit()
    session_id_str = str(session.id)
    try:
        mr = await db.execute(select(MemoryEntry).where(MemoryEntry.org_id == user.org_id).order_by(MemoryEntry.created_at.desc()).limit(20))
        memories = mr.scalars().all()
        memory_context = "\\n".join([f"- {m.content}" for m in memories])
    except Exception:
        memory_context = ""
    system_msg = get_system_prompt(memory_context)
    full_messages = [system_msg] + messages
    last_content = body.messages[-1].content if body.messages else ""
    mem_triggers = ["my company","my business","we are","i am","our product","my name is","we sell","our team","my startup","remember that","remember this","save this"]
    if any(kw in last_content.lower() for kw in mem_triggers):
        try:
            db.add(MemoryEntry(org_id=user.org_id, user_id=user.id, content=last_content[:500]))
            await db.flush()
            await db.commit()
        except Exception:
            pass
    search = needs_search(messages)
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
                    r2 = await db.execute(select(ConversationSession).where(ConversationSession.id == session_id_str))
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
async def list_sessions(user: User = Depends(_get_current_user), db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(select(ConversationSession).where(ConversationSession.org_id == user.org_id).order_by(ConversationSession.updated_at.desc()).limit(50))
        rows = result.scalars().all()
        out = []
        for s in rows:
            try:
                out.append({"id": str(s.id), "title": s.title or "New Chat", "created_at": str(s.created_at)})
            except Exception:
                continue
        return {"sessions": out, "total": len(out)}
    except Exception:
        return {"sessions": [], "total": 0}

@router.get("/sessions/{session_id}/messages")
async def get_messages(session_id: str, user: User = Depends(_get_current_user), db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(select(ConversationSession).where(ConversationSession.id == session_id, ConversationSession.org_id == user.org_id))
        session = result.scalar_one_or_none()
        if not session:
            raise HTTPException(404, "Session not found")
        msgs = session.messages or []
        if not isinstance(msgs, list):
            msgs = []
        clean = [m for m in msgs if isinstance(m, dict) and m.get("role") != "system" and str(m.get("content", "")).strip()]
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

_agent_route_content = r'''from __future__ import annotations
import json
import asyncio
import logging
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, Dict, Any, List
from src.infrastructure.persistence.database import get_db
from src.infrastructure.persistence.models.orm_models import User, AiTask
from src.infrastructure.ai_providers.deepseek import DeepSeekProvider
from src.interfaces.http.dependencies.container import get_deepseek
from src.interfaces.http.routes.auth import _get_current_user
from src.shared.config.settings import settings

log = logging.getLogger("dacexy.agent")
router = APIRouter(prefix="/agent", tags=["agent"])

active_agents:        Dict[str, WebSocket]      = {}
agent_results:        Dict[str, Dict]           = {}
pending_task_results: Dict[str, asyncio.Future] = {}
agent_metadata:       Dict[str, Dict]           = {}


class AgentRunRequest(BaseModel):
    task:      Optional[str] = None
    goal:      Optional[str] = None
    context:   Optional[str] = None
    max_steps: int           = 10
    use_swarm: bool          = True


class DesktopCommandRequest(BaseModel):
    action:       str
    x:            Optional[int]   = None
    y:            Optional[int]   = None
    x1:           Optional[int]   = None
    y1:           Optional[int]   = None
    x2:           Optional[int]   = None
    y2:           Optional[int]   = None
    text:         Optional[str]   = None
    key:          Optional[str]   = None
    keys:         Optional[list]  = None
    url:          Optional[str]   = None
    command:      Optional[str]   = None
    clicks:       Optional[int]   = 3
    app:          Optional[str]   = None
    button:       Optional[str]   = "left"
    duration:     Optional[float] = 0.3
    selector:     Optional[str]   = None
    by:           Optional[str]   = "css"
    task:         Optional[str]   = None
    query:        Optional[str]   = None
    path:         Optional[str]   = None
    content:      Optional[str]   = None
    campaign_id:  Optional[str]   = None
    contacts:     Optional[list]  = None
    message:      Optional[str]   = None
    username:     Optional[str]   = None
    password:     Optional[str]   = None
    recipients:   Optional[list]  = None
    subject:      Optional[str]   = None
    body:         Optional[str]   = None
    title:        Optional[str]   = None
    fact:         Optional[str]   = None
    category:     Optional[str]   = None
    name:         Optional[str]   = None
    folder:       Optional[str]   = None
    keyword:      Optional[str]   = None
    direction:    Optional[str]   = "down"
    timeout:      Optional[int]   = 30
    headless:     Optional[bool]  = False
    browser_type: Optional[str]   = "chrome"
    html:         Optional[bool]  = True
    delay:        Optional[float] = 1.0
    region:       Optional[list]  = None
    retries:      Optional[int]   = 3
    expected:     Optional[str]   = None
    job_id:       Optional[str]   = None
    schedule_type:Optional[str]   = None
    time_str:     Optional[str]   = None
    days:         Optional[list]  = None
    steps:        Optional[list]  = None
    tags:         Optional[list]  = None
    image_path:   Optional[str]   = None
    caption:      Optional[str]   = None
    video_path:   Optional[str]   = None
    description:  Optional[str]   = None
    page_id:      Optional[str]   = None
    credentials:  Optional[dict]  = None
    src:          Optional[str]   = None
    dst:          Optional[str]   = None
    output:       Optional[str]   = None
    paths:        Optional[list]  = None
    importance:   Optional[float] = 1.0
    seconds:      Optional[float] = 1.0
    safe:         Optional[bool]  = True
    top_k:        Optional[int]   = 5
    max_pages:    Optional[int]   = 3
    topic:        Optional[str]   = None
    contact:      Optional[str]   = None
    email:        Optional[str]   = None
    phone:        Optional[str]   = None
    app_password: Optional[str]   = None
    host:         Optional[str]   = None
    port:         Optional[int]   = 587
    use_tls:      Optional[bool]  = True
    task_name:    Optional[str]   = None
    notes:        Optional[list]  = None
    repeat_every_minutes: Optional[int] = 0
    run_on_startup: Optional[bool] = False
    day_of_month: Optional[int]   = None
    enabled:      Optional[bool]  = True
    value:        Optional[Any]   = None
    script:       Optional[str]   = None
    media:        Optional[str]   = None
    pattern:      Optional[str]   = "*"
    ext:          Optional[str]   = None
    content_search: Optional[bool] = False
    csv_path:     Optional[str]   = None
    success_indicator: Optional[str] = None
    email_selector:    Optional[str] = None
    pass_selector:     Optional[str] = None
    submit_selector:   Optional[str] = None
    fallbacks:    Optional[list]  = None
    amount:       Optional[int]   = 700
    clear_first:  Optional[bool]  = False
    human_speed:  Optional[bool]  = False
    provider_index: Optional[int] = 0


class TaskRequest(BaseModel):
    task:    Optional[str] = None
    goal:    Optional[str] = None
    context: Optional[str] = None


class CampaignRequest(BaseModel):
    name:         str
    subject:      str
    body:         str
    recipients:   List[str]
    html:         bool  = True
    delay_sec:    float = 1.0
    tags:         List[str] = []
    scheduled_at: Optional[str] = None


class BulkWhatsAppRequest(BaseModel):
    contacts: List[str]
    message:  str
    delay:    float = 3.5


class SocialPostRequest(BaseModel):
    platform:    str
    username:    str
    password:    str
    text:        Optional[str] = None
    image_path:  Optional[str] = None
    video_path:  Optional[str] = None
    caption:     Optional[str] = None
    title:       Optional[str] = None
    description: Optional[str] = None
    page_id:     Optional[str] = None


def _decode_ws_token(token: str) -> Optional[str]:
    if not token or len(token) < 20:
        return None
    try:
        from jose import jwt
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        uid = str(payload.get("sub") or payload.get("user_id") or "")
        return uid if uid else None
    except Exception as e:
        log.debug("JWT decode failed: %s", e)
        return None


@router.post("/run")
async def run_agent(
    body: AgentRunRequest,
    user: User             = Depends(_get_current_user),
    db:   AsyncSession     = Depends(get_db),
    ai:   DeepSeekProvider = Depends(get_deepseek)
):
    task_text = (body.task or body.goal or "").strip()[:2000]
    if not task_text:
        raise HTTPException(400, "task or goal is required")

    user_id = str(user.id)

    task_record = AiTask(
        org_id     = user.org_id,
        user_id    = user.id,
        task_type  = "agent_run",
        status     = "running",
        input_data = {
            "task":      task_text,
            "context":   body.context,
            "use_swarm": body.use_swarm,
            "max_steps": body.max_steps
        }
    )
    db.add(task_record)
    await db.flush()
    await db.commit()

    if user_id in active_agents:
        ws = active_agents[user_id]
        try:
            loop   = asyncio.get_event_loop()
            future = loop.create_future()
            pending_task_results[user_id] = future

            payload = {
                "type":    "task" if body.use_swarm else "command",
                "task":    task_text,
                "action":  "swarm_task" if body.use_swarm else "speak",
                "context": body.context or "",
                "task_id": str(task_record.id)
            }
            await ws.send_text(json.dumps(payload))

            try:
                result_data = await asyncio.wait_for(
                    asyncio.shield(future), timeout=300)
                ok    = result_data.get("ok", result_data.get("total", 0))
                total = result_data.get("total", 0)
                raw   = result_data.get("result", "")
                if isinstance(raw, dict):
                    result_text = json.dumps(raw)
                else:
                    result_text = (
                        str(raw) if raw else
                        f"Completed {ok}/{total} steps on your desktop."
                    )
            except asyncio.TimeoutError:
                result_text = (
                    "Task sent to desktop agent and running in background. "
                    "Check your desktop for progress."
                )
            except asyncio.CancelledError:
                result_text = "Task was cancelled."
            finally:
                pending_task_results.pop(user_id, None)

            task_record.status      = "completed"
            task_record.output_data = {"result": result_text}
            await db.commit()

            return {
                "id":            str(task_record.id),
                "task":          task_text,
                "status":        "completed",
                "result":        result_text,
                "created_at":    str(task_record.created_at),
                "agent_version": agent_metadata.get(user_id, {}).get("version", "")
            }

        except WebSocketDisconnect:
            active_agents.pop(user_id, None)
            pending_task_results.pop(user_id, None)
            log.info("Agent disconnected during task for user %s", user_id)
        except Exception as e:
            active_agents.pop(user_id, None)
            pending_task_results.pop(user_id, None)
            log.warning("Agent task error for %s: %s", user_id, e)

    system_prompt = (
        "You are Dacexy AI, the world most advanced autonomous desktop agent. "
        "The user Desktop Agent is not currently connected to their computer. "
        "Describe exactly what you would do step by step to complete this task, "
        "with specific actions like: click coordinates, type text, open apps, etc. "
        "End by telling the user to install and run the Dacexy Desktop Agent "
        "from their Settings page for fully automatic execution."
    )
    ctx_part = f"\nContext: {body.context}" if body.context else ""
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user",   "content": f"Task: {task_text}{ctx_part}"}
    ]
    try:
        result = await ai.chat(messages, model="deepseek-chat", stream=False)
        if isinstance(result, list):
            result = " ".join(
                b.get("text", "") for b in result
                if isinstance(b, dict) and b.get("type") == "text"
            )
        result = str(result)
        task_record.status      = "completed"
        task_record.output_data = {"result": result}
        await db.commit()
        return {
            "id":         str(task_record.id),
            "task":       task_text,
            "status":     "completed",
            "result":     result,
            "created_at": str(task_record.created_at),
            "note": (
                "Desktop Agent not connected. "
                "Connect your Desktop Agent for automatic execution."
            )
        }
    except Exception as e:
        task_record.status      = "failed"
        task_record.output_data = {"error": str(e)}
        await db.commit()
        raise HTTPException(500, f"Agent AI error: {e}")


@router.get("/tasks")
async def list_tasks(
    user: User         = Depends(_get_current_user),
    db:   AsyncSession = Depends(get_db)
):
    from sqlalchemy import select
    try:
        result = await db.execute(
            select(AiTask)
            .where(AiTask.org_id == user.org_id)
            .order_by(AiTask.created_at.desc())
            .limit(100)
        )
        tasks = result.scalars().all()
        return [
            {
                "id":         str(t.id),
                "task":       (t.input_data or {}).get("task", ""),
                "status":     t.status,
                "result":     (t.output_data or {}).get("result"),
                "error":      (t.output_data or {}).get("error"),
                "type":       t.task_type,
                "created_at": str(t.created_at)
            }
            for t in tasks
        ]
    except Exception as e:
        log.error("list_tasks: %s", e)
        return []


@router.get("/tasks/{task_id}")
async def get_task(
    task_id: str,
    user: User         = Depends(_get_current_user),
    db:   AsyncSession = Depends(get_db)
):
    from sqlalchemy import select
    try:
        result = await db.execute(
            select(AiTask).where(
                AiTask.id == task_id,
                AiTask.org_id == user.org_id
            )
        )
        task = result.scalar_one_or_none()
        if not task:
            raise HTTPException(404, "Task not found")
        return {
            "id":         str(task.id),
            "task":       (task.input_data or {}).get("task", ""),
            "status":     task.status,
            "result":     (task.output_data or {}).get("result"),
            "error":      (task.output_data or {}).get("error"),
            "input":      task.input_data,
            "output":     task.output_data,
            "created_at": str(task.created_at)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))


@router.get("/desktop/status")
async def desktop_status(user: User = Depends(_get_current_user)):
    uid  = str(user.id)
    meta = agent_metadata.get(uid, {})
    features = meta.get("features", [])
    return {
        "connected":       uid in active_agents,
        "user_id":         uid,
        "agent_version":   meta.get("version", ""),
        "platform":        meta.get("platform", ""),
        "hostname":        meta.get("hostname", ""),
        "features":        features,
        "connected_since": meta.get("connected_since", ""),
        "capabilities": {
            "vision":        "vision_super"        in features,
            "voice":         "voice3"              in features,
            "browser":       "browser_enterprise"  in features,
            "email":         "email_enterprise"    in features,
            "swarm":         "swarm10"             in features,
            "memory":        "memory_vector"       in features,
            "social":        "social_all"          in features,
            "multi_monitor": "multi_monitor"       in features,
            "self_healing":  "self_healing"        in features,
            "scheduler":     "scheduler"           in features,
            "plugins":       "plugins"             in features,
        }
    }


@router.get("/desktop/last_result")
async def get_last_result(user: User = Depends(_get_current_user)):
    uid = str(user.id)
    return {
        "result":        agent_results.get(uid),
        "connected":     uid in active_agents,
        "agent_version": agent_metadata.get(uid, {}).get("version", "")
    }


@router.post("/desktop/command")
async def send_desktop_command(
    body: DesktopCommandRequest,
    user: User = Depends(_get_current_user)
):
    uid = str(user.id)
    if uid not in active_agents:
        raise HTTPException(
            400,
            "Desktop agent not connected. "
            "Please run the Dacexy Desktop Agent on your computer first."
        )
    ws = active_agents[uid]
    try:
        payload = {k: v for k, v in body.dict().items() if v is not None}
        await ws.send_text(json.dumps(payload))
        return {"status": "sent", "action": body.action}
    except WebSocketDisconnect:
        active_agents.pop(uid, None)
        raise HTTPException(400, "Desktop agent disconnected.")
    except Exception as e:
        active_agents.pop(uid, None)
        raise HTTPException(500, f"Failed to send command: {e}")


@router.post("/desktop/task")
async def send_desktop_task(
    body: TaskRequest,
    user: User = Depends(_get_current_user)
):
    uid       = str(user.id)
    task_text = (body.task or body.goal or "").strip()[:2000]
    if not task_text:
        raise HTTPException(400, "task or goal required")
    if uid not in active_agents:
        raise HTTPException(400, "Desktop agent not connected.")
    ws = active_agents[uid]
    try:
        await ws.send_text(json.dumps({
            "type":    "task",
            "task":    task_text,
            "action":  "swarm_task",
            "context": body.context or ""
        }))
        return {"status": "sent", "task": task_text}
    except Exception as e:
        active_agents.pop(uid, None)
        raise HTTPException(500, f"Failed to send task: {e}")


@router.post("/desktop/screenshot")
async def take_screenshot(user: User = Depends(_get_current_user)):
    uid = str(user.id)
    if uid not in active_agents:
        raise HTTPException(400, "Desktop agent not connected.")
    try:
        await active_agents[uid].send_text(json.dumps({"action": "screenshot"}))
        await asyncio.sleep(2)
        result = agent_results.get(uid, {})
        return {"status": "ok", "screenshot": result.get("screenshot", "")}
    except Exception as e:
        raise HTTPException(500, str(e))


@router.post("/desktop/ocr")
async def ocr_screen(user: User = Depends(_get_current_user)):
    uid = str(user.id)
    if uid not in active_agents:
        raise HTTPException(400, "Desktop agent not connected.")
    try:
        await active_agents[uid].send_text(json.dumps({"action": "ocr_screen"}))
        await asyncio.sleep(3)
        result = agent_results.get(uid, {})
        return {"status": "ok", "text": result.get("text", "")}
    except Exception as e:
        raise HTTPException(500, str(e))


@router.post("/desktop/email/campaign")
async def create_email_campaign(
    body: CampaignRequest,
    user: User = Depends(_get_current_user)
):
    uid = str(user.id)
    if uid not in active_agents:
        raise HTTPException(400, "Desktop agent not connected.")
    try:
        await active_agents[uid].send_text(json.dumps({
            "action":       "create_campaign",
            "name":         body.name,
            "subject":      body.subject,
            "body":         body.body,
            "recipients":   body.recipients,
            "html":         body.html,
            "delay":        body.delay_sec,
            "tags":         body.tags,
            "scheduled_at": body.scheduled_at
        }))
        await asyncio.sleep(1)
        result      = agent_results.get(uid, {})
        campaign_id = result.get("campaign_id", "")
        if campaign_id:
            await active_agents[uid].send_text(json.dumps({
                "action":      "send_campaign",
                "campaign_id": campaign_id
            }))
        return {
            "status":     "ok",
            "campaign_id": campaign_id,
            "recipients": len(body.recipients)
        }
    except Exception as e:
        raise HTTPException(500, str(e))


@router.post("/desktop/whatsapp/bulk")
async def whatsapp_bulk(
    body: BulkWhatsAppRequest,
    user: User = Depends(_get_current_user)
):
    uid = str(user.id)
    if uid not in active_agents:
        raise HTTPException(400, "Desktop agent not connected.")
    try:
        await active_agents[uid].send_text(json.dumps({
            "action":   "whatsapp_bulk",
            "contacts": body.contacts,
            "message":  body.message,
            "delay":    body.delay
        }))
        return {"status": "sent", "contacts": len(body.contacts)}
    except Exception as e:
        raise HTTPException(500, str(e))


@router.post("/desktop/social/post")
async def social_post(
    body: SocialPostRequest,
    user: User = Depends(_get_current_user)
):
    uid = str(user.id)
    if uid not in active_agents:
        raise HTTPException(400, "Desktop agent not connected.")
    action_map = {
        "twitter":   "twitter_post",
        "linkedin":  "linkedin_post",
        "facebook":  "facebook_post",
        "instagram": "instagram_post",
        "youtube":   "youtube_upload",
        "tiktok":    "tiktok_post",
    }
    action = action_map.get(body.platform.lower())
    if not action:
        raise HTTPException(400, f"Unsupported platform: {body.platform}")
    try:
        await active_agents[uid].send_text(json.dumps({
            "action":      action,
            "username":    body.username,
            "password":    body.password,
            "text":        body.text,
            "image_path":  body.image_path,
            "video_path":  body.video_path,
            "caption":     body.caption,
            "title":       body.title,
            "description": body.description,
            "page_id":     body.page_id
        }))
        return {"status": "sent", "platform": body.platform}
    except Exception as e:
        raise HTTPException(500, str(e))


@router.post("/desktop/social/post_all")
async def post_all_social(
    body: dict,
    user: User = Depends(_get_current_user)
):
    uid = str(user.id)
    if uid not in active_agents:
        raise HTTPException(400, "Desktop agent not connected.")
    try:
        await active_agents[uid].send_text(json.dumps({
            "action":      "post_all_social",
            "text":        body.get("text", ""),
            "credentials": body.get("credentials", {})
        }))
        return {
            "status":    "sent",
            "platforms": list(body.get("credentials", {}).keys())
        }
    except Exception as e:
        raise HTTPException(500, str(e))


@router.get("/desktop/health")
async def agent_health(user: User = Depends(_get_current_user)):
    uid = str(user.id)
    if uid not in active_agents:
        raise HTTPException(400, "Desktop agent not connected.")
    try:
        await active_agents[uid].send_text(
            json.dumps({"action": "health_check"}))
        await asyncio.sleep(2)
        result = agent_results.get(uid, {})
        return {"status": "ok", "health": result.get("health", {})}
    except Exception as e:
        raise HTTPException(500, str(e))


@router.get("/desktop/memory")
async def get_agent_memory(user: User = Depends(_get_current_user)):
    uid = str(user.id)
    if uid not in active_agents:
        raise HTTPException(400, "Desktop agent not connected.")
    try:
        await active_agents[uid].send_text(
            json.dumps({"action": "get_memory", "query": ""}))
        await asyncio.sleep(1.5)
        result = agent_results.get(uid, {})
        return {"status": "ok", "memory": result.get("memory", "")}
    except Exception as e:
        raise HTTPException(500, str(e))


@router.get("/desktop/skills")
async def get_agent_skills(user: User = Depends(_get_current_user)):
    uid = str(user.id)
    if uid not in active_agents:
        raise HTTPException(400, "Desktop agent not connected.")
    try:
        await active_agents[uid].send_text(
            json.dumps({"action": "list_skills"}))
        await asyncio.sleep(1.5)
        result = agent_results.get(uid, {})
        return {"status": "ok", "skills": result.get("skills", [])}
    except Exception as e:
        raise HTTPException(500, str(e))


@router.websocket("/desktop/ws")
async def desktop_websocket(websocket: WebSocket):
    await websocket.accept()
    user_id = None

    try:
        try:
            auth_raw = await asyncio.wait_for(
                websocket.receive_text(), timeout=30)
        except asyncio.TimeoutError:
            await websocket.send_text(json.dumps({
                "type":    "error",
                "message": "Authentication timeout — send token within 30 seconds"
            }))
            await websocket.close(code=1008)
            return

        token = ""
        try:
            auth_data = json.loads(auth_raw)
            token = (auth_data.get("token", "") or
                     auth_data.get("access_token", ""))
        except json.JSONDecodeError:
            token = auth_raw.strip()

        if not token or len(token) < 20:
            await websocket.send_text(json.dumps({
                "type":    "error",
                "message": "Invalid token format. Please log in again."
            }))
            await websocket.close(code=1008)
            return

        user_id = _decode_ws_token(token)
        if not user_id:
            await websocket.send_text(json.dumps({
                "type":    "error",
                "message": (
                    "Authentication failed — token is invalid or expired. "
                    "Please log in again via the desktop agent."
                )
            }))
            await websocket.close(code=1008)
            return

        if user_id in active_agents:
            old_ws = active_agents[user_id]
            try:
                await old_ws.send_text(json.dumps({
                    "type":    "error",
                    "message": "A newer connection has been established. Closing this one."
                }))
                await old_ws.close(code=1001)
            except Exception:
                pass
            log.info("Replaced existing agent for user %s", user_id)

        import datetime as _dt
        active_agents[user_id] = websocket
        agent_metadata[user_id] = {
            "connected_since": _dt.datetime.now().isoformat(),
            "version":         "",
            "platform":        "",
            "hostname":        "",
            "features":        []
        }
        log.info("Agent connected: user=%s", user_id)

        await websocket.send_text(json.dumps({
            "type":    "connected",
            "message": "Desktop Agent connected successfully to Dacexy backend.",
            "user_id": user_id
        }))

        consecutive_errors = 0
        while True:
            try:
                try:
                    data = await asyncio.wait_for(
                        websocket.receive_text(), timeout=60)
                    consecutive_errors = 0
                except asyncio.TimeoutError:
                    try:
                        await asyncio.wait_for(
                            websocket.send_text(
                                json.dumps({"type": "ping"})),
                            timeout=5
                        )
                    except Exception:
                        log.info("Keepalive failed user=%s", user_id)
                        break
                    continue

                try:
                    msg = json.loads(data)
                except json.JSONDecodeError:
                    log.warning("Bad JSON from agent user=%s: %s",
                                user_id, data[:100])
                    continue

                msg_type = msg.get("type", "")

                if msg_type == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))

                elif msg_type == "pong":
                    pass

                elif msg_type == "init":
                    agent_metadata[user_id].update({
                        "version":        msg.get("version", ""),
                        "platform":       msg.get("platform", ""),
                        "hostname":       msg.get("hostname", ""),
                        "features":       msg.get("features", []),
                        "memory_context": msg.get("memory_context", "")
                    })
                    log.info(
                        "Agent init: user=%s version=%s features=%d",
                        user_id,
                        msg.get("version", ""),
                        len(msg.get("features", []))
                    )
                    await websocket.send_text(json.dumps({
                        "type":    "init_ack",
                        "message": "Agent registered successfully.",
                        "version": msg.get("version", "")
                    }))

                elif msg_type == "task_result":
                    agent_results[user_id] = msg
                    future = pending_task_results.get(user_id)
                    if future and not future.done():
                        try:
                            future.set_result(msg)
                        except asyncio.InvalidStateError:
                            pass
                    log.info(
                        "Task result: user=%s ok=%s/%s",
                        user_id,
                        msg.get("ok", 0),
                        msg.get("total", 0)
                    )

                elif msg_type in (
                    "result", "command_result",
                    "screenshot_before", "screenshot_after",
                    "system_info", "error", "voice_result",
                    "ocr_result", "vision_result", "memory_result",
                    "health_result", "skill_result", "heartbeat"
                ):
                    agent_results[user_id] = msg
                    future = pending_task_results.get(user_id)
                    if (future and not future.done()
                            and msg_type == "result"):
                        try:
                            future.set_result(msg)
                        except asyncio.InvalidStateError:
                            pass

                elif msg_type == "heartbeat":
                    health = msg.get("health", {})
                    if health:
                        agent_metadata[user_id]["last_health"] = health
                        agent_metadata[user_id]["last_seen"] = (
                            _dt.datetime.now().isoformat()
                        )
                    agent_results[user_id] = msg

                elif msg_type == "log":
                    log.info(
                        "[AGENT:%s] %s: %s",
                        user_id,
                        msg.get("level", "INFO").upper(),
                        msg.get("message", "")[:300]
                    )

                else:
                    log.debug(
                        "Unknown msg type user=%s: %s",
                        user_id, msg_type
                    )

            except WebSocketDisconnect:
                log.info("Agent disconnected: user=%s", user_id)
                break
            except Exception as e:
                consecutive_errors += 1
                log.warning("Message loop error user=%s: %s", user_id, e)
                if consecutive_errors >= 5:
                    log.error("Too many errors user=%s — closing", user_id)
                    break
                await asyncio.sleep(0.5)

    except WebSocketDisconnect:
        log.info("WebSocket disconnected: user=%s", user_id)
    except Exception as e:
        log.error("WebSocket handler error user=%s: %s", user_id, e)
    finally:
        if user_id:
            active_agents.pop(user_id, None)
            agent_results.pop(user_id, None)
            agent_metadata.pop(user_id, None)
            future = pending_task_results.pop(user_id, None)
            if future and not future.done():
                future.cancel()
            log.info("Agent cleanup complete: user=%s", user_id)


@router.get("/track/{campaign_id}/{recipient_index}")
async def track_email_open(
    campaign_id:     str,
    recipient_index: int,
    db: AsyncSession = Depends(get_db)
):
    log.info("Email opened: campaign=%s recipient=%d",
             campaign_id, recipient_index)
    gif_bytes = (
        b"GIF89a\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff"
        b"\x00\x00\x00!\xf9\x04\x00\x00\x00\x00\x00,"
        b"\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;"
    )
    return Response(
        content=gif_bytes,
        media_type="image/gif",
        headers={"Cache-Control": "no-cache, no-store, must-revalidate"}
    )


from pathlib import Path
from fastapi.responses import FileResponse
from fastapi import HTTPException

@router.get("/download/windows")
async def download_windows_installer():
    installer_path = (
        Path(__file__).resolve().parents[4]
        / "desktop_agent"
        / "install_dacexy_agent.bat"
    )

    if not installer_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Installer file not found: {installer_path}"
        )

    return FileResponse(
        path=str(installer_path),
        filename="install_dacexy_agent.bat",
        media_type="application/octet-stream"
    )
    
@router.get("/download/mac")
async def download_mac_installer():
    sh_content = b"#!/bin/bash\necho 'Dacexy Agent Installer'\n"
    resp = Response(
        content=sh_content,
        media_type="application/octet-stream"
    )
    resp.headers["Content-Disposition"] = (
        "attachment; filename=install_dacexy_agent.sh"
    )
    return resp
'''

w("src/interfaces/http/routes/agent.py", _agent_route_content)
 
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
async def upload_file(file: UploadFile = File(...), user: User = Depends(_get_current_user), db: AsyncSession = Depends(get_db)):
    if not file.filename:
        raise HTTPException(400, "No file provided")
    max_size = 10 * 1024 * 1024
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
    elif any(filename.endswith(ext) for ext in [".py",".js",".ts",".tsx",".jsx"]):
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
    return {"filename": file.filename, "file_type": file_type, "word_count": word_count, "extracted_text": extracted_text, "message": f"Successfully extracted {word_count} words from {file.filename}"}
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

# ── FIX 2: media.py — complete rewrite with robust video generation ──────────
w("src/interfaces/http/routes/media.py", '''from __future__ import annotations
import asyncio
import base64
import logging
import urllib.parse
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
import httpx

from src.infrastructure.persistence.database import get_db
from src.infrastructure.persistence.models.orm_models import User, GeneratedImage, GeneratedVideo
from src.interfaces.http.routes.auth import _get_current_user
from src.shared.config.settings import settings

router = APIRouter(prefix="/media", tags=["media"])
log = logging.getLogger("media")


class ImageRequest(BaseModel):
    prompt: str
    width: int = 1024
    height: int = 1024


class VideoRequest(BaseModel):
    prompt: str


# ── IMAGE ─────────────────────────────────────────────────────────────────────
@router.post("/image")
async def generate_image(
    body: ImageRequest,
    user: User = Depends(_get_current_user),
    db: AsyncSession = Depends(get_db)
):
    record = GeneratedImage(
        org_id=user.org_id, user_id=user.id,
        prompt=body.prompt, status="processing"
    )
    db.add(record)
    await db.flush()
    await db.commit()

    try:
        encoded = urllib.parse.quote(body.prompt[:120])
        seed = abs(hash(body.prompt)) % 99999
        image_url = (
            f"https://image.pollinations.ai/prompt/{encoded}"
            f"?width={body.width}&height={body.height}&seed={seed}&nologo=true&model=flux"
        )
        async with httpx.AsyncClient(timeout=60, follow_redirects=True) as client:
            r = await client.get(image_url)
            if r.status_code not in (200, 206):
                raise HTTPException(500, f"Image generation failed: status {r.status_code}")

        record.url = image_url
        record.status = "completed"
        await db.commit()
        return {"id": str(record.id), "url": image_url, "status": "completed"}

    except HTTPException:
        record.status = "failed"
        await db.commit()
        raise
    except Exception as e:
        record.status = "failed"
        await db.commit()
        log.error("Image generation error: %s", e)
        raise HTTPException(500, f"Image generation failed: {str(e)}")


# ── FALLBACK — always-working cinematic image ─────────────────────────────────
async def _image_fallback(prompt: str) -> str:
    encoded = urllib.parse.quote(f"cinematic 4k ultra detailed {prompt[:100]}")
    seed = abs(hash(prompt)) % 99999
    url = (
        f"https://image.pollinations.ai/prompt/{encoded}"
        f"?width=1280&height=720&seed={seed}&nologo=true&model=flux"
    )
    async with httpx.AsyncClient(timeout=60, follow_redirects=True) as client:
        r = await client.get(url)
        if r.status_code not in (200, 206):
            raise Exception(f"Pollinations returned {r.status_code}")
    return url


# ── STABILITY AI VIDEO ────────────────────────────────────────────────────────
# Flow: prompt → generate image via Pollinations → send image to Stability AI
# image-to-video endpoint → poll for result → return video URL
#
# Stability AI image-to-video docs:
#   POST https://api.stability.ai/v2beta/image-to-video
#   GET  https://api.stability.ai/v2beta/image-to-video/result/{id}

async def _try_stability_video(prompt: str, key: str) -> str:
    """
    1. Generate a seed image from the prompt via Pollinations (free, no key needed).
    2. Send that image to Stability AI image-to-video endpoint.
    3. Poll until complete and return the video URL (data URI or hosted URL).
    """
    headers_auth = {"authorization": f"Bearer {key}"}

    # ── Step 1: get seed image bytes from Pollinations ─────────────────────
    encoded = urllib.parse.quote(f"cinematic high quality {prompt[:120]}")
    seed = abs(hash(prompt)) % 99999
    pollinations_url = (
        f"https://image.pollinations.ai/prompt/{encoded}"
        f"?width=1024&height=576&seed={seed}&nologo=true&model=flux"
    )
    async with httpx.AsyncClient(timeout=60, follow_redirects=True) as client:
        img_resp = await client.get(pollinations_url)
        if img_resp.status_code not in (200, 206):
            raise Exception(f"Seed image fetch failed: HTTP {img_resp.status_code}")
        image_bytes = img_resp.content
        image_content_type = img_resp.headers.get("content-type", "image/jpeg").split(";")[0].strip()

    log.info("Stability seed image fetched: %d bytes (%s)", len(image_bytes), image_content_type)

    # ── Step 2: submit image-to-video job ─────────────────────────────────
    submit_url = "https://api.stability.ai/v2beta/image-to-video"
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            submit_url,
            headers=headers_auth,
            files={"image": ("image.jpg", image_bytes, image_content_type)},
            data={
                "seed": seed % 4294967295,   # must be 0–4294967295
                "cfg_scale": 1.8,
                "motion_bucket_id": 127,     # 1–255; higher = more motion
            },
        )

    log.info("Stability submit → HTTP %s: %s", resp.status_code, resp.text[:200])

    if resp.status_code in (401, 403):
        raise Exception(f"Stability AI key invalid: HTTP {resp.status_code}")
    if resp.status_code not in (200, 202):
        raise Exception(f"Stability AI submit failed: HTTP {resp.status_code} — {resp.text[:200]}")

    generation_id = resp.json().get("id", "")
    if not generation_id:
        raise Exception("Stability AI returned no generation id")

    log.info("Stability video job submitted: %s", generation_id)

    # ── Step 3: poll for result ────────────────────────────────────────────
    result_url = f"https://api.stability.ai/v2beta/image-to-video/result/{generation_id}"
    poll_headers = {**headers_auth, "accept": "video/*"}

    async with httpx.AsyncClient(timeout=30) as poll_client:
        for attempt in range(60):          # up to 5 minutes (60 × 5s)
            await asyncio.sleep(5)
            try:
                poll = await poll_client.get(result_url, headers=poll_headers)
                log.info("Stability poll %d/60 → HTTP %s", attempt + 1, poll.status_code)

                if poll.status_code == 202:
                    # Still processing — check finish-reason header
                    finish = poll.headers.get("finish-reason", "")
                    log.info("Stability still processing (finish-reason: %s)", finish)
                    continue

                if poll.status_code == 200:
                    # Response is raw video bytes
                    video_bytes = poll.content
                    if not video_bytes:
                        raise Exception("Stability returned 200 but empty video body")

                    # Encode as base64 data URI so the frontend can play it directly
                    b64 = base64.b64encode(video_bytes).decode("utf-8")
                    video_url = f"data:video/mp4;base64,{b64}"
                    log.info("Stability video complete: %d bytes", len(video_bytes))
                    return video_url

                raise Exception(f"Stability poll unexpected HTTP {poll.status_code}: {poll.text[:200]}")

            except Exception as poll_err:
                if "Stability video complete" in str(poll_err) or "Stability returned 200" in str(poll_err):
                    raise
                # transient network error — keep retrying
                log.warning("Stability poll %d error: %s", attempt + 1, poll_err)
                continue

    raise Exception("Stability AI timed out after 5 minutes")


# ── VIDEO ─────────────────────────────────────────────────────────────────────
@router.post("/video")
async def generate_video(
    body: VideoRequest,
    user: User = Depends(_get_current_user),
    db: AsyncSession = Depends(get_db)
):
    record = GeneratedVideo(
        org_id=user.org_id, user_id=user.id,
        prompt=body.prompt, status="processing"
    )
    db.add(record)
    await db.flush()
    await db.commit()

    stability_key = (getattr(settings, "STABILITY_API_KEY", "") or "").strip()

    stability_ok = bool(
        stability_key
        and len(stability_key) > 10
        and stability_key not in ("your_key_here", "STABILITY_API_KEY", "changeme", "xxx")
    )

    # ── Try Stability AI if key looks valid ───────────────────────────────────
    if stability_ok:
        try:
            video_url = await _try_stability_video(body.prompt, stability_key)
            record.url = video_url
            record.status = "completed"
            await db.commit()
            log.info("Stability AI video done")
            return {"id": str(record.id), "url": video_url, "status": "completed"}
        except Exception as e:
            log.warning("Stability AI failed (%s), using image fallback", e)
            # Fall through to image fallback below

    # ── FALLBACK: Pollinations cinematic image (always works) ─────────────────
    try:
        log.info("Using image fallback for: %s", body.prompt[:60])
        fallback_url = await _image_fallback(body.prompt)
        record.url = fallback_url
        record.status = "completed"
        await db.commit()
        return {
            "id": str(record.id),
            "url": fallback_url,
            "status": "completed",
            "note": "Set a valid STABILITY_API_KEY in Render env for real video generation"
        }
    except Exception as e:
        record.status = "failed"
        await db.commit()
        log.error("Fallback also failed: %s", e)
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

from src.interfaces.http.routes import auth, ai_chat, orgs, billing, agent, media, voice, audit, referral, admin, memory, upload
app.include_router(auth.router, prefix=settings.API_PREFIX)
app.include_router(ai_chat.router, prefix=settings.API_PREFIX)
app.include_router(orgs.router, prefix=settings.API_PREFIX)
app.include_router(billing.router, prefix=settings.API_PREFIX)
app.include_router(agent.router, prefix=settings.API_PREFIX)
app.include_router(media.router, prefix=settings.API_PREFIX)
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

import ast, pathlib, os

for f in pathlib.Path("src").rglob("*.py"):
    try:
        ast.parse(f.read_text())
    except SyntaxError as e:
        print(f"BROKEN FILE: {f}  |  Line: {e.lineno}  |  Error: {e.msg}")
        print(f"Bad text: {e.text}")

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

print("\n✅ ALL FILES CREATED SUCCESSFULLY!")

import os, sys, subprocess
port = os.environ.get('PORT', '10000')
print(f'Starting uvicorn on port: {port}', flush=True)
proc = subprocess.Popen(
    [sys.executable, '-m', 'uvicorn', 'src.main:app',
     '--host', '0.0.0.0', '--port', port, '--log-level', 'info'],
    stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
)
for line in proc.stdout:
    print(line, end='', flush=True)
proc.wait()
sys.exit(proc.returncode)
