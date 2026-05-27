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

log = logging.getLogger("website")

def extract_name(prompt):
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
    words = [x for x in re.sub(r'[^a-zA-Z0-9 ]', '', p).split()
             if len(x) > 2 and x.lower() not in skip]
    return words[0].title() if words else "Nexus"

def extract_user_data(prompt):
    data = {
        "phone": None,
        "email": None,
        "address": None,
        "whatsapp": None,
        "instagram": None,
        "facebook": None,
        "twitter": None,
        "linkedin": None,
        "youtube": None,
        "opening_hours": None,
        "tagline_custom": None,
        "about_text": None
    }

    p = prompt

    pm = re.search(
        r'(?:phone|mobile|call|contact|tel|ph)[:\s#]*([+\d][\d\s\-().+]{7,15})',
        p,
        re.IGNORECASE
    )

    if not pm:
        pm = re.search(r'(?<![\w])([+]?[0-9]{10,13})(?![\w])', p)

    if pm:
        data["phone"] = pm.group(1).strip()
        data["whatsapp"] = data["phone"]

    em = re.search(r'[\w.+-]+@[\w-]+\.[\w.]+', p)

    if em:
        data["email"] = em.group(0)

    am = re.search(
    r'(?:address|location|located at|find us at|visit us at)[:\s]+([^,\n]+)',
    p,
    re.IGNORECASE
)

if am:
    data["address"] = am.group(1).strip()

    ig = re.search(
        r'(?:instagram|ig|insta)[:\s@/]*([\w.]+)',
        p,
        re.IGNORECASE
    )

    if ig:
        data["instagram"] = ig.group(1).strip()

    fb = re.search(
        r'(?:facebook|fb)[:\s@/]*([\w.]+)',
        p,
        re.IGNORECASE
    )

    if fb:
        data["facebook"] = fb.group(1).strip()

    tw = re.search(
        r'(?:twitter|x\.com)[:\s@/]*([\w.]+)',
        p,
        re.IGNORECASE
    )

    if tw:
        data["twitter"] = tw.group(1).strip()

    li = re.search(
        r'(?:linkedin)[:\s@/]*([\w.-]+)',
        p,
        re.IGNORECASE
    )

    if li:
        data["linkedin"] = li.group(1).strip()

    hm = re.search(r'(?:open|hours|timing)[:\s]+([^.]{5,60})', p, re.IGNORECASE)

    if hm:
        data["opening_hours"] = hm.group(1).strip()

    wa = re.search(
        r'(?:whatsapp)[:\s#]*([+\d][\d\s\-+]{7,15})',
        p,
        re.IGNORECASE
    )

    if wa:
        data["whatsapp"] = wa.group(1).strip()

    tg = re.search(r'(?:tagline|slogan|headline)[:\s"]+([^"\n]{5,80})', p, re.IGNORECASE)

    if tg:
        data["tagline_custom"] = tg.group(1).strip()

    ab = re.search(
        r'(?:about us|about|description)[:\s]+([^.\n]{20,300})',
        p,
        re.IGNORECASE
    )

    if ab:
        data["about_text"] = ab.group(1).strip()

    return data

def needs_ai_generation(prompt):
    p = prompt.lower()
    ai_signals = ["custom","unique","special","exactly like","similar to","inspired by",
        "unusual","one of a kind","creative","artistic","complex","advanced",
        "multiple pages","dashboard","web app","tool","calculator","interactive",
        "animation heavy","3d effect","parallax heavy","video background",
        "ecommerce with cart","booking system","membership","login","payment gateway",
        "database","dynamic","cms","blog with categories","search functionality",
        "filter products","sort by","api integration","map with pins","chat system","realtime"]
    simple_signals = ["restaurant","cafe","gym","salon","doctor","lawyer","hotel","shop","store",
        "portfolio","agency","startup","school","hospital","ngo","travel","food",
        "photography","music","dental","cleaning","solar","car dealer","construction",
        "fitness","yoga","pet","bakery","coffee","florist","catering","dance"]
    has_ai = any(s in p for s in ai_signals)
    has_simple = any(s in p for s in simple_signals)
    if has_ai and not has_simple:
        return True
    if has_ai and len(p) > 200:
        return True
    return False

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
    "startup":       ["startup","mvp","seed stage","series a","venture","founder","product launch","early stage","tech startup","fintech startup"],
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
    "florist":       ["florist","flower shop","flower delivery","floral design","wedding flowers","bouquet","floral arrangement","plant nursery"],
    "catering":      ["catering","caterer","food catering","wedding catering","corporate catering","event catering","buffet","canteen"],
    "dance":         ["dance academy","dance studio","dance school","ballet","hip hop dance","classical dance","dance teacher","dance classes"],
    "coaching":      ["life coach","business coach","executive coach","career coach","mindset coach","leadership coaching","coaching program"],
    "insurance":     ["insurance","life insurance","health insurance","car insurance","home insurance","insurance broker","insurance agent"],
    "sports":        ["sports","sports club","sports academy","cricket","football","basketball","tennis","swimming","athletics","sports equipment"],
    "jewelry":       ["jewelry","jeweler","gold jewelry","diamond jewelry","custom jewelry","engagement ring","wedding jewelry","silver jewelry"],
    "furniture":     ["furniture","furniture store","custom furniture","wood furniture","modular furniture","office furniture","sofa","wardrobe"],
    "electronics":   ["electronics store","gadgets","mobile phone shop","laptop store","electronics repair","consumer electronics","home appliances"],
    "laundry":       ["laundry","dry cleaning","laundry service","wash and fold","ironing service","garment care","laundromat"],
    "plumber":       ["plumber","plumbing","plumbing services","pipe fitting","bathroom fitting","water tank","drainage","sanitation"],
    "electrician":   ["electrician","electrical services","wiring","electrical contractor","power backup","generator","home automation"],
    "tutor":         ["tutor","tutoring","home tuition","online tutor","math tutor","science tutor","test prep","jee","neet","upsc"],
    "dietitian":     ["dietitian","nutritionist","diet plan","weight loss","nutrition counseling","meal planning","sports nutrition","diabetic diet"],
    "car_rental":    ["car rental","self drive","vehicle rental","cab service","taxi","chauffeur","limousine","bus rental","outstation cab"],
    "coworking":     ["coworking","shared workspace","hot desk","serviced office","business center","virtual office","meeting room"],
    "tattoo":        ["tattoo studio","tattoo artist","body piercing","tattoo parlor","custom tattoo","henna","body art"],
    "nightclub":     ["nightclub","bar","lounge","pub","rooftop bar","cocktail bar","sports bar","live music venue","jazz club"],
    "church":        ["church","temple","mosque","gurdwara","religious organization","faith community","ministry","spiritual center"],
    "book":          ["bookstore","library","book club","publishing","author website","book review","literary","writing coaching","poetry"],
    "podcast":       ["podcast","podcaster","podcast studio","podcast network","audio content","podcast hosting","radio show"],
    "influencer":    ["influencer","content creator","youtuber","instagrammer","social media","personal brand","creator economy"],
    "recruitment":   ["recruitment","job portal","career","employment","job board","talent platform","hiring platform","job search"],
    "architecture":  ["architect","architecture firm","architectural design","urban planning","landscape architecture","structural engineering"],
    "charity":       ["charity","donation","fundraising","social service","community service","homeless shelter","food bank","orphanage"],
    "pharma":        ["pharmaceutical","pharma company","drug manufacturer","medicine","clinical research","biotech","life sciences"],
    "senior":        ["senior care","elderly care","retirement home","assisted living","nursing home","senior services","elder care"],
    "mortgage":      ["mortgage","home loan","property loan","loan broker","loan advisor","refinancing","home financing"],
    "business":      ["company","business","service","professional","firm","enterprise","solutions","services","management"],
}

def get_category(prompt):
    p = prompt.lower()
    noise = ["make","build","create","generate","design","need","want","please","just",
             "website","site","page","landing","web app","for","me","a","an","the","i",
             "can","you","give","good","great","best","professional","beautiful","modern",
             "awesome","nice","add","include","put","use","have","with","mobile","number",
             "phone","email","address","contact","social","media","map","gallery",
             "images","photos","logo","color","colour","theme","dark","light"]
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
]

def get_design(prompt):
    idx = abs(hash(prompt + "final_v1")) % len(ALL_DESIGNS)
    return ALL_DESIGNS[idx]

