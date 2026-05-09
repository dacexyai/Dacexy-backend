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
    if any(x in p for x in ["portfolio","designer","freelance","artist","creative","photography","studio","agency creative"]): return "portfolio"
    if any(x in p for x in ["shop","store","ecommerce","product","sell","buy","fashion","clothing","brand","retail"]): return "ecommerce"
    if any(x in p for x in ["agency","marketing","consultant","service","firm","company","corporate","enterprise"]): return "agency"
    if any(x in p for x in ["fitness","gym","health","wellness","yoga","trainer","sport","workout"]): return "fitness"
    return "business"

def get_palette(category: str) -> dict:
    palettes = {
        "restaurant": {"primary":"#C8102E","secondary":"#FF6B35","dark":"#1A0A00","light":"#FFF8F0","accent":"#FFD700"},
        "saas": {"primary":"#6366F1","secondary":"#8B5CF6","dark":"#0F0A1E","light":"#F0F0FF","accent":"#06B6D4"},
        "portfolio": {"primary":"#0F172A","secondary":"#334155","dark":"#020617","light":"#F8FAFC","accent":"#F59E0B"},
        "ecommerce": {"primary":"#059669","secondary":"#10B981","dark":"#022C22","light":"#ECFDF5","accent":"#F97316"},
        "agency": {"primary":"#DC2626","secondary":"#EF4444","dark":"#0A0000","light":"#FFF5F5","accent":"#FBBF24"},
        "fitness": {"primary":"#EA580C","secondary":"#F97316","dark":"#0C0500","light":"#FFF7ED","accent":"#22C55E"},
        "business": {"primary":"#2563EB","secondary":"#3B82F6","dark":"#020617","light":"#EFF6FF","accent":"#F59E0B"},
    }
    return palettes.get(category, palettes["business"])

