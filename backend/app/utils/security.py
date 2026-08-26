import logging
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from passlib.context import CryptContext
from app.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

BLACKLIST_PREFIX = "bl:token:"


async def blacklist_token(jti: str) -> None:
    from app.cache import get_redis
    redis = await get_redis()
    if redis:
        ttl = settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400
        try:
            await redis.set(f"{BLACKLIST_PREFIX}{jti}", "1", ex=ttl)
        except Exception as e:
            logger.warning("Redis blacklist set failed: %s", e)
    else:
        logger.warning("Redis unavailable, token %s not blacklisted", jti)


async def is_token_blacklisted(jti: str) -> bool:
    from app.cache import get_redis
    redis = await get_redis()
    if redis:
        try:
            return await redis.exists(f"{BLACKLIST_PREFIX}{jti}") == 1
        except Exception as e:
            logger.warning("Redis blacklist check failed: %s", e)
    return False


async def clear_blacklist() -> None:
    from app.cache import get_redis
    redis = await get_redis()
    if redis:
        try:
            keys = []
            async for key in redis.scan_iter(match=f"{BLACKLIST_PREFIX}*"):
                keys.append(key)
            if keys:
                await redis.delete(*keys)
        except Exception as e:
            logger.warning("Redis blacklist clear failed: %s", e)


# ─── Password hashing ────────────────────────────────────────

def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


# ─── Token creation ──────────────────────────────────────────

def _create_token(user_id: str, token_type: str, expires_delta: timedelta) -> str:
    import uuid
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "exp": now + expires_delta,
        "iat": now,
        "jti": str(uuid.uuid4()),
        "type": token_type,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")


def create_access_token(user_id: str) -> str:
    return _create_token(
        user_id,
        "access",
        timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )


def create_refresh_token(user_id: str) -> str:
    return _create_token(
        user_id,
        "refresh",
        timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )


def decode_token(token: str) -> dict:
    """Decode and validate a JWT token. Raises JWTError on failure."""
    return jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])


def verify_token_type(payload: dict, expected_type: str) -> bool:
    """Check that token has the expected type claim."""
    return payload.get("type") == expected_type


async def verify_token_not_blacklisted(payload: dict) -> bool:
    """Check that token jti is not in the blacklist."""
    jti = payload.get("jti")
    if jti and await is_token_blacklisted(jti):
        return False
    return True
