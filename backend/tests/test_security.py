import pytest
from datetime import datetime, timedelta, timezone
from jose import jwt as jose_jwt, JWTError

from app.utils.security import (
    hash_password, verify_password,
    create_access_token, create_refresh_token,
    decode_token, verify_token_type,
    blacklist_token, is_token_blacklisted, clear_blacklist,
)
from app.config import get_settings
from app.database import AsyncSession

settings = get_settings()


# ═══════════════════════════════════════════════════════════════
# TOKEN STRUCTURE & TYPE VALIDATION
# ═══════════════════════════════════════════════════════════════

class TestTokenStructure:

    def test_access_token_has_type_claim(self):
        token = create_access_token("user-1")
        payload = decode_token(token)
        assert payload["type"] == "access"

    def test_refresh_token_has_type_claim(self):
        token = create_refresh_token("user-1")
        payload = decode_token(token)
        assert payload["type"] == "refresh"

    def test_access_token_has_jti(self):
        token = create_access_token("user-1")
        payload = decode_token(token)
        assert "jti" in payload
        assert len(payload["jti"]) > 0

    def test_refresh_token_has_jti(self):
        token = create_refresh_token("user-1")
        payload = decode_token(token)
        assert "jti" in payload

    def test_access_token_has_iat(self):
        token = create_access_token("user-1")
        payload = decode_token(token)
        assert "iat" in payload

    def test_tokens_have_different_jti(self):
        t1 = create_access_token("user-1")
        t2 = create_access_token("user-1")
        p1 = decode_token(t1)
        p2 = decode_token(t2)
        assert p1["jti"] != p2["jti"]

    def test_verify_token_type_access(self):
        token = create_access_token("user-1")
        payload = decode_token(token)
        assert verify_token_type(payload, "access") is True
        assert verify_token_type(payload, "refresh") is False

    def test_verify_token_type_refresh(self):
        token = create_refresh_token("user-1")
        payload = decode_token(token)
        assert verify_token_type(payload, "refresh") is True
        assert verify_token_type(payload, "access") is False

    def test_refresh_token_cannot_be_used_as_access(self):
        refresh = create_refresh_token("user-1")
        payload = decode_token(refresh)
        assert verify_token_type(payload, "access") is False


# ═══════════════════════════════════════════════════════════════
# TOKEN BLACKLIST
# ═══════════════════════════════════════════════════════════════

class TestTokenBlacklist:

    def setup_method(self):
        clear_blacklist()

    def test_token_not_blacklisted_by_default(self):
        token = create_access_token("user-1")
        payload = decode_token(token)
        assert is_token_blacklisted(payload["jti"]) is False

    def test_blacklist_token(self):
        token = create_access_token("user-1")
        payload = decode_token(token)
        blacklist_token(payload["jti"])
        assert is_token_blacklisted(payload["jti"]) is True

    def test_blacklist_only_affects_specific_token(self):
        t1 = create_access_token("user-1")
        t2 = create_access_token("user-1")
        p1 = decode_token(t1)
        p2 = decode_token(t2)
        blacklist_token(p1["jti"])
        assert is_token_blacklisted(p1["jti"]) is True
        assert is_token_blacklisted(p2["jti"]) is False

    def test_clear_blacklist(self):
        token = create_access_token("user-1")
        payload = decode_token(token)
        blacklist_token(payload["jti"])
        assert is_token_blacklisted(payload["jti"]) is True
        clear_blacklist()
        assert is_token_blacklisted(payload["jti"]) is False


# ═══════════════════════════════════════════════════════════════
# EXPIRED / INVALID TOKENS
# ═══════════════════════════════════════════════════════════════

class TestTokenValidation:

    def test_decode_invalid_token_raises(self):
        with pytest.raises(JWTError):
            decode_token("not.a.valid.token")

    def test_decode_tampered_token_raises(self):
        token = create_access_token("user-1")
        parts = token.split(".")
        tampered = parts[0] + "." + parts[1] + "X" + "." + parts[2]
        with pytest.raises(JWTError):
            decode_token(tampered)

    def test_wrong_secret_cannot_decode(self):
        token = jose_jwt.encode(
            {"sub": "user-1", "type": "access"},
            "wrong-secret",
            algorithm="HS256",
        )
        with pytest.raises(JWTError):
            decode_token(token)

    def test_access_token_expires(self):
        token = create_access_token("user-1")
        payload = decode_token(token)
        assert "exp" in payload
        assert payload["exp"] > payload["iat"]


# ═══════════════════════════════════════════════════════════════
# API-LEVEL SECURITY TESTS
# ═══════════════════════════════════════════════════════════════

@pytest.mark.asyncio
class TestAPISecurityHeaders:

    async def test_security_headers_present(self, client):
        resp = await client.get("/health")
        assert resp.headers["X-Content-Type-Options"] == "nosniff"
        assert resp.headers["X-Frame-Options"] == "DENY"
        assert resp.headers["X-XSS-Protection"] == "1; mode=block"
        assert "Referrer-Policy" in resp.headers


