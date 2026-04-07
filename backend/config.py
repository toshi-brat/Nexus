"""
NEXUS — Application Settings
Loaded from .env (or environment variables).
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # ── App ───────────────────────────────────────────────────────────────────
    APP_NAME:  str = "NEXUS Trading System"
    DEBUG:     bool = False
    HOST:      str = "0.0.0.0"
    PORT:      int = 8000

    # ── IndMoney / INDstocks ──────────────────────────────────────────────────
    # Generate from: https://www.indstocks.com/app/api-trading
    # Expires every 24 h — whitelist your static IP before use.
    INDMONEY_ACCESS_TOKEN: str = ""

    # ── Zerodha Kite (optional) ───────────────────────────────────────────────
    ZERODHA_API_KEY:    str = ""
    ZERODHA_API_SECRET: str = ""
    ZERODHA_REQUEST_TOKEN: str = ""

    # ── Upstox (optional) ─────────────────────────────────────────────────────
    UPSTOX_API_KEY:    str = ""
    UPSTOX_API_SECRET: str = ""

    # ── Market data ───────────────────────────────────────────────────────────
    NSE_BASE_URL: str = "https://www.nseindia.com"

    # ── Sentiment sources ─────────────────────────────────────────────────────
    REDDIT_CLIENT_ID:     str = ""
    REDDIT_CLIENT_SECRET: str = ""
    REDDIT_USER_AGENT:    str = "NEXUS/1.0"
    TWITTER_BEARER_TOKEN: str = ""

    # ── Database ──────────────────────────────────────────────────────────────
    DATABASE_URL: str = "sqlite:///./data/nexus.db"

    # ── CORS ──────────────────────────────────────────────────────────────────
    CORS_ORIGINS: list = ["http://localhost:5173", "http://localhost:3000"]


settings = Settings()