def build_template(prompt: str) -> str:
    name = extract_name(prompt)
    category = get_category(prompt)
    p = get_palette(category)
    seed = abs(hash(prompt)) % 99999
    encoded = urllib.parse.quote(prompt[:60])

    imgs = {
        "hero": f"https://image.pollinations.ai/prompt/ultra_realistic_professional_{encoded}_hero_cinematic_4k?width=1400&height=700&seed={seed}&nologo=true&model=flux",
        "about": f"https://image.pollinations.ai/prompt/professional_{encoded}_team_modern_office?width=800&height=600&seed={seed+1}&nologo=true&model=flux",
        "s1": f"https://image.pollinations.ai/prompt/{encoded}_product_showcase_elegant?width=700&height=500&seed={seed+2}&nologo=true&model=flux",
        "s2": f"https://image.pollinations.ai/prompt/{encoded}_service_professional?width=700&height=500&seed={seed+3}&nologo=true&model=flux",
        "s3": f"https://image.pollinations.ai/prompt/{encoded}_result_success?width=700&height=500&seed={seed+4}&nologo=true&model=flux",
    }

    categories_data = {
        "restaurant": {
            "tagline": f"Where Every Bite Tells a Story",
            "sub": f"Experience authentic flavors crafted with passion at {name}. Fresh ingredients, timeless recipes, unforgettable moments.",
            "cta": "Reserve Your Table",
            "cta2": "View Our Menu",
            "services_title": "Our Specialties",
            "services": [
                ("🍽️","Fine Dining","Exquisite multi-course meals crafted by award-winning chefs using the finest seasonal ingredients."),
                ("🍷","Premium Bar","Curated wine cellar and craft cocktails to complement your dining experience perfectly."),
                ("🎂","Private Events","Intimate celebrations, corporate dinners, and special occasions in our exclusive private dining rooms."),
                ("🚗","Valet & Delivery","Complimentary valet parking and premium home delivery for your convenience."),
            ],
            "stats": [("15+","Years of Excellence"),("50K+","Happy Guests"),("4.9★","Average Rating"),("200+","Menu Items")],
            "testimonials": [
                ("Arjun Mehta","Food Critic","The best dining experience in the city. Every dish is a masterpiece of flavour and presentation."),
                ("Priya Sharma","Regular Guest","We celebrate every anniversary here. The ambiance and food never disappoint — pure magic."),
                ("Rahul Singh","Corporate Client","Our team events here are always exceptional. The private dining rooms are world-class."),
            ],
        },
        "saas": {
            "tagline": f"The Platform That Powers Your Growth",
            "sub": f"{name} gives your team the AI-powered tools to move faster, work smarter, and scale without limits.",
            "cta": "Start Free Trial",
            "cta2": "Watch Demo",
            "services_title": "Core Features",
            "services": [
                ("⚡","10x Faster","Automated workflows that eliminate manual work and accelerate every process in your business."),
                ("🤖","AI-Powered","Smart automation learns from your data and optimises processes without any configuration needed."),
                ("🔒","Enterprise Security","SOC2 compliant with end-to-end encryption, SSO, and granular permission controls built in."),
                ("📊","Real-time Analytics","Beautiful dashboards with actionable insights — see what matters most, instantly."),
            ],
            "stats": [("10K+","Teams Using"),("99.9%","Uptime SLA"),("10x","Faster Results"),("4.8★","G2 Rating")],
            "testimonials": [
                ("Sarah Chen","CTO, TechFlow","We cut our operational costs by 60% in the first month. Absolutely transformative platform."),
                ("Marcus Johnson","CEO, ScaleUp","The ROI was immediate. Our team ships 3x faster and customer satisfaction is at an all-time high."),
                ("Aisha Patel","VP Engineering","Best developer experience we have ever had. The API is clean and the support is world-class."),
            ],
        },
        "portfolio": {
            "tagline": f"Crafting Digital Experiences That Matter",
            "sub": f"I design and build exceptional digital products. Every pixel, every interaction, every line of code — crafted with purpose.",
            "cta": "View My Work",
            "cta2": "Let's Collaborate",
            "services_title": "What I Do",
            "services": [
                ("🎨","UI/UX Design","Human-centred design that converts. From wireframes to pixel-perfect interfaces users love."),
                ("💻","Web Development","Clean, performant code in React, Next.js and modern frameworks. Fast, accessible, scalable."),
                ("📱","Mobile Apps","Native iOS and Android apps plus cross-platform solutions that delight users on every device."),
                ("🚀","Brand Identity","Complete visual identities — logo, typography, colour systems, and brand guidelines."),
            ],
            "stats": [("50+","Projects Delivered"),("30+","Happy Clients"),("5★","Average Rating"),("8+","Years Experience")],
            "testimonials": [
                ("David Park","Founder, Launchpad","Exceptional work. Delivered beyond our expectations and on time. Will work together again."),
                ("Emma Wilson","Marketing Director","Our conversion rate increased by 240% after the redesign. Truly world-class design talent."),
                ("Carlos Rivera","CEO, Momentum","The best investment we made this year. The new brand completely transformed our market position."),
            ],
        },
        "ecommerce": {
            "tagline": f"Premium Quality, Delivered to Your Door",
            "sub": f"Discover {name}'s carefully curated collection. Free shipping on all orders. 30-day returns. Shop with confidence.",
            "cta": "Shop Collection",
            "cta2": "View Lookbook",
            "services_title": "Why Shop With Us",
            "services": [
                ("🚚","Free Shipping","Free express delivery on all orders above ₹999. Get your order within 2-3 business days."),
                ("✅","Quality Assured","Every product passes our 47-point quality check before it reaches your doorstep."),
                ("↩️","Easy Returns","Hassle-free 30-day returns. No questions asked. Full refund guaranteed."),
                ("💳","Secure Checkout","UPI, cards, EMI, COD — all payment methods accepted with bank-grade security."),
            ],
            "stats": [("50K+","Happy Customers"),("10K+","Products"),("4.9★","Average Rating"),("99%","Satisfaction"),],
            "testimonials": [
                ("Sneha Gupta","Verified Buyer","Amazing quality! Exactly as described and delivered in 2 days. Will definitely shop again."),
                ("Vikram Nair","Premium Member","Been shopping here for 3 years. Quality is consistently excellent and service is top-notch."),
                ("Divya Krishnan","Style Blogger","My go-to store for premium finds. The curation is impeccable and prices are fair."),
            ],
        },
        "agency": {
            "tagline": f"We Build Brands That Dominate Markets",
            "sub": f"{name} is a full-service agency that transforms businesses through strategy, creative, and technology that actually works.",
            "cta": "Get a Proposal",
            "cta2": "See Our Work",
            "services_title": "Our Services",
            "services": [
                ("📈","Growth Strategy","Data-driven strategies that have helped 100+ brands achieve explosive, sustainable growth."),
                ("🎯","Performance Marketing","ROI-focused campaigns across Google, Meta, and programmatic that consistently beat benchmarks."),
                ("🌐","Digital Products","We build websites, apps, and platforms that convert visitors into loyal, paying customers."),
                ("✍️","Content & Creative","Storytelling that connects emotionally and drives action — from brand film to social content."),
            ],
            "stats": [("100+","Brands Grown"),("₹50Cr+","Revenue Generated"),("4.9★","Client Rating"),("8+","Years Experience")],
            "testimonials": [
                ("Ankit Joshi","CMO, GrowthBrand","They tripled our qualified leads in 90 days. Best agency we have ever partnered with."),
                ("Meera Kapoor","Founder, StyleCo","The rebrand completely transformed how the market perceives us. Revenue up 180% YoY."),
                ("Rajesh Patel","CEO, TechStart","From strategy to execution — they are a true growth partner. Exceptional results every time."),
            ],
        },
        "fitness": {
            "tagline": f"Transform Your Body, Elevate Your Life",
            "sub": f"Join {name} and unlock your true potential. Expert coaching, state-of-the-art facilities, and a community that pushes you further.",
            "cta": "Start Free Trial",
            "cta2": "View Programs",
            "services_title": "Our Programs",
            "services": [
                ("💪","Strength Training","Progressive overload programs designed by elite coaches to build real, lasting strength."),
                ("🏃","Cardio & HIIT","High-intensity programs that torch calories, improve endurance, and keep you energised all day."),
                ("🧘","Mind & Body","Yoga, meditation, and mobility work to balance your training and optimise recovery."),
                ("🥗","Nutrition Coaching","Personalised meal plans and nutrition coaching to fuel your transformation from the inside out."),
            ],
            "stats": [("5K+","Members"),("50+","Expert Trainers"),("98%","Success Rate"),("4.9★","Member Rating")],
            "testimonials": [
                ("Kiran Rao","Member since 2022","Lost 20kg in 6 months. The trainers here are exceptional and the community keeps you motivated."),
                ("Ananya Singh","Marathon Runner","Improved my personal best by 22 minutes. The coaching and programs here are world-class."),
                ("Dev Malhotra","Strength Athlete","Gained 12kg of muscle in a year. The programming is scientific and the results speak for themselves."),
            ],
        },
        "business": {
            "tagline": f"Excellence Delivered, Every Single Time",
            "sub": f"{name} combines deep expertise with innovative thinking to deliver results that exceed expectations and drive real business impact.",
            "cta": "Get Started Today",
            "cta2": "Learn More",
            "services_title": "What We Offer",
            "services": [
                ("⚡","Fast Delivery","We deliver exceptional results in record time — without ever compromising on quality or attention to detail."),
                ("🎯","Results Focused","Every decision we make is tied to measurable outcomes and the specific goals of your business."),
                ("🤝","True Partnership","We embed ourselves in your mission and work as a genuine extension of your team."),
                ("🛡️","Proven Reliability","100+ satisfied clients trust us with their most important projects. We never miss a deadline."),
            ],
            "stats": [("100+","Projects Done"),("50+","Happy Clients"),("4.9★","Average Rating"),("5+","Years Experience")],
            "testimonials": [
                ("Rohit Kumar","Managing Director","Exceptional quality and professionalism. They delivered exactly what they promised and more."),
                ("Nisha Agarwal","Operations Head","Reliable, skilled, and genuinely invested in our success. The best vendor relationship we have."),
                ("Amit Sharma","Founder","Working with them was a game-changer for our business. Results speak louder than words."),
            ],
        },
    }

    d = categories_data.get(category, categories_data["business"])
    tagline = d["tagline"]
    sub = d["sub"]
    cta = d["cta"]
    cta2 = d["cta2"]
    services_title = d["services_title"]
    services = d["services"]
    stats = d["stats"]
    testimonials = d["testimonials"]

    services_html = ""
    for icon, title, desc in services:
        services_html += f\'\'\'
        <div class="service-card">
            <div class="service-icon">{icon}</div>
            <h3>{title}</h3>
            <p>{desc}</p>
        </div>\'\'\'

    stats_html = ""
    for num, label in stats:
        stats_html += f\'<div class="stat-item"><div class="stat-num">{num}</div><div class="stat-label">{label}</div></div>\'

    testimonials_html = ""
    for author, role, text in testimonials:
        initials = "".join([w[0] for w in author.split()[:2]])
        testimonials_html += f\'\'\'
        <div class="testimonial-card">
            <div class="stars">★★★★★</div>
            <p class="testimonial-text">"{text}"</p>
            <div class="testimonial-author">
                <div class="author-avatar">{initials}</div>
                <div>
                    <div class="author-name">{author}</div>
                    <div class="author-role">{role}</div>
                </div>
            </div>
        </div>\'\'\'

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{name} — {tagline}</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=Playfair+Display:ital,wght@0,700;0,800;0,900;1,700&display=swap" rel="stylesheet">
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
:root{{
  --primary:{p["primary"]};
  --secondary:{p["secondary"]};
  --dark:{p["dark"]};
  --light:{p["light"]};
  --accent:{p["accent"]};
  --white:#ffffff;
  --gray:#6B7280;
  --border:rgba(0,0,0,0.08);
}}
html{{scroll-behavior:smooth}}
body{{font-family:"Inter",sans-serif;color:var(--dark);background:var(--white);overflow-x:hidden;line-height:1.6}}

