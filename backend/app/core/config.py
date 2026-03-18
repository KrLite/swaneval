from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "EvalScope GUI"
    API_V1_PREFIX: str = "/api/v1"

    DATABASE_URL: str = "postgresql://evalscope:evalscope@localhost:6001/evalscope"
    REDIS_URL: str = "redis://localhost:6379/0"

    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    model_config = {"env_file": ".env", "case_sensitive": True}


settings = Settings()
