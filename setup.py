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
from src.infrastructure.ai_providers.deepseek import DeepSeekProvider

log = logging.getLogger("website")

def extract_name(prompt: str) -> str:
    p = prompt.strip()
    patterns = [
        r"(?:named?|called?|for)\\s+([A-Z][a-zA-Z0-9\\s]{1,30}?)(?:\\s+(?:with|that|which|website|app|platform|startup|business|restaurant|store|shop|company)|\\.|,|$)",
        r"^(?:website|landing page|page|site|app|platform|startup|business|restaurant|store|shop|company|portfolio)\\s+(?:for\\s+)?([A-Z][a-zA-Z0-9\\s]{1,25}?)(?:\\s+with|\\s+that|$)",
        r"^([A-Z][a-zA-Z0-9]{1,20})\\s+",
    ]
    for pat in patterns:
        m = re.search(pat, p, re.IGNORECASE)
        if m:
            name = m.group(1).strip()
            if 2 <= len(name) <= 30 and name.lower() not in ["a","an","the","my","our","build","make","create","generate"]:
                return name.title()
    words = [w for w in p.replace(",","").replace(".","").split()
             if len(w) > 2 and w.lower() not in
             ["for","the","with","that","this","and","build","make","create","generate",
              "website","page","site","app","landing","platform","startup","business",
              "restaurant","store","shop","company","portfolio","a","an","my","our"]]
    return words[0].title() if words else "Nexus"

def get_category(prompt: str) -> str:
    p = prompt.lower()
    if any(x in p for x in ["restaurant","food","cafe","kitchen","dining","menu","eat","chef","pizza","hotel","bakery","cuisine"]): return "restaurant"
    if any(x in p for x in ["saas","software","app","platform","tech","startup","ai","tool","dashboard","crm","b2b"]): return "saas"
    if any(x in p for x in ["portfolio","designer","freelance","artist","creative","photography","studio"]): return "portfolio"
    if any(x in p for x in ["shop","store","ecommerce","product","sell","buy","fashion","clothing","brand","retail"]): return "ecommerce"
    if any(x in p for x in ["agency","marketing","consultant","service","firm","corporate","enterprise"]): return "agency"
    if any(x in p for x in ["fitness","gym","health","wellness","yoga","trainer","sport","workout"]): return "fitness"
    return "business"

def get_palette(category: str) -> dict:
    palettes = {
        "restaurant": {"primary":"#C8102E","secondary":"#FF6B35","dark":"#0D0500","light":"#FFF8F0","accent":"#FFD700","grad1":"#1A0800","grad2":"#C8102E"},
        "saas": {"primary":"#6366F1","secondary":"#8B5CF6","dark":"#0A0A1A","light":"#F0F0FF","accent":"#06B6D4","grad1":"#0A0A1A","grad2":"#1E1B4B"},
        "portfolio": {"primary":"#F59E0B","secondary":"#EF4444","dark":"#0A0A0A","light":"#FAFAFA","accent":"#10B981","grad1":"#0A0A0A","grad2":"#1C1917"},
        "ecommerce": {"primary":"#059669","secondary":"#10B981","dark":"#022C22","light":"#ECFDF5","accent":"#F97316","grad1":"#022C22","grad2":"#064E3B"},
        "agency": {"primary":"#DC2626","secondary":"#F97316","dark":"#0A0000","light":"#FFF5F5","accent":"#FBBF24","grad1":"#0A0000","grad2":"#1C0A00"},
        "fitness": {"primary":"#EA580C","secondary":"#F97316","dark":"#0C0500","light":"#FFF7ED","accent":"#22C55E","grad1":"#0C0500","grad2":"#1C0A00"},
        "business": {"primary":"#2563EB","secondary":"#7C3AED","dark":"#020617","light":"#EFF6FF","accent":"#F59E0B","grad1":"#020617","grad2":"#0F172A"},
    }
    return palettes.get(category, palettes["business"])

