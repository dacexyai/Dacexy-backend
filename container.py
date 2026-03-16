from __future__ import annotations
from src.infrastructure.ai_providers.deepseek import DeepSeekProvider
from src.infrastructure.email.email_service import EmailService
from src.infrastructure.cache.upstash import UpstashRedis
from src.infrastructure.storage.supabase_storage import SupabaseStorage

_deepseek: DeepSeekProvider | None = None
_email: EmailService | None = None
_redis: UpstashRedis | None = None
_storage: SupabaseStorage | None = None


def get_deepseek() -> DeepSeekProvider:
    global _deepseek
    if _deepseek is None:
        _deepseek = DeepSeekProvider()
    return _deepseek


def get_email() -> EmailService:
    global _email
    if _email is None:
        _email = EmailService()
    return _email


def get_redis() -> UpstashRedis:
    global _redis
    if _redis is None:
        _redis = UpstashRedis()
    return _redis


def get_storage() -> SupabaseStorage:
    global _storage
    if _storage is None:
        _storage = SupabaseStorage()
    return _storage
