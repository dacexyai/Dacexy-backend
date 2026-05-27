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
            "me","i","want","need","please","just","can","you","give","type"}
    words = [w for w in re.sub(r\'[^a-zA-Z0-9 ]\', \'\', p).split()
             if len(w) > 2 and w.lower() not in skip]
    return words[0].title() if words else "Nexus"

CATEGORY_KEYWORDS = {
    "restaurant":    ["restaurant","cafe","bistro","dhaba","tiffin","biryani","pizzeria","steakhouse","sushi","diner","eatery","food truck","bakery","patisserie","catering","fine dining","cuisine","chef","menu items","reservations","table booking","takeaway"],
    "saas":          ["saas","software as a service","b2b software","crm","erp","dashboard","api platform","devtool","developer tool","productivity tool","project management tool","workflow automation","no-code","low-code","subscription software","cloud software","enterprise software","analytics platform"],
    "car":           ["car dealer","automobile dealer","vehicle dealer","car showroom","cars for sale","used cars","new cars","auto dealer","car rental","fleet management","automotive dealership","test drive","car lot"],
    "portfolio":     ["portfolio","my work","my projects","personal website","freelancer","designer portfolio","developer portfolio","photographer portfolio","artist portfolio","creative portfolio","resume site","cv website","showcase my work"],
    "ecommerce":     ["ecommerce","online store","online shop","shopify store","products for sale","buy online","shopping cart","checkout","merchandise","dropship","retail online","fashion store","clothing store","jewelry store","electronics store"],
    "agency":        ["marketing agency","digital agency","creative agency","advertising agency","branding agency","pr agency","seo agency","web agency","design studio","growth agency","media agency","consulting agency"],
    "fitness":       ["gym","fitness center","workout studio","personal trainer","yoga studio","crossfit","pilates studio","health club","wellness center","martial arts","boxing gym","bodybuilding","weight loss program"],
    "education":     ["school","college","university","online course","e-learning","edtech","tutoring","coaching center","training institute","certification course","bootcamp","learning platform","educational institute"],
    "realestate":    ["real estate","property listing","homes for sale","apartments for rent","flat","villa for sale","plot","realtor","real estate agent","property dealer","mortgage","rent property","commercial property","residential property"],
    "hospital":      ["hospital","clinic","doctor","medical center","healthcare","dental clinic","dentist","pharmacy","health center","diagnostic center","specialist doctor","physiotherapy","ayurveda","telemedicine"],
    "hotel":         ["hotel","resort","motel","bed and breakfast","bnb","accommodation","lodging","rooms","suite","vacation rental","boutique hotel","hospitality","spa resort"],
    "law":           ["law firm","lawyer","attorney","legal services","advocate","solicitor","barrister","legal counsel","litigation","corporate law","criminal defense","family law","immigration law","legal aid"],
    "startup":       ["startup","mvp","seed stage","series a","venture","founder","product launch","early stage","tech startup","fintech startup","healthtech startup","saas startup","ai startup"],
    "finance":       ["finance","fintech","banking","investment","wealth management","mutual fund","insurance","accounting","tax","chartered accountant","financial advisor","stock trading","crypto","neobank","lending","payment gateway"],
    "construction":  ["construction","builder","contractor","architect","interior design","renovation","remodeling","civil engineering","infrastructure","building company","real estate developer","landscaping","masonry"],
    "ngo":           ["ngo","nonprofit","charity","foundation","social cause","donation","volunteer","social impact","csr","humanitarian","welfare","fundraising","advocacy"],
    "photography":   ["photography","photographer","photo studio","wedding photography","portrait photography","commercial photography","fashion photography","event photography","photo editing","videography"],
    "music":         ["music","band","musician","singer","dj","music studio","record label","music producer","concert","album","music lessons","guitar teacher","piano teacher","music school"],
    "salon":         ["salon","beauty parlor","hair salon","barbershop","spa","nail salon","makeup artist","beauty studio","hair stylist","grooming","waxing","threading","beauty services"],
    "travel":        ["travel agency","travel","tour operator","tours","vacation packages","holiday packages","destination wedding","adventure travel","travel blog","safari","cruise","backpacking"],
    "food_delivery": ["food delivery","cloud kitchen","ghost kitchen","meal prep","meal delivery","tiffin service","home chef","online food","meal kit","meal subscription"],
    "tech_company":  ["tech company","software company","it company","technology company","digital transformation","it services","software development","app development","web development company","it consulting","cybersecurity company"],
    "event":         ["event management","event planner","wedding planner","corporate events","conference organizer","event venue","party planner","event decorator","wedding coordinator","exhibition organizer"],
    "consulting":    ["consulting","management consulting","business consulting","strategy consulting","hr consulting","operations consulting","supply chain consulting","change management","advisory services"],
    "fashion":       ["fashion","clothing brand","fashion designer","apparel brand","streetwear","luxury fashion","sustainable fashion","fashion label","couture","ready to wear","accessories brand"],
    "interior":      ["interior design","interior designer","home decor","furniture","home furnishing","space planning","interior styling","commercial interior","residential interior","interior architect"],
    "bakery":        ["bakery","cake shop","pastry","dessert shop","confectionery","wedding cake","custom cake","bread bakery","cookie shop","donut shop","macaron","chocolate shop"],
    "coffee":        ["coffee shop","cafe","coffee roaster","specialty coffee","third wave coffee","coffee bar","espresso bar","coffee subscription","coffee brand","tea house","tea cafe"],
    "yoga":          ["yoga","meditation","mindfulness","wellness retreat","yoga teacher","yoga studio","breathwork","sound healing","spiritual wellness","holistic health","chakra","ayurvedic wellness"],
    "pet":           ["pet shop","pet clinic","veterinary","pet grooming","pet boarding","dog trainer","pet care","animal shelter","pet food","pet accessories","veterinarian"],
    "book":          ["bookstore","library","book club","publishing","author website","book review","literary","writing coaching","poetry","book publishing house"],
    "gaming":        ["gaming","esports","game studio","game developer","gaming cafe","mobile game","pc game","gaming community","game streaming","twitch","youtube gaming","game coaching"],
    "crypto":        ["crypto","blockchain","web3","nft","defi","cryptocurrency","token","dao","metaverse","digital assets","crypto exchange","crypto wallet","smart contract"],
    "podcast":       ["podcast","podcaster","podcast studio","podcast network","audio content","podcast hosting","podcast production","radio show","audio storytelling"],
    "newspaper":     ["newspaper","news portal","news website","journalism","media house","online news","digital magazine","blog","content platform","newsletter"],
    "church":        ["church","temple","mosque","gurdwara","religious organization","faith community","ministry","spiritual center","place of worship","religious services","prayer group"],
    "wedding":       ["wedding","wedding planner","bridal","wedding venue","wedding photography","wedding catering","wedding dress","bridal boutique","wedding invitation","wedding decor"],
    "children":      ["children","kids","daycare","kindergarten","preschool","child care","baby products","kids clothing","children entertainment","toy store","children academy"],
    "senior":        ["senior care","elderly care","retirement home","assisted living","nursing home","senior services","elder care","home care for seniors","geriatric care"],
    "insurance":     ["insurance","life insurance","health insurance","car insurance","home insurance","insurance broker","insurance agent","risk management","insurance company"],
    "hr":            ["hr","human resources","recruitment","staffing agency","talent acquisition","executive search","headhunting","job portal","employment agency","workforce solutions"],
    "logistics":     ["logistics","courier","shipping","freight","supply chain","warehouse","last mile delivery","trucking","cargo","3pl","fulfillment center","delivery service"],
    "agriculture":   ["agriculture","farm","farming","organic farm","agritech","crop","fertilizer","seeds","dairy farm","poultry","aquaculture","greenhouse","agricultural machinery"],
    "solar":         ["solar","solar energy","solar panel","renewable energy","green energy","solar installation","wind energy","ev charging","sustainable energy","clean energy"],
    "cleaning":      ["cleaning service","house cleaning","commercial cleaning","janitorial","maid service","deep cleaning","carpet cleaning","sanitization","facility management"],
    "printing":      ["printing","print shop","graphic design","branding","logo design","stationery","packaging design","banner printing","signage","merchandise printing"],
    "pharmacy":      ["pharmacy","medical store","chemist","drug store","online pharmacy","medicine delivery","health products","nutraceuticals","supplements"],
    "automobile_service": ["car service","auto repair","car workshop","mechanic","car wash","auto detailing","tire shop","car accessories","auto parts","battery service","car ac service"],
    "dentist":       ["dental","dentist","dental clinic","oral health","teeth whitening","braces","orthodontist","dental implants","root canal","dental surgery","smile makeover"],
    "optician":      ["optician","eye care","eyewear","spectacles","contact lens","optometry","eye hospital","laser eye surgery","vision care","ophthalmologist"],
    "accounting":    ["accounting","bookkeeping","ca firm","tax filing","gst","audit","payroll","financial reporting","tax consultant","chartered accountant firm"],
    "security":      ["security","security agency","cctv","surveillance","guard service","cybersecurity","private security","access control","fire safety","alarm system"],
    "mining":        ["mining","coal mine","gold mine","mineral extraction","quarry","ore processing","mining equipment","geological survey","mining company"],
    "textile":       ["textile","fabric","garment factory","clothing manufacturer","weaving","embroidery","knitting","textile mill","yarn","denim","silk","cotton"],
    "pharma":        ["pharmaceutical","pharma company","drug manufacturer","medicine","clinical research","biotech","life sciences","medical device","diagnostics company"],
    "airline":       ["airline","aviation","flight booking","charter flight","private jet","helicopter service","air cargo","airport services","aviation training"],
    "shipping":      ["shipping company","maritime","port","vessel","cargo ship","container shipping","freight forwarding","import export","customs clearance","sea freight"],
    "sports":        ["sports","sports club","sports academy","cricket","football","basketball","tennis","swimming","athletics","sports equipment","sports management"],
    "art_gallery":   ["art gallery","art museum","art exhibition","contemporary art","fine art","sculpture","art dealer","art auction","art collection","artist studio"],
    "architect":     ["architect","architecture firm","architectural design","urban planning","landscape architecture","structural engineering","building design","architectural firm"],
    "coworking":     ["coworking","shared workspace","hot desk","serviced office","business center","virtual office","meeting room","collaborative workspace"],
    "mental_health": ["mental health","therapist","psychologist","counseling","therapy","anxiety","depression treatment","psychiatrist","behavioral health","emotional wellness"],
    "recruitment":   ["recruitment","job portal","career","employment","job board","talent platform","hiring platform","job search","career counseling","resume service"],
    "charity":       ["charity","donation","fundraising","social service","community service","homeless shelter","food bank","blood bank","disaster relief","orphanage"],
    "media":         ["media production","film production","video production","documentary","short film","music video","animation studio","vfx studio","post production"],
    "influencer":    ["influencer","content creator","youtuber","instagrammer","social media","personal brand","creator economy","brand deals","sponsorship","merchandise"],
    "coaching":      ["life coach","business coach","executive coach","career coach","mindset coach","success coach","performance coach","leadership coaching","coaching program"],
    "dance":         ["dance academy","dance studio","dance school","ballet","hip hop dance","contemporary dance","classical dance","bharatanatyam","dance teacher","dance classes"],
    "language":      ["language school","english classes","foreign language","translation","interpretation","language learning","spoken english","ielts","toefl","language institute"],
    "astrology":     ["astrology","horoscope","numerology","tarot","vastu","palmistry","vedic astrology","psychic reading","spiritual guidance","jyotish"],
    "florist":       ["florist","flower shop","flower delivery","floral design","wedding flowers","bouquet","floral arrangement","flower subscription","plant nursery","garden center"],
    "catering":      ["catering","caterer","food catering","wedding catering","corporate catering","event catering","buffet","canteen","meal service","tiffin catering"],
    "laundry":       ["laundry","dry cleaning","laundry service","wash and fold","ironing service","garment care","laundromat","express laundry"],
    "plumber":       ["plumber","plumbing","plumbing services","pipe fitting","bathroom fitting","water tank","drainage","sanitation","plumbing contractor"],
    "electrician":   ["electrician","electrical services","wiring","electrical contractor","power backup","generator","ups","solar installation","home automation","electrical repair"],
    "tutor":         ["tutor","tutoring","home tuition","online tutor","math tutor","science tutor","test prep","ielts tutor","competitive exam","jee","neet","upsc coaching"],
    "dietitian":     ["dietitian","nutritionist","diet plan","weight loss","nutrition counseling","meal planning","sports nutrition","diabetic diet","clinical nutrition"],
    "mortgage":      ["mortgage","home loan","property loan","loan broker","loan advisor","refinancing","home financing","mortgage calculator","loan eligibility"],
    "car_rental":    ["car rental","self drive","vehicle rental","cab service","taxi","chauffeur","limousine","bus rental","tempo traveller","outstation cab"],
    "bike":          ["bike shop","bicycle store","cycling","mountain bike","electric bike","bike rental","cycling academy","bike accessories","bike service"],
    "jewelry":       ["jewelry","jeweler","gold jewelry","diamond jewelry","custom jewelry","engagement ring","wedding jewelry","silver jewelry","gemstone","jewelry store"],
    "furniture":     ["furniture","furniture store","custom furniture","wood furniture","modular furniture","office furniture","home furniture","sofa","wardrobe","bed"],
    "electronics":   ["electronics store","gadgets","mobile phone shop","laptop store","electronics repair","consumer electronics","home appliances","tv","camera shop"],
    "hardware":      ["hardware store","tools","building materials","plywood","cement","paint","pipe","hardware shop","construction material","electrical hardware"],
    "optical":       ["optical store","spectacle shop","sunglasses","contact lens store","eyeglass frame","prescription glasses","reading glasses","optical accessories"],
    "swimming":      ["swimming pool","swim school","swimming academy","swim coach","aqua fitness","swimming lessons","competitive swimming","triathlon training"],
    "golf":          ["golf club","golf course","golf academy","golf lessons","golf equipment","mini golf","golf resort","golf tournament","golf instructor"],
    "horse":         ["equestrian","horse riding","horse stable","polo","equestrian club","horse farm","riding lessons","horse training","show jumping","dressage"],
    "diving":        ["scuba diving","snorkeling","diving center","underwater photography","dive resort","freediving","marine biology","ocean adventure","water sports"],
    "climbing":      ["rock climbing","bouldering","climbing gym","mountaineering","trekking","hiking","adventure sports","rappelling","zip line","outdoor adventure"],
    "cannabis":      ["dispensary","cannabis","cbd","hemp","wellness products","herbal supplements","natural remedies","holistic health products"],
    "tattoo":        ["tattoo studio","tattoo artist","body piercing","tattoo parlor","custom tattoo","temporary tattoo","henna","body art"],
    "escape":        ["escape room","puzzle room","team building","entertainment center","gaming lounge","board game cafe","vr arcade","family entertainment"],
    "bowling":       ["bowling alley","sports entertainment","bowling club","family fun","bowling league","cosmic bowling","glow bowling"],
    "cinema":        ["movie theater","cinema hall","multiplex","film screening","drive-in theater","independent cinema","arthouse cinema","film club"],
    "museum":        ["museum","heritage site","cultural center","exhibition hall","science museum","history museum","children museum","virtual museum"],
    "zoo":           ["zoo","wildlife sanctuary","animal park","safari","aquarium","nature reserve","bird park","reptile house","marine park"],
    "amusement":     ["amusement park","theme park","water park","adventure park","rides","roller coaster","family park","kids entertainment"],
    "nightclub":     ["nightclub","bar","lounge","pub","rooftop bar","cocktail bar","sports bar","live music venue","jazz club","comedy club"],
    "coworking":     ["coworking","shared workspace","hot desk","serviced office","business center","virtual office","meeting room","collaborative workspace"],
    "business":      ["company","business","service","professional","firm","enterprise","solutions","services","consulting","management"],
}

# 100+ unique design systems
DESIGN_SYSTEMS = [
    # Dark dramatic
    {"dark":True,"bg":"#0A0A0A","pr":"#E11D48","ac":"#F59E0B","tx":"#FFFFFF","mu":"rgba(255,255,255,0.6)","ca":"rgba(255,255,255,0.05)","br":"rgba(225,29,72,0.25)","nb":"rgba(10,10,10,0.95)","nt":"rgba(255,255,255,0.8)","font":"Playfair Display","hero_style":"split","layout":"bold"},
    {"dark":True,"bg":"#050010","pr":"#8B5CF6","ac":"#06B6D4","tx":"#F5F3FF","mu":"rgba(245,243,255,0.55)","ca":"rgba(139,92,246,0.08)","br":"rgba(139,92,246,0.2)","nb":"rgba(5,0,16,0.95)","nt":"rgba(245,243,255,0.8)","font":"Inter","hero_style":"centered","layout":"tech"},
    {"dark":True,"bg":"#0D0500","pr":"#C8102E","ac":"#FFD700","tx":"#FFF8F0","mu":"rgba(255,248,240,0.55)","ca":"rgba(255,255,255,0.04)","br":"rgba(255,215,0,0.15)","nb":"rgba(13,5,0,0.95)","nt":"rgba(255,248,240,0.8)","font":"Playfair Display","hero_style":"split","layout":"luxury"},
    {"dark":True,"bg":"#0C0500","pr":"#EA580C","ac":"#22C55E","tx":"#FFF7ED","mu":"rgba(255,247,237,0.55)","ca":"rgba(234,88,12,0.08)","br":"rgba(234,88,12,0.2)","nb":"rgba(12,5,0,0.95)","nt":"rgba(255,247,237,0.8)","font":"Inter","hero_style":"split","layout":"energy"},
    {"dark":True,"bg":"#060A14","pr":"#3B82F6","ac":"#10B981","tx":"#EFF6FF","mu":"rgba(239,246,255,0.55)","ca":"rgba(59,130,246,0.08)","br":"rgba(59,130,246,0.2)","nb":"rgba(6,10,20,0.95)","nt":"rgba(239,246,255,0.8)","font":"Inter","hero_style":"centered","layout":"corporate"},
    {"dark":True,"bg":"#0A0800","pr":"#B45309","ac":"#FCD34D","tx":"#FFFBEB","mu":"rgba(255,251,235,0.55)","ca":"rgba(180,83,9,0.08)","br":"rgba(252,211,77,0.15)","nb":"rgba(10,8,0,0.95)","nt":"rgba(255,251,235,0.8)","font":"Playfair Display","hero_style":"split","layout":"luxury"},
    {"dark":True,"bg":"#030712","pr":"#06B6D4","ac":"#8B5CF6","tx":"#F0FDFE","mu":"rgba(240,253,254,0.55)","ca":"rgba(6,182,212,0.08)","br":"rgba(6,182,212,0.2)","nb":"rgba(3,7,18,0.95)","nt":"rgba(240,253,254,0.8)","font":"Inter","hero_style":"centered","layout":"tech"},
    {"dark":True,"bg":"#0A0A1A","pr":"#F43F5E","ac":"#A78BFA","tx":"#FFF1F2","mu":"rgba(255,241,242,0.55)","ca":"rgba(244,63,94,0.08)","br":"rgba(244,63,94,0.2)","nb":"rgba(10,10,26,0.95)","nt":"rgba(255,241,242,0.8)","font":"Inter","hero_style":"split","layout":"bold"},
    {"dark":True,"bg":"#071A0E","pr":"#16A34A","ac":"#FCD34D","tx":"#F0FDF4","mu":"rgba(240,253,244,0.55)","ca":"rgba(22,163,74,0.08)","br":"rgba(22,163,74,0.2)","nb":"rgba(7,26,14,0.95)","nt":"rgba(240,253,244,0.8)","font":"Inter","hero_style":"split","layout":"natural"},
    {"dark":True,"bg":"#14000A","pr":"#DB2777","ac":"#FB923C","tx":"#FDF2F8","mu":"rgba(253,242,248,0.55)","ca":"rgba(219,39,119,0.08)","br":"rgba(219,39,119,0.2)","nb":"rgba(20,0,10,0.95)","nt":"rgba(253,242,248,0.8)","font":"Playfair Display","hero_style":"centered","layout":"luxury"},
    # Light vibrant
    {"dark":False,"bg":"#FFFFFF","pr":"#6366F1","ac":"#06B6D4","tx":"#0F0F1A","mu":"#6B7280","ca":"#F8F7FF","br":"#E5E7EB","nb":"rgba(255,255,255,0.97)","nt":"#374151","font":"Inter","hero_style":"split","layout":"clean"},
    {"dark":False,"bg":"#FFFBF0","pr":"#D97706","ac":"#EF4444","tx":"#1C1917","mu":"#78716C","ca":"#FEF3C7","br":"#FDE68A","nb":"rgba(255,251,240,0.97)","nt":"#44403C","font":"Playfair Display","hero_style":"split","layout":"warm"},
    {"dark":False,"bg":"#F0FDF4","pr":"#059669","ac":"#F97316","tx":"#022C22","mu":"#6B7280","ca":"#DCFCE7","br":"#A7F3D0","nb":"rgba(240,253,244,0.97)","nt":"#065F46","font":"Inter","hero_style":"split","layout":"fresh"},
    {"dark":False,"bg":"#FFF5F5","pr":"#DC2626","ac":"#F59E0B","tx":"#1A0000","mu":"#6B7280","ca":"#FEE2E2","br":"#FECACA","nb":"rgba(255,245,245,0.97)","nt":"#7F1D1D","font":"Playfair Display","hero_style":"centered","layout":"bold"},
    {"dark":False,"bg":"#FAF5FF","pr":"#7C3AED","ac":"#F59E0B","tx":"#1A0A3E","mu":"#6B7280","ca":"#EDE9FE","br":"#DDD6FE","nb":"rgba(250,245,255,0.97)","nt":"#4C1D95","font":"Playfair Display","hero_style":"split","layout":"creative"},
    {"dark":False,"bg":"#EFF6FF","pr":"#2563EB","ac":"#F59E0B","tx":"#020617","mu":"#6B7280","ca":"#DBEAFE","br":"#BFDBFE","nb":"rgba(239,246,255,0.97)","nt":"#1E3A8A","font":"Inter","hero_style":"split","layout":"corporate"},
    {"dark":False,"bg":"#FFF7ED","pr":"#EA580C","ac":"#22C55E","tx":"#1C0A00","mu":"#6B7280","ca":"#FFEDD5","br":"#FED7AA","nb":"rgba(255,247,237,0.97)","nt":"#7C2D12","font":"Inter","hero_style":"centered","layout":"energy"},
    {"dark":False,"bg":"#F0FFFE","pr":"#0891B2","ac":"#10B981","tx":"#042F2E","mu":"#6B7280","ca":"#CCFBF1","br":"#99F6E4","nb":"rgba(240,255,254,0.97)","nt":"#134E4A","font":"Inter","hero_style":"split","layout":"clean"},
    {"dark":False,"bg":"#FAFAF8","pr":"#0F0F0F","ac":"#F59E0B","tx":"#0F0F0F","mu":"#6B7280","ca":"#F5F5F0","br":"#E5E5E0","nb":"rgba(250,250,248,0.97)","nt":"#0F0F0F","font":"Playfair Display","hero_style":"centered","layout":"minimal"},
    {"dark":False,"bg":"#FDF4FF","pr":"#A21CAF","ac":"#F59E0B","tx":"#2E1065","mu":"#6B7280","ca":"#FAE8FF","br":"#F0ABFC","nb":"rgba(253,244,255,0.97)","nt":"#6B21A8","font":"Playfair Display","hero_style":"split","layout":"luxury"},
    # Gradient/special
    {"dark":True,"bg":"#0F0F23","pr":"#F97316","ac":"#FACC15","tx":"#FFFBEB","mu":"rgba(255,251,235,0.6)","ca":"rgba(249,115,22,0.08)","br":"rgba(249,115,22,0.2)","nb":"rgba(15,15,35,0.95)","nt":"rgba(255,251,235,0.8)","font":"Inter","hero_style":"centered","layout":"bold"},
    {"dark":True,"bg":"#0A1628","pr":"#0EA5E9","ac":"#38BDF8","tx":"#F0F9FF","mu":"rgba(240,249,255,0.55)","ca":"rgba(14,165,233,0.08)","br":"rgba(14,165,233,0.2)","nb":"rgba(10,22,40,0.95)","nt":"rgba(240,249,255,0.8)","font":"Inter","hero_style":"split","layout":"tech"},
    {"dark":False,"bg":"#FEFCE8","pr":"#CA8A04","ac":"#DC2626","tx":"#1C1400","mu":"#78716C","ca":"#FEF9C3","br":"#FEF08A","nb":"rgba(254,252,232,0.97)","nt":"#92400E","font":"Playfair Display","hero_style":"centered","layout":"warm"},
    {"dark":False,"bg":"#F8FAFC","pr":"#334155","ac":"#3B82F6","tx":"#0F172A","mu":"#64748B","ca":"#F1F5F9","br":"#CBD5E1","nb":"rgba(248,250,252,0.97)","nt":"#1E293B","font":"Inter","hero_style":"split","layout":"minimal"},
    {"dark":True,"bg":"#0D1117","pr":"#58A6FF","ac":"#3FB950","tx":"#C9D1D9","mu":"rgba(201,209,217,0.6)","ca":"rgba(88,166,255,0.08)","br":"rgba(88,166,255,0.15)","nb":"rgba(13,17,23,0.95)","nt":"rgba(201,209,217,0.8)","font":"Inter","hero_style":"centered","layout":"tech"},
    {"dark":False,"bg":"#FFF1F2","pr":"#E11D48","ac":"#F59E0B","tx":"#881337","mu":"#6B7280","ca":"#FFE4E6","br":"#FECDD3","nb":"rgba(255,241,242,0.97)","nt":"#9F1239","font":"Playfair Display","hero_style":"split","layout":"luxury"},
    {"dark":True,"bg":"#1A0533","pr":"#C084FC","ac":"#F472B6","tx":"#FAF5FF","mu":"rgba(250,245,255,0.6)","ca":"rgba(192,132,252,0.08)","br":"rgba(192,132,252,0.2)","nb":"rgba(26,5,51,0.95)","nt":"rgba(250,245,255,0.8)","font":"Playfair Display","hero_style":"centered","layout":"creative"},
    {"dark":False,"bg":"#ECFDF5","pr":"#10B981","ac":"#3B82F6","tx":"#022C22","mu":"#6B7280","ca":"#D1FAE5","br":"#6EE7B7","nb":"rgba(236,253,245,0.97)","nt":"#065F46","font":"Inter","hero_style":"split","layout":"fresh"},
    {"dark":True,"bg":"#18181B","pr":"#A1A1AA","ac":"#FACC15","tx":"#FAFAFA","mu":"rgba(250,250,250,0.5)","ca":"rgba(255,255,255,0.04)","br":"rgba(255,255,255,0.1)","nb":"rgba(24,24,27,0.97)","nt":"rgba(250,250,250,0.8)","font":"Inter","hero_style":"centered","layout":"minimal"},
    {"dark":False,"bg":"#FEF9EE","pr":"#B45309","ac":"#059669","tx":"#1C1200","mu":"#78716C","ca":"#FEF3C7","br":"#FDE68A","nb":"rgba(254,249,238,0.97)","nt":"#78350F","font":"Playfair Display","hero_style":"split","layout":"natural"},
    {"dark":True,"bg":"#020617","pr":"#6366F1","ac":"#A5F3FC","tx":"#E0F2FE","mu":"rgba(224,242,254,0.55)","ca":"rgba(99,102,241,0.08)","br":"rgba(99,102,241,0.2)","nb":"rgba(2,6,23,0.97)","nt":"rgba(224,242,254,0.8)","font":"Inter","hero_style":"split","layout":"tech"},
    {"dark":False,"bg":"#F5F3FF","pr":"#4F46E5","ac":"#EC4899","tx":"#1E1B4B","mu":"#6B7280","ca":"#EDE9FE","br":"#C4B5FD","nb":"rgba(245,243,255,0.97)","nt":"#3730A3","font":"Inter","hero_style":"centered","layout":"creative"},
    {"dark":True,"bg":"#0C1A0C","pr":"#22C55E","ac":"#FACC15","tx":"#F0FDF4","mu":"rgba(240,253,244,0.55)","ca":"rgba(34,197,94,0.08)","br":"rgba(34,197,94,0.15)","nb":"rgba(12,26,12,0.97)","nt":"rgba(240,253,244,0.8)","font":"Inter","hero_style":"split","layout":"natural"},
    {"dark":False,"bg":"#FFF8F0","pr":"#C2410C","ac":"#FBBF24","tx":"#431407","mu":"#78716C","ca":"#FEE2D5","br":"#FCA27B","nb":"rgba(255,248,240,0.97)","nt":"#7C2D12","font":"Playfair Display","hero_style":"centered","layout":"warm"},
    {"dark":True,"bg":"#08080F","pr":"#E879F9","ac":"#22D3EE","tx":"#FAF5FF","mu":"rgba(250,245,255,0.55)","ca":"rgba(232,121,249,0.06)","br":"rgba(232,121,249,0.15)","nb":"rgba(8,8,15,0.97)","nt":"rgba(250,245,255,0.8)","font":"Inter","hero_style":"centered","layout":"bold"},
    {"dark":False,"bg":"#F8F9FA","pr":"#212529","ac":"#E63946","tx":"#212529","mu":"#6C757D","ca":"#E9ECEF","br":"#CED4DA","nb":"rgba(248,249,250,0.97)","nt":"#495057","font":"Inter","hero_style":"split","layout":"minimal"},
    {"dark":True,"bg":"#0A0A0A","pr":"#FFFFFF","ac":"#F59E0B","tx":"#FFFFFF","mu":"rgba(255,255,255,0.5)","ca":"rgba(255,255,255,0.04)","br":"rgba(255,255,255,0.1)","nb":"rgba(10,10,10,0.97)","nt":"rgba(255,255,255,0.8)","font":"Playfair Display","hero_style":"centered","layout":"minimal"},
    {"dark":False,"bg":"#FFF0F3","pr":"#FF4D6D","ac":"#FF9F1C","tx":"#590D22","mu":"#6B7280","ca":"#FFD6E0","br":"#FFAFC5","nb":"rgba(255,240,243,0.97)","nt":"#A4133C","font":"Playfair Display","hero_style":"split","layout":"bold"},
    {"dark":True,"bg":"#061014","pr":"#34D399","ac":"#60A5FA","tx":"#ECFDF5","mu":"rgba(236,253,245,0.55)","ca":"rgba(52,211,153,0.08)","br":"rgba(52,211,153,0.15)","nb":"rgba(6,16,20,0.97)","nt":"rgba(236,253,245,0.8)","font":"Inter","hero_style":"split","layout":"tech"},
    {"dark":False,"bg":"#FFFAF0","pr":"#F97316","ac":"#14B8A6","tx":"#1C0A00","mu":"#78716C","ca":"#FFF1E0","br":"#FED7AA","nb":"rgba(255,250,240,0.97)","nt":"#7C2D12","font":"Playfair Display","hero_style":"centered","layout":"warm"},
    {"dark":True,"bg":"#140028","pr":"#A855F7","ac":"#EC4899","tx":"#FAF5FF","mu":"rgba(250,245,255,0.55)","ca":"rgba(168,85,247,0.08)","br":"rgba(168,85,247,0.2)","nb":"rgba(20,0,40,0.97)","nt":"rgba(250,245,255,0.8)","font":"Playfair Display","hero_style":"split","layout":"luxury"},
    {"dark":False,"bg":"#F0F9FF","pr":"#0284C7","ac":"#F59E0B","tx":"#0C4A6E","mu":"#6B7280","ca":"#E0F2FE","br":"#BAE6FD","nb":"rgba(240,249,255,0.97)","nt":"#075985","font":"Inter","hero_style":"split","layout":"corporate"},
    {"dark":True,"bg":"#0F1923","pr":"#FB923C","ac":"#34D399","tx":"#FFF7ED","mu":"rgba(255,247,237,0.55)","ca":"rgba(251,146,60,0.08)","br":"rgba(251,146,60,0.2)","nb":"rgba(15,25,35,0.97)","nt":"rgba(255,247,237,0.8)","font":"Inter","hero_style":"centered","layout":"bold"},
    {"dark":False,"bg":"#F9FAFB","pr":"#111827","ac":"#6366F1","tx":"#111827","mu":"#6B7280","ca":"#F3F4F6","br":"#D1D5DB","nb":"rgba(249,250,251,0.97)","nt":"#374151","font":"Inter","hero_style":"split","layout":"minimal"},
    {"dark":True,"bg":"#180A00","pr":"#F97316","ac":"#FCD34D","tx":"#FFF7ED","mu":"rgba(255,247,237,0.6)","ca":"rgba(249,115,22,0.1)","br":"rgba(252,211,77,0.2)","nb":"rgba(24,10,0,0.97)","nt":"rgba(255,247,237,0.8)","font":"Playfair Display","hero_style":"centered","layout":"warm"},
    {"dark":False,"bg":"#FAFFFE","pr":"#0D9488","ac":"#F59E0B","tx":"#042F2E","mu":"#6B7280","ca":"#CCFBF1","br":"#99F6E4","nb":"rgba(250,255,254,0.97)","nt":"#0F766E","font":"Inter","hero_style":"split","layout":"fresh"},
    {"dark":True,"bg":"#09090B","pr":"#D97706","ac":"#A78BFA","tx":"#FFFBEB","mu":"rgba(255,251,235,0.55)","ca":"rgba(217,119,6,0.08)","br":"rgba(217,119,6,0.2)","nb":"rgba(9,9,11,0.97)","nt":"rgba(255,251,235,0.8)","font":"Playfair Display","hero_style":"split","layout":"luxury"},
]

def get_design(prompt: str) -> dict:
    # Use prompt hash for consistent but varied design selection
    idx = abs(hash(prompt + "design")) % len(DESIGN_SYSTEMS)
    return DESIGN_SYSTEMS[idx]

def get_category(prompt: str) -> str:
    p = prompt.lower()
    noise = ["make","build","create","generate","design","need","want","please","just",
             "website","site","page","landing page","web app","online presence","for",
             "me","a","an","the","i","can","you","give","type","good","great","best",
             "professional","beautiful","modern","awesome","nice"]
    clean = p
    for n in noise:
        clean = re.sub(r"\\b" + n + r"\\b", " ", clean)
    clean = clean.strip()

    scores = {}
    for cat, keywords in CATEGORY_KEYWORDS.items():
        score = 0
        for kw in keywords:
            if kw in clean:
                score += len(kw.split()) * 2
            elif any(word in clean for word in kw.split() if len(word) > 4):
                score += 1
        scores[cat] = score

    best_cat = max(scores, key=scores.get)
    return best_cat if scores[best_cat] > 0 else "business"

CONTENT = {
    "restaurant":    {"tagline":"Where Every Bite Tells a Story","sub":"Authentic flavours crafted with passion. Fresh ingredients, timeless recipes, unforgettable moments.","cta1":"Reserve a Table","cta2":"View Menu","services_title":"Our Specialties","services":[("🍽️","Fine Dining","Exquisite multi-course meals by award-winning chefs."),("🍷","Premium Bar","Curated wines, craft cocktails, and rare spirits."),("🎂","Private Events","Exclusive rooms for celebrations."),("🚗","Home Delivery","Restaurant quality at your doorstep.")],"stats":[("15+","Years"),("50K+","Guests"),("4.9★","Rating"),("200+","Dishes")],"testi":[("Arjun M.","Food Critic","Best dining in the city. Every dish is perfection."),("Priya S.","Guest","We celebrate every anniversary here. Magical."),("Rahul K.","Corporate","World-class private dining.")],"af":[("🏆","Award-Winning","Top culinary awards for 10 consecutive years."),("🌿","Farm to Table","Only locally sourced fresh ingredients."),("🎶","Perfect Ambiance","As memorable as the food itself.")]},
    "saas":          {"tagline":"Ship Faster. Scale Without Limits.","sub":"AI-powered platform that automates your entire workflow. Built for teams that move fast.","cta1":"Start Free Trial","cta2":"Watch Demo","services_title":"Platform Features","services":[("⚡","Automation","Eliminate repetitive tasks with intelligent automation."),("📊","Analytics","Real-time dashboards with actionable insights."),("🔗","Integrations","Connect 200+ tools your team already uses."),("🛡️","Security","SOC2, SSO, SAML, audit logs built in.")],"stats":[("10K+","Teams"),("99.9%","Uptime"),("10x","Faster"),("4.8★","G2")],"testi":[("Sarah C.","CTO","Cut costs 60% in month one. Transformative."),("Marcus J.","CEO","Team ships 3x faster. Immediate ROI."),("Aisha P.","VP Eng","Best developer experience ever. World-class.")],"af":[("⚡","Sub-100ms","Blazing fast response times your users will love."),("🔒","SOC2","Enterprise security built in from day one."),("🤖","AI-Native","Every feature powered by intelligent automation.")]},
    "car":           {"tagline":"Drive Your Dream Car Today","sub":"Premium vehicles, transparent pricing, and a buying experience that respects your time.","cta1":"Browse Inventory","cta2":"Book Test Drive","services_title":"Our Services","services":[("🚗","New Cars","Latest models at unbeatable prices."),("✅","Certified Used","Pre-owned vehicles inspected and warrantied."),("💳","Easy Finance","Loans approved in 24 hours from 7.9% APR."),("🔧","Service Centre","Manufacturer-trained technicians.")],"stats":[("2K+","Cars Sold"),("500+","Reviews"),("15+","Brands"),("24hr","Loan Approval")],"testi":[("Vikram P.","Business Owner","Found my dream SUV. Zero pressure sales."),("Sunita R.","Doctor","Financing approved in hours. Drove home same day."),("Amit K.","Entrepreneur","Third car here. Never going anywhere else.")],"af":[("🏅","150-Point Check","Every used vehicle certified and inspected."),("💰","Price Match","We match any verified competitor price."),("🔧","Free Service","Complimentary maintenance checks for life.")]},
    "portfolio":     {"tagline":"Design That Moves People","sub":"I craft digital products that convert. Every pixel deliberate. Every interaction purposeful.","cta1":"View My Work","cta2":"Hire Me","services_title":"What I Do","services":[("🎨","UI/UX Design","Research-driven interfaces users love."),("💻","Development","React and Next.js — fast and accessible."),("📱","Mobile Apps","iOS and Android that delight users."),("🚀","Brand Identity","Logos and systems that stand the test of time.")],"stats":[("50+","Projects"),("30+","Clients"),("5★","Rating"),("8+","Years")],"testi":[("David P.","Founder","Delivered beyond expectations. On time."),("Emma W.","Director","Conversion up 240% after redesign."),("Carlos R.","CEO","Best investment this year. Life-changing.")],"af":[("🎯","Data-Driven","Every design decision backed by research."),("⚡","Fast Delivery","Production-ready in days, not months."),("🤝","Collaborative","I work as an extension of your team.")]},
    "ecommerce":     {"tagline":"Premium Quality, Delivered Fast","sub":"Curated collections you will love. Free shipping. 30-day returns. Shop with confidence.","cta1":"Shop Now","cta2":"View Lookbook","services_title":"Why Shop With Us","services":[("🚚","Free Shipping","Express delivery on every order."),("✅","Quality Assured","47-point inspection on every product."),("↩️","Easy Returns","30-day returns, no questions asked."),("💳","Secure Checkout","UPI, cards, EMI, COD accepted.")],"stats":[("50K+","Customers"),("10K+","Products"),("4.9★","Rating"),("99%","Satisfaction")],"testi":[("Sneha G.","Buyer","Incredible quality. Delivered in 2 days."),("Vikram N.","Member","Shopping here 3 years. Always excellent."),("Divya K.","Blogger","My go-to for premium finds.")],"af":[("🚚","Express Delivery","Free on all orders, no minimum spend."),("↩️","30-Day Returns","No questions. Full refund guaranteed."),("✅","Quality Certified","47-point inspection every product.")]},
    "agency":        {"tagline":"We Build Brands That Dominate Markets","sub":"Full-service growth agency. Strategy, creative, and technology that turns businesses into leaders.","cta1":"Get a Proposal","cta2":"See Case Studies","services_title":"Our Services","services":[("📈","Growth Strategy","Data-driven plans for explosive growth."),("🎯","Performance Ads","Campaigns that consistently beat benchmarks."),("🌐","Digital Products","Websites and apps that convert visitors."),("✍️","Brand and Creative","Stories that connect and drive action.")],"stats":[("100+","Brands"),("₹50Cr+","Revenue"),("4.9★","Rating"),("8+","Years")],"testi":[("Ankit J.","CMO","Tripled leads in 90 days. Best agency."),("Meera K.","Founder","Rebrand drove 180% revenue growth."),("Rajesh P.","CEO","True growth partners. Exceptional results.")],"af":[("📊","Data-Driven","Every strategy backed by research."),("⚡","Agile","Results in weeks, not quarters."),("🎯","ROI-Obsessed","Every spend tied to measurable outcomes.")]},
    "fitness":       {"tagline":"Transform Your Body. Own Your Life.","sub":"Expert coaching, elite facilities, community that refuses to let you quit. Start today.","cta1":"Start Free Trial","cta2":"View Programs","services_title":"Our Programs","services":[("💪","Strength","Elite programming to build real power."),("🏃","HIIT Cardio","High-intensity sessions that torch fat."),("🧘","Recovery","Yoga and mobility to prevent injury."),("🥗","Nutrition","Personalised plans that fuel transformation.")],"stats":[("5K+","Members"),("50+","Coaches"),("98%","Success"),("4.9★","Rating")],"testi":[("Kiran R.","Member","Lost 20kg in 6 months. Life-changing."),("Ananya S.","Runner","PB improved 22 minutes. World-class."),("Dev M.","Athlete","12kg muscle in a year. Real programming.")],"af":[("🏆","Elite Coaches","Internationally certified trainers."),("📊","Science-Based","Peer-reviewed sports science programming."),("👥","Community","Support system that keeps you accountable.")]},
    "education":     {"tagline":"Learn Without Limits. Grow Without Ceiling.","sub":"World-class instructors. Live cohorts. Lifetime access. Certifications employers value.","cta1":"Enroll Now","cta2":"Browse Courses","services_title":"What We Offer","services":[("📚","Expert Courses","Learn from top industry practitioners."),("🎯","Live Cohorts","Real-time classes with Q&A and mentorship."),("🏆","Certifications","Credentials hiring managers trust."),("♾️","Lifetime Access","Learn at your pace, revisit forever.")],"stats":[("20K+","Students"),("500+","Courses"),("4.9★","Rating"),("95%","Placement")],"testi":[("Rohan M.","Graduate","Dream job 3 months after completing."),("Priya T.","Career Changer","Best investment in my career ever."),("Amit S.","Professional","Promoted twice. Skills directly applicable.")],"af":[("👨‍🏫","Expert Instructors","Industry practitioners with real results."),("🎯","Project-Based","Build real projects, not just watch videos."),("🏆","Recognised","Credentials employers and managers trust.")]},
    "realestate":    {"tagline":"Find Your Perfect Home","sub":"Premium listings, trusted agents, transparent process. Buying, selling, or renting made effortless.","cta1":"Browse Properties","cta2":"Talk to Agent","services_title":"Our Services","services":[("🏠","Residential Sales","Premium homes in prime locations."),("🔑","Rental","Verified listings with transparent pricing."),("💼","Commercial","Offices and retail for every business."),("📋","Management","Complete end-to-end property management.")],"stats":[("5K+","Properties"),("2K+","Clients"),("₹500Cr+","Transactions"),("4.9★","Rating")],"testi":[("Suresh P.","Buyer","Perfect 3BHK in 2 weeks. Agent was exceptional."),("Kavita M.","Investor","ROI on properties recommended has been outstanding."),("Arun K.","Seller","Sold above asking in 10 days. Remarkable.")],"af":[("🔍","Market Knowledge","Hyper-local expertise in every area."),("💰","Best Price","We negotiate hard for the best deal."),("📋","Paperwork","Every document, verification, legal step handled.")]},
    "hospital":      {"tagline":"Expert Care, Every Step of the Way","sub":"Compassionate healthcare with cutting-edge technology. Your health is our only priority.","cta1":"Book Appointment","cta2":"Find a Doctor","services_title":"Our Departments","services":[("🫀","Cardiology","Comprehensive heart care from diagnosis to surgery."),("🧠","Neurology","Advanced neurological treatment and care."),("🦷","Dental","Complete dental services from routine to complex."),("👶","Paediatrics","Specialised child healthcare for all ages.")],"stats":[("50K+","Patients"),("50+","Specialists"),("20+","Departments"),("4.9★","Rating")],"testi":[("Ramesh K.","Patient","The care here saved my life. Exceptional team."),("Sunita V.","Family","Compassionate, skilled, always available."),("Dr. Anil S.","Physician","Best facility in the region. Refer all complex cases here.")],"af":[("👨‍⚕️","Expert Specialists","50+ specialists across every department."),("🏥","Advanced Tech","State-of-the-art diagnostic and surgical."),("❤️","Patient-First","Treating the whole person, not just illness.")]},
    "hotel":         {"tagline":"Where Luxury Meets Serenity","sub":"Extraordinary escape where world-class hospitality and breathtaking comfort come together.","cta1":"Book Your Stay","cta2":"Explore Rooms","services_title":"Our Offerings","services":[("🛏️","Luxury Rooms","Beautifully appointed rooms with stunning views."),("🍽️","Fine Dining","Award-winning restaurants serving world cuisine."),("🏊","Pool and Spa","Infinity pool and full-service wellness."),("💼","Business Centre","State-of-the-art conference facilities.")],"stats":[("20+","Years"),("10K+","Guests"),("5★","Rating"),("4.9★","Reviews")],"testi":[("Ananya P.","Honeymooner","Most magical experience of our lives."),("Rohit V.","Business","World-class facilities. My go-to every visit."),("Meera S.","Leisure","Every detail perfect. Return every year.")],"af":[("⭐","5-Star Service","Award-winning hospitality anticipates every need."),("🍽️","Signature Dining","Three restaurants, each a destination."),("🧖","World-Class Spa","A sanctuary of wellness and rejuvenation.")]},
    "law":           {"tagline":"Justice. Expertise. Results.","sub":"Experienced legal counsel for individuals and businesses. We fight for your rights with precision.","cta1":"Free Consultation","cta2":"Our Practice Areas","services_title":"Practice Areas","services":[("🏢","Corporate Law","Business formation, contracts, M&A, governance."),("⚖️","Civil Litigation","Representation across all civil courts."),("👨‍👩‍👧","Family Law","Divorce, custody, adoption, all family matters."),("🏠","Property Law","Real estate transactions, disputes, rights.")],"stats":[("10K+","Cases Won"),("25+","Years"),("200+","Corporate Clients"),("4.9★","Rating")],"testi":[("Rajesh M.","Business Owner","Won a case others said was unwinnable."),("Priya S.","Client","Handled with total sensitivity and professionalism."),("Amit Corp","General Counsel","Trusted legal partner for 10 years.")],"af":[("⚖️","Track Record","10,000+ cases won across all courts."),("🔒","Confidential","Absolute attorney-client privilege always."),("📞","24/7 Available","Always accessible for urgent matters.")]},
    "startup":       {"tagline":"From Zero to Category Leader","sub":"Building the future. Join us at the ground floor of what will be the defining company of our generation.","cta1":"Join Waitlist","cta2":"See How It Works","services_title":"What We Are Building","services":[("⚡","Core Product","Fastest, most intuitive solution in the market."),("🤖","AI Layer","Features that learn with every interaction."),("🔗","Platform API","Open platform developers can build on."),("🌐","Global Scale","Infrastructure for millions from day one.")],"stats":[("1K+","Beta Users"),("₹2Cr+","Pre-orders"),("3x","Monthly Growth"),("4.9★","Beta")],"testi":[("Ankit S.","Beta User","This is going to be massive. Never seen anything like it."),("Meera V.","Investor","Most impressive founding team and product."),("Rahul P.","Early Adopter","Switched day one, never looked back.")],"af":[("🚀","Hypergrowth","3x month-over-month since launch."),("🤖","AI-First","Intelligence built in, not bolted on."),("🌍","Global Vision","India first, then the world.")]},
    "finance":       {"tagline":"Your Wealth. Our Expertise.","sub":"SEBI-registered advisors helping you build, protect, and grow wealth through disciplined planning.","cta1":"Free Consultation","cta2":"Our Services","services_title":"Our Services","services":[("📈","Wealth Mgmt","Personalised portfolios aligned to your goals."),("🏦","Mutual Funds","Curated funds and SIP planning."),("🛡️","Insurance","Comprehensive coverage for everything you have built."),("📋","Tax Planning","Legal optimisation to maximise returns.")],"stats":[("5K+","Clients"),("₹500Cr+","AUM"),("15+","Years"),("4.9★","Rating")],"testi":[("Suresh M.","Business","Portfolio grown 18% annually for 5 years."),("Kavita P.","Retired","Secured my retirement completely. Total peace of mind."),("Arun S.","Professional","Started my SIP here. Remarkable compounding.")],"af":[("📊","Research-Driven","Recommendations backed by rigorous analysis."),("🔒","SEBI Registered","Fully regulated, compliant with all guidelines."),("💼","Personalised","No generic advice. Built for your situation.")]},
    "construction":  {"tagline":"Building Dreams. Delivering Excellence.","sub":"From homes to commercial complexes, delivered on time, on budget, to highest quality standards.","cta1":"Get a Quote","cta2":"View Projects","services_title":"Our Services","services":[("🏠","Residential","Custom homes built to highest specifications."),("🏢","Commercial","Offices, malls, industrial at scale."),("🎨","Interior Design","Complete fit-out services for every space."),("🔧","Renovation","Expert renovation of existing structures.")],"stats":[("500+","Projects"),("₹500Cr+","Value"),("20+","Years"),("4.9★","Rating")],"testi":[("Vikram S.","Developer","5 projects with them. Quality always perfect."),("Anita R.","Home Owner","My dream home, exactly as imagined."),("Raj Corp","Commercial","Office complex on time, on budget, exceptional.")],"af":[("🏗️","Turnkey","Complete management from foundation to finishing."),("⏰","On-Time","Never missed a project deadline in 20 years."),("🏆","ISO 9001","Certified processes ensuring highest quality.")]},
    "ngo":           {"tagline":"Every Life Deserves Dignity","sub":"Compassion and action creating lasting change for communities that need it most.","cta1":"Donate Now","cta2":"Get Involved","services_title":"Our Programs","services":[("📚","Education","Scholarships for underprivileged children."),("🏥","Healthcare","Mobile clinics in remote communities."),("💼","Livelihood","Skills training and microfinance programs."),("🌱","Environment","Tree planting and water conservation.")],"stats":[("100K+","Lives Impacted"),("15+","Years"),("50+","Communities"),("4.9★","Transparency")],"testi":[("Anita S.","Donor","I can see exactly where my money goes. Real impact."),("Rahul M.","Corporate","Most transparent NGO we have ever partnered with."),("Meera P.","Volunteer","Changed my life as much as the communities.")],"af":[("✅","100% Transparent","Full financial reports published for every donor."),("🎯","Measurable","Every program evaluated against audited outcomes."),("🤝","Community-Led","Designed with and for the communities we serve.")]},
    "photography":   {"tagline":"Capturing Moments That Last Forever","sub":"Every frame tells a story. Professional photography that transforms ordinary moments into extraordinary memories.","cta1":"Book a Session","cta2":"View Portfolio","services_title":"Our Services","services":[("📸","Wedding Photography","Your perfect day captured forever."),("👤","Portrait Sessions","Professional headshots and personal portraits."),("🏢","Commercial Photography","Product and corporate photography."),("🎬","Videography","Cinematic videos that move people.")],"stats":[("500+","Sessions"),("50K+","Photos"),("5★","Rating"),("10+","Years")],"testi":[("Sneha P.","Bride","Our wedding photos are absolutely breathtaking."),("Rajesh K.","CEO","Professional headshots exceeded all expectations."),("Priya M.","Marketing","Commercial shots drove our campaign results.")],"af":[("📷","Award-Winning","Recognised by national photography associations."),("🎨","Artistic Vision","Every photo is a work of art."),("💾","Fast Delivery","Edited photos delivered within 48 hours.")]},
    "music":         {"tagline":"Where Music Meets Passion","sub":"Professional music production, lessons, and performances. Where talent meets opportunity.","cta1":"Book a Session","cta2":"Listen Now","services_title":"Our Services","services":[("🎵","Music Production","Professional recording and mixing."),("🎸","Music Lessons","Expert tuition for all instruments and levels."),("🎤","Live Performances","Bookings for events and concerts."),("🎼","Composition","Original music composition and arrangement.")],"stats":[("1K+","Artists",""),("500+","Albums",""),("20+","Years",""),("5★","Rating","")],"testi":[("Arjun S.","Artist","My album would not exist without this studio."),("Priya T.","Student","My guitar skills transformed in 3 months."),("Event Co.","Client","Live performance was the highlight of our event.")],"af":[("🎵","Pro Studio","State-of-the-art recording equipment."),("🏆","Award-Winning","Produced chart-topping albums."),("👨‍🏫","Expert Faculty","Industry professionals teaching real skills.")]},
    "salon":         {"tagline":"Where Beauty Meets Expertise","sub":"Premium salon services in a luxurious setting. Look and feel your absolute best every single day.","cta1":"Book Appointment","cta2":"Our Services","services_title":"Our Services","services":[("💇","Hair Styling","Cuts, colors, and treatments by experts."),("💅","Nail Art","Manicure, pedicure, and nail artistry."),("🧖","Spa Treatments","Relaxing facials and body treatments."),("💄","Makeup","Bridal and occasion makeup by professionals.")],"stats":[("10K+","Clients"),("50+","Services"),("5★","Rating"),("8+","Years")],"testi":[("Sunita R.","Bride","Best bridal makeup I have ever seen."),("Kavita P.","Regular","Come every month. Always leave glowing."),("Meera S.","Client","The hair treatment transformed my confidence.")],"af":[("💎","Premium Products","Only top-tier professional products used."),("👩‍🎨","Expert Stylists","Internationally trained beauty professionals."),("🌿","Hygienic","Sterilized tools, fresh towels, every client.")]},
    "travel":        {"tagline":"Your World Awaits. Let Us Take You There.","sub":"Curated travel experiences, personalised itineraries, and memories that last a lifetime.","cta1":"Plan My Trip","cta2":"View Packages","services_title":"Our Services","services":[("✈️","International Tours","Handcrafted itineraries worldwide."),("🏔️","Adventure Travel","Treks, safaris, and extreme experiences."),("🏖️","Beach Holidays","Perfect resort stays and island getaways."),("💑","Honeymoon","Romantic escapes tailored for couples.")],"stats":[("5K+","Happy Travellers"),("100+","Destinations"),("15+","Years"),("4.9★","Rating")],"testi":[("Rahul K.","Traveller","The Bali trip was flawlessly organised. Dream experience."),("Priya S.","Couple","Our honeymoon was beyond anything we imagined."),("Amit R.","Family","The Rajasthan tour was magical for our whole family.")],"af":[("🗺️","Expert Guides","Local experts in every destination."),("💰","Best Value","Unbeatable packages for unforgettable experiences."),("📞","24/7 Support","We are with you every step of your journey.")]},
    "tech_company":  {"tagline":"Technology That Transforms Business","sub":"End-to-end technology solutions that drive digital transformation and accelerate growth.","cta1":"Get a Quote","cta2":"Our Work","services_title":"Our Services","services":[("💻","Software Development","Custom software built for your exact needs."),("📱","App Development","iOS, Android, and cross-platform mobile apps."),("☁️","Cloud Solutions","Migration, architecture, and managed cloud services."),("🔒","Cybersecurity","Protecting your business from evolving threats.")],"stats":[("500+","Projects"),("200+","Clients"),("15+","Years"),("4.9★","Rating")],"testi":[("Vikram S.","CTO","Delivered our platform on time and under budget."),("Anita R.","CEO","The app they built drives 60% of our revenue."),("Rahul P.","Founder","Best tech partner we have ever worked with.")],"af":[("⚡","Agile Delivery","Fast, iterative development with regular releases."),("🔒","Secure by Design","Security built in at every layer."),("🤝","Long-term Partner","We stay invested in your success always.")]},
    "event":         {"tagline":"Creating Unforgettable Experiences","sub":"Every event tells a story. We make sure yours is one people never stop talking about.","cta1":"Plan Your Event","cta2":"Our Events","services_title":"Our Services","services":[("💒","Weddings","Dream weddings executed to absolute perfection."),("🏢","Corporate Events","Conferences, team outings, product launches."),("🎂","Private Parties","Birthday, anniversary, and milestone celebrations."),("🎪","Exhibitions","Trade shows and public exhibitions organised.")],"stats":[("1K+","Events"),("50K+","Guests"),("10+","Years"),("5★","Rating")],"testi":[("Priya V.","Bride","Our wedding was exactly as I dreamed. Perfect."),("TechCorp","Client","Our annual conference was flawlessly managed."),("Rahul F.","Client","Dad's 60th was the most memorable party ever.")],"af":[("🎯","Detail-Obsessed","Every element planned to absolute perfection."),("⚡","Full Service","From concept to execution, we handle everything."),("💡","Creative Vision","Unique themes and concepts for every event.")]},
    "consulting":    {"tagline":"Strategy That Drives Results","sub":"Management consulting that transforms organisations, accelerates growth, and delivers measurable impact.","cta1":"Book Consultation","cta2":"Our Work","services_title":"Our Services","services":[("📊","Strategy Consulting","Clear roadmaps for sustainable competitive advantage."),("🔄","Operations","Process optimisation and efficiency transformation."),("👥","HR Consulting","Building high-performance teams and cultures."),("📈","Growth Advisory","Revenue acceleration and market expansion.")],"stats":[("200+","Clients"),("₹100Cr+","Value Delivered"),("15+","Years"),("4.9★","Rating")],"testi":[("Vikram M.","CEO","Their strategy doubled our revenue in 18 months."),("Anita S.","MD","Operations overhaul saved us ₹2Cr annually."),("Rahul T.","Founder","The best business decision I ever made.")],"af":[("🎯","Outcome-Focused","Every engagement measured against clear results."),("📊","Data-Driven","Insights backed by rigorous research and analysis."),("🤝","Embedded Partners","We work inside your team, not alongside it.")]},
    "fashion":       {"tagline":"Wear Your Story","sub":"Distinctive fashion that speaks before you do. Crafted with intention, worn with confidence.","cta1":"Shop Collection","cta2":"View Lookbook","services_title":"Our Collections","services":[("👗","Women's Wear","Contemporary designs for the modern woman."),("👔","Men's Wear","Sharp, sophisticated pieces for every occasion."),("👜","Accessories","The perfect finishing touch for every look."),("✂️","Custom Design","Bespoke pieces tailored exactly to you.")],"stats":[("10K+","Customers"),("500+","Pieces"),("5★","Rating"),("5+","Years")],"testi":[("Sneha P.","Influencer","The quality and design are absolutely unmatched."),("Kavita R.","Stylist","My clients always ask about pieces from this brand."),("Meera S.","Customer","I have never received so many compliments.")],"af":[("🌿","Sustainable","Ethically sourced, sustainably produced always."),("✂️","Bespoke","Custom tailoring available for every piece."),("💎","Premium Quality","Fabrics and craftsmanship that last forever.")]},
    "interior":      {"tagline":"Transform Your Space. Elevate Your Life.","sub":"Thoughtful interior design that turns any space into a place you truly love to be.","cta1":"Get a Consultation","cta2":"View Projects","services_title":"Our Services","services":[("🏠","Residential Design","Homes that reflect your personality perfectly."),("🏢","Commercial Spaces","Offices and retail that inspire productivity."),("🛋️","Furniture Design","Custom furniture designed and built for you."),("🏗️","Project Management","Complete turnkey interior delivery.")],"stats":[("300+","Projects"),("₹50Cr+","Work Done"),("10+","Years"),("5★","Rating")],"testi":[("Rahul K.","Home Owner","Transformed my apartment beyond imagination."),("TechCorp","Client","Our new office increased team productivity 40%."),("Priya M.","Home Owner","The design perfectly captures our family's soul.")],"af":[("🎨","Creative Vision","Unique concepts tailored to every client."),("⏰","On Schedule","Every project delivered on time without fail."),("💎","Premium Materials","Only the finest materials for lasting beauty.")]},
    "bakery":        {"tagline":"Baked With Love. Tasted With Joy.","sub":"Artisan baked goods made fresh daily. From morning pastries to celebration cakes.","cta1":"Order Now","cta2":"View Menu","services_title":"Our Specialties","services":[("🎂","Custom Cakes","Celebration and wedding cakes designed for you."),("🥐","Pastries","Fresh croissants, danish, and artisan pastries."),("🍞","Artisan Bread","Sourdough, focaccia, whole grain breads."),("🍪","Cookies and Sweets","Handcrafted cookies, macarons, and confections.")],"stats":[("5K+","Happy Customers"),("50+","Products"),("5★","Rating"),("8+","Years")],"testi":[("Priya S.","Bride","Our wedding cake was the centrepiece of the day."),("Rahul K.","Regular","Best sourdough I have ever had. Come every week."),("Anita V.","Customer","The custom birthday cake made my son's day perfect.")],"af":[("🌾","Fresh Daily","Everything baked fresh every single morning."),("🥚","Natural Ingredients","No preservatives, no artificial additives ever."),("❤️","Made With Love","Every item crafted with genuine care and passion.")]},
    "coffee":        {"tagline":"Your Perfect Cup Awaits","sub":"Specialty coffee sourced from the world's finest farms. Brewed with precision, served with passion.","cta1":"Visit Us","cta2":"Order Online","services_title":"What We Offer","services":[("☕","Specialty Coffee","Single origin and blends from world's best farms."),("🍵","Tea Selection","Premium loose leaf teas curated globally."),("🥪","Food Menu","Fresh snacks and meals to complement your coffee."),("📦","Subscriptions","Monthly coffee subscriptions delivered fresh.")],"stats":[("10K+","Cups Served"),("20+","Origins"),("5★","Rating"),("5+","Years")],"testi":[("Vikram P.","Regular","Best flat white I have had outside of Melbourne."),("Sunita R.","Remote Worker","My permanent office. Perfect coffee, perfect vibe."),("Rahul M.","Coffee Lover","Their single origin Ethiopian is a revelation.")],"af":[("🌍","Direct Trade","We buy direct from farmers, fairly priced."),("🔬","Precision Brewing","Every cup dialled in to perfect extraction."),("🌿","Sustainable","Compostable cups, ethical sourcing always.")]},
    "yoga":          {"tagline":"Find Your Inner Peace. Transform Your Life.","sub":"A sanctuary for the mind, body, and soul. All levels welcome. Transform from the inside out.","cta1":"Book a Class","cta2":"View Schedule","services_title":"Our Classes","services":[("🧘","Yoga Classes","Hatha, vinyasa, restorative, yin, and more."),("🧠","Meditation","Guided meditation for clarity and calm."),("💨","Breathwork","Pranayama and breathing techniques."),("🌿","Wellness Retreats","Weekend and week-long transformational retreats.")],"stats":[("2K+","Students"),("20+","Classes/Week"),("10+","Instructors"),("5★","Rating")],"testi":[("Priya S.","Student","My anxiety is completely transformed. Grateful."),("Rahul K.","Meditator","The meditation practice changed my leadership."),("Anita V.","Retreater","The retreat was the most profound experience of my life.")],"af":[("🏆","Certified","Internationally certified instructors."),("🌿","Holistic","Mind, body, and spirit treated as one."),("❤️","Inclusive","All bodies, all levels, always welcome here.")]},
    "pet":           {"tagline":"Because They Deserve the Best","sub":"Premium pet care, grooming, and products for your furry family members. They are family.","cta1":"Book Service","cta2":"Shop Now","services_title":"Our Services","services":[("✂️","Pet Grooming","Bathing, trimming, and styling for all breeds."),("🏥","Veterinary Care","Health checkups, vaccinations, and treatment."),("🛏️","Pet Boarding","Safe, loving home away from home for pets."),("🦮","Dog Training","Positive reinforcement obedience training.")],"stats":[("5K+","Happy Pets"),("50+","Services"),("10+","Years"),("5★","Rating")],"testi":[("Rahul K.","Dog Owner","My lab looks and smells amazing after every groom."),("Priya S.","Cat Owner","The vet here is patient, thorough, and so kind."),("Amit M.","Pet Parent","Boarding here gives total peace of mind when travelling.")],"af":[("❤️","Animal Lovers","Every team member is a passionate pet lover."),("🔬","Expert Care","Qualified vets and certified groomers only."),("🏠","Safe Environment","Clean, safe, and loving care always.")]},
    "book":          {"tagline":"Every Book Is a New World","sub":"Curated books for curious minds. Rare finds, bestsellers, and literary gems all in one place.","cta1":"Browse Books","cta2":"Visit Us","services_title":"What We Offer","services":[("📚","Fiction and Literature","Contemporary and classic fiction from worldwide."),("📖","Non-Fiction","Business, self-help, history, science, and more."),("👶","Children's Books","Inspiring books for young readers of all ages."),("☕","Reading Cafe","Browse books with a perfect cup of coffee.")],"stats":[("10K+","Titles"),("5K+","Members"),("15+","Years"),("5★","Rating")],"testi":[("Priya M.","Book Lover","Found books here I could not find anywhere else."),("Rahul T.","Author","The best independent bookstore I have ever visited."),("Anita S.","Parent","My children's love of reading started here.")],"af":[("📚","Curated Selection","Every book personally selected by our team."),("🤝","Community","Monthly book clubs and author events."),("🌍","Global Titles","Books from publishers worldwide, rare and new.")]},
    "gaming":        {"tagline":"Level Up Your Game","sub":"The ultimate gaming community. Tournaments, coaching, gear, and a tribe of passionate players.","cta1":"Join Now","cta2":"View Games","services_title":"What We Offer","services":[("🎮","Gaming Tournaments","Competitive esports events with real prizes."),("🏆","Pro Coaching","Learn from professional esports players."),("🖥️","Gaming Cafe","Premium rigs, low latency, perfect setups."),("🎯","Game Reviews","Expert reviews and gaming content.")],"stats":[("10K+","Players"),("100+","Tournaments"),("5+","Years"),("4.9★","Rating")],"testi":[("Arjun P.","Pro Gamer","The coaching here took me to national level."),("Vikram S.","Casual Gamer","Best gaming cafe setup I have ever played on."),("Rahul K.","Parent","My son's confidence transformed through gaming here.")],"af":[("🏆","Pro Community","Connect with professional and aspiring players."),("🖥️","Premium Rigs","High-end gaming setups with zero lag."),("🎯","Expert Coaching","Certified coaches from professional esports.")]},
    "crypto":        {"tagline":"The Future of Finance Is Here","sub":"Your trusted gateway to Web3, DeFi, and digital assets. Secure, simple, and powerful.","cta1":"Get Started","cta2":"Learn More","services_title":"Our Platform","services":[("₿","Crypto Exchange","Trade 500+ cryptocurrencies securely."),("🏦","DeFi Protocols","Earn yield through decentralised finance."),("🖼️","NFT Marketplace","Discover, create, and trade digital art."),("🔐","Secure Wallet","Military-grade security for your assets.")],"stats":[("100K+","Users"),("$1B+","Volume"),("500+","Tokens"),("4.8★","Rating")],"testi":[("Rahul K.","Investor","Clearest and safest crypto platform in India."),("Priya S.","Trader","The interface makes complex trading effortless."),("Amit M.","NFT Creator","Sold my first NFT collection here. Life-changing.")],"af":[("🔐","Bank-Grade Security","Military encryption for every transaction."),("⚡","Instant Settlement","Trades settled in seconds, not days."),("📊","Advanced Analytics","Professional tools for serious investors.")]},
    "wedding":       {"tagline":"Your Perfect Day. Our Greatest Joy.","sub":"Creating wedding experiences so perfect they feel like dreams you never want to wake from.","cta1":"Plan Your Wedding","cta2":"View Gallery","services_title":"Our Services","services":[("💒","Full Planning","Complete wedding management from concept to day."),("📸","Photography","Cinematic wedding photography and videography."),("🌸","Decor and Florals","Breathtaking decorations and floral design."),("🍽️","Catering","Exquisite menus for every cuisine and taste.")],"stats":[("500+","Weddings"),("50K+","Happy Guests"),("10+","Years"),("5★","Rating")],"testi":[("Priya and Rahul","Couple","Our wedding was beyond any dream we had."),("Sunita P.","Bride's Mother","Every detail was handled with such love and care."),("Amit V.","Groom","Best decision we made was hiring this team.")],"af":[("💎","Luxury Execution","Every element crafted to absolute perfection."),("🤝","Personal Touch","Your wedding planner is dedicated solely to you."),("📞","Always On Call","Available 24/7 throughout your planning journey.")]},
    "children":      {"tagline":"Where Every Child Shines","sub":"Nurturing environments where children discover, learn, play, and grow into their best selves.","cta1":"Enroll Now","cta2":"Visit Us","services_title":"Our Programs","services":[("📚","Early Education","Holistic learning for children aged 2 to 6."),("🎨","Creative Arts","Painting, craft, music, and drama programs."),("⚽","Sports and Play","Physical development through structured play."),("🧑‍💻","STEM Programs","Science, tech, engineering, math for kids.")],"stats":[("500+","Children"),("50+","Programs"),("10+","Years"),("5★","Rating")],"testi":[("Priya S.","Parent","My son has flourished academically and socially."),("Rahul K.","Father","The teachers genuinely care about every child."),("Anita M.","Mother","The best investment we made for our daughter.")],"af":[("❤️","Child-First","Every decision made in the best interest of children."),("👩‍🏫","Expert Teachers","Qualified educators with child psychology training."),("🔒","Safe Environment","CCTV, secure premises, strict safety protocols.")]},
    "dental":        {"tagline":"Your Smile. Our Expertise.","sub":"Advanced dental care in a comfortable, anxiety-free environment. Your perfect smile awaits.","cta1":"Book Appointment","cta2":"Our Treatments","services_title":"Our Treatments","services":[("🦷","General Dentistry","Checkups, cleaning, and preventive care."),("😁","Cosmetic Dentistry","Whitening, veneers, and smile makeovers."),("🦾","Implants","Permanent tooth replacement solutions."),("😬","Orthodontics","Braces and Invisalign for perfect alignment.")],"stats":[("10K+","Patients"),("20+","Services"),("15+","Years"),("5★","Rating")],"testi":[("Rahul K.","Patient","My smile transformation was absolutely incredible."),("Priya S.","Patient","The most pain-free dental experience I have had."),("Amit M.","Parent","My children actually look forward to visits here.")],"af":[("🔬","Advanced Tech","Latest dental technology for precise treatment."),("💊","Pain-Free","Anxiety-free care with modern pain management."),("😁","Smile Guarantee","We guarantee results or we make it right.")]},
    "cleaning":      {"tagline":"Spotless Spaces. Happy Places.","sub":"Professional cleaning services that transform your home or office into a pristine sanctuary.","cta1":"Book a Clean","cta2":"Our Services","services_title":"Our Services","services":[("🏠","Home Cleaning","Deep and regular cleaning for residences."),("🏢","Office Cleaning","Professional commercial cleaning services."),("🧹","Deep Clean","Intensive cleaning for move-in and move-out."),("🌿","Eco Cleaning","Green cleaning with non-toxic products.")],"stats":[("5K+","Clients"),("50K+","Cleans Done"),("8+","Years"),("5★","Rating")],"testi":[("Priya S.","Home Owner","My home has never been so clean. Exceptional."),("TechCorp","Manager","Our office is always spotless. The team is reliable."),("Rahul K.","Landlord","Move-out cleans are perfect every time.")],"af":[("✅","Verified Staff","All staff background-checked and insured."),("🌿","Eco-Friendly","Non-toxic, safe products for your family."),("⏰","Reliable","Always on time, always thorough, always.")]},
    "solar":         {"tagline":"Harness the Power of the Sun","sub":"Clean, renewable solar energy solutions that reduce your bills and help save the planet.","cta1":"Get Free Quote","cta2":"Our Solutions","services_title":"Our Solutions","services":[("☀️","Solar Installation","Residential and commercial solar panel systems."),("🔋","Battery Storage","Store energy and use it when you need it."),("📊","Energy Audit","Free analysis of your energy consumption."),("🔧","Maintenance","Regular servicing to maximise efficiency.")],"stats":[("2K+","Installations"),("500MW+","Installed"),("10+","Years"),("4.9★","Rating")],"testi":[("Rahul K.","Home Owner","My electricity bill dropped 80%. Incredible ROI."),("Vikram S.","Factory Owner","Best investment for our manufacturing plant."),("Priya M.","School Principal","Our school is fully energy independent now.")],"af":[("💰","Save 80%","Average 80% reduction in electricity bills."),("🌍","Planet-Positive","Every installation reduces carbon footprint."),("⚡","25-Year Warranty","Panels guaranteed for 25 years performance.")]},
    "automobile_service": {"tagline":"Your Car Deserves the Best Care","sub":"Expert automotive service you can trust. From oil changes to complete rebuilds, done right every time.","cta1":"Book Service","cta2":"Our Services","services_title":"Our Services","services":[("🔧","Servicing","Complete vehicle servicing and maintenance."),("🚘","Repairs","Expert diagnosis and repair of all issues."),("🎨","Detailing","Professional detailing inside and out."),("🔋","Electrical","Advanced diagnostics and electrical repair.")],"stats":[("10K+","Cars Serviced"),("20+","Technicians"),("15+","Years"),("4.9★","Rating")],"testi":[("Rahul K.","Driver","Never going to another workshop. These guys are the best."),("Priya S.","Owner","My car runs better than when I bought it. Amazing."),("Amit M.","Fleet Owner","All 20 of our company vehicles serviced here.")],"af":[("🔧","Expert Technicians","Manufacturer-trained mechanics for all brands."),("⚡","Fast Turnaround","Most services completed same day."),("✅","Guaranteed Work","All work backed by our quality guarantee.")]},
    "logistics":     {"tagline":"Delivering Reliability, Every Mile","sub":"End-to-end logistics solutions that keep your supply chain moving efficiently and on time.","cta1":"Get a Quote","cta2":"Our Services","services_title":"Our Services","services":[("🚚","Last Mile Delivery","Fast and reliable delivery to your customers."),("🏭","Warehousing","Secure storage and inventory management."),("✈️","Air Freight","Time-sensitive international cargo solutions."),("🚢","Sea Freight","Cost-effective bulk shipping worldwide.")],"stats":[("10K+","Deliveries/Day"),("50+","Cities"),("15+","Years"),("4.9★","Rating")],"testi":[("Vikram S.","E-commerce","Their delivery reliability transformed our customer ratings."),("Anita R.","Manufacturer","Supply chain has never run this smoothly."),("Rahul M.","Importer","Sea freight rates and reliability are unmatched.")],"af":[("⏰","On-Time","99.8% on-time delivery rate across all routes."),("📍","Real-Time","Live tracking for every shipment always."),("🔐","Insured","Full insurance coverage on every consignment.")]},
    "agriculture":   {"tagline":"Nourishing the Nation from Seed to Table","sub":"Modern agricultural solutions that help farmers grow more, earn more, and sustain our planet.","cta1":"Get Started","cta2":"Our Products","services_title":"Our Services","services":[("🌾","Premium Seeds","High-yield, disease-resistant crop varieties."),("🌱","Organic Inputs","Natural fertilisers and pest management."),("📱","AgriTech Platform","Digital tools for precision farming."),("🚚","Market Linkage","Direct connection to buyers for better prices.")],"stats":[("10K+","Farmers"),("5+","States"),("10+","Years"),("4.9★","Rating")],"testi":[("Ravi P.","Farmer","My wheat yield increased 40% using their seeds."),("Suresh K.","Cooperative","The platform helps us get fair market prices."),("Anita M.","Organic Farmer","Their natural inputs transformed my soil health.")],"af":[("🔬","Science-Backed","Agronomists supporting every farmer."),("💰","Better Prices","Direct market linkage for maximum income."),("🌍","Sustainable","Practices that protect soil for future generations.")]},
    "security":      {"tagline":"Protect What Matters Most","sub":"Comprehensive security solutions for homes, businesses, and institutions. Your safety is our mission.","cta1":"Get Assessment","cta2":"Our Solutions","services_title":"Our Solutions","services":[("📷","CCTV Systems","HD surveillance systems for 24/7 monitoring."),("👮","Manned Guards","Trained security personnel for your premises."),("🔐","Access Control","Smart access management systems."),("🔥","Fire Safety","Detection, suppression, and evacuation systems.")],"stats":[("1K+","Clients"),("5K+","Guards"),("15+","Years"),("4.9★","Rating")],"testi":[("Vikram S.","Mall Owner","Their security system paid for itself in month one."),("Anita R.","School Principal","Our parents have complete peace of mind now."),("Rahul K.","Factory Owner","Zero security incidents since partnering with them.")],"af":[("🛡️","24/7 Response","Round-the-clock monitoring and rapid response."),("👮","Trained Guards","All personnel certified and background-verified."),("🔬","Latest Tech","Cutting-edge security technology deployed.")]},
    "mental_health": {"tagline":"Your Mental Health Matters","sub":"Compassionate, confidential therapy and counselling. You deserve support, and help is here.","cta1":"Book Session","cta2":"Meet Our Team","services_title":"Our Services","services":[("🧠","Individual Therapy","One-on-one sessions with qualified therapists."),("👫","Couples Counselling","Strengthen your relationship with expert guidance."),("👨‍👩‍👧","Family Therapy","Healing and communication for families."),("📱","Online Sessions","Convenient therapy from the comfort of home.")],"stats":[("5K+","Clients Helped"),("20+","Therapists"),("10+","Years"),("5★","Rating")],"testi":[("Priya S.","Client","My anxiety is manageable for the first time in years."),("Rahul K.","Couple","Our marriage is stronger than ever after counselling."),("Anita M.","Client","The online sessions fit perfectly into my busy life.")],"af":[("🔐","Confidential","Absolute privacy and confidentiality guaranteed."),("❤️","Non-Judgmental","A safe space to be completely yourself."),("👩‍⚕️","Qualified","All therapists hold international credentials.")]},
    "business":      {"tagline":"Excellence Delivered Every Single Time","sub":"Deep expertise, bold execution, and an obsession with results. We help businesses grow and win.","cta1":"Get Started","cta2":"Learn More","services_title":"What We Offer","services":[("⚡","Fast Results","Exceptional outcomes ahead of schedule."),("🎯","Results-Obsessed","Every action tied to your measurable goals."),("🤝","True Partnership","We are invested in your success as deeply as you are."),("🛡️","Reliable","100+ clients trust us with critical work.")],"stats":[("100+","Projects"),("50+","Clients"),("4.9★","Rating"),("5+","Years")],"testi":[("Rohit K.","MD","Delivered as promised, ahead of schedule."),("Nisha A.","COO","Best vendor relationship we have ever had."),("Amit S.","Founder","A game-changer for our business growth.")],"af":[("⚡","Fast Delivery","Results delivered faster than any competitor."),("🎯","ROI-Focused","Every engagement measured against business impact."),("🛡️","Proven Track Record","5+ years, 100+ clients, zero failures.")]},
}

def get_content_for_category(cat: str) -> dict:
    """Get content, falling back to business if category not in CONTENT."""
    return CONTENT.get(cat, CONTENT.get("business"))

def build_template(prompt: str) -> str:
    name = extract_name(prompt)
    cat = get_category(prompt)
    ds = get_design(prompt)
    con = get_content_for_category(cat)
    seed = abs(hash(prompt)) % 99999
    enc = urllib.parse.quote(prompt[:80])
    is_dark = ds["dark"]
    font = ds["font"]

    imgs = {
        "hero":  f"https://image.pollinations.ai/prompt/ultra_realistic_cinematic_{enc}_dramatic_4k_professional?width=1400&height=800&seed={seed}&nologo=true&model=flux",
        "about": f"https://image.pollinations.ai/prompt/professional_premium_{enc}_team_modern_office?width=900&height=700&seed={seed+1}&nologo=true&model=flux",
        "g1":    f"https://image.pollinations.ai/prompt/{enc}_premium_showcase_professional_1?width=700&height=500&seed={seed+2}&nologo=true&model=flux",
        "g2":    f"https://image.pollinations.ai/prompt/{enc}_premium_showcase_professional_2?width=700&height=500&seed={seed+3}&nologo=true&model=flux",
        "g3":    f"https://image.pollinations.ai/prompt/{enc}_premium_showcase_professional_3?width=700&height=500&seed={seed+4}&nologo=true&model=flux",
        "g4":    f"https://image.pollinations.ai/prompt/{enc}_premium_showcase_professional_4?width=700&height=500&seed={seed+5}&nologo=true&model=flux",
    }

    svcs_html = "".join([f\'<div class="sc"><div class="si">{ic}</div><h3>{t}</h3><p>{d}</p></div>\' for ic,t,d in con["services"]])
    stats_html = "".join([f\'<div class="stat"><div class="sn">{n}</div><div class="sl">{l}</div></div>\' for n,l in con["stats"]])
    testi_html = "".join([f\'<div class="tc"><div class="ts">★★★★★</div><p class="tt">"{t}"</p><div class="ta"><div class="av">{a[0]}</div><div><div class="an">{a}</div><div class="ar">{r}</div></div></div></div>\' for a,r,t in con["testi"]])
    gal_html = "".join([f\'<div class="gi"><img src="{imgs[k]}" loading="lazy" alt=""/></div>\' for k in ["g1","g2","g3","g4"]])
    af_html = "".join([f\'<div class="af"><div class="afi">{ic}</div><div class="aft"><h4>{t}</h4><p>{d}</p></div></div>\' for ic,t,d in con["af"]])

    nav_logo_color = "#fff" if is_dark else ds["pr"]
    nav_link_color = "rgba(255,255,255,0.8)" if is_dark else ds["mu"]
    nav_hb_color = "#fff" if is_dark else ds["tx"]
    hero_img_opacity = "0.12" if is_dark else "0.07"
    hero_overlay = f"linear-gradient(135deg,{ds['bg']}F5 0%,{ds['bg']}CC 60%,{ds['pr']}22 100%)"
    card_shadow = "0 40px 80px rgba(0,0,0,0.5)" if is_dark else "0 40px 80px rgba(0,0,0,0.12)"
    hover_shadow = "0 20px 60px rgba(0,0,0,0.3)" if is_dark else "0 20px 60px rgba(0,0,0,0.1)"
    stat_bg = "rgba(0,0,0,0.4)" if is_dark else ds["ca"]
    services_bg = "rgba(255,255,255,0.03)" if is_dark else ds["ca"]

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{name} — {con["tagline"]}</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=Playfair+Display:ital,wght@0,700;0,800;0,900;1,700&display=swap" rel="stylesheet">
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
:root{{
  --bg:{ds["bg"]};--pr:{ds["pr"]};--ac:{ds["ac"]};--tx:{ds["tx"]};
  --mu:{ds["mu"]};--ca:{ds["ca"]};--br:{ds["br"]};--nb:{ds["nb"]};--nt:{ds["nt"]};
}}
html{{scroll-behavior:smooth}}
body{{font-family:"Inter",sans-serif;background:var(--bg);color:var(--tx);overflow-x:hidden;line-height:1.6}}
nav{{position:fixed;top:0;width:100%;z-index:1000;transition:all 0.4s;padding:0 5%}}
nav.sc{{background:var(--nb);backdrop-filter:blur(24px);border-bottom:1px solid var(--br);box-shadow:0 4px 30px rgba(0,0,0,0.1)}}
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
.hbg{{position:absolute;inset:0;background:url("{imgs["hero"]}") center/cover no-repeat;opacity:{hero_img_opacity};filter:blur(2px);transform:scale(1.05)}}
.hov{{position:absolute;inset:0;background:{hero_overlay}}}
.hsh{{position:absolute;inset:0;overflow:hidden;pointer-events:none}}
.hsh::before{{content:"";position:absolute;top:-30%;right:-10%;width:600px;height:600px;border-radius:50%;background:radial-gradient(circle,{ds["pr"]}{"18" if is_dark else "0D"} 0%,transparent 70%)}}
.hsh::after{{content:"";position:absolute;bottom:-20%;left:-5%;width:400px;height:400px;border-radius:50%;background:radial-gradient(circle,{ds["ac"]}{"12" if is_dark else "0A"} 0%,transparent 70%)}}
.hi{{position:relative;z-index:2;max-width:1280px;margin:0 auto;width:100%;display:grid;grid-template-columns:1fr 1fr;gap:80px;align-items:center}}
.hbadge{{display:inline-flex;align-items:center;gap:8px;background:{"rgba(255,255,255,0.1)" if is_dark else ds["ca"]};backdrop-filter:blur(10px);border:1px solid var(--br);color:var(--tx);padding:9px 20px;border-radius:100px;font-size:0.75rem;font-weight:700;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:24px}}
.bdot{{width:8px;height:8px;border-radius:50%;background:var(--ac);animation:pulse 2s infinite;box-shadow:0 0 10px var(--ac)}}
@keyframes pulse{{0%,100%{{opacity:1;transform:scale(1)}}50%{{opacity:0.6;transform:scale(1.4)}}}}
.ht{{font-family:"{font}",serif;font-size:clamp(2.8rem,4.5vw,4.5rem);font-weight:900;line-height:1.05;letter-spacing:-2px;margin-bottom:16px;color:var(--tx)}}
.hta{{color:var(--pr);display:block;font-style:italic}}
.hs{{font-size:1.05rem;color:var(--mu);line-height:1.75;margin-bottom:36px;max-width:480px}}
.hbtns{{display:flex;gap:14px;flex-wrap:wrap}}
.bp{{display:inline-flex;align-items:center;gap:8px;background:var(--pr);color:#fff;font-weight:800;font-size:0.9rem;padding:16px 32px;border-radius:100px;text-decoration:none;transition:all 0.3s;box-shadow:0 8px 30px rgba(0,0,0,0.2)}}
.bp:hover{{transform:translateY(-3px);filter:brightness(1.1);box-shadow:0 16px 40px rgba(0,0,0,0.3)}}
.bs{{display:inline-flex;align-items:center;gap:8px;background:var(--ca);color:var(--tx);font-weight:700;font-size:0.9rem;padding:16px 32px;border-radius:100px;text-decoration:none;border:1px solid var(--br);transition:all 0.3s}}
.bs:hover{{transform:translateY(-3px);filter:brightness(1.05)}}
.hiw{{position:relative;perspective:1200px}}
.hic{{border-radius:24px;overflow:hidden;box-shadow:{card_shadow},0 0 0 1px var(--br);transform:rotateY(-6deg) rotateX(3deg);transition:transform 0.6s ease}}
.hic:hover{{transform:rotateY(0deg) rotateX(0deg)}}
.hic img{{width:100%;height:420px;object-fit:cover;display:block}}
.hib{{position:absolute;bottom:20px;left:20px;background:rgba(0,0,0,0.75);backdrop-filter:blur(20px);border:1px solid rgba(255,255,255,0.15);padding:12px 18px;border-radius:14px;display:flex;align-items:center;gap:10px}}
.ld{{width:8px;height:8px;border-radius:50%;background:#22C55E;box-shadow:0 0 12px #22C55E;animation:pulse 2s infinite}}
.lt{{color:#fff;font-size:0.78rem;font-weight:600}}
.stbar{{background:{stat_bg};border-top:1px solid var(--br);border-bottom:1px solid var(--br);padding:0 5%}}
.sti{{max-width:1280px;margin:0 auto;display:grid;grid-template-columns:repeat(4,1fr)}}
.stat{{padding:32px 24px;text-align:center;border-right:1px solid var(--br);transition:background 0.3s}}
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
.af:hover{{border-color:var(--pr);transform:translateX(4px);box-shadow:0 8px 24px rgba(0,0,0,0.08)}}
.afi{{width:42px;height:42px;border-radius:12px;background:var(--bg);border:1px solid var(--br);display:flex;align-items:center;justify-content:center;font-size:1.3rem;flex-shrink:0}}
.aft h4{{font-weight:700;font-size:0.88rem;color:var(--tx);margin-bottom:3px}}
.aft p{{font-size:0.8rem;color:var(--mu)}}
.services{{padding:120px 5%;background:{services_bg}}}
.svi{{max-width:1280px;margin:0 auto}}
.sh2{{text-align:center;margin-bottom:60px}}
.sg{{display:grid;grid-template-columns:repeat(2,1fr);gap:20px}}
.sc{{background:var(--bg);border:1px solid var(--br);border-radius:24px;padding:36px;transition:all 0.4s;position:relative;overflow:hidden}}
.sc::before{{content:"";position:absolute;inset:0;background:linear-gradient(135deg,var(--pr) 0%,transparent 60%);opacity:0;transition:opacity 0.4s}}
.sc:hover{{border-color:var(--pr);transform:translateY(-6px);box-shadow:{hover_shadow}}}
.sc:hover::before{{opacity:0.04}}
.si{{font-size:2.6rem;margin-bottom:20px;display:block}}
.sc h3{{font-family:"{font}",serif;font-size:1.25rem;font-weight:800;color:var(--tx);margin-bottom:12px}}
.sc p{{font-size:0.88rem;color:var(--mu);line-height:1.7}}
.gallery{{padding:80px 5%;background:var(--bg)}}
.gli{{max-width:1280px;margin:0 auto}}
.gg{{display:grid;grid-template-columns:repeat(2,1fr);gap:16px;margin-top:48px}}
.gi{{border-radius:20px;overflow:hidden;aspect-ratio:4/3;cursor:pointer;position:relative;box-shadow:0 8px 24px rgba(0,0,0,0.1)}}
.gi img{{width:100%;height:100%;object-fit:cover;display:block;transition:transform 0.6s}}
.gi:hover img{{transform:scale(1.08)}}
.gi::after{{content:"";position:absolute;inset:0;background:linear-gradient(to top,rgba(0,0,0,0.5),transparent);opacity:0;transition:opacity 0.3s}}
.gi:hover::after{{opacity:1}}
.testi{{padding:120px 5%;background:{services_bg}}}
.tti{{max-width:1280px;margin:0 auto}}
.tg{{display:grid;grid-template-columns:repeat(3,1fr);gap:20px;margin-top:48px}}
.tc{{background:var(--bg);border:1px solid var(--br);border-radius:24px;padding:32px;transition:all 0.3s;position:relative;overflow:hidden}}
.tc::before{{content:"\\201C";position:absolute;top:-20px;right:16px;font-size:8rem;color:var(--pr);opacity:0.06;font-family:serif;line-height:1}}
.tc:hover{{border-color:var(--pr);transform:translateY(-4px);box-shadow:{hover_shadow}}}
.ts{{color:var(--ac);font-size:1rem;letter-spacing:2px;margin-bottom:16px}}
.tt{{font-size:0.9rem;color:var(--mu);line-height:1.75;margin-bottom:24px;font-style:italic}}
.ta{{display:flex;align-items:center;gap:12px}}
.av{{width:44px;height:44px;border-radius:50%;background:linear-gradient(135deg,var(--pr),var(--ac));display:flex;align-items:center;justify-content:center;color:#fff;font-weight:800;font-size:0.9rem;flex-shrink:0}}
.an{{font-weight:700;font-size:0.85rem;color:var(--tx)}}
.ar{{font-size:0.72rem;color:var(--mu)}}
.cta{{padding:120px 5%;background:var(--bg)}}
.ctai{{max-width:1000px;margin:0 auto;border-radius:32px;padding:80px 60px;text-align:center;position:relative;overflow:hidden;background:linear-gradient(135deg,var(--pr) 0%,var(--ac) 100%);box-shadow:0 40px 80px rgba(0,0,0,0.25)}}
.ctai::before{{content:"";position:absolute;top:-50%;right:-10%;width:500px;height:500px;border-radius:50%;background:rgba(255,255,255,0.08);pointer-events:none}}
.ctai h2{{font-family:"{font}",serif;font-size:clamp(2rem,4vw,3rem);font-weight:900;color:#fff;margin-bottom:16px;position:relative;z-index:1;letter-spacing:-1px}}
.ctai p{{font-size:1rem;color:rgba(255,255,255,0.85);margin-bottom:40px;position:relative;z-index:1;max-width:500px;margin-left:auto;margin-right:auto}}
.cbtns{{display:flex;gap:14px;justify-content:center;flex-wrap:wrap;position:relative;z-index:1}}
.cb1{{display:inline-flex;align-items:center;gap:8px;background:#fff;color:var(--pr);font-weight:800;padding:16px 36px;border-radius:100px;text-decoration:none;font-size:0.9rem;transition:all 0.3s;box-shadow:0 8px 30px rgba(0,0,0,0.15)}}
.cb1:hover{{transform:translateY(-3px);box-shadow:0 16px 40px rgba(0,0,0,0.2)}}
.cb2{{display:inline-flex;align-items:center;gap:8px;background:rgba(255,255,255,0.15);color:#fff;font-weight:700;padding:16px 36px;border-radius:100px;text-decoration:none;font-size:0.9rem;border:1px solid rgba(255,255,255,0.3);transition:all 0.3s}}
.cb2:hover{{background:rgba(255,255,255,0.25);transform:translateY(-3px)}}
footer{{padding:60px 5% 30px;border-top:1px solid var(--br);background:{services_bg}}}
.fi{{max-width:1280px;margin:0 auto}}
.ft{{display:grid;grid-template-columns:2fr 1fr 1fr 1fr;gap:48px;margin-bottom:48px}}
.fb p{{font-size:0.82rem;color:var(--mu);margin-top:12px;line-height:1.7;max-width:240px}}
.flogo{{font-family:"{font}",serif;font-size:1.6rem;font-weight:900;color:var(--pr)}}
.fc h4{{font-weight:700;font-size:0.75rem;color:var(--mu);text-transform:uppercase;letter-spacing:1.5px;margin-bottom:16px}}
.fc a{{display:block;color:var(--mu);text-decoration:none;font-size:0.82rem;margin-bottom:10px;transition:color 0.2s}}
.fc a:hover{{color:var(--pr)}}
.fbot{{border-top:1px solid var(--br);padding-top:24px;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px}}
.fbot p{{font-size:0.75rem;color:var(--mu)}}
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
      <li><a href="#services">{con["services_title"]}</a></li>
      <li><a href="#gallery">Gallery</a></li>
      <li><a href="#contact" class="nc">{con["cta1"]}</a></li>
    </ul>
    <button class="nhb" id="hb"><span></span><span></span><span></span></button>
  </div>
</nav>
<div class="nmob" id="nmo">
  <a href="#about">About</a>
  <a href="#services">{con["services_title"]}</a>
  <a href="#gallery">Gallery</a>
  <a href="#contact" class="mc">{con["cta1"]}</a>
</div>
<section class="hero" id="home">
  <div class="hbg"></div><div class="hov"></div><div class="hsh"></div>
  <div class="hi">
    <div>
      <div class="hbadge"><span class="bdot"></span>✦ {name} · {cat.replace("_"," ").title()}</div>
      <h1 class="ht">{name}<span class="hta">{con["tagline"]}</span></h1>
      <p class="hs">{con["sub"]}</p>
      <div class="hbtns">
        <a href="#contact" class="bp">{con["cta1"]} →</a>
        <a href="#services" class="bs">▶ {con["cta2"]}</a>
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
      <p class="ss">{con["sub"]}</p>
      <div class="aff">{af_html}</div>
    </div>
  </div>
</section>
<section class="services" id="services">
  <div class="svi">
    <div class="sh2">
      <div class="sl2">✦ {con["services_title"]}</div>
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
      <div class="sl2">✦ Testimonials</div>
      <h2 class="sh" style="text-align:center">What Our <span>Clients Say</span></h2>
    </div>
    <div class="tg">{testi_html}</div>
  </div>
</section>
<section class="cta" id="contact">
  <div class="ctai">
    <h2>Ready to Get Started?</h2>
    <p>Join thousands who already trust {name}. Take the first step today.</p>
    <div class="cbtns">
      <a href="mailto:hello@{re.sub(r"[^a-z0-9]","",name.lower())}.com" class="cb1">{con["cta1"]} →</a>
      <a href="tel:+919999999999" class="cb2">📞 Contact Us</a>
    </div>
  </div>
</section>
<footer>
  <div class="fi">
    <div class="ft">
      <div class="fb">
        <div class="flogo">{name}</div>
        <p>{con["sub"][:100]}...</p>
      </div>
      <div class="fc">
        <h4>Company</h4>
        <a href="#about">About</a>
        <a href="#services">{con["services_title"]}</a>
        <a href="#gallery">Gallery</a>
        <a href="#contact">Contact</a>
      </div>
      <div class="fc">
        <h4>Services</h4>
        {"".join([f\'<a href="#services">{s[1]}</a>\' for s in con["services"]])}
      </div>
      <div class="fc">
        <h4>Connect</h4>
        <a href="#">Instagram</a>
        <a href="#">LinkedIn</a>
        <a href="#">Twitter</a>
        <a href="mailto:hello@{re.sub(r"[^a-z0-9]","",name.lower())}.com">Email</a>
      </div>
    </div>
    <div class="fbot">
      <p>© 2024 {name}. All rights reserved.</p>
      <p>Built with Dacexy AI</p>
    </div>
  </div>
</footer>
<script>
const nav=document.getElementById("nav");
window.addEventListener("scroll",()=>nav.classList.toggle("sc",scrollY>60));
const hb=document.getElementById("hb"),nmo=document.getElementById("nmo");
hb.addEventListener("click",()=>nmo.classList.toggle("open"));
nmo.querySelectorAll("a").forEach(a=>a.addEventListener("click",()=>nmo.classList.remove("open")));
const obs=new IntersectionObserver(entries=>entries.forEach(e=>{{
  if(e.isIntersecting){{e.target.style.opacity="1";e.target.style.transform="translateY(0) scale(1)"}}
}}),{{threshold:0.1}});
document.querySelectorAll(".sc,.tc,.af,.gi,.stat").forEach(el=>{{
  el.style.opacity="0";
  el.style.transform="translateY(40px) scale(0.97)";
  el.style.transition="opacity 0.7s ease,transform 0.7s ease";
  obs.observe(el);
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
