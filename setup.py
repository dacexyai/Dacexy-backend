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
    WAVESPEED_API_KEY: str = ""
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
import urllib.parse
import re
from src.infrastructure.ai_providers.deepseek import DeepSeekProvider

log = logging.getLogger("website")

def extract_name(prompt: str) -> str:
    p = prompt.strip()
    patterns = [
        r"(?:named?|called?|for)\s+([A-Z][a-zA-Z0-9\s]{1,30}?)(?:\s+(?:with|that|which|a\s|an\s|the\s|website|app|saas|platform|startup|business|restaurant|store|shop|company|landing|page)|\.|,|$)",
        r"^(?:a\s+)?(?:website|landing page|page|site|app|saas|platform|startup|business|restaurant|store|shop|company|portfolio)\s+(?:for\s+)?([A-Z][a-zA-Z0-9\s]{1,25}?)(?:\s+with|\s+that|$)",
        r"^([A-Z][a-zA-Z0-9]{1,20})\s+",
    ]
    for pat in patterns:
        m = re.search(pat, p, re.IGNORECASE)
        if m:
            name = m.group(1).strip()
            if 2 <= len(name) <= 30 and not name.lower() in ["a","an","the","my","our","build","make","create","generate"]:
                return name.title()
    words = [w for w in p.replace(",","").replace(".","").split() if len(w) > 2 and w.lower() not in ["for","the","with","that","this","and","build","make","create","generate","website","page","site","app","landing","saas","platform","startup","business","restaurant","store","shop","company","portfolio","a","an","my","our"]]
    if words:
        return words[0].title()
    return "Our Business"

def get_category(prompt: str) -> str:
    p = prompt.lower()
    if any(x in p for x in ["restaurant","food","cafe","kitchen","dining","menu","eat","chef","pizza","hotel"]):
        return "restaurant"
    if any(x in p for x in ["saas","software","app","platform","tech","startup","ai","tool","dashboard","crm"]):
        return "saas"
    if any(x in p for x in ["portfolio","designer","freelance","artist","creative","photography","studio"]):
        return "portfolio"
    if any(x in p for x in ["shop","store","ecommerce","product","sell","buy","fashion","clothing","brand"]):
        return "ecommerce"
    if any(x in p for x in ["agency","marketing","consultant","service","firm","company","corporate"]):
        return "agency"
    return "business"

