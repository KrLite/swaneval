from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://evalscope:evalscope@localhost:6001/evalscope"
    DATABASE_URL_SYNC: str = "postgresql://evalscope:evalscope@localhost:6001/evalscope"
    REDIS_URL: str = "redis://localhost:6379/0"
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]
    SECRET_KEY: str = "dev-secret-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24
    UPLOAD_DIR: str = "data/uploads"

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
