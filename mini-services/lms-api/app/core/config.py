from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Central application settings (overridable via .env / environment)."""

    APP_NAME: str = "LearnHub LMS API"
    API_PREFIX: str = "/api"

    # Security
    SECRET_KEY: str = "learnhub-dev-secret-change-in-production-3f9a1c7e2b"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24          # 24h access tokens
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    RESET_TOKEN_EXPIRE_MINUTES: int = 30
    PASSWORD_MIN_LENGTH: int = 6

    # Database - swap to postgresql://... for production; schema is portable
    LMS_DATABASE_URL: str = "sqlite:///./data/lms.db"

    # Uploads
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_MB: int = 50

    class Config:
        env_file = ".env"


settings = Settings()