CONTENT_DB = {
    "restaurant":   {"tagline":"Where Every Bite Tells a Story","sub":"Authentic flavours crafted with passion. Fresh ingredients, timeless recipes, unforgettable dining moments.","cta1":"Reserve a Table","cta2":"View Menu","sv_title":"Our Specialties","sv":[("🍽️","Fine Dining","Exquisite multi-course meals by award-winning chefs."),("🍷","Premium Bar","Curated wines, craft cocktails, and rare spirits."),("🎂","Private Events","Exclusive rooms for celebrations and corporate dinners."),("🚗","Home Delivery","Restaurant quality food delivered fast to your door.")],"stats":[("15+","Years"),("50K+","Guests"),("4.9★","Rating"),("200+","Dishes")],"testi":[("Arjun M.","Food Critic","The finest dining in the city. Every dish is a masterpiece."),("Priya S.","Regular Guest","We celebrate every anniversary here. Simply magical."),("Rahul K.","Corporate Host","World-class private dining. Clients always impressed.")],"af":[("🏆","Award-Winning","Top culinary awards 10 consecutive years."),("🌿","Farm to Table","Only freshest locally sourced ingredients."),("🎶","Perfect Ambiance","Atmosphere as memorable as the food.")]},
    "saas":         {"tagline":"Ship Faster. Scale Without Limits.","sub":"AI-powered platform automating your entire workflow. Built for teams that move fast and win.","cta1":"Start Free Trial","cta2":"Watch Demo","sv_title":"Platform Features","sv":[("⚡","Automation","Eliminate repetitive tasks with intelligent workflows."),("📊","Analytics","Real-time dashboards with actionable insights."),("🔗","200+ Integrations","Connect every tool your team already uses."),("🛡️","Enterprise Security","SOC2, SSO, SAML, audit logs built in.")],"stats":[("10K+","Teams"),("99.9%","Uptime"),("10x","ROI"),("4.8★","G2")],"testi":[("Sarah C.","CTO","Cut costs 60% in month one. Transformative."),("Marcus J.","CEO","Team ships 3x faster. ROI was immediate."),("Aisha P.","VP Eng","Best developer experience ever. World-class.")],"af":[("⚡","Sub-100ms","Blazing fast response times users notice."),("🔒","SOC2","Enterprise security from day one."),("🤖","AI-Native","Every feature powered by automation.")]},
    "car":          {"tagline":"Drive Your Dream Car Today","sub":"Premium vehicles, transparent pricing, buying experience that respects your time and budget.","cta1":"Browse Inventory","cta2":"Book Test Drive","sv_title":"Our Services","sv":[("🚗","New Cars","Latest models from top manufacturers at best prices."),("✅","Certified Used","Pre-owned vehicles inspected and warrantied."),("💳","Easy Finance","Loans approved in 24 hours from 7.9% APR."),("🔧","Service Centre","Manufacturer-trained technicians all brands.")],"stats":[("2K+","Cars Sold"),("500+","Reviews"),("15+","Brands"),("24hr","Approval")],"testi":[("Vikram P.","Business Owner","Dream SUV at unbelievable price. Zero pressure."),("Sunita R.","Doctor","Financing approved in hours. Drove home same day."),("Amit K.","Entrepreneur","Third car here. Never going anywhere else.")],"af":[("🏅","150-Point Check","Every used vehicle certified inspected."),("💰","Price Match","Match any verified competitor price."),("🔧","Free Service","Complimentary checks life of vehicle.")]},
    "portfolio":    {"tagline":"Design That Moves People","sub":"Digital products that convert. Every pixel deliberate. Every interaction purposeful and precise.","cta1":"View My Work","cta2":"Hire Me","sv_title":"What I Do","sv":[("🎨","UI/UX Design","Research-driven interfaces users love and convert."),("💻","Development","React and Next.js — fast, accessible, beautiful."),("📱","Mobile Apps","iOS and Android experiences that delight users."),("🚀","Brand Identity","Logos and systems that stand the test of time.")],"stats":[("50+","Projects"),("30+","Clients"),("5★","Rating"),("8+","Years")],"testi":[("David P.","Founder","Delivered beyond expectations on time under budget."),("Emma W.","Director","Conversion up 240% after redesign. Extraordinary."),("Carlos R.","CEO","Best investment this year. Changed market position.")],"af":[("🎯","Data-Driven","Every decision backed by research and data."),("⚡","Fast Delivery","Production-ready designs in days not weeks."),("🤝","Collaborative","Extension of your team not a vendor.")]},
    "ecommerce":    {"tagline":"Premium Quality, Delivered Fast","sub":"Curated collections you will love. Free shipping. 30-day returns. Shop with confidence.","cta1":"Shop Now","cta2":"View Lookbook","sv_title":"Why Shop With Us","sv":[("🚚","Free Shipping","Express delivery on every order always."),("✅","Quality Assured","47-point inspection on every product."),("↩️","Easy Returns","30-day returns full refund guaranteed."),("💳","Secure Checkout","UPI, cards, EMI, COD accepted.")],"stats":[("50K+","Customers"),("10K+","Products"),("4.9★","Rating"),("99%","Satisfaction")],"testi":[("Sneha G.","Buyer","Incredible quality. Delivered in 2 days."),("Vikram N.","Member","Shopping here 3 years. Always excellent."),("Divya K.","Blogger","Go-to for premium finds. Impeccable curation.")],"af":[("🚚","Express Delivery","Free all orders no minimum spend."),("↩️","30-Day Returns","No questions. Full refund guaranteed."),("✅","Quality Certified","47-point inspection every product.")]},
    "agency":       {"tagline":"We Build Brands That Dominate","sub":"Full-service growth agency turning businesses into category leaders through strategy, creative, technology.","cta1":"Get a Proposal","cta2":"See Case Studies","sv_title":"Our Services","sv":[("📈","Growth Strategy","Data-driven plans for explosive sustainable growth."),("🎯","Performance Marketing","Campaigns that beat every benchmark."),("🌐","Digital Products","Websites and apps engineered to convert."),("✍️","Brand and Creative","Stories that connect and drive action.")],"stats":[("100+","Brands"),("₹50Cr+","Revenue"),("4.9★","Rating"),("8+","Years")],"testi":[("Ankit J.","CMO","Tripled leads in 90 days. Best agency ever."),("Meera K.","Founder","Rebrand drove 180% revenue growth."),("Rajesh P.","CEO","True growth partners. Exceptional results.")],"af":[("📊","Data-Driven","Every strategy backed by rigorous research."),("⚡","Agile","Results in weeks not quarters."),("🎯","ROI-Obsessed","Every spend tied to measurable outcomes.")]},
    "fitness":      {"tagline":"Transform Your Body. Own Your Life.","sub":"Expert coaching, elite facilities, community that refuses to let you quit. Start today.","cta1":"Start Free Trial","cta2":"View Programs","sv_title":"Our Programs","sv":[("💪","Strength Training","Elite programming to build real lasting power."),("🏃","HIIT and Cardio","High-intensity sessions that torch fat fast."),("🧘","Recovery","Yoga and protocols to prevent injury."),("🥗","Nutrition Coaching","Personalised plans that fuel transformation.")],"stats":[("5K+","Members"),("50+","Coaches"),("98%","Success"),("4.9★","Rating")],"testi":[("Kiran R.","Member","Lost 20kg in 6 months. Life-changing."),("Ananya S.","Runner","PB improved 22 minutes. World-class."),("Dev M.","Athlete","12kg muscle in one year. Real results.")],"af":[("🏆","Elite Coaches","Internationally certified trainers."),("📊","Science-Based","Peer-reviewed sports science programming."),("👥","Community","Support that keeps you accountable.")]},
    "education":    {"tagline":"Learn Without Limits.","sub":"World-class instructors, live cohorts, lifetime access, certifications employers genuinely value.","cta1":"Enroll Now","cta2":"Browse Courses","sv_title":"What We Offer","sv":[("📚","Expert Courses","Learn from top industry practitioners."),("🎯","Live Cohorts","Real-time classes with Q&A and mentorship."),("🏆","Certifications","Credentials hiring managers trust."),("♾️","Lifetime Access","Learn at your pace revisit forever.")],"stats":[("20K+","Students"),("500+","Courses"),("4.9★","Rating"),("95%","Placement")],"testi":[("Rohan M.","Graduate","Dream job 3 months after completing."),("Priya T.","Career Changer","Best investment in my career."),("Amit S.","Professional","Promoted twice. Skills directly applicable.")],"af":[("👨‍🏫","Expert Instructors","Industry practitioners with real results."),("🎯","Project-Based","Build real projects not just watch videos."),("🏆","Recognised","Credentials employers truly trust.")]},
    "realestate":   {"tagline":"Find Your Perfect Home","sub":"Premium listings, trusted agents, transparent process. Buying, selling, renting made effortless.","cta1":"Browse Properties","cta2":"Talk to an Agent","sv_title":"Our Services","sv":[("🏠","Residential Sales","Premium homes in prime locations."),("🔑","Rental Properties","Verified listings transparent pricing."),("💼","Commercial Spaces","Offices and retail for every business."),("📋","Property Management","Complete end-to-end management.")],"stats":[("5K+","Properties"),("2K+","Clients"),("₹500Cr+","Transactions"),("4.9★","Rating")],"testi":[("Suresh P.","Buyer","Perfect home in 2 weeks. Agent exceptional."),("Kavita M.","Investor","ROI on recommendations outstanding."),("Arun K.","Seller","Sold above asking in 10 days.")],"af":[("🔍","Market Knowledge","Hyper-local expertise every area."),("💰","Best Price","We negotiate hard for best deal."),("📋","All Handled","Every document and legal step managed.")]},
    "hospital":     {"tagline":"Expert Care, Every Step","sub":"Compassionate healthcare with cutting-edge technology. Your health is our absolute priority.","cta1":"Book Appointment","cta2":"Find a Doctor","sv_title":"Our Departments","sv":[("🫀","Cardiology","Heart care from diagnosis to surgery."),("🧠","Neurology","Advanced neurological treatment."),("🦷","Dental Care","Complete dental services."),("👶","Paediatrics","Specialised child healthcare.")],"stats":[("50K+","Patients"),("50+","Specialists"),("20+","Departments"),("4.9★","Rating")],"testi":[("Ramesh K.","Patient","Care saved my life. Exceptional team."),("Sunita V.","Family","Compassionate and always available."),("Dr. Anil S.","Physician","Best facility in the region.")],"af":[("👨‍⚕️","Expert Specialists","50+ specialists every department."),("🏥","Advanced Tech","State-of-the-art diagnostic technology."),("❤️","Patient-First","Treating whole person always.")]},
    "hotel":        {"tagline":"Where Luxury Meets Serenity","sub":"Extraordinary escape where world-class hospitality and unmatched comfort unite perfectly.","cta1":"Book Your Stay","cta2":"Explore Rooms","sv_title":"Our Offerings","sv":[("🛏️","Luxury Rooms","Beautifully appointed rooms stunning views."),("🍽️","Fine Dining","Award-winning restaurants world cuisine."),("🏊","Pool and Spa","Infinity pool full wellness sanctuary."),("💼","Business Centre","State-of-the-art conference facilities.")],"stats":[("20+","Years"),("10K+","Guests"),("5★","Rating"),("4.9★","Reviews")],"testi":[("Ananya P.","Honeymooner","Most magical experience of our lives."),("Rohit V.","Business","World-class. My go-to every visit."),("Meera S.","Leisure","Every detail perfect. Return every year.")],"af":[("⭐","5-Star Service","Award-winning hospitality always."),("🍽️","Signature Dining","Three restaurants each a destination."),("🧖","World-Class Spa","Sanctuary of wellness rejuvenation.")]},
    "law":          {"tagline":"Justice. Expertise. Results.","sub":"Experienced legal counsel for individuals and businesses. We fight for your rights with precision.","cta1":"Free Consultation","cta2":"Practice Areas","sv_title":"Practice Areas","sv":[("🏢","Corporate Law","Business formation, contracts, M&A."),("⚖️","Civil Litigation","Representation all civil courts."),("👨‍👩‍👧","Family Law","Divorce, custody, adoption."),("🏠","Property Law","Real estate transactions and disputes.")],"stats":[("10K+","Cases Won"),("25+","Years"),("200+","Clients"),("4.9★","Rating")],"testi":[("Rajesh M.","Business","Won a case others said unwinnable."),("Priya S.","Client","Total sensitivity and professionalism."),("Amit Corp","Counsel","Trusted legal partner 10 years.")],"af":[("⚖️","Track Record","10,000+ cases won all courts."),("🔒","Confidential","Absolute privilege guaranteed."),("📞","24/7 Available","Always accessible urgent matters.")]},
    "startup":      {"tagline":"From Zero to Category Leader","sub":"Building the future. Join us at ground floor of the defining company of our generation.","cta1":"Join Waitlist","cta2":"See How It Works","sv_title":"What We Build","sv":[("⚡","Core Product","Fastest most intuitive solution in market."),("🤖","AI Layer","Features that learn with every interaction."),("🔗","Open Platform","API developers can build great things on."),("🌐","Global Scale","Infrastructure for millions from day one.")],"stats":[("1K+","Beta Users"),("₹2Cr+","Pre-orders"),("3x","Growth"),("4.9★","Beta")],"testi":[("Ankit S.","Beta User","Going to be massive. Never seen anything like it."),("Meera V.","Investor","Most impressive team and product ever."),("Rahul P.","Early Adopter","Switched day one never looked back.")],"af":[("🚀","Hypergrowth","3x month-over-month since launch."),("🤖","AI-First","Intelligence built in not bolted on."),("🌍","Global Vision","India first then the world.")]},
    "finance":      {"tagline":"Your Wealth. Our Expertise.","sub":"SEBI-registered advisors helping build, protect, and grow wealth through disciplined planning.","cta1":"Free Consultation","cta2":"Our Services","sv_title":"Our Services","sv":[("📈","Wealth Management","Personalised portfolios aligned to goals."),("🏦","Mutual Funds","Curated funds and expert SIP planning."),("🛡️","Insurance","Comprehensive coverage for everything built."),("📋","Tax Planning","Legal optimisation to maximise returns.")],"stats":[("5K+","Clients"),("₹500Cr+","AUM"),("15+","Years"),("4.9★","Rating")],"testi":[("Suresh M.","Business","Portfolio grown 18% annually 5 years."),("Kavita P.","Retired","Secured retirement. Total peace of mind."),("Arun S.","Professional","SIP journey remarkable compounding.")],"af":[("📊","Research-Driven","Backed by rigorous fundamental analysis."),("🔒","SEBI Registered","Fully regulated and compliant."),("💼","Personalised","No generic advice. Built for your situation.")]},
    "construction": {"tagline":"Building Dreams. Delivering Excellence.","sub":"From homes to complexes, delivered on time, on budget, to the highest quality standards.","cta1":"Get Free Quote","cta2":"View Projects","sv_title":"Our Services","sv":[("🏠","Residential","Custom homes to highest specifications."),("🏢","Commercial","Offices, malls, industrial at scale."),("🎨","Interior Design","Complete fit-out every space."),("🔧","Renovation","Expert renovation existing structures.")],"stats":[("500+","Projects"),("₹500Cr+","Value"),("20+","Years"),("4.9★","Rating")],"testi":[("Vikram S.","Developer","5 projects. Quality timing always perfect."),("Anita R.","Home Owner","Dream home exactly as imagined."),("Raj Corp","Commercial","On time, on budget, exceptional finish.")],"af":[("🏗️","Turnkey","Foundation to final finishing."),("⏰","On-Time","Never missed deadline in 20 years."),("🏆","ISO 9001","Certified highest quality always.")]},
    "ngo":          {"tagline":"Every Life Deserves Dignity","sub":"Working at compassion and action creating lasting change for communities most in need.","cta1":"Donate Now","cta2":"Get Involved","sv_title":"Our Programs","sv":[("📚","Education","Scholarships for underprivileged children."),("🏥","Healthcare","Mobile clinics remote communities."),("💼","Livelihood","Skills training microfinance programs."),("🌱","Environment","Tree planting water conservation.")],"stats":[("100K+","Lives Impacted"),("15+","Years"),("50+","Communities"),("4.9★","Transparency")],"testi":[("Anita S.","Donor","See exactly where money goes. Real impact."),("Rahul M.","Corporate","Most transparent NGO partnered with."),("Meera P.","Volunteer","Changed my life as much as communities.")],"af":[("✅","100% Transparent","Full reports published every donor."),("🎯","Measurable","Programs evaluated audited outcomes."),("🤝","Community-Led","Designed with communities we serve.")]},
    "photography":  {"tagline":"Capturing Moments Forever","sub":"Every frame tells a story. Transforming ordinary moments into extraordinary timeless memories.","cta1":"Book a Session","cta2":"View Portfolio","sv_title":"Our Services","sv":[("📸","Wedding Photography","Your perfect day captured beautifully."),("👤","Portrait Sessions","Professional headshots personal portraits."),("🏢","Commercial","Stunning product and corporate photography."),("🎬","Videography","Cinematic videos that move people.")],"stats":[("500+","Sessions"),("50K+","Photos"),("5★","Rating"),("10+","Years")],"testi":[("Sneha P.","Bride","Wedding photos breathtakingly beautiful."),("Rajesh K.","CEO","Headshots exceeded every expectation."),("Priya M.","Marketing","Shots improved campaign performance.")],"af":[("📷","Award-Winning","Recognised national photography associations."),("🎨","Artistic Vision","Every photo a deliberate work of art."),("💾","48hr Delivery","Edited photos within 48 hours.")]},
    "salon":        {"tagline":"Where Beauty Meets Expertise","sub":"Premium salon services in luxurious setting. Look and feel your absolute best every day.","cta1":"Book Appointment","cta2":"Our Services","sv_title":"Our Services","sv":[("💇","Hair Styling","Expert cuts, colours, treatments by masters."),("💅","Nail Art","Manicure, pedicure, nail artistry perfectly."),("🧖","Spa Treatments","Relaxing facials and body treatments."),("💄","Bridal Makeup","Wedding makeup by skilled professionals.")],"stats":[("10K+","Clients"),("50+","Services"),("5★","Rating"),("8+","Years")],"testi":[("Sunita R.","Bride","Best bridal makeup ever seen. Perfect."),("Kavita P.","Regular","Come monthly. Always leave amazing."),("Meera S.","Client","Treatment transformed my confidence.")],"af":[("💎","Premium Products","Top-tier professional products only."),("👩‍🎨","Expert Stylists","Internationally trained certified."),("🌿","Hygienic","Sterilized tools fresh towels always.")]},
    "travel":       {"tagline":"Your World Awaits.","sub":"Curated travel experiences, personalised itineraries, and unforgettable memories for a lifetime.","cta1":"Plan My Trip","cta2":"View Packages","sv_title":"Our Services","sv":[("✈️","International Tours","Handcrafted itineraries worldwide."),("🏔️","Adventure Travel","Treks, safaris, extreme experiences."),("🏖️","Beach Holidays","Perfect resort stays island getaways."),("💑","Honeymoon Packages","Romantic escapes tailored for couples.")],"stats":[("5K+","Travellers"),("100+","Destinations"),("15+","Years"),("4.9★","Rating")],"testi":[("Rahul K.","Traveller","Bali trip flawlessly organised."),("Priya S.","Couple","Honeymoon beyond anything imagined."),("Amit R.","Family","Rajasthan tour magical for everyone.")],"af":[("🗺️","Expert Guides","Local expertise every destination."),("💰","Best Value","Unbeatable packages for experiences."),("📞","24/7 Support","With you every step of journey.")]},
    "tech_company": {"tagline":"Technology That Transforms","sub":"End-to-end solutions driving digital transformation and accelerating sustainable growth.","cta1":"Get a Quote","cta2":"Our Work","sv_title":"Our Services","sv":[("💻","Software Dev","Custom software for exact business needs."),("📱","App Development","iOS, Android, cross-platform apps."),("☁️","Cloud Solutions","Migration, architecture, managed services."),("🔒","Cybersecurity","Protecting from all evolving threats.")],"stats":[("500+","Projects"),("200+","Clients"),("15+","Years"),("4.9★","Rating")],"testi":[("Vikram S.","CTO","Platform delivered on time under budget."),("Anita R.","CEO","App drives 60% of our revenue."),("Rahul P.","Founder","Best tech partner ever worked with.")],"af":[("⚡","Agile","Fast iterative meaningful releases."),("🔒","Secure","Security built in every layer."),("🤝","Long-term","Stay invested in your success.")]},
    "wedding":      {"tagline":"Your Perfect Day. Our Greatest Joy.","sub":"Wedding experiences so perfect they feel like dreams you never want to wake from.","cta1":"Plan Your Wedding","cta2":"View Gallery","sv_title":"Our Services","sv":[("💒","Full Planning","Complete management concept to big day."),("📸","Photography","Cinematic wedding photography videography."),("🌸","Decor and Florals","Breathtaking decorations floral design."),("🍽️","Catering","Exquisite menus every cuisine taste.")],"stats":[("500+","Weddings"),("50K+","Guests"),("10+","Years"),("5★","Rating")],"testi":[("Priya and Rahul","Couple","Wedding beyond any dream we had."),("Sunita P.","Mother","Every detail handled with love and care."),("Amit V.","Groom","Best decision hiring this incredible team.")],"af":[("💎","Luxury Execution","Every element absolute perfection."),("🤝","Personal Touch","Planner dedicated solely to your wedding."),("📞","Always On Call","24/7 throughout planning.")]},
    "dental":       {"tagline":"Your Smile. Our Expertise.","sub":"Advanced dental care in comfortable anxiety-free environment. Your perfect smile awaits.","cta1":"Book Appointment","cta2":"Our Treatments","sv_title":"Our Treatments","sv":[("🦷","General Dentistry","Checkups, cleaning, preventive care."),("😁","Cosmetic","Whitening, veneers, smile makeovers."),("🦾","Implants","Permanent natural tooth replacement."),("😬","Orthodontics","Braces and Invisalign perfect alignment.")],"stats":[("10K+","Patients"),("20+","Treatments"),("15+","Years"),("5★","Rating")],"testi":[("Rahul K.","Patient","Smile transformation incredible."),("Priya S.","Patient","Most pain-free dental experience ever."),("Amit M.","Parent","Children look forward to visits.")],"af":[("🔬","Latest Tech","Advanced technology precise treatment."),("💊","Pain-Free","Modern pain management always."),("😁","Guaranteed","Results guaranteed or we make right.")]},
    "cleaning":     {"tagline":"Spotless Spaces. Happy Places.","sub":"Professional cleaning transforming home or office into pristine immaculate sanctuary.","cta1":"Book a Clean","cta2":"Our Services","sv_title":"Our Services","sv":[("🏠","Home Cleaning","Thorough deep regular residential cleaning."),("🏢","Office Cleaning","Professional commercial cleaning."),("🧹","Deep Clean","Intensive move-in move-out cleaning."),("🌿","Eco Cleaning","Non-toxic safe eco products.")],"stats":[("5K+","Clients"),("50K+","Cleans"),("8+","Years"),("5★","Rating")],"testi":[("Priya S.","Home Owner","Home never this clean. Exceptional."),("TechCorp","Manager","Office spotless. Team incredibly reliable."),("Rahul K.","Landlord","Move-out cleans perfect every time.")],"af":[("✅","Verified Staff","Background-checked fully insured."),("🌿","Eco-Friendly","Safe products protecting family."),("⏰","Reliable","Always on time always thorough.")]},
    "mental_health":{"tagline":"Your Mental Health Matters","sub":"Compassionate confidential therapy and counselling. You deserve support and help is here.","cta1":"Book a Session","cta2":"Meet Our Team","sv_title":"Our Services","sv":[("🧠","Individual Therapy","One-on-one with qualified therapists."),("👫","Couples Counselling","Expert guidance strengthen relationship."),("👨‍👩‍👧","Family Therapy","Healing communication for families."),("📱","Online Sessions","Therapy from comfort of home.")],"stats":[("5K+","Clients Helped"),("20+","Therapists"),("10+","Years"),("5★","Rating")],"testi":[("Priya S.","Client","Anxiety manageable first time in years."),("Rahul K.","Couple","Marriage stronger than ever."),("Anita M.","Client","Online sessions fit my busy life.")],"af":[("🔐","Confidential","Absolute privacy guaranteed always."),("❤️","Non-Judgmental","Safe space to be yourself."),("👩‍⚕️","Qualified","International credentials all therapists.")]},
    "business":     {"tagline":"Excellence Delivered Every Time","sub":"Deep expertise, bold execution, obsession with results. We help businesses grow and win.","cta1":"Get Started","cta2":"Learn More","sv_title":"What We Offer","sv":[("⚡","Fast Results","Exceptional outcomes ahead of schedule."),("🎯","Results-Obsessed","Every action tied to measurable goals."),("🤝","True Partnership","Invested in your success always."),("🛡️","Reliable","100+ clients trust critical projects.")],"stats":[("100+","Projects"),("50+","Clients"),("4.9★","Rating"),("5+","Years")],"testi":[("Rohit K.","MD","Delivered as promised ahead of schedule."),("Nisha A.","COO","Best vendor relationship we have had."),("Amit S.","Founder","Game-changer for our business growth.")],"af":[("⚡","Always Fast","Results faster than any competitor."),("🎯","ROI-Focused","Every engagement measured impact."),("🛡️","Proven","5+ years, 100+ clients, zero failures.")]},
}

