import secrets
import warnings
from pydantic import field_validator
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/internetshop"
    SECRET_KEY: str = "change-me-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    REDIS_URL: str = "redis://localhost:6379/0"
    DEBUG: bool = True

    CORS_ORIGINS: str = "http://localhost:3000"
    ALLOWED_HOSTS: str = "*"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        if v in ("change-me-in-production", "your-secret-key-change-in-production", ""):
            warnings.warn(
                "SECRET_KEY is a default/insecure value. "
                "Set a strong random key in production!",
                UserWarning,
                stacklevel=2,
            )
        if len(v) < 16:
            raise ValueError("SECRET_KEY must be at least 16 characters")
        return v

    @field_validator("DATABASE_URL")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        if "postgres:postgres" in v:
            warnings.warn(
                "DATABASE_URL contains default credentials. "
                "Change them for production!",
                UserWarning,
                stacklevel=2,
            )
        return v

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def allowed_hosts_list(self) -> list[str]:
        return [h.strip() for h in self.ALLOWED_HOSTS.split(",") if h.strip()]

    @property
    def is_production(self) -> bool:
        return not self.DEBUG


def generate_secret_key() -> str:
    """Generate a cryptographically strong random secret key."""
    return secrets.token_hex(32)


@lru_cache
def get_settings() -> Settings:
    return Settings()