def build_template(prompt: str) -> str:
    name = extract_name(prompt)
    category = get_category(prompt)
    p = get_palette(category)
    seed = abs(hash(prompt)) % 99999
    enc = urllib.parse.quote(prompt[:60])

    imgs = {
        "hero": f"https://image.pollinations.ai/prompt/ultra_realistic_cinematic_{enc}_hero_4k_dramatic_lighting?width=1600&height=900&seed={seed}&nologo=true&model=flux",
        "about": f"https://image.pollinations.ai/prompt/professional_{enc}_modern_premium?width=900&height=700&seed={seed+1}&nologo=true&model=flux",
        "g1": f"https://image.pollinations.ai/prompt/{enc}_showcase_elegant_premium?width=800&height=600&seed={seed+2}&nologo=true&model=flux",
        "g2": f"https://image.pollinations.ai/prompt/{enc}_detail_luxury_close?width=800&height=600&seed={seed+3}&nologo=true&model=flux",
        "g3": f"https://image.pollinations.ai/prompt/{enc}_lifestyle_aspirational?width=800&height=600&seed={seed+4}&nologo=true&model=flux",
        "g4": f"https://image.pollinations.ai/prompt/{enc}_product_hero_premium?width=800&height=600&seed={seed+5}&nologo=true&model=flux",
    }

    data = {
        "restaurant": {
            "tagline":"Where Every Bite Tells a Story",
            "sub":f"Experience authentic flavours crafted with passion at {name}. Fresh ingredients, timeless recipes, unforgettable moments.",
            "cta":"Reserve Your Table","cta2":"View Our Menu",
            "about_title":"A Legacy of Flavour","about_sub":f"Founded with a single vision — to serve food that moves people. At {name}, every dish is a love letter to tradition, reimagined for the modern palate.",
            "services_title":"Our Specialties",
            "services":[("🍽️","Fine Dining","Exquisite multi-course meals by award-winning chefs using the finest seasonal ingredients."),("🍷","Premium Bar","Curated wine cellar and craft cocktails to complement your dining experience."),("🎂","Private Events","Intimate celebrations and corporate dinners in exclusive private dining rooms."),("🚗","Delivery","Premium home delivery — restaurant quality, at your doorstep.")],
            "stats":[("15+","Years of Excellence"),("50K+","Happy Guests"),("4.9★","Average Rating"),("200+","Menu Items")],
            "testimonials":[("Arjun Mehta","Food Critic","The finest dining experience in the city. Every dish is a masterpiece of flavour and art."),("Priya Sharma","Regular Guest","We celebrate every anniversary here. The ambiance and food never disappoint."),("Rahul Singh","Corporate Client","Our team events here are always exceptional. Truly world-class.")],
        },
        "saas": {
            "tagline":"The Platform That Powers Your Growth",
            "sub":f"{name} gives teams AI-powered tools to move faster, work smarter, and scale without limits.",
            "cta":"Start Free Trial","cta2":"Watch Demo",
            "about_title":"Built for Scale","about_sub":f"{name} was built by engineers who were tired of duct-taping together broken tools. One platform. Every workflow. Zero compromise.",
            "services_title":"Core Features",
            "services":[("⚡","10x Faster","Automated workflows that eliminate manual work and accelerate every process."),("🤖","AI-Powered","Smart automation learns from your data and optimises without configuration."),("🔒","Enterprise Security","SOC2 compliant with end-to-end encryption and granular permissions."),("📊","Real-time Analytics","Beautiful dashboards with actionable insights — see what matters, instantly.")],
            "stats":[("10K+","Teams Using"),("99.9%","Uptime SLA"),("10x","Faster Results"),("4.8★","G2 Rating")],
            "testimonials":[("Sarah Chen","CTO, TechFlow","We cut operational costs by 60% in the first month. Absolutely transformative."),("Marcus Johnson","CEO, ScaleUp","The ROI was immediate. Our team ships 3x faster now."),("Aisha Patel","VP Engineering","Best developer experience we have ever had. World-class support.")],
        },
        "portfolio": {
            "tagline":"Crafting Digital Experiences That Matter",
            "sub":"I design and build exceptional digital products. Every pixel, every interaction — crafted with purpose.",
            "cta":"View My Work","cta2":"Let's Collaborate",
            "about_title":"Design With Intent","about_sub":"I believe great design is invisible. It just works. After 8 years and 50+ projects, I have learned that the best solutions are always the simplest ones.",
            "services_title":"What I Do",
            "services":[("🎨","UI/UX Design","Human-centred design that converts. From wireframes to pixel-perfect interfaces."),("💻","Web Development","Clean, performant code in React and Next.js. Fast, accessible, scalable."),("📱","Mobile Apps","Native iOS and Android apps that delight users on every device."),("🚀","Brand Identity","Complete visual identities — logo, typography, colour systems, guidelines.")],
            "stats":[("50+","Projects Delivered"),("30+","Happy Clients"),("5★","Average Rating"),("8+","Years Experience")],
            "testimonials":[("David Park","Founder, Launchpad","Exceptional work. Delivered beyond expectations and on time. Truly outstanding."),("Emma Wilson","Marketing Director","Our conversion rate increased by 240% after the redesign. World-class talent."),("Carlos Rivera","CEO, Momentum","The best investment we made this year. Completely transformed our market position.")],
        },
        "ecommerce": {
            "tagline":"Premium Quality, Delivered to Your Door",
            "sub":f"Discover {name}'s curated collection. Free shipping. 30-day returns. Shop with complete confidence.",
            "cta":"Shop Collection","cta2":"View Lookbook",
            "about_title":"Quality You Can Feel","about_sub":f"Every product at {name} passes our 47-point quality check. We source only the finest materials and work with artisans who share our obsession with excellence.",
            "services_title":"Why Shop With Us",
            "services":[("🚚","Free Shipping","Free express delivery on all orders. Get your order within 2-3 business days."),("✅","Quality Assured","Every product passes our 47-point quality check before reaching your door."),("↩️","Easy Returns","Hassle-free 30-day returns. No questions asked. Full refund guaranteed."),("💳","Secure Checkout","UPI, cards, EMI, COD — all payment methods with bank-grade security.")],
            "stats":[("50K+","Happy Customers"),("10K+","Products"),("4.9★","Average Rating"),("99%","Satisfaction")],
            "testimonials":[("Sneha Gupta","Verified Buyer","Amazing quality! Exactly as described, delivered in 2 days. Will shop again."),("Vikram Nair","Premium Member","Been shopping here 3 years. Quality is consistently excellent."),("Divya Krishnan","Style Blogger","My go-to store for premium finds. The curation is impeccable.")],
        },
        "agency": {
            "tagline":"We Build Brands That Dominate Markets",
            "sub":f"{name} is a full-service agency that transforms businesses through strategy, creative, and technology.",
            "cta":"Get a Proposal","cta2":"See Our Work",
            "about_title":"Strategy Meets Execution","about_sub":f"We are not a typical agency. We embed ourselves in your mission, move at startup speed, and deliver enterprise-grade results. That is the {name} difference.",
            "services_title":"Our Services",
            "services":[("📈","Growth Strategy","Data-driven strategies that have helped 100+ brands achieve explosive growth."),("🎯","Performance Marketing","ROI-focused campaigns across Google and Meta that consistently beat benchmarks."),("🌐","Digital Products","Websites, apps, and platforms that convert visitors into paying customers."),("✍️","Content & Creative","Storytelling that connects emotionally and drives action at every touchpoint.")],
            "stats":[("100+","Brands Grown"),("₹50Cr+","Revenue Generated"),("4.9★","Client Rating"),("8+","Years Experience")],
            "testimonials":[("Ankit Joshi","CMO, GrowthBrand","They tripled our qualified leads in 90 days. Best agency we have ever worked with."),("Meera Kapoor","Founder, StyleCo","The rebrand transformed how the market perceives us. Revenue up 180% YoY."),("Rajesh Patel","CEO, TechStart","From strategy to execution — a true growth partner. Exceptional results every time.")],
        },
        "fitness": {
            "tagline":"Transform Your Body. Elevate Your Life.",
            "sub":f"Join {name} and unlock your true potential. Expert coaching, world-class facilities, unstoppable community.",
            "cta":"Start Free Trial","cta2":"View Programs",
            "about_title":"More Than a Gym","about_sub":f"{name} is a movement. We believe every person has an elite athlete inside them — they just need the right environment, coaching, and community to unleash it.",
            "services_title":"Our Programs",
            "services":[("💪","Strength Training","Progressive overload programs by elite coaches to build real, lasting strength."),("🏃","Cardio & HIIT","High-intensity programs that torch calories and keep you energised all day."),("🧘","Mind & Body","Yoga, meditation, and mobility work to balance training and optimise recovery."),("🥗","Nutrition Coaching","Personalised meal plans to fuel your transformation from the inside out.")],
            "stats":[("5K+","Members"),("50+","Expert Trainers"),("98%","Success Rate"),("4.9★","Member Rating")],
            "testimonials":[("Kiran Rao","Member since 2022","Lost 20kg in 6 months. The trainers are exceptional and the community keeps you going."),("Ananya Singh","Marathon Runner","Improved my personal best by 22 minutes. The coaching here is world-class."),("Dev Malhotra","Strength Athlete","Gained 12kg of muscle in a year. The programming is scientific, the results real.")],
        },
        "business": {
            "tagline":"Excellence Delivered. Every Single Time.",
            "sub":f"{name} combines deep expertise with innovative thinking to deliver results that exceed every expectation.",
            "cta":"Get Started Today","cta2":"Learn More",
            "about_title":"Why We Are Different","about_sub":f"At {name}, we do not just complete projects — we build partnerships. We are invested in your success as deeply as you are, and our track record proves it.",
            "services_title":"What We Offer",
            "services":[("⚡","Fast Delivery","Exceptional results in record time — without compromising on quality or detail."),("🎯","Results Focused","Every decision tied to measurable outcomes and your specific business goals."),("🤝","True Partnership","We embed in your mission and work as a genuine extension of your team."),("🛡️","Proven Reliability","100+ satisfied clients trust us with their most important projects.")],
            "stats":[("100+","Projects Done"),("50+","Happy Clients"),("4.9★","Average Rating"),("5+","Years Experience")],
            "testimonials":[("Rohit Kumar","Managing Director","Exceptional quality and professionalism. Delivered exactly what they promised and more."),("Nisha Agarwal","Operations Head","Reliable, skilled, genuinely invested in our success. Best vendor relationship we have."),("Amit Sharma","Founder","Working with them was a game-changer for our business. Results speak for themselves.")],
        },
    }

    d = data.get(category, data["business"])

    services_html = ""
    for icon, title, desc in d["services"]:
        services_html += f"""
        <div class="service-card">
            <div class="service-icon">{icon}</div>
            <h3>{title}</h3>
            <p>{desc}</p>
        </div>"""

    stats_html = ""
    for num, label in d["stats"]:
        stats_html += f\'<div class="stat-item"><div class="stat-num">{num}</div><div class="stat-label">{label}</div></div>\'

    testimonials_html = ""
    for author, role, text in d["testimonials"]:
        initials = "".join([w[0] for w in author.split()[:2]])
        testimonials_html += f"""
        <div class="testimonial-card">
            <div class="stars">★★★★★</div>
            <p class="t-text">"{text}"</p>
            <div class="t-author">
                <div class="t-avatar">{initials}</div>
                <div><div class="t-name">{author}</div><div class="t-role">{role}</div></div>
            </div>
        </div>"""

    gallery_html = ""
    for key in ["g1","g2","g3","g4"]:
        gallery_html += f\'<div class="gallery-item"><img src="{imgs[key]}" alt="Gallery" loading="lazy"/></div>\'

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{name} — {d["tagline"]}</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=Playfair+Display:ital,wght@0,700;0,800;0,900;1,700&display=swap" rel="stylesheet">
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
:root{{
  --pr:{p["primary"]};--sc:{p["secondary"]};--dk:{p["dark"]};
  --lt:{p["light"]};--ac:{p["accent"]};--g1:{p["grad1"]};--g2:{p["grad2"]};
  --white:#fff;--gray:#6B7280;--border:rgba(0,0,0,0.08);
  --radius:16px;--shadow:0 25px 60px rgba(0,0,0,0.15);
}}
html{{scroll-behavior:smooth}}
body{{font-family:"Inter",sans-serif;color:var(--dk);background:var(--white);overflow-x:hidden;line-height:1.6}}