/* ── NAVIGATION ── */
nav{{
  position:fixed;top:0;width:100%;z-index:1000;
  padding:0 5%;transition:all 0.4s cubic-bezier(0.4,0,0.2,1);
}}
nav.scrolled{{
  background:rgba(255,255,255,0.95);backdrop-filter:blur(20px);
  box-shadow:0 4px 40px rgba(0,0,0,0.08);border-bottom:1px solid var(--border);
}}
.nav-inner{{
  max-width:1280px;margin:0 auto;display:flex;align-items:center;
  justify-content:space-between;height:72px;
}}
.nav-logo{{
  font-family:"Playfair Display",serif;font-size:1.8rem;font-weight:900;
  color:var(--white);text-decoration:none;letter-spacing:-0.5px;
  transition:color 0.3s;
}}
nav.scrolled .nav-logo{{color:var(--primary);}}
.nav-links{{display:flex;align-items:center;gap:40px;list-style:none;}}
.nav-links a{{
  color:rgba(255,255,255,0.85);text-decoration:none;font-weight:500;
  font-size:0.9rem;transition:all 0.2s;letter-spacing:0.3px;
}}
nav.scrolled .nav-links a{{color:var(--gray);}}
.nav-links a:hover{{color:var(--white);}}
nav.scrolled .nav-links a:hover{{color:var(--primary);}}
.nav-cta{{
  background:var(--primary)!important;color:var(--white)!important;
  padding:10px 24px;border-radius:100px;font-weight:700!important;
  font-size:0.85rem!important;transition:all 0.3s!important;
  box-shadow:0 4px 20px rgba(0,0,0,0.2);
}}
.nav-cta:hover{{transform:translateY(-2px);box-shadow:0 8px 30px rgba(0,0,0,0.25)!important;}}

/* ── HERO ── */
.hero{{
  position:relative;min-height:100vh;display:flex;align-items:center;
  padding:100px 5% 80px;overflow:hidden;
  background:linear-gradient(135deg,{p["dark"]} 0%,{p["primary"]}99 60%,{p["secondary"]} 100%);
}}
.hero-bg{{
  position:absolute;inset:0;
  background:url("{imgs["hero"]}") center/cover no-repeat;
  opacity:0.15;filter:blur(2px);
}}
.hero-overlay{{
  position:absolute;inset:0;
  background:linear-gradient(135deg,{p["dark"]}F0 0%,{p["primary"]}CC 60%,{p["secondary"]}99 100%);
}}
.hero-shapes{{position:absolute;inset:0;overflow:hidden;pointer-events:none;}}
.hero-circle{{
  position:absolute;border-radius:50%;
  background:radial-gradient(circle,rgba(255,255,255,0.06) 0%,transparent 70%);
}}
.hero-circle:nth-child(1){{width:600px;height:600px;top:-200px;right:-100px;}}
.hero-circle:nth-child(2){{width:400px;height:400px;bottom:-100px;left:-50px;}}
.hero-circle:nth-child(3){{width:300px;height:300px;top:50%;right:20%;}}
.hero-inner{{
  position:relative;z-index:2;max-width:1280px;margin:0 auto;width:100%;
  display:grid;grid-template-columns:1fr 1fr;gap:80px;align-items:center;
}}
.hero-badge{{
  display:inline-flex;align-items:center;gap:8px;
  background:rgba(255,255,255,0.12);backdrop-filter:blur(10px);
  border:1px solid rgba(255,255,255,0.2);
  color:rgba(255,255,255,0.95);padding:8px 18px;
  border-radius:100px;font-size:0.78rem;font-weight:700;
  text-transform:uppercase;letter-spacing:1.5px;margin-bottom:28px;
  width:fit-content;
}}
.hero-badge::before{{content:"✦";color:var(--accent);}}
.hero-title{{
  font-family:"Playfair Display",serif;
  font-size:clamp(2.8rem,5vw,5rem);font-weight:900;
  color:var(--white);line-height:1.08;margin-bottom:24px;
  letter-spacing:-1px;
}}
.hero-title span{{
  color:var(--accent);font-style:italic;
  text-shadow:0 0 40px rgba(255,215,0,0.3);
}}
.hero-sub{{
  font-size:1.1rem;color:rgba(255,255,255,0.78);
  margin-bottom:44px;line-height:1.8;max-width:520px;font-weight:400;
}}
.hero-buttons{{display:flex;gap:16px;flex-wrap:wrap;}}
.btn-primary{{
  background:var(--accent);color:var(--dark);
  padding:16px 36px;border-radius:100px;font-weight:800;
  font-size:0.95rem;text-decoration:none;transition:all 0.3s;
  box-shadow:0 8px 30px rgba(0,0,0,0.3);letter-spacing:0.3px;
  display:inline-flex;align-items:center;gap:8px;
}}
.btn-primary:hover{{transform:translateY(-3px);box-shadow:0 16px 40px rgba(0,0,0,0.35);}}
.btn-secondary{{
  background:transparent;border:2px solid rgba(255,255,255,0.5);color:var(--white);
  padding:16px 36px;border-radius:100px;font-weight:700;font-size:0.95rem;
  text-decoration:none;transition:all 0.3s;
  display:inline-flex;align-items:center;gap:8px;
}}
.btn-secondary:hover{{background:rgba(255,255,255,0.1);border-color:rgba(255,255,255,0.8);}}
.hero-stats{{
  display:flex;gap:40px;margin-top:60px;padding-top:40px;
  border-top:1px solid rgba(255,255,255,0.15);
}}
.hero-stat-num{{font-size:2.2rem;font-weight:900;color:var(--white);line-height:1;}}
.hero-stat-label{{font-size:0.78rem;color:rgba(255,255,255,0.6);margin-top:4px;text-transform:uppercase;letter-spacing:0.5px;}}
.hero-visual{{position:relative;}}
.hero-card{{
  background:rgba(255,255,255,0.07);backdrop-filter:blur(20px);
  border:1px solid rgba(255,255,255,0.15);border-radius:28px;
  overflow:hidden;box-shadow:0 40px 80px rgba(0,0,0,0.4);
}}
.hero-card img{{width:100%;height:420px;object-fit:cover;display:block;}}
.hero-card-badge{{
  position:absolute;bottom:24px;left:24px;right:24px;
  background:rgba(255,255,255,0.12);backdrop-filter:blur(20px);
  border:1px solid rgba(255,255,255,0.2);border-radius:16px;
  padding:16px 20px;display:flex;align-items:center;gap:12px;
}}
.hero-card-badge-dot{{width:10px;height:10px;border-radius:50%;background:#22C55E;animation:pulse 2s infinite;}}
@keyframes pulse{{0%,100%{{opacity:1}}50%{{opacity:0.5}}}}
.hero-card-badge-text{{color:var(--white);font-size:0.85rem;font-weight:600;}}
.hero-floating{{
  position:absolute;top:-20px;right:-20px;
  background:var(--accent);border-radius:20px;
  padding:16px 20px;color:var(--dark);font-weight:800;
  font-size:0.85rem;box-shadow:0 10px 30px rgba(0,0,0,0.3);
}}

/* ── SECTIONS ── */
section{{padding:120px 5%;}}
.section-inner{{max-width:1280px;margin:0 auto;}}
.section-badge{{
  display:inline-flex;align-items:center;gap:6px;
  background:linear-gradient(135deg,{p["primary"]}18,{p["secondary"]}18);
  color:var(--primary);font-size:0.75rem;font-weight:800;
  padding:8px 18px;border-radius:100px;
  border:1px solid {p["primary"]}30;
  text-transform:uppercase;letter-spacing:1.5px;margin-bottom:20px;
}}
.section-title{{
  font-family:"Playfair Display",serif;
  font-size:clamp(2rem,4vw,3.5rem);font-weight:900;
  color:var(--dark);margin-bottom:20px;line-height:1.1;letter-spacing:-0.5px;
}}
.section-title em{{font-style:italic;color:var(--primary);}}
.section-sub{{color:var(--gray);font-size:1.05rem;max-width:600px;line-height:1.8;}}
.text-center{{text-align:center;}}
.text-center .section-sub{{margin:0 auto;}}

/* ── SERVICES ── */
.services-section{{background:var(--light);}}
.services-grid{{
  display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));
  gap:28px;margin-top:64px;
}}
.service-card{{
  background:var(--white);border-radius:24px;padding:40px 32px;
  border:1px solid var(--border);transition:all 0.4s cubic-bezier(0.4,0,0.2,1);
  position:relative;overflow:hidden;cursor:default;
}}
.service-card::before{{
  content:"";position:absolute;inset:0;
  background:linear-gradient(135deg,{p["primary"]}08,{p["secondary"]}08);
  opacity:0;transition:opacity 0.4s;
}}
.service-card::after{{
  content:"";position:absolute;top:0;left:0;right:0;height:3px;
  background:linear-gradient(90deg,{p["primary"]},{p["secondary"]});
  transform:scaleX(0);transform-origin:left;transition:transform 0.4s;
}}
.service-card:hover{{transform:translateY(-8px);box-shadow:0 30px 60px rgba(0,0,0,0.1);border-color:transparent;}}
.service-card:hover::before{{opacity:1;}}
.service-card:hover::after{{transform:scaleX(1);}}
.service-icon{{
  width:64px;height:64px;border-radius:18px;
  background:linear-gradient(135deg,{p["primary"]}15,{p["secondary"]}15);
  display:flex;align-items:center;justify-content:center;
  font-size:1.8rem;margin-bottom:24px;transition:transform 0.3s;
}}
.service-card:hover .service-icon{{transform:scale(1.1) rotate(5deg);}}
.service-card h3{{font-size:1.2rem;font-weight:800;margin-bottom:12px;color:var(--dark);}}
.service-card p{{color:var(--gray);line-height:1.75;font-size:0.93rem;}}

