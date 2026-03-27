from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Supabase
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""
    SUPABASE_SERVICE_KEY: str = ""

    # OpenAI / Groq
    OPENAI_API_KEY: str = ""
    GROQ_API_KEY: str = ""

    # SerpAPI / Apify
    SERPAPI_KEY: str = ""
    APIFY_API_KEY: str = ""

    # Google PageSpeed
    PAGESPEED_API_KEY: str = ""

    # Redis
    REDIS_URL: str = "redis://localhost:6379"

    # App
    APP_NAME: str = "Orpaq AI"
    DEBUG: bool = False

    # Storage
    SCREENSHOT_BUCKET: str = "screenshots"
    SCREENSHOT_PATH: str = "screenshots"


settings = Settings()
