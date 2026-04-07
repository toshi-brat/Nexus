import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True
    DATABASE_URL: str = "sqlite:///./data/nexus.db"
    USE_DEMO_DATA: bool = True
    ENABLE_BROKER_SYNC: bool = False
    BROKER: str = "zerodha"           # zerodha | upstox | dhan
    ZERODHA_API_KEY: str = ""
    ZERODHA_ACCESS_TOKEN: str = ""
    UPSTOX_ACCESS_TOKEN: str = ""
    DHAN_ACCESS_TOKEN: str = ""
    DHAN_CLIENT_ID: str = ""
    REDDIT_CLIENT_ID: str = ""
    REDDIT_CLIENT_SECRET: str = ""
    REDDIT_USER_AGENT: str = "nexus-trading/1.0"
    NEWS_API_KEY: str = ""
    TRADINGVIEW_MCP_URL: str = "http://localhost:3001"
    class Config:
        env_file = ".env"

settings = Settings()
