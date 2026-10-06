from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str = (
        "postgresql+psycopg://retail:retail123@postgres:5432/retail_analytics"
    )
    REDIS_URL: str = "redis://redis:6379/0"
    JWT_SECRET: str = "retail-analytics-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 1440
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"
    AI_SERVICE_API_KEY: str = "ai-service-internal-key"


settings = Settings()