def get_content(cat):
    return CONTENT_DB.get(cat, CONTENT_DB["business"])

def build_ai_prompt(prompt, name, ud):
    phone = ud.get("phone") or "+91 99999 99999"
    email = ud.get("email") or ("hello@" + re.sub(r'[^a-z0-9]', '', name.lower()) + ".com")
    address = ud.get("address") or "Mumbai, India"
    wa = (ud.get("whatsapp") or phone).replace("+","").replace(" ","").replace("-","")
    hours = ud.get("opening_hours") or "Mon-Sat 9AM-8PM"
    seed = abs(hash(prompt)) % 99999
    enc = urllib.parse.quote(prompt[:60])
    h1 = "https://image.pollinations.ai/prompt/ultra_realistic_" + enc + "_hero_4k?width=1400&height=800&seed=" + str(seed) + "&nologo=true&model=flux"
    h2 = "https://image.pollinations.ai/prompt/professional_" + enc + "?width=900&height=700&seed=" + str(seed+1) + "&nologo=true&model=flux"
    map_q = urllib.parse.quote(address)
    return (
        "You are an expert web developer. Generate a COMPLETE, STUNNING single HTML file website.\n\n"
        "USER REQUEST: " + prompt + "\n"
        "BUSINESS NAME: " + name + "\n"
        "PHONE: " + phone + " | EMAIL: " + email + " | ADDRESS: " + address + " | WHATSAPP: " + wa + " | HOURS: " + hours + "\n\n"
        "IMAGES (use these exact URLs):\n"
        "Hero: " + h1 + "\n"
        "About: " + h2 + "\n\n"
        "RULES:\n"
        "1. Output ONLY raw HTML starting with <!DOCTYPE html>. Zero markdown.\n"
        "2. Match quality of Stripe, Linear, Apple.\n"
        "3. Include: sticky nav, hamburger, hero 3D tilt, stats bar, about, services grid, gallery, testimonials, FAQ accordion, contact form with validation, Google Maps (https://maps.google.com/maps?q=" + map_q + "&output=embed), WhatsApp float, sticky CTA, newsletter, footer, loading screen, scroll reveal, counters, back to top, cookie banner.\n"
        "4. Google Fonts. CSS variables. Smooth animations. Mobile responsive.\n"
        "5. Contact form success message on submit.\n"
        "6. WhatsApp: https://wa.me/" + wa
    )

