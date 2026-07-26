from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # App
    APP_NAME: str = "Orpaq AI"
    DEBUG: bool = False

    # SQLite database path (default: ~/.orpaq/leads.db)
    SQLITE_PATH: str = str(Path.home() / ".orpaq" / "leads.db")

    # Legacy API keys — keep empty defaults so old services don't error
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""
    SUPABASE_SERVICE_KEY: str = ""
    OPENAI_API_KEY: str = ""
    GROQ_API_KEY: str = ""
    SERPAPI_KEY: str = ""
    APIFY_API_KEY: str = ""
    PAGESPEED_API_KEY: str = ""
    REDIS_URL: str = "redis://localhost:6379"


settings = Settings()
