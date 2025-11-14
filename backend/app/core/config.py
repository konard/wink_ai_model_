from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    app_name: str = "Movie Rating Backend"
    app_version: str = "1.0.0"
    debug: bool = False

    database_url: str = (
        "postgresql+asyncpg://rating_user:rating_pass@localhost:5432/rating_db"
    )

    redis_url: str = "redis://localhost:6379/0"

    ml_service_url: str = "http://localhost:8001"

    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:5173"]

    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
