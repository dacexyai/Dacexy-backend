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
    skip = {"for","the","with","that","this","and","build","make","create","generate","website","page","site","app","landing","platform","startup","business","restaurant","store","shop","company","portfolio","a","an","my","our","me","i","want","need"}
    words = [w for w in re.sub(r\'[^a-zA-Z0-9 ]\', \'\', p).split() if len(w) > 2 and w.lower() not in skip]
    return words[0].title() if words else "Nexus"

def get_category(prompt: str) -> str:
    p = prompt.lower()
    scores = {
        "restaurant": sum(p.count(x) for x in ["restaurant","food","cafe","kitchen","dining","menu","eat","chef","pizza","hotel","bakery","cuisine","biryani","dhaba","tiffin"]),
        "saas": sum(p.count(x) for x in ["saas","software","app","platform","tech","startup","ai tool","dashboard","crm","b2b","productivity","workflow","automation tool"]),
        "portfolio": sum(p.count(x) for x in ["portfolio","designer","freelance","artist","creative","photography","my work","personal","illustrator","architect"]),
        "ecommerce": sum(p.count(x) for x in ["shop","store","ecommerce","product","sell","buy","fashion","clothing","brand","retail","marketplace","cart"]),
        "agency": sum(p.count(x) for x in ["agency","marketing","consultant","service","firm","corporate","enterprise","digital agency","creative agency"]),
        "fitness": sum(p.count(x) for x in ["fitness","gym","health","wellness","yoga","trainer","sport","workout","weight loss","muscle"]),
        "education": sum(p.count(x) for x in ["education","school","course","learning","teach","tutor","academy","college","online learning","edtech"]),
        "realestate": sum(p.count(x) for x in ["real estate","property","house","apartment","rent","buy home","realtor","housing","flat","villa"]),
    }
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "business"

def build_template(prompt: str) -> str:
    name = extract_name(prompt)
    cat = get_category(prompt)
    seed = abs(hash(prompt)) % 99999
    enc = urllib.parse.quote(prompt[:80])

    configs = {
        "restaurant": {
            "colors": {"bg":"#0D0500","primary":"#C8102E","accent":"#FFD700","text":"#FFF8F0","muted":"rgba(255,248,240,0.6)","card":"rgba(255,255,255,0.04)","border":"rgba(255,215,0,0.15)"},
            "font_heading": "Playfair Display",
            "tagline": "Where Every Bite Tells a Story",
            "sub": f"Experience authentic flavours crafted with passion at {name}. Fresh ingredients, timeless recipes, unforgettable moments.",
            "cta1": "Reserve a Table", "cta2": "View Menu",
            "services": [("🍽️","Fine Dining","Exquisite multi-course meals by award-winning chefs."),("🍷","Premium Bar","Curated wines and craft cocktails."),("🎂","Private Events","Exclusive dining rooms for celebrations."),("🚗","Home Delivery","Restaurant quality at your doorstep.")],
            "stats": [("15+","Years"),("50K+","Guests"),("4.9★","Rating"),("200+","Dishes")],
            "testimonials": [("Arjun M.","Food Critic","Best dining in the city. Every dish is perfection."),("Priya S.","Guest","We celebrate here every year. Simply magical."),("Rahul K.","Corporate","World-class private dining experience.")],
        },
        "saas": {
            "colors": {"bg":"#060614","primary":"#6366F1","accent":"#06B6D4","text":"#F0F0FF","muted":"rgba(240,240,255,0.55)","card":"rgba(99,102,241,0.08)","border":"rgba(99,102,241,0.2)"},
            "font_heading": "Inter",
            "tagline": "Ship Faster. Scale Smarter.",
            "sub": f"{name} gives your team AI superpowers — automate workflows, ship products faster, and grow without limits.",
            "cta1": "Start Free Trial", "cta2": "Watch Demo",
            "services": [("⚡","10x Velocity","Automated workflows eliminate manual bottlenecks instantly."),("🤖","AI-Native","Smart automation that learns and improves continuously."),("🔒","SOC2 Secure","Enterprise-grade security with full audit trails."),("📊","Live Analytics","Real-time dashboards with actionable insights.")],
            "stats": [("10K+","Teams"),("99.9%","Uptime"),("10x","ROI"),("4.8★","G2")],
            "testimonials": [("Sarah C.","CTO TechFlow","Cut costs 60% in month one. Transformative."),("Marcus J.","CEO ScaleUp","Team ships 3x faster. ROI was immediate."),("Aisha P.","VP Eng","Best developer experience we have ever had.")],
        },
        "portfolio": {
            "colors": {"bg":"#0A0A0A","primary":"#F59E0B","accent":"#EF4444","text":"#FAFAFA","muted":"rgba(250,250,250,0.55)","card":"rgba(245,158,11,0.06)","border":"rgba(245,158,11,0.15)"},
            "font_heading": "Playfair Display",
            "tagline": "Design That Moves People",
            "sub": "I craft digital experiences that convert. Every pixel, every interaction, every line of code — built with purpose.",
            "cta1": "See My Work", "cta2": "Hire Me",
            "services": [("🎨","UI/UX Design","Human-centred interfaces users love."),("💻","Development","React, Next.js — fast, accessible, scalable."),("📱","Mobile Apps","iOS and Android that delight every user."),("🚀","Brand Identity","Logos, systems, and guidelines that last.")],
            "stats": [("50+","Projects"),("30+","Clients"),("5★","Rating"),("8+","Years")],
            "testimonials": [("David P.","Founder","Delivered beyond expectations. Outstanding."),("Emma W.","Director","Conversion up 240% after redesign. World-class."),("Carlos R.","CEO","Best investment this year. Market-changing.")],
        },
        "ecommerce": {
            "colors": {"bg":"#022C22","primary":"#10B981","accent":"#F97316","text":"#ECFDF5","muted":"rgba(236,253,245,0.6)","card":"rgba(16,185,129,0.08)","border":"rgba(16,185,129,0.2)"},
            "font_heading": "Inter",
            "tagline": "Premium Quality, Fast Delivery",
            "sub": f"Shop {name}'s curated collection. Free shipping on all orders. 30-day hassle-free returns.",
            "cta1": "Shop Now", "cta2": "View Collection",
            "services": [("🚚","Free Shipping","Express delivery on all orders nationwide."),("✅","Quality Check","47-point inspection on every product."),("↩️","Easy Returns","30-day no-questions-asked returns."),("💳","Secure Pay","UPI, cards, COD — all accepted.")],
            "stats": [("50K+","Customers"),("10K+","Products"),("4.9★","Rating"),("99%","Satisfaction")],
            "testimonials": [("Sneha G.","Buyer","Amazing quality, delivered in 2 days!"),("Vikram N.","Member","Shopping here 3 years. Always excellent."),("Divya K.","Blogger","My go-to for premium finds. Impeccable.")],
        },
        "agency": {
            "colors": {"bg":"#0A0000","primary":"#DC2626","accent":"#FBBF24","text":"#FFF5F5","muted":"rgba(255,245,245,0.55)","card":"rgba(220,38,38,0.08)","border":"rgba(220,38,38,0.2)"},
            "font_heading": "Playfair Display",
            "tagline": "We Build Brands That Dominate",
            "sub": f"{name} transforms businesses through razor-sharp strategy, bold creative, and technology that delivers results.",
            "cta1": "Get a Proposal", "cta2": "See Our Work",
            "services": [("📈","Growth Strategy","Data-driven plans for explosive growth."),("🎯","Performance Ads","ROI-focused campaigns that beat benchmarks."),("🌐","Digital Products","Websites and apps that convert."),("✍️","Creative Content","Stories that connect and drive action.")],
            "stats": [("100+","Brands"),("₹50Cr+","Revenue"),("4.9★","Rating"),("8+","Years")],
            "testimonials": [("Ankit J.","CMO","Tripled leads in 90 days. Best agency ever."),("Meera K.","Founder","Rebrand drove 180% revenue growth."),("Rajesh P.","CEO","True growth partner. Exceptional results.")],
        },
        "fitness": {
            "colors": {"bg":"#0C0500","primary":"#EA580C","accent":"#22C55E","text":"#FFF7ED","muted":"rgba(255,247,237,0.55)","card":"rgba(234,88,12,0.08)","border":"rgba(234,88,12,0.2)"},
            "font_heading": "Inter",
            "tagline": "Transform Your Body. Own Your Life.",
            "sub": f"Join {name} and unlock your peak potential. Expert coaches, elite facilities, unstoppable community.",
            "cta1": "Start Free Trial", "cta2": "View Programs",
            "services": [("💪","Strength","Elite programming to build real power."),("🏃","HIIT Cardio","High-intensity sessions that torch fat fast."),("🧘","Recovery","Yoga and mobility for peak performance."),("🥗","Nutrition","Personalised plans that fuel transformation.")],
            "stats": [("5K+","Members"),("50+","Coaches"),("98%","Success"),("4.9★","Rating")],
            "testimonials": [("Kiran R.","Member","Lost 20kg in 6 months. Life-changing."),("Ananya S.","Runner","PR improved 22 minutes. World-class coaching."),("Dev M.","Athlete","12kg muscle in a year. Scientific programming.")],
        },
        "education": {
            "colors": {"bg":"#0F0A2E","primary":"#7C3AED","accent":"#F59E0B","text":"#F5F0FF","muted":"rgba(245,240,255,0.55)","card":"rgba(124,58,237,0.08)","border":"rgba(124,58,237,0.2)"},
            "font_heading": "Playfair Display",
            "tagline": "Learn Without Limits",
            "sub": f"{name} delivers world-class education that transforms careers. Expert instructors, live classes, lifetime access.",
            "cta1": "Enroll Now", "cta2": "Browse Courses",
            "services": [("📚","Expert Courses","Industry leaders teach real-world skills."),("🎯","Live Sessions","Interactive classes with Q&A and mentorship."),("🏆","Certifications","Recognised credentials that employers value."),("♾️","Lifetime Access","Learn at your pace, revisit anytime forever.")],
            "stats": [("20K+","Students"),("500+","Courses"),("4.9★","Rating"),("95%","Job Rate")],
            "testimonials": [("Rohan M.","Student","Got my dream job 3 months after completing."),("Priya T.","Graduate","Best investment in my career. Life-changing."),("Amit S.","Professional","Promoted twice. Skills directly applicable.")],
        },
        "realestate": {
            "colors": {"bg":"#020617","primary":"#2563EB","accent":"#F59E0B","text":"#EFF6FF","muted":"rgba(239,246,255,0.55)","card":"rgba(37,99,235,0.08)","border":"rgba(37,99,235,0.2)"},
            "font_heading": "Playfair Display",
            "tagline": "Find Your Perfect Home",
            "sub": f"{name} makes finding your dream property effortless. Premium listings, trusted agents, transparent process.",
            "cta1": "Browse Properties", "cta2": "Talk to an Agent",
            "services": [("🏠","Buy","Premium residential properties in top locations."),("🔑","Rent","Verified rentals with transparent pricing."),("💼","Invest","High-yield commercial and residential opportunities."),("📋","Manage","Complete property management services.")],
            "stats": [("5K+","Properties"),("2K+","Happy Clients"),("₹500Cr+","Sold"),("4.9★","Rating")],
            "testimonials": [("Suresh P.","Buyer","Found perfect home in 2 weeks. Seamless."),("Kavita M.","Investor","Best ROI properties. Expert guidance."),("Arun K.","Seller","Sold above asking price. Outstanding service.")],
        },
        "business": {
            "colors": {"bg":"#020617","primary":"#2563EB","accent":"#F59E0B","text":"#EFF6FF","muted":"rgba(239,246,255,0.55)","card":"rgba(37,99,235,0.08)","border":"rgba(37,99,235,0.2)"},
            "font_heading": "Inter",
            "tagline": "Excellence Delivered Every Time",
            "sub": f"{name} combines deep expertise and bold execution to deliver results that transform businesses.",
            "cta1": "Get Started", "cta2": "Learn More",
            "services": [("⚡","Fast Results","Exceptional outcomes delivered ahead of schedule."),("🎯","Results First","Every action tied to your measurable goals."),("🤝","True Partners","We are invested in your success as deeply as you are."),("🛡️","Reliable","100+ clients trust us with their most critical work.")],
            "stats": [("100+","Projects"),("50+","Clients"),("4.9★","Rating"),("5+","Years")],
            "testimonials": [("Rohit K.","MD","Delivered exactly as promised. Exceptional."),("Nisha A.","COO","Best vendor relationship we have. Reliable."),("Amit S.","Founder","Game-changer for our business growth.")],
        },
    }

    c = configs.get(cat, configs["business"])
    colors = c["colors"]
    font = c["font_heading"]

    imgs = {
        "hero": f"https://image.pollinations.ai/prompt/ultra_realistic_cinematic_{enc}_dramatic_professional_4k_hero?width=1400&height=800&seed={seed}&nologo=true&model=flux",
        "about": f"https://image.pollinations.ai/prompt/professional_premium_{enc}_team_modern?width=900&height=700&seed={seed+1}&nologo=true&model=flux",
        "g1": f"https://image.pollinations.ai/prompt/{enc}_premium_showcase_1?width=700&height=500&seed={seed+2}&nologo=true&model=flux",
        "g2": f"https://image.pollinations.ai/prompt/{enc}_premium_showcase_2?width=700&height=500&seed={seed+3}&nologo=true&model=flux",
        "g3": f"https://image.pollinations.ai/prompt/{enc}_premium_showcase_3?width=700&height=500&seed={seed+4}&nologo=true&model=flux",
        "g4": f"https://image.pollinations.ai/prompt/{enc}_premium_showcase_4?width=700&height=500&seed={seed+5}&nologo=true&model=flux",
    }

    svcs_html = "".join([f\'\'\'<div class="sc"><div class="si">{ic}</div><h3>{t}</h3><p>{d}</p></div>\'\'\' for ic,t,d in c["services"]])
    stats_html = "".join([f\'<div class="stat"><div class="sn">{n}</div><div class="sl">{l}</div></div>\' for n,l in c["stats"]])
    testi_html = "".join([f\'\'\'<div class="tc"><div class="ts">★★★★★</div><p class="tt">"{t}"</p><div class="ta"><div class="av">{a[0]}</div><div><div class="an">{a}</div><div class="ar">{r}</div></div></div></div>\'\'\' for a,r,t in c["testimonials"]])
    gal_html = "".join([f\'<div class="gi"><img src="{imgs[k]}" loading="lazy" alt=""/></div>\' for k in ["g1","g2","g3","g4"]])

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{name} — {c["tagline"]}</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=Playfair+Display:ital,wght@0,700;0,800;0,900;1,700&display=swap" rel="stylesheet">
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
:root{{--bg:{colors["bg"]};--pr:{colors["primary"]};--ac:{colors["accent"]};--tx:{colors["text"]};--mu:{colors["muted"]};--ca:{colors["card"]};--br:{colors["border"]}}}
html{{scroll-behavior:smooth}}
body{{font-family:"Inter",sans-serif;background:var(--bg);color:var(--tx);overflow-x:hidden;line-height:1.6}}

/* NAV */
nav{{position:fixed;top:0;width:100%;z-index:1000;transition:all 0.4s;padding:0 5%}}
nav.sc{{background:rgba(0,0,0,0.85);backdrop-filter:blur(24px);border-bottom:1px solid var(--br);box-shadow:0 4px 30px rgba(0,0,0,0.3)}}
.ni{{max-width:1280px;margin:0 auto;display:flex;align-items:center;justify-content:space-between;height:72px}}
.nl{{font-family:"{font}",serif;font-size:1.8rem;font-weight:900;color:var(--tx);text-decoration:none;letter-spacing:-0.5px}}
.nm{{display:flex;align-items:center;gap:36px;list-style:none}}
.nm a{{color:var(--mu);text-decoration:none;font-weight:500;font-size:0.9rem;transition:color 0.2s}}
.nm a:hover{{color:var(--tx)}}
.nc{{background:var(--pr)!important;color:#fff!important;padding:11px 26px;border-radius:100px;font-weight:700!important;transition:all 0.3s!important;box-shadow:0 4px 20px rgba(0,0,0,0.3)}}
.nc:hover{{transform:translateY(-2px)!important;box-shadow:0 8px 30px rgba(0,0,0,0.4)!important}}
.nhb{{display:none;background:none;border:none;cursor:pointer;flex-direction:column;gap:5px;padding:4px}}
.nhb span{{width:24px;height:2px;background:var(--tx);border-radius:2px;display:block;transition:all 0.3s}}
.nmob{{display:none;position:fixed;top:72px;left:0;right:0;padding:20px 5%;flex-direction:column;gap:16px;background:rgba(0,0,0,0.95);backdrop-filter:blur(20px);border-bottom:1px solid var(--br)}}
.nmob.open{{display:flex}}
.nmob a{{color:var(--mu);text-decoration:none;font-weight:600;font-size:0.95rem;padding:8px 0;border-bottom:1px solid var(--br)}}
.nmob .mc{{background:var(--pr);color:#fff!important;text-align:center;padding:14px;border-radius:12px;border:none!important;margin-top:4px}}

/* HERO */
.hero{{min-height:100vh;display:flex;align-items:center;padding:100px 5% 80px;position:relative;overflow:hidden;background:var(--bg)}}
.hbg{{position:absolute;inset:0;background:url("{imgs["hero"]}") center/cover no-repeat;opacity:0.15;filter:blur(2px);transform:scale(1.05)}}
.hov{{position:absolute;inset:0;background:linear-gradient(135deg,{colors["bg"]}F8 0%,{colors["bg"]}CC 50%,{colors["primary"]}22 100%)}}
.hsh{{position:absolute;inset:0;overflow:hidden;pointer-events:none}}
.hsh::before{{content:"";position:absolute;top:-30%;right:-10%;width:600px;height:600px;border-radius:50%;background:radial-gradient(circle,{colors["primary"]}18 0%,transparent 70%)}}
.hsh::after{{content:"";position:absolute;bottom:-20%;left:-5%;width:400px;height:400px;border-radius:50%;background:radial-gradient(circle,{colors["accent"]}12 0%,transparent 70%)}}
.hi{{position:relative;z-index:2;max-width:1280px;margin:0 auto;width:100%;display:grid;grid-template-columns:1fr 1fr;gap:80px;align-items:center}}
.hbadge{{display:inline-flex;align-items:center;gap:8px;background:var(--ca);backdrop-filter:blur(10px);border:1px solid var(--br);color:var(--tx);padding:9px 20px;border-radius:100px;font-size:0.75rem;font-weight:700;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:24px}}
.bdot{{width:8px;height:8px;border-radius:50%;background:var(--ac);animation:pulse 2s infinite;box-shadow:0 0 10px var(--ac)}}
@keyframes pulse{{0%,100%{{opacity:1;transform:scale(1)}}50%{{opacity:0.6;transform:scale(1.4)}}}}
.ht{{font-family:"{font}",serif;font-size:clamp(2.8rem,4.5vw,4.5rem);font-weight:900;line-height:1.05;letter-spacing:-2px;margin-bottom:16px;color:var(--tx)}}
.hta{{color:var(--ac);display:block;font-style:italic}}
.hs{{font-size:1.05rem;color:var(--mu);line-height:1.75;margin-bottom:36px;max-width:480px}}
.hbtns{{display:flex;gap:14px;flex-wrap:wrap}}
.bp{{display:inline-flex;align-items:center;gap:8px;background:var(--pr);color:#fff;font-weight:800;font-size:0.9rem;padding:16px 32px;border-radius:100px;text-decoration:none;transition:all 0.3s;box-shadow:0 8px 30px rgba(0,0,0,0.3)}}
.bp:hover{{transform:translateY(-3px);filter:brightness(1.1);box-shadow:0 16px 40px rgba(0,0,0,0.4)}}
.bs{{display:inline-flex;align-items:center;gap:8px;background:var(--ca);backdrop-filter:blur(10px);color:var(--tx);font-weight:700;font-size:0.9rem;padding:16px 32px;border-radius:100px;text-decoration:none;border:1px solid var(--br);transition:all 0.3s}}
.bs:hover{{background:rgba(255,255,255,0.08);transform:translateY(-3px)}}
.hiw{{position:relative;perspective:1000px}}
.hic{{border-radius:24px;overflow:hidden;box-shadow:0 40px 80px rgba(0,0,0,0.6),0 0 0 1px var(--br);transform:rotateY(-5deg) rotateX(3deg);transition:transform 0.5s ease;position:relative}}
.hic:hover{{transform:rotateY(0deg) rotateX(0deg)}}
.hic img{{width:100%;height:420px;object-fit:cover;display:block}}
.hib{{position:absolute;bottom:20px;left:20px;background:rgba(0,0,0,0.75);backdrop-filter:blur(20px);border:1px solid var(--br);padding:12px 18px;border-radius:14px;display:flex;align-items:center;gap:10px}}
.ld{{width:8px;height:8px;border-radius:50%;background:#22C55E;box-shadow:0 0 12px #22C55E;animation:pulse 2s infinite}}
.lt{{color:var(--tx);font-size:0.78rem;font-weight:600}}

/* STATS */
.stbar{{background:rgba(0,0,0,0.4);border-top:1px solid var(--br);border-bottom:1px solid var(--br);padding:0 5%}}
.sti{{max-width:1280px;margin:0 auto;display:grid;grid-template-columns:repeat(4,1fr)}}
.stat{{padding:32px 24px;text-align:center;border-right:1px solid var(--br);transition:background 0.3s}}
.stat:last-child{{border-right:none}}
.stat:hover{{background:var(--ca)}}
.sn{{font-family:"{font}",serif;font-size:2.4rem;font-weight:900;color:var(--ac);margin-bottom:4px}}
.sl{{font-size:0.72rem;color:var(--mu);font-weight:600;text-transform:uppercase;letter-spacing:1.2px}}

/* ABOUT */
.about{{padding:120px 5%;background:var(--bg)}}
.abi{{max-width:1280px;margin:0 auto;display:grid;grid-template-columns:1fr 1fr;gap:80px;align-items:center}}
.abimg{{border-radius:24px;overflow:hidden;position:relative;box-shadow:0 40px 80px rgba(0,0,0,0.4)}}
.abimg img{{width:100%;height:480px;object-fit:cover;display:block;transition:transform 0.6s}}
.abimg:hover img{{transform:scale(1.04)}}
.abtag{{position:absolute;top:20px;left:20px;background:var(--pr);color:#fff;font-size:0.72rem;font-weight:800;padding:8px 16px;border-radius:100px;text-transform:uppercase;letter-spacing:1px}}
.sl2{{display:inline-flex;align-items:center;gap:8px;background:var(--ca);color:var(--ac);font-size:0.72rem;font-weight:800;text-transform:uppercase;letter-spacing:2px;padding:8px 18px;border-radius:100px;margin-bottom:20px;border:1px solid var(--br)}}
.sh{{font-family:"{font}",serif;font-size:clamp(2rem,3vw,2.8rem);font-weight:900;color:var(--tx);line-height:1.15;letter-spacing:-1px;margin-bottom:20px}}
.sh span{{color:var(--pr)}}
.ss{{font-size:0.95rem;color:var(--mu);line-height:1.8;margin-bottom:36px}}
.aff{{display:flex;flex-direction:column;gap:14px}}
.af{{display:flex;align-items:flex-start;gap:14px;padding:16px;background:var(--ca);border-radius:16px;border:1px solid var(--br);transition:all 0.3s}}
.af:hover{{border-color:var(--pr);transform:translateX(4px)}}
.afi{{width:42px;height:42px;border-radius:12px;background:var(--ca);border:1px solid var(--br);display:flex;align-items:center;justify-content:center;font-size:1.3rem;flex-shrink:0}}
.aft h4{{font-weight:700;font-size:0.88rem;color:var(--tx);margin-bottom:3px}}
.aft p{{font-size:0.8rem;color:var(--mu)}}

/* SERVICES */
.services{{padding:120px 5%}}
.svi{{max-width:1280px;margin:0 auto}}
.sh2{{text-align:center;margin-bottom:60px}}
.sg{{display:grid;grid-template-columns:repeat(2,1fr);gap:20px}}
.sc{{background:var(--ca);border:1px solid var(--br);border-radius:24px;padding:36px;transition:all 0.4s;position:relative;overflow:hidden}}
.sc::before{{content:"";position:absolute;inset:0;background:linear-gradient(135deg,var(--pr) 0%,transparent 60%);opacity:0;transition:opacity 0.4s}}
.sc:hover{{border-color:var(--pr);transform:translateY(-6px);box-shadow:0 20px 60px rgba(0,0,0,0.3)}}
.sc:hover::before{{opacity:0.05}}
.si{{font-size:2.4rem;margin-bottom:20px;display:block}}
.sc h3{{font-family:"{font}",serif;font-size:1.25rem;font-weight:800;color:var(--tx);margin-bottom:12px}}
.sc p{{font-size:0.88rem;color:var(--mu);line-height:1.7}}

/* GALLERY */
.gallery{{padding:80px 5%;background:rgba(0,0,0,0.3)}}
.gli{{max-width:1280px;margin:0 auto}}
.gg{{display:grid;grid-template-columns:repeat(2,1fr);gap:16px;margin-top:48px}}
.gi{{border-radius:20px;overflow:hidden;aspect-ratio:4/3;cursor:pointer;position:relative}}
.gi img{{width:100%;height:100%;object-fit:cover;display:block;transition:transform 0.6s}}
.gi:hover img{{transform:scale(1.08)}}
.gi::after{{content:"";position:absolute;inset:0;background:linear-gradient(to top,rgba(0,0,0,0.5),transparent);opacity:0;transition:opacity 0.3s}}
.gi:hover::after{{opacity:1}}

/* TESTIMONIALS */
.testi{{padding:120px 5%}}
.tti{{max-width:1280px;margin:0 auto}}
.tg{{display:grid;grid-template-columns:repeat(3,1fr);gap:20px;margin-top:48px}}
.tc{{background:var(--ca);border:1px solid var(--br);border-radius:24px;padding:32px;transition:all 0.3s;position:relative;overflow:hidden}}
.tc::before{{content:"\\201C";position:absolute;top:-20px;right:16px;font-size:8rem;color:var(--pr);opacity:0.08;font-family:serif;line-height:1}}
.tc:hover{{border-color:var(--pr);transform:translateY(-4px);box-shadow:0 20px 50px rgba(0,0,0,0.3)}}
.ts{{color:var(--ac);font-size:1rem;letter-spacing:2px;margin-bottom:16px}}
.tt{{font-size:0.9rem;color:var(--mu);line-height:1.75;margin-bottom:24px;font-style:italic}}
.ta{{display:flex;align-items:center;gap:12px}}
.av{{width:44px;height:44px;border-radius:50%;background:linear-gradient(135deg,var(--pr),var(--ac));display:flex;align-items:center;justify-content:center;color:#fff;font-weight:800;font-size:0.9rem;flex-shrink:0}}
.an{{font-weight:700;font-size:0.85rem;color:var(--tx)}}
.ar{{font-size:0.72rem;color:var(--mu)}}

/* CTA */
.cta{{padding:120px 5%}}
.ctai{{max-width:1000px;margin:0 auto;border-radius:32px;padding:80px 60px;text-align:center;position:relative;overflow:hidden;border:1px solid var(--br);background:linear-gradient(135deg,var(--ca) 0%,rgba(0,0,0,0.3) 100%);box-shadow:0 40px 80px rgba(0,0,0,0.3)}}
.ctai::before{{content:"";position:absolute;top:-50%;right:-10%;width:500px;height:500px;border-radius:50%;background:radial-gradient(circle,var(--pr) 0%,transparent 60%);opacity:0.08;pointer-events:none}}
.ctai::after{{content:"";position:absolute;bottom:-30%;left:-5%;width:350px;height:350px;border-radius:50%;background:radial-gradient(circle,var(--ac) 0%,transparent 60%);opacity:0.06;pointer-events:none}}
.ctai h2{{font-family:"{font}",serif;font-size:clamp(2rem,4vw,3rem);font-weight:900;color:var(--tx);margin-bottom:16px;position:relative;z-index:1;letter-spacing:-1px}}
.ctai p{{font-size:1rem;color:var(--mu);margin-bottom:40px;position:relative;z-index:1;max-width:500px;margin-left:auto;margin-right:auto}}
.cbtns{{display:flex;gap:14px;justify-content:center;flex-wrap:wrap;position:relative;z-index:1}}
.cb1{{display:inline-flex;align-items:center;gap:8px;background:var(--pr);color:#fff;font-weight:800;padding:16px 36px;border-radius:100px;text-decoration:none;font-size:0.9rem;transition:all 0.3s;box-shadow:0 8px 30px rgba(0,0,0,0.3)}}
.cb1:hover{{transform:translateY(-3px);filter:brightness(1.1)}}
.cb2{{display:inline-flex;align-items:center;gap:8px;background:transparent;color:var(--tx);font-weight:700;padding:16px 36px;border-radius:100px;text-decoration:none;font-size:0.9rem;border:1px solid var(--br);transition:all 0.3s}}
.cb2:hover{{background:var(--ca);transform:translateY(-3px)}}

/* FOOTER */
footer{{padding:60px 5% 30px;border-top:1px solid var(--br);background:rgba(0,0,0,0.4)}}
.fi{{max-width:1280px;margin:0 auto}}
.ft{{display:grid;grid-template-columns:2fr 1fr 1fr 1fr;gap:48px;margin-bottom:48px}}
.fb p{{font-size:0.82rem;color:var(--mu);margin-top:12px;line-height:1.7;max-width:240px}}
.flogo{{font-family:"{font}",serif;font-size:1.6rem;font-weight:900;color:var(--tx)}}
.fc h4{{font-weight:700;font-size:0.75rem;color:var(--mu);text-transform:uppercase;letter-spacing:1.5px;margin-bottom:16px}}
.fc a{{display:block;color:var(--mu);text-decoration:none;font-size:0.82rem;margin-bottom:10px;transition:color 0.2s}}
.fc a:hover{{color:var(--tx)}}
.fbot{{border-top:1px solid var(--br);padding-top:24px;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px}}
.fbot p{{font-size:0.75rem;color:rgba(255,255,255,0.2)}}

/* RESPONSIVE */
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

<nav id="nav">
  <div class="ni">
    <a href="#" class="nl">{name}</a>
    <ul class="nm">
      <li><a href="#about">About</a></li>
      <li><a href="#services">Services</a></li>
      <li><a href="#gallery">Gallery</a></li>
      <li><a href="#contact" class="nc">{c["cta1"]}</a></li>
    </ul>
    <button class="nhb" id="hb"><span></span><span></span><span></span></button>
  </div>
</nav>
<div class="nmob" id="nm">
  <a href="#about">About</a>
  <a href="#services">Services</a>
  <a href="#gallery">Gallery</a>
  <a href="#contact" class="mc">{c["cta1"]}</a>
</div>

<section class="hero" id="home">
  <div class="hbg"></div>
  <div class="hov"></div>
  <div class="hsh"></div>
  <div class="hi">
    <div>
      <div class="hbadge"><span class="bdot"></span>✦ {name} · {cat.title()}</div>
      <h1 class="ht">{name}<span class="hta">{c["tagline"]}</span></h1>
      <p class="hs">{c["sub"]}</p>
      <div class="hbtns">
        <a href="#contact" class="bp">{c["cta1"]} →</a>
        <a href="#services" class="bs">▶ {c["cta2"]}</a>
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

<div class="stbar"><div class="sti">{stats_html}</div></div>

<section class="about" id="about">
  <div class="abi">
    <div class="abimg">
      <img src="{imgs["about"]}" alt="About {name}" loading="lazy"/>
      <div class="abtag">Our Story</div>
    </div>
    <div>
      <div class="sl2">✦ About Us</div>
      <h2 class="sh">Built for <span>Excellence</span>.</h2>
      <p class="ss">We started with a single mission — to deliver the best possible experience for every client. Today, {name} is trusted by thousands and recognised for quality that never compromises.</p>
      <div class="aff">
        <div class="af"><div class="afi">🏆</div><div class="aft"><h4>Award-Winning</h4><p>Recognised by industry leaders for consistent excellence.</p></div></div>
        <div class="af"><div class="afi">🌍</div><div class="aft"><h4>Trusted Globally</h4><p>Clients across India and beyond rely on us every day.</p></div></div>
        <div class="af"><div class="afi">💡</div><div class="aft"><h4>Always Innovating</h4><p>We never stop improving. Better every single day.</p></div></div>
      </div>
    </div>
  </div>
</section>

<section class="services" id="services">
  <div class="svi">
    <div class="sh2">
      <div class="sl2">✦ What We Offer</div>
      <h2 class="sh" style="text-align:center">Why Choose <span>{name}</span></h2>
    </div>
    <div class="sg">{svcs_html}</div>
  </div>
</section>

<section class="gallery" id="gallery">
  <div class="gli">
    <div class="sh2">
      <div class="sl2">✦ Gallery</div>
      <h2 class="sh" style="text-align:center">See It For <span>Yourself</span></h2>
    </div>
    <div class="gg">{gal_html}</div>
  </div>
</section>

<section class="testi" id="testimonials">
  <div class="tti">
    <div class="sh2">
      <div class="sl2">✦ Reviews</div>
      <h2 class="sh" style="text-align:center">What Our <span>Clients Say</span></h2>
    </div>
    <div class="tg">{testi_html}</div>
  </div>
</section>

<section class="cta" id="contact">
  <div class="ctai">
    <h2>Ready to Get Started?</h2>
    <p>Join thousands who already trust {name}. Take the first step today — no commitment needed.</p>
    <div class="cbtns">
      <a href="mailto:hello@{name.lower().replace(" ","")}.com" class="cb1">{c["cta1"]} →</a>
      <a href="tel:+919999999999" class="cb2">📞 Contact Us</a>
    </div>
  </div>
</section>

<footer>
  <div class="fi">
    <div class="ft">
      <div class="fb">
        <div class="flogo">{name}</div>
        <p>{c["sub"][:90]}...</p>
      </div>
      <div class="fc"><h4>Company</h4><a href="#about">About</a><a href="#services">Services</a><a href="#gallery">Gallery</a><a href="#contact">Contact</a></div>
      <div class="fc"><h4>Services</h4>{"".join([f\'<a href="#services">{s[1]}</a>\' for s in c["services"]])}</div>
      <div class="fc"><h4>Connect</h4><a href="#">Instagram</a><a href="#">LinkedIn</a><a href="#">Twitter</a><a href="mailto:hello@{name.lower().replace(" ","")}.com">Email Us</a></div>
    </div>
    <div class="fbot"><p>© 2024 {name}. All rights reserved.</p><p>Built with Dacexy AI</p></div>
  </div>
</footer>

<script>
const nav=document.getElementById("nav");
window.addEventListener("scroll",()=>nav.classList.toggle("sc",scrollY>60));
const hb=document.getElementById("hb"),nm=document.getElementById("nm");
hb.addEventListener("click",()=>nm.classList.toggle("open"));
nm.querySelectorAll("a").forEach(a=>a.addEventListener("click",()=>nm.classList.remove("open")));
const obs=new IntersectionObserver(entries=>entries.forEach(e=>{{if(e.isIntersecting){{e.target.style.opacity="1";e.target.style.transform="translateY(0) scale(1)"}}}}),{{threshold:0.1}});
document.querySelectorAll(".sc,.tc,.af,.gi,.stat").forEach(el=>{{el.style.opacity="0";el.style.transform="translateY(40px) scale(0.97)";el.style.transition="opacity 0.7s ease,transform 0.7s ease";obs.observe(el)}});
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