/* ── NAV ── */
nav{{position:fixed;top:0;width:100%;z-index:1000;padding:0 5%;transition:all 0.4s ease}}
nav.scrolled{{background:rgba(255,255,255,0.97);backdrop-filter:blur(24px);box-shadow:0 4px 40px rgba(0,0,0,0.1);border-bottom:1px solid var(--border)}}
.nav-inner{{max-width:1280px;margin:0 auto;display:flex;align-items:center;justify-content:space-between;height:76px}}
.nav-logo{{font-family:"Playfair Display",serif;font-size:1.9rem;font-weight:900;color:#fff;text-decoration:none;transition:color 0.3s;letter-spacing:-0.5px}}
nav.scrolled .nav-logo{{color:var(--pr)}}
.nav-links{{display:flex;align-items:center;gap:36px;list-style:none}}
.nav-links a{{color:rgba(255,255,255,0.85);text-decoration:none;font-weight:500;font-size:0.9rem;transition:all 0.2s}}
nav.scrolled .nav-links a{{color:var(--gray)}}
.nav-links a:hover{{color:#fff}}
nav.scrolled .nav-links a:hover{{color:var(--pr)}}
.nav-cta{{background:var(--pr)!important;color:#fff!important;padding:11px 26px;border-radius:100px;font-weight:700!important;transition:all 0.3s!important;box-shadow:0 4px 20px rgba(0,0,0,0.2)}}
.nav-cta:hover{{transform:translateY(-2px);box-shadow:0 8px 30px rgba(0,0,0,0.3)!important}}
.nav-hamburger{{display:none;background:none;border:none;cursor:pointer;flex-direction:column;gap:5px;padding:4px}}
.nav-hamburger span{{width:24px;height:2px;background:#fff;border-radius:2px;transition:all 0.3s;display:block}}
nav.scrolled .nav-hamburger span{{background:var(--dk)}}
.nav-mobile{{display:none;position:fixed;top:76px;left:0;right:0;background:#fff;border-bottom:1px solid var(--border);padding:20px 5%;flex-direction:column;gap:16px;box-shadow:0 10px 40px rgba(0,0,0,0.1)}}
.nav-mobile.open{{display:flex}}
.nav-mobile a{{color:var(--gray);text-decoration:none;font-weight:600;font-size:0.95rem;padding:8px 0;border-bottom:1px solid var(--border)}}
.nav-mobile .mob-cta{{background:var(--pr);color:#fff!important;text-align:center;padding:14px;border-radius:12px;border:none!important;margin-top:4px}}

/* ── HERO ── */
.hero{{
  position:relative;min-height:100vh;display:flex;align-items:center;
  padding:100px 5% 80px;overflow:hidden;
  background:linear-gradient(135deg,var(--g1) 0%,var(--g2) 50%,var(--pr) 100%);
}}
.hero-bg-img{{position:absolute;inset:0;background:url("{imgs["hero"]}") center/cover no-repeat;opacity:0.12;filter:blur(3px);transform:scale(1.05)}}
.hero-overlay{{position:absolute;inset:0;background:linear-gradient(135deg,{p["dark"]}F5 0%,{p["primary"]}BB 70%,{p["secondary"]}88 100%)}}
.hero-particles{{position:absolute;inset:0;overflow:hidden;pointer-events:none}}
.particle{{position:absolute;border-radius:50%;background:rgba(255,255,255,0.06);animation:float linear infinite}}
@keyframes float{{0%{{transform:translateY(100vh) rotate(0deg);opacity:0}}10%{{opacity:1}}90%{{opacity:1}}100%{{transform:translateY(-100px) rotate(720deg);opacity:0}}}}
.hero-inner{{position:relative;z-index:2;max-width:1280px;margin:0 auto;width:100%;display:grid;grid-template-columns:1fr 1fr;gap:80px;align-items:center}}
.hero-badge{{display:inline-flex;align-items:center;gap:8px;background:rgba(255,255,255,0.12);backdrop-filter:blur(12px);border:1px solid rgba(255,255,255,0.25);color:rgba(255,255,255,0.95);padding:9px 20px;border-radius:100px;font-size:0.78rem;font-weight:700;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:24px;animation:fadeInUp 0.6s ease}}
.badge-dot{{width:8px;height:8px;border-radius:50%;background:var(--ac);box-shadow:0 0 12px var(--ac);animation:pulse 2s infinite}}
@keyframes pulse{{0%,100%{{opacity:1;transform:scale(1)}}50%{{opacity:0.6;transform:scale(1.3)}}}}
.hero-title{{font-family:"Playfair Display",serif;font-size:clamp(2.8rem,5vw,4.5rem);font-weight:900;color:#fff;line-height:1.05;letter-spacing:-2px;margin-bottom:16px;animation:fadeInUp 0.7s ease 0.1s both}}
.hero-title-accent{{color:var(--ac);font-style:italic;display:block}}
.hero-sub{{font-size:1.05rem;color:rgba(255,255,255,0.75);line-height:1.75;margin-bottom:36px;max-width:480px;animation:fadeInUp 0.7s ease 0.2s both}}
.hero-btns{{display:flex;gap:14px;flex-wrap:wrap;animation:fadeInUp 0.7s ease 0.3s both}}
.btn-primary{{display:inline-flex;align-items:center;gap:8px;background:var(--ac);color:var(--dk);font-weight:800;font-size:0.9rem;padding:16px 32px;border-radius:100px;text-decoration:none;transition:all 0.3s;box-shadow:0 8px 30px rgba(0,0,0,0.3);letter-spacing:0.3px}}
.btn-primary:hover{{transform:translateY(-3px);box-shadow:0 16px 40px rgba(0,0,0,0.4);filter:brightness(1.1)}}
.btn-secondary{{display:inline-flex;align-items:center;gap:8px;background:rgba(255,255,255,0.1);backdrop-filter:blur(10px);color:#fff;font-weight:700;font-size:0.9rem;padding:16px 32px;border-radius:100px;text-decoration:none;border:1px solid rgba(255,255,255,0.3);transition:all 0.3s}}
.btn-secondary:hover{{background:rgba(255,255,255,0.2);transform:translateY(-3px)}}
.hero-img-wrap{{position:relative;animation:fadeInRight 0.9s ease 0.2s both}}
@keyframes fadeInRight{{from{{opacity:0;transform:translateX(40px)}}to{{opacity:1;transform:translateX(0)}}}}
.hero-img{{width:100%;border-radius:24px;overflow:hidden;box-shadow:0 40px 80px rgba(0,0,0,0.5);border:1px solid rgba(255,255,255,0.1);position:relative}}
.hero-img img{{width:100%;height:420px;object-fit:cover;display:block}}
.hero-img-badge{{position:absolute;bottom:20px;left:20px;background:rgba(0,0,0,0.7);backdrop-filter:blur(20px);border:1px solid rgba(255,255,255,0.1);padding:12px 18px;border-radius:14px;display:flex;align-items:center;gap:10px}}
.live-dot{{width:8px;height:8px;border-radius:50%;background:#22C55E;box-shadow:0 0 10px #22C55E;animation:pulse 2s infinite}}
.live-text{{color:#fff;font-size:0.78rem;font-weight:600}}
@keyframes fadeInUp{{from{{opacity:0;transform:translateY(30px)}}to{{opacity:1;transform:translateY(0)}}}}

/* ── STATS BAR ── */
.stats-bar{{background:var(--dk);padding:0 5%}}
.stats-inner{{max-width:1280px;margin:0 auto;display:grid;grid-template-columns:repeat(4,1fr);border-left:1px solid rgba(255,255,255,0.06)}}
.stat-item{{padding:36px 24px;text-align:center;border-right:1px solid rgba(255,255,255,0.06);border-bottom:1px solid rgba(255,255,255,0.06);transition:background 0.3s}}
.stat-item:hover{{background:rgba(255,255,255,0.03)}}
.stat-num{{font-family:"Playfair Display",serif;font-size:2.4rem;font-weight:900;color:#fff;line-height:1;margin-bottom:6px}}
.stat-label{{font-size:0.75rem;color:rgba(255,255,255,0.45);font-weight:600;text-transform:uppercase;letter-spacing:1.2px}}

/* ── ABOUT ── */
.about{{padding:120px 5%;background:var(--lt)}}
.about-inner{{max-width:1280px;margin:0 auto;display:grid;grid-template-columns:1fr 1fr;gap:80px;align-items:center}}
.about-img{{border-radius:24px;overflow:hidden;box-shadow:var(--shadow);position:relative}}
.about-img img{{width:100%;height:500px;object-fit:cover;display:block;transition:transform 0.6s ease}}
.about-img:hover img{{transform:scale(1.04)}}
.about-img-tag{{position:absolute;top:24px;left:24px;background:var(--pr);color:#fff;font-size:0.72rem;font-weight:800;padding:8px 16px;border-radius:100px;text-transform:uppercase;letter-spacing:1px}}
.section-label{{display:inline-flex;align-items:center;gap:8px;background:var(--pr)18;color:var(--pr);font-size:0.72rem;font-weight:800;text-transform:uppercase;letter-spacing:2px;padding:8px 18px;border-radius:100px;margin-bottom:20px;border:1px solid var(--pr)30}}
.section-title{{font-family:"Playfair Display",serif;font-size:clamp(2rem,3.5vw,3rem);font-weight:900;color:var(--dk);line-height:1.15;letter-spacing:-1px;margin-bottom:20px}}
.section-title span{{color:var(--pr)}}
.section-sub{{font-size:1rem;color:var(--gray);line-height:1.8;margin-bottom:36px}}
.about-features{{display:flex;flex-direction:column;gap:16px}}
.about-feature{{display:flex;align-items:flex-start;gap:14px;padding:18px;background:#fff;border-radius:16px;border:1px solid var(--border);transition:all 0.3s}}
.about-feature:hover{{border-color:var(--pr);box-shadow:0 8px 30px rgba(0,0,0,0.08);transform:translateX(4px)}}
.af-icon{{width:44px;height:44px;border-radius:12px;background:var(--pr)15;display:flex;align-items:center;justify-content:center;font-size:1.4rem;flex-shrink:0}}
.af-text h4{{font-weight:700;font-size:0.9rem;color:var(--dk);margin-bottom:4px}}
.af-text p{{font-size:0.82rem;color:var(--gray);line-height:1.5}}

/* ── SERVICES ── */
.services{{padding:120px 5%;background:#fff}}
.services-inner{{max-width:1280px;margin:0 auto}}
.section-header{{text-align:center;margin-bottom:60px}}
.services-grid{{display:grid;grid-template-columns:repeat(2,1fr);gap:24px}}
.service-card{{
  background:var(--lt);border:1px solid var(--border);border-radius:24px;
  padding:36px;transition:all 0.4s cubic-bezier(0.4,0,0.2,1);
  position:relative;overflow:hidden;
}}
.service-card::before{{
  content:"";position:absolute;inset:0;
  background:linear-gradient(135deg,var(--pr)08,transparent);
  opacity:0;transition:opacity 0.4s;
}}
.service-card:hover{{border-color:var(--pr);box-shadow:0 20px 60px rgba(0,0,0,0.12);transform:translateY(-6px)}}
.service-card:hover::before{{opacity:1}}
.service-icon{{font-size:2.4rem;margin-bottom:20px;display:block}}
.service-card h3{{font-family:"Playfair Display",serif;font-size:1.3rem;font-weight:800;color:var(--dk);margin-bottom:12px}}
.service-card p{{font-size:0.88rem;color:var(--gray);line-height:1.7}}

/* ── GALLERY ── */
.gallery{{padding:80px 5%;background:var(--dk)}}
.gallery-inner{{max-width:1280px;margin:0 auto}}
.gallery-grid{{display:grid;grid-template-columns:repeat(2,1fr);gap:16px;margin-top:48px}}
.gallery-item{{border-radius:20px;overflow:hidden;aspect-ratio:4/3;position:relative;cursor:pointer}}
.gallery-item img{{width:100%;height:100%;object-fit:cover;display:block;transition:transform 0.6s ease}}
.gallery-item:hover img{{transform:scale(1.08)}}
.gallery-item::after{{content:"";position:absolute;inset:0;background:linear-gradient(to top,rgba(0,0,0,0.4),transparent);opacity:0;transition:opacity 0.3s}}
.gallery-item:hover::after{{opacity:1}}

/* ── TESTIMONIALS ── */
.testimonials{{padding:120px 5%;background:var(--lt)}}
.testimonials-inner{{max-width:1280px;margin:0 auto}}
.testimonials-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:24px;margin-top:48px}}
.testimonial-card{{
  background:#fff;border:1px solid var(--border);border-radius:24px;
  padding:32px;transition:all 0.3s;position:relative;overflow:hidden;
}}
.testimonial-card::before{{content:"\\201C";position:absolute;top:-10px;right:20px;font-size:8rem;color:var(--pr);opacity:0.06;font-family:"Playfair Display",serif;line-height:1}}
.testimonial-card:hover{{border-color:var(--pr);box-shadow:0 20px 50px rgba(0,0,0,0.1);transform:translateY(-4px)}}
.stars{{color:var(--ac);font-size:1rem;margin-bottom:16px;letter-spacing:2px}}
.t-text{{font-size:0.9rem;color:var(--gray);line-height:1.75;margin-bottom:24px;font-style:italic}}
.t-author{{display:flex;align-items:center;gap:12px}}
.t-avatar{{width:46px;height:46px;border-radius:50%;background:linear-gradient(135deg,var(--pr),var(--sc));display:flex;align-items:center;justify-content:center;color:#fff;font-weight:800;font-size:0.9rem;flex-shrink:0}}
.t-name{{font-weight:700;font-size:0.88rem;color:var(--dk)}}
.t-role{{font-size:0.75rem;color:var(--gray)}}

/* ── CTA ── */
.cta-section{{padding:120px 5%;background:#fff}}
.cta-inner{{
  max-width:1000px;margin:0 auto;
  background:linear-gradient(135deg,var(--g1),var(--pr) 60%,var(--sc));
  border-radius:32px;padding:80px 60px;text-align:center;
  position:relative;overflow:hidden;box-shadow:0 40px 80px rgba(0,0,0,0.2);
}}
.cta-inner::before{{content:"";position:absolute;top:-50%;right:-10%;width:500px;height:500px;border-radius:50%;background:rgba(255,255,255,0.05);pointer-events:none}}
.cta-inner::after{{content:"";position:absolute;bottom:-30%;left:-5%;width:350px;height:350px;border-radius:50%;background:rgba(255,255,255,0.04);pointer-events:none}}
.cta-title{{font-family:"Playfair Display",serif;font-size:clamp(2rem,4vw,3.2rem);font-weight:900;color:#fff;margin-bottom:16px;position:relative;z-index:1;letter-spacing:-1px}}
.cta-sub{{font-size:1rem;color:rgba(255,255,255,0.7);margin-bottom:40px;position:relative;z-index:1;max-width:500px;margin-left:auto;margin-right:auto}}
.cta-btns{{display:flex;gap:14px;justify-content:center;flex-wrap:wrap;position:relative;z-index:1}}
.cta-btn-primary{{display:inline-flex;align-items:center;gap:8px;background:var(--ac);color:var(--dk);font-weight:800;padding:16px 36px;border-radius:100px;text-decoration:none;font-size:0.9rem;transition:all 0.3s;box-shadow:0 8px 30px rgba(0,0,0,0.3)}}
.cta-btn-primary:hover{{transform:translateY(-3px);filter:brightness(1.1);box-shadow:0 16px 40px rgba(0,0,0,0.4)}}
.cta-btn-secondary{{display:inline-flex;align-items:center;gap:8px;background:rgba(255,255,255,0.12);backdrop-filter:blur(10px);color:#fff;font-weight:700;padding:16px 36px;border-radius:100px;text-decoration:none;font-size:0.9rem;border:1px solid rgba(255,255,255,0.3);transition:all 0.3s}}
.cta-btn-secondary:hover{{background:rgba(255,255,255,0.2);transform:translateY(-3px)}}

/* ── FOOTER ── */
footer{{background:var(--dk);padding:60px 5% 30px;border-top:1px solid rgba(255,255,255,0.06)}}
.footer-inner{{max-width:1280px;margin:0 auto}}
.footer-top{{display:grid;grid-template-columns:2fr 1fr 1fr 1fr;gap:48px;margin-bottom:48px}}
.footer-brand p{{font-size:0.85rem;color:rgba(255,255,255,0.45);margin-top:12px;line-height:1.7;max-width:260px}}
.footer-logo{{font-family:"Playfair Display",serif;font-size:1.6rem;font-weight:900;color:#fff}}
.footer-col h4{{font-weight:700;font-size:0.8rem;color:rgba(255,255,255,0.5);text-transform:uppercase;letter-spacing:1.5px;margin-bottom:16px}}
.footer-col a{{display:block;color:rgba(255,255,255,0.4);text-decoration:none;font-size:0.85rem;margin-bottom:10px;transition:color 0.2s}}
.footer-col a:hover{{color:#fff}}
.footer-bottom{{border-top:1px solid rgba(255,255,255,0.06);padding-top:28px;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px}}
.footer-bottom p{{font-size:0.78rem;color:rgba(255,255,255,0.25)}}

/* ── RESPONSIVE ── */
@media(max-width:900px){{
  .hero-inner{{grid-template-columns:1fr;gap:48px;text-align:center}}
  .hero-img-wrap{{order:-1}}
  .hero-sub{{max-width:100%}}
  .hero-btns{{justify-content:center}}
  .about-inner{{grid-template-columns:1fr;gap:48px}}
  .services-grid{{grid-template-columns:1fr}}
  .gallery-grid{{grid-template-columns:1fr 1fr}}
  .testimonials-grid{{grid-template-columns:1fr}}
  .stats-inner{{grid-template-columns:repeat(2,1fr)}}
  .footer-top{{grid-template-columns:1fr 1fr;gap:32px}}
  .nav-links,.nav-cta-wrap{{display:none}}
  .nav-hamburger{{display:flex}}
  .cta-inner{{padding:60px 30px}}
}}
@media(max-width:540px){{
  .gallery-grid{{grid-template-columns:1fr}}
  .stats-inner{{grid-template-columns:1fr 1fr}}
  .hero-title{{font-size:2.4rem}}
  .footer-top{{grid-template-columns:1fr}}
  .footer-bottom{{flex-direction:column;text-align:center}}
}}
</style>
</head>
<body>

<!-- NAV -->
<nav id="nav">
  <div class="nav-inner">
    <a href="#" class="nav-logo">{name}</a>
    <ul class="nav-links">
      <li><a href="#about">About</a></li>
      <li><a href="#services">{d["services_title"]}</a></li>
      <li><a href="#gallery">Gallery</a></li>
      <li><a href="#contact" class="nav-cta">{d["cta"]}</a></li>
    </ul>
    <button class="nav-hamburger" id="hamburger" aria-label="Menu">
      <span></span><span></span><span></span>
    </button>
  </div>
</nav>
<div class="nav-mobile" id="navMobile">
  <a href="#about">About</a>
  <a href="#services">{d["services_title"]}</a>
  <a href="#gallery">Gallery</a>
  <a href="#contact" class="mob-cta">{d["cta"]}</a>
</div>

<!-- HERO -->
<section class="hero" id="home">
  <div class="hero-bg-img"></div>
  <div class="hero-overlay"></div>
  <div class="hero-particles" id="particles"></div>
  <div class="hero-inner">
    <div class="hero-content">
      <div class="hero-badge"><span class="badge-dot"></span>✦ {name} · {category.title()}</div>
      <h1 class="hero-title">
        {name}
        <span class="hero-title-accent">{d["tagline"]}</span>
      </h1>
      <p class="hero-sub">{d["sub"]}</p>
      <div class="hero-btns">
        <a href="#contact" class="btn-primary">{d["cta"]} →</a>
        <a href="#services" class="btn-secondary">▶ {d["cta2"]}</a>
      </div>
    </div>
    <div class="hero-img-wrap">
      <div class="hero-img">
        <img src="{imgs["hero"]}" alt="{name}" loading="eager"/>
        <div class="hero-img-badge">
          <div class="live-dot"></div>
          <span class="live-text">Live &amp; Serving Clients Now</span>
        </div>
      </div>
    </div>
  </div>
</section>

<!-- STATS -->
<div class="stats-bar">
  <div class="stats-inner">
    {stats_html}
  </div>
</div>

<!-- ABOUT -->
<section class="about" id="about">
  <div class="about-inner">
    <div class="about-img">
      <img src="{imgs["about"]}" alt="About {name}" loading="lazy"/>
      <div class="about-img-tag">Est. 2010</div>
    </div>
    <div class="about-text">
      <div class="section-label">✦ Our Story</div>
      <h2 class="section-title">{d["about_title"]}<span>.</span></h2>
      <p class="section-sub">{d["about_sub"]}</p>
      <div class="about-features">
        <div class="about-feature">
          <div class="af-icon">🏆</div>
          <div class="af-text"><h4>Award-Winning Quality</h4><p>Recognised for excellence by industry leaders and customers alike.</p></div>
        </div>
        <div class="about-feature">
          <div class="af-icon">🌍</div>
          <div class="af-text"><h4>Trusted Globally</h4><p>Serving clients across India and beyond with consistent world-class results.</p></div>
        </div>
        <div class="about-feature">
          <div class="af-icon">💡</div>
          <div class="af-text"><h4>Innovation First</h4><p>We never stop improving — always finding better ways to serve you.</p></div>
        </div>
      </div>
    </div>
  </div>
</section>

<!-- SERVICES -->
<section class="services" id="services">
  <div class="services-inner">
    <div class="section-header">
      <div class="section-label">✦ {d["services_title"]}</div>
      <h2 class="section-title">What Makes Us <span>Different</span></h2>
      <p class="section-sub" style="max-width:500px;margin:0 auto">Everything you need, crafted to the highest standard — nothing less.</p>
    </div>
    <div class="services-grid">
      {services_html}
    </div>
  </div>
</section>

<!-- GALLERY -->
<section class="gallery" id="gallery">
  <div class="gallery-inner">
    <div class="section-header">
      <div class="section-label" style="background:rgba(255,255,255,0.1);color:rgba(255,255,255,0.8);border-color:rgba(255,255,255,0.2)">✦ Gallery</div>
      <h2 class="section-title" style="color:#fff">See It For <span style="color:var(--ac)">Yourself</span></h2>
    </div>
    <div class="gallery-grid">
      {gallery_html}
    </div>
  </div>
</section>

<!-- TESTIMONIALS -->
<section class="testimonials" id="testimonials">
  <div class="testimonials-inner">
    <div class="section-header">
      <div class="section-label">✦ Testimonials</div>
      <h2 class="section-title">What Our <span>Clients Say</span></h2>
      <p class="section-sub" style="max-width:480px;margin:0 auto">Real results from real people who trusted us with what matters most.</p>
    </div>
    <div class="testimonials-grid">
      {testimonials_html}
    </div>
  </div>
</section>

<!-- CTA -->
<section class="cta-section" id="contact">
  <div class="cta-inner">
    <h2 class="cta-title">Ready to Get Started?</h2>
    <p class="cta-sub">Join thousands who have already transformed their experience with {name}. Take the first step today.</p>
    <div class="cta-btns">
      <a href="mailto:hello@{name.lower().replace(' ','')}.com" class="cta-btn-primary">{d["cta"]} →</a>
      <a href="tel:+919999999999" class="cta-btn-secondary">📞 Call Us Now</a>
    </div>
  </div>
</section>

<!-- FOOTER -->
<footer>
  <div class="footer-inner">
    <div class="footer-top">
      <div class="footer-brand">
        <div class="footer-logo">{name}</div>
        <p>{d["sub"][:100]}...</p>
      </div>
      <div class="footer-col">
        <h4>Company</h4>
        <a href="#about">About Us</a>
        <a href="#services">Services</a>
        <a href="#gallery">Gallery</a>
        <a href="#contact">Contact</a>
      </div>
      <div class="footer-col">
        <h4>Services</h4>
        {''.join([f\'<a href="#services">{s[1]}</a>\' for s in d["services"]])}
      </div>
      <div class="footer-col">
        <h4>Contact</h4>
        <a href="mailto:hello@{name.lower().replace(' ','')}.com">Email Us</a>
        <a href="tel:+919999999999">+91 99999 99999</a>
        <a href="#">Instagram</a>
        <a href="#">LinkedIn</a>
      </div>
    </div>
    <div class="footer-bottom">
      <p>© 2024 {name}. All rights reserved.</p>
      <p>Built with ❤️ using Dacexy AI</p>
    </div>
  </div>
</footer>

<script>
// Nav scroll
const nav=document.getElementById("nav");
window.addEventListener("scroll",()=>{{nav.classList.toggle("scrolled",scrollY>60)}});

// Hamburger
const hb=document.getElementById("hamburger");
const nm=document.getElementById("navMobile");
hb.addEventListener("click",()=>{{nm.classList.toggle("open")}});
nm.querySelectorAll("a").forEach(a=>a.addEventListener("click",()=>nm.classList.remove("open")));

// Particles
const pc=document.getElementById("particles");
for(let i=0;i<18;i++){{
  const d=document.createElement("div");
  const s=Math.random()*60+20;
  d.className="particle";
  d.style.cssText=`width:${{s}}px;height:${{s}}px;left:${{Math.random()*100}}%;animation-duration:${{Math.random()*15+10}}s;animation-delay:${{Math.random()*10}}s;`;
  pc.appendChild(d);
}}

// Scroll reveal
const observer=new IntersectionObserver((entries)=>{{
  entries.forEach(e=>{{
    if(e.isIntersecting){{
      e.target.style.opacity="1";
      e.target.style.transform="translateY(0)";
    }}
  }});
}},{{threshold:0.1}});
document.querySelectorAll(".service-card,.testimonial-card,.about-feature,.gallery-item,.stat-item").forEach(el=>{{
  el.style.opacity="0";
  el.style.transform="translateY(30px)";
  el.style.transition="opacity 0.6s ease,transform 0.6s ease";
  observer.observe(el);
}});
</script>
</body>
</html>"""

async def generate_website(prompt: str, user_id: str) -> str:
    try:
        return build_template(prompt)
    except Exception as e:
        log.error(f"Website generation error: {{e}}")
        raise
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

router = APIRouter(prefix="/auth", tags=["auth"])
bearer = HTTPBearer(auto_error=False)

# ═══════════════════════════════════════════════════════════
# ENTERPRISE RATE LIMITING
# ═══════════════════════════════════════════════════════════

_rate_store: dict = defaultdict(lambda: {"count": 0, "window_start": 0.0, "blocked_until": 0.0})

RATE_LIMITS = {
    "register":        {"rpm": 3,   "window": 60,   "block": 300},
    "login":           {"rpm": 10,  "window": 60,   "block": 60},
    "login_fail":      {"rpm": 5,   "window": 300,  "block": 900},
    "google":          {"rpm": 10,  "window": 60,   "block": 60},
    "verify":          {"rpm": 5,   "window": 60,   "block": 120},
    "default":         {"rpm": 30,  "window": 60,   "block": 60},
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

    # Check if currently blocked
    if store["blocked_until"] > now:
        wait = int(store["blocked_until"] - now)
        raise HTTPException(
            status_code=429,
            detail=f"Too many attempts. Please wait {wait} seconds before trying again.",
            headers={"Retry-After": str(wait), "X-RateLimit-Limit": str(cfg["rpm"])}
        )

    # Reset window if expired
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

# Track failed login attempts separately per email
_login_failures: dict = defaultdict(lambda: {"count": 0, "first_fail": 0.0, "blocked_until": 0.0})

def check_login_failures(email: str) -> None:
    now = time.time()
    record = _login_failures[email.lower()]
    if record["blocked_until"] > now:
        wait = int(record["blocked_until"] - now)
        raise HTTPException(
            status_code=429,
            detail=f"Account temporarily locked due to multiple failed attempts. Try again in {wait} seconds.",
            headers={"Retry-After": str(wait)}
        )
    # Reset if window expired (5 minutes)
    if now - record["first_fail"] > 300:
        record["count"] = 0
        record["first_fail"] = now

def record_login_failure(email: str) -> None:
    now = time.time()
    record = _login_failures[email.lower()]
    if record["count"] == 0:
        record["first_fail"] = now
    record["count"] += 1
    # Progressive lockout
    if record["count"] >= 10:
        record["blocked_until"] = now + 3600   # 1 hour
    elif record["count"] >= 5:
        record["blocked_until"] = now + 900    # 15 minutes
    elif record["count"] >= 3:
        record["blocked_until"] = now + 60     # 1 minute

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
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters long.")
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
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or account disabled")
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

    org_name = body.org_name.strip() if body.org_name.strip() else (body.full_name.strip().split()[0] + "s Workspace")
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
# LOGIN
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

    access = create_access_token(str(user.id), {"org_id": str(user.org_id), "role": user.role})
    refresh = create_refresh_token()
    db.add(RefreshToken(
        user_id=user.id,
        token_hash=hash_password(refresh),
        expires_at=datetime.utcnow() + timedelta(days=30)
    ))
    await db.commit()
    return TokenResponse(access_token=access, refresh_token=refresh)

# ═══════════════════════════════════════════════════════════
# ME
# ═══════════════════════════════════════════════════════════

@router.get("/me")
async def me(user: User = Depends(_get_current_user), db: AsyncSession = Depends(get_db)):
    org = await db.get(Organization, user.org_id)
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
    return {"message": "Logged out successfully"}

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
        return RedirectResponse("https://dacexy.vercel.app/login?error=Google+OAuth+not+configured+on+server")

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
# GOOGLE CALLBACK
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
            # Exchange code for token
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

            # Get user info
            user_res = await client.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {google_access_token}"}
            )
            info = user_res.json()

        email = (info.get("email") or "").lower().strip()
        full_name = (info.get("name") or "").strip()

        if not email:
            return RedirectResponse(f"{FRONTEND}/login?error=no_email_from_google")
        if not full_name:
            full_name = email.split("@")[0].title()

        # Find or create user
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

        if not user:
            first_name = full_name.split()[0] if full_name.split() else "User"
            org_name = first_name + "s Workspace"
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
                metadata_={"provider": "google", "google_id": info.get("id", "")}
            )
            db.add(user)
            await db.flush()
        else:
            # Update name if changed
            if full_name and user.full_name != full_name:
                user.full_name = full_name

        await db.commit()

        jwt_token = create_access_token(
            str(user.id),
            {"org_id": str(user.org_id), "role": user.role}
        )
        return RedirectResponse(f"{FRONTEND}/login?token={jwt_token}")

    except httpx.TimeoutException:
        return RedirectResponse(f"{FRONTEND}/login?error=Google+server+timeout.+Please+try+again.")
    except Exception as e:
        log_msg = str(e)[:60].replace(" ", "+")
        return RedirectResponse(f"{FRONTEND}/login?error={log_msg}")
""")
            

w("src/interfaces/http/routes/ai_chat.py", '''
import json
import datetime
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

def get_base_system_prompt(memory_context: str = "") -> dict:
    today = datetime.datetime.now().strftime("%B %d, %Y")
    memory_section = f"\\n\\nUser context to personalize responses:\\n{memory_context}" if memory_context else ""
    content = f"""You are Dacexy AI, a sharp and intelligent AI assistant built into the Dacexy platform. Today is {today}.

RESPONSE STYLE — FOLLOW STRICTLY:
- Be direct. Answer the question first, then add context only if needed
- Write in plain natural prose like a knowledgeable friend
- Never use asterisks (*) for bold or bullets in your responses
- Never use excessive symbols like **text**, _text_, or ##headings
- No filler openers like "Certainly!", "Of course!", "Great question!", "Sure!", "Absolutely!"
- No closing lines like "I hope this helps!", "Feel free to ask!", "Let me know if you need more!"
- Keep responses concise — short answers for simple questions, detailed only when necessary
- Use numbered lists or plain bullet points only when the user explicitly asks for a list
- Match the user's language — if they write in Hindi, respond in Hindi naturally

FOR NEWS, SPORTS, PRICES, CURRENT EVENTS:
- Always use the most recent information from web search when available
- Today is {today} — never present information from 2022 or 2023 as current
- For sports scores, election results, stock prices — clearly state you are showing the latest available data
- If you don't have current data, say so clearly and briefly

FOR CODE AND TECHNICAL QUESTIONS:
- Give working code directly without excessive explanation unless asked
- Use proper code formatting with language labels{memory_section}"""
    return {{"role": "system", "content": content}}

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
    messages = [{{"role": m.role, "content": m.content}} for m in body.messages]
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
    memory_context = "\\n".join([f"- {m.content}" for m in memories]) if memories else ""
    system_msg = get_base_system_prompt(memory_context)
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
        record_id = str(record.id)
        session_id = str(session.id)
        async def website_stream():
            yield "data: " + json.dumps({{"type": "session_id", "session_id": session_id}}) + "\\n\\n"
            yield "data: " + json.dumps({{"type": "chunk", "content": "Building your website...\\n\\n"}}) + "\\n\\n"
            try:
                html = await generate_website(prompt, ai)
                record.html_content = html
                record.status = "completed"
                await db.commit()
                preview_url = "/api/v1/websites/" + record_id + "/preview"
                msg = "Your website is ready! Preview: " + preview_url + "\\n\\nClick Open to view it."
                yield "data: " + json.dumps({{"type": "chunk", "content": msg}}) + "\\n\\n"
            except Exception as e:
                record.status = "failed"
                yield "data: " + json.dumps({{"type": "chunk", "content": "Website generation failed: " + str(e)}}) + "\\n\\n"
            yield "data: " + json.dumps({{"type": "done"}}) + "\\n\\n"
        return StreamingResponse(website_stream(), media_type="text/event-stream")

    if body.stream:
        session_id = str(session.id)
        async def event_stream():
            full = ""
            yield "data: " + json.dumps({{"type": "session_id", "session_id": session_id}}) + "\\n\\n"
            if search:
                yield "data: " + json.dumps({{"type": "chunk", "content": "Searching the web...\\n\\n"}}) + "\\n\\n"
            try:
                async for chunk in await ai.chat(messages, model=body.model, stream=True, search=search):
                    full += chunk
                    yield "data: " + json.dumps({{"type": "chunk", "content": chunk}}) + "\\n\\n"
            except Exception as e:
                yield "data: " + json.dumps({{"type": "chunk", "content": "Something went wrong: " + str(e)}}) + "\\n\\n"
            yield "data: " + json.dumps({{"type": "done"}}) + "\\n\\n"
            session.messages = messages + [{{"role": "assistant", "content": full}}]
            try:
                await db.commit()
            except Exception:
                pass
        return StreamingResponse(event_stream(), media_type="text/event-stream")

    response = await ai.chat(messages, model=body.model, stream=False, search=search)
    session.messages = messages + [{{"role": "assistant", "content": response}}]
    await db.commit()
    return {{"content": response, "session_id": str(session.id)}}

@router.get("/sessions")
async def list_sessions(user: User = Depends(_get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ConversationSession).where(ConversationSession.org_id == user.org_id).order_by(ConversationSession.updated_at.desc()).limit(50))
    sessions = result.scalars().all()
    return {{"sessions": [{{"id": str(s.id), "title": s.title, "created_at": str(s.created_at)}} for s in sessions], "total": len(sessions)}}

@router.get("/sessions/{session_id}/messages")
async def get_messages(session_id: str, user: User = Depends(_get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ConversationSession).where(ConversationSession.id == session_id, ConversationSession.org_id == user.org_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(404, "Session not found")
    messages = session.messages or []
    clean = [m for m in messages if isinstance(m, dict) and m.get("role") != "system" and m.get("content")]
    return {{"messages": clean, "session_id": str(session.id), "title": session.title}}
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
