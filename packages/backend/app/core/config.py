from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator


class Settings(BaseSettings):
    database_url: str
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_expires_minutes: int = 60
    board_width: int = 540
    board_height: int = 540
    cors_origins: str = "http://localhost:5173"
    redis_url: str = "redis://localhost:6379/0"
    db_ssl: bool = False

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

    @field_validator("database_url")
    @classmethod
    def _use_async_driver(cls, v: str) -> str:
        """Railway and Heroku-style URLs use the bare postgres scheme."""
        for prefix in ("postgresql://", "postgres://"):
            if v.startswith(prefix):
                return "postgresql+asyncpg://" + v[len(prefix):]
        return v

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",")]


@lru_cache
def get_settings() -> Settings:
    return Settings()