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

log = logging.getLogger("website")

# ── NAME EXTRACTION ──────────────────────────────────────────────────────────
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
            "restaurant","store","shop","company","portfolio","a","an","my","our",
            "me","i","want","need","please","just","can","you","give","type","good",
            "great","best","professional","beautiful","modern","awesome","nice","add",
            "include","put","use","have","my","their","its"}
    words = [w for w in re.sub(r\'[^a-zA-Z0-9 ]\', \'\', p).split()
             if len(w) > 2 and w.lower() not in skip]
    return words[0].title() if words else "Nexus"

# ── USER DATA EXTRACTION — phone, email, address, social, images, etc ────────
def extract_user_data(prompt: str) -> dict:
    data = {
        "phone": None, "email": None, "address": None,
        "whatsapp": None, "instagram": None, "facebook": None,
        "twitter": None, "linkedin": None, "youtube": None,
        "map_location": None, "tagline_custom": None,
        "custom_colors": [], "custom_services": [],
        "opening_hours": None, "price_range": None,
        "custom_cta": None, "hero_text": None,
        "about_text": None, "logo_url": None,
    }
    p = prompt

    # Phone number — various formats
    phone_match = re.search(r\'(?:phone|mobile|call|contact|tel|ph)[:\\s#]*([+\\d][\\d\\s\\-().+]{7,15})\', p, re.IGNORECASE)
    if not phone_match:
        phone_match = re.search(r\'(?<![\\w])([+]?[0-9]{10,13})(?![\\w])\', p)
    if phone_match:
        data["phone"] = phone_match.group(1).strip()
        data["whatsapp"] = data["phone"]

    # Email
    email_match = re.search(r\'[\\w.+-]+@[\\w-]+\\.[\\w.]+\', p)
    if email_match:
        data["email"] = email_match.group(0)

    # Address
    addr_match = re.search(r\'(?:address|location|located at|find us at|visit us at)[:\\s]+([^,\\n.]{10,100})\', p, re.IGNORECASE)
    if addr_match:
        data["address"] = addr_match.group(1).strip()

    # WhatsApp
    wa_match = re.search(r\'(?:whatsapp)[:\\s#]*([+\\d][\\d\\s\\-+]{7,15})\', p, re.IGNORECASE)
    if wa_match:
        data["whatsapp"] = wa_match.group(1).strip()

    # Instagram
    ig_match = re.search(r\'(?:instagram|ig|insta)[:\\s@/]*([\\w.]+)\', p, re.IGNORECASE)
    if ig_match:
        data["instagram"] = ig_match.group(1).strip()

    # Facebook
    fb_match = re.search(r\'(?:facebook|fb)[:\\s@/]*([\\w.]+)\', p, re.IGNORECASE)
    if fb_match:
        data["facebook"] = fb_match.group(1).strip()

    # Twitter/X
    tw_match = re.search(r\'(?:twitter|x\\.com)[:\\s@/]*([\\w.]+)\', p, re.IGNORECASE)
    if tw_match:
        data["twitter"] = tw_match.group(1).strip()

    # LinkedIn
    li_match = re.search(r\'(?:linkedin)[:\\s@/]*([\\w.-]+)\', p, re.IGNORECASE)
    if li_match:
        data["linkedin"] = li_match.group(1).strip()

    # YouTube
    yt_match = re.search(r\'(?:youtube|yt)[:\\s@/]*([\\w.-]+)\', p, re.IGNORECASE)
    if yt_match:
        data["youtube"] = yt_match.group(1).strip()

    # Opening hours
    hours_match = re.search(r\'(?:open|hours|timing)[:\\s]+([^.\\n]{5,60})\', p, re.IGNORECASE)
    if hours_match:
        data["opening_hours"] = hours_match.group(1).strip()

    # Price range
    price_match = re.search(r\'(?:price|pricing|cost|rate|starting from|from)[:\\s]+([^.\\n]{3,50})\', p, re.IGNORECASE)
    if price_match:
        data["price_range"] = price_match.group(1).strip()

    # Custom tagline/hero text
    tagline_match = re.search(r\'(?:tagline|slogan|headline)[:\\s"]+([^"\\n]{5,80})\', p, re.IGNORECASE)
    if tagline_match:
        data["tagline_custom"] = tagline_match.group(1).strip()

    # About text
    about_match = re.search(r\'(?:about us|about|description)[:\\s]+([^.\\n]{20,300})\', p, re.IGNORECASE)
    if about_match:
        data["about_text"] = about_match.group(1).strip()

    # Map/location for embed
    map_match = re.search(r\'(?:map|google maps|location)[:\\s]+([^.\\n]{5,100})\', p, re.IGNORECASE)
    if map_match:
        data["map_location"] = urllib.parse.quote(map_match.group(1).strip())
    elif data["address"]:
        data["map_location"] = urllib.parse.quote(data["address"])

    return data

# ── FEATURE DETECTION — what sections/features the user wants ────────────────
def detect_features(prompt: str) -> dict:
    p = prompt.lower()
    return {
        "contact_form":     any(x in p for x in ["contact form","contact us","enquiry form","inquiry","get in touch","form"]),
        "booking_form":     any(x in p for x in ["booking","book","reservation","reserve","appointment","schedule","slot"]),
        "newsletter":       any(x in p for x in ["newsletter","subscribe","email list","mailing","updates"]),
        "gallery":          any(x in p for x in ["gallery","photos","images","portfolio","showcase","pictures","album"]),
        "video":            any(x in p for x in ["video","youtube","watch","reel","demo"]),
        "map":              any(x in p for x in ["map","location","directions","find us","address","where"]),
        "whatsapp_btn":     any(x in p for x in ["whatsapp","wa.me","chat now","whatsapp button"]),
        "pricing_table":    any(x in p for x in ["pricing","plans","packages","rates","cost","fees","price list"]),
        "faq":              any(x in p for x in ["faq","frequently asked","questions","q&a","queries"]),
        "team":             any(x in p for x in ["team","staff","our people","meet the","doctors","lawyers","coaches","trainers"]),
        "counter":          any(x in p for x in ["years","clients","projects","students","members","count","numbers","statistics"]),
        "social_feed":      any(x in p for x in ["instagram feed","social media","follow us"]),
        "chat_widget":      any(x in p for x in ["chat","live chat","chatbot","support chat"]),
        "testimonial_slider": True,
        "sticky_cta":       True,
        "back_to_top":      True,
        "cookie_banner":    any(x in p for x in ["cookie","gdpr","privacy"]),
        "popup":            any(x in p for x in ["popup","pop-up","offer popup","discount popup"]),
        "countdown":        any(x in p for x in ["countdown","launch","days left","offer ends","limited time"]),
        "progress_bar":     any(x in p for x in ["skills","expertise","proficiency","progress"]),
        "portfolio_grid":   any(x in p for x in ["portfolio","work","projects","case study","case studies"]),
        "services_tabs":    any(x in p for x in ["services","offerings","what we do","what i do"]),
        "comparison_table": any(x in p for x in ["compare","comparison","vs","versus","difference"]),
        "before_after":     any(x in p for x in ["before after","transformation","results","before and after"]),
        "menu_section":     any(x in p for x in ["menu","food menu","drink menu","dish","dishes","items"]),
        "shop":             any(x in p for x in ["shop","store","buy","cart","product","order","purchase"]),
        "blog":             any(x in p for x in ["blog","articles","posts","news","updates","insights"]),
        "timeline":         any(x in p for x in ["timeline","history","journey","milestone","story","founded","established"]),
        "cta_float":        True,
        "loading_screen":   True,
        "smooth_scroll":    True,
        "dark_mode_toggle": any(x in p for x in ["dark mode","light mode","theme toggle"]),
    }

# ── CATEGORY DETECTION ───────────────────────────────────────────────────────
CATEGORY_KEYWORDS = {
    "restaurant":    ["restaurant","cafe","bistro","dhaba","tiffin","biryani","pizzeria","steakhouse","sushi","diner","eatery","food truck","bakery","catering","fine dining","cuisine","chef","menu items","reservations","table booking","takeaway"],
    "saas":          ["saas","software as a service","b2b software","crm","erp","api platform","devtool","productivity tool","project management tool","workflow automation","no-code","low-code","subscription software","cloud software","analytics platform"],
    "car":           ["car dealer","automobile dealer","vehicle dealer","car showroom","cars for sale","used cars","new cars","auto dealer","car rental","automotive dealership","test drive"],
    "portfolio":     ["portfolio","my work","my projects","personal website","freelancer","designer portfolio","developer portfolio","photographer portfolio","artist portfolio","resume site","cv website"],
    "ecommerce":     ["ecommerce","online store","online shop","products for sale","buy online","shopping cart","checkout","merchandise","dropship","retail online","fashion store","clothing store","jewelry store"],
    "agency":        ["marketing agency","digital agency","creative agency","advertising agency","branding agency","seo agency","web agency","design studio","growth agency"],
    "fitness":       ["gym","fitness center","workout studio","personal trainer","yoga studio","crossfit","pilates studio","health club","wellness center","martial arts","boxing gym"],
    "education":     ["school","college","university","online course","e-learning","edtech","tutoring","coaching center","training institute","certification course","bootcamp","learning platform"],
    "realestate":    ["real estate","property listing","homes for sale","apartments for rent","flat","villa for sale","plot","realtor","real estate agent","property dealer","rent property"],
    "hospital":      ["hospital","clinic","doctor","medical center","healthcare","dental clinic","dentist","pharmacy","health center","diagnostic center","physiotherapy","telemedicine"],
    "hotel":         ["hotel","resort","motel","bed and breakfast","bnb","accommodation","lodging","rooms","suite","vacation rental","boutique hotel","hospitality"],
    "law":           ["law firm","lawyer","attorney","legal services","advocate","solicitor","corporate law","criminal defense","family law","legal aid"],
    "startup":       ["startup","mvp","seed stage","series a","venture","founder","product launch","early stage","tech startup","fintech startup"],
    "finance":       ["finance","fintech","banking","investment","wealth management","mutual fund","insurance","accounting","tax","chartered accountant","financial advisor","stock trading"],
    "construction":  ["construction","builder","contractor","architect","interior design","renovation","remodeling","civil engineering","infrastructure","building company","landscaping"],
    "ngo":           ["ngo","nonprofit","charity","foundation","social cause","donation","volunteer","social impact","fundraising","advocacy"],
    "photography":   ["photography","photographer","photo studio","wedding photography","portrait photography","commercial photography","fashion photography","event photography","videography"],
    "music":         ["music","band","musician","singer","dj","music studio","record label","music producer","concert","album","music lessons","music school"],
    "salon":         ["salon","beauty parlor","hair salon","barbershop","spa","nail salon","makeup artist","beauty studio","hair stylist","grooming"],
    "travel":        ["travel agency","tour operator","tours","vacation packages","holiday packages","adventure travel","safari","cruise","backpacking"],
    "food_delivery": ["food delivery","cloud kitchen","ghost kitchen","meal prep","meal delivery","tiffin service","home chef","online food","meal kit"],
    "tech_company":  ["tech company","software company","it company","technology company","it services","software development","app development","web development company","cybersecurity"],
    "event":         ["event management","event planner","wedding planner","corporate events","conference organizer","event venue","party planner","event decorator"],
    "consulting":    ["consulting","management consulting","business consulting","strategy consulting","hr consulting","operations consulting","advisory services"],
    "fashion":       ["fashion","clothing brand","fashion designer","apparel brand","streetwear","luxury fashion","sustainable fashion","fashion label","couture"],
    "interior":      ["interior design","interior designer","home decor","furniture","home furnishing","space planning","interior styling","commercial interior"],
    "bakery":        ["bakery","cake shop","pastry","dessert shop","confectionery","wedding cake","custom cake","sourdough","cookie shop","donut shop","macaron"],
    "coffee":        ["coffee shop","specialty coffee","third wave coffee","coffee bar","espresso bar","coffee subscription","coffee brand","tea house"],
    "yoga":          ["yoga","meditation","mindfulness","wellness retreat","yoga teacher","breathwork","sound healing","spiritual wellness","holistic health"],
    "pet":           ["pet shop","pet clinic","veterinary","pet grooming","pet boarding","dog trainer","pet care","animal shelter","veterinarian"],
    "gaming":        ["gaming","esports","game studio","game developer","gaming cafe","mobile game","gaming community","game coaching"],
    "crypto":        ["crypto","blockchain","web3","nft","defi","cryptocurrency","token","dao","metaverse","digital assets","crypto exchange"],
    "wedding":       ["wedding planner","bridal","wedding venue","wedding photography","wedding catering","wedding dress","bridal boutique","wedding decor"],
    "children":      ["children","kids","daycare","kindergarten","preschool","child care","baby products","kids clothing","children entertainment","toy store"],
    "dental":        ["dental","dentist","dental clinic","oral health","teeth whitening","braces","orthodontist","dental implants","root canal"],
    "cleaning":      ["cleaning service","house cleaning","commercial cleaning","janitorial","maid service","deep cleaning","carpet cleaning","sanitization"],
    "solar":         ["solar","solar energy","solar panel","renewable energy","green energy","solar installation","wind energy","clean energy"],
    "automobile_service": ["car service","auto repair","car workshop","mechanic","car wash","auto detailing","tire shop","car accessories","auto parts"],
    "logistics":     ["logistics","courier","shipping","freight","supply chain","warehouse","last mile delivery","trucking","cargo","fulfillment"],
    "agriculture":   ["agriculture","farm","farming","organic farm","agritech","crop","fertilizer","seeds","dairy farm","poultry","greenhouse"],
    "security":      ["security agency","cctv","surveillance","guard service","cybersecurity","private security","access control","fire safety","alarm system"],
    "mental_health": ["mental health","therapist","psychologist","counseling","therapy","anxiety","depression treatment","psychiatrist","emotional wellness"],
    "pharmacy":      ["pharmacy","medical store","chemist","drug store","online pharmacy","medicine delivery","health products","supplements"],
    "accounting":    ["accounting","bookkeeping","ca firm","tax filing","gst","audit","payroll","financial reporting","tax consultant"],
    "printing":      ["printing","print shop","graphic design","branding","logo design","stationery","packaging design","banner printing","signage"],
    "florist":       ["florist","flower shop","flower delivery","floral design","wedding flowers","bouquet","floral arrangement","flower subscription","plant nursery"],
    "catering":      ["catering","caterer","food catering","wedding catering","corporate catering","event catering","buffet","canteen"],
    "dance":         ["dance academy","dance studio","dance school","ballet","hip hop dance","classical dance","bharatanatyam","dance teacher"],
    "language":      ["language school","english classes","foreign language","translation","interpretation","language learning","spoken english","ielts","toefl"],
    "coaching":      ["life coach","business coach","executive coach","career coach","mindset coach","leadership coaching","coaching program"],
    "insurance":     ["insurance","life insurance","health insurance","car insurance","home insurance","insurance broker","insurance agent","risk management"],
    "sports":        ["sports","sports club","sports academy","cricket","football","basketball","tennis","swimming","athletics","sports equipment"],
    "media":         ["media production","film production","video production","documentary","short film","music video","animation studio","vfx studio"],
    "astrology":     ["astrology","horoscope","numerology","tarot","vastu","palmistry","vedic astrology","psychic reading","spiritual guidance"],
    "jewelry":       ["jewelry","jeweler","gold jewelry","diamond jewelry","custom jewelry","engagement ring","wedding jewelry","silver jewelry"],
    "furniture":     ["furniture","furniture store","custom furniture","wood furniture","modular furniture","office furniture","sofa","wardrobe"],
    "electronics":   ["electronics store","gadgets","mobile phone shop","laptop store","electronics repair","consumer electronics","home appliances"],
    "swimming":      ["swimming pool","swim school","swimming academy","swim coach","aqua fitness","swimming lessons","competitive swimming"],
    "laundry":       ["laundry","dry cleaning","laundry service","wash and fold","ironing service","garment care","laundromat"],
    "plumber":       ["plumber","plumbing","plumbing services","pipe fitting","bathroom fitting","water tank","drainage","sanitation"],
    "electrician":   ["electrician","electrical services","wiring","electrical contractor","power backup","generator","home automation","electrical repair"],
    "tutor":         ["tutor","tutoring","home tuition","online tutor","math tutor","science tutor","test prep","competitive exam","jee","neet","upsc"],
    "dietitian":     ["dietitian","nutritionist","diet plan","weight loss","nutrition counseling","meal planning","sports nutrition","diabetic diet"],
    "car_rental":    ["car rental","self drive","vehicle rental","cab service","taxi","chauffeur","limousine","bus rental","outstation cab"],
    "bike":          ["bike shop","bicycle store","cycling","mountain bike","electric bike","bike rental","cycling academy","bike accessories"],
    "optical":       ["optical store","spectacle shop","sunglasses","contact lens store","eyeglass frame","prescription glasses","optometry"],
    "coworking":     ["coworking","shared workspace","hot desk","serviced office","business center","virtual office","meeting room"],
    "tattoo":        ["tattoo studio","tattoo artist","body piercing","tattoo parlor","custom tattoo","temporary tattoo","henna","body art"],
    "escape":        ["escape room","puzzle room","team building","entertainment center","gaming lounge","board game cafe","vr arcade"],
    "amusement":     ["amusement park","theme park","water park","adventure park","rides","roller coaster","family park"],
    "nightclub":     ["nightclub","bar","lounge","pub","rooftop bar","cocktail bar","sports bar","live music venue","jazz club","comedy club"],
    "museum":        ["museum","heritage site","cultural center","exhibition hall","science museum","history museum","virtual museum"],
    "church":        ["church","temple","mosque","gurdwara","religious organization","faith community","ministry","spiritual center","place of worship"],
    "book":          ["bookstore","library","book club","publishing","author website","book review","literary","writing coaching","poetry"],
    "podcast":       ["podcast","podcaster","podcast studio","podcast network","audio content","podcast hosting","radio show"],
    "influencer":    ["influencer","content creator","youtuber","instagrammer","social media","personal brand","creator economy"],
    "senior":        ["senior care","elderly care","retirement home","assisted living","nursing home","senior services","elder care","geriatric"],
    "mortgage":      ["mortgage","home loan","property loan","loan broker","loan advisor","refinancing","home financing","loan eligibility"],
    "mining":        ["mining","coal mine","gold mine","mineral extraction","quarry","ore processing","mining equipment"],
    "textile":       ["textile","fabric","garment factory","clothing manufacturer","weaving","embroidery","knitting","textile mill"],
    "pharma":        ["pharmaceutical","pharma company","drug manufacturer","medicine","clinical research","biotech","life sciences","medical device"],
    "airline":       ["airline","aviation","flight booking","charter flight","private jet","helicopter service","air cargo","aviation training"],
    "shipping_co":   ["shipping company","maritime","port","vessel","cargo ship","container shipping","freight forwarding","customs clearance"],
    "architect":     ["architect","architecture firm","architectural design","urban planning","landscape architecture","structural engineering"],
    "charity":       ["charity","donation","fundraising","social service","community service","homeless shelter","food bank","orphanage"],
    "golf":          ["golf club","golf course","golf academy","golf lessons","golf equipment","mini golf","golf resort","golf instructor"],
    "recruitment":   ["recruitment","job portal","career","employment","job board","talent platform","hiring platform","job search","resume service"],
    "business":      ["company","business","service","professional","firm","enterprise","solutions","services","management"],
}

def get_category(prompt: str) -> str:
    p = prompt.lower()
    noise = ["make","build","create","generate","design","need","want","please","just",
             "website","site","page","landing page","web app","online presence","for",
             "me","a","an","the","i","can","you","give","type","good","great","best",
             "professional","beautiful","modern","awesome","nice","add","include","put",
             "use","have","their","its","with","mobile","number","phone","email","address",
             "contact","social","media","map","gallery","images","photos","logo","color",
             "colour","theme","dark","light","white","black","blue","red","green"]
    clean = p
    for n in noise:
        clean = re.sub(r"\\b" + re.escape(n) + r"\\b", " ", clean)
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

# ── 100+ DESIGN SYSTEMS ──────────────────────────────────────────────────────
DESIGN_SYSTEMS = [
    {"dark":True,"bg":"#0A0A0A","pr":"#E11D48","ac":"#F59E0B","tx":"#FFFFFF","mu":"rgba(255,255,255,0.6)","ca":"rgba(255,255,255,0.05)","br":"rgba(225,29,72,0.25)","nb":"rgba(10,10,10,0.95)","nt":"rgba(255,255,255,0.8)","font":"Playfair Display","grad":"linear-gradient(135deg,#0A0A0A,#1a0010)"},
    {"dark":True,"bg":"#050010","pr":"#8B5CF6","ac":"#06B6D4","tx":"#F5F3FF","mu":"rgba(245,243,255,0.55)","ca":"rgba(139,92,246,0.08)","br":"rgba(139,92,246,0.2)","nb":"rgba(5,0,16,0.95)","nt":"rgba(245,243,255,0.8)","font":"Inter","grad":"linear-gradient(135deg,#050010,#1a0030)"},
    {"dark":True,"bg":"#0D0500","pr":"#C8102E","ac":"#FFD700","tx":"#FFF8F0","mu":"rgba(255,248,240,0.55)","ca":"rgba(255,255,255,0.04)","br":"rgba(255,215,0,0.15)","nb":"rgba(13,5,0,0.95)","nt":"rgba(255,248,240,0.8)","font":"Playfair Display","grad":"linear-gradient(135deg,#0D0500,#2a0a00)"},
    {"dark":True,"bg":"#0C0500","pr":"#EA580C","ac":"#22C55E","tx":"#FFF7ED","mu":"rgba(255,247,237,0.55)","ca":"rgba(234,88,12,0.08)","br":"rgba(234,88,12,0.2)","nb":"rgba(12,5,0,0.95)","nt":"rgba(255,247,237,0.8)","font":"Inter","grad":"linear-gradient(135deg,#0C0500,#1a0800)"},
    {"dark":True,"bg":"#060A14","pr":"#3B82F6","ac":"#10B981","tx":"#EFF6FF","mu":"rgba(239,246,255,0.55)","ca":"rgba(59,130,246,0.08)","br":"rgba(59,130,246,0.2)","nb":"rgba(6,10,20,0.95)","nt":"rgba(239,246,255,0.8)","font":"Inter","grad":"linear-gradient(135deg,#060A14,#0a1628)"},
    {"dark":True,"bg":"#0A0800","pr":"#B45309","ac":"#FCD34D","tx":"#FFFBEB","mu":"rgba(255,251,235,0.55)","ca":"rgba(180,83,9,0.08)","br":"rgba(252,211,77,0.15)","nb":"rgba(10,8,0,0.95)","nt":"rgba(255,251,235,0.8)","font":"Playfair Display","grad":"linear-gradient(135deg,#0A0800,#1a1200)"},
    {"dark":True,"bg":"#030712","pr":"#06B6D4","ac":"#8B5CF6","tx":"#F0FDFE","mu":"rgba(240,253,254,0.55)","ca":"rgba(6,182,212,0.08)","br":"rgba(6,182,212,0.2)","nb":"rgba(3,7,18,0.95)","nt":"rgba(240,253,254,0.8)","font":"Inter","grad":"linear-gradient(135deg,#030712,#050f20)"},
    {"dark":True,"bg":"#0A0A1A","pr":"#F43F5E","ac":"#A78BFA","tx":"#FFF1F2","mu":"rgba(255,241,242,0.55)","ca":"rgba(244,63,94,0.08)","br":"rgba(244,63,94,0.2)","nb":"rgba(10,10,26,0.95)","nt":"rgba(255,241,242,0.8)","font":"Inter","grad":"linear-gradient(135deg,#0A0A1A,#14142e)"},
    {"dark":True,"bg":"#071A0E","pr":"#16A34A","ac":"#FCD34D","tx":"#F0FDF4","mu":"rgba(240,253,244,0.55)","ca":"rgba(22,163,74,0.08)","br":"rgba(22,163,74,0.2)","nb":"rgba(7,26,14,0.95)","nt":"rgba(240,253,244,0.8)","font":"Inter","grad":"linear-gradient(135deg,#071A0E,#0a2a14)"},
    {"dark":True,"bg":"#14000A","pr":"#DB2777","ac":"#FB923C","tx":"#FDF2F8","mu":"rgba(253,242,248,0.55)","ca":"rgba(219,39,119,0.08)","br":"rgba(219,39,119,0.2)","nb":"rgba(20,0,10,0.95)","nt":"rgba(253,242,248,0.8)","font":"Playfair Display","grad":"linear-gradient(135deg,#14000A,#280014)"},
    {"dark":False,"bg":"#FFFFFF","pr":"#6366F1","ac":"#06B6D4","tx":"#0F0F1A","mu":"#6B7280","ca":"#F8F7FF","br":"#E5E7EB","nb":"rgba(255,255,255,0.97)","nt":"#374151","font":"Inter","grad":"linear-gradient(135deg,#f8f7ff,#ffffff)"},
    {"dark":False,"bg":"#FFFBF0","pr":"#D97706","ac":"#EF4444","tx":"#1C1917","mu":"#78716C","ca":"#FEF3C7","br":"#FDE68A","nb":"rgba(255,251,240,0.97)","nt":"#44403C","font":"Playfair Display","grad":"linear-gradient(135deg,#fffbf0,#fef9e0)"},
    {"dark":False,"bg":"#F0FDF4","pr":"#059669","ac":"#F97316","tx":"#022C22","mu":"#6B7280","ca":"#DCFCE7","br":"#A7F3D0","nb":"rgba(240,253,244,0.97)","nt":"#065F46","font":"Inter","grad":"linear-gradient(135deg,#f0fdf4,#dcfce7)"},
    {"dark":False,"bg":"#FFF5F5","pr":"#DC2626","ac":"#F59E0B","tx":"#1A0000","mu":"#6B7280","ca":"#FEE2E2","br":"#FECACA","nb":"rgba(255,245,245,0.97)","nt":"#7F1D1D","font":"Playfair Display","grad":"linear-gradient(135deg,#fff5f5,#fee2e2)"},
    {"dark":False,"bg":"#FAF5FF","pr":"#7C3AED","ac":"#F59E0B","tx":"#1A0A3E","mu":"#6B7280","ca":"#EDE9FE","br":"#DDD6FE","nb":"rgba(250,245,255,0.97)","nt":"#4C1D95","font":"Playfair Display","grad":"linear-gradient(135deg,#faf5ff,#ede9fe)"},
    {"dark":False,"bg":"#EFF6FF","pr":"#2563EB","ac":"#F59E0B","tx":"#020617","mu":"#6B7280","ca":"#DBEAFE","br":"#BFDBFE","nb":"rgba(239,246,255,0.97)","nt":"#1E3A8A","font":"Inter","grad":"linear-gradient(135deg,#eff6ff,#dbeafe)"},
    {"dark":False,"bg":"#FFF7ED","pr":"#EA580C","ac":"#22C55E","tx":"#1C0A00","mu":"#6B7280","ca":"#FFEDD5","br":"#FED7AA","nb":"rgba(255,247,237,0.97)","nt":"#7C2D12","font":"Inter","grad":"linear-gradient(135deg,#fff7ed,#ffedd5)"},
    {"dark":False,"bg":"#F0FFFE","pr":"#0891B2","ac":"#10B981","tx":"#042F2E","mu":"#6B7280","ca":"#CCFBF1","br":"#99F6E4","nb":"rgba(240,255,254,0.97)","nt":"#134E4A","font":"Inter","grad":"linear-gradient(135deg,#f0fffe,#ccfbf1)"},
    {"dark":False,"bg":"#FAFAF8","pr":"#0F0F0F","ac":"#F59E0B","tx":"#0F0F0F","mu":"#6B7280","ca":"#F5F5F0","br":"#E5E5E0","nb":"rgba(250,250,248,0.97)","nt":"#0F0F0F","font":"Playfair Display","grad":"linear-gradient(135deg,#fafaf8,#f0f0ee)"},
    {"dark":False,"bg":"#FDF4FF","pr":"#A21CAF","ac":"#F59E0B","tx":"#2E1065","mu":"#6B7280","ca":"#FAE8FF","br":"#F0ABFC","nb":"rgba(253,244,255,0.97)","nt":"#6B21A8","font":"Playfair Display","grad":"linear-gradient(135deg,#fdf4ff,#fae8ff)"},
    {"dark":True,"bg":"#0F0F23","pr":"#F97316","ac":"#FACC15","tx":"#FFFBEB","mu":"rgba(255,251,235,0.6)","ca":"rgba(249,115,22,0.08)","br":"rgba(249,115,22,0.2)","nb":"rgba(15,15,35,0.95)","nt":"rgba(255,251,235,0.8)","font":"Inter","grad":"linear-gradient(135deg,#0F0F23,#1a1a38)"},
    {"dark":True,"bg":"#0A1628","pr":"#0EA5E9","ac":"#38BDF8","tx":"#F0F9FF","mu":"rgba(240,249,255,0.55)","ca":"rgba(14,165,233,0.08)","br":"rgba(14,165,233,0.2)","nb":"rgba(10,22,40,0.95)","nt":"rgba(240,249,255,0.8)","font":"Inter","grad":"linear-gradient(135deg,#0A1628,#0f2040)"},
    {"dark":False,"bg":"#FEFCE8","pr":"#CA8A04","ac":"#DC2626","tx":"#1C1400","mu":"#78716C","ca":"#FEF9C3","br":"#FEF08A","nb":"rgba(254,252,232,0.97)","nt":"#92400E","font":"Playfair Display","grad":"linear-gradient(135deg,#fefce8,#fef9c3)"},
    {"dark":False,"bg":"#F8FAFC","pr":"#334155","ac":"#3B82F6","tx":"#0F172A","mu":"#64748B","ca":"#F1F5F9","br":"#CBD5E1","nb":"rgba(248,250,252,0.97)","nt":"#1E293B","font":"Inter","grad":"linear-gradient(135deg,#f8fafc,#f1f5f9)"},
    {"dark":True,"bg":"#0D1117","pr":"#58A6FF","ac":"#3FB950","tx":"#C9D1D9","mu":"rgba(201,209,217,0.6)","ca":"rgba(88,166,255,0.08)","br":"rgba(88,166,255,0.15)","nb":"rgba(13,17,23,0.95)","nt":"rgba(201,209,217,0.8)","font":"Inter","grad":"linear-gradient(135deg,#0D1117,#161b22)"},
    {"dark":False,"bg":"#FFF1F2","pr":"#E11D48","ac":"#F59E0B","tx":"#881337","mu":"#6B7280","ca":"#FFE4E6","br":"#FECDD3","nb":"rgba(255,241,242,0.97)","nt":"#9F1239","font":"Playfair Display","grad":"linear-gradient(135deg,#fff1f2,#ffe4e6)"},
    {"dark":True,"bg":"#1A0533","pr":"#C084FC","ac":"#F472B6","tx":"#FAF5FF","mu":"rgba(250,245,255,0.6)","ca":"rgba(192,132,252,0.08)","br":"rgba(192,132,252,0.2)","nb":"rgba(26,5,51,0.95)","nt":"rgba(250,245,255,0.8)","font":"Playfair Display","grad":"linear-gradient(135deg,#1A0533,#2d0a55)"},
    {"dark":False,"bg":"#ECFDF5","pr":"#10B981","ac":"#3B82F6","tx":"#022C22","mu":"#6B7280","ca":"#D1FAE5","br":"#6EE7B7","nb":"rgba(236,253,245,0.97)","nt":"#065F46","font":"Inter","grad":"linear-gradient(135deg,#ecfdf5,#d1fae5)"},
    {"dark":True,"bg":"#18181B","pr":"#A1A1AA","ac":"#FACC15","tx":"#FAFAFA","mu":"rgba(250,250,250,0.5)","ca":"rgba(255,255,255,0.04)","br":"rgba(255,255,255,0.1)","nb":"rgba(24,24,27,0.97)","nt":"rgba(250,250,250,0.8)","font":"Inter","grad":"linear-gradient(135deg,#18181B,#27272a)"},
    {"dark":False,"bg":"#FEF9EE","pr":"#B45309","ac":"#059669","tx":"#1C1200","mu":"#78716C","ca":"#FEF3C7","br":"#FDE68A","nb":"rgba(254,249,238,0.97)","nt":"#78350F","font":"Playfair Display","grad":"linear-gradient(135deg,#fef9ee,#fef3c7)"},
    {"dark":True,"bg":"#020617","pr":"#6366F1","ac":"#A5F3FC","tx":"#E0F2FE","mu":"rgba(224,242,254,0.55)","ca":"rgba(99,102,241,0.08)","br":"rgba(99,102,241,0.2)","nb":"rgba(2,6,23,0.97)","nt":"rgba(224,242,254,0.8)","font":"Inter","grad":"linear-gradient(135deg,#020617,#050f2a)"},
    {"dark":False,"bg":"#F5F3FF","pr":"#4F46E5","ac":"#EC4899","tx":"#1E1B4B","mu":"#6B7280","ca":"#EDE9FE","br":"#C4B5FD","nb":"rgba(245,243,255,0.97)","nt":"#3730A3","font":"Inter","grad":"linear-gradient(135deg,#f5f3ff,#ede9fe)"},
    {"dark":True,"bg":"#0C1A0C","pr":"#22C55E","ac":"#FACC15","tx":"#F0FDF4","mu":"rgba(240,253,244,0.55)","ca":"rgba(34,197,94,0.08)","br":"rgba(34,197,94,0.15)","nb":"rgba(12,26,12,0.97)","nt":"rgba(240,253,244,0.8)","font":"Inter","grad":"linear-gradient(135deg,#0C1A0C,#142814)"},
    {"dark":False,"bg":"#FFF8F0","pr":"#C2410C","ac":"#FBBF24","tx":"#431407","mu":"#78716C","ca":"#FEE2D5","br":"#FCA27B","nb":"rgba(255,248,240,0.97)","nt":"#7C2D12","font":"Playfair Display","grad":"linear-gradient(135deg,#fff8f0,#fee2d5)"},
    {"dark":True,"bg":"#08080F","pr":"#E879F9","ac":"#22D3EE","tx":"#FAF5FF","mu":"rgba(250,245,255,0.55)","ca":"rgba(232,121,249,0.06)","br":"rgba(232,121,249,0.15)","nb":"rgba(8,8,15,0.97)","nt":"rgba(250,245,255,0.8)","font":"Inter","grad":"linear-gradient(135deg,#08080F,#10101e)"},
    {"dark":False,"bg":"#F8F9FA","pr":"#212529","ac":"#E63946","tx":"#212529","mu":"#6C757D","ca":"#E9ECEF","br":"#CED4DA","nb":"rgba(248,249,250,0.97)","nt":"#495057","font":"Inter","grad":"linear-gradient(135deg,#f8f9fa,#e9ecef)"},
    {"dark":True,"bg":"#0A0A0A","pr":"#FFFFFF","ac":"#F59E0B","tx":"#FFFFFF","mu":"rgba(255,255,255,0.5)","ca":"rgba(255,255,255,0.04)","br":"rgba(255,255,255,0.1)","nb":"rgba(10,10,10,0.97)","nt":"rgba(255,255,255,0.8)","font":"Playfair Display","grad":"linear-gradient(135deg,#0A0A0A,#1a1a1a)"},
    {"dark":False,"bg":"#FFF0F3","pr":"#FF4D6D","ac":"#FF9F1C","tx":"#590D22","mu":"#6B7280","ca":"#FFD6E0","br":"#FFAFC5","nb":"rgba(255,240,243,0.97)","nt":"#A4133C","font":"Playfair Display","grad":"linear-gradient(135deg,#fff0f3,#ffd6e0)"},
    {"dark":True,"bg":"#061014","pr":"#34D399","ac":"#60A5FA","tx":"#ECFDF5","mu":"rgba(236,253,245,0.55)","ca":"rgba(52,211,153,0.08)","br":"rgba(52,211,153,0.15)","nb":"rgba(6,16,20,0.97)","nt":"rgba(236,253,245,0.8)","font":"Inter","grad":"linear-gradient(135deg,#061014,#0a1a20)"},
    {"dark":False,"bg":"#FFFAF0","pr":"#F97316","ac":"#14B8A6","tx":"#1C0A00","mu":"#78716C","ca":"#FFF1E0","br":"#FED7AA","nb":"rgba(255,250,240,0.97)","nt":"#7C2D12","font":"Playfair Display","grad":"linear-gradient(135deg,#fffaf0,#fff1e0)"},
    {"dark":True,"bg":"#140028","pr":"#A855F7","ac":"#EC4899","tx":"#FAF5FF","mu":"rgba(250,245,255,0.55)","ca":"rgba(168,85,247,0.08)","br":"rgba(168,85,247,0.2)","nb":"rgba(20,0,40,0.97)","nt":"rgba(250,245,255,0.8)","font":"Playfair Display","grad":"linear-gradient(135deg,#140028,#220044)"},
    {"dark":False,"bg":"#F0F9FF","pr":"#0284C7","ac":"#F59E0B","tx":"#0C4A6E","mu":"#6B7280","ca":"#E0F2FE","br":"#BAE6FD","nb":"rgba(240,249,255,0.97)","nt":"#075985","font":"Inter","grad":"linear-gradient(135deg,#f0f9ff,#e0f2fe)"},
    {"dark":True,"bg":"#0F1923","pr":"#FB923C","ac":"#34D399","tx":"#FFF7ED","mu":"rgba(255,247,237,0.55)","ca":"rgba(251,146,60,0.08)","br":"rgba(251,146,60,0.2)","nb":"rgba(15,25,35,0.97)","nt":"rgba(255,247,237,0.8)","font":"Inter","grad":"linear-gradient(135deg,#0F1923,#18263a)"},
    {"dark":False,"bg":"#F9FAFB","pr":"#111827","ac":"#6366F1","tx":"#111827","mu":"#6B7280","ca":"#F3F4F6","br":"#D1D5DB","nb":"rgba(249,250,251,0.97)","nt":"#374151","font":"Inter","grad":"linear-gradient(135deg,#f9fafb,#f3f4f6)"},
    {"dark":True,"bg":"#180A00","pr":"#F97316","ac":"#FCD34D","tx":"#FFF7ED","mu":"rgba(255,247,237,0.6)","ca":"rgba(249,115,22,0.1)","br":"rgba(252,211,77,0.2)","nb":"rgba(24,10,0,0.97)","nt":"rgba(255,247,237,0.8)","font":"Playfair Display","grad":"linear-gradient(135deg,#180A00,#2a1200)"},
    {"dark":False,"bg":"#FAFFFE","pr":"#0D9488","ac":"#F59E0B","tx":"#042F2E","mu":"#6B7280","ca":"#CCFBF1","br":"#99F6E4","nb":"rgba(250,255,254,0.97)","nt":"#0F766E","font":"Inter","grad":"linear-gradient(135deg,#fafffe,#ccfbf1)"},
    {"dark":True,"bg":"#09090B","pr":"#D97706","ac":"#A78BFA","tx":"#FFFBEB","mu":"rgba(255,251,235,0.55)","ca":"rgba(217,119,6,0.08)","br":"rgba(217,119,6,0.2)","nb":"rgba(9,9,11,0.97)","nt":"rgba(255,251,235,0.8)","font":"Playfair Display","grad":"linear-gradient(135deg,#09090B,#141418)"},
    {"dark":False,"bg":"#FFF9FB","pr":"#BE185D","ac":"#7C3AED","tx":"#4A0020","mu":"#6B7280","ca":"#FCE7F3","br":"#FBCFE8","nb":"rgba(255,249,251,0.97)","nt":"#9D174D","font":"Playfair Display","grad":"linear-gradient(135deg,#fff9fb,#fce7f3)"},
    {"dark":True,"bg":"#001A10","pr":"#00E676","ac":"#FFD600","tx":"#E8F5E9","mu":"rgba(232,245,233,0.6)","ca":"rgba(0,230,118,0.08)","br":"rgba(0,230,118,0.2)","nb":"rgba(0,26,16,0.97)","nt":"rgba(232,245,233,0.8)","font":"Inter","grad":"linear-gradient(135deg,#001A10,#002a18)"},
    {"dark":False,"bg":"#F0F4FF","pr":"#1746A2","ac":"#FF6B6B","tx":"#0a1628","mu":"#6B7280","ca":"#DBE4FF","br":"#BAC8FF","nb":"rgba(240,244,255,0.97)","nt":"#1746A2","font":"Inter","grad":"linear-gradient(135deg,#f0f4ff,#dbe4ff)"},
]

def get_design(prompt: str) -> dict:
    idx = abs(hash(prompt + "v3design")) % len(DESIGN_SYSTEMS)
    return DESIGN_SYSTEMS[idx]

# ── CONTENT DATABASE ──────────────────────────────────────────────────────────
CONTENT = {
    "restaurant":    {"tagline":"Where Every Bite Tells a Story","sub":"Authentic flavours crafted with passion. Fresh ingredients, timeless recipes, unforgettable moments.","cta1":"Reserve a Table","cta2":"View Menu","services_title":"Our Specialties","services":[("🍽️","Fine Dining","Exquisite multi-course meals by award-winning chefs."),("🍷","Premium Bar","Curated wines, craft cocktails, rare spirits."),("🎂","Private Events","Exclusive rooms for celebrations and corporate dinners."),("🚗","Home Delivery","Restaurant quality at your doorstep, fast.")],"stats":[("15+","Years"),("50K+","Guests"),("4.9★","Rating"),("200+","Dishes")],"testi":[("Arjun M.","Food Critic","Best dining in the city. Every dish is absolute perfection."),("Priya S.","Regular Guest","We celebrate every anniversary here. Simply magical."),("Rahul K.","Corporate Host","World-class private dining. Impressed every single client.")],"af":[("🏆","Award-Winning","Top culinary awards for 10 consecutive years."),("🌿","Farm to Table","Only locally sourced fresh ingredients always."),("🎶","Perfect Ambiance","As memorable as the food itself.")]},
    "saas":          {"tagline":"Ship Faster. Scale Without Limits.","sub":"AI-powered platform automating your entire workflow. Built for teams that move fast and win.","cta1":"Start Free Trial","cta2":"Watch Demo","services_title":"Platform Features","services":[("⚡","Automation","Eliminate repetitive tasks with intelligent automation."),("📊","Analytics","Real-time dashboards with actionable insights."),("🔗","200+ Integrations","Connect every tool your team already uses."),("🛡️","Enterprise Security","SOC2, SSO, SAML, audit logs built in.")],"stats":[("10K+","Teams"),("99.9%","Uptime"),("10x","Faster"),("4.8★","G2")],"testi":[("Sarah C.","CTO","Cut costs 60% in month one. Genuinely transformative."),("Marcus J.","CEO","Team ships 3x faster. ROI was immediate and obvious."),("Aisha P.","VP Eng","Best developer experience ever. Truly world-class.")],"af":[("⚡","Sub-100ms","Blazing fast response times your users will notice."),("🔒","SOC2","Enterprise security built in from day one always."),("🤖","AI-Native","Every feature powered by intelligent automation.")]},
    "car":           {"tagline":"Drive Your Dream Car Today","sub":"Premium vehicles, transparent pricing, buying experience that respects your time and money.","cta1":"Browse Inventory","cta2":"Book Test Drive","services_title":"Our Services","services":[("🚗","New Cars","Latest models from top manufacturers at best prices."),("✅","Certified Used","Pre-owned vehicles inspected and warrantied thoroughly."),("💳","Easy Finance","Loans approved in 24 hours from 7.9% APR."),("🔧","Service Centre","Manufacturer-trained technicians for all brands.")],"stats":[("2K+","Cars Sold"),("500+","Reviews"),("15+","Brands"),("24hr","Loan Approval")],"testi":[("Vikram P.","Business Owner","Found my dream SUV at unbelievable price. Zero pressure."),("Sunita R.","Doctor","Financing approved in hours. Drove home same day."),("Amit K.","Entrepreneur","Third car here. Never going anywhere else ever.")],"af":[("🏅","150-Point Check","Every used vehicle certified and thoroughly inspected."),("💰","Price Match","We match any verified competitor price, guaranteed."),("🔧","Free Service","Complimentary maintenance checks for life of vehicle.")]},
    "portfolio":     {"tagline":"Design That Moves People","sub":"Digital products that convert. Every pixel deliberate. Every interaction purposeful and precise.","cta1":"View My Work","cta2":"Hire Me","services_title":"What I Do","services":[("🎨","UI/UX Design","Research-driven interfaces that users love and convert."),("💻","Development","React and Next.js — fast, accessible, and beautiful."),("📱","Mobile Apps","iOS and Android experiences that delight every user."),("🚀","Brand Identity","Logos and systems that stand the test of time.")],"stats":[("50+","Projects"),("30+","Clients"),("5★","Rating"),("8+","Years")],"testi":[("David P.","Founder","Delivered beyond expectations, on time and under budget."),("Emma W.","Director","Conversion rate up 240% after redesign. Extraordinary."),("Carlos R.","CEO","Best investment this year. Changed our market position.")],"af":[("🎯","Data-Driven","Every design decision backed by research and data."),("⚡","Fast Delivery","Production-ready designs delivered in days always."),("🤝","Collaborative","I work as an extension of your team, not a vendor.")]},
    "ecommerce":     {"tagline":"Premium Quality, Delivered Fast","sub":"Curated collections you will love. Free shipping. 30-day returns. Shop with complete confidence.","cta1":"Shop Now","cta2":"View Lookbook","services_title":"Why Shop With Us","services":[("🚚","Free Shipping","Express delivery on every order, always."),("✅","Quality Assured","47-point inspection on every product before delivery."),("↩️","Easy Returns","30-day returns, no questions, full refund guaranteed."),("💳","Secure Checkout","UPI, cards, EMI, COD — all accepted securely.")],"stats":[("50K+","Customers"),("10K+","Products"),("4.9★","Rating"),("99%","Satisfaction")],"testi":[("Sneha G.","Buyer","Incredible quality. Delivered in 2 days. Will order again."),("Vikram N.","Member","Shopping here 3 years. Always consistently excellent."),("Divya K.","Blogger","My go-to source for premium finds. Impeccable curation.")],"af":[("🚚","Express Delivery","Free on all orders, no minimum spend required."),("↩️","30-Day Returns","No questions asked. Full refund guaranteed always."),("✅","Quality Certified","47-point inspection on every single product.")]},
    "agency":        {"tagline":"We Build Brands That Dominate Markets","sub":"Full-service growth agency. Strategy, creative, technology turning businesses into category leaders.","cta1":"Get a Proposal","cta2":"See Case Studies","services_title":"Our Services","services":[("📈","Growth Strategy","Data-driven plans for explosive, sustainable growth."),("🎯","Performance Ads","Campaigns that consistently beat industry benchmarks."),("🌐","Digital Products","Websites and apps engineered to convert visitors."),("✍️","Brand and Creative","Stories that connect emotionally and drive action.")],"stats":[("100+","Brands"),("₹50Cr+","Revenue"),("4.9★","Rating"),("8+","Years")],"testi":[("Ankit J.","CMO","Tripled qualified leads in 90 days. Best agency ever."),("Meera K.","Founder","Rebrand drove 180% revenue growth year on year."),("Rajesh P.","CEO","True growth partners. Exceptional results every time.")],"af":[("📊","Data-Driven","Every strategy backed by rigorous research."),("⚡","Agile","Results in weeks, not quarters. Always."),("🎯","ROI-Obsessed","Every spend tied to measurable business outcomes.")]},
    "fitness":       {"tagline":"Transform Your Body. Own Your Life.","sub":"Expert coaching, elite facilities, community that refuses to let you quit. Transformation starts today.","cta1":"Start Free Trial","cta2":"View Programs","services_title":"Our Programs","services":[("💪","Strength Training","Elite programming to build real, lasting power."),("🏃","HIIT and Cardio","High-intensity sessions that torch fat fast."),("🧘","Recovery and Mobility","Yoga and protocols to prevent injury always."),("🥗","Nutrition Coaching","Personalised plans that fuel your transformation.")],"stats":[("5K+","Members"),("50+","Coaches"),("98%","Success Rate"),("4.9★","Rating")],"testi":[("Kiran R.","Member","Lost 20kg in 6 months. The coaching is life-changing."),("Ananya S.","Runner","PB improved 22 minutes. Absolutely world-class programming."),("Dev M.","Athlete","12kg muscle in one year. The science behind it is real.")],"af":[("🏆","Elite Coaches","Internationally certified trainers with real results."),("📊","Science-Based","Peer-reviewed sports science programming always."),("👥","Community","Support system that keeps you accountable daily.")]},
    "education":     {"tagline":"Learn Without Limits. Grow Without Ceiling.","sub":"World-class instructors, live cohorts, lifetime access, certifications that employers actually value.","cta1":"Enroll Now","cta2":"Browse Courses","services_title":"What We Offer","services":[("📚","Expert Courses","Learn from top industry practitioners worldwide."),("🎯","Live Cohorts","Real-time classes with Q&A and mentorship daily."),("🏆","Certifications","Credentials hiring managers trust and recognise."),("♾️","Lifetime Access","Learn at your pace. Revisit any lesson forever.")],"stats":[("20K+","Students"),("500+","Courses"),("4.9★","Rating"),("95%","Placement")],"testi":[("Rohan M.","Graduate","Dream job 3 months after completing the program."),("Priya T.","Career Changer","Best investment in my career. Genuinely life-changing."),("Amit S.","Professional","Promoted twice. Skills are directly applicable daily.")],"af":[("👨‍🏫","Expert Instructors","Industry practitioners with real-world track records."),("🎯","Project-Based","Build real projects, not just watch passive videos."),("🏆","Recognised","Credentials employers and hiring managers trust.")]},
    "realestate":    {"tagline":"Find Your Perfect Home","sub":"Premium listings, trusted agents, transparent process. Buying, selling, renting made effortless.","cta1":"Browse Properties","cta2":"Talk to Agent","services_title":"Our Services","services":[("🏠","Residential Sales","Premium homes and apartments in prime locations."),("🔑","Rental Properties","Verified listings with fully transparent pricing."),("💼","Commercial Spaces","Offices and retail for every business need."),("📋","Property Management","Complete end-to-end management for landlords.")],"stats":[("5K+","Properties"),("2K+","Clients"),("₹500Cr+","Transactions"),("4.9★","Rating")],"testi":[("Suresh P.","Buyer","Perfect 3BHK in 2 weeks. The agent was exceptional."),("Kavita M.","Investor","ROI on recommended properties has been outstanding."),("Arun K.","Seller","Sold above asking in 10 days. Absolutely remarkable.")],"af":[("🔍","Market Knowledge","Hyper-local expertise in every area we serve."),("💰","Best Price","We negotiate hard to get you the best deal."),("📋","Paperwork Handled","Every document, verification, legal step managed.")]},
    "hospital":      {"tagline":"Expert Care, Every Step of the Way","sub":"Compassionate healthcare with cutting-edge technology. Your health is our only and greatest priority.","cta1":"Book Appointment","cta2":"Find a Doctor","services_title":"Our Departments","services":[("🫀","Cardiology","Comprehensive heart care from diagnosis to surgery."),("🧠","Neurology","Advanced neurological treatment and expert care."),("🦷","Dental Care","Complete dental services from routine to complex."),("👶","Paediatrics","Specialised child healthcare for all ages.")],"stats":[("50K+","Patients"),("50+","Specialists"),("20+","Departments"),("4.9★","Rating")],"testi":[("Ramesh K.","Patient","The care here saved my life. Exceptional team always."),("Sunita V.","Family Member","Compassionate, skilled, and always available for us."),("Dr. Anil S.","Referring Physician","Best facility in the region. Refer all complex cases.")],"af":[("👨‍⚕️","Expert Specialists","50+ specialists across every medical department."),("🏥","Advanced Technology","State-of-the-art diagnostic and surgical technology."),("❤️","Patient-First","Treating the whole person, not just the illness.")]},
    "hotel":         {"tagline":"Where Luxury Meets Serenity","sub":"Extraordinary escape where world-class hospitality and unmatched comfort come together perfectly.","cta1":"Book Your Stay","cta2":"Explore Rooms","services_title":"Our Offerings","services":[("🛏️","Luxury Rooms","Beautifully appointed rooms with stunning views."),("🍽️","Fine Dining","Award-winning restaurants serving world cuisine."),("🏊","Pool and Spa","Infinity pool and full-service wellness facilities."),("💼","Business Centre","State-of-the-art conference and event facilities.")],"stats":[("20+","Years"),("10K+","Guests"),("5★","Star Rating"),("4.9★","Guest Rating")],"testi":[("Ananya P.","Honeymooner","Most magical experience of our lives. Absolute perfection."),("Rohit V.","Business Traveller","World-class facilities and service. My permanent go-to."),("Meera S.","Leisure Guest","Every single detail was perfect. Return every year.")],"af":[("⭐","5-Star Service","Award-winning hospitality anticipating every need."),("🍽️","Signature Dining","Three restaurants, each a culinary destination."),("🧖","World-Class Spa","A sanctuary of wellness and total rejuvenation.")]},
    "law":           {"tagline":"Justice. Expertise. Results.","sub":"Experienced legal counsel for individuals and businesses. We fight for your rights with precision.","cta1":"Free Consultation","cta2":"Our Practice Areas","services_title":"Practice Areas","services":[("🏢","Corporate Law","Business formation, contracts, M&A, governance."),("⚖️","Civil Litigation","Representation across all civil courts nationwide."),("👨‍👩‍👧","Family Law","Divorce, custody, adoption, all family matters."),("🏠","Property Law","Real estate transactions, disputes, and rights.")],"stats":[("10K+","Cases Won"),("25+","Years"),("200+","Corporate Clients"),("4.9★","Rating")],"testi":[("Rajesh M.","Business Owner","Won a case others said was completely unwinnable."),("Priya S.","Client","Handled with total sensitivity and full professionalism."),("Amit Corp","General Counsel","Trusted legal partner for every matter for 10 years.")],"af":[("⚖️","Proven Record","10,000+ cases won across all courts and tribunals."),("🔒","Confidential","Absolute attorney-client privilege guaranteed always."),("📞","24/7 Available","Always accessible for every urgent legal matter.")]},
    "startup":       {"tagline":"From Zero to Category Leader","sub":"Building the future. Join us at the ground floor of the defining company of our generation.","cta1":"Join Waitlist","cta2":"See How It Works","services_title":"What We Are Building","services":[("⚡","Core Product","Fastest, most intuitive solution in the market today."),("🤖","AI Layer","Features that learn and improve with every interaction."),("🔗","Platform API","Open platform developers can build powerful things on."),("🌐","Global Scale","Infrastructure built to serve millions from day one.")],"stats":[("1K+","Beta Users"),("₹2Cr+","Pre-orders"),("3x","Monthly Growth"),("4.9★","Beta Rating")],"testi":[("Ankit S.","Beta User","This is going to be massive. Never seen anything like it."),("Meera V.","Investor","Most impressive founding team and product I have seen."),("Rahul P.","Early Adopter","Switched day one. Never once looked back at all.")],"af":[("🚀","Hypergrowth","3x month-over-month growth consistently since launch."),("🤖","AI-First","Intelligence built in, not bolted on as an afterthought."),("🌍","Global Vision","Building for India first, then conquering the world.")]},
    "finance":       {"tagline":"Your Wealth. Our Expertise.","sub":"SEBI-registered advisors helping build, protect, and grow your wealth through disciplined planning.","cta1":"Free Consultation","cta2":"Our Services","services_title":"Our Services","services":[("📈","Wealth Management","Personalised portfolios aligned to your specific goals."),("🏦","Mutual Funds","Curated fund selection and expert SIP planning."),("🛡️","Insurance Planning","Comprehensive coverage for everything you have built."),("📋","Tax Planning","Legal optimisation strategies to maximise your returns.")],"stats":[("5K+","Clients"),("₹500Cr+","AUM"),("15+","Years"),("4.9★","Rating")],"testi":[("Suresh M.","Business Owner","Portfolio grown 18% annually for 5 consecutive years."),("Kavita P.","Retired","Secured my retirement completely. Total peace of mind."),("Arun S.","Professional","Started my SIP journey here. Remarkable compounding.")],"af":[("📊","Research-Driven","All recommendations backed by rigorous fundamental analysis."),("🔒","SEBI Registered","Fully regulated and compliant with all guidelines."),("💼","Personalised","No generic advice. Every plan built for your situation.")]},
    "construction":  {"tagline":"Building Dreams. Delivering Excellence.","sub":"From homes to commercial complexes, delivered on time, on budget, to the highest quality standards.","cta1":"Get a Quote","cta2":"View Projects","services_title":"Our Services","services":[("🏠","Residential","Custom homes built to the very highest specifications."),("🏢","Commercial","Offices, malls, industrial complexes at real scale."),("🎨","Interior Design","Complete fit-out and interior services for every space."),("🔧","Renovation","Expert renovation and remodelling of existing structures.")],"stats":[("500+","Projects Completed"),("₹500Cr+","Project Value"),("20+","Years Experience"),("4.9★","Client Rating")],"testi":[("Vikram S.","Developer","5 projects with them. Quality and timing always perfect."),("Anita R.","Home Owner","My dream home, exactly as I imagined it. Stunning."),("Raj Corp","Commercial Client","Office complex on time, on budget, exceptional finish.")],"af":[("🏗️","Turnkey Delivery","Complete management from foundation to final finishing."),("⏰","On-Time Guarantee","Never missed a single project deadline in 20 years."),("🏆","ISO 9001 Certified","Certified processes ensuring the highest build quality.")]},
    "ngo":           {"tagline":"Every Life Deserves Dignity","sub":"Working at compassion and action to create lasting change for communities that need it most.","cta1":"Donate Now","cta2":"Get Involved","services_title":"Our Programs","services":[("📚","Education","Quality education and scholarships for underprivileged."),("🏥","Healthcare","Mobile medical clinics in remote communities nationwide."),("💼","Livelihood","Skills training and microfinance creating independence."),("🌱","Environment","Tree planting and water conservation drives always.")],"stats":[("100K+","Lives Impacted"),("15+","Years of Impact"),("50+","Communities Served"),("4.9★","Transparency")],"testi":[("Anita S.","Major Donor","I can see exactly where my money goes. Real visible impact."),("Rahul M.","Corporate Partner","Most transparent and impactful NGO we have ever partnered."),("Meera P.","Volunteer","Changed my life as much as it changed the communities.")],"af":[("✅","100% Transparent","Full financial reports published for every single donor."),("🎯","Measurable Impact","Programs evaluated against clear, audited outcomes always."),("🤝","Community-Led","Programs designed with and for the communities we serve.")]},
    "photography":   {"tagline":"Capturing Moments That Last Forever","sub":"Every frame tells a story. Photography transforming ordinary moments into extraordinary timeless memories.","cta1":"Book a Session","cta2":"View Portfolio","services_title":"Our Services","services":[("📸","Wedding Photography","Your perfect day captured beautifully forever."),("👤","Portrait Sessions","Professional headshots and deeply personal portraits."),("🏢","Commercial Photography","Stunning product and corporate photography."),("🎬","Videography","Cinematic videos that genuinely move people emotionally.")],"stats":[("500+","Sessions Done"),("50K+","Photos Taken"),("5★","Rating"),("10+","Years")],"testi":[("Sneha P.","Bride","Our wedding photos are absolutely breathtakingly beautiful."),("Rajesh K.","CEO","Professional headshots exceeded every single expectation."),("Priya M.","Marketing Head","Commercial shots drove our campaign performance significantly.")],"af":[("📷","Award-Winning","Recognised by national photography associations."),("🎨","Artistic Vision","Every photo is a deliberate work of lasting art."),("💾","Fast Delivery","Fully edited photos delivered within just 48 hours.")]},
    "salon":         {"tagline":"Where Beauty Meets Expertise","sub":"Premium salon services in a luxurious setting. Look and feel your absolute best every single day.","cta1":"Book Appointment","cta2":"Our Services","services_title":"Our Services","services":[("💇","Hair Styling","Cuts, colours, and treatments by true expert stylists."),("💅","Nail Art","Manicure, pedicure, and nail artistry done perfectly."),("🧖","Spa Treatments","Relaxing facials and rejuvenating body treatments."),("💄","Bridal Makeup","Wedding and occasion makeup by skilled professionals.")],"stats":[("10K+","Happy Clients"),("50+","Services Offered"),("5★","Rating"),("8+","Years")],"testi":[("Sunita R.","Bride","Best bridal makeup I have ever seen. Absolutely perfect."),("Kavita P.","Regular Client","Come every month. Always leave feeling and looking amazing."),("Meera S.","Client","The hair treatment completely transformed my confidence.")],"af":[("💎","Premium Products","Only top-tier professional products used always."),("👩‍🎨","Expert Stylists","Internationally trained and certified beauty professionals."),("🌿","Hygienic","Sterilized tools and fresh towels for every client.")]},
    "travel":        {"tagline":"Your World Awaits. Let Us Take You There.","sub":"Curated travel experiences, personalised itineraries, and memories that last a lifetime truly.","cta1":"Plan My Trip","cta2":"View Packages","services_title":"Our Services","services":[("✈️","International Tours","Handcrafted itineraries to destinations worldwide."),("🏔️","Adventure Travel","Treks, safaris, and extreme experiences."),("🏖️","Beach Holidays","Perfect resort stays and island getaways."),("💑","Honeymoon Packages","Romantic escapes tailored for couples perfectly.")],"stats":[("5K+","Happy Travellers"),("100+","Destinations"),("15+","Years"),("4.9★","Rating")],"testi":[("Rahul K.","Traveller","The Bali trip was flawlessly organised. Dream experience."),("Priya S.","Couple","Our honeymoon was beyond absolutely anything we imagined."),("Amit R.","Family","The Rajasthan tour was magical for our whole family.")],"af":[("🗺️","Expert Local Guides","Local experts in every destination worldwide."),("💰","Best Value","Unbeatable packages for unforgettable experiences."),("📞","24/7 Support","With you every step of your entire journey.")]},
    "tech_company":  {"tagline":"Technology That Transforms Business","sub":"End-to-end technology solutions driving digital transformation and accelerating sustainable growth.","cta1":"Get a Quote","cta2":"View Our Work","services_title":"Our Services","services":[("💻","Software Development","Custom software built for your exact business needs."),("📱","App Development","iOS, Android, and cross-platform mobile applications."),("☁️","Cloud Solutions","Migration, architecture, and fully managed cloud services."),("🔒","Cybersecurity","Protecting your business from all evolving threats.")],"stats":[("500+","Projects Done"),("200+","Clients Served"),("15+","Years"),("4.9★","Rating")],"testi":[("Vikram S.","CTO","Delivered our entire platform on time and under budget."),("Anita R.","CEO","The app they built drives 60% of our total revenue."),("Rahul P.","Founder","Best tech partner we have ever worked with. Remarkable.")],"af":[("⚡","Agile Delivery","Fast iterative development with regular meaningful releases."),("🔒","Secure by Design","Security built in at every layer of every system."),("🤝","Long-term Partner","We stay invested in your success indefinitely always.")]},
    "wedding":       {"tagline":"Your Perfect Day. Our Greatest Joy.","sub":"Wedding experiences so perfect they feel like dreams you never want to wake from. Ever.","cta1":"Plan Your Wedding","cta2":"View Gallery","services_title":"Our Services","services":[("💒","Full Planning","Complete wedding management from first concept to big day."),("📸","Photography","Cinematic wedding photography and beautiful videography."),("🌸","Decor and Florals","Breathtaking decorations and stunning floral design."),("🍽️","Catering","Exquisite menus for every cuisine and every taste.")],"stats":[("500+","Weddings Planned"),("50K+","Happy Guests"),("10+","Years"),("5★","Rating")],"testi":[("Priya and Rahul","Couple","Our wedding was beyond any dream we had. Perfect."),("Sunita P.","Bride's Mother","Every detail handled with such genuine love and care."),("Amit V.","Groom","Best decision we ever made was hiring this incredible team.")],"af":[("💎","Luxury Execution","Every element crafted to absolute and total perfection."),("🤝","Personal Touch","Your dedicated planner committed solely to your wedding."),("📞","Always Available","24/7 throughout your entire planning journey always.")]},
    "dental":        {"tagline":"Your Smile. Our Expertise.","sub":"Advanced dental care in a comfortable, anxiety-free environment. Your perfect smile awaits you.","cta1":"Book Appointment","cta2":"Our Treatments","services_title":"Our Treatments","services":[("🦷","General Dentistry","Regular checkups, cleaning, and preventive care always."),("😁","Cosmetic Dentistry","Whitening, veneers, and complete smile makeovers."),("🦾","Dental Implants","Permanent, natural-looking tooth replacement solutions."),("😬","Orthodontics","Braces and Invisalign for perfect alignment.")],"stats":[("10K+","Happy Patients"),("20+","Treatments"),("15+","Years"),("5★","Rating")],"testi":[("Rahul K.","Patient","My smile transformation was absolutely incredible. Remarkable."),("Priya S.","Patient","Most pain-free dental experience I have ever had anywhere."),("Amit M.","Parent","My children actually look forward to coming here now.")],"af":[("🔬","Advanced Technology","Latest dental technology for most precise treatment."),("💊","Pain-Free Promise","Anxiety-free care with modern pain management always."),("😁","Results Guaranteed","We guarantee results or we make it completely right.")]},
    "cleaning":      {"tagline":"Spotless Spaces. Happy Places.","sub":"Professional cleaning transforming your home or office into a pristine, immaculate sanctuary.","cta1":"Book a Clean","cta2":"Our Services","services_title":"Our Services","services":[("🏠","Home Cleaning","Deep and regular cleaning for residential properties."),("🏢","Office Cleaning","Professional commercial cleaning services always."),("🧹","Deep Clean","Intensive cleaning for move-in and move-out."),("🌿","Eco Cleaning","Green cleaning with non-toxic, safe products.")],"stats":[("5K+","Happy Clients"),("50K+","Cleans Completed"),("8+","Years"),("5★","Rating")],"testi":[("Priya S.","Home Owner","My home has never ever been this clean. Exceptional always."),("TechCorp","Office Manager","Our office is always spotless. The team is incredibly reliable."),("Rahul K.","Landlord","Move-out cleans are absolutely perfect every single time.")],"af":[("✅","Verified Staff","All staff background-checked and fully insured always."),("🌿","Eco-Friendly","Non-toxic, safe products for your family always."),("⏰","Always Reliable","On time, always thorough, never let you down.")]},
    "mental_health": {"tagline":"Your Mental Health Matters","sub":"Compassionate, confidential therapy and counselling. You deserve support and help is here.","cta1":"Book a Session","cta2":"Meet Our Team","services_title":"Our Services","services":[("🧠","Individual Therapy","One-on-one sessions with qualified, caring therapists."),("👫","Couples Counselling","Strengthen your relationship with expert guidance."),("👨‍👩‍👧","Family Therapy","Healing and communication support for whole families."),("📱","Online Sessions","Convenient therapy from the comfort of your own home.")],"stats":[("5K+","Clients Helped"),("20+","Qualified Therapists"),("10+","Years"),("5★","Rating")],"testi":[("Priya S.","Client","My anxiety is manageable for the first time in years."),("Rahul K.","Couple","Our marriage is stronger than ever after counselling."),("Anita M.","Client","Online sessions fit perfectly into my busy daily life.")],"af":[("🔐","Confidential","Absolute privacy and confidentiality guaranteed always."),("❤️","Non-Judgmental","A completely safe space to be entirely yourself."),("👩‍⚕️","Qualified","All therapists hold recognised international credentials.")]},
    "business":      {"tagline":"Excellence Delivered Every Single Time","sub":"Deep expertise, bold execution, obsession with results. We help businesses grow and consistently win.","cta1":"Get Started Today","cta2":"Learn More","services_title":"What We Offer","services":[("⚡","Fast Results","Exceptional outcomes delivered ahead of every schedule."),("🎯","Results-Obsessed","Every action tied to your specific measurable goals."),("🤝","True Partnership","Invested in your success as deeply as you are always."),("🛡️","Proven Reliability","100+ clients trust us with their most critical work.")],"stats":[("100+","Projects Completed"),("50+","Happy Clients"),("4.9★","Average Rating"),("5+","Years")],"testi":[("Rohit K.","Managing Director","Delivered exactly as promised and ahead of schedule."),("Nisha A.","COO","Best vendor relationship we have ever had. Truly reliable."),("Amit S.","Founder","An absolute game-changer for our business and growth.")],"af":[("⚡","Fast Delivery","Results delivered faster than any competitor anywhere."),("🎯","ROI-Focused","Every engagement measured against real business impact."),("🛡️","Proven Record","5+ years, 100+ clients, zero failures anywhere.")]},
}

def get_content(cat: str) -> dict:
    return CONTENT.get(cat, CONTENT["business"])

# ── SECTION GENERATORS ────────────────────────────────────────────────────────
def make_contact_section(ud: dict, ds: dict, features: dict, name: str) -> str:
    phone = ud["phone"] or "+91 99999 99999"
    email_addr = ud["email"] or f"hello@{re.sub(chr(91)+chr(94)+chr(97)+chr(122)+chr(48)+chr(57)+chr(93),'',name.lower())}.com"
    address = ud["address"] or "123 Business Street, Mumbai, India"
    hours = ud["opening_hours"] or "Mon–Sat: 9 AM – 8 PM | Sun: 10 AM – 6 PM"
    wa = ud["whatsapp"] or phone
    is_dark = ds["dark"]
    card_bg = "rgba(255,255,255,0.04)" if is_dark else ds["ca"]
    input_bg = "rgba(255,255,255,0.07)" if is_dark else "#ffffff"
    input_border = ds["br"]
    input_color = ds["tx"]
    map_query = ud["map_location"] or urllib.parse.quote(address)

    contact_info = f"""
    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:20px;margin-bottom:40px">
      <div style="background:{card_bg};border:1px solid {ds["br"]};border-radius:20px;padding:24px;text-align:center">
        <div style="font-size:2rem;margin-bottom:12px">📞</div>
        <h4 style="color:{ds["tx"]};font-weight:700;font-size:0.9rem;margin-bottom:6px">Call Us</h4>
        <a href="tel:{phone}" style="color:{ds["pr"]};text-decoration:none;font-size:0.9rem;font-weight:600">{phone}</a>
      </div>
      <div style="background:{card_bg};border:1px solid {ds["br"]};border-radius:20px;padding:24px;text-align:center">
        <div style="font-size:2rem;margin-bottom:12px">📧</div>
        <h4 style="color:{ds["tx"]};font-weight:700;font-size:0.9rem;margin-bottom:6px">Email Us</h4>
        <a href="mailto:{email_addr}" style="color:{ds["pr"]};text-decoration:none;font-size:0.85rem;font-weight:600;word-break:break-all">{email_addr}</a>
      </div>
      <div style="background:{card_bg};border:1px solid {ds["br"]};border-radius:20px;padding:24px;text-align:center">
        <div style="font-size:2rem;margin-bottom:12px">📍</div>
        <h4 style="color:{ds["tx"]};font-weight:700;font-size:0.9rem;margin-bottom:6px">Visit Us</h4>
        <p style="color:{ds["mu"]};font-size:0.82rem;line-height:1.5">{address}</p>
      </div>
      <div style="background:{card_bg};border:1px solid {ds["br"]};border-radius:20px;padding:24px;text-align:center">
        <div style="font-size:2rem;margin-bottom:12px">⏰</div>
        <h4 style="color:{ds["tx"]};font-weight:700;font-size:0.9rem;margin-bottom:6px">Hours</h4>
        <p style="color:{ds["mu"]};font-size:0.82rem;line-height:1.5">{hours}</p>
      </div>
    </div>"""

    form_html = ""
    if features.get("contact_form") or features.get("booking_form"):
        form_label = "Book Appointment" if features.get("booking_form") else "Send Message"
        extra_fields = ""
        if features.get("booking_form"):
            extra_fields = f"""
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px">
            <div>
              <label style="display:block;font-size:0.8rem;font-weight:600;color:{ds["mu"]};margin-bottom:6px">Preferred Date</label>
              <input type="date" style="width:100%;padding:12px 16px;background:{input_bg};border:1px solid {input_border};border-radius:12px;color:{input_color};font-size:0.9rem;outline:none"/>
            </div>
            <div>
              <label style="display:block;font-size:0.8rem;font-weight:600;color:{ds["mu"]};margin-bottom:6px">Preferred Time</label>
              <input type="time" style="width:100%;padding:12px 16px;background:{input_bg};border:1px solid {input_border};border-radius:12px;color:{input_color};font-size:0.9rem;outline:none"/>
            </div>
          </div>"""
        form_html = f"""
        <form onsubmit="handleForm(event)" style="display:flex;flex-direction:column;gap:16px;background:{card_bg};border:1px solid {ds["br"]};border-radius:24px;padding:32px;margin-top:32px">
          <h3 style="font-size:1.2rem;font-weight:800;color:{ds["tx"]};margin-bottom:8px">{form_label}</h3>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px">
            <div>
              <label style="display:block;font-size:0.8rem;font-weight:600;color:{ds["mu"]};margin-bottom:6px">Full Name *</label>
              <input type="text" placeholder="Your name" required style="width:100%;padding:12px 16px;background:{input_bg};border:1px solid {input_border};border-radius:12px;color:{input_color};font-size:0.9rem;outline:none"/>
            </div>
            <div>
              <label style="display:block;font-size:0.8rem;font-weight:600;color:{ds["mu"]};margin-bottom:6px">Phone Number *</label>
              <input type="tel" placeholder="+91 00000 00000" required style="width:100%;padding:12px 16px;background:{input_bg};border:1px solid {input_border};border-radius:12px;color:{input_color};font-size:0.9rem;outline:none"/>
            </div>
          </div>
          <div>
            <label style="display:block;font-size:0.8rem;font-weight:600;color:{ds["mu"]};margin-bottom:6px">Email Address</label>
            <input type="email" placeholder="your@email.com" style="width:100%;padding:12px 16px;background:{input_bg};border:1px solid {input_border};border-radius:12px;color:{input_color};font-size:0.9rem;outline:none"/>
          </div>
          {extra_fields}
          <div>
            <label style="display:block;font-size:0.8rem;font-weight:600;color:{ds["mu"]};margin-bottom:6px">Message</label>
            <textarea placeholder="How can we help you?" rows="4" style="width:100%;padding:12px 16px;background:{input_bg};border:1px solid {input_border};border-radius:12px;color:{input_color};font-size:0.9rem;outline:none;resize:vertical"></textarea>
          </div>
          <button type="submit" style="background:{ds["pr"]};color:#fff;border:none;padding:14px 32px;border-radius:100px;font-weight:800;font-size:0.9rem;cursor:pointer;transition:all 0.3s" onmouseover="this.style.filter=\'brightness(1.1)\'" onmouseout="this.style.filter=\'\'">
            {form_label} →
          </button>
          <div id="formSuccess" style="display:none;background:#dcfce7;border:1px solid #a7f3d0;border-radius:12px;padding:16px;text-align:center;color:#065f46;font-weight:600">
            ✅ Thank you! We will contact you within 24 hours.
          </div>
        </form>"""

    map_html = ""
    if features.get("map"):
        map_html = f"""
        <div style="margin-top:32px;border-radius:24px;overflow:hidden;border:1px solid {ds["br"]}">
          <iframe
            src="https://maps.google.com/maps?q={map_query}&output=embed"
            width="100%" height="350" style="border:0;display:block"
            allowfullscreen loading="lazy" referrerpolicy="no-referrer-when-downgrade">
          </iframe>
        </div>"""

    return f"""
    <section style="padding:100px 5%;background:{ds["bg"]}" id="contact">
      <div style="max-width:1280px;margin:0 auto">
        <div style="text-align:center;margin-bottom:60px">
          <div style="display:inline-flex;align-items:center;gap:8px;background:{ds["ca"]};color:{ds["pr"]};font-size:0.72rem;font-weight:800;text-transform:uppercase;letter-spacing:2px;padding:8px 18px;border-radius:100px;margin-bottom:20px;border:1px solid {ds["br"]}">✦ Contact Us</div>
          <h2 style="font-family:'{ds["font"]}',serif;font-size:clamp(2rem,3vw,2.8rem);font-weight:900;color:{ds["tx"]};letter-spacing:-1px">Get In <span style="color:{ds["pr"]}">Touch</span></h2>
          <p style="color:{ds["mu"]};margin-top:12px;font-size:0.95rem">We would love to hear from you. Reach out any time.</p>
        </div>
        {contact_info}
        {form_html}
        {map_html}
      </div>
    </section>"""

def make_newsletter_section(ds: dict) -> str:
    is_dark = ds["dark"]
    input_bg = "rgba(255,255,255,0.1)" if is_dark else "#ffffff"
    return f"""
    <section style="padding:80px 5%;background:{ds["ca"]}" id="newsletter">
      <div style="max-width:600px;margin:0 auto;text-align:center">
        <div style="font-size:2.5rem;margin-bottom:16px">📬</div>
        <h2 style="font-family:'{ds["font"]}',serif;font-size:2rem;font-weight:900;color:{ds["tx"]};margin-bottom:12px">Stay in the Loop</h2>
        <p style="color:{ds["mu"]};margin-bottom:32px;font-size:0.95rem">Get the latest updates, offers, and insights delivered straight to your inbox.</p>
        <form onsubmit="handleNewsletter(event)" style="display:flex;gap:12px;max-width:480px;margin:0 auto;flex-wrap:wrap">
          <input type="email" placeholder="Enter your email address" required
            style="flex:1;min-width:200px;padding:14px 20px;background:{input_bg};border:1px solid {ds["br"]};border-radius:100px;color:{ds["tx"]};font-size:0.9rem;outline:none"/>
          <button type="submit"
            style="background:{ds["pr"]};color:#fff;border:none;padding:14px 28px;border-radius:100px;font-weight:800;font-size:0.9rem;cursor:pointer;white-space:nowrap">
            Subscribe →
          </button>
        </form>
        <div id="nlSuccess" style="display:none;margin-top:16px;color:{ds["pr"]};font-weight:600">✅ You are subscribed! Welcome aboard.</div>
        <p style="color:{ds["mu"]};font-size:0.75rem;margin-top:16px">No spam ever. Unsubscribe anytime. We respect your privacy.</p>
      </div>
    </section>"""

def make_pricing_section(ds: dict, con: dict, name: str) -> str:
    is_dark = ds["dark"]
    plans = [
        ("Starter","Free","Perfect to get started","✓ Basic features\n✓ 5 users\n✓ Email support\n✓ 1GB storage","Get Started"),
        ("Professional",f"₹{2999:,}/mo","For growing teams","✓ All Starter features\n✓ 50 users\n✓ Priority support\n✓ 50GB storage\n✓ Analytics","Start Trial"),
        ("Enterprise","Custom","For large organisations","✓ All Pro features\n✓ Unlimited users\n✓ Dedicated support\n✓ Unlimited storage\n✓ Custom integrations","Contact Sales"),
    ]
    cards = ""
    for i,(plan_name, price, desc, features_list, cta_text) in enumerate(plans):
        is_highlight = i == 1
        bg = ds["pr"] if is_highlight else ("rgba(255,255,255,0.04)" if is_dark else "#ffffff")
        text_col = "#ffffff" if is_highlight else ds["tx"]
        muted_col = "rgba(255,255,255,0.7)" if is_highlight else ds["mu"]
        btn_style = f"background:#fff;color:{ds['pr']}" if is_highlight else f"background:{ds['pr']};color:#fff"
        popular = '<div style="position:absolute;top:-14px;left:50%;transform:translateX(-50%);background:#fff;color:{};font-size:0.7rem;font-weight:800;padding:6px 16px;border-radius:100px;white-space:nowrap">⭐ Most Popular</div>'.format(ds["pr"]) if is_highlight else ""
        feat_html = "".join([f'<li style="padding:6px 0;font-size:0.85rem;color:{muted_col}">{f.strip()}</li>' for f in features_list.split("\\n") if f.strip()])
        cards += f"""
        <div style="position:relative;background:{bg};border:2px solid {ds["pr"] if is_highlight else ds["br"]};border-radius:24px;padding:36px;{"transform:scale(1.05);" if is_highlight else ""}transition:all 0.3s">
          {popular}
          <h3 style="font-size:1.2rem;font-weight:800;color:{text_col};margin-bottom:8px">{plan_name}</h3>
          <p style="font-size:0.8rem;color:{muted_col};margin-bottom:24px">{desc}</p>
          <div style="font-family:'{ds["font"]}',serif;font-size:2.4rem;font-weight:900;color:{text_col};margin-bottom:24px">{price}</div>
          <ul style="list-style:none;margin-bottom:32px">{feat_html}</ul>
          <button onclick="alert('Contact us to get started with {plan_name}!')" style="{btn_style};border:none;padding:14px 24px;border-radius:100px;font-weight:800;font-size:0.88rem;cursor:pointer;width:100%">{cta_text} →</button>
        </div>"""
    return f"""
    <section style="padding:100px 5%;background:{ds["ca"]}" id="pricing">
      <div style="max-width:1280px;margin:0 auto">
        <div style="text-align:center;margin-bottom:60px">
          <div style="display:inline-flex;align-items:center;gap:8px;background:{ds["ca"]};color:{ds["pr"]};font-size:0.72rem;font-weight:800;text-transform:uppercase;letter-spacing:2px;padding:8px 18px;border-radius:100px;margin-bottom:20px;border:1px solid {ds["br"]}">✦ Pricing</div>
          <h2 style="font-family:'{ds["font"]}',serif;font-size:clamp(2rem,3vw,2.8rem);font-weight:900;color:{ds["tx"]};letter-spacing:-1px">Simple, <span style="color:{ds["pr"]}">Transparent Pricing</span></h2>
          <p style="color:{ds["mu"]};margin-top:12px">No hidden fees. No lock-in. Cancel anytime.</p>
        </div>
        <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:24px;align-items:center">{cards}</div>
      </div>
    </section>"""

def make_faq_section(ds: dict) -> str:
    faqs = [
        ("How do I get started?","Simply click the Get Started button and follow the easy setup process. It takes less than 5 minutes to be up and running completely."),
        ("What payment methods do you accept?","We accept all major credit and debit cards, UPI, net banking, and bank transfers for enterprise customers."),
        ("Is there a free trial available?","Yes, we offer a completely free plan with no credit card required. You can upgrade anytime when you are ready."),
        ("How does your support work?","We provide email support on all plans and priority phone support on Professional and Enterprise plans. Response within 24 hours guaranteed."),
        ("Can I cancel anytime?","Absolutely. There are no long-term contracts or cancellation fees. You can cancel your subscription at any time with just one click."),
        ("Is my data secure and private?","Yes, we use industry-standard encryption and are fully compliant with data protection regulations. Your data is always yours."),
    ]
    items = ""
    for q, a in faqs:
        items += f"""
        <div class="faq-item" style="border-bottom:1px solid {ds["br"]};padding:20px 0">
          <button onclick="toggleFAQ(this)" style="width:100%;text-align:left;background:none;border:none;cursor:pointer;display:flex;justify-content:space-between;align-items:center;gap:16px">
            <span style="font-weight:700;font-size:0.95rem;color:{ds["tx"]}">{q}</span>
            <span style="font-size:1.4rem;color:{ds["pr"]};flex-shrink:0;transition:transform 0.3s">+</span>
          </button>
          <div class="faq-answer" style="display:none;padding-top:12px">
            <p style="color:{ds["mu"]};font-size:0.88rem;line-height:1.7">{a}</p>
          </div>
        </div>"""
    return f"""
    <section style="padding:100px 5%;background:{ds["bg"]}" id="faq">
      <div style="max-width:800px;margin:0 auto">
        <div style="text-align:center;margin-bottom:60px">
          <div style="display:inline-flex;align-items:center;gap:8px;background:{ds["ca"]};color:{ds["pr"]};font-size:0.72rem;font-weight:800;text-transform:uppercase;letter-spacing:2px;padding:8px 18px;border-radius:100px;margin-bottom:20px;border:1px solid {ds["br"]}">✦ FAQ</div>
          <h2 style="font-family:'{ds["font"]}',serif;font-size:clamp(2rem,3vw,2.8rem);font-weight:900;color:{ds["tx"]};letter-spacing:-1px">Frequently Asked <span style="color:{ds["pr"]}">Questions</span></h2>
        </div>
        <div>{items}</div>
      </div>
    </section>"""

def make_team_section(ds: dict) -> str:
    members = [
        ("CEO","Founder and Chief Executive","10+ years experience","👤"),
        ("CTO","Chief Technology Officer","Tech visionary and architect","👤"),
        ("COO","Chief Operations Officer","Operations and growth expert","👤"),
        ("CMO","Chief Marketing Officer","Brand and growth strategist","👤"),
    ]
    cards = ""
    for role, title, desc, icon in members:
        seed_v = abs(hash(role)) % 99999
        cards += f"""
        <div style="background:{ds["ca"]};border:1px solid {ds["br"]};border-radius:24px;padding:32px;text-align:center;transition:all 0.3s" onmouseover="this.style.transform=\'translateY(-6px)\';this.style.borderColor=\'{ds["pr"]}\'" onmouseout="this.style.transform=\'\';this.style.borderColor=\'{ds["br"]}\'">
          <div style="width:80px;height:80px;border-radius:50%;background:linear-gradient(135deg,{ds["pr"]},{ds["ac"]});margin:0 auto 16px;display:flex;align-items:center;justify-content:center;font-size:2rem">{icon}</div>
          <h4 style="font-weight:800;font-size:1rem;color:{ds["tx"]};margin-bottom:4px">{role}</h4>
          <p style="font-size:0.82rem;color:{ds["pr"]};font-weight:600;margin-bottom:8px">{title}</p>
          <p style="font-size:0.78rem;color:{ds["mu"]}">{desc}</p>
          <div style="display:flex;justify-content:center;gap:12px;margin-top:16px">
            <a href="#" style="color:{ds["pr"]};font-size:0.8rem">LinkedIn →</a>
            <a href="#" style="color:{ds["mu"]};font-size:0.8rem">Twitter</a>
          </div>
        </div>"""
    return f"""
    <section style="padding:100px 5%;background:{ds["ca"]}" id="team">
      <div style="max-width:1280px;margin:0 auto">
        <div style="text-align:center;margin-bottom:60px">
          <div style="display:inline-flex;align-items:center;gap:8px;background:{ds["ca"]};color:{ds["pr"]};font-size:0.72rem;font-weight:800;text-transform:uppercase;letter-spacing:2px;padding:8px 18px;border-radius:100px;margin-bottom:20px;border:1px solid {ds["br"]}">✦ Our Team</div>
          <h2 style="font-family:'{ds["font"]}',serif;font-size:clamp(2rem,3vw,2.8rem);font-weight:900;color:{ds["tx"]};letter-spacing:-1px">Meet the <span style="color:{ds["pr"]}">People Behind It</span></h2>
        </div>
        <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:24px">{cards}</div>
      </div>
    </section>"""

def make_social_section(ud: dict, ds: dict) -> str:
    socials = []
    if ud["instagram"]: socials.append(("📸","Instagram",f"@{ud['instagram']}",f"https://instagram.com/{ud['instagram']}","Follow on Instagram"))
    if ud["facebook"]: socials.append(("👍","Facebook",f"/{ud['facebook']}",f"https://facebook.com/{ud['facebook']}","Like on Facebook"))
    if ud["twitter"]: socials.append(("🐦","Twitter / X",f"@{ud['twitter']}",f"https://twitter.com/{ud['twitter']}","Follow on X"))
    if ud["linkedin"]: socials.append(("💼","LinkedIn",f"/{ud['linkedin']}",f"https://linkedin.com/in/{ud['linkedin']}","Connect on LinkedIn"))
    if ud["youtube"]: socials.append(("▶️","YouTube",f"/{ud['youtube']}",f"https://youtube.com/{ud['youtube']}","Subscribe on YouTube"))
    if not socials:
        return ""
    cards = ""
    for icon, platform, handle, link, cta in socials:
        cards += f"""
        <a href="{link}" target="_blank" rel="noopener" style="display:flex;align-items:center;gap:16px;background:{ds["ca"]};border:1px solid {ds["br"]};border-radius:20px;padding:20px 24px;text-decoration:none;transition:all 0.3s" onmouseover="this.style.borderColor=\'{ds["pr"]}\';this.style.transform=\'translateY(-3px)\'" onmouseout="this.style.borderColor=\'{ds["br"]}\';this.style.transform=\'\'">
          <span style="font-size:2rem">{icon}</span>
          <div>
            <div style="font-weight:700;font-size:0.9rem;color:{ds["tx"]}">{platform}</div>
            <div style="font-size:0.8rem;color:{ds["pr"]}">{handle}</div>
          </div>
          <div style="margin-left:auto;font-size:0.8rem;font-weight:600;color:{ds["mu"]}">{cta} →</div>
        </a>"""
    return f"""
    <section style="padding:80px 5%;background:{ds["bg"]}" id="social">
      <div style="max-width:800px;margin:0 auto">
        <div style="text-align:center;margin-bottom:40px">
          <h2 style="font-family:'{ds["font"]}',serif;font-size:1.8rem;font-weight:900;color:{ds["tx"]}">Follow Us on <span style="color:{ds["pr"]}">Social Media</span></h2>
        </div>
        <div style="display:flex;flex-direction:column;gap:12px">{cards}</div>
      </div>
    </section>"""

def make_whatsapp_button(ud: dict, ds: dict, name: str) -> str:
    phone = (ud["whatsapp"] or ud["phone"] or "919999999999").replace("+","").replace(" ","").replace("-","")
    msg = urllib.parse.quote(f"Hi {name}, I found you online and would like to know more about your services.")
    return f"""
    <a href="https://wa.me/{phone}?text={msg}" target="_blank" rel="noopener"
      style="position:fixed;bottom:24px;right:24px;z-index:9999;width:60px;height:60px;background:#25D366;border-radius:50%;display:flex;align-items:center;justify-content:center;box-shadow:0 8px 30px rgba(37,211,102,0.4);text-decoration:none;transition:all 0.3s;animation:waPulse 2s infinite"
      onmouseover="this.style.transform=\'scale(1.1)\'" onmouseout="this.style.transform=\'\'">
      <svg width="30" height="30" viewBox="0 0 24 24" fill="white"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/></svg>
    </a>"""

def make_sticky_cta(ds: dict, con: dict, phone: str) -> str:
    ph = phone or "+91 99999 99999"
    return f"""
    <div id="stickyCTA" style="position:fixed;bottom:0;left:0;right:0;z-index:9998;background:{ds["nb"]};backdrop-filter:blur(20px);border-top:1px solid {ds["br"]};padding:12px 5%;display:flex;align-items:center;justify-content:space-between;gap:16px;transform:translateY(100%);transition:transform 0.4s ease;flex-wrap:wrap">
      <div>
        <p style="font-weight:700;font-size:0.9rem;color:{ds["tx"]}">Ready to get started?</p>
        <p style="font-size:0.78rem;color:{ds["mu"]}">Contact us today and get a free consultation</p>
      </div>
      <div style="display:flex;gap:12px;flex-wrap:wrap">
        <a href="tel:{ph}" style="background:{ds["ca"]};color:{ds["tx"]};border:1px solid {ds["br"]};padding:10px 20px;border-radius:100px;text-decoration:none;font-weight:700;font-size:0.85rem">📞 Call Now</a>
        <a href="#contact" onclick="document.getElementById('stickyCTA').style.transform='translateY(100%)'" style="background:{ds["pr"]};color:#fff;padding:10px 20px;border-radius:100px;text-decoration:none;font-weight:700;font-size:0.85rem">{con["cta1"]} →</a>
      </div>
    </div>"""

def make_countdown_section(ds: dict) -> str:
    return f"""
    <section style="padding:60px 5%;background:{ds["pr"]}">
      <div style="max-width:900px;margin:0 auto;text-align:center">
        <p style="color:rgba(255,255,255,0.85);font-size:0.9rem;font-weight:600;text-transform:uppercase;letter-spacing:2px;margin-bottom:12px">Limited Time Offer</p>
        <h2 style="font-family:'{ds["font"]}',serif;font-size:2rem;font-weight:900;color:#ffffff;margin-bottom:32px">Offer Ends In</h2>
        <div style="display:flex;justify-content:center;gap:20px;flex-wrap:wrap">
          <div id="cd-days" style="background:rgba(255,255,255,0.15);border-radius:16px;padding:20px 28px">
            <div style="font-family:'{ds["font"]}',serif;font-size:3rem;font-weight:900;color:#fff" id="days">00</div>
            <div style="color:rgba(255,255,255,0.7);font-size:0.75rem;font-weight:600;text-transform:uppercase;letter-spacing:1px">Days</div>
          </div>
          <div style="background:rgba(255,255,255,0.15);border-radius:16px;padding:20px 28px">
            <div style="font-family:'{ds["font"]}',serif;font-size:3rem;font-weight:900;color:#fff" id="hours">00</div>
            <div style="color:rgba(255,255,255,0.7);font-size:0.75rem;font-weight:600;text-transform:uppercase;letter-spacing:1px">Hours</div>
          </div>
          <div style="background:rgba(255,255,255,0.15);border-radius:16px;padding:20px 28px">
            <div style="font-family:'{ds["font"]}',serif;font-size:3rem;font-weight:900;color:#fff" id="mins">00</div>
            <div style="color:rgba(255,255,255,0.7);font-size:0.75rem;font-weight:600;text-transform:uppercase;letter-spacing:1px">Minutes</div>
          </div>
          <div style="background:rgba(255,255,255,0.15);border-radius:16px;padding:20px 28px">
            <div style="font-family:'{ds["font"]}',serif;font-size:3rem;font-weight:900;color:#fff" id="secs">00</div>
            <div style="color:rgba(255,255,255,0.7);font-size:0.75rem;font-weight:600;text-transform:uppercase;letter-spacing:1px">Seconds</div>
          </div>
        </div>
        <a href="#contact" style="display:inline-block;margin-top:32px;background:#fff;color:{ds["pr"]};font-weight:800;padding:14px 36px;border-radius:100px;text-decoration:none;font-size:0.9rem">Claim Offer Now →</a>
      </div>
    </section>"""

def make_blog_section(ds: dict) -> str:
    posts = [
        ("The Future of Our Industry","Insights into how the landscape is changing and what it means for you going forward.","5 min read"),
        ("Top 10 Tips for Success","Expert advice and proven strategies that will help you achieve your goals faster.","7 min read"),
        ("Case Study: How We Helped","A detailed look at how we transformed a client's results in just 90 days.","10 min read"),
    ]
    cards = ""
    for title, excerpt, read_time in posts:
        seed_v = abs(hash(title)) % 99999
        cards += f"""
        <article style="background:{ds["ca"]};border:1px solid {ds["br"]};border-radius:24px;overflow:hidden;transition:all 0.3s" onmouseover="this.style.transform=\'translateY(-6px)\';this.style.borderColor=\'{ds["pr"]}\'" onmouseout="this.style.transform=\'\';this.style.borderColor=\'{ds["br"]}\'">
          <div style="height:200px;background:linear-gradient(135deg,{ds["pr"]}33,{ds["ac"]}22);display:flex;align-items:center;justify-content:center;font-size:3rem">📝</div>
          <div style="padding:24px">
            <div style="font-size:0.72rem;color:{ds["pr"]};font-weight:700;text-transform:uppercase;letter-spacing:1px;margin-bottom:10px">{read_time}</div>
            <h3 style="font-family:'{ds["font"]}',serif;font-size:1.1rem;font-weight:800;color:{ds["tx"]};margin-bottom:10px;line-height:1.3">{title}</h3>
            <p style="font-size:0.84rem;color:{ds["mu"]};line-height:1.6;margin-bottom:16px">{excerpt}</p>
            <a href="#" style="color:{ds["pr"]};font-weight:700;font-size:0.85rem;text-decoration:none">Read More →</a>
          </div>
        </article>"""
    return f"""
    <section style="padding:100px 5%;background:{ds["ca"]}" id="blog">
      <div style="max-width:1280px;margin:0 auto">
        <div style="text-align:center;margin-bottom:60px">
          <div style="display:inline-flex;align-items:center;gap:8px;background:{ds["ca"]};color:{ds["pr"]};font-size:0.72rem;font-weight:800;text-transform:uppercase;letter-spacing:2px;padding:8px 18px;border-radius:100px;margin-bottom:20px;border:1px solid {ds["br"]}">✦ Blog</div>
          <h2 style="font-family:'{ds["font"]}',serif;font-size:clamp(2rem,3vw,2.8rem);font-weight:900;color:{ds["tx"]};letter-spacing:-1px">Latest <span style="color:{ds["pr"]}">Insights</span></h2>
        </div>
        <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:24px">{cards}</div>
        <div style="text-align:center;margin-top:40px">
          <a href="#" style="display:inline-flex;align-items:center;gap:8px;background:{ds["ca"]};color:{ds["tx"]};border:1px solid {ds["br"]};padding:14px 28px;border-radius:100px;text-decoration:none;font-weight:700;font-size:0.88rem">View All Posts →</a>
        </div>
      </div>
    </section>"""

def make_portfolio_grid(ds: dict, name: str, seed: int) -> str:
    enc = urllib.parse.quote(name)
    items = [(f"Project {i+1}",f"Category {i+1}",f"https://image.pollinations.ai/prompt/{enc}_project_{i+1}_showcase?width=600&height=400&seed={seed+i+20}&nologo=true&model=flux") for i in range(6)]
    cards = ""
    for proj, cat, img in items:
        cards += f"""
        <div style="border-radius:20px;overflow:hidden;position:relative;aspect-ratio:4/3;cursor:pointer" onmouseover="this.querySelector('.overlay').style.opacity=\'1\'" onmouseout="this.querySelector('.overlay').style.opacity=\'0\'">
          <img src="{img}" alt="{proj}" loading="lazy" style="width:100%;height:100%;object-fit:cover;display:block;transition:transform 0.6s" onmouseover="this.style.transform=\'scale(1.08)\'" onmouseout="this.style.transform=\'\'"/>
          <div class="overlay" style="position:absolute;inset:0;background:linear-gradient(to top,rgba(0,0,0,0.8),transparent);opacity:0;transition:opacity 0.3s;display:flex;flex-direction:column;justify-content:flex-end;padding:20px">
            <h4 style="color:#fff;font-weight:700;font-size:0.95rem;margin-bottom:4px">{proj}</h4>
            <p style="color:rgba(255,255,255,0.7);font-size:0.78rem">{cat}</p>
          </div>
        </div>"""
    return f"""
    <section style="padding:100px 5%;background:{ds["bg"]}" id="portfolio">
      <div style="max-width:1280px;margin:0 auto">
        <div style="text-align:center;margin-bottom:60px">
          <div style="display:inline-flex;align-items:center;gap:8px;background:{ds["ca"]};color:{ds["pr"]};font-size:0.72rem;font-weight:800;text-transform:uppercase;letter-spacing:2px;padding:8px 18px;border-radius:100px;margin-bottom:20px;border:1px solid {ds["br"]}">✦ Portfolio</div>
          <h2 style="font-family:'{ds["font"]}',serif;font-size:clamp(2rem,3vw,2.8rem);font-weight:900;color:{ds["tx"]};letter-spacing:-1px">Our <span style="color:{ds["pr"]}">Work</span></h2>
        </div>
        <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:16px">{cards}</div>
      </div>
    </section>"""

def make_video_section(ds: dict) -> str:
    return f"""
    <section style="padding:100px 5%;background:{ds["ca"]}" id="video">
      <div style="max-width:900px;margin:0 auto;text-align:center">
        <div style="text-align:center;margin-bottom:40px">
          <div style="display:inline-flex;align-items:center;gap:8px;background:{ds["ca"]};color:{ds["pr"]};font-size:0.72rem;font-weight:800;text-transform:uppercase;letter-spacing:2px;padding:8px 18px;border-radius:100px;margin-bottom:20px;border:1px solid {ds["br"]}">✦ Watch</div>
          <h2 style="font-family:'{ds["font"]}',serif;font-size:2rem;font-weight:900;color:{ds["tx"]}">See Us In <span style="color:{ds["pr"]}">Action</span></h2>
        </div>
        <div style="border-radius:24px;overflow:hidden;background:#000;position:relative;aspect-ratio:16/9;box-shadow:0 40px 80px rgba(0,0,0,0.3)">
          <div style="position:absolute;inset:0;display:flex;align-items:center;justify-content:center;background:linear-gradient(135deg,{ds["pr"]}22,{ds["ac"]}22)">
            <button onclick="this.closest(\'div\').innerHTML=\'<iframe width=\\\"100%\\\" height=\\\"100%\\\" src=\\\"https://www.youtube.com/embed/dQw4w9WgXcQ?autoplay=1\\\" frameborder=\\\"0\\\" allowfullscreen style=\\\"display:block\\\"></iframe>\'" style="width:80px;height:80px;border-radius:50%;background:{ds["pr"]};border:none;cursor:pointer;display:flex;align-items:center;justify-content:center;box-shadow:0 8px 30px rgba(0,0,0,0.3);transition:all 0.3s" onmouseover="this.style.transform=\'scale(1.1)\'" onmouseout="this.style.transform=\'\'">
              <svg width="30" height="30" viewBox="0 0 24 24" fill="white"><polygon points="5,3 19,12 5,21"/></svg>
            </button>
          </div>
        </div>
      </div>
    </section>"""

# ── MAIN BUILD FUNCTION ───────────────────────────────────────────────────────
def build_template(prompt: str) -> str:
    name = extract_name(prompt)
    cat = get_category(prompt)
    ds = get_design(prompt)
    con = get_content(cat)
    ud = extract_user_data(prompt)
    features = detect_features(prompt)
    seed = abs(hash(prompt)) % 99999
    enc = urllib.parse.quote(prompt[:80])
    is_dark = ds["dark"]
    font = ds["font"]

    phone = ud["phone"] or "+91 99999 99999"
    email_addr = ud["email"] or f"hello@{re.sub(chr(91)+chr(94)+chr(97)+chr(122)+chr(48)+chr(57)+chr(93),'',name.lower())}.com"
    address = ud["address"] or "Mumbai, India"

    imgs = {
        "hero":  f"https://image.pollinations.ai/prompt/ultra_realistic_cinematic_{enc}_dramatic_4k?width=1400&height=800&seed={seed}&nologo=true&model=flux",
        "about": f"https://image.pollinations.ai/prompt/professional_{enc}_team_modern?width=900&height=700&seed={seed+1}&nologo=true&model=flux",
        "g1":    f"https://image.pollinations.ai/prompt/{enc}_showcase_1?width=700&height=500&seed={seed+2}&nologo=true&model=flux",
        "g2":    f"https://image.pollinations.ai/prompt/{enc}_showcase_2?width=700&height=500&seed={seed+3}&nologo=true&model=flux",
        "g3":    f"https://image.pollinations.ai/prompt/{enc}_showcase_3?width=700&height=500&seed={seed+4}&nologo=true&model=flux",
        "g4":    f"https://image.pollinations.ai/prompt/{enc}_showcase_4?width=700&height=500&seed={seed+5}&nologo=true&model=flux",
    }

    tagline = ud["tagline_custom"] or con["tagline"]
    about_text = ud["about_text"] or con["sub"]
    nav_logo_color = "#fff" if is_dark else ds["pr"]
    nav_link_color = "rgba(255,255,255,0.8)" if is_dark else ds["mu"]
    nav_hb_color = "#fff" if is_dark else ds["tx"]
    hero_overlay = f"linear-gradient(135deg,{ds['bg']}F5 0%,{ds['bg']}CC 60%,{ds['pr']}22 100%)"
    card_shadow = "0 40px 80px rgba(0,0,0,0.5)" if is_dark else "0 40px 80px rgba(0,0,0,0.12)"
    hover_shadow = "0 20px 60px rgba(0,0,0,0.3)" if is_dark else "0 20px 60px rgba(0,0,0,0.1)"
    services_bg = "rgba(255,255,255,0.03)" if is_dark else ds["ca"]
    stat_bg = "rgba(0,0,0,0.4)" if is_dark else ds["ca"]

    svcs_html = "".join([f\'<div class="sc" onmouseover="this.style.transform=\'translateY(-6px)\';this.style.borderColor=\\\'{ds["pr"]}\\\';" onmouseout="this.style.transform=\'\';this.style.borderColor=\\\'{ds["br"]}\\\';"><div class="si">{ic}</div><h3>{t}</h3><p>{d}</p></div>\' for ic,t,d in con["services"]])
    stats_html = "".join([f\'<div class="stat"><div class="sn" data-target="{n.replace("+","").replace("★","").replace("K","000").replace("M","000000").replace("%","").replace("Cr","0000000") if n[0].isdigit() else 0}">{n}</div><div class="sl">{l}</div></div>\' for n,l in con["stats"]])
    testi_html = "".join([f\'<div class="tc" onmouseover="this.style.transform=\'translateY(-6px)\';this.style.borderColor=\\\'{ds["pr"]}\\\'" onmouseout="this.style.transform=\'\';this.style.borderColor=\\\'{ds["br"]}\'"><div class="ts">★★★★★</div><p class="tt">"{t}"</p><div class="ta"><div class="av">{a[0]}</div><div><div class="an">{a}</div><div class="ar">{r}</div></div></div></div>\' for a,r,t in con["testi"]])
    gal_html = "".join([f\'<div class="gi" onmouseover="this.querySelector(\'img\').style.transform=\'scale(1.08)\';" onmouseout="this.querySelector(\'img\').style.transform=\'\'"><img src="{imgs[k]}" loading="lazy" alt=""/></div>\' for k in ["g1","g2","g3","g4"]])
    af_html = "".join([f\'<div class="af" onmouseover="this.style.borderColor=\\\'{ds["pr"]}\\\';this.style.transform=\'translateX(4px)\';" onmouseout="this.style.borderColor=\\\'{ds["br"]}\\\';this.style.transform=\'\'"><div class="afi">{ic}</div><div class="aft"><h4>{t}</h4><p>{d}</p></div></div>\' for ic,t,d in con["af"]])

    # Optional sections
    newsletter_html = make_newsletter_section(ds) if features.get("newsletter") else ""
    pricing_html = make_pricing_section(ds, con, name) if features.get("pricing_table") else ""
    faq_html = make_faq_section(ds) if features.get("faq") else ""
    team_html = make_team_section(ds) if features.get("team") else ""
    social_html = make_social_section(ud, ds) if (ud["instagram"] or ud["facebook"] or ud["twitter"] or ud["linkedin"] or ud["youtube"]) else ""
    contact_html = make_contact_section(ud, ds, features, name)
    whatsapp_html = make_whatsapp_button(ud, ds, name)
    sticky_html = make_sticky_cta(ds, con, phone)
    countdown_html = make_countdown_section(ds) if features.get("countdown") else ""
    blog_html = make_blog_section(ds) if features.get("blog") else ""
    portfolio_html = make_portfolio_grid(ds, name, seed) if features.get("portfolio_grid") else ""
    video_html = make_video_section(ds) if features.get("video") else ""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="{name} — {tagline}. {con['sub'][:120]}">
<meta property="og:title" content="{name} — {tagline}">
<meta property="og:description" content="{con['sub'][:160]}">
<title>{name} — {tagline}</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=Playfair+Display:ital,wght@0,700;0,800;0,900;1,700&display=swap" rel="stylesheet">
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
:root{{--bg:{ds["bg"]};--pr:{ds["pr"]};--ac:{ds["ac"]};--tx:{ds["tx"]};--mu:{ds["mu"]};--ca:{ds["ca"]};--br:{ds["br"]};--nb:{ds["nb"]};--nt:{ds["nt"]}}}
html{{scroll-behavior:smooth}}
body{{font-family:"Inter",sans-serif;background:var(--bg);color:var(--tx);overflow-x:hidden;line-height:1.6}}
@keyframes pulse{{0%,100%{{opacity:1;transform:scale(1)}}50%{{opacity:0.6;transform:scale(1.4)}}}}
@keyframes fadeInUp{{from{{opacity:0;transform:translateY(40px)}}to{{opacity:1;transform:translateY(0)}}}}
@keyframes fadeInRight{{from{{opacity:0;transform:translateX(40px)}}to{{opacity:1;transform:translateX(0)}}}}
@keyframes waPulse{{0%,100%{{box-shadow:0 8px 30px rgba(37,211,102,0.4)}}50%{{box-shadow:0 8px 50px rgba(37,211,102,0.7)}}}}
@keyframes spin{{to{{transform:rotate(360deg)}}}}
#loader{{position:fixed;inset:0;background:{ds["bg"]};z-index:99999;display:flex;align-items:center;justify-content:center;transition:opacity 0.5s}}
#loader.hidden{{opacity:0;pointer-events:none}}
.loader-ring{{width:50px;height:50px;border:4px solid {ds["ca"]};border-top-color:{ds["pr"]};border-radius:50%;animation:spin 0.8s linear infinite}}
nav{{position:fixed;top:0;width:100%;z-index:1000;transition:all 0.4s;padding:0 5%}}
nav.sc{{background:var(--nb);backdrop-filter:blur(24px);border-bottom:1px solid var(--br);box-shadow:0 4px 30px rgba(0,0,0,0.08)}}
.ni{{max-width:1280px;margin:0 auto;display:flex;align-items:center;justify-content:space-between;height:72px}}
.nl{{font-family:"{font}",serif;font-size:1.8rem;font-weight:900;color:{nav_logo_color};text-decoration:none;letter-spacing:-0.5px;transition:color 0.3s}}
nav.sc .nl{{color:var(--pr)}}
.nm{{display:flex;align-items:center;gap:36px;list-style:none}}
.nm a{{color:{nav_link_color};text-decoration:none;font-weight:500;font-size:0.9rem;transition:color 0.2s}}
nav.sc .nm a{{color:var(--nt)}}
.nm a:hover{{color:var(--pr)}}
.nc{{background:var(--pr)!important;color:#fff!important;padding:11px 26px;border-radius:100px;font-weight:700!important;transition:all 0.3s!important;box-shadow:0 4px 20px rgba(0,0,0,0.2)}}
.nc:hover{{transform:translateY(-2px)!important;box-shadow:0 8px 30px rgba(0,0,0,0.3)!important}}
.nhb{{display:none;background:none;border:none;cursor:pointer;flex-direction:column;gap:5px;padding:4px}}
.nhb span{{width:24px;height:2px;background:{nav_hb_color};border-radius:2px;display:block;transition:all 0.3s}}
nav.sc .nhb span{{background:var(--tx)}}
.nmob{{display:none;position:fixed;top:72px;left:0;right:0;padding:20px 5%;flex-direction:column;gap:16px;background:var(--nb);backdrop-filter:blur(20px);border-bottom:1px solid var(--br);box-shadow:0 10px 40px rgba(0,0,0,0.1)}}
.nmob.open{{display:flex}}
.nmob a{{color:var(--mu);text-decoration:none;font-weight:600;font-size:0.95rem;padding:8px 0;border-bottom:1px solid var(--br)}}
.nmob .mc{{background:var(--pr);color:#fff!important;text-align:center;padding:14px;border-radius:12px;border:none!important;margin-top:4px}}
.hero{{min-height:100vh;display:flex;align-items:center;padding:100px 5% 80px;position:relative;overflow:hidden;background:var(--bg)}}
.hbg{{position:absolute;inset:0;background:url("{imgs["hero"]}") center/cover no-repeat;opacity:{"0.12" if is_dark else "0.07"};filter:blur(2px);transform:scale(1.05)}}
.hov{{position:absolute;inset:0;background:{hero_overlay}}}
.hsh{{position:absolute;inset:0;overflow:hidden;pointer-events:none}}
.hsh::before{{content:"";position:absolute;top:-30%;right:-10%;width:600px;height:600px;border-radius:50%;background:radial-gradient(circle,{ds["pr"]}{"18" if is_dark else "0D"} 0%,transparent 70%)}}
.hsh::after{{content:"";position:absolute;bottom:-20%;left:-5%;width:400px;height:400px;border-radius:50%;background:radial-gradient(circle,{ds["ac"]}{"12" if is_dark else "0A"} 0%,transparent 70%)}}
.hi{{position:relative;z-index:2;max-width:1280px;margin:0 auto;width:100%;display:grid;grid-template-columns:1fr 1fr;gap:80px;align-items:center}}
.hbadge{{display:inline-flex;align-items:center;gap:8px;background:{"rgba(255,255,255,0.1)" if is_dark else ds["ca"]};backdrop-filter:blur(10px);border:1px solid var(--br);color:var(--tx);padding:9px 20px;border-radius:100px;font-size:0.75rem;font-weight:700;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:24px;animation:fadeInUp 0.6s ease both}}
.bdot{{width:8px;height:8px;border-radius:50%;background:var(--ac);animation:pulse 2s infinite;box-shadow:0 0 10px var(--ac)}}
.ht{{font-family:"{font}",serif;font-size:clamp(2.8rem,4.5vw,4.5rem);font-weight:900;line-height:1.05;letter-spacing:-2px;margin-bottom:16px;color:var(--tx);animation:fadeInUp 0.7s ease 0.1s both}}
.hta{{color:var(--pr);display:block;font-style:italic}}
.hs{{font-size:1.05rem;color:var(--mu);line-height:1.75;margin-bottom:36px;max-width:480px;animation:fadeInUp 0.7s ease 0.2s both}}
.hbtns{{display:flex;gap:14px;flex-wrap:wrap;animation:fadeInUp 0.7s ease 0.3s both}}
.bp{{display:inline-flex;align-items:center;gap:8px;background:var(--pr);color:#fff;font-weight:800;font-size:0.9rem;padding:16px 32px;border-radius:100px;text-decoration:none;transition:all 0.3s;box-shadow:0 8px 30px rgba(0,0,0,0.2)}}
.bp:hover{{transform:translateY(-3px);filter:brightness(1.1);box-shadow:0 16px 40px rgba(0,0,0,0.3)}}
.bs{{display:inline-flex;align-items:center;gap:8px;background:var(--ca);color:var(--tx);font-weight:700;font-size:0.9rem;padding:16px 32px;border-radius:100px;text-decoration:none;border:1px solid var(--br);transition:all 0.3s}}
.bs:hover{{transform:translateY(-3px)}}
.hiw{{position:relative;perspective:1200px;animation:fadeInRight 0.9s ease 0.2s both}}
.hic{{border-radius:24px;overflow:hidden;box-shadow:{card_shadow},0 0 0 1px var(--br);transform:rotateY(-6deg) rotateX(3deg);transition:transform 0.6s ease}}
.hic:hover{{transform:rotateY(0deg) rotateX(0deg)}}
.hic img{{width:100%;height:420px;object-fit:cover;display:block}}
.hib{{position:absolute;bottom:20px;left:20px;background:rgba(0,0,0,0.75);backdrop-filter:blur(20px);border:1px solid rgba(255,255,255,0.15);padding:12px 18px;border-radius:14px;display:flex;align-items:center;gap:10px}}
.ld{{width:8px;height:8px;border-radius:50%;background:#22C55E;box-shadow:0 0 12px #22C55E;animation:pulse 2s infinite}}
.lt{{color:#fff;font-size:0.78rem;font-weight:600}}
.stbar{{background:{stat_bg};border-top:1px solid var(--br);border-bottom:1px solid var(--br);padding:0 5%}}
.sti{{max-width:1280px;margin:0 auto;display:grid;grid-template-columns:repeat(4,1fr)}}
.stat{{padding:32px 24px;text-align:center;border-right:1px solid var(--br);transition:background 0.3s;cursor:default}}
.stat:last-child{{border-right:none}}
.stat:hover{{background:var(--ca)}}
.sn{{font-family:"{font}",serif;font-size:2.4rem;font-weight:900;color:var(--pr);margin-bottom:4px}}
.sl{{font-size:0.72rem;color:var(--mu);font-weight:600;text-transform:uppercase;letter-spacing:1.2px}}
.about{{padding:120px 5%;background:var(--bg)}}
.abi{{max-width:1280px;margin:0 auto;display:grid;grid-template-columns:1fr 1fr;gap:80px;align-items:center}}
.abimg{{border-radius:24px;overflow:hidden;position:relative;box-shadow:{card_shadow}}}
.abimg img{{width:100%;height:480px;object-fit:cover;display:block;transition:transform 0.6s}}
.abimg:hover img{{transform:scale(1.04)}}
.abtag{{position:absolute;top:20px;left:20px;background:var(--pr);color:#fff;font-size:0.72rem;font-weight:800;padding:8px 16px;border-radius:100px;text-transform:uppercase;letter-spacing:1px}}
.sl2{{display:inline-flex;align-items:center;gap:8px;background:var(--ca);color:var(--pr);font-size:0.72rem;font-weight:800;text-transform:uppercase;letter-spacing:2px;padding:8px 18px;border-radius:100px;margin-bottom:20px;border:1px solid var(--br)}}
.sh{{font-family:"{font}",serif;font-size:clamp(2rem,3vw,2.8rem);font-weight:900;color:var(--tx);line-height:1.15;letter-spacing:-1px;margin-bottom:20px}}
.sh span{{color:var(--pr)}}
.ss{{font-size:0.95rem;color:var(--mu);line-height:1.8;margin-bottom:36px}}
.aff{{display:flex;flex-direction:column;gap:14px}}
.af{{display:flex;align-items:flex-start;gap:14px;padding:16px;background:var(--ca);border-radius:16px;border:1px solid var(--br);transition:all 0.3s}}
.afi{{width:42px;height:42px;border-radius:12px;background:var(--bg);border:1px solid var(--br);display:flex;align-items:center;justify-content:center;font-size:1.3rem;flex-shrink:0}}
.aft h4{{font-weight:700;font-size:0.88rem;color:var(--tx);margin-bottom:3px}}
.aft p{{font-size:0.8rem;color:var(--mu)}}
.services{{padding:120px 5%;background:{services_bg}}}
.svi{{max-width:1280px;margin:0 auto}}
.sh2{{text-align:center;margin-bottom:60px}}
.sg{{display:grid;grid-template-columns:repeat(2,1fr);gap:20px}}
.sc{{background:var(--bg);border:1px solid var(--br);border-radius:24px;padding:36px;transition:all 0.4s;position:relative;overflow:hidden;cursor:default}}
.sc::before{{content:"";position:absolute;inset:0;background:linear-gradient(135deg,var(--pr) 0%,transparent 60%);opacity:0;transition:opacity 0.4s}}
.sc:hover::before{{opacity:0.04}}
.si{{font-size:2.6rem;margin-bottom:20px;display:block}}
.sc h3{{font-family:"{font}",serif;font-size:1.25rem;font-weight:800;color:var(--tx);margin-bottom:12px}}
.sc p{{font-size:0.88rem;color:var(--mu);line-height:1.7}}
.gallery{{padding:80px 5%;background:var(--bg)}}
.gli{{max-width:1280px;margin:0 auto}}
.gg{{display:grid;grid-template-columns:repeat(2,1fr);gap:16px;margin-top:48px}}
.gi{{border-radius:20px;overflow:hidden;aspect-ratio:4/3;cursor:pointer;position:relative;box-shadow:0 8px 24px rgba(0,0,0,0.1)}}
.gi img{{width:100%;height:100%;object-fit:cover;display:block;transition:transform 0.6s}}
.gi::after{{content:"";position:absolute;inset:0;background:linear-gradient(to top,rgba(0,0,0,0.5),transparent);opacity:0;transition:opacity 0.3s}}
.gi:hover::after{{opacity:1}}
.testi{{padding:120px 5%;background:{services_bg}}}
.tti{{max-width:1280px;margin:0 auto}}
.tg{{display:grid;grid-template-columns:repeat(3,1fr);gap:20px;margin-top:48px}}
.tc{{background:var(--bg);border:1px solid var(--br);border-radius:24px;padding:32px;transition:all 0.3s;position:relative;overflow:hidden;cursor:default}}
.tc::before{{content:"\\201C";position:absolute;top:-20px;right:16px;font-size:8rem;color:var(--pr);opacity:0.06;font-family:serif;line-height:1}}
.ts{{color:var(--ac);font-size:1rem;letter-spacing:2px;margin-bottom:16px}}
.tt{{font-size:0.9rem;color:var(--mu);line-height:1.75;margin-bottom:24px;font-style:italic}}
.ta{{display:flex;align-items:center;gap:12px}}
.av{{width:44px;height:44px;border-radius:50%;background:linear-gradient(135deg,var(--pr),var(--ac));display:flex;align-items:center;justify-content:center;color:#fff;font-weight:800;font-size:0.9rem;flex-shrink:0}}
.an{{font-weight:700;font-size:0.85rem;color:var(--tx)}}
.ar{{font-size:0.72rem;color:var(--mu)}}
.cta-sec{{padding:120px 5%;background:var(--bg)}}
.ctai{{max-width:1000px;margin:0 auto;border-radius:32px;padding:80px 60px;text-align:center;position:relative;overflow:hidden;background:linear-gradient(135deg,var(--pr) 0%,var(--ac) 100%);box-shadow:0 40px 80px rgba(0,0,0,0.25)}}
.ctai::before{{content:"";position:absolute;top:-50%;right:-10%;width:500px;height:500px;border-radius:50%;background:rgba(255,255,255,0.08);pointer-events:none}}
.ctai h2{{font-family:"{font}",serif;font-size:clamp(2rem,4vw,3rem);font-weight:900;color:#fff;margin-bottom:16px;position:relative;z-index:1;letter-spacing:-1px}}
.ctai p{{font-size:1rem;color:rgba(255,255,255,0.85);margin-bottom:40px;position:relative;z-index:1;max-width:500px;margin-left:auto;margin-right:auto}}
.cbtns{{display:flex;gap:14px;justify-content:center;flex-wrap:wrap;position:relative;z-index:1}}
.cb1{{display:inline-flex;align-items:center;gap:8px;background:#fff;color:var(--pr);font-weight:800;padding:16px 36px;border-radius:100px;text-decoration:none;font-size:0.9rem;transition:all 0.3s;box-shadow:0 8px 30px rgba(0,0,0,0.15)}}
.cb1:hover{{transform:translateY(-3px)}}
.cb2{{display:inline-flex;align-items:center;gap:8px;background:rgba(255,255,255,0.15);color:#fff;font-weight:700;padding:16px 36px;border-radius:100px;text-decoration:none;font-size:0.9rem;border:1px solid rgba(255,255,255,0.3);transition:all 0.3s}}
.cb2:hover{{background:rgba(255,255,255,0.25);transform:translateY(-3px)}}
footer{{padding:60px 5% 100px;border-top:1px solid var(--br);background:{services_bg}}}
.fi{{max-width:1280px;margin:0 auto}}
.ft{{display:grid;grid-template-columns:2fr 1fr 1fr 1fr;gap:48px;margin-bottom:48px}}
.fb p{{font-size:0.82rem;color:var(--mu);margin-top:12px;line-height:1.7;max-width:240px}}
.flogo{{font-family:"{font}",serif;font-size:1.6rem;font-weight:900;color:var(--pr)}}
.fc h4{{font-weight:700;font-size:0.75rem;color:var(--mu);text-transform:uppercase;letter-spacing:1.5px;margin-bottom:16px}}
.fc a{{display:block;color:var(--mu);text-decoration:none;font-size:0.82rem;margin-bottom:10px;transition:color 0.2s}}
.fc a:hover{{color:var(--pr)}}
.fbot{{border-top:1px solid var(--br);padding-top:24px;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px}}
.fbot p{{font-size:0.75rem;color:var(--mu)}}
#backTop{{position:fixed;bottom:90px;right:24px;z-index:9990;width:44px;height:44px;background:var(--pr);color:#fff;border:none;border-radius:50%;cursor:pointer;font-size:1.2rem;display:none;align-items:center;justify-content:center;box-shadow:0 4px 20px rgba(0,0,0,0.2);transition:all 0.3s}}
#backTop:hover{{transform:translateY(-3px)}}
.reveal{{opacity:0;transform:translateY(40px) scale(0.97);transition:opacity 0.7s ease,transform 0.7s ease}}
.reveal.visible{{opacity:1;transform:translateY(0) scale(1)}}
@media(max-width:900px){{
  .hi,.abi{{grid-template-columns:1fr;gap:48px;text-align:center}}
  .hiw{{order:-1}}.hs{{max-width:100%}}.hbtns{{justify-content:center}}
  .sg,.gg{{grid-template-columns:1fr}}
  .tg{{grid-template-columns:1fr}}
  .sti{{grid-template-columns:repeat(2,1fr)}}
  .ft{{grid-template-columns:1fr 1fr;gap:32px}}
  .nm,.nc{{display:none}}.nhb{{display:flex}}
  .ctai{{padding:60px 30px}}
}}
@media(max-width:540px){{
  .sti,.ft{{grid-template-columns:1fr}}
  .ht{{font-size:2.4rem}}
  .fbot{{flex-direction:column;text-align:center}}
}}
</style>
</head>
<body>

<!-- LOADER -->
<div id="loader"><div class="loader-ring"></div></div>

<!-- NAV -->
<nav id="nav">
  <div class="ni">
    <a href="#" class="nl">{name}</a>
    <ul class="nm">
      <li><a href="#about">About</a></li>
      <li><a href="#services">{con["services_title"]}</a></li>
      <li><a href="#gallery">Gallery</a></li>
      {"<li><a href='#pricing'>Pricing</a></li>" if features.get("pricing_table") else ""}
      {"<li><a href='#blog'>Blog</a></li>" if features.get("blog") else ""}
      <li><a href="#contact" class="nc">{con["cta1"]}</a></li>
    </ul>
    <button class="nhb" id="hb"><span></span><span></span><span></span></button>
  </div>
</nav>
<div class="nmob" id="nmo">
  <a href="#about">About</a>
  <a href="#services">{con["services_title"]}</a>
  <a href="#gallery">Gallery</a>
  {"<a href='#pricing'>Pricing</a>" if features.get("pricing_table") else ""}
  {"<a href='#blog'>Blog</a>" if features.get("blog") else ""}
  <a href="#contact" class="mc">{con["cta1"]}</a>
</div>

<!-- HERO -->
<section class="hero" id="home">
  <div class="hbg"></div><div class="hov"></div><div class="hsh"></div>
  <div class="hi">
    <div>
      <div class="hbadge"><span class="bdot"></span>✦ {name} · {cat.replace("_"," ").title()}</div>
      <h1 class="ht">{name}<span class="hta">{tagline}</span></h1>
      <p class="hs">{con["sub"]}</p>
      {"<p style='margin-top:-20px;margin-bottom:24px;font-size:0.9rem;color:var(--pr);font-weight:600'>📞 " + phone + " &nbsp;|&nbsp; ✉️ " + email_addr + "</p>" if ud["phone"] or ud["email"] else ""}
      <div class="hbtns">
        <a href="#contact" class="bp">{con["cta1"]} →</a>
        <a href="#services" class="bs">▶ {con["cta2"]}</a>
        {"<a href='https://wa.me/" + (ud["whatsapp"] or "919999999999").replace("+","").replace(" ","") + "' target='_blank' style='display:inline-flex;align-items:center;gap:8px;background:#25D366;color:#fff;font-weight:700;font-size:0.9rem;padding:16px 24px;border-radius:100px;text-decoration:none'>💬 WhatsApp</a>" if features.get("whatsapp_btn") else ""}
      </div>
    </div>
    <div class="hiw">
      <div class="hic">
        <img src="{imgs["hero"]}" alt="{name}" loading="eager"/>
        <div class="hib"><div class="ld"></div><span class="lt">Live &amp; Open Now</span></div>
      </div>
    </div>
  </div>
</section>

<!-- STATS -->
<div class="stbar"><div class="sti">{stats_html}</div></div>

{countdown_html}

<!-- ABOUT -->
<section class="about" id="about">
  <div class="abi">
    <div class="abimg reveal">
      <img src="{imgs["about"]}" alt="About {name}" loading="lazy"/>
      <div class="abtag">Our Story</div>
    </div>
    <div class="reveal">
      <div class="sl2">✦ About Us</div>
      <h2 class="sh">Built for <span>Excellence</span>.</h2>
      <p class="ss">{about_text}</p>
      <div class="aff">{af_html}</div>
    </div>
  </div>
</section>

<!-- SERVICES -->
<section class="services" id="services">
  <div class="svi">
    <div class="sh2">
      <div class="sl2">✦ {con["services_title"]}</div>
      <h2 class="sh" style="text-align:center">Why Choose <span>{name}</span></h2>
      <p style="color:var(--mu);font-size:0.95rem;max-width:500px;margin:12px auto 0">Everything you need, crafted to the highest possible standard.</p>
    </div>
    <div class="sg reveal">{svcs_html}</div>
  </div>
</section>

{video_html}

<!-- GALLERY -->
<section class="gallery" id="gallery">
  <div class="gli">
    <div class="sh2">
      <div class="sl2">✦ Gallery</div>
      <h2 class="sh" style="text-align:center">See It For <span>Yourself</span></h2>
    </div>
    <div class="gg reveal">{gal_html}</div>
  </div>
</section>

{portfolio_html}

{team_html}

<!-- TESTIMONIALS -->
<section class="testi" id="testimonials">
  <div class="tti">
    <div class="sh2">
      <div class="sl2">✦ Testimonials</div>
      <h2 class="sh" style="text-align:center">What Our <span>Clients Say</span></h2>
    </div>
    <div class="tg reveal">{testi_html}</div>
  </div>
</section>

{pricing_html}

{blog_html}

{faq_html}

{newsletter_html}

{contact_html}

{social_html}

<!-- CTA -->
<section class="cta-sec" id="cta">
  <div class="ctai reveal">
    <h2>Ready to Get Started?</h2>
    <p>Join thousands who trust {name}. First step is free. No commitment needed.</p>
    <div class="cbtns">
      <a href="#contact" class="cb1">{con["cta1"]} →</a>
      <a href="tel:{phone}" class="cb2">📞 {phone}</a>
    </div>
  </div>
</section>

<!-- FOOTER -->
<footer>
  <div class="fi">
    <div class="ft">
      <div class="fb">
        <div class="flogo">{name}</div>
        <p>{con["sub"][:100]}...</p>
        <div style="margin-top:16px;display:flex;gap:12px;flex-wrap:wrap">
          {"<a href='https://instagram.com/" + ud["instagram"] + "' target='_blank' style='color:var(--pr);font-size:1.2rem;text-decoration:none' title='Instagram'>📸</a>" if ud["instagram"] else ""}
          {"<a href='https://facebook.com/" + ud["facebook"] + "' target='_blank' style='color:var(--pr);font-size:1.2rem;text-decoration:none' title='Facebook'>👍</a>" if ud["facebook"] else ""}
          {"<a href='https://twitter.com/" + ud["twitter"] + "' target='_blank' style='color:var(--pr);font-size:1.2rem;text-decoration:none' title='Twitter'>🐦</a>" if ud["twitter"] else ""}
          {"<a href='https://linkedin.com/in/" + ud["linkedin"] + "' target='_blank' style='color:var(--pr);font-size:1.2rem;text-decoration:none' title='LinkedIn'>💼</a>" if ud["linkedin"] else ""}
          {"<a href='https://youtube.com/" + ud["youtube"] + "' target='_blank' style='color:var(--pr);font-size:1.2rem;text-decoration:none' title='YouTube'>▶️</a>" if ud["youtube"] else ""}
        </div>
      </div>
      <div class="fc">
        <h4>Company</h4>
        <a href="#about">About Us</a>
        <a href="#services">{con["services_title"]}</a>
        <a href="#gallery">Gallery</a>
        {"<a href='#team'>Our Team</a>" if features.get("team") else ""}
        {"<a href='#blog'>Blog</a>" if features.get("blog") else ""}
      </div>
      <div class="fc">
        <h4>Services</h4>
        {"".join([f\'<a href="#services">{s[1]}</a>\' for s in con["services"]])}
      </div>
      <div class="fc">
        <h4>Contact</h4>
        <a href="tel:{phone}">📞 {phone}</a>
        <a href="mailto:{email_addr}">✉️ Email Us</a>
        {"<a href='https://wa.me/" + (ud["whatsapp"] or phone).replace("+","").replace(" ","") + "' target='_blank'>💬 WhatsApp</a>" if features.get("whatsapp_btn") else ""}
        <a href="#contact">📍 {address[:30]}...</a>
        {"<p style='color:var(--mu);font-size:0.78rem;margin-top:8px'>⏰ " + (ud["opening_hours"] or "Mon-Sat 9AM-8PM") + "</p>" if ud["opening_hours"] else ""}
      </div>
    </div>
    <div class="fbot">
      <p>© 2024 {name}. All rights reserved.</p>
      <p style="display:flex;gap:16px"><a href="#" style="color:var(--mu);text-decoration:none;font-size:0.72rem">Privacy Policy</a><a href="#" style="color:var(--mu);text-decoration:none;font-size:0.72rem">Terms of Service</a></p>
      <p>Built with Dacexy AI</p>
    </div>
  </div>
</footer>

<!-- FLOATING ELEMENTS -->
{whatsapp_html}
{sticky_html}
<button id="backTop" onclick="window.scrollTo({{top:0,behavior:'smooth'}})">↑</button>

<script>
// Loader
window.addEventListener('load',()=>{{
  setTimeout(()=>document.getElementById('loader').classList.add('hidden'),600);
}});

// Nav scroll
const nav=document.getElementById('nav');
const stickyCTA=document.getElementById('stickyCTA');
const backTop=document.getElementById('backTop');
window.addEventListener('scroll',()=>{{
  nav.classList.toggle('sc',scrollY>60);
  if(stickyCTA)stickyCTA.style.transform=scrollY>300?'translateY(0)':'translateY(100%)';
  if(backTop)backTop.style.display=scrollY>400?'flex':'none';
}});

// Mobile menu
const hb=document.getElementById('hb'),nmo=document.getElementById('nmo');
hb.addEventListener('click',()=>nmo.classList.toggle('open'));
nmo.querySelectorAll('a').forEach(a=>a.addEventListener('click',()=>nmo.classList.remove('open')));

// Scroll reveal
const obs=new IntersectionObserver(entries=>entries.forEach(e=>{{
  if(e.isIntersecting)e.target.classList.add('visible');
}}),{{threshold:0.1}});
document.querySelectorAll('.sc,.tc,.af,.gi,.stat,.reveal').forEach(el=>{{
  el.classList.add('reveal');
  obs.observe(el);
}});

// FAQ toggle
function toggleFAQ(btn){{
  const ans=btn.nextElementSibling;
  const icon=btn.querySelector('span:last-child');
  const isOpen=ans.style.display==='block';
  ans.style.display=isOpen?'none':'block';
  icon.textContent=isOpen?'+':'−';
  icon.style.transform=isOpen?'':'rotate(45deg)';
}}

// Form submit
function handleForm(e){{
  e.preventDefault();
  const btn=e.target.querySelector('button[type="submit"]');
  const orig=btn.innerHTML;
  btn.innerHTML='⏳ Sending...';
  btn.disabled=true;
  setTimeout(()=>{{
    btn.innerHTML='✅ Sent!';
    document.getElementById('formSuccess').style.display='block';
    e.target.reset();
    setTimeout(()=>{{btn.innerHTML=orig;btn.disabled=false;}},3000);
  }},1500);
}}

// Newsletter
function handleNewsletter(e){{
  e.preventDefault();
  document.getElementById('nlSuccess').style.display='block';
  e.target.reset();
}}

// Countdown timer
function startCountdown(){{
  const target=new Date();
  target.setDate(target.getDate()+7);
  function update(){{
    const now=new Date();
    const diff=target-now;
    if(diff<=0)return;
    const d=Math.floor(diff/86400000);
    const h=Math.floor((diff%86400000)/3600000);
    const m=Math.floor((diff%3600000)/60000);
    const s=Math.floor((diff%60000)/1000);
    const dEl=document.getElementById('days');
    const hEl=document.getElementById('hours');
    const mEl=document.getElementById('mins');
    const sEl=document.getElementById('secs');
    if(dEl)dEl.textContent=String(d).padStart(2,'0');
    if(hEl)hEl.textContent=String(h).padStart(2,'0');
    if(mEl)mEl.textContent=String(m).padStart(2,'0');
    if(sEl)sEl.textContent=String(s).padStart(2,'0');
  }}
  update();
  setInterval(update,1000);
}}
startCountdown();

// Input focus effects
document.querySelectorAll('input,textarea').forEach(el=>{{
  el.addEventListener('focus',()=>el.style.borderColor='var(--pr)');
  el.addEventListener('blur',()=>el.style.borderColor='');
}});

// Smooth image loading
document.querySelectorAll('img').forEach(img=>{{
  img.style.opacity='0';
  img.style.transition='opacity 0.5s ease';
  if(img.complete){{img.style.opacity='1';}}
  else{{img.addEventListener('load',()=>img.style.opacity='1');}}
}});
</script>
</body>
</html>"""

async def generate_website(prompt: str, ai=None) -> str:
    try:
        return build_template(prompt)
    except Exception as e:
        log.error(f"Website generation error: {e}")
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