def build_template(prompt: str) -> str:
    name = extract_name(prompt)
    category = get_category(prompt)
    encoded = urllib.parse.quote(prompt[:80])
    seed1 = abs(hash(prompt)) % 99999
    seed2 = abs(hash(prompt + "hero")) % 99999
    seed3 = abs(hash(prompt + "about")) % 99999
    seed4 = abs(hash(prompt + "gallery")) % 99999
    img_hero = f"https://image.pollinations.ai/prompt/professional_{encoded}_hero_banner?width=1200&height=600&seed={seed1}&nologo=true&model=flux"
    img_about = f"https://image.pollinations.ai/prompt/professional_{encoded}_team_office?width=700&height=500&seed={seed2}&nologo=true&model=flux"
    img2 = f"https://image.pollinations.ai/prompt/{encoded}_showcase?width=600&height=400&seed={seed3}&nologo=true&model=flux"
    img3 = f"https://image.pollinations.ai/prompt/{encoded}_product?width=600&height=400&seed={seed4}&nologo=true&model=flux"

    if category == "restaurant":
        tagline = f"Authentic flavors, unforgettable experiences at {name}"
        features = [("🍽️","Exquisite Menu","From starters to desserts, every dish is crafted with the finest ingredients."),("👨‍🍳","Expert Chefs","Our award-winning chefs bring decades of culinary expertise to your plate."),("🌿","Fresh Ingredients","We source locally and seasonally to ensure the highest quality in every bite."),("🎉","Private Dining","Perfect for celebrations, corporate events, and intimate gatherings."),("⭐","5-Star Service","Attentive, warm hospitality that makes every visit memorable."),("🚗","Free Parking","Convenient free parking available for all our guests.")]
        cta = "Reserve a Table"
        section2 = "Our Signature Dishes"
    elif category == "saas":
        tagline = f"{name} — The smarter way to work, grow, and succeed"
        features = [("⚡","Lightning Fast","10x faster than traditional solutions with our optimized infrastructure."),("🔒","Enterprise Security","Bank-grade encryption and SOC2 compliance keeps your data safe."),("🤖","AI-Powered","Smart automation that learns and adapts to your workflow automatically."),("📊","Real-time Analytics","Beautiful dashboards with actionable insights at your fingertips."),("🔗","Easy Integration","Connect with 200+ tools you already use in just a few clicks."),("💬","24/7 Support","Dedicated support team available around the clock to help you succeed.")]
        cta = "Start Free Trial"
        section2 = "Powerful Features"
    elif category == "portfolio":
        tagline = f"Creative work that speaks for itself — {name}"
        features = [("🎨","UI/UX Design","Beautiful, intuitive interfaces that users love and businesses need."),("💻","Web Development","Clean, performant code built with modern frameworks and best practices."),("📱","Mobile Apps","Native and cross-platform apps that delight users on every device."),("🎬","Motion Design","Stunning animations and video content that bring brands to life."),("📸","Photography","Professional photography that captures moments and tells stories."),("🚀","Brand Strategy","Complete brand identity from logo to full design system.")]
        cta = "View Portfolio"
        section2 = "Featured Projects"
    elif category == "ecommerce":
        tagline = f"Shop the finest collection at {name}"
        features = [("🚚","Fast Delivery","Free delivery on orders above ₹999. Get it in 2-3 business days."),("↩️","Easy Returns","30-day hassle-free returns. No questions asked."),("✅","Quality Assured","Every product is quality-checked before shipping to you."),("💳","Secure Payments","UPI, cards, net banking — all payments are 100% secure."),("🎁","Gift Wrapping","Beautiful gift packaging available for all orders."),("⭐","Premium Quality","Handpicked products from the best brands and artisans.")]
        cta = "Shop Now"
        section2 = "Featured Products"
    else:
        tagline = f"Delivering excellence and innovation — {name}"
        features = [("⚡","Fast & Reliable","We deliver results quickly without compromising on quality or reliability."),("🛡️","Trusted Partner","Hundreds of businesses trust us with their most important projects."),("🎯","Results Driven","Every strategy is focused on measurable outcomes and real growth."),("🌍","Global Reach","Serving clients across India and internationally with consistent excellence."),("💡","Innovation First","We stay ahead of trends to give you a competitive advantage."),("🤝","Dedicated Support","Our team is always available to ensure your complete satisfaction.")]
        cta = "Get Started"
        section2 = "Our Services"

    features_html = "".join([f'<div class="feature-card"><div class="feature-icon">{f[0]}</div><h3>{f[1]}</h3><p>{f[2]}</p></div>' for f in features])

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{name}</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=Playfair+Display:wght@700;800&display=swap" rel="stylesheet">
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
:root{{--primary:#6366f1;--primary-dark:#4f46e5;--accent:#f59e0b;--dark:#0f172a;--gray:#64748b;--light:#f8fafc}}
body{{font-family:"Inter",sans-serif;color:var(--dark);background:#fff;overflow-x:hidden}}
html{{scroll-behavior:smooth}}
/* NAV */
nav{{position:fixed;top:0;width:100%;z-index:1000;transition:all 0.3s;padding:0 5%}}
nav.scrolled{{background:rgba(255,255,255,0.97);backdrop-filter:blur(20px);box-shadow:0 1px 30px rgba(0,0,0,0.08)}}
.nav-inner{{max-width:1200px;margin:0 auto;display:flex;align-items:center;justify-content:space-between;height:70px}}
.logo{{font-family:"Playfair Display",serif;font-size:1.6rem;font-weight:800;background:linear-gradient(135deg,var(--primary),#8b5cf6);-webkit-background-clip:text;-webkit-text-fill-color:transparent}}
.nav-links{{display:flex;gap:36px;list-style:none;align-items:center}}
.nav-links a{{color:rgba(255,255,255,0.9);text-decoration:none;font-weight:500;font-size:0.9rem;transition:all 0.2s}}
nav.scrolled .nav-links a{{color:var(--gray)}}
.nav-links a:hover{{color:#fff}}
nav.scrolled .nav-links a:hover{{color:var(--primary)}}
.nav-cta{{background:linear-gradient(135deg,var(--primary),#8b5cf6)!important;color:#fff!important;padding:10px 24px;border-radius:50px!important;font-weight:600!important}}
/* HERO */
.hero{{min-height:100vh;background:linear-gradient(135deg,#0f172a 0%,#1e1b4b 40%,#312e81 70%,#4c1d95 100%);display:flex;align-items:center;padding:90px 5% 60px;position:relative;overflow:hidden}}
.hero::before{{content:"";position:absolute;top:0;left:0;right:0;bottom:0;background:url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%239C92AC' fill-opacity='0.05'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E");opacity:0.4}}
.hero-content{{max-width:1200px;margin:0 auto;display:grid;grid-template-columns:1.1fr 0.9fr;gap:80px;align-items:center;position:relative;z-index:1}}
.hero-badge{{display:inline-flex;align-items:center;gap:8px;background:rgba(255,255,255,0.1);border:1px solid rgba(255,255,255,0.2);color:rgba(255,255,255,0.9);padding:8px 16px;border-radius:50px;font-size:0.8rem;font-weight:600;margin-bottom:24px;backdrop-filter:blur(10px)}}
.hero-badge::before{{content:"✨"}}
.hero-text h1{{font-family:"Playfair Display",serif;font-size:4rem;font-weight:800;color:#fff;line-height:1.15;margin-bottom:24px}}
.hero-text h1 span{{background:linear-gradient(135deg,#f59e0b,#f97316);-webkit-background-clip:text;-webkit-text-fill-color:transparent}}
.hero-text p{{font-size:1.15rem;color:rgba(255,255,255,0.75);margin-bottom:40px;line-height:1.8;max-width:520px}}
.hero-btns{{display:flex;gap:16px;flex-wrap:wrap}}
.btn-hero-primary{{background:linear-gradient(135deg,var(--accent),#f97316);color:#fff;padding:16px 36px;border-radius:50px;font-weight:700;font-size:1rem;text-decoration:none;transition:all 0.3s;box-shadow:0 8px 30px rgba(245,158,11,0.4)}}
.btn-hero-primary:hover{{transform:translateY(-3px);box-shadow:0 15px 40px rgba(245,158,11,0.5)}}
.btn-hero-secondary{{border:2px solid rgba(255,255,255,0.4);color:#fff;padding:16px 36px;border-radius:50px;font-weight:600;font-size:1rem;text-decoration:none;transition:all 0.3s;backdrop-filter:blur(10px)}}
.btn-hero-secondary:hover{{background:rgba(255,255,255,0.1);border-color:rgba(255,255,255,0.7)}}
.hero-stats{{display:flex;gap:32px;margin-top:48px}}
.hero-stat{{text-align:center}}
.hero-stat-num{{font-size:2rem;font-weight:800;color:#fff}}
.hero-stat-label{{font-size:0.75rem;color:rgba(255,255,255,0.6);margin-top:4px;text-transform:uppercase;letter-spacing:1px}}
.hero-image{{position:relative}}
.hero-image img{{width:100%;border-radius:24px;box-shadow:0 40px 80px rgba(0,0,0,0.5);transform:perspective(1000px) rotateY(-5deg)}}
.hero-image::before{{content:"";position:absolute;inset:-2px;border-radius:26px;background:linear-gradient(135deg,rgba(99,102,241,0.5),rgba(139,92,246,0.5));z-index:-1;filter:blur(20px)}}
/* SECTIONS */
.section{{padding:100px 5%}}
.section-inner{{max-width:1200px;margin:0 auto}}
.section-badge{{display:inline-block;background:linear-gradient(135deg,rgba(99,102,241,0.1),rgba(139,92,246,0.1));color:var(--primary);font-size:0.75rem;font-weight:700;padding:6px 16px;border-radius:50px;border:1px solid rgba(99,102,241,0.2);text-transform:uppercase;letter-spacing:1px;margin-bottom:16px}}
.section-title{{font-family:"Playfair Display",serif;font-size:2.8rem;font-weight:800;margin-bottom:16px;color:var(--dark)}}
.section-subtitle{{color:var(--gray);font-size:1.1rem;max-width:580px;margin:0 auto 60px;line-height:1.7}}
.text-center{{text-align:center}}
/* FEATURES */
.features{{background:var(--light)}}
.features-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:28px}}
.feature-card{{background:#fff;border-radius:20px;padding:36px 28px;border:1px solid #e2e8f0;transition:all 0.3s;position:relative;overflow:hidden}}
.feature-card::before{{content:"";position:absolute;top:0;left:0;right:0;height:3px;background:linear-gradient(135deg,var(--primary),#8b5cf6);transform:scaleX(0);transition:transform 0.3s;transform-origin:left}}
.feature-card:hover{{transform:translateY(-6px);box-shadow:0 25px 50px rgba(99,102,241,0.15);border-color:rgba(99,102,241,0.3)}}
.feature-card:hover::before{{transform:scaleX(1)}}
.feature-icon{{width:60px;height:60px;background:linear-gradient(135deg,rgba(99,102,241,0.1),rgba(139,92,246,0.1));border-radius:16px;display:flex;align-items:center;justify-content:center;font-size:1.8rem;margin-bottom:20px}}
.feature-card h3{{font-size:1.15rem;font-weight:700;margin-bottom:12px;color:var(--dark)}}
.feature-card p{{color:var(--gray);line-height:1.7;font-size:0.93rem}}
/* ABOUT */
.about{{background:#fff}}
.about-grid{{display:grid;grid-template-columns:1fr 1fr;gap:80px;align-items:center}}
.about-img{{position:relative}}
.about-img img{{width:100%;border-radius:24px;box-shadow:0 30px 60px rgba(0,0,0,0.12)}}
.about-img::after{{content:"";position:absolute;bottom:-20px;right:-20px;width:70%;height:70%;border-radius:24px;background:linear-gradient(135deg,rgba(99,102,241,0.15),rgba(139,92,246,0.15));z-index:-1}}
.about-text h2{{font-family:"Playfair Display",serif;font-size:2.4rem;font-weight:800;margin-bottom:20px;color:var(--dark)}}
.about-text p{{color:var(--gray);line-height:1.8;margin-bottom:16px;font-size:1rem}}
.stats{{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-top:36px}}
.stat{{text-align:center;background:var(--light);border-radius:16px;padding:24px 16px}}
.stat-number{{font-size:2.2rem;font-weight:900;background:linear-gradient(135deg,var(--primary),#8b5cf6);-webkit-background-clip:text;-webkit-text-fill-color:transparent}}
.stat-label{{font-size:0.8rem;color:var(--gray);margin-top:6px;font-weight:500}}
/* GALLERY */
.gallery{{background:var(--light)}}
.gallery-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:20px}}
.gallery-item{{border-radius:20px;overflow:hidden;position:relative;group:cursor-pointer}}
.gallery-item img{{width:100%;height:250px;object-fit:cover;transition:transform 0.4s}}
.gallery-item:hover img{{transform:scale(1.08)}}
.gallery-overlay{{position:absolute;inset:0;background:linear-gradient(to top,rgba(99,102,241,0.8),transparent);opacity:0;transition:opacity 0.3s;display:flex;align-items:flex-end;padding:20px}}
.gallery-item:hover .gallery-overlay{{opacity:1}}
.gallery-overlay-text{{color:#fff;font-weight:600;font-size:0.9rem}}
/* TESTIMONIALS */
.testimonials{{background:linear-gradient(135deg,#0f172a,#1e1b4b)}}
.testimonials .section-title{{color:#fff}}
.testimonials .section-subtitle{{color:rgba(255,255,255,0.6)}}
.testimonials-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:24px}}
.testimonial-card{{background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.1);border-radius:20px;padding:32px;backdrop-filter:blur(10px);transition:all 0.3s}}
.testimonial-card:hover{{background:rgba(255,255,255,0.08);transform:translateY(-4px)}}
.stars{{color:#f59e0b;font-size:1rem;margin-bottom:16px;letter-spacing:2px}}
.testimonial-text{{color:rgba(255,255,255,0.85);line-height:1.8;font-style:italic;margin-bottom:24px;font-size:0.95rem}}
.testimonial-author{{display:flex;align-items:center;gap:12px}}
.author-avatar{{width:48px;height:48px;border-radius:50%;background:linear-gradient(135deg,var(--primary),#8b5cf6);display:flex;align-items:center;justify-content:center;color:#fff;font-weight:800;font-size:1.1rem}}
.author-name{{color:#fff;font-weight:700;font-size:0.95rem}}
.author-role{{color:rgba(255,255,255,0.5);font-size:0.8rem;margin-top:2px}}
/* PRICING */
.pricing-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:24px;max-width:1000px;margin:0 auto}}
.pricing-card{{background:#fff;border:2px solid #e2e8f0;border-radius:24px;padding:40px 32px;text-align:center;transition:all 0.3s;position:relative}}
.pricing-card.popular{{border-color:var(--primary);box-shadow:0 25px 60px rgba(99,102,241,0.2)}}
.popular-badge{{position:absolute;top:-14px;left:50%;transform:translateX(-50%);background:linear-gradient(135deg,var(--primary),#8b5cf6);color:#fff;font-size:0.75rem;font-weight:700;padding:6px 20px;border-radius:50px;white-space:nowrap}}
.pricing-name{{font-size:1.1rem;font-weight:700;color:var(--gray);text-transform:uppercase;letter-spacing:1px;margin-bottom:12px}}
.pricing-price{{font-size:3.5rem;font-weight:900;color:var(--dark);line-height:1}}
.pricing-price sub{{font-size:1rem;color:var(--gray);font-weight:400}}
.pricing-features{{list-style:none;margin:28px 0;text-align:left}}
.pricing-features li{{color:var(--gray);padding:10px 0;border-bottom:1px solid #f1f5f9;font-size:0.9rem;display:flex;align-items:center;gap:8px}}
.pricing-features li::before{{content:"✓";color:var(--primary);font-weight:700;flex-shrink:0}}
.btn-plan{{display:block;background:linear-gradient(135deg,var(--primary),#8b5cf6);color:#fff;padding:16px;border-radius:14px;font-weight:700;text-decoration:none;margin-top:24px;transition:all 0.3s}}
.btn-plan:hover{{transform:translateY(-2px);box-shadow:0 10px 30px rgba(99,102,241,0.4)}}
.btn-plan.outline{{background:transparent;border:2px solid var(--primary);color:var(--primary)}}
.btn-plan.outline:hover{{background:var(--primary);color:#fff}}
/* CTA */
.cta-section{{background:linear-gradient(135deg,var(--primary),#8b5cf6,#ec4899);padding:100px 5%;text-align:center}}
.cta-section h2{{font-family:"Playfair Display",serif;font-size:3rem;font-weight:800;color:#fff;margin-bottom:16px}}
.cta-section p{{color:rgba(255,255,255,0.85);font-size:1.15rem;margin-bottom:40px}}
.btn-cta{{display:inline-block;background:#fff;color:var(--primary);padding:18px 48px;border-radius:50px;font-weight:800;font-size:1.05rem;text-decoration:none;transition:all 0.3s;box-shadow:0 10px 40px rgba(0,0,0,0.2)}}
.btn-cta:hover{{transform:translateY(-3px);box-shadow:0 20px 50px rgba(0,0,0,0.3)}}
/* CONTACT */
.contact-grid{{display:grid;grid-template-columns:1fr 1.5fr;gap:60px;align-items:start}}
.contact-info h3{{font-size:1.4rem;font-weight:700;margin-bottom:16px}}
.contact-detail{{display:flex;align-items:center;gap:12px;margin-bottom:20px;color:var(--gray)}}
.contact-detail-icon{{width:44px;height:44px;background:linear-gradient(135deg,rgba(99,102,241,0.1),rgba(139,92,246,0.1));border-radius:12px;display:flex;align-items:center;justify-content:center;font-size:1.1rem;flex-shrink:0}}
.contact-form-card{{background:var(--light);border-radius:24px;padding:40px}}
.form-row{{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:16px}}
.form-group{{display:flex;flex-direction:column;margin-bottom:16px}}
.form-group label{{color:var(--dark);font-size:0.85rem;font-weight:600;margin-bottom:8px}}
.form-group input,.form-group textarea,.form-group select{{background:#fff;border:2px solid #e2e8f0;border-radius:12px;padding:14px 16px;color:var(--dark);font-size:0.95rem;outline:none;width:100%;font-family:inherit;transition:border-color 0.2s}}
.form-group input:focus,.form-group textarea:focus{{border-color:var(--primary)}}
.form-group textarea{{height:130px;resize:vertical}}
.btn-submit{{width:100%;background:linear-gradient(135deg,var(--primary),#8b5cf6);color:#fff;padding:16px;border-radius:14px;font-weight:700;font-size:1rem;border:none;cursor:pointer;transition:all 0.3s}}
.btn-submit:hover{{transform:translateY(-2px);box-shadow:0 10px 30px rgba(99,102,241,0.4)}}
/* FOOTER */
footer{{background:#0f172a;color:rgba(255,255,255,0.6);padding:64px 5% 28px}}
.footer-inner{{max-width:1200px;margin:0 auto}}
.footer-grid{{display:grid;grid-template-columns:2fr 1fr 1fr 1fr;gap:48px;margin-bottom:48px}}
.footer-brand .logo{{font-size:1.6rem;display:block;margin-bottom:16px}}
.footer-brand p{{font-size:0.9rem;line-height:1.7;max-width:260px}}
.footer-col h4{{color:#fff;font-weight:700;margin-bottom:20px;font-size:0.9rem;text-transform:uppercase;letter-spacing:1px}}
.footer-col ul{{list-style:none}}
.footer-col ul li{{margin-bottom:12px}}
.footer-col ul li a{{color:rgba(255,255,255,0.5);text-decoration:none;font-size:0.9rem;transition:color 0.2s}}
.footer-col ul li a:hover{{color:var(--primary)}}
.footer-bottom{{border-top:1px solid rgba(255,255,255,0.08);padding-top:28px;display:flex;justify-content:space-between;align-items:center;font-size:0.85rem;flex-wrap:gap;gap:12px}}
.footer-links{{display:flex;gap:24px}}
.footer-links a{{color:rgba(255,255,255,0.5);text-decoration:none;transition:color 0.2s}}
.footer-links a:hover{{color:var(--primary)}}
/* MOBILE */
@media(max-width:768px){{
  .hero-content,.about-grid,.contact-grid,.footer-grid{{grid-template-columns:1fr}}
  .hero-text h1{{font-size:2.4rem}}
  .section-title{{font-size:2rem}}
  .features-grid,.testimonials-grid,.pricing-grid,.gallery-grid{{grid-template-columns:1fr}}
  .form-row{{grid-template-columns:1fr}}
  .stats{{grid-template-columns:repeat(2,1fr)}}
  .nav-links{{display:none}}
  .hero-stats{{gap:20px}}
  .hero-stat-num{{font-size:1.5rem}}
  .footer-bottom{{flex-direction:column;text-align:center}}
}}
/* ANIMATIONS */
.fade-up{{opacity:0;transform:translateY(30px);transition:all 0.6s ease}}
.fade-up.visible{{opacity:1;transform:translateY(0)}}
</style>
</head>
<body>
<nav id="navbar">
  <div class="nav-inner">
    <span class="logo">{name}</span>
    <ul class="nav-links">
      <li><a href="#features">Features</a></li>
      <li><a href="#about">About</a></li>
      <li><a href="#pricing">Pricing</a></li>
      <li><a href="#contact" class="nav-cta">{cta}</a></li>
    </ul>
  </div>
</nav>

<section class="hero">
  <div class="hero-content">
    <div class="hero-text">
      <div class="hero-badge">Introducing {name}</div>
      <h1>{name} — <span>Built for the future</span></h1>
      <p>{tagline}</p>
      <div class="hero-btns">
        <a href="#contact" class="btn-hero-primary">{cta} →</a>
        <a href="#features" class="btn-hero-secondary">See How It Works</a>
      </div>
      <div class="hero-stats">
        <div class="hero-stat"><div class="hero-stat-num">10K+</div><div class="hero-stat-label">Happy Users</div></div>
        <div class="hero-stat"><div class="hero-stat-num">99%</div><div class="hero-stat-label">Satisfaction</div></div>
        <div class="hero-stat"><div class="hero-stat-num">24/7</div><div class="hero-stat-label">Support</div></div>
      </div>
    </div>
    <div class="hero-image fade-up">
      <img src="{img_hero}" alt="{name}" loading="lazy">
    </div>
  </div>
</section>

<section class="section features" id="features">
  <div class="section-inner">
    <div class="text-center">
      <span class="section-badge">{section2}</span>
      <h2 class="section-title">Everything You Need</h2>
      <p class="section-subtitle">Powerful features designed to help you grow faster and work smarter.</p>
    </div>
    <div class="features-grid">{features_html}</div>
  </div>
</section>

<section class="section about" id="about">
  <div class="section-inner">
    <div class="about-grid">
      <div class="about-img fade-up">
        <img src="{img_about}" alt="About {name}" loading="lazy">
      </div>
      <div class="about-text">
        <span class="section-badge">Our Story</span>
        <h2>Why {name} is Different</h2>
        <p>We started with a simple belief: that great experiences should be accessible to everyone. Since our founding, we've been dedicated to delivering excellence in everything we do.</p>
        <p>Our team of passionate experts works tirelessly to ensure every customer gets the best possible experience. We don't just meet expectations — we exceed them.</p>
        <div class="stats">
          <div class="stat"><div class="stat-number">500+</div><div class="stat-label">Happy Clients</div></div>
          <div class="stat"><div class="stat-number">98%</div><div class="stat-label">Satisfaction Rate</div></div>
          <div class="stat"><div class="stat-number">5★</div><div class="stat-label">Average Rating</div></div>
        </div>
      </div>
    </div>
  </div>
</section>

<section class="section gallery" id="gallery">
  <div class="section-inner">
    <div class="text-center">
      <span class="section-badge">Showcase</span>
      <h2 class="section-title">See It in Action</h2>
      <p class="section-subtitle">A glimpse of what we've created and achieved.</p>
    </div>
    <div class="gallery-grid">
      <div class="gallery-item fade-up"><img src="{img_hero}" alt="Gallery 1" loading="lazy"><div class="gallery-overlay"><span class="gallery-overlay-text">View Project →</span></div></div>
      <div class="gallery-item fade-up"><img src="{img2}" alt="Gallery 2" loading="lazy"><div class="gallery-overlay"><span class="gallery-overlay-text">View Project →</span></div></div>
      <div class="gallery-item fade-up"><img src="{img3}" alt="Gallery 3" loading="lazy"><div class="gallery-overlay"><span class="gallery-overlay-text">View Project →</span></div></div>
    </div>
  </div>
</section>

<section class="section testimonials">
  <div class="section-inner">
    <div class="text-center">
      <span class="section-badge" style="background:rgba(255,255,255,0.1);color:rgba(255,255,255,0.8);border-color:rgba(255,255,255,0.2)">Testimonials</span>
      <h2 class="section-title">Loved by Thousands</h2>
      <p class="section-subtitle">Real stories from real customers who transformed their business with {name}.</p>
    </div>
    <div class="testimonials-grid">
      <div class="testimonial-card fade-up"><div class="stars">★★★★★</div><p class="testimonial-text">"Absolutely incredible. {name} completely transformed how we operate. The results speak for themselves — 3x growth in just 6 months!"</p><div class="testimonial-author"><div class="author-avatar">R</div><div><div class="author-name">Rahul Sharma</div><div class="author-role">CEO, TechVentures India</div></div></div></div>
      <div class="testimonial-card fade-up"><div class="stars">★★★★★</div><p class="testimonial-text">"The best investment we made this year. The team is exceptional and the product delivers exactly what it promises. Highly recommend!"</p><div class="testimonial-author"><div class="author-avatar">P</div><div><div class="author-name">Priya Patel</div><div class="author-role">Marketing Director</div></div></div></div>
      <div class="testimonial-card fade-up"><div class="stars">★★★★★</div><p class="testimonial-text">"Fast, reliable, and genuinely world-class. {name} sets the gold standard. I cannot imagine running my business without it now."</p><div class="testimonial-author"><div class="author-avatar">A</div><div><div class="author-name">Arjun Mehta</div><div class="author-role">Founder, GrowthLab</div></div></div></div>
    </div>
  </div>
</section>

<section class="section" id="pricing">
  <div class="section-inner">
    <div class="text-center">
      <span class="section-badge">Pricing</span>
      <h2 class="section-title">Simple, Transparent Pricing</h2>
      <p class="section-subtitle">No hidden fees. Choose the plan that works for you.</p>
    </div>
    <div class="pricing-grid">
      <div class="pricing-card fade-up"><div class="pricing-name">Starter</div><div class="pricing-price">₹999<sub>/mo</sub></div><ul class="pricing-features"><li>5 Projects</li><li>10GB Storage</li><li>Email Support</li><li>Basic Analytics</li><li>API Access</li></ul><a href="#contact" class="btn-plan outline">Get Started</a></div>
      <div class="pricing-card popular fade-up"><div class="popular-badge">⭐ Most Popular</div><div class="pricing-name">Professional</div><div class="pricing-price">₹2,499<sub>/mo</sub></div><ul class="pricing-features"><li>Unlimited Projects</li><li>100GB Storage</li><li>Priority Support</li><li>Advanced Analytics</li><li>Custom Domain</li><li>Team Collaboration</li></ul><a href="#contact" class="btn-plan">Get Started</a></div>
      <div class="pricing-card fade-up"><div class="pricing-name">Enterprise</div><div class="pricing-price">₹9,999<sub>/mo</sub></div><ul class="pricing-features"><li>Everything in Pro</li><li>Unlimited Storage</li><li>Dedicated Manager</li><li>Custom Integrations</li><li>SLA Guarantee</li><li>White Label</li></ul><a href="#contact" class="btn-plan outline">Contact Sales</a></div>
    </div>
  </div>
</section>

<section class="cta-section">
  <div class="section-inner">
    <h2>Ready to Get Started?</h2>
    <p>Join thousands of satisfied customers. Start your journey with {name} today.</p>
    <a href="#contact" class="btn-cta">{cta} — It\'s Free to Start</a>
  </div>
</section>

<section class="section" id="contact">
  <div class="section-inner">
    <div class="text-center" style="margin-bottom:60px">
      <span class="section-badge">Contact</span>
      <h2 class="section-title">Let\'s Talk</h2>
      <p class="section-subtitle">Have a question or ready to get started? We would love to hear from you.</p>
    </div>
    <div class="contact-grid">
      <div class="contact-info">
        <h3>Get in Touch</h3>
        <p style="color:var(--gray);margin-bottom:28px;line-height:1.7">We\'re here to help. Reach out through any channel and our team will respond within 24 hours.</p>
        <div class="contact-detail"><div class="contact-detail-icon">📧</div><div><strong>Email</strong><br>hello@{name.lower().replace(" ","")}.com</div></div>
        <div class="contact-detail"><div class="contact-detail-icon">📞</div><div><strong>Phone</strong><br>+91 98765 43210</div></div>
        <div class="contact-detail"><div class="contact-detail-icon">📍</div><div><strong>Location</strong><br>Mumbai, Maharashtra, India</div></div>
        <div class="contact-detail"><div class="contact-detail-icon">⏰</div><div><strong>Hours</strong><br>Mon–Sat, 9 AM – 8 PM IST</div></div>
      </div>
      <div class="contact-form-card">
        <div class="form-row">
          <div class="form-group"><label>Full Name *</label><input type="text" placeholder="Your full name"></div>
          <div class="form-group"><label>Email *</label><input type="email" placeholder="your@email.com"></div>
        </div>
        <div class="form-row">
          <div class="form-group"><label>Phone</label><input type="tel" placeholder="+91 98765 43210"></div>
          <div class="form-group"><label>Subject</label><select><option>General Inquiry</option><option>Pricing</option><option>Partnership</option><option>Support</option></select></div>
        </div>
        <div class="form-group"><label>Message *</label><textarea placeholder="Tell us about your project or question..."></textarea></div>
        <button class="btn-submit" onclick="this.textContent='✓ Message Sent!';this.style.background='#10b981';setTimeout(()=>{{this.textContent='Send Message';this.style.background=''}},3000)">Send Message</button>
      </div>
    </div>
  </div>
</section>

<footer>
  <div class="footer-inner">
    <div class="footer-grid">
      <div class="footer-brand"><span class="logo">{name}</span><p>Delivering excellence and innovation to help businesses grow and succeed in the digital age.</p></div>
      <div class="footer-col"><h4>Company</h4><ul><li><a href="#about">About Us</a></li><li><a href="#features">Services</a></li><li><a href="#pricing">Pricing</a></li><li><a href="#contact">Contact</a></li></ul></div>
      <div class="footer-col"><h4>Services</h4><ul><li><a href="#">Consulting</a></li><li><a href="#">Development</a></li><li><a href="#">Design</a></li><li><a href="#">Analytics</a></li></ul></div>
      <div class="footer-col"><h4>Follow Us</h4><ul><li><a href="#">Twitter / X</a></li><li><a href="#">LinkedIn</a></li><li><a href="#">Instagram</a></li><li><a href="#">YouTube</a></li></ul></div>
    </div>
    <div class="footer-bottom"><span>© 2026 {name}. All rights reserved.</span><div class="footer-links"><a href="#">Privacy</a><a href="#">Terms</a><a href="#">Sitemap</a></div><span>Built with ❤️ using Dacexy AI</span></div>
  </div>
</footer>

<script>
const navbar=document.getElementById("navbar");
window.addEventListener("scroll",()=>{{navbar.classList.toggle("scrolled",window.scrollY>50)}});
document.querySelectorAll("a[href^='#']").forEach(a=>{{a.addEventListener("click",e=>{{e.preventDefault();const t=document.querySelector(a.getAttribute("href"));if(t)t.scrollIntoView({{behavior:"smooth",block:"start"}})}})}});
const observer=new IntersectionObserver(entries=>{{entries.forEach(e=>{{if(e.isIntersecting){{e.target.classList.add("visible");observer.unobserve(e.target)}}}})}},{{threshold:0.15}});
document.querySelectorAll(".fade-up").forEach(el=>observer.observe(el));
</script>
</body>
</html>"""

async def generate_website(prompt: str, ai: DeepSeekProvider) -> str:
    try:
        return build_template(prompt)
    except Exception as e:
        log.error("Website generation failed: %s", e)
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
        {"role": "user", "content": "Task: " + body.task + ("\nContext: " + body.context if body.context else "")}
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
        raise HTTPException(500, "Agent error: " + str(e))

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
        raise HTTPException(500, "Failed to send command: " + str(e))

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

@router.get("/download/windows")
async def download_windows_agent():
    lines = [
        "@echo off",
        "setlocal enabledelayedexpansion",
        "title Dacexy Desktop Agent Installer",
        "color 0A",
        "echo.",
        "echo  ================================",
        "echo   DACEXY Desktop Agent v3.0",
        "echo  ================================",
        "echo.",
        "echo [1/5] Checking Python...",
        "python --version >nul 2>&1",
        "if errorlevel 1 (",
        "    echo Python not found. Auto-installing Python 3.11...",
        "    echo Please wait 2-3 minutes...",
        "    powershell -Command \"Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe' -OutFile '%TEMP%\\python_installer.exe' -UseBasicParsing\"",
        "    \"%TEMP%\\python_installer.exe\" /quiet InstallAllUsers=1 PrependPath=1 Include_test=0",
        "    timeout /t 15 /nobreak >nul",
        "    del \"%TEMP%\\python_installer.exe\"",
        "    set \"PATH=%PATH%;C:\\Program Files\\Python311;C:\\Program Files\\Python311\\Scripts\"",
        "    set \"PATH=%PATH%;C:\\Users\\%USERNAME%\\AppData\\Local\\Programs\\Python\\Python311\"",
        "    set \"PATH=%PATH%;C:\\Users\\%USERNAME%\\AppData\\Local\\Programs\\Python\\Python311\\Scripts\"",
        ")",
        "echo OK: Python ready",
        "echo.",
        "echo [2/5] Creating agent folder...",
        "if not exist \"%USERPROFILE%\\DacexyAgent\" mkdir \"%USERPROFILE%\\DacexyAgent\"",
        "echo.",
        "echo [3/5] Installing packages (please wait 2-3 minutes)...",
        "python -m pip install --upgrade pip --quiet --no-warn-script-location",
        "python -m pip install pyautogui pillow websockets requests speechrecognition pyttsx3 numpy psutil --quiet --no-warn-script-location",
        "if errorlevel 1 (",
        "    echo Retrying package install...",
        "    python -m pip install pyautogui pillow websockets requests speechrecognition pyttsx3 numpy psutil",
        ")",
        "echo OK: Packages installed",
        "echo.",
        "echo [4/5] Downloading Dacexy Agent script...",
        "powershell -Command \"Invoke-WebRequest -Uri 'https://raw.githubusercontent.com/dacexyai/Dacexy-backend/main/desktop_agent/dacexy_agent.py' -OutFile '%USERPROFILE%\\DacexyAgent\\dacexy_agent.py' -UseBasicParsing\"",
        "if errorlevel 1 (",
        "    echo ERROR: Download failed. Check internet connection.",
        "    pause",
        "    exit /b 1",
        ")",
        "echo OK: Agent downloaded",
        "echo.",
        "echo [5/5] Creating desktop shortcut...",
        "set SCRIPT=\"%TEMP%\\dacexy_sc.vbs\"",
        "echo Set oWS = WScript.CreateObject(\"WScript.Shell\") > %SCRIPT%",
        "echo Set oLink = oWS.CreateShortcut(\"%USERPROFILE%\\Desktop\\Dacexy Agent.lnk\") >> %SCRIPT%",
        "echo oLink.TargetPath = \"cmd.exe\" >> %SCRIPT%",
        "echo oLink.Arguments = \"/k python %USERPROFILE%\\DacexyAgent\\dacexy_agent.py\" >> %SCRIPT%",
        "echo oLink.WorkingDirectory = \"%USERPROFILE%\\DacexyAgent\" >> %SCRIPT%",
        "echo oLink.Save >> %SCRIPT%",
        "cscript /nologo %SCRIPT%",
        "del %SCRIPT%",
        "echo.",
        "echo  ================================",
        "echo   Done! Launching agent now...",
        "echo  ================================",
        "echo.",
        "cd \"%USERPROFILE%\\DacexyAgent\"",
        "python dacexy_agent.py",
        "pause",
    ]
    bat = "\r\n".join(lines) + "\r\n"
    return Response(
        content=bat.encode("utf-8"),
        media_type="application/octet-stream",
        headers={"Content-Disposition": "attachment; filename=install_dacexy_agent.bat"}
    )
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

# ── START SERVER ──────────────────────────────────────────────────────────────
import os
import subprocess
import sys

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    subprocess.run(
        [
            sys.executable, "-m", "uvicorn",
            "src.main:app",
            "--host", "0.0.0.0",
            "--port", str(port),
            "--workers", "1",
        ],
        check=True,
    )
       