/* ── STATS ── */
.stats-section{{
  background:linear-gradient(135deg,{p["dark"]},{p["primary"]});
  position:relative;overflow:hidden;
}}
.stats-section::before{{
  content:"";position:absolute;inset:0;
  background:url("data:image/svg+xml,%3Csvg width=\'80\' height=\'80\' viewBox=\'0 0 80 80\' xmlns=\'http://www.w3.org/2000/svg\'%3E%3Cg fill=\'none\' fill-rule=\'evenodd\'%3E%3Cg fill=\'%23ffffff\' fill-opacity=\'0.03\'%3E%3Cpath d=\'M40 40L0 0h80z\'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E");
}}
.stats-grid{{
  display:grid;grid-template-columns:repeat(4,1fr);gap:0;
  position:relative;z-index:1;
}}
.stat-item{{
  text-align:center;padding:60px 32px;border-right:1px solid rgba(255,255,255,0.1);
}}
.stat-item:last-child{{border-right:none;}}
.stat-num{{
  font-family:"Playfair Display",serif;font-size:3.2rem;font-weight:900;
  color:var(--white);line-height:1;margin-bottom:12px;
}}
.stat-label{{font-size:0.85rem;color:rgba(255,255,255,0.6);font-weight:500;text-transform:uppercase;letter-spacing:0.5px;}}

/* ── ABOUT ── */
.about-section{{background:var(--white);}}
.about-grid{{display:grid;grid-template-columns:1fr 1fr;gap:100px;align-items:center;}}
.about-image-wrap{{position:relative;}}
.about-image-main{{
  width:100%;border-radius:28px;
  box-shadow:0 40px 80px rgba(0,0,0,0.15);display:block;
}}
.about-image-secondary{{
  position:absolute;bottom:-32px;right:-32px;
  width:55%;border-radius:20px;
  box-shadow:0 20px 60px rgba(0,0,0,0.2);
  border:6px solid var(--white);
}}
.about-accent{{
  position:absolute;top:-20px;left:-20px;
  width:80px;height:80px;border-radius:20px;
  background:linear-gradient(135deg,var(--primary),var(--secondary));
  display:flex;align-items:center;justify-content:center;
  font-size:2rem;box-shadow:0 10px 30px {p["primary"]}50;
}}
.about-text h2{{
  font-family:"Playfair Display",serif;font-size:2.8rem;
  font-weight:900;margin-bottom:24px;color:var(--dark);line-height:1.1;
}}
.about-text p{{color:var(--gray);line-height:1.9;margin-bottom:20px;font-size:1rem;}}
.about-points{{list-style:none;margin:32px 0;}}
.about-points li{{
  display:flex;align-items:flex-start;gap:12px;
  padding:12px 0;border-bottom:1px solid var(--border);font-size:0.95rem;color:var(--dark);
}}
.about-points li::before{{
  content:"✓";width:24px;height:24px;border-radius:50%;
  background:var(--primary);color:var(--white);
  display:flex;align-items:center;justify-content:center;
  font-size:0.7rem;font-weight:900;flex-shrink:0;margin-top:2px;
}}