def build_template(prompt, name, ud):
    cat = get_category(prompt)
    ds = get_design(prompt)
    con = get_content(cat)
    seed = abs(hash(prompt)) % 99999
    enc = urllib.parse.quote(prompt[:80])

    phone = ud.get("phone") or "+91 99999 99999"
    email_addr = ud.get("email") or ("hello@" + re.sub(r'[^a-z0-9]', '', name.lower()) + ".com")
    address = ud.get("address") or "Mumbai, India"
    wa = (ud.get("whatsapp") or phone).replace("+","").replace(" ","").replace("-","")
    hours = ud.get("opening_hours") or "Mon-Sat 9AM-8PM"
    tagline = ud.get("tagline_custom") or con["tagline"]
    about_text = ud.get("about_text") or con["sub"]
    ig = ud.get("instagram") or ""
    fb = ud.get("facebook") or ""
    tw = ud.get("twitter") or ""
    li = ud.get("linkedin") or ""

    is_dark = ds["dark"]
    f1 = ds["f1"]
    f2 = ds["f2"]
    gf1 = f1.replace(" ","+")
    gf2 = f2.replace(" ","+")

    h_img  = "https://image.pollinations.ai/prompt/ultra_realistic_cinematic_" + enc + "_dramatic_4k?width=1400&height=800&seed=" + str(seed) + "&nologo=true&model=flux"
    a_img  = "https://image.pollinations.ai/prompt/professional_" + enc + "_premium_team?width=900&height=700&seed=" + str(seed+1) + "&nologo=true&model=flux"
    g1_img = "https://image.pollinations.ai/prompt/" + enc + "_showcase_1?width=700&height=500&seed=" + str(seed+2) + "&nologo=true&model=flux"
    g2_img = "https://image.pollinations.ai/prompt/" + enc + "_showcase_2?width=700&height=500&seed=" + str(seed+3) + "&nologo=true&model=flux"
    g3_img = "https://image.pollinations.ai/prompt/" + enc + "_showcase_3?width=700&height=500&seed=" + str(seed+4) + "&nologo=true&model=flux"
    g4_img = "https://image.pollinations.ai/prompt/" + enc + "_showcase_4?width=700&height=500&seed=" + str(seed+5) + "&nologo=true&model=flux"

    nav_logo = "#fff" if is_dark else ds["pr"]
    nav_link = "rgba(255,255,255,0.8)" if is_dark else ds["mu"]
    nav_hb   = "#fff" if is_dark else ds["tx"]
    hero_ov  = "linear-gradient(135deg," + ds["bg"] + "F5 0%," + ds["bg"] + "CC 60%," + ds["pr"] + "22 100%)"
    shadow   = "0 40px 80px rgba(0,0,0,0.5)" if is_dark else "0 40px 80px rgba(0,0,0,0.12)"
    svc_bg   = "rgba(255,255,255,0.03)" if is_dark else ds["ca"]
    inp_bg   = "rgba(255,255,255,0.07)" if is_dark else "#ffffff"
    mob_bg   = "rgba(2,0,8,0.98)" if is_dark else "rgba(255,255,255,0.99)"
    hg1_c    = ds["pr"] + ("1E" if is_dark else "0D")
    hg2_c    = ds["ac"] + ("14" if is_dark else "09")
    badge_bg = "rgba(255,255,255,0.1)" if is_dark else ds["ca"]
    afi_bg   = "rgba(255,255,255,0.06)" if is_dark else "#fff"
    stat_bg  = "rgba(0,0,0,0.4)" if is_dark else ds["ca"]
    ck_bg    = "rgba(2,0,8,0.97)" if is_dark else "rgba(15,15,15,0.97)"
    map_q    = urllib.parse.quote(address)

    svcs = ""
    for ic, t, d in con["sv"]:
        svcs += ("<div class=\"sc\" onmouseover=\"this.style.transform='translateY(-8px)';this.style.borderColor='" + ds["pr"] + "'\" "
                 "onmouseout=\"this.style.transform='';this.style.borderColor='" + ds["br"] + "'\">"
                 "<span class=\"si\">" + ic + "</span><h3>" + t + "</h3><p>" + d + "</p></div>")

    stats = ""
    for n, l in con["stats"]:
        stats += "<div class=\"sti\"><div class=\"sn\">" + n + "</div><div class=\"sl\">" + l + "</div></div>"

    testis = ""
    for a, r, t in con["testi"]:
        testis += ("<div class=\"tc\" onmouseover=\"this.style.transform='translateY(-6px)';this.style.borderColor='" + ds["pr"] + "'\" "
                   "onmouseout=\"this.style.transform='';this.style.borderColor='" + ds["br"] + "'\">"
                   "<div class=\"ts\">★★★★★</div><p class=\"tt\">&ldquo;" + t + "&rdquo;</p>"
                   "<div class=\"ta\"><div class=\"av\">" + a[0] + "</div>"
                   "<div><div class=\"an\">" + a + "</div><div class=\"ar\">" + r + "</div></div></div></div>")

    gals = ""
    for gimg in [g1_img, g2_img, g3_img, g4_img]:
        gals += ("<div class=\"gi\" onmouseover=\"this.querySelector('img').style.transform='scale(1.1)'\" "
                 "onmouseout=\"this.querySelector('img').style.transform=''\">"
                 "<img src=\"" + gimg + "\" loading=\"lazy\" alt=\"Gallery\"/>"
                 "<div class=\"go\"><span>View &rarr;</span></div></div>")

    afs = ""
    for ic, t, d in con["af"]:
        afs += ("<div class=\"af\" onmouseover=\"this.style.borderColor='" + ds["pr"] + "';this.style.transform='translateX(5px)'\" "
                "onmouseout=\"this.style.borderColor='" + ds["br"] + "';this.style.transform=''\">"
                "<div class=\"afi\">" + ic + "</div><div class=\"aft\"><h4>" + t + "</h4><p>" + d + "</p></div></div>")

    soc_ig = "<a href=\"" + ("https://instagram.com/" + ig if ig else "#") + "\" target=\"_blank\" title=\"Instagram\">📸</a>"
    soc_fb = "<a href=\"" + ("https://facebook.com/" + fb if fb else "#") + "\" target=\"_blank\" title=\"Facebook\">👍</a>"
    soc_tw = "<a href=\"" + ("https://twitter.com/" + tw if tw else "#") + "\" target=\"_blank\" title=\"Twitter\">🐦</a>"
    soc_li = "<a href=\"" + ("https://linkedin.com/in/" + li if li else "#") + "\" target=\"_blank\" title=\"LinkedIn\">💼</a>"
    soc_wa = "<a href=\"https://wa.me/" + wa + "\" target=\"_blank\" title=\"WhatsApp\">💬</a>"
    social_links = soc_ig + soc_fb + soc_tw + soc_li + soc_wa

    svc_footer = ""
    for s in con["sv"]:
        svc_footer += "<a href=\"#services\">" + s[1] + "</a>"

    wa_svg = ("<svg width=\"28\" height=\"28\" viewBox=\"0 0 24 24\" fill=\"white\">"
              "<path d=\"M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15"
              "-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475"
              "-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52"
              ".149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207"
              "-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372"
              "-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 "
              "5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 "
              "1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347"
              "m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648"
              "-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 "
              "5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 "
              "9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096"
              ".547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 "
              "0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z\"/></svg>")

    html = (
"<!DOCTYPE html>\n"
"<html lang=\"en\">\n"
"<head>\n"
"<meta charset=\"UTF-8\">\n"
"<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">\n"
"<meta name=\"description\" content=\"" + name + " \u2014 " + tagline + ". " + con["sub"][:120] + "\">\n"
"<meta property=\"og:title\" content=\"" + name + "\">\n"
"<meta property=\"og:description\" content=\"" + con["sub"][:160] + "\">\n"
"<meta property=\"og:image\" content=\"" + h_img + "\">\n"
"<meta name=\"twitter:card\" content=\"summary_large_image\">\n"
"<title>" + name + " \u2014 " + tagline + "</title>\n"
"<link href=\"https://fonts.googleapis.com/css2?family=" + gf1 + ":ital,wght@0,700;0,800;0,900;1,700&family=" + gf2 + ":wght@300;400;500;600;700;800&display=swap\" rel=\"stylesheet\">\n"
"<style>\n"
"*{margin:0;padding:0;box-sizing:border-box}\n"
":root{--bg:" + ds["bg"] + ";--pr:" + ds["pr"] + ";--ac:" + ds["ac"] + ";--tx:" + ds["tx"] + ";--mu:" + ds["mu"] + ";--ca:" + ds["ca"] + ";--br:" + ds["br"] + ";--nb:" + ds["nb"] + ";--nt:" + ds["nt"] + "}\n"
"html{scroll-behavior:smooth}\n"
"::-webkit-scrollbar{width:5px}::-webkit-scrollbar-track{background:var(--bg)}::-webkit-scrollbar-thumb{background:var(--pr);border-radius:3px}\n"
"body{font-family:'" + f2 + "',sans-serif;background:var(--bg);color:var(--tx);overflow-x:hidden;line-height:1.6}\n"
"@keyframes fadeUp{from{opacity:0;transform:translateY(40px)}to{opacity:1;transform:translateY(0)}}\n"
"@keyframes fadeRight{from{opacity:0;transform:translateX(50px)}to{opacity:1;transform:translateX(0)}}\n"
"@keyframes pulse{0%,100%{opacity:1;transform:scale(1)}50%{opacity:0.65;transform:scale(1.35)}}\n"
"@keyframes float{0%,100%{transform:translateY(0)}50%{transform:translateY(-14px)}}\n"
"@keyframes spin{to{transform:rotate(360deg)}}\n"
"@keyframes waP{0%,100%{box-shadow:0 0 0 0 rgba(37,211,102,0.5)}70%{box-shadow:0 0 0 16px rgba(37,211,102,0)}}\n"
"#ldr{position:fixed;inset:0;background:var(--bg);z-index:99999;display:flex;align-items:center;justify-content:center;flex-direction:column;gap:18px;transition:opacity 0.6s}\n"
"#ldr.out{opacity:0;pointer-events:none}\n"
".ldr-logo{font-family:'" + f1 + "',serif;font-size:2.2rem;font-weight:900;color:var(--pr);letter-spacing:-1px}\n"
".ldr-ring{width:46px;height:46px;border:3px solid var(--ca);border-top-color:var(--pr);border-radius:50%;animation:spin 0.8s linear infinite}\n"
"nav{position:fixed;top:0;width:100%;z-index:1000;padding:0 5%;transition:all 0.4s}\n"
"nav.solid{background:var(--nb);backdrop-filter:blur(24px);border-bottom:1px solid var(--br);box-shadow:0 4px 30px rgba(0,0,0,0.08)}\n"
".ni{max-width:1280px;margin:0 auto;display:flex;align-items:center;justify-content:space-between;height:72px}\n"
".logo{font-family:'" + f1 + "',serif;font-size:1.75rem;font-weight:900;color:" + nav_logo + ";text-decoration:none;letter-spacing:-0.5px;transition:color 0.3s}\n"
"nav.solid .logo{color:var(--pr)}\n"
".lks{display:flex;align-items:center;gap:32px;list-style:none}\n"
".lks a{color:" + nav_link + ";text-decoration:none;font-weight:500;font-size:0.88rem;transition:color 0.2s}\n"
"nav.solid .lks a{color:var(--nt)}\n"
".lks a:hover,.lks a.active{color:var(--pr)}\n"
".nbtn{background:var(--pr);color:#fff;padding:10px 24px;border-radius:100px;font-weight:700;font-size:0.85rem;text-decoration:none;transition:all 0.3s;box-shadow:0 4px 20px rgba(0,0,0,0.15)}\n"
".nbtn:hover{transform:translateY(-2px);filter:brightness(1.1);color:#fff}\n"
".hb{display:none;background:none;border:none;cursor:pointer;flex-direction:column;gap:5px;padding:4px}\n"
".hb span{width:24px;height:2px;background:" + nav_hb + ";border-radius:2px;display:block;transition:all 0.3s}\n"
"nav.solid .hb span{background:var(--tx)}\n"
".hb.o span:nth-child(1){transform:translateY(7px) rotate(45deg)}\n"
".hb.o span:nth-child(2){opacity:0}\n"
".hb.o span:nth-child(3){transform:translateY(-7px) rotate(-45deg)}\n"
".mob{display:none;position:fixed;inset:0;z-index:999;background:" + mob_bg + ";backdrop-filter:blur(30px);flex-direction:column;align-items:center;justify-content:center;gap:28px}\n"
".mob.o{display:flex}\n"
".mob a{font-size:1.6rem;font-weight:700;color:var(--tx);text-decoration:none;transition:color 0.2s}\n"
".mob a:hover{color:var(--pr)}\n"
".mob .xb{position:absolute;top:22px;right:24px;background:none;border:none;color:var(--tx);font-size:1.9rem;cursor:pointer}\n"
".hero{min-height:100vh;display:flex;align-items:center;padding:100px 5% 80px;position:relative;overflow:hidden}\n"
".hbg{position:absolute;inset:0;background:url('" + h_img + "') center/cover no-repeat;opacity:" + ("0.13" if is_dark else "0.07") + ";filter:blur(2px);transform:scale(1.08)}\n"
".hov{position:absolute;inset:0;background:" + hero_ov + "}\n"
".hg1{position:absolute;top:-25%;right:-8%;width:700px;height:700px;border-radius:50%;background:radial-gradient(circle," + hg1_c + " 0%,transparent 70%);pointer-events:none}\n"
".hg2{position:absolute;bottom:-20%;left:-5%;width:500px;height:500px;border-radius:50%;background:radial-gradient(circle," + hg2_c + " 0%,transparent 70%);pointer-events:none}\n"
".hin{position:relative;z-index:2;max-width:1280px;margin:0 auto;width:100%;display:grid;grid-template-columns:1fr 1fr;gap:80px;align-items:center}\n"
".badge{display:inline-flex;align-items:center;gap:8px;background:" + badge_bg + ";backdrop-filter:blur(12px);border:1px solid var(--br);padding:8px 20px;border-radius:100px;font-size:0.72rem;font-weight:700;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:20px;animation:fadeUp 0.6s ease both;color:var(--tx)}\n"
".dot{width:8px;height:8px;border-radius:50%;background:var(--ac);animation:pulse 2s infinite;box-shadow:0 0 10px var(--ac)}\n"
".htitle{font-family:'" + f1 + "',serif;font-size:clamp(2.6rem,4.5vw,4.5rem);font-weight:900;line-height:1.06;letter-spacing:-2px;margin-bottom:16px;color:var(--tx);animation:fadeUp 0.7s ease 0.1s both}\n"
".hac{color:var(--pr);display:block;font-style:italic}\n"
".hsub{font-size:1rem;color:var(--mu);line-height:1.78;margin-bottom:28px;max-width:480px;animation:fadeUp 0.7s ease 0.2s both}\n"
".hcbar{display:flex;gap:20px;flex-wrap:wrap;margin-bottom:28px;animation:fadeUp 0.7s ease 0.25s both}\n"
".hci{display:flex;align-items:center;gap:8px;font-size:0.84rem;color:var(--mu)}\n"
".hci a{color:var(--pr);text-decoration:none;font-weight:600}\n"
".hbtns{display:flex;gap:14px;flex-wrap:wrap;animation:fadeUp 0.7s ease 0.3s both}\n"
".bp{display:inline-flex;align-items:center;gap:8px;background:var(--pr);color:#fff;font-weight:800;font-size:0.88rem;padding:15px 30px;border-radius:100px;text-decoration:none;transition:all 0.3s;box-shadow:0 8px 30px rgba(0,0,0,0.2)}\n"
".bp:hover{transform:translateY(-3px);filter:brightness(1.1);box-shadow:0 16px 40px rgba(0,0,0,0.3)}\n"
".bs{display:inline-flex;align-items:center;gap:8px;background:var(--ca);color:var(--tx);font-weight:700;font-size:0.88rem;padding:15px 30px;border-radius:100px;text-decoration:none;border:1px solid var(--br);transition:all 0.3s}\n"
".bs:hover{transform:translateY(-3px)}\n"
".bwa{display:inline-flex;align-items:center;gap:8px;background:#25D366;color:#fff;font-weight:700;font-size:0.88rem;padding:15px 22px;border-radius:100px;text-decoration:none;transition:all 0.3s}\n"
".bwa:hover{transform:translateY(-3px);filter:brightness(1.1)}\n"
".hiw{position:relative;perspective:1200px;animation:fadeRight 0.9s ease 0.2s both}\n"
".hic{border-radius:24px;overflow:hidden;box-shadow:" + shadow + ",0 0 0 1px var(--br);transform:rotateY(-6deg) rotateX(3deg);transition:transform 0.7s ease;animation:float 6s ease-in-out infinite}\n"
".hic:hover{transform:rotateY(0) rotateX(0)}\n"
".hic img{width:100%;height:440px;object-fit:cover;display:block}\n"
".hib{position:absolute;bottom:20px;left:20px;background:rgba(0,0,0,0.75);backdrop-filter:blur(20px);border:1px solid rgba(255,255,255,0.15);padding:12px 18px;border-radius:14px;display:flex;align-items:center;gap:10px}\n"
".ldot{width:8px;height:8px;border-radius:50%;background:#22C55E;box-shadow:0 0 10px #22C55E;animation:pulse 2s infinite}\n"
".ltext{color:#fff;font-size:0.74rem;font-weight:600}\n"
".statbar{padding:0 5%;border-top:1px solid var(--br);border-bottom:1px solid var(--br);background:" + stat_bg + "}\n"
".stin{max-width:1280px;margin:0 auto;display:grid;grid-template-columns:repeat(4,1fr)}\n"
".sti{padding:32px 20px;text-align:center;border-right:1px solid var(--br);transition:background 0.3s;cursor:default}\n"
".sti:last-child{border-right:none}\n"
".sti:hover{background:var(--ca)}\n"
".sn{font-family:'" + f1 + "',serif;font-size:2.4rem;font-weight:900;color:var(--pr);margin-bottom:4px;line-height:1}\n"
".sl{font-size:0.7rem;color:var(--mu);font-weight:600;text-transform:uppercase;letter-spacing:1.2px}\n"
"section{padding:100px 5%}\n"
".sec{max-width:1280px;margin:0 auto}\n"
".lbl{display:inline-flex;align-items:center;gap:8px;background:var(--ca);color:var(--pr);font-size:0.7rem;font-weight:800;text-transform:uppercase;letter-spacing:2px;padding:7px 17px;border-radius:100px;margin-bottom:18px;border:1px solid var(--br)}\n"
".sh{font-family:'" + f1 + "',serif;font-size:clamp(1.8rem,3vw,2.8rem);font-weight:900;color:var(--tx);line-height:1.15;letter-spacing:-1px;margin-bottom:14px}\n"
".sh span{color:var(--pr)}\n"
".sb{font-size:0.93rem;color:var(--mu);line-height:1.78;max-width:520px}\n"
".ag{display:grid;grid-template-columns:1fr 1fr;gap:80px;align-items:center}\n"
".aimg{border-radius:24px;overflow:hidden;position:relative;box-shadow:" + shadow + "}\n"
".aimg img{width:100%;height:500px;object-fit:cover;display:block;transition:transform 0.7s}\n"
".aimg:hover img{transform:scale(1.05)}\n"
".atag{position:absolute;top:20px;left:20px;background:var(--pr);color:#fff;font-size:0.7rem;font-weight:800;padding:8px 16px;border-radius:100px;text-transform:uppercase;letter-spacing:1px}\n"
".afs{display:flex;flex-direction:column;gap:14px;margin-top:28px}\n"
".af{display:flex;align-items:flex-start;gap:14px;padding:17px;background:var(--ca);border-radius:16px;border:1px solid var(--br);transition:all 0.3s;cursor:default}\n"
".afi{width:44px;height:44px;border-radius:12px;background:" + afi_bg + ";border:1px solid var(--br);display:flex;align-items:center;justify-content:center;font-size:1.3rem;flex-shrink:0}\n"
".aft h4{font-weight:700;font-size:0.87rem;color:var(--tx);margin-bottom:3px}\n"
".aft p{font-size:0.78rem;color:var(--mu);line-height:1.5}\n"
".sg{display:grid;grid-template-columns:repeat(2,1fr);gap:20px;margin-top:20px}\n"
".sc{background:var(--bg);border:1px solid var(--br);border-radius:24px;padding:36px;transition:all 0.4s;position:relative;overflow:hidden;cursor:default}\n"
".sc::before{content:\"\";position:absolute;inset:0;background:linear-gradient(135deg,var(--pr),transparent);opacity:0;transition:opacity 0.4s}\n"
".sc:hover::before{opacity:0.04}\n"
".si{font-size:2.8rem;margin-bottom:18px;display:block}\n"
".sc h3{font-family:'" + f1 + "',serif;font-size:1.2rem;font-weight:800;color:var(--tx);margin-bottom:10px}\n"
".sc p{font-size:0.86rem;color:var(--mu);line-height:1.7}\n"
".gg{display:grid;grid-template-columns:repeat(2,1fr);gap:16px;margin-top:40px}\n"
".gi{border-radius:20px;overflow:hidden;aspect-ratio:4/3;position:relative;cursor:pointer}\n"
".gi img{width:100%;height:100%;object-fit:cover;display:block;transition:transform 0.6s}\n"
".go{position:absolute;inset:0;background:linear-gradient(to top,rgba(0,0,0,0.65),transparent);opacity:0;transition:opacity 0.3s;display:flex;align-items:flex-end;padding:20px}\n"
".go span{color:#fff;font-weight:700;font-size:0.88rem}\n"
".gi:hover .go{opacity:1}\n"
".tg{display:grid;grid-template-columns:repeat(3,1fr);gap:20px;margin-top:40px}\n"
".tc{background:var(--bg);border:1px solid var(--br);border-radius:24px;padding:32px;transition:all 0.3s;position:relative;overflow:hidden;cursor:default}\n"
".tc::before{content:'\\201C';position:absolute;top:-18px;right:14px;font-size:7.5rem;color:var(--pr);opacity:0.06;font-family:serif;line-height:1}\n"
".ts{color:var(--ac);font-size:0.9rem;letter-spacing:3px;margin-bottom:14px}\n"
".tt{font-size:0.87rem;color:var(--mu);line-height:1.75;margin-bottom:20px;font-style:italic}\n"
".ta{display:flex;align-items:center;gap:12px}\n"
".av{width:44px;height:44px;border-radius:50%;background:linear-gradient(135deg,var(--pr),var(--ac));display:flex;align-items:center;justify-content:center;color:#fff;font-weight:800;font-size:0.9rem;flex-shrink:0}\n"
".an{font-weight:700;font-size:0.84rem;color:var(--tx)}\n"
".ar{font-size:0.72rem;color:var(--mu)}\n"
".fqi{border-bottom:1px solid var(--br)}\n"
".fqb{width:100%;background:none;border:none;cursor:pointer;padding:18px 0;display:flex;justify-content:space-between;align-items:center;gap:16px;text-align:left}\n"
".fqq{font-weight:700;font-size:0.93rem;color:var(--tx)}\n"
".fqi2{font-size:1.3rem;color:var(--pr);flex-shrink:0;transition:transform 0.3s}\n"
".fqa{display:none;padding-bottom:14px}\n"
".fqa p{color:var(--mu);font-size:0.86rem;line-height:1.75}\n"
".ccg{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:14px;margin-bottom:28px;margin-top:36px}\n"
".cc{background:var(--bg);border:1px solid var(--br);border-radius:18px;padding:20px;text-align:center}\n"
".cci{font-size:1.7rem;margin-bottom:8px}\n"
".cc h4{font-weight:700;font-size:0.82rem;color:var(--tx);margin-bottom:5px}\n"
".cc a,.cc p{color:var(--pr);text-decoration:none;font-size:0.78rem;font-weight:600;display:block;line-height:1.4}\n"
".cc p{color:var(--mu);font-weight:400}\n"
".cf{background:var(--bg);border:1px solid var(--br);border-radius:24px;padding:32px}\n"
".fg{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:16px}\n"
".fg2{display:flex;flex-direction:column;gap:6px}\n"
".fg2 label{font-size:0.77rem;font-weight:600;color:var(--mu)}\n"
".fg2 input,.fg2 textarea{padding:12px 15px;background:" + inp_bg + ";border:1px solid var(--br);border-radius:12px;color:var(--tx);font-size:0.87rem;outline:none;transition:border-color 0.2s;font-family:'" + f2 + "',sans-serif;width:100%}\n"
".fg2 input:focus,.fg2 textarea:focus{border-color:var(--pr)}\n"
".fg2 textarea{resize:vertical;min-height:96px}\n"
".fsucc{display:none;background:#dcfce7;border:1px solid #a7f3d0;border-radius:12px;padding:14px;text-align:center;color:#065f46;font-weight:600;margin-top:12px}\n"
".nlf{display:flex;gap:12px;max-width:480px;margin:20px auto 0;flex-wrap:wrap}\n"
".nlf input{flex:1;min-width:160px;padding:13px 18px;background:" + inp_bg + ";border:1px solid var(--br);border-radius:100px;color:var(--tx);font-size:0.87rem;outline:none}\n"
".nlf button{background:var(--pr);color:#fff;border:none;padding:13px 22px;border-radius:100px;font-weight:800;font-size:0.87rem;cursor:pointer;white-space:nowrap}\n"
".nlf button:hover{filter:brightness(1.1)}\n"
".ctab{max-width:960px;margin:0 auto;background:linear-gradient(135deg,var(--pr),var(--ac));border-radius:32px;padding:70px 55px;text-align:center;position:relative;overflow:hidden;box-shadow:0 40px 80px rgba(0,0,0,0.25)}\n"
".ctab::before{content:\"\";position:absolute;top:-40%;right:-8%;width:500px;height:500px;border-radius:50%;background:rgba(255,255,255,0.07);pointer-events:none}\n"
".ctab h2{font-family:'" + f1 + "',serif;font-size:clamp(1.8rem,3.5vw,2.8rem);font-weight:900;color:#fff;margin-bottom:14px;position:relative;z-index:1;letter-spacing:-1px}\n"
".ctab p{color:rgba(255,255,255,0.85);font-size:0.93rem;margin-bottom:30px;position:relative;z-index:1;max-width:480px;margin-left:auto;margin-right:auto}\n"
".cbtns{display:flex;gap:14px;justify-content:center;flex-wrap:wrap;position:relative;z-index:1}\n"
".cb1{background:#fff;color:var(--pr);font-weight:800;padding:14px 32px;border-radius:100px;text-decoration:none;font-size:0.88rem;transition:all 0.3s;box-shadow:0 8px 30px rgba(0,0,0,0.15)}\n"
".cb1:hover{transform:translateY(-3px)}\n"
".cb2{background:rgba(255,255,255,0.15);color:#fff;font-weight:700;padding:14px 32px;border-radius:100px;text-decoration:none;font-size:0.88rem;border:1px solid rgba(255,255,255,0.3);transition:all 0.3s}\n"
".cb2:hover{background:rgba(255,255,255,0.25);transform:translateY(-3px)}\n"
".fgrid{display:grid;grid-template-columns:2fr 1fr 1fr 1fr;gap:44px;max-width:1280px;margin:0 auto 36px}\n"
".fbr p{font-size:0.8rem;color:var(--mu);margin-top:12px;line-height:1.7;max-width:220px}\n"
".flogo{font-family:'" + f1 + "',serif;font-size:1.6rem;font-weight:900;color:var(--pr)}\n"
".fsoc{display:flex;gap:10px;margin-top:16px;flex-wrap:wrap}\n"
".fsoc a{width:36px;height:36px;border-radius:10px;background:var(--ca);border:1px solid var(--br);display:flex;align-items:center;justify-content:center;text-decoration:none;font-size:1rem;transition:all 0.3s}\n"
".fsoc a:hover{background:var(--pr);transform:translateY(-2px)}\n"
".fc h4{font-weight:700;font-size:0.72rem;color:var(--mu);text-transform:uppercase;letter-spacing:1.5px;margin-bottom:16px}\n"
".fc a{display:block;color:var(--mu);text-decoration:none;font-size:0.8rem;margin-bottom:10px;transition:color 0.2s}\n"
".fc a:hover{color:var(--pr)}\n"
".fbot{max-width:1280px;margin:0 auto;border-top:1px solid var(--br);padding-top:22px;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px}\n"
".fbot p{font-size:0.74rem;color:var(--mu)}\n"
".fbot a{color:var(--mu);text-decoration:none;font-size:0.7rem;margin-left:14px}\n"
".fbot a:hover{color:var(--pr)}\n"
".wab{position:fixed;bottom:24px;right:24px;z-index:9999;width:58px;height:58px;background:#25D366;border-radius:50%;display:flex;align-items:center;justify-content:center;text-decoration:none;animation:waP 2s infinite;transition:transform 0.3s;box-shadow:0 8px 30px rgba(37,211,102,0.4)}\n"
".wab:hover{transform:scale(1.12)}\n"
".scta{position:fixed;bottom:0;left:0;right:0;z-index:9990;background:var(--nb);backdrop-filter:blur(22px);border-top:1px solid var(--br);padding:12px 5%;display:flex;align-items:center;justify-content:space-between;gap:16px;transform:translateY(100%);transition:transform 0.4s ease;flex-wrap:wrap}\n"
".scta-t p:first-child{font-weight:700;font-size:0.87rem;color:var(--tx)}\n"
".scta-t p:last-child{font-size:0.74rem;color:var(--mu)}\n"
".scta-b{display:flex;gap:10px}\n"
".scta-b a{padding:10px 20px;border-radius:100px;text-decoration:none;font-weight:700;font-size:0.82rem;transition:all 0.3s}\n"
".sb1{background:var(--ca);color:var(--tx);border:1px solid var(--br)}\n"
".sb2{background:var(--pr);color:#fff}\n"
"#btt{position:fixed;bottom:90px;right:24px;z-index:9980;width:42px;height:42px;background:var(--pr);color:#fff;border:none;border-radius:50%;cursor:pointer;font-size:1.1rem;display:none;align-items:center;justify-content:center;box-shadow:0 4px 20px rgba(0,0,0,0.2);transition:all 0.3s}\n"
"#btt:hover{transform:translateY(-3px)}\n"
".ckb{position:fixed;bottom:0;left:0;right:0;z-index:9970;background:" + ck_bg + ";color:#fff;padding:14px 5%;display:flex;align-items:center;justify-content:space-between;gap:16px;flex-wrap:wrap;transition:transform 0.4s}\n"
".ckb.h{transform:translateY(100%)}\n"
".ckb p{font-size:0.8rem;color:rgba(255,255,255,0.78);max-width:600px}\n"
".ckbs{display:flex;gap:10px}\n"
".cka{background:var(--pr);color:#fff;border:none;padding:10px 20px;border-radius:100px;font-weight:700;font-size:0.8rem;cursor:pointer}\n"
".ckd{background:rgba(255,255,255,0.1);color:#fff;border:1px solid rgba(255,255,255,0.2);padding:10px 20px;border-radius:100px;font-weight:600;font-size:0.8rem;cursor:pointer}\n"
".rev{opacity:0;transform:translateY(40px) scale(0.97);transition:opacity 0.7s ease,transform 0.7s ease}\n"
".rev.vis{opacity:1;transform:translateY(0) scale(1)}\n"
"@media(max-width:900px){"
".hin,.ag{grid-template-columns:1fr;gap:48px;text-align:center}"
".hiw{order:-1}.hsub{max-width:100%}.hbtns,.hcbar{justify-content:center}"
".sg,.gg{grid-template-columns:1fr}"
".tg{grid-template-columns:1fr}"
".stin{grid-template-columns:repeat(2,1fr)}"
".fgrid{grid-template-columns:1fr 1fr;gap:28px}"
".lks,.nbtn{display:none}.hb{display:flex}"
".ctab{padding:48px 28px}.sb{max-width:100%}"
".fg{grid-template-columns:1fr}"
"}\n"
"@media(max-width:540px){"
".stin,.fgrid{grid-template-columns:1fr}"
".htitle{font-size:2.4rem}.fbot{flex-direction:column;text-align:center}"
"}\n"
"</style>\n"
"</head>\n"
"<body>\n"
"\n"
"<div id=\"ldr\"><div class=\"ldr-logo\">" + name + "</div><div class=\"ldr-ring\"></div></div>\n"
"\n"
"<div class=\"mob\" id=\"mob\">\n"
"  <button class=\"xb\" onclick=\"cm()\">&#x2715;</button>\n"
"  <a href=\"#about\" onclick=\"cm()\">About</a>\n"
"  <a href=\"#services\" onclick=\"cm()\">Services</a>\n"
"  <a href=\"#gallery\" onclick=\"cm()\">Gallery</a>\n"
"  <a href=\"#testimonials\" onclick=\"cm()\">Reviews</a>\n"
"  <a href=\"#faq\" onclick=\"cm()\">FAQ</a>\n"
"  <a href=\"#contact\" onclick=\"cm()\" style=\"background:var(--pr);color:#fff;padding:14px 32px;border-radius:100px\">Get Started &rarr;</a>\n"
"</div>\n"
"\n"
"<nav id=\"nav\">\n"
"  <div class=\"ni\">\n"
"    <a href=\"#\" class=\"logo\">" + name + "</a>\n"
"    <ul class=\"lks\">\n"
"      <li><a href=\"#about\">About</a></li>\n"
"      <li><a href=\"#services\">Services</a></li>\n"
"      <li><a href=\"#gallery\">Gallery</a></li>\n"
"      <li><a href=\"#testimonials\">Reviews</a></li>\n"
"      <li><a href=\"#faq\">FAQ</a></li>\n"
"    </ul>\n"
"    <a href=\"#contact\" class=\"nbtn\">Get Started &rarr;</a>\n"
"    <button class=\"hb\" id=\"hb\" onclick=\"tm()\"><span></span><span></span><span></span></button>\n"
"  </div>\n"
"</nav>\n"
"\n"
"<section class=\"hero\" id=\"home\">\n"
"  <div class=\"hbg\"></div><div class=\"hov\"></div><div class=\"hg1\"></div><div class=\"hg2\"></div>\n"
"  <div class=\"hin\">\n"
"    <div>\n"
"      <div class=\"badge\"><span class=\"dot\"></span>&#x2736; " + name + " &middot; Premium</div>\n"
"      <h1 class=\"htitle\">" + name + "<span class=\"hac\">" + tagline + "</span></h1>\n"
"      <p class=\"hsub\">" + con["sub"] + "</p>\n"
"      <div class=\"hcbar\">\n"
"        <div class=\"hci\">&#128222; <a href=\"tel:" + phone + "\">" + phone + "</a></div>\n"
"        <div class=\"hci\">&#9993;&#65039; <a href=\"mailto:" + email_addr + "\">" + email_addr + "</a></div>\n"
"      </div>\n"
"      <div class=\"hbtns\">\n"
"        <a href=\"#contact\" class=\"bp\">" + con["cta1"] + " &rarr;</a>\n"
"        <a href=\"#services\" class=\"bs\">&#9654; " + con["cta2"] + "</a>\n"
"        <a href=\"https://wa.me/" + wa + "\" target=\"_blank\" class=\"bwa\">\n"
"          <svg width=\"18\" height=\"18\" viewBox=\"0 0 24 24\" fill=\"white\"><path d=\"M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z\"/></svg>\n"
"          WhatsApp\n"
"        </a>\n"
"      </div>\n"
"    </div>\n"
"    <div class=\"hiw\">\n"
"      <div class=\"hic\">\n"
"        <img src=\"" + h_img + "\" alt=\"" + name + "\" loading=\"eager\"/>\n"
"        <div class=\"hib\"><div class=\"ldot\"></div><span class=\"ltext\">Live &middot; " + hours + "</span></div>\n"
"      </div>\n"
"    </div>\n"
"  </div>\n"
"</section>\n"
"\n"
"<div class=\"statbar\"><div class=\"stin\">" + stats + "</div></div>\n"
"\n"
"<section id=\"about\" style=\"background:var(--bg)\">\n"
"  <div class=\"sec\">\n"
"    <div class=\"ag\">\n"
"      <div class=\"aimg rev\"><img src=\"" + a_img + "\" alt=\"About " + name + "\" loading=\"lazy\"/><div class=\"atag\">Our Story</div></div>\n"
"      <div class=\"rev\">\n"
"        <div class=\"lbl\">&#x2736; About Us</div>\n"
"        <h2 class=\"sh\">Built for <span>Excellence</span>.</h2>\n"
"        <p class=\"sb\">" + about_text + "</p>\n"
"        <div class=\"afs\">" + afs + "</div>\n"
"      </div>\n"
"    </div>\n"
"  </div>\n"
"</section>\n"
"\n"
"<section id=\"services\" style=\"background:" + svc_bg + "\">\n"
"  <div class=\"sec\">\n"
"    <div style=\"text-align:center;margin-bottom:40px\">\n"
"      <div class=\"lbl\">&#x2736; " + con["sv_title"] + "</div>\n"
"      <h2 class=\"sh\" style=\"text-align:center\">Why Choose <span>" + name + "</span></h2>\n"
"      <p class=\"sb\" style=\"margin:10px auto 0;text-align:center\">Everything delivered to the highest possible standard.</p>\n"
"    </div>\n"
"    <div class=\"sg rev\">" + svcs + "</div>\n"
"  </div>\n"
"</section>\n"
"\n"
"<section id=\"gallery\" style=\"background:var(--bg)\">\n"
"  <div class=\"sec\">\n"
"    <div style=\"text-align:center;margin-bottom:20px\">\n"
"      <div class=\"lbl\">&#x2736; Gallery</div>\n"
"      <h2 class=\"sh\" style=\"text-align:center\">See It For <span>Yourself</span></h2>\n"
"    </div>\n"
"    <div class=\"gg rev\">" + gals + "</div>\n"
"  </div>\n"
"</section>\n"
"\n"
"<section id=\"testimonials\" style=\"background:" + svc_bg + "\">\n"
"  <div class=\"sec\">\n"
"    <div style=\"text-align:center;margin-bottom:20px\">\n"
"      <div class=\"lbl\">&#x2736; Reviews</div>\n"
"      <h2 class=\"sh\" style=\"text-align:center\">What Our <span>Clients Say</span></h2>\n"
"    </div>\n"
"    <div class=\"tg rev\">" + testis + "</div>\n"
"  </div>\n"
"</section>\n"
"\n"
"<section id=\"faq\" style=\"background:var(--bg)\">\n"
"  <div class=\"sec\" style=\"max-width:800px\">\n"
"    <div style=\"text-align:center;margin-bottom:36px\">\n"
"      <div class=\"lbl\">&#x2736; FAQ</div>\n"
"      <h2 class=\"sh\" style=\"text-align:center\">Frequently Asked <span>Questions</span></h2>\n"
"    </div>\n"
"    <div class=\"rev\">\n"
"      <div class=\"fqi\"><button class=\"fqb\" onclick=\"fq(this)\"><span class=\"fqq\">How do I get started with " + name + "?</span><span class=\"fqi2\">+</span></button><div class=\"fqa\"><p>Simply contact us through the form below or call us directly. We respond within 24 hours and set up a free initial consultation to understand exactly what you need.</p></div></div>\n"
"      <div class=\"fqi\"><button class=\"fqb\" onclick=\"fq(this)\"><span class=\"fqq\">What is your pricing?</span><span class=\"fqi2\">+</span></button><div class=\"fqa\"><p>Our pricing is completely transparent and tailored to your requirements. Contact us for a personalised quote with no hidden fees ever.</p></div></div>\n"
"      <div class=\"fqi\"><button class=\"fqb\" onclick=\"fq(this)\"><span class=\"fqq\">How long does the process take?</span><span class=\"fqi2\">+</span></button><div class=\"fqa\"><p>Timelines depend on scope. We are known for fast reliable delivery and will give you a clear timeline upfront before any work begins.</p></div></div>\n"
"      <div class=\"fqi\"><button class=\"fqb\" onclick=\"fq(this)\"><span class=\"fqq\">Do you offer ongoing support?</span><span class=\"fqi2\">+</span></button><div class=\"fqa\"><p>Absolutely. We pride ourselves on long-term relationships. Ongoing support and assistance are always available to you.</p></div></div>\n"
"      <div class=\"fqi\"><button class=\"fqb\" onclick=\"fq(this)\"><span class=\"fqq\">What areas do you serve?</span><span class=\"fqi2\">+</span></button><div class=\"fqa\"><p>We serve clients across all of India and internationally. Whether in-person or remote we adapt completely to your location and needs.</p></div></div>\n"
"    </div>\n"
"  </div>\n"
"</section>\n"
"\n"
"<section id=\"contact\" style=\"background:" + svc_bg + "\">\n"
"  <div class=\"sec\">\n"
"    <div style=\"text-align:center;margin-bottom:16px\">\n"
"      <div class=\"lbl\">&#x2736; Contact Us</div>\n"
"      <h2 class=\"sh\" style=\"text-align:center\">Get In <span>Touch</span></h2>\n"
"      <p class=\"sb\" style=\"margin:10px auto;text-align:center\">We would love to hear from you. Reach out any time.</p>\n"
"    </div>\n"
"    <div class=\"ccg rev\">\n"
"      <div class=\"cc\"><div class=\"cci\">&#128222;</div><h4>Call Us</h4><a href=\"tel:" + phone + "\">" + phone + "</a></div>\n"
"      <div class=\"cc\"><div class=\"cci\">&#9993;&#65039;</div><h4>Email Us</h4><a href=\"mailto:" + email_addr + "\" style=\"word-break:break-all;font-size:0.74rem\">" + email_addr + "</a></div>\n"
"      <div class=\"cc\"><div class=\"cci\">&#128205;</div><h4>Visit Us</h4><p>" + address + "</p></div>\n"
"      <div class=\"cc\"><div class=\"cci\">&#9200;</div><h4>Hours</h4><p>" + hours + "</p></div>\n"
"      <div class=\"cc\"><div class=\"cci\">&#128172;</div><h4>WhatsApp</h4><a href=\"https://wa.me/" + wa + "\" target=\"_blank\">Chat Now &rarr;</a></div>\n"
"    </div>\n"
"    <div class=\"cf rev\">\n"
"      <h3 style=\"font-family:'" + f1 + "',serif;font-size:1.25rem;font-weight:800;color:var(--tx);margin-bottom:20px\">Send Us a Message</h3>\n"
"      <form onsubmit=\"hf(event)\">\n"
"        <div class=\"fg\">\n"
"          <div class=\"fg2\"><label>Full Name *</label><input type=\"text\" placeholder=\"Your full name\" required/></div>\n"
"          <div class=\"fg2\"><label>Phone Number *</label><input type=\"tel\" placeholder=\"+91 00000 00000\" required/></div>\n"
"        </div>\n"
"        <div class=\"fg2\" style=\"margin-bottom:14px\"><label>Email Address</label><input type=\"email\" placeholder=\"your@email.com\"/></div>\n"
"        <div class=\"fg2\" style=\"margin-bottom:14px\"><label>Subject</label><input type=\"text\" placeholder=\"How can we help you?\"/></div>\n"
"        <div class=\"fg2\" style=\"margin-bottom:18px\"><label>Message</label><textarea rows=\"4\" placeholder=\"Tell us about your requirements...\"></textarea></div>\n"
"        <button type=\"submit\" class=\"bp\" style=\"border:none;cursor:pointer\">Send Message &rarr;</button>\n"
"        <div class=\"fsucc\" id=\"fsucc\">&#x2705; Thank you! We will contact you within 24 hours.</div>\n"
"      </form>\n"
"    </div>\n"
"    <div style=\"margin-top:28px;border-radius:24px;overflow:hidden;border:1px solid var(--br)\" class=\"rev\">\n"
"      <iframe src=\"https://maps.google.com/maps?q=" + map_q + "&output=embed\" width=\"100%\" height=\"320\" style=\"border:0;display:block\" allowfullscreen loading=\"lazy\"></iframe>\n"
"    </div>\n"
"  </div>\n"
"</section>\n"
"\n"
"<section id=\"newsletter\" style=\"background:var(--bg);padding:70px 5%\">\n"
"  <div style=\"max-width:560px;margin:0 auto;text-align:center\" class=\"rev\">\n"
"    <div style=\"font-size:2.2rem;margin-bottom:10px\">&#128236;</div>\n"
"    <div class=\"lbl\" style=\"margin:0 auto 14px\">&#x2736; Newsletter</div>\n"
"    <h2 class=\"sh\" style=\"text-align:center\">Stay in the <span>Loop</span></h2>\n"
"    <p style=\"color:var(--mu);font-size:0.88rem;margin-top:8px\">Get updates, offers, and insights delivered to your inbox.</p>\n"
"    <form class=\"nlf\" onsubmit=\"hnl(event)\">\n"
"      <input type=\"email\" placeholder=\"Enter your email address\" required/>\n"
"      <button type=\"submit\">Subscribe &rarr;</button>\n"
"    </form>\n"
"    <div id=\"nls\" style=\"display:none;margin-top:12px;color:var(--pr);font-weight:600\">&#x2705; Subscribed! Welcome aboard.</div>\n"
"    <p style=\"color:var(--mu);font-size:0.7rem;margin-top:10px\">No spam. Unsubscribe anytime.</p>\n"
"  </div>\n"
"</section>\n"
"\n"
"<section style=\"padding:80px 5%;background:" + svc_bg + "\">\n"
"  <div class=\"ctab rev\">\n"
"    <h2>Ready to Get Started?</h2>\n"
"    <p>Join hundreds who already trust " + name + ". First consultation is completely free.</p>\n"
"    <div class=\"cbtns\">\n"
"      <a href=\"#contact\" class=\"cb1\">" + con["cta1"] + " &rarr;</a>\n"
"      <a href=\"tel:" + phone + "\" class=\"cb2\">&#128222; " + phone + "</a>\n"
"    </div>\n"
"  </div>\n"
"</section>\n"
"\n"
"<footer style=\"padding:60px 5% 90px;border-top:1px solid var(--br);background:" + svc_bg + "\">\n"
"  <div class=\"fgrid\">\n"
"    <div class=\"fbr\">\n"
"      <div class=\"flogo\">" + name + "</div>\n"
"      <p>" + con["sub"][:100] + "...</p>\n"
"      <div class=\"fsoc\">" + social_links + "</div>\n"
"    </div>\n"
"    <div class=\"fc\"><h4>Company</h4><a href=\"#about\">About Us</a><a href=\"#services\">" + con["sv_title"] + "</a><a href=\"#gallery\">Gallery</a><a href=\"#testimonials\">Reviews</a><a href=\"#faq\">FAQ</a></div>\n"
"    <div class=\"fc\"><h4>Services</h4>" + svc_footer + "</div>\n"
"    <div class=\"fc\"><h4>Contact</h4><a href=\"tel:" + phone + "\">&#128222; " + phone + "</a><a href=\"mailto:" + email_addr + "\">&#9993;&#65039; Email Us</a><a href=\"https://wa.me/" + wa + "\" target=\"_blank\">&#128172; WhatsApp</a><a href=\"#contact\">&#128205; " + address[:30] + "...</a><p style=\"color:var(--mu);font-size:0.72rem;margin-top:6px\">&#9200; " + hours + "</p></div>\n"
"  </div>\n"
"  <div class=\"fbot\">\n"
"    <p>&copy; 2024 " + name + ". All rights reserved.</p>\n"
"    <div><a href=\"#\">Privacy Policy</a><a href=\"#\">Terms of Service</a><a href=\"#\">Sitemap</a></div>\n"
"    <p>Built with <a href=\"https://dacexy.vercel.app\" style=\"color:var(--pr)\">Dacexy AI</a></p>\n"
"  </div>\n"
"</footer>\n"
"\n"
"<a href=\"https://wa.me/" + wa + "\" class=\"wab\" target=\"_blank\" title=\"Chat on WhatsApp\">" + wa_svg + "</a>\n"
"\n"
"<div class=\"scta\" id=\"scta\">\n"
"  <div class=\"scta-t\"><p>Ready to work with " + name + "?</p><p>Free consultation &mdash; contact us today.</p></div>\n"
"  <div class=\"scta-b\">\n"
"    <a href=\"tel:" + phone + "\" class=\"scta-b sb1\">&#128222; Call</a>\n"
"    <a href=\"#contact\" class=\"scta-b sb2\" onclick=\"document.getElementById('scta').style.transform='translateY(100%)'\">Get Started &rarr;</a>\n"
"  </div>\n"
"</div>\n"
"\n"
"<button id=\"btt\" onclick=\"window.scrollTo({top:0,behavior:'smooth'})\">&#x2191;</button>\n"
"\n"
"<div class=\"ckb\" id=\"ckb\">\n"
"  <p>&#127850; We use cookies to enhance your experience. By continuing, you agree to our <a href=\"#\" style=\"color:var(--pr)\">Privacy Policy</a>.</p>\n"
"  <div class=\"ckbs\">\n"
"    <button class=\"cka\" onclick=\"acc()\">Accept All</button>\n"
"    <button class=\"ckd\" onclick=\"acc()\">Decline</button>\n"
"  </div>\n"
"</div>\n"
"\n"
"<script>\n"
"window.addEventListener('load',function(){setTimeout(function(){document.getElementById('ldr').classList.add('out');},700);});\n"
"var nav=document.getElementById('nav'),scta=document.getElementById('scta'),btt=document.getElementById('btt');\n"
"window.addEventListener('scroll',function(){\n"
"  var y=window.scrollY;\n"
"  nav.classList.toggle('solid',y>60);\n"
"  scta.style.transform=y>400?'translateY(0)':'translateY(100%)';\n"
"  btt.style.display=y>500?'flex':'none';\n"
"  document.querySelectorAll('.lks a').forEach(function(a){\n"
"    var s=document.querySelector(a.getAttribute('href'));\n"
"    if(s){var r=s.getBoundingClientRect();a.classList.toggle('active',r.top<=100&&r.bottom>100);}\n"
"  });\n"
"});\n"
"function tm(){var m=document.getElementById('mob'),h=document.getElementById('hb');m.classList.toggle('o');h.classList.toggle('o');document.body.style.overflow=m.classList.contains('o')?'hidden':'';}\n"
"function cm(){document.getElementById('mob').classList.remove('o');document.getElementById('hb').classList.remove('o');document.body.style.overflow='';}\n"
"var ro=new IntersectionObserver(function(e){e.forEach(function(x){if(x.isIntersecting){x.target.classList.add('vis');ro.unobserve(x.target);}});},{threshold:0.08,rootMargin:'0px 0px -40px 0px'});\n"
"document.querySelectorAll('.rev').forEach(function(el){ro.observe(el);});\n"
"function fq(b){var a=b.nextElementSibling,i=b.querySelector('.fqi2'),op=a.style.display==='block';document.querySelectorAll('.fqa').forEach(function(x){x.style.display='none';});document.querySelectorAll('.fqi2').forEach(function(x){x.textContent='+';x.style.transform='';});if(!op){a.style.display='block';i.textContent='\\u2212';i.style.transform='rotate(45deg)';}}\n"
"function hf(e){e.preventDefault();var b=e.target.querySelector('button[type=\"submit\"]');b.innerHTML='&#x23F3; Sending...';b.disabled=true;setTimeout(function(){b.innerHTML='&#x2705; Sent!';document.getElementById('fsucc').style.display='block';e.target.reset();setTimeout(function(){b.innerHTML='Send Message &rarr;';b.disabled=false;document.getElementById('fsucc').style.display='none';},4000);},1500);}\n"
"function hnl(e){e.preventDefault();document.getElementById('nls').style.display='block';e.target.reset();}\n"
"function acc(){document.getElementById('ckb').classList.add('h');try{localStorage.setItem('ck','1');}catch(e){}}\n"
"try{if(localStorage.getItem('ck'))document.getElementById('ckb').classList.add('h');}catch(e){}\n"
"document.querySelectorAll('input,textarea').forEach(function(el){el.addEventListener('focus',function(){el.style.borderColor='var(--pr)';});el.addEventListener('blur',function(){el.style.borderColor='';});});\n"
"document.querySelectorAll('img[loading=\"lazy\"]').forEach(function(img){img.style.opacity='0';img.style.transition='opacity 0.5s ease';img.addEventListener('load',function(){img.style.opacity='1';});if(img.complete)img.style.opacity='1';});\n"
"</script>\n"
"</body>\n"
"</html>"
    )
    return html

async def generate_website(prompt, ai=None):
    name = extract_name(prompt)
    ud = extract_user_data(prompt)
    if ai is not None and needs_ai_generation(prompt):
        try:
            log.info("Using AI for custom website: " + prompt[:60])
            ai_prompt = build_ai_prompt(prompt, name, ud)
            messages = [
                {"role": "system", "content": "You are an expert web developer. Generate complete stunning HTML websites. Output ONLY raw HTML starting with <!DOCTYPE html>. No markdown, no explanation, no code blocks."},
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
            log.warning("AI generation failed, using premium template: " + str(e))
    log.info("Using premium template for: " + prompt[:60])
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
