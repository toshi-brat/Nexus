from fastapi import APIRouter, Query
from pydantic import BaseModel
import pandas as pd
from datetime import datetime
import logging

from services.brain.engine import brain
from services.data.indstocks_feed import indstocks_feed

logger = logging.getLogger("brain_api")
router = APIRouter(prefix="/brain", tags=["Nexus Brain"])

# Initialize connection on startup
@router.on_event("startup")
async def startup_event():
    indstocks_feed.authenticate()

@router.get("/analyze/{symbol}")
async def analyze_symbol(symbol: str, capital: float = Query(100000.0)):
    # 1. Fetch OHLCV History (Real API or Fallback Simulator)
    df = indstocks_feed.get_historical_data(symbol, timeframe="15m", days=5)

    # 2. Fetch Option Chain Data (PCR, Max Pain)
    options_data, current_price = indstocks_feed.get_option_chain_snapshot(symbol)
    if current_price == 0 and len(df) > 0:
        current_price = df.iloc[-1]['close']

    # 3. Fetch Sentiment (Mocking for now until Twitter/Reddit scraper is built)
    from services.data.scraper import scraper
    from services.data.nlp import nlp_engine

    # 3. Fetch Real Sentiment for the Asset
    posts = scraper.get_news(limit=10) + scraper.get_reddit_posts(limit=10)
    real_score = nlp_engine.aggregate_score(posts)
    # Map [-1, 1] to [0, 1] for strategy math
    normalized_score = (real_score + 1) / 2
    sentiment_data = {"score": normalized_score}

    # 4. Run Quant Engine
    signals = brain.run_all(symbol, df, options_data, sentiment_data, capital=capital)

    return {
        "symbol": symbol,
        "current_price": round(current_price, 2),
        "capital_base": capital,
        "timestamp": datetime.now().isoformat(),
        "data_source": "INDstocks API" if not indstocks_feed._mock_mode else "INDstocks Simulator",
        "signals_found": len(signals),
        "suggestions": [s.__dict__ for s in signals]
    }
