from __future__ import annotations
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import make_asgi_app

from src.shared.config.settings import settings

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL, logging.INFO),
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)
log = logging.getLogger("app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("Dacexy %s starting — env=%s", settings.APP_VERSION, settings.ENVIRONMENT)
    if settings.SENTRY_DSN:
        try:
            import sentry_sdk
            sentry_sdk.init(dsn=settings.SENTRY_DSN, environment=settings.ENVIRONMENT)
            log.info("Sentry configured")
        except Exception:
            pass
    # Test Redis connection
    try:
        from src.interfaces.http.dependencies.container import get_redis
        redis = get_redis()
        ok = await redis.ping()
        log.info("Redis: %s", "connected" if ok else "not configured")
    except Exception as e:
        log.warning("Redis ping failed: %s", e)
    log.info("Startup complete — API ready at %s", settings.API_PREFIX)
    yield
    try:
        from src.interfaces.http.dependencies.container import get_deepseek
        await get_deepseek().aclose()
    except Exception:
        pass
    log.info("Shutdown complete")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Dacexy Enterprise AI Platform API",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── Middleware ────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)

from src.interfaces.http.middleware.rate_limit import RateLimitMiddleware
app.add_middleware(RateLimitMiddleware)

# ── Prometheus ────────────────────────────────────────────────
if settings.PROMETHEUS_ENABLED:
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)

# ── Routes ────────────────────────────────────────────────────
from src.interfaces.http.routes import (
    auth, ai_chat, orgs, billing, agent,
    media, websites, voice, audit, referral, admin, memory
)

app.include_router(auth.router,     prefix=settings.API_PREFIX)
app.include_router(ai_chat.router,  prefix=settings.API_PREFIX)
app.include_router(orgs.router,     prefix=settings.API_PREFIX)
app.include_router(billing.router,  prefix=settings.API_PREFIX)
app.include_router(agent.router,    prefix=settings.API_PREFIX)
app.include_router(media.router,    prefix=settings.API_PREFIX)
app.include_router(websites.router, prefix=settings.API_PREFIX)
app.include_router(voice.router,    prefix=settings.API_PREFIX)
app.include_router(audit.router,    prefix=settings.API_PREFIX)
app.include_router(referral.router, prefix=settings.API_PREFIX)
app.include_router(admin.router,    prefix=settings.API_PREFIX)
app.include_router(memory.router,   prefix=settings.API_PREFIX)


# ── Global error handler ──────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    log.error("Unhandled error: %s %s — %s", request.method, request.url.path, exc)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


# ── Core endpoints ────────────────────────────────────────────
@app.get("/health")
async def health():
    return {
        "status": "ok",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
    }


@app.get("/config")
async def config():
    return {
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "features": {
            "ai_chat": bool(settings.DEEPSEEK_API_KEY),
            "media_generation": bool(settings.BYTEZ_API_KEY),
            "payments": settings.payments_enabled,
            "email": bool(settings.SMTP_USER),
            "storage": bool(settings.SUPABASE_URL),
            "cache": bool(settings.UPSTASH_REDIS_REST_URL),
        },
    }


@app.get("/")
async def root():
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/health",
    }
