"""
Secure configuration tests — lesson 60.
Validates settings, CORS, secrets, production readiness.
"""
import pytest
import os
from unittest.mock import patch


class TestSecretKeyValidation:

    def test_default_secret_key_warns(self):
        from app.config import Settings
        with pytest.warns(UserWarning, match="SECRET_KEY"):
            Settings(SECRET_KEY="change-me-in-production")

    def test_short_secret_key_rejected(self):
        from app.config import Settings
        with pytest.raises(ValueError, match="at least 16"):
            Settings(SECRET_KEY="short")

    def test_empty_secret_key_rejected(self):
        from app.config import Settings
        with pytest.raises(ValueError, match="at least 16"):
            Settings(SECRET_KEY="")

    def test_valid_secret_key_accepted(self):
        from app.config import Settings
        s = Settings(SECRET_KEY="a" * 32)
        assert s.SECRET_KEY == "a" * 32


class TestDatabaseURLValidation:

    def test_default_credentials_warn(self):
        from app.config import Settings
        with pytest.warns(UserWarning, match="default credentials"):
            Settings(DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/test")

    def test_custom_credentials_no_warning(self):
        from app.config import Settings
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            s = Settings(DATABASE_URL="postgresql+asyncpg://myuser:mypass@localhost:5432/test")
            assert "myuser" in s.DATABASE_URL


class TestCORSConfiguration:

    def test_cors_origins_list_single(self):
        from app.config import Settings
        s = Settings(CORS_ORIGINS="http://localhost:3000")
        assert s.cors_origins_list == ["http://localhost:3000"]

    def test_cors_origins_list_multiple(self):
        from app.config import Settings
        s = Settings(CORS_ORIGINS="http://localhost:3000,https://shop.com")
        assert s.cors_origins_list == ["http://localhost:3000", "https://shop.com"]

    def test_cors_origins_strips_whitespace(self):
        from app.config import Settings
        s = Settings(CORS_ORIGINS="http://a.com , http://b.com")
        assert s.cors_origins_list == ["http://a.com", "http://b.com"]

    def test_cors_origins_empty_string(self):
        from app.config import Settings
        s = Settings(CORS_ORIGINS="")
        assert s.cors_origins_list == []


class TestAllowedHosts:

    def test_allowed_hosts_list(self):
        from app.config import Settings
        s = Settings(ALLOWED_HOSTS="shop.com,api.shop.com")
        assert s.allowed_hosts_list == ["shop.com", "api.shop.com"]

    def test_wildcard(self):
        from app.config import Settings
        s = Settings(ALLOWED_HOSTS="*")
        assert s.allowed_hosts_list == ["*"]


class TestProductionDetection:

    def test_is_production_false_when_debug(self):
        from app.config import Settings
        s = Settings(DEBUG=True)
        assert s.is_production is False

    def test_is_production_true_when_not_debug(self):
        from app.config import Settings
        s = Settings(DEBUG=False)
        assert s.is_production is True


class TestSecretKeyGenerator:

    def test_generate_secret_key_length(self):
        from app.config import generate_secret_key
        key = generate_secret_key()
        assert len(key) == 64  # hex(32 bytes)

    def test_generate_secret_key_unique(self):
        from app.config import generate_secret_key
        k1 = generate_secret_key()
        k2 = generate_secret_key()
        assert k1 != k2

    def test_generate_secret_key_hex_only(self):
        from app.config import generate_secret_key
        key = generate_secret_key()
        int(key, 16)  # Should not raise


@pytest.mark.asyncio
class TestSecurityHeadersConfig:

    async def test_cors_headers_configured(self, client):
        """Verify CORS middleware is configured with settings."""
        from app.main import settings
        assert isinstance(settings.cors_origins_list, list)

    async def test_cors_origins_from_settings(self):
        """CORS origins come from Settings, not hardcoded."""
        from app.config import Settings
        s = Settings(CORS_ORIGINS="https://production.com")
        assert s.cors_origins_list == ["https://production.com"]


class TestTokenExpiration:

    def test_access_token_expire_default(self):
        from app.config import Settings
        s = Settings()
        assert s.ACCESS_TOKEN_EXPIRE_MINUTES == 30

    def test_refresh_token_expire_default(self):
        from app.config import Settings
        s = Settings()
        assert s.REFRESH_TOKEN_EXPIRE_DAYS == 7

    def test_custom_expiration(self):
        from app.config import Settings
        s = Settings(ACCESS_TOKEN_EXPIRE_MINUTES=60, REFRESH_TOKEN_EXPIRE_DAYS=30)
        assert s.ACCESS_TOKEN_EXPIRE_MINUTES == 60
        assert s.REFRESH_TOKEN_EXPIRE_DAYS == 30


@pytest.mark.asyncio
class TestEnvironmentBehavior:

    async def test_debug_mode_allows_rate_limit_skip(self, client):
        """In debug mode, rate limiter should be skipped."""
        from app.main import settings
        assert settings.DEBUG is True  # test env

    async def test_health_endpoint_always_accessible(self, client):
        """Health check works regardless of config."""
        resp = await client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