@pytest.mark.asyncio
class TestTokenAPIFlow:

    async def test_access_token_works_for_auth(self, client, db_session):
        from sqlalchemy import insert
        from app.models.user import User

        await db_session.execute(insert(User).values(
            id="sec-u1", email="sec@test.com", username="secuser",
            hashed_password=hash_password("secret123"), role="user",
        ))
        await db_session.commit()

        login = await client.post("/api/auth/login", json={
            "email": "sec@test.com", "password": "secret123",
        })
        access = login.json()["access_token"]

        me = await client.get("/api/auth/me", headers={"Authorization": f"Bearer {access}"})
        assert me.status_code == 200
        assert me.json()["email"] == "sec@test.com"

    async def test_refresh_token_rejected_as_access(self, client, db_session):
        from sqlalchemy import insert
        from app.models.user import User

        await db_session.execute(insert(User).values(
            id="sec-u2", email="sec2@test.com", username="secuser2",
            hashed_password=hash_password("secret123"), role="user",
        ))
        await db_session.commit()

        login = await client.post("/api/auth/login", json={
            "email": "sec2@test.com", "password": "secret123",
        })
        refresh = login.json()["refresh_token"]

        me = await client.get("/api/auth/me", headers={"Authorization": f"Bearer {refresh}"})
        assert me.status_code == 401

    async def test_logout_blacklists_refresh_token(self, client, db_session):
        from sqlalchemy import insert
        from app.models.user import User

        await db_session.execute(insert(User).values(
            id="sec-u3", email="sec3@test.com", username="secuser3",
            hashed_password=hash_password("secret123"), role="user",
        ))
        await db_session.commit()

        login = await client.post("/api/auth/login", json={
            "email": "sec3@test.com", "password": "secret123",
        })
        data = login.json()
        access = data["access_token"]
        refresh = data["refresh_token"]

        logout_resp = await client.post("/api/auth/logout",
            json={"refresh_token": refresh},
            headers={"Authorization": f"Bearer {access}"},
        )
        assert logout_resp.status_code == 204

        refresh_resp = await client.post("/api/auth/refresh",
            json={"refresh_token": refresh},
        )
        assert refresh_resp.status_code == 400
        assert "revoked" in refresh_resp.json()["detail"].lower()

    async def test_refresh_token_rotation(self, client, db_session):
        from sqlalchemy import insert
        from app.models.user import User

        await db_session.execute(insert(User).values(
            id="sec-u4", email="sec4@test.com", username="secuser4",
            hashed_password=hash_password("secret123"), role="user",
        ))
        await db_session.commit()

        login = await client.post("/api/auth/login", json={
            "email": "sec4@test.com", "password": "secret123",
        })
        old_refresh = login.json()["refresh_token"]

        refresh_resp = await client.post("/api/auth/refresh",
            json={"refresh_token": old_refresh},
        )
        assert refresh_resp.status_code == 200
        new_refresh = refresh_resp.json()["refresh_token"]
        assert new_refresh != old_refresh

        reuse_resp = await client.post("/api/auth/refresh",
            json={"refresh_token": old_refresh},
        )
        assert reuse_resp.status_code == 400
        assert "revoked" in reuse_resp.json()["detail"].lower()

        reuse_resp2 = await client.post("/api/auth/refresh",
            json={"refresh_token": new_refresh},
        )
        assert reuse_resp2.status_code == 200

    async def test_expired_access_token_rejected(self, client, db_session):
        payload = {
            "sub": "any-user",
            "exp": datetime.now(timezone.utc) - timedelta(hours=1),
            "iat": datetime.now(timezone.utc) - timedelta(hours=2),
            "jti": "expired-jti",
            "type": "access",
        }
        expired_token = jose_jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")

        resp = await client.get("/api/auth/me",
            headers={"Authorization": f"Bearer {expired_token}"},
        )
        assert resp.status_code == 401

    async def test_malformed_bearer_header(self, client):
        resp = await client.get("/api/auth/me",
            headers={"Authorization": "Bearer "},
        )
        assert resp.status_code == 401

    async def test_no_bearer_prefix(self, client):
        resp = await client.get("/api/auth/me",
            headers={"Authorization": "invalid-token"},
        )
        assert resp.status_code == 401


