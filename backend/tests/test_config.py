from app.config import get_settings


def test_settings_load():
    settings = get_settings()
    assert settings.SECRET_KEY
    assert "postgresql" in settings.DATABASE_URL
    assert settings.ACCESS_TOKEN_EXPIRE_MINUTES > 0
    assert settings.REFRESH_TOKEN_EXPIRE_DAYS > 0


def test_settings_defaults():
    settings = get_settings()
    assert settings.DEBUG is True
    assert "redis" in settings.REDIS_URL
