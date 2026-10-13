import secrets
import warnings

from pydantic_settings import BaseSettings, SettingsConfigDict

_DEV_SECRET = "learnhub-dev-secret-change-in-production-3f9a1c7e2b"  # legacy default; never valid


class Settings(BaseSettings):
    """Central application settings (overridable via .env / environment)."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_NAME: str = "Infohive LMS API"
    API_PREFIX: str = "/api"
    # "development" or "production". Production refuses to start with an unsafe config.
    ENV: str = "development"

    # Security
    SECRET_KEY: str = _DEV_SECRET
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60                # short-lived access tokens; refresh rotates
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    RESET_TOKEN_EXPIRE_MINUTES: int = 30
    PASSWORD_MIN_LENGTH: int = 8
    # Comma-separated list of browser origins allowed to call the API directly.
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"
    # Simple per-IP rate limit for login / register / password reset.
    AUTH_RATE_LIMIT_PER_MINUTE: int = 10

    # Payments are not integrated yet. While False, students cannot self-enroll in paid
    # courses (instructors/admins can still enroll them manually after payment).
    ALLOW_UNPAID_ENROLLMENT: bool = False

    # Database. SQLite locally; on Supabase use the *pooler* URL (port 6543), e.g.
    # postgresql://postgres.<ref>:<password>@aws-0-<region>.pooler.supabase.com:6543/postgres
    LMS_DATABASE_URL: str = "sqlite:///./data/lms.db"
    AUTO_MIGRATE: bool = True                  # create missing tables/columns at startup

    # Public URL of the website (used in emails, Paystack callback, certificate links)
    FRONTEND_URL: str = "http://localhost:3000"

    # ---- session cookies (HttpOnly; the browser's JavaScript can never read the tokens)
    COOKIE_SECURE: bool | None = None          # default: True in production
    COOKIE_SAMESITE: str = "lax"
    # Shared secret the website's /api proxy sends, so the API can trust the client IP it forwards
    PROXY_SHARED_SECRET: str = ""

    # ---- email (SMTP). Leave SMTP_HOST empty to log emails instead of sending them.
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "Infohive Technology <no-reply@infohive.local>"
    SMTP_SECURITY: str = "starttls"            # starttls | ssl | none
    SMTP_TIMEOUT: int = 10

    # ---- payments (Paystack). Off by default.
    PAYSTACK_ENABLED: bool = False
    PAYSTACK_SECRET_KEY: str = ""
    PAYSTACK_PUBLIC_KEY: str = ""
    PAYSTACK_BASE_URL: str = "https://api.paystack.co"
    PAYMENT_CURRENCY: str = "NGN"              # course prices are in this currency

    # ---- live classes
    # Built-in video rooms use Jitsi. For production use JaaS (8x8 "Jitsi as a Service", free tier
    # available): set JAAS_APP_ID, JAAS_KID and JAAS_PRIVATE_KEY and instructors become moderators.
    # Without JaaS, rooms open on JITSI_DOMAIN (public meet.jit.si limits embedded calls to ~5 min;
    # fine for testing, or point it at your own Jitsi server).
    JITSI_DOMAIN: str = "meet.jit.si"
    JAAS_APP_ID: str = ""
    JAAS_KID: str = ""
    JAAS_PRIVATE_KEY: str = ""                 # PEM; "\n" escapes are accepted
    LIVE_JOIN_EARLY_MINUTES: int = 15

    # ---- public contact details shown on the website (empty = hidden)
    CONTACT_EMAIL: str = ""
    CONTACT_PHONE: str = ""
    CONTACT_ADDRESS: str = ""
    CONTACT_HOURS: str = ""
    SOCIAL_FACEBOOK: str = ""
    SOCIAL_LINKEDIN: str = ""
    SOCIAL_INSTAGRAM: str = ""
    SOCIAL_X: str = ""
    # where contact-form enquiries are emailed (defaults to CONTACT_EMAIL)
    ENQUIRY_NOTIFY_EMAIL: str = ""

    # ---- file storage. Local disk by default; set these to use Supabase Storage (needed on Vercel).
    SUPABASE_URL: str = ""
    SUPABASE_SERVICE_KEY: str = ""
    SUPABASE_BUCKET: str = "lms-media"

    # Uploads
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_MB: int = 50

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.ENV.lower() == "production"

    @property
    def cookie_secure(self) -> bool:
        return self.is_production if self.COOKIE_SECURE is None else self.COOKIE_SECURE

    @property
    def email_enabled(self) -> bool:
        return bool(self.SMTP_HOST)

    @property
    def payments_enabled(self) -> bool:
        return self.PAYSTACK_ENABLED and bool(self.PAYSTACK_SECRET_KEY)

    @property
    def jaas_enabled(self) -> bool:
        return bool(self.JAAS_APP_ID and self.JAAS_KID and self.JAAS_PRIVATE_KEY)

    @property
    def use_supabase_storage(self) -> bool:
        return bool(self.SUPABASE_URL and self.SUPABASE_SERVICE_KEY)

    @property
    def database_url(self) -> str:
        """Accept the plain postgres:// URL Supabase shows and use the psycopg 3 driver."""
        url = self.LMS_DATABASE_URL
        for prefix in ("postgres://", "postgresql://"):
            if url.startswith(prefix):
                return "postgresql+psycopg://" + url[len(prefix):]
        return url


settings = Settings()

if settings.is_production:
    if settings.PAYSTACK_ENABLED and not settings.PAYSTACK_SECRET_KEY:
        raise RuntimeError("PAYSTACK_ENABLED=true needs PAYSTACK_SECRET_KEY")
    if settings.LMS_DATABASE_URL.startswith("sqlite"):
        warnings.warn("ENV=production is using SQLite; set LMS_DATABASE_URL to your Supabase Postgres URL")

if settings.SECRET_KEY == _DEV_SECRET or len(settings.SECRET_KEY) < 32:
    if settings.is_production:
        raise RuntimeError("SECRET_KEY must be set to a long random value (>= 32 chars) in production")
    # dev: generate a random key once and keep it in data/ (git-ignored), so the
    # published default can never be used to forge tokens
    import os
    _key_file = os.path.join("data", ".secret_key")
    # (never reached in production: ENV=production requires SECRET_KEY above)
    os.makedirs("data", exist_ok=True)
    if not os.path.exists(_key_file):
        with open(_key_file, "w") as fh:
            fh.write(secrets.token_urlsafe(48))
        warnings.warn(f"SECRET_KEY not set - generated a development key in {_key_file}")
    with open(_key_file) as fh:
        settings.SECRET_KEY = fh.read().strip()