/* ── GALLERY ── */
.gallery-section{{background:var(--light);}}
.gallery-grid{{
  display:grid;grid-template-columns:repeat(3,1fr);
  grid-template-rows:auto auto;gap:20px;margin-top:64px;
}}
.gallery-item{{
  border-radius:20px;overflow:hidden;position:relative;
  cursor:pointer;
}}
.gallery-item:first-child{{grid-column:span 2;}}
.gallery-item img{{
  width:100%;height:100%;min-height:280px;object-fit:cover;
  transition:transform 0.6s cubic-bezier(0.4,0,0.2,1);display:block;
}}
.gallery-item:hover img{{transform:scale(1.07);}}
.gallery-item-overlay{{
  position:absolute;inset:0;
  background:linear-gradient(to top,{p["primary"]}CC 0%,transparent 50%);
  opacity:0;transition:opacity 0.4s;
  display:flex;align-items:flex-end;padding:24px;
}}
.gallery-item:hover .gallery-item-overlay{{opacity:1;}}
.gallery-item-overlay span{{
  color:var(--white);font-weight:700;font-size:0.9rem;
  border-bottom:2px solid var(--accent);padding-bottom:4px;
}}

/* ── TESTIMONIALS ── */
.testimonials-section{{
  background:linear-gradient(135deg,{p["dark"]} 0%,#1a1a2e 100%);
}}
.testimonials-section .section-title{{color:var(--white);}}
.testimonials-section .section-sub{{color:rgba(255,255,255,0.6);}}
.testimonials-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:24px;margin-top:64px;}}
.testimonial-card{{
  background:rgba(255,255,255,0.05);
  border:1px solid rgba(255,255,255,0.1);
  border-radius:24px;padding:36px;
  transition:all 0.4s;backdrop-filter:blur(10px);
}}
.testimonial-card:hover{{
  background:rgba(255,255,255,0.08);
  transform:translateY(-6px);
  border-color:rgba(255,255,255,0.2);
}}
.stars{{color:var(--accent);font-size:1rem;letter-spacing:3px;margin-bottom:20px;}}
.testimonial-text{{
  color:rgba(255,255,255,0.85);line-height:1.8;
  font-style:italic;margin-bottom:28px;font-size:0.95rem;
}}
.testimonial-author{{display:flex;align-items:center;gap:14px;}}
.author-avatar{{
  width:48px;height:48px;border-radius:50%;
  background:linear-gradient(135deg,var(--primary),var(--secondary));
  display:flex;align-items:center;justify-content:center;
  color:var(--white);font-weight:900;font-size:0.95rem;flex-shrink:0;
}}
.author-name{{color:var(--white);font-weight:700;font-size:0.95rem;}}
.author-role{{color:rgba(255,255,255,0.5);font-size:0.8rem;margin-top:2px;}}

/* ── CTA ── */
.cta-section{{
  background:linear-gradient(135deg,var(--primary),var(--secondary));
  text-align:center;padding:120px 5%;position:relative;overflow:hidden;
}}
.cta-section::before{{
  content:"";position:absolute;inset:0;
  background:url("data:image/svg+xml,%3Csvg width=\'60\' height=\'60\' viewBox=\'0 0 60 60\' xmlns=\'http://www.w3.org/2000/svg\'%3E%3Cg fill=\'none\'%3E%3Cg fill=\'%23ffffff\' fill-opacity=\'0.05\'%3E%3Ccircle cx=\'30\' cy=\'30\' r=\'4\'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E");
}}
.cta-section h2{{
  font-family:"Playfair Display",serif;font-size:clamp(2rem,4vw,3.5rem);
  font-weight:900;color:var(--white);margin-bottom:20px;position:relative;
}}
.cta-section p{{color:rgba(255,255,255,0.85);font-size:1.1rem;margin-bottom:48px;position:relative;}}
.btn-cta{{
  display:inline-flex;align-items:center;gap:10px;
  background:var(--white);color:var(--primary);
  padding:18px 48px;border-radius:100px;font-weight:800;
  font-size:1rem;text-decoration:none;transition:all 0.3s;
  box-shadow:0 10px 40px rgba(0,0,0,0.2);
  position:relative;
}}
.btn-cta:hover{{transform:translateY(-4px);box-shadow:0 20px 50px rgba(0,0,0,0.25);}}

/* ── CONTACT ── */
.contact-section{{background:var(--white);}}
.contact-grid{{display:grid;grid-template-columns:1fr 1.4fr;gap:80px;align-items:start;}}
.contact-info h3{{
  font-family:"Playfair Display",serif;font-size:2rem;font-weight:900;
  margin-bottom:20px;color:var(--dark);
}}
.contact-info p{{color:var(--gray);line-height:1.8;margin-bottom:40px;}}
.contact-detail{{
  display:flex;align-items:center;gap:16px;
  margin-bottom:24px;padding:16px;
  background:var(--light);border-radius:16px;
  transition:all 0.3s;
}}
.contact-detail:hover{{background:linear-gradient(135deg,{p["primary"]}10,{p["secondary"]}10);}}
.contact-detail-icon{{
  width:48px;height:48px;border-radius:14px;
  background:linear-gradient(135deg,{p["primary"]},{p["secondary"]});
  display:flex;align-items:center;justify-content:center;
  font-size:1.2rem;flex-shrink:0;
}}
.contact-detail-text strong{{display:block;color:var(--dark);font-weight:700;font-size:0.9rem;}}
.contact-detail-text span{{color:var(--gray);font-size:0.85rem;}}
.contact-form-wrap{{
  background:var(--light);border-radius:28px;padding:48px;
  border:1px solid var(--border);
}}
.form-row{{display:grid;grid-template-columns:1fr 1fr;gap:16px;}}
.form-group{{margin-bottom:20px;}}
.form-group label{{
  display:block;font-weight:700;font-size:0.8rem;
  text-transform:uppercase;letter-spacing:0.5px;
  color:var(--dark);margin-bottom:8px;
}}
.form-group input,.form-group textarea,.form-group select{{
  width:100%;background:var(--white);border:1.5px solid var(--border);
  border-radius:14px;padding:14px 18px;color:var(--dark);
  font-size:0.95rem;outline:none;font-family:"Inter",sans-serif;
  transition:all 0.2s;
}}
.form-group input:focus,.form-group textarea:focus{{
  border-color:var(--primary);
  box-shadow:0 0 0 4px {p["primary"]}18;
}}
.form-group textarea{{height:140px;resize:vertical;}}
.btn-submit{{
  width:100%;background:linear-gradient(135deg,{p["primary"]},{p["secondary"]});
  color:var(--white);padding:16px;border-radius:14px;font-weight:800;
  font-size:1rem;border:none;cursor:pointer;transition:all 0.3s;
  font-family:"Inter",sans-serif;letter-spacing:0.3px;
}}
.btn-submit:hover{{transform:translateY(-2px);box-shadow:0 10px 30px {p["primary"]}50;}}

