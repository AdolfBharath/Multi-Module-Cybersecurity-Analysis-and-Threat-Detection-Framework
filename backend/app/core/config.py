from functools import cached_property

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    PROJECT_NAME: str = "CyberShield XDR"
    ENVIRONMENT: str = "local"
    API_V1_PREFIX: str = "/api/v1"
    SECRET_KEY: str = "change-me-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 14
    DATABASE_URL: str = "sqlite:///./cybershield.db"
    REDIS_URL: str = "redis://localhost:6379/0"
    BACKEND_CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"
    VIRUSTOTAL_API_KEY: str = ""
    ABUSEIPDB_API_KEY: str = ""
    OTX_API_KEY: str = ""

    @cached_property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.BACKEND_CORS_ORIGINS.split(",") if origin.strip()]


settings = Settings()

