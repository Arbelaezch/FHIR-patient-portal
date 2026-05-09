"""
Redis-backed session store.

Thin async wrapper around the redis-py client.
All auth state (PKCE verifiers, Epic access tokens) lives here.
Keys are namespaced by the caller — e.g. "pkce:{state}", "session:{id}".
"""
import redis.asyncio as aioredis
from app.config import settings

# Module-level client — created once at import time.
# redis-py manages its own connection pool internally.
_client: aioredis.Redis = aioredis.from_url(
    settings.REDIS_URL,
    encoding="utf-8",
    decode_responses=True,
)


class SessionStore:
    """Static async methods for get / set / delete operations on Redis."""

    @staticmethod
    async def get(key: str) -> str | None:
        """Return the value for key, or None if missing / expired."""
        return await _client.get(key)

    @staticmethod
    async def set(key: str, value: str, ttl: int = 3600) -> None:
        """Store value under key with a TTL in seconds."""
        await _client.setex(key, ttl, value)

    @staticmethod
    async def delete(key: str) -> None:
        """Delete a key (no-op if it doesn't exist)."""
        await _client.delete(key)