/* ── FOOTER ── */
footer{{
  background:{p["dark"]};color:rgba(255,255,255,0.5);
  padding:80px 5% 32px;
}}
.footer-inner{{max-width:1280px;margin:0 auto;}}
.footer-top{{
  display:grid;grid-template-columns:2fr 1fr 1fr 1fr;
  gap:60px;margin-bottom:60px;
  padding-bottom:60px;border-bottom:1px solid rgba(255,255,255,0.08);
}}
.footer-brand .footer-logo{{
  font-family:"Playfair Display",serif;font-size:1.8rem;
  font-weight:900;color:var(--white);display:block;margin-bottom:16px;
  letter-spacing:-0.5px;
}}
.footer-brand p{{font-size:0.9rem;line-height:1.8;max-width:280px;}}
.footer-col h4{{
  color:var(--white);font-weight:800;margin-bottom:20px;
  font-size:0.85rem;text-transform:uppercase;letter-spacing:1px;
}}
.footer-col ul{{list-style:none;}}
.footer-col ul li{{margin-bottom:12px;}}
.footer-col ul li a{{
  color:rgba(255,255,255,0.45);text-decoration:none;
  font-size:0.9rem;transition:color 0.2s;
}}
.footer-col ul li a:hover{{color:var(--primary);}}
.footer-bottom{{
  display:flex;justify-content:space-between;align-items:center;
  flex-wrap:wrap;gap:16px;
}}
.footer-bottom p{{font-size:0.85rem;}}
.footer-socials{{display:flex;gap:12px;}}
.footer-social{{
  width:36px;height:36px;border-radius:10px;
  background:rgba(255,255,255,0.06);border:1px solid rgba(255,255,255,0.1);
  display:flex;align-items:center;justify-content:center;
  color:rgba(255,255,255,0.5);text-decoration:none;font-size:0.85rem;
  transition:all 0.2s;
}}
.footer-social:hover{{background:var(--primary);color:var(--white);border-color:var(--primary);}}

/* ── ANIMATIONS ── */
.reveal{{opacity:0;transform:translateY(40px);transition:all 0.7s cubic-bezier(0.4,0,0.2,1);}}
.reveal.visible{{opacity:1;transform:translateY(0);}}
.reveal-left{{opacity:0;transform:translateX(-40px);transition:all 0.7s cubic-bezier(0.4,0,0.2,1);}}
.reveal-left.visible{{opacity:1;transform:translateX(0);}}
.reveal-right{{opacity:0;transform:translateX(40px);transition:all 0.7s cubic-bezier(0.4,0,0.2,1);}}
.reveal-right.visible{{opacity:1;transform:translateX(0);}}

/* ── RESPONSIVE ── */
@media(max-width:1024px){{
  .hero-inner,.about-grid,.contact-grid{{grid-template-columns:1fr;}}
  .hero-inner{{gap:48px;}}
  .footer-top{{grid-template-columns:1fr 1fr;gap:40px;}}
  .about-image-secondary{{display:none;}}
}}
@media(max-width:768px){{
  section{{padding:80px 5%;}}
  .stats-grid{{grid-template-columns:repeat(2,1fr);}}
  .stat-item{{border-right:none;border-bottom:1px solid rgba(255,255,255,0.1);}}
  .testimonials-grid{{grid-template-columns:1fr;}}
  .gallery-grid{{grid-template-columns:1fr;}}
  .gallery-item:first-child{{grid-column:span 1;}}
  .footer-top{{grid-template-columns:1fr;}}
  .nav-links{{display:none;}}
  .hero-stats{{gap:24px;}}
  .form-row{{grid-template-columns:1fr;}}
}}
</style>
</head>
<body>

<!-- NAVIGATION -->
<nav id="navbar">
  <div class="nav-inner">
    <a href="#" class="nav-logo">{name}</a>
    <ul class="nav-links">
      <li><a href="#services">Services</a></li>
      <li><a href="#about">About</a></li>
      <li><a href="#gallery">Work</a></li>
      <li><a href="#testimonials">Reviews</a></li>
      <li><a href="#contact" class="nav-cta">{cta}</a></li>
    </ul>
  </div>
</nav>

<!-- HERO -->
<section class="hero">
  <div class="hero-bg"></div>
  <div class="hero-overlay"></div>
  <div class="hero-shapes">
    <div class="hero-circle"></div>
    <div class="hero-circle"></div>
    <div class="hero-circle"></div>
  </div>
  <div class="hero-inner">
    <div class="hero-content reveal-left">
      <div class="hero-badge">{name} · {category.title()}</div>
      <h1 class="hero-title">
        {name}<br>
        <span>{tagline}</span>
      </h1>
      <p class="hero-sub">{sub}</p>
      <div class="hero-buttons">
        <a href="#contact" class="btn-primary">{cta} →</a>
        <a href="#services" class="btn-secondary">{cta2}</a>
      </div>
      <div class="hero-stats">
        {stats_html}
      </div>
    </div>
    <div class="hero-visual reveal-right">
      <div class="hero-floating">⭐ Top Rated 2026</div>
      <div class="hero-card">
        <img src="{imgs["hero"]}" alt="{name}" loading="lazy">
        <div class="hero-card-badge">
          <div class="hero-card-badge-dot"></div>
          <span class="hero-card-badge-text">Live & Serving Clients Now</span>
        </div>
      </div>
    </div>
  </div>
</section>

<!-- SERVICES -->
<section class="services-section" id="services">
  <div class="section-inner">
    <div class="text-center reveal">
      <span class="section-badge">✦ {services_title}</span>
      <h2 class="section-title">Everything You Need,<br><em>Delivered Perfectly</em></h2>
      <p class="section-sub">We bring together expertise, technology, and passion to deliver outcomes that exceed expectations every time.</p>
    </div>
    <div class="services-grid">
      {services_html}
    </div>
  </div>
</section>

<!-- STATS -->
<section class="stats-section">
  <div class="section-inner">
    <div class="stats-grid">
      {stats_html}
    </div>
  </div>
</section>

