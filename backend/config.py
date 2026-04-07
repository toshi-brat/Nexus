"""
NEXUS — Application Settings
Loaded from .env (or environment variables).
"""

from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(BASE_DIR / ".env"), extra="ignore")

    # ── App ───────────────────────────────────────────────────────────────────
    APP_NAME:  str = "NEXUS Trading System"
    DEBUG:     bool = False
    HOST:      str = "0.0.0.0"
    PORT:      int = 8000
    USE_DEMO_DATA: bool = False
    ENABLE_BROKER_SYNC: bool = False
    BROKER: str = "indmoney"

    # ── IndMoney / INDstocks ──────────────────────────────────────────────────
    # Generate from: https://www.indstocks.com/app/api-trading
    # Expires every 24 h — whitelist your static IP before use.
    INDMONEY_ACCESS_TOKEN: str = ""

    # ── Zerodha Kite (optional) ───────────────────────────────────────────────
    ZERODHA_API_KEY:    str = ""
    ZERODHA_API_SECRET: str = ""
    ZERODHA_REQUEST_TOKEN: str = ""
    ZERODHA_ACCESS_TOKEN: str = ""

    # ── Upstox (optional) ─────────────────────────────────────────────────────
    UPSTOX_API_KEY:    str = ""
    UPSTOX_API_SECRET: str = ""
    UPSTOX_ACCESS_TOKEN: str = ""

    # ── Dhan (legacy optional) ───────────────────────────────────────────────
    DHAN_ACCESS_TOKEN: str = ""
    DHAN_CLIENT_ID:    str = ""

    # ── Market data ───────────────────────────────────────────────────────────
    NSE_BASE_URL: str = "https://www.nseindia.com"

    # ── Sentiment sources ─────────────────────────────────────────────────────
    REDDIT_CLIENT_ID:     str = ""
    REDDIT_CLIENT_SECRET: str = ""
    REDDIT_USER_AGENT:    str = "NEXUS/1.0"
    TWITTER_BEARER_TOKEN: str = ""
    NEWS_API_KEY:         str = ""
    NEWS_QUERY:           str = "NSE OR BSE OR NIFTY OR BANKNIFTY OR SENSEX OR Bombay Stock Exchange OR National Stock Exchange OR Indian stock market"
    ADDITIONAL_RSS_FEEDS: str = ""

    # ── Database ──────────────────────────────────────────────────────────────
    DATABASE_URL: str = "sqlite:///./data/nexus.db"

    # ── CORS ──────────────────────────────────────────────────────────────────
    CORS_ORIGINS: list = ["http://localhost:5173", "http://localhost:3000"]
    TRADINGVIEW_MCP_URL: str = "http://localhost:3001"

    @field_validator("DEBUG", mode="before")
    @classmethod
    def parse_debug(cls, value):
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            raw = value.strip().lower()
            if raw in {"1", "true", "yes", "on", "debug", "development", "dev"}:
                return True
            if raw in {"0", "false", "no", "off", "release", "production", "prod"}:
                return False
        return value


settings = Settings()
