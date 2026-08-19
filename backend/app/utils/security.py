from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from passlib.context import CryptContext
from app.config import get_settings

settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ─── Token blacklist (in-memory; production → Redis/DB) ─────
_token_blacklist: set[str] = set()


def blacklist_token(jti: str) -> None:
    _token_blacklist.add(jti)


def is_token_blacklisted(jti: str) -> bool:
    return jti in _token_blacklist


def clear_blacklist() -> None:
    _token_blacklist.clear()


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


def verify_token_not_blacklisted(payload: dict) -> bool:
    """Check that token jti is not in the blacklist."""
    jti = payload.get("jti")
    if jti and is_token_blacklisted(jti):
        return False
    return True