<!-- ABOUT -->
<section class="about-section" id="about">
  <div class="section-inner">
    <div class="about-grid">
      <div class="about-image-wrap reveal-left">
        <div class="about-accent">✦</div>
        <img src="{imgs["about"]}" alt="About {name}" class="about-image-main" loading="lazy">
        <img src="{imgs["s1"]}" alt="{name} work" class="about-image-secondary" loading="lazy">
      </div>
      <div class="about-text reveal-right">
        <span class="section-badge">✦ Our Story</span>
        <h2>Why {name} Is the Best Choice for You</h2>
        <p>We started with a singular obsession: delivering excellence that actually moves the needle for our clients. Not just pretty outputs, but real, measurable impact that transforms businesses and lives.</p>
        <p>Every project we take on is treated as if it were our own. We bring the same energy, rigour, and creative fire to a small startup as we do to a Fortune 500 company.</p>
        <ul class="about-points">
          <li>Proven track record with 100+ successful projects</li>
          <li>Team of world-class experts with decades of combined experience</li>
          <li>Results-obsessed — we measure everything that matters</li>
          <li>Transparent, honest communication throughout every project</li>
          <li>Post-delivery support and genuine long-term partnership</li>
        </ul>
        <a href="#contact" class="btn-primary" style="display:inline-flex;margin-top:8px;">{cta} →</a>
      </div>
    </div>
  </div>
</section>

<!-- GALLERY -->
<section class="gallery-section" id="gallery">
  <div class="section-inner">
    <div class="text-center reveal">
      <span class="section-badge">✦ Our Work</span>
      <h2 class="section-title">Results That<br><em>Speak for Themselves</em></h2>
      <p class="section-sub">A glimpse into the work, impact, and craft that defines everything we do at {name}.</p>
    </div>
    <div class="gallery-grid reveal">
      <div class="gallery-item">
        <img src="{imgs["hero"]}" alt="Work 1" loading="lazy">
        <div class="gallery-item-overlay"><span>View Project →</span></div>
      </div>
      <div class="gallery-item">
        <img src="{imgs["s2"]}" alt="Work 2" loading="lazy">
        <div class="gallery-item-overlay"><span>View Project →</span></div>
      </div>
      <div class="gallery-item">
        <img src="{imgs["s1"]}" alt="Work 3" loading="lazy">
        <div class="gallery-item-overlay"><span>View Project →</span></div>
      </div>
      <div class="gallery-item">
        <img src="{imgs["s3"]}" alt="Work 4" loading="lazy">
        <div class="gallery-item-overlay"><span>View Project →</span></div>
      </div>
    </div>
  </div>
</section>

<!-- TESTIMONIALS -->
<section class="testimonials-section" id="testimonials">
  <div class="section-inner">
    <div class="text-center reveal">
      <span class="section-badge" style="background:rgba(255,255,255,0.1);color:rgba(255,255,255,0.9);border-color:rgba(255,255,255,0.2);">✦ Client Love</span>
      <h2 class="section-title">Trusted by the<br>Best in the Business</h2>
      <p class="section-sub" style="color:rgba(255,255,255,0.6);">Real words from real clients who have experienced the {name} difference.</p>
    </div>
    <div class="testimonials-grid">
      {testimonials_html}
    </div>
  </div>
</section>

<!-- CTA BANNER -->
<section class="cta-section">
  <div class="section-inner">
    <span class="section-badge" style="background:rgba(255,255,255,0.15);color:rgba(255,255,255,0.95);border-color:rgba(255,255,255,0.3);">✦ Get Started Today</span>
    <h2>Ready to Work With<br>the Best?</h2>
    <p>Join hundreds of clients who trust {name} to deliver extraordinary results. Your success story starts here.</p>
    <a href="#contact" class="btn-cta">{cta} — It\'s Free to Start →</a>
  </div>
</section>

<!-- CONTACT -->
<section class="contact-section" id="contact">
  <div class="section-inner">
    <div class="contact-grid">
      <div>
        <span class="section-badge">✦ Contact Us</span>
        <div class="contact-info">
          <h3>Let\'s Create Something Extraordinary Together</h3>
          <p>Whether you have a clear vision or just a spark of an idea — we would love to hear from you. Let\'s start a conversation.</p>
        </div>
        <div class="contact-detail">
          <div class="contact-detail-icon">📧</div>
          <div class="contact-detail-text">
            <strong>Email Us</strong>
            <span>hello@{name.lower().replace(" ","")}.com</span>
          </div>
        </div>
        <div class="contact-detail">
          <div class="contact-detail-icon">📞</div>
          <div class="contact-detail-text">
            <strong>Call Us</strong>
            <span>+91 98765 43210</span>
          </div>
        </div>
        <div class="contact-detail">
          <div class="contact-detail-icon">📍</div>
          <div class="contact-detail-text">
            <strong>Find Us</strong>
            <span>Mumbai, Maharashtra, India</span>
          </div>
        </div>
        <div class="contact-detail">
          <div class="contact-detail-icon">⏰</div>
          <div class="contact-detail-text">
            <strong>Working Hours</strong>
            <span>Mon–Sat: 9 AM – 8 PM IST</span>
          </div>
        </div>
      </div>
      <div class="contact-form-wrap reveal-right">
        <div class="form-row">
          <div class="form-group"><label>Full Name *</label><input type="text" placeholder="Your name"></div>
          <div class="form-group"><label>Email *</label><input type="email" placeholder="your@email.com"></div>
        </div>
        <div class="form-row">
          <div class="form-group"><label>Phone</label><input type="tel" placeholder="+91 98765 43210"></div>
          <div class="form-group"><label>Subject</label>
            <select><option>General Inquiry</option><option>Pricing</option><option>Partnership</option><option>Support</option><option>Other</option></select>
          </div>
        </div>
        <div class="form-group"><label>Your Message *</label><textarea placeholder="Tell us about your project, goals, or any questions you have..."></textarea></div>
        <button class="btn-submit" onclick="this.textContent=\'✓ Message Sent! We will reply within 24h\';this.style.background=\'#22C55E\';setTimeout(()=>{{this.textContent=\'Send Message\';this.style.background=\'\'}},4000)">Send Message →</button>
      </div>
    </div>
  </div>
</section>

