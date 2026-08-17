from app.utils.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
)
from jose import jwt
from app.config import get_settings

settings = get_settings()


def test_hash_password():
    hashed = hash_password("mypassword")
    assert hashed != "mypassword"
    assert len(hashed) > 50


def test_verify_password_correct():
    hashed = hash_password("secret123")
    assert verify_password("secret123", hashed) is True


def test_verify_password_wrong():
    hashed = hash_password("secret123")
    assert verify_password("wrongpassword", hashed) is False


def test_create_access_token():
    token = create_access_token("user-id-123")
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    assert payload["sub"] == "user-id-123"
    assert "exp" in payload


def test_create_refresh_token():
    token = create_refresh_token("user-id-456")
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    assert payload["sub"] == "user-id-456"
    assert "exp" in payload


def test_different_tokens_different_payloads():
    t1 = create_access_token("user-1")
    t2 = create_access_token("user-2")
    p1 = jwt.decode(t1, settings.SECRET_KEY, algorithms=["HS256"])
    p2 = jwt.decode(t2, settings.SECRET_KEY, algorithms=["HS256"])
    assert p1["sub"] != p2["sub"]