@pytest.mark.asyncio
class TestRBACSecurity:

    async def test_user_cannot_access_admin_users(self, client, db_session):
        from sqlalchemy import insert
        from app.models.user import User

        await db_session.execute(insert(User).values(
            id="rbac-user", email="rbac@test.com", username="rbacuser",
            hashed_password=hash_password("secret123"), role="user",
        ))
        await db_session.commit()

        login = await client.post("/api/auth/login", json={
            "email": "rbac@test.com", "password": "secret123",
        })
        h = {"Authorization": f"Bearer {login.json()['access_token']}"}

        resp = await client.get("/api/admin/users", headers=h)
        assert resp.status_code == 403

    async def test_user_cannot_access_admin_stats(self, client, db_session):
        from sqlalchemy import insert
        from app.models.user import User

        await db_session.execute(insert(User).values(
            id="rbac-u2", email="rbac2@test.com", username="rbacuser2",
            hashed_password=hash_password("secret123"), role="user",
        ))
        await db_session.commit()

        login = await client.post("/api/auth/login", json={
            "email": "rbac2@test.com", "password": "secret123",
        })
        h = {"Authorization": f"Bearer {login.json()['access_token']}"}

        resp = await client.get("/api/admin/stats", headers=h)
        assert resp.status_code == 403

    async def test_user_cannot_block_users(self, client, db_session):
        from sqlalchemy import insert
        from app.models.user import User

        await db_session.execute(insert(User).values(
            id="rbac-u3", email="rbac3@test.com", username="rbacuser3",
            hashed_password=hash_password("secret123"), role="user",
        ))
        await db_session.commit()

        login = await client.post("/api/auth/login", json={
            "email": "rbac3@test.com", "password": "secret123",
        })
        h = {"Authorization": f"Bearer {login.json()['access_token']}"}

        resp = await client.patch("/api/admin/users/rbac-u3/block", headers=h)
        assert resp.status_code == 403

    async def test_admin_can_access_admin_endpoints(self, client, db_session):
        from sqlalchemy import insert
        from app.models.user import User

        await db_session.execute(insert(User).values(
            id="rbac-admin", email="rbacadm@test.com", username="rbacadmin",
            hashed_password=hash_password("secret123"), role="admin",
        ))
        await db_session.commit()

        login = await client.post("/api/auth/login", json={
            "email": "rbacadm@test.com", "password": "secret123",
        })
        h = {"Authorization": f"Bearer {login.json()['access_token']}"}

        resp = await client.get("/api/admin/users", headers=h)
        assert resp.status_code == 200

    async def test_user_cannot_update_order_status(self, client, db_session):
        from sqlalchemy import insert
        from app.models.user import User

        await db_session.execute(insert(User).values(
            id="rbac-u5", email="rbac5@test.com", username="rbacuser5",
            hashed_password=hash_password("secret123"), role="user",
        ))
        await db_session.commit()

        login = await client.post("/api/auth/login", json={
            "email": "rbac5@test.com", "password": "secret123",
        })
        h = {"Authorization": f"Bearer {login.json()['access_token']}"}

        resp = await client.patch("/api/orders/fake-id/status",
            json={"status": "paid"}, headers=h,
        )
        assert resp.status_code in (400, 403, 404)

    async def test_user_cannot_delete_reviews_of_others(self, client, db_session):
        from sqlalchemy import insert
        from app.models.user import User

        await db_session.execute(insert(User).values(
            id="rbac-u6", email="rbac6@test.com", username="rbacuser6",
            hashed_password=hash_password("secret123"), role="user",
        ))
        await db_session.commit()

        login = await client.post("/api/auth/login", json={
            "email": "rbac6@test.com", "password": "secret123",
        })
        h = {"Authorization": f"Bearer {login.json()['access_token']}"}

        resp = await client.delete("/api/reviews/fake-review-id", headers=h)
        assert resp.status_code == 404


@pytest.mark.asyncio
class TestSQLInjectionAttempts:

    async def test_register_with_sql_injection_email(self, client):
        resp = await client.post("/api/auth/register", json={
            "email": "admin'--@test.com",
            "username": "sqluser",
            "password": "secret123",
        })
        assert resp.status_code in (201, 422)

    async def test_search_with_sql_injection(self, client):
        resp = await client.get("/api/products/", params={"q": "'; DROP TABLE products; --"})
        assert resp.status_code == 200

    async def test_login_with_sql_injection_email(self, client):
        resp = await client.post("/api/auth/login", json={
            "email": "admin@test.com' OR '1'='1",
            "password": "anything",
        })
        assert resp.status_code in (400, 422)

    async def test_promo_apply_with_sql_injection(self, client):
        resp = await client.post("/api/promo-codes/apply", json={
            "code": "'; DROP TABLE promo_codes; --",
        })
        assert resp.status_code == 404


@pytest.mark.asyncio
class TestXSSAttempts:

    async def test_register_with_xss_username(self, client):
        resp = await client.post("/api/auth/register", json={
            "email": "xss@test.com",
            "username": "<script>alert('xss')</script>",
            "password": "secret123",
        })
        assert resp.status_code in (201, 422)

    async def test_product_search_xss(self, client):
        resp = await client.get("/api/products/", params={
            "q": "<img src=x onerror=alert(1)>",
        })
        assert resp.status_code == 200
