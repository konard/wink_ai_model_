from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    service_name: str = "ml-rating-service"
    model_version: str = "v1.0"
    model_name: str = "all-MiniLM-L6-v2"

    device: str = "cuda:0"
    max_scenes: int = 1000

    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        env_prefix = "ML_"


settings = Settings()
