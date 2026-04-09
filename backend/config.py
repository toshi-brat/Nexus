import os
from pathlib import Path
from typing import List

BACKEND_DIR = Path(__file__).resolve().parent
REPO_ROOT = BACKEND_DIR.parent
ENV_FILE = REPO_ROOT / ".env"


def _load_env_file(path: Path) -> None:
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            continue

        if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
            value = value[1:-1]

        os.environ.setdefault(key, value)


def _env(key: str, default: str = "") -> str:
    return os.getenv(key, default)


def _env_bool(key: str, default: bool = False) -> bool:
    raw = os.getenv(key)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(key: str, default: int) -> int:
    raw = os.getenv(key)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _env_list(key: str, default: List[str]) -> List[str]:
    raw = os.getenv(key)
    if raw is None or not raw.strip():
        return default
    return [item.strip() for item in raw.split(",") if item.strip()]


def _resolve_database_url(url: str) -> str:
    prefix = "sqlite:///"
    if not url.startswith(prefix):
        return url

    path_part = url[len(prefix):]
    if path_part.startswith("/"):
        return url

    resolved = (REPO_ROOT / path_part.lstrip("./")).resolve()
    return f"{prefix}{resolved}"


_load_env_file(ENV_FILE)

APP_NAME = _env("APP_NAME", "NEXUS Trading System")
DEBUG = _env_bool("DEBUG", False)
HOST = _env("HOST", "0.0.0.0")
PORT = _env_int("PORT", 8000)
CORS_ORIGINS = _env_list(
    "CORS_ORIGINS",
    ["http://localhost:5173", "http://127.0.0.1:5173"],
)
USE_DEMO_DATA = _env_bool("USE_DEMO_DATA", False)
ENABLE_AUTONOMOUS_BOT = _env_bool("ENABLE_AUTONOMOUS_BOT", False)

DATABASE_URL = _resolve_database_url(_env("DATABASE_URL", "sqlite:///./data/nexus.db"))
DATABASE_DIR = str(Path(DATABASE_URL.replace("sqlite:///", "", 1)).parent) if DATABASE_URL.startswith("sqlite:///") else str(REPO_ROOT / "data")

BROKER = _env("BROKER", "indmoney").strip().lower()
ENABLE_BROKER_SYNC = _env_bool("ENABLE_BROKER_SYNC", False)
ZERODHA_API_KEY = _env("ZERODHA_API_KEY", "")
ZERODHA_ACCESS_TOKEN = _env("ZERODHA_ACCESS_TOKEN", "")
UPSTOX_ACCESS_TOKEN = _env("UPSTOX_ACCESS_TOKEN", "")
DHAN_CLIENT_ID = _env("DHAN_CLIENT_ID", "")
DHAN_ACCESS_TOKEN = _env("DHAN_ACCESS_TOKEN", "")

INDMONEY_ACCESS_TOKEN = _env("INDMONEY_ACCESS_TOKEN", "")
INDSTOCKS_API_KEY = _env("INDSTOCKS_API_KEY", "")
INDSTOCKS_SECRET = _env("INDSTOCKS_SECRET", "")
INDSTOCKS_REST_URL = _env("INDSTOCKS_REST_URL", "https://api.indstocks.com/v1")
INDSTOCKS_WS_URL = _env("INDSTOCKS_WS_URL", "wss://api.indstocks.com/quotes")

REDDIT_CLIENT_ID = _env("REDDIT_CLIENT_ID", "")
REDDIT_CLIENT_SECRET = _env("REDDIT_CLIENT_SECRET", "")
REDDIT_USER_AGENT = _env("REDDIT_USER_AGENT", "NEXUS/1.0")
TWITTER_BEARER_TOKEN = _env("TWITTER_BEARER_TOKEN", "")

NEWS_API_KEY = _env("NEWS_API_KEY", "")
NEWS_QUERY = _env(
    "NEWS_QUERY",
    "NSE OR BSE OR NIFTY OR BANKNIFTY OR SENSEX OR Bombay Stock Exchange OR National Stock Exchange OR Indian stock market",
)
ADDITIONAL_RSS_FEEDS = _env("ADDITIONAL_RSS_FEEDS", "")
TRADINGVIEW_MCP_URL = _env("TRADINGVIEW_MCP_URL", "http://localhost:3001")

NEWS_FEEDS = {
    "MoneyControl": "https://www.moneycontrol.com/rss/marketreports.xml",
    "Economic Times": "https://economictimes.indiatimes.com/markets/rssfeeds/2146842.cms",
    "LiveMint": "https://www.livemint.com/rss/markets",
    "Business Standard": "https://www.business-standard.com/rss/markets-106.rss",
    "Financial Express": "https://www.financialexpress.com/market/feed/",
    "CNBC TV18": "https://www.cnbctv18.com/common/standardrss/market.xml",
}


class Settings:
    def __init__(self) -> None:
        self.APP_NAME = APP_NAME
        self.DEBUG = DEBUG
        self.HOST = HOST
        self.PORT = PORT
        self.CORS_ORIGINS = CORS_ORIGINS
        self.USE_DEMO_DATA = USE_DEMO_DATA
        self.ENABLE_AUTONOMOUS_BOT = ENABLE_AUTONOMOUS_BOT
        self.DATABASE_URL = DATABASE_URL
        self.DATABASE_DIR = DATABASE_DIR

        self.BROKER = BROKER
        self.ENABLE_BROKER_SYNC = ENABLE_BROKER_SYNC
        self.ZERODHA_API_KEY = ZERODHA_API_KEY
        self.ZERODHA_ACCESS_TOKEN = ZERODHA_ACCESS_TOKEN
        self.UPSTOX_ACCESS_TOKEN = UPSTOX_ACCESS_TOKEN
        self.DHAN_CLIENT_ID = DHAN_CLIENT_ID
        self.DHAN_ACCESS_TOKEN = DHAN_ACCESS_TOKEN

        self.INDMONEY_ACCESS_TOKEN = INDMONEY_ACCESS_TOKEN
        self.INDSTOCKS_API_KEY = INDSTOCKS_API_KEY
        self.INDSTOCKS_SECRET = INDSTOCKS_SECRET
        self.INDSTOCKS_REST_URL = INDSTOCKS_REST_URL
        self.INDSTOCKS_WS_URL = INDSTOCKS_WS_URL

        self.REDDIT_CLIENT_ID = REDDIT_CLIENT_ID
        self.REDDIT_CLIENT_SECRET = REDDIT_CLIENT_SECRET
        self.REDDIT_USER_AGENT = REDDIT_USER_AGENT
        self.TWITTER_BEARER_TOKEN = TWITTER_BEARER_TOKEN

        self.NEWS_API_KEY = NEWS_API_KEY
        self.NEWS_QUERY = NEWS_QUERY
        self.ADDITIONAL_RSS_FEEDS = ADDITIONAL_RSS_FEEDS
        self.TRADINGVIEW_MCP_URL = TRADINGVIEW_MCP_URL


settings = Settings()