<!-- FOOTER -->
<footer>
  <div class="footer-inner">
    <div class="footer-top">
      <div class="footer-brand">
        <span class="footer-logo">{name}</span>
        <p>We exist to make our clients wildly successful. Every project. Every time. No exceptions.</p>
      </div>
      <div class="footer-col">
        <h4>Company</h4>
        <ul>
          <li><a href="#about">About Us</a></li>
          <li><a href="#services">Services</a></li>
          <li><a href="#gallery">Portfolio</a></li>
          <li><a href="#contact">Contact</a></li>
        </ul>
      </div>
      <div class="footer-col">
        <h4>Services</h4>
        <ul>
          <li><a href="#">Consulting</a></li>
          <li><a href="#">Development</a></li>
          <li><a href="#">Design</a></li>
          <li><a href="#">Marketing</a></li>
        </ul>
      </div>
      <div class="footer-col">
        <h4>Connect</h4>
        <ul>
          <li><a href="#">Twitter / X</a></li>
          <li><a href="#">LinkedIn</a></li>
          <li><a href="#">Instagram</a></li>
          <li><a href="#">YouTube</a></li>
        </ul>
      </div>
    </div>
    <div class="footer-bottom">
      <p>© 2026 {name}. All rights reserved. Built with Dacexy AI.</p>
      <div class="footer-socials">
        <a href="#" class="footer-social">𝕏</a>
        <a href="#" class="footer-social">in</a>
        <a href="#" class="footer-social">ig</a>
        <a href="#" class="footer-social">yt</a>
      </div>
      <p><a href="#" style="color:rgba(255,255,255,0.3);text-decoration:none;">Privacy</a> · <a href="#" style="color:rgba(255,255,255,0.3);text-decoration:none;">Terms</a></p>
    </div>
  </div>
</footer>

<script>
// Navbar scroll
const nav=document.getElementById("navbar");
window.addEventListener("scroll",()=>nav.classList.toggle("scrolled",window.scrollY>60));

// Smooth scroll
document.querySelectorAll("a[href^=\'#\']").forEach(a=>{{
  a.addEventListener("click",e=>{{
    e.preventDefault();
    const t=document.querySelector(a.getAttribute("href"));
    if(t) t.scrollIntoView({{behavior:"smooth",block:"start"}});
  }});
}});

// Scroll reveal
const observer=new IntersectionObserver(entries=>{{
  entries.forEach(e=>{{
    if(e.isIntersecting){{e.target.classList.add("visible");observer.unobserve(e.target);}}
  }});
}},{{threshold:0.12,rootMargin:"0px 0px -60px 0px"}});
document.querySelectorAll(".reveal,.reveal-left,.reveal-right").forEach(el=>observer.observe(el));

// Stagger service cards
document.querySelectorAll(".service-card").forEach((card,i)=>{{
  card.style.transitionDelay=i*0.08+"s";
  observer.observe(card);
  card.classList.add("reveal");
}});
</script>
</body>
</html>"""

async def generate_website(prompt: str, ai: DeepSeekProvider) -> str:
    try:
        return build_template(prompt)
    except Exception as e:
        log.error(f"Website generation failed: {e}")
        return build_template("Business")
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
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is disabled")
    access = create_access_token(str(user.id), {"org_id": str(user.org_id), "role": user.role})
    refresh = create_refresh_token()
    db.add(RefreshToken(user_id=user.id, token_hash=hash_password(refresh), expires_at=datetime.utcnow() + timedelta(days=30)))
    await db.commit()
    return TokenResponse(access_token=access, refresh_token=refresh)

@router.post("/register", response_model=TokenResponse)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db), email_svc: EmailService = Depends(get_email)):
    existing = await db.execute(select(User).where(User.email == body.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="This email is already registered. Please sign in instead.")
    org_name = body.org_name or (body.full_name.split()[0] + "s Workspace")
    org = Organization(name=org_name, slug=_make_slug(org_name))
    db.add(org)
    await db.flush()
    verify_token = secrets.token_urlsafe(32)
    user = User(org_id=org.id, email=body.email, full_name=body.full_name,
        hashed_password=hash_password(body.password), role="owner",
        is_verified=True, metadata_={"verify_token": verify_token})
    db.add(user)
    await db.flush()
    try: email_svc.send_verification_email(body.email, verify_token)
    except: pass
    access = create_access_token(str(user.id), {"org_id": str(org.id), "role": "owner"})
    refresh = create_refresh_token()
    db.add(RefreshToken(user_id=user.id, token_hash=hash_password(refresh), expires_at=datetime.utcnow() + timedelta(days=30)))
    await db.commit()
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

@router.get("/google/login")
async def google_login():
    from fastapi.responses import RedirectResponse
    import urllib.parse
    client_id = settings.GOOGLE_CLIENT_ID
    if not client_id:
        from fastapi.responses import RedirectResponse
        return RedirectResponse("https://dacexy.vercel.app/login?error=Google+login+not+configured")
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
async def google_callback(code: str = None, error: str = None, db: AsyncSession = Depends(get_db)):
    from fastapi.responses import RedirectResponse
    import httpx, re, secrets as sec
    FRONTEND = "https://dacexy.vercel.app"
    BACKEND_REDIRECT = "https://dacexy-backend-v7ku.onrender.com/api/v1/auth/google/callback"
    if error:
        return RedirectResponse(FRONTEND + "/login?error=" + str(error))
    if not code:
        return RedirectResponse(FRONTEND + "/login?error=no_code")
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            token_res = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "code": code,
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "redirect_uri": BACKEND_REDIRECT,
                    "grant_type": "authorization_code"
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            token_data = token_res.json()
            if "error" in token_data:
                err_msg = str(token_data.get("error_description", token_data.get("error", "unknown")))
                return RedirectResponse(FRONTEND + "/login?error=" + err_msg.replace(" ", "+"))
            google_token = token_data.get("access_token", "")
            if not google_token:
                return RedirectResponse(FRONTEND + "/login?error=no_access_token")
            user_res = await client.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": "Bearer " + google_token}
            )
            info = user_res.json()
        email = info.get("email", "")
        full_name = info.get("name", "")
        if not email:
            return RedirectResponse(FRONTEND + "/login?error=no_email_from_google")
        if not full_name:
            full_name = email.split("@")[0]
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if not user:
            org_name = full_name.split()[0] + "s Workspace"
            slug = re.sub(r"[^a-z0-9]+", "-", org_name.lower()).strip("-") + "-" + sec.token_hex(4)
            org = Organization(name=org_name, slug=slug)
            db.add(org)
            await db.flush()
            user = User(
                org_id=org.id,
                email=email,
                full_name=full_name,
                hashed_password=hash_password(sec.token_urlsafe(32)),
                role="owner",
                is_verified=True,
                metadata_={"google": True}
            )
            db.add(user)
            await db.flush()
        await db.commit()
        jwt_token = create_access_token(str(user.id), {"org_id": str(user.org_id), "role": user.role})
        return RedirectResponse(FRONTEND + "/login?token=" + jwt_token)
    except Exception as e:
        err = str(e)[:80].replace(" ", "+")
        return RedirectResponse(FRONTEND + "/login?error=" + err)
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

@app.get("/health")
async def health():
    return {"status": "ok", "version": settings.APP_VERSION, "environment": settings.ENVIRONMENT}

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
