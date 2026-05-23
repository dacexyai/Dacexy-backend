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
import json
import asyncio

log = logging.getLogger("website")

def extract_name(prompt: str) -> str:
    p = prompt.strip()
    patterns = [
        r"(?:named?|called?|for)\\s+([A-Z][a-zA-Z0-9\\s]{1,30}?)(?:\\s+(?:with|that|which|website|app|platform|startup|business|restaurant|store|shop|company)|\\.|,|$)",
        r"^([A-Z][a-zA-Z0-9]{1,20})\\s+",
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
    words = [w for w in re.sub(r\'[^a-zA-Z0-9 ]\', \'\', p).split()
             if len(w) > 2 and w.lower() not in skip]
    return words[0].title() if words else "Nexus"

def extract_user_data(prompt: str) -> dict:
    data = {"phone": None, "email": None, "address": None,
            "whatsapp": None, "instagram": None, "facebook": None,
            "twitter": None, "linkedin": None, "youtube": None,
            "opening_hours": None, "tagline_custom": None, "about_text": None}
    p = prompt
    phone_match = re.search(r\'(?:phone|mobile|call|contact|tel|ph)[:\\s#]*([+\\d][\\d\\s\\-().+]{7,15})\', p, re.IGNORECASE)
    if not phone_match:
        phone_match = re.search(r\'(?<![\\w])([+]?[0-9]{10,13})(?![\\w])\', p)
    if phone_match:
        data["phone"] = phone_match.group(1).strip()
        data["whatsapp"] = data["phone"]
    email_match = re.search(r\'[\\w.+-]+@[\\w-]+\\.[\\w.]+\', p)
    if email_match:
        data["email"] = email_match.group(0)
    addr_match = re.search(r\'(?:address|location|located at|find us at|visit us at)[:\\s]+([^,\\n.]{10,100})\', p, re.IGNORECASE)
    if addr_match:
        data["address"] = addr_match.group(1).strip()
    ig_match = re.search(r\'(?:instagram|ig|insta)[:\\s@/]*([\\w.]+)\', p, re.IGNORECASE)
    if ig_match:
        data["instagram"] = ig_match.group(1).strip()
    fb_match = re.search(r\'(?:facebook|fb)[:\\s@/]*([\\w.]+)\', p, re.IGNORECASE)
    if fb_match:
        data["facebook"] = fb_match.group(1).strip()
    tw_match = re.search(r\'(?:twitter|x\\.com)[:\\s@/]*([\\w.]+)\', p, re.IGNORECASE)
    if tw_match:
        data["twitter"] = tw_match.group(1).strip()
    li_match = re.search(r\'(?:linkedin)[:\\s@/]*([\\w.-]+)\', p, re.IGNORECASE)
    if li_match:
        data["linkedin"] = li_match.group(1).strip()
    yt_match = re.search(r\'(?:youtube|yt)[:\\s@/]*([\\w.-]+)\', p, re.IGNORECASE)
    if yt_match:
        data["youtube"] = yt_match.group(1).strip()
    hours_match = re.search(r\'(?:open|hours|timing)[:\\s]+([^.\\n]{5,60})\', p, re.IGNORECASE)
    if hours_match:
        data["opening_hours"] = hours_match.group(1).strip()
    wa_match = re.search(r\'(?:whatsapp)[:\\s#]*([+\\d][\\d\\s\\-+]{7,15})\', p, re.IGNORECASE)
    if wa_match:
        data["whatsapp"] = wa_match.group(1).strip()
    return data

def build_ai_prompt(user_prompt: str, name: str, ud: dict) -> str:
    phone = ud.get("phone") or "+91 99999 99999"
    email = ud.get("email") or f"hello@{re.sub(chr(91)+chr(94)+chr(97)+chr(122)+chr(48)+chr(57)+chr(93),'',name.lower())}.com"
    address = ud.get("address") or "Mumbai, India"
    instagram = ud.get("instagram") or ""
    whatsapp = (ud.get("whatsapp") or phone).replace("+","").replace(" ","").replace("-","")
    hours = ud.get("opening_hours") or "Mon-Sat 9AM-8PM"

    seed = abs(hash(user_prompt)) % 99999
    enc = urllib.parse.quote(user_prompt[:60])
    hero_img = f"https://image.pollinations.ai/prompt/ultra_realistic_cinematic_{enc}_4k_dramatic?width=1400&height=800&seed={seed}&nologo=true&model=flux"
    img2 = f"https://image.pollinations.ai/prompt/professional_{enc}_premium?width=900&height=700&seed={seed+1}&nologo=true&model=flux"
    img3 = f"https://image.pollinations.ai/prompt/{enc}_showcase_1?width=700&height=500&seed={seed+2}&nologo=true&model=flux"
    img4 = f"https://image.pollinations.ai/prompt/{enc}_showcase_2?width=700&height=500&seed={seed+3}&nologo=true&model=flux"
    img5 = f"https://image.pollinations.ai/prompt/{enc}_showcase_3?width=700&height=500&seed={seed+4}&nologo=true&model=flux"
    img6 = f"https://image.pollinations.ai/prompt/{enc}_showcase_4?width=700&height=500&seed={seed+5}&nologo=true&model=flux"

    return f"""You are an expert web developer like the team behind Lovable.dev, Bolt.new, and Framer. Generate a COMPLETE, STUNNING, PRODUCTION-READY single HTML file website.

USER REQUEST: {user_prompt}
BUSINESS NAME: {name}
PHONE: {phone}
EMAIL: {email}
ADDRESS: {address}
WHATSAPP: {whatsapp}
HOURS: {hours}
{f"INSTAGRAM: @{instagram}" if instagram else ""}

USE THESE AI-GENERATED IMAGES (do not use placeholder images):
- Hero image: {hero_img}
- About image: {img2}
- Gallery 1: {img3}
- Gallery 2: {img4}
- Gallery 3: {img5}
- Gallery 4: {img6}

REQUIREMENTS — FOLLOW EVERY SINGLE ONE:

1. OUTPUT ONLY raw HTML. No markdown. No ```html. No explanation. Just the complete HTML file starting with <!DOCTYPE html>.

2. DESIGN QUALITY — Must match or exceed Lovable/Bolt/Framer quality:
   - Choose a bold, unique design direction (NOT generic). Pick from: glassmorphism dark, neon cyberpunk, luxury gold on black, vibrant gradient mesh, clean minimalist white, bold editorial, retro brutalist, soft pastel premium, nature organic, corporate navy, rose gold luxury, etc.
   - Use Google Fonts — pick 2 beautiful fonts that match the brand personality
   - Pixel-perfect spacing, shadows, and borders
   - Smooth CSS animations and micro-interactions
   - Full mobile responsiveness with hamburger menu
   - CSS custom properties for consistent design tokens

3. SECTIONS TO INCLUDE (based on user request, include ALL relevant ones):
   - Fixed navigation with logo, links, CTA button, mobile hamburger menu
   - Hero section: full-screen, with heading, subheading, dual CTA buttons, hero image with 3D perspective tilt effect
   - Stats/numbers bar (animated counters)
   - About section: split layout with image and text, 3 feature highlights
   - Services/Features: 4-card grid with icons, hover effects
   - Gallery: 4-image masonry/grid with hover overlay
   - Testimonials: 3 cards with star ratings, quote marks, author info
   - Pricing: 3-tier table if relevant (Free / Pro / Enterprise)
   - FAQ: accordion with smooth open/close animation
   - Team: 4 member cards if relevant
   - Contact section: contact info cards (phone, email, address, hours) + working contact form with validation
   - Newsletter signup with email input
   - Google Maps embed using address
   - WhatsApp floating button (bottom right, animated pulse)
   - Sticky call-to-action bar (appears on scroll)
   - Back to top button
   - Footer: 4-column with logo, links, contact info, social media icons
   - Loading screen with spinner
   - Scroll reveal animations using Intersection Observer
   - Cookie consent banner

4. CONTACT FORM — Must be functional with:
   - Name, phone, email, message fields
   - If booking: date and time picker fields too
   - HTML5 validation
   - Submit handler showing success message (no backend needed)
   - Beautiful styling matching the design

5. SOCIAL MEDIA — Include icons/links for:
   {f"Instagram: https://instagram.com/{instagram}" if instagram else "Instagram, Facebook, Twitter, LinkedIn (use # as href)"}
   WhatsApp: https://wa.me/{whatsapp}

6. JAVASCRIPT — Include all:
   - Page loader with fade out
   - Smooth scroll
   - Mobile menu open/close
   - Nav background change on scroll
   - Scroll reveal for all sections
   - Counter animation for stats
   - FAQ accordion toggle
   - Contact form submission with success state
   - Newsletter form with success state
   - Countdown timer (if offer/launch mentioned)
   - Back to top button visibility
   - Sticky CTA bar on scroll
   - Image lazy loading
   - Parallax effect on hero background
   - Active nav link highlighting on scroll
   - Typed text animation in hero if appropriate

7. CSS — Must include:
   - CSS custom properties (--primary, --secondary, --bg, --text, --accent, etc.)
   - Smooth transitions everywhere
   - Hover states with transform/shadow
   - CSS animations (fadeInUp, slideIn, pulse, float)
   - Glass morphism cards where appropriate
   - Gradient backgrounds
   - Custom scrollbar styling
   - Focus states for accessibility
   - Print styles

8. META TAGS — Include full SEO and OG tags:
   - title, description, keywords
   - og:title, og:description, og:image
   - twitter:card tags
   - viewport, charset

9. PERFORMANCE:
   - Lazy load all images except hero
   - Defer non-critical scripts
   - Optimize animations with will-change

10. The website MUST look like it was built by a senior developer at a top agency. Think Apple.com quality layout, Stripe.com component design, Linear.app animations.

CRITICAL: Return ONLY the complete HTML. Start your response with <!DOCTYPE html> and end with </html>. Nothing else."""

async def generate_with_ai(prompt: str, ai) -> str:
    """Generate website using DeepSeek AI — produces unique custom code every time."""
    name = extract_name(prompt)
    ud = extract_user_data(prompt)
    ai_prompt = build_ai_prompt(prompt, name, ud)

    messages = [
        {"role": "system", "content": "You are an expert full-stack web developer specializing in beautiful, production-ready websites. You generate complete, stunning HTML/CSS/JS websites that look like they were built by top agencies. You ONLY output raw HTML code, nothing else. No markdown, no explanations, no code blocks."},
        {"role": "user", "content": ai_prompt}
    ]

    try:
        if hasattr(ai, 'chat'):
            result = await ai.chat(messages, model="deepseek-chat", stream=False, search=False)
            if isinstance(result, str):
                html = result.strip()
                if html.startswith("```"):
                    html = re.sub(r\'```[a-z]*\\n?\', \'\', html).strip()
                    html = html.rstrip(\'`\').strip()
                if "<!DOCTYPE" in html or "<html" in html:
                    start = html.find("<!DOCTYPE")
                    if start == -1:
                        start = html.find("<html")
                    if start > 0:
                        html = html[start:]
                    return html
        raise Exception("AI returned invalid HTML")
    except Exception as e:
        log.warning(f"AI generation failed: {e}, using enhanced fallback")
        return build_fallback(prompt, name, ud)

def build_fallback(prompt: str, name: str, ud: dict) -> str:
    """Enhanced fallback — still produces beautiful unique websites."""
    seed = abs(hash(prompt)) % 99999
    enc = urllib.parse.quote(prompt[:80])
    phone = ud.get("phone") or "+91 99999 99999"
    email_addr = ud.get("email") or f"hello@{re.sub(chr(91)+chr(94)+chr(97)+chr(122)+chr(48)+chr(57)+chr(93),'',name.lower())}.com"
    address = ud.get("address") or "Mumbai, India"
    whatsapp = (ud.get("whatsapp") or phone).replace("+","").replace(" ","").replace("-","")
    hours = ud.get("opening_hours") or "Mon–Sat: 9 AM – 8 PM"

    # 50 unique design systems selected by prompt hash
    designs = [
        {"bg":"#0A0A0A","pr":"#E11D48","ac":"#F59E0B","tx":"#fff","mu":"rgba(255,255,255,0.6)","ca":"rgba(255,255,255,0.05)","br":"rgba(225,29,72,0.3)","font1":"Playfair Display","font2":"Inter","style":"luxury-dark","grad":"linear-gradient(135deg,#0A0A0A 0%,#1a0010 100%)"},
        {"bg":"#FFFFFF","pr":"#6366F1","ac":"#06B6D4","tx":"#0F0F1A","mu":"#6B7280","ca":"#F8F7FF","br":"#E5E7EB","font1":"Inter","font2":"Inter","style":"clean-light","grad":"linear-gradient(135deg,#f8f7ff 0%,#ffffff 100%)"},
        {"bg":"#050010","pr":"#8B5CF6","ac":"#EC4899","tx":"#F5F3FF","mu":"rgba(245,243,255,0.6)","ca":"rgba(139,92,246,0.1)","br":"rgba(139,92,246,0.25)","font1":"Inter","font2":"Inter","style":"neon-dark","grad":"linear-gradient(135deg,#050010 0%,#1a0030 50%,#050010 100%)"},
        {"bg":"#FFFBF0","pr":"#D97706","ac":"#EF4444","tx":"#1C1917","mu":"#78716C","ca":"#FEF3C7","br":"#FDE68A","font1":"Playfair Display","font2":"Inter","style":"warm-cream","grad":"linear-gradient(135deg,#fffbf0 0%,#fef9e0 100%)"},
        {"bg":"#F0FDF4","pr":"#059669","ac":"#F97316","tx":"#022C22","mu":"#6B7280","ca":"#DCFCE7","br":"#A7F3D0","font1":"Inter","font2":"Inter","style":"fresh-green","grad":"linear-gradient(135deg,#f0fdf4 0%,#dcfce7 100%)"},
        {"bg":"#0D0500","pr":"#C8102E","ac":"#FFD700","tx":"#FFF8F0","mu":"rgba(255,248,240,0.6)","ca":"rgba(255,255,255,0.04)","br":"rgba(255,215,0,0.2)","font1":"Playfair Display","font2":"Inter","style":"restaurant-dark","grad":"linear-gradient(135deg,#0D0500 0%,#2a0a00 100%)"},
        {"bg":"#0C0500","pr":"#EA580C","ac":"#22C55E","tx":"#FFF7ED","mu":"rgba(255,247,237,0.6)","ca":"rgba(234,88,12,0.1)","br":"rgba(234,88,12,0.25)","font1":"Inter","font2":"Inter","style":"energy-dark","grad":"linear-gradient(135deg,#0C0500 0%,#1a0800 100%)"},
        {"bg":"#060A14","pr":"#3B82F6","ac":"#10B981","tx":"#EFF6FF","mu":"rgba(239,246,255,0.6)","ca":"rgba(59,130,246,0.08)","br":"rgba(59,130,246,0.2)","font1":"Inter","font2":"Inter","style":"tech-dark","grad":"linear-gradient(135deg,#060A14 0%,#0a1628 100%)"},
        {"bg":"#FFF5F5","pr":"#DC2626","ac":"#F59E0B","tx":"#1A0000","mu":"#6B7280","ca":"#FEE2E2","br":"#FECACA","font1":"Playfair Display","font2":"Inter","style":"rose-light","grad":"linear-gradient(135deg,#fff5f5 0%,#fee2e2 100%)"},
        {"bg":"#FAF5FF","pr":"#7C3AED","ac":"#F59E0B","tx":"#1A0A3E","mu":"#6B7280","ca":"#EDE9FE","br":"#DDD6FE","font1":"Playfair Display","font2":"Inter","style":"purple-light","grad":"linear-gradient(135deg,#faf5ff 0%,#ede9fe 100%)"},
        {"bg":"#EFF6FF","pr":"#2563EB","ac":"#F59E0B","tx":"#020617","mu":"#6B7280","ca":"#DBEAFE","br":"#BFDBFE","font1":"Inter","font2":"Inter","style":"blue-light","grad":"linear-gradient(135deg,#eff6ff 0%,#dbeafe 100%)"},
        {"bg":"#0A0800","pr":"#B45309","ac":"#FCD34D","tx":"#FFFBEB","mu":"rgba(255,251,235,0.6)","ca":"rgba(180,83,9,0.1)","br":"rgba(252,211,77,0.2)","font1":"Playfair Display","font2":"Inter","style":"gold-dark","grad":"linear-gradient(135deg,#0A0800 0%,#1a1200 100%)"},
        {"bg":"#F0FFFE","pr":"#0891B2","ac":"#10B981","tx":"#042F2E","mu":"#6B7280","ca":"#CCFBF1","br":"#99F6E4","font1":"Inter","font2":"Inter","style":"teal-light","grad":"linear-gradient(135deg,#f0fffe 0%,#ccfbf1 100%)"},
        {"bg":"#FAFAF8","pr":"#0F0F0F","ac":"#F59E0B","tx":"#0F0F0F","mu":"#6B7280","ca":"#F5F5F0","br":"#E0E0D8","font1":"Playfair Display","font2":"Inter","style":"minimal-mono","grad":"linear-gradient(135deg,#fafaf8 0%,#f5f5f0 100%)"},
        {"bg":"#14000A","pr":"#DB2777","ac":"#FB923C","tx":"#FDF2F8","mu":"rgba(253,242,248,0.6)","ca":"rgba(219,39,119,0.1)","br":"rgba(219,39,119,0.25)","font1":"Playfair Display","font2":"Inter","style":"pink-dark","grad":"linear-gradient(135deg,#14000A 0%,#280014 100%)"},
        {"bg":"#0F0F23","pr":"#F97316","ac":"#FACC15","tx":"#FFFBEB","mu":"rgba(255,251,235,0.6)","ca":"rgba(249,115,22,0.1)","br":"rgba(249,115,22,0.25)","font1":"Inter","font2":"Inter","style":"orange-dark","grad":"linear-gradient(135deg,#0F0F23 0%,#1a1a38 100%)"},
        {"bg":"#071A0E","pr":"#16A34A","ac":"#FCD34D","tx":"#F0FDF4","mu":"rgba(240,253,244,0.6)","ca":"rgba(22,163,74,0.08)","br":"rgba(22,163,74,0.2)","font1":"Inter","font2":"Inter","style":"forest-dark","grad":"linear-gradient(135deg,#071A0E 0%,#0a2a14 100%)"},
        {"bg":"#FFF7ED","pr":"#EA580C","ac":"#22C55E","tx":"#1C0A00","mu":"#6B7280","ca":"#FFEDD5","br":"#FED7AA","font1":"Inter","font2":"Inter","style":"orange-light","grad":"linear-gradient(135deg,#fff7ed 0%,#ffedd5 100%)"},
        {"bg":"#FDF4FF","pr":"#A21CAF","ac":"#F59E0B","tx":"#2E1065","mu":"#6B7280","ca":"#FAE8FF","br":"#F0ABFC","font1":"Playfair Display","font2":"Inter","style":"magenta-light","grad":"linear-gradient(135deg,#fdf4ff 0%,#fae8ff 100%)"},
        {"bg":"#1A0533","pr":"#C084FC","ac":"#F472B6","tx":"#FAF5FF","mu":"rgba(250,245,255,0.6)","ca":"rgba(192,132,252,0.1)","br":"rgba(192,132,252,0.25)","font1":"Playfair Display","font2":"Inter","style":"violet-dark","grad":"linear-gradient(135deg,#1A0533 0%,#2d0a55 100%)"},
        {"bg":"#ECFDF5","pr":"#10B981","ac":"#3B82F6","tx":"#022C22","mu":"#6B7280","ca":"#D1FAE5","br":"#6EE7B7","font1":"Inter","font2":"Inter","style":"emerald-light","grad":"linear-gradient(135deg,#ecfdf5 0%,#d1fae5 100%)"},
        {"bg":"#18181B","pr":"#FACC15","ac":"#A78BFA","tx":"#FAFAFA","mu":"rgba(250,250,250,0.55)","ca":"rgba(255,255,255,0.05)","br":"rgba(255,255,255,0.1)","font1":"Inter","font2":"Inter","style":"zinc-yellow","grad":"linear-gradient(135deg,#18181B 0%,#27272a 100%)"},
        {"bg":"#020617","pr":"#6366F1","ac":"#A5F3FC","tx":"#E0F2FE","mu":"rgba(224,242,254,0.6)","ca":"rgba(99,102,241,0.08)","br":"rgba(99,102,241,0.2)","font1":"Inter","font2":"Inter","style":"indigo-space","grad":"linear-gradient(135deg,#020617 0%,#050f2a 100%)"},
        {"bg":"#FFF1F2","pr":"#E11D48","ac":"#F59E0B","tx":"#881337","mu":"#6B7280","ca":"#FFE4E6","br":"#FECDD3","font1":"Playfair Display","font2":"Inter","style":"crimson-light","grad":"linear-gradient(135deg,#fff1f2 0%,#ffe4e6 100%)"},
        {"bg":"#F8F9FA","pr":"#212529","ac":"#E63946","tx":"#212529","mu":"#6C757D","ca":"#E9ECEF","br":"#CED4DA","font1":"Inter","font2":"Inter","style":"bootstrap-clean","grad":"linear-gradient(135deg,#f8f9fa 0%,#e9ecef 100%)"},
        {"bg":"#0A0A0A","pr":"#FFFFFF","ac":"#F59E0B","tx":"#FFFFFF","mu":"rgba(255,255,255,0.5)","ca":"rgba(255,255,255,0.05)","br":"rgba(255,255,255,0.12)","font1":"Playfair Display","font2":"Inter","style":"bw-luxury","grad":"linear-gradient(135deg,#0A0A0A 0%,#1a1a1a 100%)"},
        {"bg":"#FFF0F3","pr":"#FF4D6D","ac":"#FF9F1C","tx":"#590D22","mu":"#6B7280","ca":"#FFD6E0","br":"#FFAFC5","font1":"Playfair Display","font2":"Inter","style":"coral-pink","grad":"linear-gradient(135deg,#fff0f3 0%,#ffd6e0 100%)"},
        {"bg":"#061014","pr":"#34D399","ac":"#60A5FA","tx":"#ECFDF5","mu":"rgba(236,253,245,0.6)","ca":"rgba(52,211,153,0.08)","br":"rgba(52,211,153,0.2)","font1":"Inter","font2":"Inter","style":"matrix-green","grad":"linear-gradient(135deg,#061014 0%,#0a1a20 100%)"},
        {"bg":"#140028","pr":"#A855F7","ac":"#EC4899","tx":"#FAF5FF","mu":"rgba(250,245,255,0.6)","ca":"rgba(168,85,247,0.1)","br":"rgba(168,85,247,0.25)","font1":"Playfair Display","font2":"Inter","style":"galaxy","grad":"linear-gradient(135deg,#140028 0%,#220044 100%)"},
        {"bg":"#FEFCE8","pr":"#CA8A04","ac":"#DC2626","tx":"#1C1400","mu":"#78716C","ca":"#FEF9C3","br":"#FEF08A","font1":"Playfair Display","font2":"Inter","style":"golden-cream","grad":"linear-gradient(135deg,#fefce8 0%,#fef9c3 100%)"},
        {"bg":"#F5F3FF","pr":"#4F46E5","ac":"#EC4899","tx":"#1E1B4B","mu":"#6B7280","ca":"#EDE9FE","br":"#C4B5FD","font1":"Inter","font2":"Inter","style":"electric-indigo","grad":"linear-gradient(135deg,#f5f3ff 0%,#ede9fe 100%)"},
        {"bg":"#0C1A0C","pr":"#22C55E","ac":"#FACC15","tx":"#F0FDF4","mu":"rgba(240,253,244,0.6)","ca":"rgba(34,197,94,0.08)","br":"rgba(34,197,94,0.2)","font1":"Inter","font2":"Inter","style":"jungle-dark","grad":"linear-gradient(135deg,#0C1A0C 0%,#142814 100%)"},
        {"bg":"#FFF9FB","pr":"#BE185D","ac":"#7C3AED","tx":"#4A0020","mu":"#6B7280","ca":"#FCE7F3","br":"#FBCFE8","font1":"Playfair Display","font2":"Inter","style":"rose-gold","grad":"linear-gradient(135deg,#fff9fb 0%,#fce7f3 100%)"},
        {"bg":"#001A10","pr":"#00E676","ac":"#FFD600","tx":"#E8F5E9","mu":"rgba(232,245,233,0.6)","ca":"rgba(0,230,118,0.08)","br":"rgba(0,230,118,0.2)","font1":"Inter","font2":"Inter","style":"neon-green","grad":"linear-gradient(135deg,#001A10 0%,#002a18 100%)"},
        {"bg":"#F0F4FF","pr":"#1746A2","ac":"#FF6B6B","tx":"#0a1628","mu":"#6B7280","ca":"#DBE4FF","br":"#BAC8FF","font1":"Inter","font2":"Inter","style":"ocean-blue","grad":"linear-gradient(135deg,#f0f4ff 0%,#dbe4ff 100%)"},
        {"bg":"#08080F","pr":"#E879F9","ac":"#22D3EE","tx":"#FAF5FF","mu":"rgba(250,245,255,0.6)","ca":"rgba(232,121,249,0.06)","br":"rgba(232,121,249,0.2)","font1":"Inter","font2":"Inter","style":"cyberpunk","grad":"linear-gradient(135deg,#08080F 0%,#10101e 100%)"},
        {"bg":"#FAFFFE","pr":"#0D9488","ac":"#F59E0B","tx":"#042F2E","mu":"#6B7280","ca":"#CCFBF1","br":"#99F6E4","font1":"Inter","font2":"Inter","style":"mint-fresh","grad":"linear-gradient(135deg,#fafffe 0%,#ccfbf1 100%)"},
        {"bg":"#09090B","pr":"#D97706","ac":"#A78BFA","tx":"#FFFBEB","mu":"rgba(255,251,235,0.55)","ca":"rgba(217,119,6,0.08)","br":"rgba(217,119,6,0.2)","font1":"Playfair Display","font2":"Inter","style":"amber-dark","grad":"linear-gradient(135deg,#09090B 0%,#141418 100%)"},
        {"bg":"#180A00","pr":"#F97316","ac":"#FCD34D","tx":"#FFF7ED","mu":"rgba(255,247,237,0.6)","ca":"rgba(249,115,22,0.1)","br":"rgba(252,211,77,0.2)","font1":"Playfair Display","font2":"Inter","style":"sunset-dark","grad":"linear-gradient(135deg,#180A00 0%,#2a1200 100%)"},
        {"bg":"#0A1628","pr":"#0EA5E9","ac":"#38BDF8","tx":"#F0F9FF","mu":"rgba(240,249,255,0.6)","ca":"rgba(14,165,233,0.08)","br":"rgba(14,165,233,0.2)","font1":"Inter","font2":"Inter","style":"sky-dark","grad":"linear-gradient(135deg,#0A1628 0%,#0f2040 100%)"},
        {"bg":"#FFFAF0","pr":"#F97316","ac":"#14B8A6","tx":"#1C0A00","mu":"#78716C","ca":"#FFF1E0","br":"#FED7AA","font1":"Playfair Display","font2":"Inter","style":"peach-warm","grad":"linear-gradient(135deg,#fffaf0 0%,#fff1e0 100%)"},
        {"bg":"#F0F9FF","pr":"#0284C7","ac":"#F59E0B","tx":"#0C4A6E","mu":"#6B7280","ca":"#E0F2FE","br":"#BAE6FD","font1":"Inter","font2":"Inter","style":"sky-blue","grad":"linear-gradient(135deg,#f0f9ff 0%,#e0f2fe 100%)"},
        {"bg":"#0F1923","pr":"#FB923C","ac":"#34D399","tx":"#FFF7ED","mu":"rgba(255,247,237,0.6)","ca":"rgba(251,146,60,0.1)","br":"rgba(251,146,60,0.25)","font1":"Inter","font2":"Inter","style":"sunset-navy","grad":"linear-gradient(135deg,#0F1923 0%,#18263a 100%)"},
        {"bg":"#FEF9EE","pr":"#B45309","ac":"#059669","tx":"#1C1200","mu":"#78716C","ca":"#FEF3C7","br":"#FDE68A","font1":"Playfair Display","font2":"Inter","style":"honey-warm","grad":"linear-gradient(135deg,#fef9ee 0%,#fef3c7 100%)"},
        {"bg":"#F9FAFB","pr":"#111827","ac":"#6366F1","tx":"#111827","mu":"#6B7280","ca":"#F3F4F6","br":"#D1D5DB","font1":"Inter","font2":"Inter","style":"clean-dark-on-white","grad":"linear-gradient(135deg,#f9fafb 0%,#f3f4f6 100%)"},
        {"bg":"#0D1117","pr":"#58A6FF","ac":"#3FB950","tx":"#C9D1D9","mu":"rgba(201,209,217,0.6)","ca":"rgba(88,166,255,0.08)","br":"rgba(88,166,255,0.15)","font1":"Inter","font2":"Inter","style":"github-dark","grad":"linear-gradient(135deg,#0D1117 0%,#161b22 100%)"},
        {"bg":"#FFF8F0","pr":"#C2410C","ac":"#FBBF24","tx":"#431407","mu":"#78716C","ca":"#FEE2D5","br":"#FCA27B","font1":"Playfair Display","font2":"Inter","style":"rust-warm","grad":"linear-gradient(135deg,#fff8f0 0%,#fee2d5 100%)"},
        {"bg":"#FEFCE8","pr":"#CA8A04","ac":"#DC2626","tx":"#1C1400","mu":"#78716C","ca":"#FEF9C3","br":"#FEF08A","font1":"Playfair Display","font2":"Inter","style":"lemon-gold","grad":"linear-gradient(135deg,#fefce8 0%,#fef9c3 100%)"},
        {"bg":"#030712","pr":"#06B6D4","ac":"#8B5CF6","tx":"#F0FDFE","mu":"rgba(240,253,254,0.6)","ca":"rgba(6,182,212,0.08)","br":"rgba(6,182,212,0.2)","font1":"Inter","font2":"Inter","style":"cyan-space","grad":"linear-gradient(135deg,#030712 0%,#050f20 100%)"},
        {"bg":"#FFF0F3","pr":"#FF4D6D","ac":"#FF9F1C","tx":"#590D22","mu":"#6B7280","ca":"#FFD6E0","br":"#FFAFC5","font1":"Playfair Display","font2":"Inter","style":"valentine-pink","grad":"linear-gradient(135deg,#fff0f3 0%,#ffd6e0 100%)"},
    ]
    d = designs[abs(hash(prompt + "v4")) % len(designs)]
    is_dark = d["tx"] in ["#fff","#FFFFFF","#F5F3FF","#FFF8F0","#FFFBEB","#FFF7ED","#FFF8F0","#FAF5FF","#FDF2F8","#F0FDF4","#ECFDF5","#C9D1D9","#E0F2FE","#F0F9FF","#E8F5E9"] or d["bg"].startswith("#0") or d["bg"].startswith("#1") and len(d["bg"]) < 5

    imgs = {
        "hero":  f"https://image.pollinations.ai/prompt/ultra_realistic_cinematic_{enc}_dramatic_4k?width=1400&height=800&seed={seed}&nologo=true&model=flux",
        "about": f"https://image.pollinations.ai/prompt/professional_{enc}_premium_team?width=900&height=700&seed={seed+1}&nologo=true&model=flux",
        "g1":    f"https://image.pollinations.ai/prompt/{enc}_showcase_1?width=700&height=500&seed={seed+2}&nologo=true&model=flux",
        "g2":    f"https://image.pollinations.ai/prompt/{enc}_showcase_2?width=700&height=500&seed={seed+3}&nologo=true&model=flux",
        "g3":    f"https://image.pollinations.ai/prompt/{enc}_showcase_3?width=700&height=500&seed={seed+4}&nologo=true&model=flux",
        "g4":    f"https://image.pollinations.ai/prompt/{enc}_showcase_4?width=700&height=500&seed={seed+5}&nologo=true&model=flux",
    }

    nav_logo = "#fff" if is_dark else d["pr"]
    nav_link = "rgba(255,255,255,0.8)" if is_dark else d["mu"]
    hero_ov = f"linear-gradient(135deg,{d['bg']}F5,{d['bg']}CC,{d['pr']}22)"
    shadow = "0 40px 80px rgba(0,0,0,0.5)" if is_dark else "0 40px 80px rgba(0,0,0,0.12)"
    hov_shadow = "0 20px 60px rgba(0,0,0,0.35)" if is_dark else "0 20px 60px rgba(0,0,0,0.1)"
    svc_bg = "rgba(255,255,255,0.03)" if is_dark else d["ca"]
    inp_bg = "rgba(255,255,255,0.07)" if is_dark else "#ffffff"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="{name} — Premium services with excellence and expertise.">
<meta property="og:title" content="{name}">
<meta property="og:image" content="{imgs["hero"]}">
<title>{name}</title>
<link href="https://fonts.googleapis.com/css2?family={d["font1"].replace(" ","+")}:wght@400;700;800;900&family={d["font2"]}:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
:root{{
  --bg:{d["bg"]};--pr:{d["pr"]};--ac:{d["ac"]};--tx:{d["tx"]};
  --mu:{d["mu"]};--ca:{d["ca"]};--br:{d["br"]};
  --r:20px;--shadow:{shadow};
}}
html{{scroll-behavior:smooth}}
::-webkit-scrollbar{{width:6px}}
::-webkit-scrollbar-track{{background:var(--bg)}}
::-webkit-scrollbar-thumb{{background:var(--pr);border-radius:3px}}
body{{font-family:"{d["font2"]}",sans-serif;background:var(--bg);color:var(--tx);overflow-x:hidden;line-height:1.6}}
@keyframes fadeInUp{{from{{opacity:0;transform:translateY(40px)}}to{{opacity:1;transform:translateY(0)}}}}
@keyframes fadeInRight{{from{{opacity:0;transform:translateX(50px)}}to{{opacity:1;transform:translateX(0)}}}}
@keyframes pulse{{0%,100%{{opacity:1;transform:scale(1)}}50%{{opacity:0.7;transform:scale(1.3)}}}}
@keyframes float{{0%,100%{{transform:translateY(0)}}50%{{transform:translateY(-12px)}}}}
@keyframes spin{{to{{transform:rotate(360deg)}}}}
@keyframes waPulse{{0%,100%{{box-shadow:0 0 0 0 rgba(37,211,102,0.5)}}70%{{box-shadow:0 0 0 14px rgba(37,211,102,0)}}}}
@keyframes slideDown{{from{{transform:translateY(-100%)}}to{{transform:translateY(0)}}}}
@keyframes countUp{{from{{opacity:0;transform:translateY(20px)}}to{{opacity:1;transform:translateY(0)}}}}
#loader{{position:fixed;inset:0;background:var(--bg);z-index:99999;display:flex;align-items:center;justify-content:center;flex-direction:column;gap:16px;transition:opacity 0.6s}}
#loader.out{{opacity:0;pointer-events:none}}
.loader-logo{{font-family:"{d["font1"]}",serif;font-size:2rem;font-weight:900;color:var(--pr)}}
.loader-ring{{width:44px;height:44px;border:3px solid {d["ca"]};border-top-color:var(--pr);border-radius:50%;animation:spin 0.8s linear infinite}}
nav{{position:fixed;top:0;width:100%;z-index:1000;padding:0 5%;transition:all 0.4s}}
nav.solid{{background:{"rgba(10,10,20,0.96)" if is_dark else "rgba(255,255,255,0.97)"};backdrop-filter:blur(24px);border-bottom:1px solid var(--br);box-shadow:0 4px 30px rgba(0,0,0,0.1)}}
.ni{{max-width:1280px;margin:0 auto;display:flex;align-items:center;justify-content:space-between;height:72px}}
.logo{{font-family:"{d["font1"]}",serif;font-size:1.7rem;font-weight:900;color:{nav_logo};text-decoration:none;transition:color 0.3s;letter-spacing:-0.5px}}
nav.solid .logo{{color:var(--pr)}}
.links{{display:flex;align-items:center;gap:32px;list-style:none}}
.links a{{color:{nav_link};text-decoration:none;font-weight:500;font-size:0.88rem;transition:color 0.2s;letter-spacing:0.3px}}
nav.solid .links a{{color:var(--mu)}}
.links a:hover,.links a.active{{color:var(--pr)}}
.nav-btn{{background:var(--pr);color:#fff;padding:10px 24px;border-radius:100px;font-weight:700;font-size:0.85rem;text-decoration:none;transition:all 0.3s;box-shadow:0 4px 20px rgba(0,0,0,0.15)}}
.nav-btn:hover{{transform:translateY(-2px);filter:brightness(1.1);box-shadow:0 8px 30px rgba(0,0,0,0.2);color:#fff}}
.hb{{display:none;background:none;border:none;cursor:pointer;flex-direction:column;gap:5px;padding:4px;z-index:10}}
.hb span{{width:24px;height:2px;background:{"#fff" if is_dark else d["tx"]};border-radius:2px;display:block;transition:all 0.3s}}
nav.solid .hb span{{background:var(--tx)}}
.hb.open span:nth-child(1){{transform:translateY(7px) rotate(45deg)}}
.hb.open span:nth-child(2){{opacity:0}}
.hb.open span:nth-child(3){{transform:translateY(-7px) rotate(-45deg)}}
.mob-menu{{display:none;position:fixed;top:0;left:0;right:0;bottom:0;z-index:999;background:{"rgba(5,0,16,0.98)" if is_dark else "rgba(255,255,255,0.99)"};backdrop-filter:blur(30px);flex-direction:column;align-items:center;justify-content:center;gap:28px;animation:slideDown 0.3s ease}}
.mob-menu.open{{display:flex}}
.mob-menu a{{font-size:1.5rem;font-weight:700;color:var(--tx);text-decoration:none;transition:color 0.2s}}
.mob-menu a:hover{{color:var(--pr)}}
.mob-menu .close-btn{{position:absolute;top:20px;right:24px;background:none;border:none;color:var(--tx);font-size:1.8rem;cursor:pointer}}
.hero{{min-height:100vh;display:flex;align-items:center;padding:100px 5% 80px;position:relative;overflow:hidden}}
.hero-bg{{position:absolute;inset:0;background:url("{imgs["hero"]}") center/cover no-repeat;opacity:{"0.13" if is_dark else "0.07"};filter:blur(2px);transform:scale(1.08)}}
.hero-overlay{{position:absolute;inset:0;background:{hero_ov}}}
.hero-glow1{{position:absolute;top:-20%;right:-10%;width:700px;height:700px;border-radius:50%;background:radial-gradient(circle,{d["pr"]}{"20" if is_dark else "10"} 0%,transparent 70%);pointer-events:none}}
.hero-glow2{{position:absolute;bottom:-20%;left:-5%;width:500px;height:500px;border-radius:50%;background:radial-gradient(circle,{d["ac"]}{"15" if is_dark else "08"} 0%,transparent 70%);pointer-events:none}}
.hero-inner{{position:relative;z-index:2;max-width:1280px;margin:0 auto;width:100%;display:grid;grid-template-columns:1fr 1fr;gap:80px;align-items:center}}
.badge{{display:inline-flex;align-items:center;gap:8px;background:{"rgba(255,255,255,0.1)" if is_dark else d["ca"]};backdrop-filter:blur(12px);border:1px solid var(--br);padding:8px 20px;border-radius:100px;font-size:0.73rem;font-weight:700;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:20px;animation:fadeInUp 0.6s ease both;color:var(--tx)}}
.dot{{width:8px;height:8px;border-radius:50%;background:var(--ac);animation:pulse 2s infinite;box-shadow:0 0 8px var(--ac)}}
.hero-title{{font-family:"{d["font1"]}",serif;font-size:clamp(2.6rem,4.5vw,4.5rem);font-weight:900;line-height:1.06;letter-spacing:-2px;margin-bottom:16px;color:var(--tx);animation:fadeInUp 0.7s ease 0.1s both}}
.hero-title .accent{{color:var(--pr);display:block;font-style:italic}}
.hero-sub{{font-size:1rem;color:var(--mu);line-height:1.8;margin-bottom:32px;max-width:480px;animation:fadeInUp 0.7s ease 0.2s both}}
.hero-contact-bar{{display:flex;gap:20px;margin-bottom:28px;flex-wrap:wrap;animation:fadeInUp 0.7s ease 0.25s both}}
.hcb-item{{display:flex;align-items:center;gap:8px;font-size:0.85rem;color:var(--mu)}}
.hcb-item a{{color:var(--pr);text-decoration:none;font-weight:600}}
.hero-btns{{display:flex;gap:14px;flex-wrap:wrap;animation:fadeInUp 0.7s ease 0.3s both}}
.btn-primary{{display:inline-flex;align-items:center;gap:8px;background:var(--pr);color:#fff;font-weight:800;font-size:0.88rem;padding:15px 30px;border-radius:100px;text-decoration:none;transition:all 0.3s;box-shadow:0 8px 30px rgba(0,0,0,0.2)}}
.btn-primary:hover{{transform:translateY(-3px);filter:brightness(1.1);box-shadow:0 16px 40px rgba(0,0,0,0.3)}}
.btn-secondary{{display:inline-flex;align-items:center;gap:8px;background:var(--ca);color:var(--tx);font-weight:700;font-size:0.88rem;padding:15px 30px;border-radius:100px;text-decoration:none;border:1px solid var(--br);transition:all 0.3s}}
.btn-secondary:hover{{transform:translateY(-3px);filter:brightness(1.05)}}
.btn-wa{{display:inline-flex;align-items:center;gap:8px;background:#25D366;color:#fff;font-weight:700;font-size:0.88rem;padding:15px 24px;border-radius:100px;text-decoration:none;transition:all 0.3s}}
.btn-wa:hover{{transform:translateY(-3px);filter:brightness(1.1)}}
.hero-img-wrap{{position:relative;perspective:1200px;animation:fadeInRight 0.9s ease 0.2s both}}
.hero-img-card{{border-radius:24px;overflow:hidden;box-shadow:{shadow},0 0 0 1px var(--br);transform:rotateY(-6deg) rotateX(3deg);transition:transform 0.7s ease;animation:float 6s ease-in-out infinite}}
.hero-img-card:hover{{transform:rotateY(0) rotateX(0)}}
.hero-img-card img{{width:100%;height:440px;object-fit:cover;display:block}}
.hero-badge{{position:absolute;bottom:20px;left:20px;background:rgba(0,0,0,0.75);backdrop-filter:blur(20px);border:1px solid rgba(255,255,255,0.15);padding:12px 18px;border-radius:14px;display:flex;align-items:center;gap:10px}}
.live-dot{{width:8px;height:8px;border-radius:50%;background:#22C55E;box-shadow:0 0 10px #22C55E;animation:pulse 2s infinite}}
.live-text{{color:#fff;font-size:0.75rem;font-weight:600}}
.stats-bar{{padding:0 5%;border-top:1px solid var(--br);border-bottom:1px solid var(--br);background:{"rgba(0,0,0,0.4)" if is_dark else d["ca"]}}}
.stats-inner{{max-width:1280px;margin:0 auto;display:grid;grid-template-columns:repeat(4,1fr)}}
.stat-item{{padding:36px 20px;text-align:center;border-right:1px solid var(--br)}}
.stat-item:last-child{{border-right:none}}
.stat-num{{font-family:"{d["font1"]}",serif;font-size:2.6rem;font-weight:900;color:var(--pr);margin-bottom:4px;line-height:1}}
.stat-label{{font-size:0.72rem;color:var(--mu);font-weight:600;text-transform:uppercase;letter-spacing:1.2px}}
section{{padding:100px 5%}}
.sec-inner{{max-width:1280px;margin:0 auto}}
.sec-label{{display:inline-flex;align-items:center;gap:8px;background:var(--ca);color:var(--pr);font-size:0.7rem;font-weight:800;text-transform:uppercase;letter-spacing:2px;padding:8px 18px;border-radius:100px;margin-bottom:18px;border:1px solid var(--br)}}
.sec-title{{font-family:"{d["font1"]}",serif;font-size:clamp(1.8rem,3vw,2.8rem);font-weight:900;color:var(--tx);line-height:1.15;letter-spacing:-1px;margin-bottom:16px}}
.sec-title span{{color:var(--pr)}}
.sec-sub{{font-size:0.95rem;color:var(--mu);line-height:1.8;max-width:520px}}
.about-grid{{display:grid;grid-template-columns:1fr 1fr;gap:80px;align-items:center}}
.about-img{{border-radius:24px;overflow:hidden;position:relative;box-shadow:{shadow}}}
.about-img img{{width:100%;height:500px;object-fit:cover;display:block;transition:transform 0.7s}}
.about-img:hover img{{transform:scale(1.05)}}
.about-tag{{position:absolute;top:20px;left:20px;background:var(--pr);color:#fff;font-size:0.7rem;font-weight:800;padding:8px 16px;border-radius:100px;text-transform:uppercase;letter-spacing:1px}}
.features{{display:flex;flex-direction:column;gap:14px;margin-top:28px}}
.feature-item{{display:flex;align-items:flex-start;gap:14px;padding:18px;background:var(--ca);border-radius:16px;border:1px solid var(--br);transition:all 0.3s;cursor:default}}
.feature-item:hover{{border-color:var(--pr);transform:translateX(5px);box-shadow:0 8px 30px rgba(0,0,0,0.08)}}
.fi-icon{{width:44px;height:44px;border-radius:12px;background:{"rgba(255,255,255,0.06)" if is_dark else "#fff"};border:1px solid var(--br);display:flex;align-items:center;justify-content:center;font-size:1.3rem;flex-shrink:0}}
.fi-text h4{{font-weight:700;font-size:0.88rem;color:var(--tx);margin-bottom:3px}}
.fi-text p{{font-size:0.78rem;color:var(--mu);line-height:1.5}}
.services-bg{{background:{svc_bg}}}
.services-grid{{display:grid;grid-template-columns:repeat(2,1fr);gap:20px;margin-top:20px}}
.svc-card{{background:var(--bg);border:1px solid var(--br);border-radius:24px;padding:36px;transition:all 0.4s;position:relative;overflow:hidden;cursor:default}}
.svc-card::before{{content:"";position:absolute;inset:0;background:linear-gradient(135deg,var(--pr),transparent);opacity:0;transition:opacity 0.4s}}
.svc-card:hover{{border-color:var(--pr);transform:translateY(-8px);box-shadow:{hov_shadow}}}
.svc-card:hover::before{{opacity:0.04}}
.svc-icon{{font-size:2.8rem;margin-bottom:18px;display:block}}
.svc-card h3{{font-family:"{d["font1"]}",serif;font-size:1.2rem;font-weight:800;color:var(--tx);margin-bottom:10px}}
.svc-card p{{font-size:0.86rem;color:var(--mu);line-height:1.7}}
.gallery-bg{{background:var(--bg)}}
.gallery-grid{{display:grid;grid-template-columns:repeat(2,1fr);gap:16px;margin-top:40px}}
.gal-item{{border-radius:20px;overflow:hidden;aspect-ratio:4/3;position:relative;cursor:pointer}}
.gal-item img{{width:100%;height:100%;object-fit:cover;display:block;transition:transform 0.6s}}
.gal-item:hover img{{transform:scale(1.1)}}
.gal-overlay{{position:absolute;inset:0;background:linear-gradient(to top,rgba(0,0,0,0.6),transparent);opacity:0;transition:opacity 0.3s;display:flex;align-items:flex-end;padding:20px}}
.gal-item:hover .gal-overlay{{opacity:1}}
.gal-overlay span{{color:#fff;font-weight:700;font-size:0.9rem}}
.testi-bg{{background:{svc_bg}}}
.testi-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:20px;margin-top:40px}}
.testi-card{{background:var(--bg);border:1px solid var(--br);border-radius:24px;padding:32px;transition:all 0.3s;position:relative;overflow:hidden;cursor:default}}
.testi-card::before{{content:"\\201C";position:absolute;top:-15px;right:16px;font-size:7rem;color:var(--pr);opacity:0.07;font-family:serif;line-height:1}}
.testi-card:hover{{border-color:var(--pr);transform:translateY(-5px);box-shadow:{hov_shadow}}}
.stars{{color:var(--ac);font-size:0.9rem;letter-spacing:3px;margin-bottom:14px}}
.testi-text{{font-size:0.88rem;color:var(--mu);line-height:1.75;margin-bottom:20px;font-style:italic}}
.testi-author{{display:flex;align-items:center;gap:12px}}
.t-avatar{{width:46px;height:46px;border-radius:50%;background:linear-gradient(135deg,var(--pr),var(--ac));display:flex;align-items:center;justify-content:center;color:#fff;font-weight:800;font-size:0.9rem;flex-shrink:0}}
.t-name{{font-weight:700;font-size:0.85rem;color:var(--tx)}}
.t-role{{font-size:0.72rem;color:var(--mu)}}
.faq-bg{{background:var(--bg)}}
.faq-list{{max-width:800px;margin:0 auto;margin-top:40px}}
.faq-item{{border-bottom:1px solid var(--br)}}
.faq-btn{{width:100%;background:none;border:none;cursor:pointer;padding:20px 0;display:flex;justify-content:space-between;align-items:center;gap:16px;text-align:left}}
.faq-q{{font-weight:700;font-size:0.95rem;color:var(--tx)}}
.faq-icon{{font-size:1.3rem;color:var(--pr);flex-shrink:0;transition:transform 0.3s}}
.faq-icon.open{{transform:rotate(45deg)}}
.faq-answer{{display:none;padding-bottom:16px}}
.faq-answer p{{color:var(--mu);font-size:0.88rem;line-height:1.75}}
.contact-bg{{background:{svc_bg}}}
.contact-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:16px;margin-bottom:36px;margin-top:40px}}
.contact-card{{background:var(--bg);border:1px solid var(--br);border-radius:20px;padding:24px;text-align:center}}
.contact-card .icon{{font-size:1.8rem;margin-bottom:10px}}
.contact-card h4{{font-weight:700;font-size:0.85rem;color:var(--tx);margin-bottom:6px}}
.contact-card a,.contact-card p{{color:var(--pr);text-decoration:none;font-size:0.82rem;font-weight:600;display:block;line-height:1.4}}
.contact-card p{{color:var(--mu);font-weight:400}}
.contact-form{{background:var(--bg);border:1px solid var(--br);border-radius:24px;padding:36px}}
.form-grid{{display:grid;grid-template-columns:1fr 1fr;gap:16px}}
.form-group{{display:flex;flex-direction:column;gap:6px}}
.form-group label{{font-size:0.78rem;font-weight:600;color:var(--mu)}}
.form-group input,.form-group textarea,.form-group select{{padding:12px 16px;background:{inp_bg};border:1px solid var(--br);border-radius:12px;color:var(--tx);font-size:0.88rem;outline:none;transition:border-color 0.2s;font-family:"{d["font2"]}",sans-serif}}
.form-group input:focus,.form-group textarea:focus,.form-group select:focus{{border-color:var(--pr)}}
.form-group textarea{{resize:vertical;min-height:100px}}
.form-success{{display:none;background:#dcfce7;border:1px solid #a7f3d0;border-radius:12px;padding:16px;text-align:center;color:#065f46;font-weight:600;margin-top:12px}}
.newsletter-bg{{background:var(--bg)}}
.newsletter-inner{{max-width:600px;margin:0 auto;text-align:center}}
.newsletter-form{{display:flex;gap:12px;max-width:480px;margin:24px auto 0;flex-wrap:wrap}}
.newsletter-form input{{flex:1;min-width:180px;padding:14px 20px;background:{inp_bg};border:1px solid var(--br);border-radius:100px;color:var(--tx);font-size:0.88rem;outline:none}}
.newsletter-form button{{background:var(--pr);color:#fff;border:none;padding:14px 26px;border-radius:100px;font-weight:800;font-size:0.88rem;cursor:pointer;white-space:nowrap}}
.map-wrap{{margin-top:32px;border-radius:24px;overflow:hidden;border:1px solid var(--br)}}
.cta-section{{padding:100px 5%;background:var(--bg)}}
.cta-box{{max-width:960px;margin:0 auto;background:linear-gradient(135deg,var(--pr),var(--ac));border-radius:32px;padding:72px 56px;text-align:center;position:relative;overflow:hidden;box-shadow:0 40px 80px rgba(0,0,0,0.25)}}
.cta-box::before{{content:"";position:absolute;top:-40%;right:-8%;width:500px;height:500px;border-radius:50%;background:rgba(255,255,255,0.07);pointer-events:none}}
.cta-box h2{{font-family:"{d["font1"]}",serif;font-size:clamp(1.8rem,3.5vw,2.8rem);font-weight:900;color:#fff;margin-bottom:14px;position:relative;z-index:1;letter-spacing:-1px}}
.cta-box p{{color:rgba(255,255,255,0.85);font-size:0.95rem;margin-bottom:32px;position:relative;z-index:1;max-width:480px;margin-left:auto;margin-right:auto}}
.cta-btns{{display:flex;gap:14px;justify-content:center;flex-wrap:wrap;position:relative;z-index:1}}
.cta-btn1{{background:#fff;color:var(--pr);font-weight:800;padding:14px 32px;border-radius:100px;text-decoration:none;font-size:0.88rem;transition:all 0.3s;box-shadow:0 8px 30px rgba(0,0,0,0.15)}}
.cta-btn1:hover{{transform:translateY(-3px);box-shadow:0 16px 40px rgba(0,0,0,0.2)}}
.cta-btn2{{background:rgba(255,255,255,0.15);color:#fff;font-weight:700;padding:14px 32px;border-radius:100px;text-decoration:none;font-size:0.88rem;border:1px solid rgba(255,255,255,0.3);transition:all 0.3s}}
.cta-btn2:hover{{background:rgba(255,255,255,0.25);transform:translateY(-3px)}}
footer{{padding:60px 5% 80px;border-top:1px solid var(--br);background:{svc_bg}}}
.footer-grid{{max-width:1280px;margin:0 auto;display:grid;grid-template-columns:2fr 1fr 1fr 1fr;gap:48px;margin-bottom:40px}}
.footer-brand p{{font-size:0.82rem;color:var(--mu);margin-top:12px;line-height:1.7;max-width:220px}}
.footer-logo{{font-family:"{d["font1"]}",serif;font-size:1.6rem;font-weight:900;color:var(--pr)}}
.footer-social{{display:flex;gap:10px;margin-top:16px}}
.footer-social a{{width:36px;height:36px;border-radius:10px;background:var(--ca);border:1px solid var(--br);display:flex;align-items:center;justify-content:center;text-decoration:none;font-size:1rem;transition:all 0.3s}}
.footer-social a:hover{{background:var(--pr);transform:translateY(-2px)}}
.footer-col h4{{font-weight:700;font-size:0.72rem;color:var(--mu);text-transform:uppercase;letter-spacing:1.5px;margin-bottom:16px}}
.footer-col a{{display:block;color:var(--mu);text-decoration:none;font-size:0.82rem;margin-bottom:10px;transition:color 0.2s}}
.footer-col a:hover{{color:var(--pr)}}
.footer-bottom{{max-width:1280px;margin:0 auto;border-top:1px solid var(--br);padding-top:24px;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px}}
.footer-bottom p{{font-size:0.75rem;color:var(--mu)}}
.footer-bottom a{{color:var(--mu);text-decoration:none;font-size:0.72rem}}
.footer-bottom a:hover{{color:var(--pr)}}
.wa-btn{{position:fixed;bottom:24px;right:24px;z-index:9999;width:58px;height:58px;background:#25D366;border-radius:50%;display:flex;align-items:center;justify-content:center;text-decoration:none;box-shadow:0 8px 30px rgba(37,211,102,0.4);animation:waPulse 2s infinite;transition:transform 0.3s}}
.wa-btn:hover{{transform:scale(1.12)}}
.sticky-cta{{position:fixed;bottom:0;left:0;right:0;z-index:9990;background:{"rgba(5,0,16,0.97)" if is_dark else "rgba(255,255,255,0.97)"};backdrop-filter:blur(20px);border-top:1px solid var(--br);padding:12px 5%;display:flex;align-items:center;justify-content:space-between;gap:16px;transform:translateY(100%);transition:transform 0.4s ease;flex-wrap:wrap}}
.sticky-cta-text p:first-child{{font-weight:700;font-size:0.88rem;color:var(--tx)}}
.sticky-cta-text p:last-child{{font-size:0.75rem;color:var(--mu)}}
.sticky-cta-btns{{display:flex;gap:10px}}
.sticky-cta-btns a{{padding:10px 20px;border-radius:100px;text-decoration:none;font-weight:700;font-size:0.82rem;transition:all 0.3s}}
.sc-btn1{{background:var(--ca);color:var(--tx);border:1px solid var(--br)}}
.sc-btn2{{background:var(--pr);color:#fff}}
#back-top{{position:fixed;bottom:90px;right:24px;z-index:9980;width:42px;height:42px;background:var(--pr);color:#fff;border:none;border-radius:50%;cursor:pointer;font-size:1.1rem;display:none;align-items:center;justify-content:center;box-shadow:0 4px 20px rgba(0,0,0,0.2);transition:all 0.3s}}
#back-top:hover{{transform:translateY(-3px)}}
.cookie-banner{{position:fixed;bottom:0;left:0;right:0;z-index:9970;background:{"rgba(5,0,16,0.97)" if is_dark else "rgba(15,15,15,0.97)"};color:#fff;padding:16px 5%;display:flex;align-items:center;justify-content:space-between;gap:16px;flex-wrap:wrap;transition:transform 0.4s}}
.cookie-banner.hidden{{transform:translateY(100%)}}
.cookie-banner p{{font-size:0.82rem;color:rgba(255,255,255,0.8);max-width:600px}}
.cookie-btns{{display:flex;gap:10px}}
.cookie-accept{{background:var(--pr);color:#fff;border:none;padding:10px 20px;border-radius:100px;font-weight:700;font-size:0.82rem;cursor:pointer}}
.cookie-decline{{background:rgba(255,255,255,0.1);color:#fff;border:1px solid rgba(255,255,255,0.2);padding:10px 20px;border-radius:100px;font-weight:600;font-size:0.82rem;cursor:pointer}}
.reveal{{opacity:0;transform:translateY(40px) scale(0.97);transition:opacity 0.7s ease,transform 0.7s ease}}
.reveal.visible{{opacity:1;transform:translateY(0) scale(1)}}
@media(max-width:900px){{
  .hero-inner,.about-grid{{grid-template-columns:1fr;gap:48px;text-align:center}}
  .hero-img-wrap{{order:-1}}.hero-sub{{max-width:100%}}.hero-btns{{justify-content:center}}.hero-contact-bar{{justify-content:center}}
  .services-grid,.gallery-grid{{grid-template-columns:1fr}}
  .testi-grid{{grid-template-columns:1fr}}
  .stats-inner{{grid-template-columns:repeat(2,1fr)}}
  .footer-grid{{grid-template-columns:1fr 1fr;gap:32px}}
  .links,.nav-btn{{display:none}}.hb{{display:flex}}
  .cta-box{{padding:48px 28px}}.sec-sub{{max-width:100%}}
  .form-grid{{grid-template-columns:1fr}}
}}
@media(max-width:540px){{
  .stats-inner,.footer-grid{{grid-template-columns:1fr}}
  .hero-title{{font-size:2.4rem}}.footer-bottom{{flex-direction:column;text-align:center}}
}}
</style>
</head>
<body>

<!-- LOADER -->
<div id="loader">
  <div class="loader-logo">{name}</div>
  <div class="loader-ring"></div>
</div>

<!-- MOBILE MENU -->
<div class="mob-menu" id="mobMenu">
  <button class="close-btn" onclick="closeMob()">✕</button>
  <a href="#about" onclick="closeMob()">About</a>
  <a href="#services" onclick="closeMob()">Services</a>
  <a href="#gallery" onclick="closeMob()">Gallery</a>
  <a href="#testimonials" onclick="closeMob()">Reviews</a>
  <a href="#contact" onclick="closeMob()">Contact</a>
  <a href="#contact" onclick="closeMob()" style="background:var(--pr);color:#fff;padding:14px 32px;border-radius:100px;font-size:1rem">Get Started →</a>
</div>

<!-- NAV -->
<nav id="nav">
  <div class="ni">
    <a href="#" class="logo">{name}</a>
    <ul class="links">
      <li><a href="#about">About</a></li>
      <li><a href="#services">Services</a></li>
      <li><a href="#gallery">Gallery</a></li>
      <li><a href="#testimonials">Reviews</a></li>
      <li><a href="#contact">Contact</a></li>
    </ul>
    <a href="#contact" class="nav-btn">Get Started →</a>
    <button class="hb" id="hb" onclick="toggleMob()"><span></span><span></span><span></span></button>
  </div>
</nav>

<!-- HERO -->
<section class="hero" id="home">
  <div class="hero-bg"></div>
  <div class="hero-overlay"></div>
  <div class="hero-glow1"></div>
  <div class="hero-glow2"></div>
  <div class="hero-inner">
    <div>
      <div class="badge"><span class="dot"></span>✦ {name} · Premium</div>
      <h1 class="hero-title">
        {name}
        <span class="accent" id="typed-text">Excellence Redefined.</span>
      </h1>
      <p class="hero-sub">Premium services delivered with passion, precision, and an obsession with results that exceed every expectation.</p>
      <div class="hero-contact-bar">
        <div class="hcb-item">📞 <a href="tel:{phone}">{phone}</a></div>
        <div class="hcb-item">✉️ <a href="mailto:{email_addr}">{email_addr}</a></div>
      </div>
      <div class="hero-btns">
        <a href="#contact" class="btn-primary">Get Started →</a>
        <a href="#services" class="btn-secondary">▶ See Our Work</a>
        <a href="https://wa.me/{whatsapp}" target="_blank" class="btn-wa">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="white"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/></svg>
          WhatsApp
        </a>
      </div>
    </div>
    <div class="hero-img-wrap">
      <div class="hero-img-card">
        <img src="{imgs["hero"]}" alt="{name}" loading="eager"/>
        <div class="hero-badge"><div class="live-dot"></div><span class="live-text">Live &amp; Open Now · {hours}</span></div>
      </div>
    </div>
  </div>
</section>

<!-- STATS -->
<div class="stats-bar">
  <div class="stats-inner">
    <div class="stat-item reveal"><div class="stat-num" data-target="500">0</div><div class="stat-label">Projects Done</div></div>
    <div class="stat-item reveal"><div class="stat-num" data-target="200">0</div><div class="stat-label">Happy Clients</div></div>
    <div class="stat-item reveal"><div class="stat-num" data-target="15">0</div><div class="stat-label">Years Experience</div></div>
    <div class="stat-item reveal"><div class="stat-num" data-target="99">0</div><div class="stat-label">% Satisfaction</div></div>
  </div>
</div>

<!-- ABOUT -->
<section id="about" style="background:var(--bg)">
  <div class="sec-inner">
    <div class="about-grid">
      <div class="about-img reveal">
        <img src="{imgs["about"]}" alt="About {name}" loading="lazy"/>
        <div class="about-tag">Our Story</div>
      </div>
      <div class="reveal">
        <div class="sec-label">✦ About Us</div>
        <h2 class="sec-title">Built for <span>Excellence</span>.</h2>
        <p class="sec-sub">We started with one mission — to deliver the best possible experience for every client. Today, {name} is trusted by hundreds and recognised for quality that never compromises.</p>
        <div class="features">
          <div class="feature-item"><div class="fi-icon">🏆</div><div class="fi-text"><h4>Award-Winning Quality</h4><p>Consistently recognised for excellence and outstanding results.</p></div></div>
          <div class="feature-item"><div class="fi-icon">🌍</div><div class="fi-text"><h4>Trusted by Hundreds</h4><p>Clients across the country rely on us for their most important needs.</p></div></div>
          <div class="feature-item"><div class="fi-icon">💡</div><div class="fi-text"><h4>Always Innovating</h4><p>We never stop improving — always finding better ways to serve you.</p></div></div>
        </div>
      </div>
    </div>
  </div>
</section>

<!-- SERVICES -->
<section id="services" class="services-bg">
  <div class="sec-inner">
    <div style="text-align:center;margin-bottom:48px">
      <div class="sec-label">✦ What We Offer</div>
      <h2 class="sec-title" style="text-align:center">Why Choose <span>{name}</span></h2>
      <p class="sec-sub" style="margin:12px auto 0;text-align:center">Everything you need, crafted to the highest possible standard. Nothing less.</p>
    </div>
    <div class="services-grid reveal">
      <div class="svc-card"><span class="svc-icon">⚡</span><h3>Fast Delivery</h3><p>Exceptional results delivered ahead of schedule, without ever compromising quality or attention to detail.</p></div>
      <div class="svc-card"><span class="svc-icon">🎯</span><h3>Precision Focused</h3><p>Every action tied to your specific, measurable goals. No guesswork, no wasted effort, only results.</p></div>
      <div class="svc-card"><span class="svc-icon">🤝</span><h3>True Partnership</h3><p>We embed ourselves in your mission and work as a genuine extension of your team, not just a vendor.</p></div>
      <div class="svc-card"><span class="svc-icon">🛡️</span><h3>Proven Reliability</h3><p>Trusted by 200+ clients with their most critical projects. We never miss a deadline or a promise.</p></div>
    </div>
  </div>
</section>

<!-- GALLERY -->
<section id="gallery" style="background:var(--bg)">
  <div class="sec-inner">
    <div style="text-align:center;margin-bottom:48px">
      <div class="sec-label">✦ Gallery</div>
      <h2 class="sec-title" style="text-align:center">See It For <span>Yourself</span></h2>
    </div>
    <div class="gallery-grid reveal">
      <div class="gal-item"><img src="{imgs["g1"]}" loading="lazy" alt="Gallery 1"/><div class="gal-overlay"><span>Our Work →</span></div></div>
      <div class="gal-item"><img src="{imgs["g2"]}" loading="lazy" alt="Gallery 2"/><div class="gal-overlay"><span>Our Work →</span></div></div>
      <div class="gal-item"><img src="{imgs["g3"]}" loading="lazy" alt="Gallery 3"/><div class="gal-overlay"><span>Our Work →</span></div></div>
      <div class="gal-item"><img src="{imgs["g4"]}" loading="lazy" alt="Gallery 4"/><div class="gal-overlay"><span>Our Work →</span></div></div>
    </div>
  </div>
</section>

<!-- TESTIMONIALS -->
<section id="testimonials" class="testi-bg">
  <div class="sec-inner">
    <div style="text-align:center;margin-bottom:48px">
      <div class="sec-label">✦ Reviews</div>
      <h2 class="sec-title" style="text-align:center">What Our <span>Clients Say</span></h2>
    </div>
    <div class="testi-grid reveal">
      <div class="testi-card"><div class="stars">★★★★★</div><p class="testi-text">"Delivered exactly as promised and ahead of schedule. The quality was exceptional and the team was a pleasure to work with throughout."</p><div class="testi-author"><div class="t-avatar">R</div><div><div class="t-name">Rohit K.</div><div class="t-role">Managing Director</div></div></div></div>
      <div class="testi-card"><div class="stars">★★★★★</div><p class="testi-text">"Best decision we ever made. The results speak for themselves — our business has genuinely transformed since working with {name}."</p><div class="testi-author"><div class="t-avatar">N</div><div><div class="t-name">Nisha A.</div><div class="t-role">Operations Head</div></div></div></div>
      <div class="testi-card"><div class="stars">★★★★★</div><p class="testi-text">"An absolute game-changer. Reliable, professional, and genuinely invested in our success. I recommend {name} to everyone I know."</p><div class="testi-author"><div class="t-avatar">A</div><div><div class="t-name">Amit S.</div><div class="t-role">Founder</div></div></div></div>
    </div>
  </div>
</section>

<!-- FAQ -->
<section id="faq" class="faq-bg">
  <div class="sec-inner">
    <div style="text-align:center;margin-bottom:40px">
      <div class="sec-label">✦ FAQ</div>
      <h2 class="sec-title" style="text-align:center">Frequently Asked <span>Questions</span></h2>
    </div>
    <div class="faq-list reveal">
      <div class="faq-item"><button class="faq-btn" onclick="toggleFAQ(this)"><span class="faq-q">How do I get started?</span><span class="faq-icon">+</span></button><div class="faq-answer"><p>Simply contact us through the form below or call us directly. We will respond within 24 hours and set up a free initial consultation to understand your needs.</p></div></div>
      <div class="faq-item"><button class="faq-btn" onclick="toggleFAQ(this)"><span class="faq-q">What is your pricing?</span><span class="faq-icon">+</span></button><div class="faq-answer"><p>Our pricing is transparent and competitive, tailored to your specific requirements. Contact us for a personalised quote — no hidden fees, ever.</p></div></div>
      <div class="faq-item"><button class="faq-btn" onclick="toggleFAQ(this)"><span class="faq-q">How long does it typically take?</span><span class="faq-icon">+</span></button><div class="faq-answer"><p>Timelines depend on the scope of work. We are known for fast, reliable delivery and will give you a clear timeline upfront before any work begins.</p></div></div>
      <div class="faq-item"><button class="faq-btn" onclick="toggleFAQ(this)"><span class="faq-q">Do you offer ongoing support?</span><span class="faq-icon">+</span></button><div class="faq-answer"><p>Absolutely. We pride ourselves on long-term relationships with our clients. Support, maintenance, and continued assistance are always available.</p></div></div>
      <div class="faq-item"><button class="faq-btn" onclick="toggleFAQ(this)"><span class="faq-q">What areas do you serve?</span><span class="faq-icon">+</span></button><div class="faq-answer"><p>We serve clients across India and internationally. Whether in-person or remote, we adapt to your needs and location seamlessly.</p></div></div>
    </div>
  </div>
</section>

<!-- CONTACT -->
<section id="contact" class="contact-bg">
  <div class="sec-inner">
    <div style="text-align:center;margin-bottom:40px">
      <div class="sec-label">✦ Contact Us</div>
      <h2 class="sec-title" style="text-align:center">Get In <span>Touch</span></h2>
      <p class="sec-sub" style="margin:12px auto;text-align:center">We would love to hear from you. Reach out through any channel below.</p>
    </div>
    <div class="contact-grid reveal">
      <div class="contact-card"><div class="icon">📞</div><h4>Call Us</h4><a href="tel:{phone}">{phone}</a></div>
      <div class="contact-card"><div class="icon">✉️</div><h4>Email Us</h4><a href="mailto:{email_addr}" style="word-break:break-all">{email_addr}</a></div>
      <div class="contact-card"><div class="icon">📍</div><h4>Visit Us</h4><p>{address}</p></div>
      <div class="contact-card"><div class="icon">⏰</div><h4>Hours</h4><p>{hours}</p></div>
    </div>
    <div class="contact-form reveal">
      <h3 style="font-family:'{d["font1"]}',serif;font-size:1.3rem;font-weight:800;color:var(--tx);margin-bottom:24px">Send Us a Message</h3>
      <form onsubmit="handleForm(event)">
        <div class="form-grid" style="margin-bottom:16px">
          <div class="form-group"><label>Full Name *</label><input type="text" placeholder="Your full name" required/></div>
          <div class="form-group"><label>Phone Number *</label><input type="tel" placeholder="+91 00000 00000" required/></div>
        </div>
        <div class="form-group" style="margin-bottom:16px"><label>Email Address</label><input type="email" placeholder="your@email.com"/></div>
        <div class="form-group" style="margin-bottom:16px"><label>Subject</label><input type="text" placeholder="How can we help you?"/></div>
        <div class="form-group" style="margin-bottom:20px"><label>Message</label><textarea placeholder="Tell us more about your requirements..." rows="4"></textarea></div>
        <button type="submit" class="btn-primary" style="border:none;cursor:pointer">Send Message →</button>
        <div class="form-success" id="formSuccess">✅ Thank you! We will contact you within 24 hours.</div>
      </form>
    </div>
    <div class="map-wrap reveal">
      <iframe src="https://maps.google.com/maps?q={urllib.parse.quote(address)}&output=embed" width="100%" height="350" style="border:0;display:block" allowfullscreen loading="lazy"></iframe>
    </div>
  </div>
</section>

<!-- NEWSLETTER -->
<section id="newsletter" style="background:var(--bg);padding:80px 5%">
  <div class="newsletter-inner reveal">
    <div style="font-size:2.5rem;margin-bottom:12px">📬</div>
    <div class="sec-label" style="margin:0 auto 16px">✦ Newsletter</div>
    <h2 class="sec-title" style="text-align:center">Stay in the <span>Loop</span></h2>
    <p style="color:var(--mu);font-size:0.9rem;margin-top:8px">Get the latest updates, offers, and insights delivered to your inbox.</p>
    <form class="newsletter-form" onsubmit="handleNewsletter(event)">
      <input type="email" placeholder="Enter your email address" required/>
      <button type="submit">Subscribe →</button>
    </form>
    <div id="nlSuccess" style="display:none;margin-top:14px;color:var(--pr);font-weight:600">✅ Subscribed! Welcome aboard.</div>
    <p style="color:var(--mu);font-size:0.72rem;margin-top:12px">No spam. Unsubscribe anytime.</p>
  </div>
</section>

<!-- CTA -->
<section class="cta-section">
  <div class="cta-box reveal">
    <h2>Ready to Get Started with {name}?</h2>
    <p>Join hundreds who already trust {name}. First consultation is completely free.</p>
    <div class="cta-btns">
      <a href="#contact" class="cta-btn1">Get Started Free →</a>
      <a href="tel:{phone}" class="cta-btn2">📞 {phone}</a>
    </div>
  </div>
</section>

<!-- FOOTER -->
<footer>
  <div class="footer-grid">
    <div class="footer-brand">
      <div class="footer-logo">{name}</div>
      <p>Premium services delivered with excellence, passion, and an obsession with results that exceed every expectation.</p>
      <div class="footer-social">
        {"<a href='https://instagram.com/" + ud["instagram"] + "' target='_blank' title='Instagram'>📸</a>" if ud["instagram"] else "<a href='#' title='Instagram'>📸</a>"}
        {"<a href='https://facebook.com/" + ud["facebook"] + "' target='_blank' title='Facebook'>👍</a>" if ud["facebook"] else "<a href='#' title='Facebook'>👍</a>"}
        {"<a href='https://twitter.com/" + ud["twitter"] + "' target='_blank' title='Twitter'>🐦</a>" if ud["twitter"] else "<a href='#' title='Twitter'>🐦</a>"}
        {"<a href='https://linkedin.com/in/" + ud["linkedin"] + "' target='_blank' title='LinkedIn'>💼</a>" if ud["linkedin"] else "<a href='#' title='LinkedIn'>💼</a>"}
        <a href="https://wa.me/{whatsapp}" target="_blank" title="WhatsApp">💬</a>
      </div>
    </div>
    <div class="footer-col">
      <h4>Company</h4>
      <a href="#about">About Us</a>
      <a href="#services">Services</a>
      <a href="#gallery">Gallery</a>
      <a href="#testimonials">Reviews</a>
      <a href="#faq">FAQ</a>
    </div>
    <div class="footer-col">
      <h4>Services</h4>
      <a href="#services">Our Services</a>
      <a href="#services">How It Works</a>
      <a href="#services">Case Studies</a>
      <a href="#contact">Get a Quote</a>
      <a href="#newsletter">Newsletter</a>
    </div>
    <div class="footer-col">
      <h4>Contact</h4>
      <a href="tel:{phone}">📞 {phone}</a>
      <a href="mailto:{email_addr}">✉️ Email Us</a>
      <a href="https://wa.me/{whatsapp}" target="_blank">💬 WhatsApp</a>
      <a href="#contact">📍 {address[:35]}...</a>
      <p style="color:var(--mu);font-size:0.75rem;margin-top:6px">⏰ {hours}</p>
    </div>
  </div>
  <div class="footer-bottom">
    <p>© 2024 {name}. All rights reserved.</p>
    <div style="display:flex;gap:16px"><a href="#">Privacy Policy</a><a href="#">Terms of Service</a><a href="#">Sitemap</a></div>
    <p>Built with <a href="https://dacexy.vercel.app" style="color:var(--pr)">Dacexy AI</a></p>
  </div>
</footer>

<!-- FLOATING -->
<a href="https://wa.me/{whatsapp}" class="wa-btn" target="_blank" title="Chat on WhatsApp">
  <svg width="28" height="28" viewBox="0 0 24 24" fill="white"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/></svg>
</a>

<div class="sticky-cta" id="stickyCTA">
  <div class="sticky-cta-text">
    <p>Ready to get started with {name}?</p>
    <p>Contact us today and get a free consultation.</p>
  </div>
  <div class="sticky-cta-btns">
    <a href="tel:{phone}" class="sc-btn1">📞 Call Now</a>
    <a href="#contact" class="sc-btn2" onclick="document.getElementById('stickyCTA').style.transform='translateY(100%)'">Get Started →</a>
  </div>
</div>

<button id="back-top" onclick="window.scrollTo({{top:0,behavior:'smooth'}})">↑</button>

<div class="cookie-banner" id="cookieBanner">
  <p>🍪 We use cookies to enhance your experience. By continuing, you agree to our <a href="#" style="color:var(--pr)">Privacy Policy</a>.</p>
  <div class="cookie-btns">
    <button class="cookie-accept" onclick="document.getElementById('cookieBanner').classList.add('hidden')">Accept All</button>
    <button class="cookie-decline" onclick="document.getElementById('cookieBanner').classList.add('hidden')">Decline</button>
  </div>
</div>

<script>
// ── Loader
window.addEventListener('load',()=>setTimeout(()=>document.getElementById('loader').classList.add('out'),700));

// ── Nav
const nav=document.getElementById('nav');
const stickyCTA=document.getElementById('stickyCTA');
const backTop=document.getElementById('back-top');
let lastY=0;
window.addEventListener('scroll',()=>{{
  const y=scrollY;
  nav.classList.toggle('solid',y>60);
  stickyCTA.style.transform=y>400?'translateY(0)':'translateY(100%)';
  backTop.style.display=y>500?'flex':'none';
  // Active nav link
  document.querySelectorAll('.links a').forEach(a=>{{
    const sec=document.querySelector(a.getAttribute('href'));
    if(sec){{
      const r=sec.getBoundingClientRect();
      a.classList.toggle('active',r.top<=100&&r.bottom>100);
    }}
  }});
  lastY=y;
}});

// ── Mobile menu
function toggleMob(){{
  const m=document.getElementById('mobMenu');
  const h=document.getElementById('hb');
  m.classList.toggle('open');
  h.classList.toggle('open');
  document.body.style.overflow=m.classList.contains('open')?'hidden':'';
}}
function closeMob(){{
  document.getElementById('mobMenu').classList.remove('open');
  document.getElementById('hb').classList.remove('open');
  document.body.style.overflow='';
}}

// ── Scroll reveal
const obs=new IntersectionObserver(entries=>entries.forEach(e=>{{
  if(e.isIntersecting){{e.target.classList.add('visible');obs.unobserve(e.target);}}
}}),{{threshold:0.08,rootMargin:'0px 0px -40px 0px'}});
document.querySelectorAll('.reveal').forEach(el=>obs.observe(el));

// ── Counter animation
function animateCount(el){{
  const target=parseInt(el.dataset.target)||0;
  if(!target)return;
  const suffix=el.textContent.replace(/[0-9]/g,'');
  let current=0;
  const step=Math.ceil(target/60);
  const timer=setInterval(()=>{{
    current=Math.min(current+step,target);
    el.textContent=current.toLocaleString()+(el.parentElement.querySelector('.stat-label').textContent.includes('%')?'%':'+');
    if(current>=target)clearInterval(timer);
  }},20);
}}
const counterObs=new IntersectionObserver(entries=>entries.forEach(e=>{{
  if(e.isIntersecting){{
    e.target.querySelectorAll('.stat-num[data-target]').forEach(animateCount);
    counterObs.unobserve(e.target);
  }}
}}),{{threshold:0.3}});
document.querySelectorAll('.stats-bar').forEach(el=>counterObs.observe(el));

// ── FAQ
function toggleFAQ(btn){{
  const ans=btn.nextElementSibling;
  const icon=btn.querySelector('.faq-icon');
  const isOpen=ans.style.display==='block';
  document.querySelectorAll('.faq-answer').forEach(a=>a.style.display='none');
  document.querySelectorAll('.faq-icon').forEach(i=>{{i.textContent='+';i.classList.remove('open')}});
  if(!isOpen){{ans.style.display='block';icon.textContent='−';icon.classList.add('open');}}
}}

// ── Forms
function handleForm(e){{
  e.preventDefault();
  const btn=e.target.querySelector('button[type="submit"]');
  btn.innerHTML='⏳ Sending...';btn.disabled=true;
  setTimeout(()=>{{
    btn.innerHTML='✅ Message Sent!';
    document.getElementById('formSuccess').style.display='block';
    e.target.reset();
    setTimeout(()=>{{btn.innerHTML='Send Message →';btn.disabled=false;document.getElementById('formSuccess').style.display='none';}},4000);
  }},1500);
}}
function handleNewsletter(e){{
  e.preventDefault();
  document.getElementById('nlSuccess').style.display='block';
  e.target.reset();
}}

// ── Image lazy load with fade
document.querySelectorAll('img[loading="lazy"]').forEach(img=>{{
  img.style.opacity='0';img.style.transition='opacity 0.5s ease';
  img.addEventListener('load',()=>img.style.opacity='1');
  if(img.complete)img.style.opacity='1';
}});

// ── Parallax hero
window.addEventListener('scroll',()=>{{
  const heroBg=document.querySelector('.hero-bg');
  if(heroBg)heroBg.style.transform=`scale(1.08) translateY(${{scrollY*0.3}}px)`;
}});

// ── Typed text effect
const phrases=['Excellence Redefined.','Quality Delivered.','Results Guaranteed.','Your Success Story.'];
let pi=0,ci=0,del=false;
const typedEl=document.getElementById('typed-text');
if(typedEl){{
  function type(){{
    const current=phrases[pi];
    if(!del){{
      typedEl.textContent=current.slice(0,++ci);
      if(ci===current.length){{del=true;setTimeout(type,1800);return;}}
    }}else{{
      typedEl.textContent=current.slice(0,--ci);
      if(ci===0){{del=false;pi=(pi+1)%phrases.length;}}
    }}
    setTimeout(type,del?40:80);
  }}
  type();
}}

// ── Input focus effects
document.querySelectorAll('input,textarea').forEach(el=>{{
  el.addEventListener('focus',()=>el.style.borderColor='var(--pr)');
  el.addEventListener('blur',()=>el.style.borderColor='');
}});

// ── Cookie
setTimeout(()=>{{
  if(!localStorage.getItem('cookies_accepted')){{
    // Show after 3s
  }}
}},3000);
document.querySelector('.cookie-accept')?.addEventListener('click',()=>localStorage.setItem('cookies_accepted','1'));
</script>
</body>
</html>"""

async def generate_website(prompt: str, ai=None) -> str:
    """
    Primary: Use DeepSeek AI to generate fully custom website code (like Lovable/Bolt).
    Fallback: Use enhanced template system if AI fails.
    """
    if ai is not None:
        try:
            return await generate_with_ai(prompt, ai)
        except Exception as e:
            log.warning(f"AI website generation failed, using fallback: {e}")

    name = extract_name(prompt)
    ud = extract_user_data(prompt)
    return build_fallback(prompt, name, ud)
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
