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


# ──────────────────────────────────────────────────────────────────────────────
# NSE Full Market Scanner — runs all 5 strategies across full F&O universe
# ──────────────────────────────────────────────────────────────────────────────
from services.brain.market_scanner import run_full_scan
from models.database import ScanResult, get_db
from sqlalchemy.orm import Session
from fastapi import Depends
from sqlalchemy import func


@router.get("/scan")
async def scan_full_nse(
    timeframe: str = Query("15m", description="Candle interval: 1m,5m,15m,1d"),
    days: int = Query(10, ge=3, le=60, description="Lookback days"),
    capital: float = Query(100000.0, description="Portfolio capital for Kelly sizing"),
    strategy: str = Query(None, description="Filter by strategy name substring"),
    save: bool = Query(True, description="Persist signals to DB for tracking"),
    db: Session = Depends(get_db),
):
    """
    Runs all 5 strategies across the full NSE F&O universe (~180 symbols).
    Index symbols (NIFTY, BANKNIFTY, FINNIFTY, MIDCPNIFTY) run all 5 strategies.
    Equity F&O stocks run: VolatilityBreakout, StatArb, SentimentConvergence.
    Returns signals ranked by confidence + Kelly %.
    """
    result = run_full_scan(
        timeframe=timeframe,
        days=days,
        capital=capital,
        strategy_filter=strategy,
    )

    if save:
        for sig in result["signals"]:
            row = ScanResult(
                symbol=sig["symbol"],
                strategy=sig["strategy"],
                action=sig["action"],
                instrument=sig["instrument"],
                entry_price=sig["entry"],
                target_price=sig["target"],
                stop_loss=sig["stop_loss"],
                confidence=sig["confidence"],
                kelly_pct=sig["kelly_pct"],
                qty=sig["qty"],
                capital_allocated=sig["capital_allocated"],
                rationale=sig["rationale"],
                timeframe=timeframe,
                days_lookback=days,
                is_index=sig["is_index"],
            )
            db.add(row)
        db.commit()
        result["saved_to_db"] = True
        result["saved_count"] = len(result["signals"])

    return result


@router.get("/scan/history")
async def scan_history(
    strategy: str = Query(None, description="Filter by strategy name (partial match)"),
    symbol: str = Query(None, description="Filter by symbol e.g. RELIANCE"),
    outcome: str = Query(None, description="PENDING | WIN | LOSS | SKIP"),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """
    Returns historical scan signals with outcomes for performance analysis.
    Use outcome=PENDING to see unresolved signals awaiting TP/SL.
    """
    q = db.query(ScanResult)
    if strategy:
        q = q.filter(ScanResult.strategy.ilike(f"%{strategy}%"))
    if symbol:
        q = q.filter(ScanResult.symbol == symbol.upper())
    if outcome:
        q = q.filter(ScanResult.outcome == outcome.upper())
    rows = q.order_by(ScanResult.scanned_at.desc()).limit(limit).all()

    clean = []
    for r in rows:
        d = {c.name: getattr(r, c.name) for c in r.__table__.columns}
        clean.append(d)

    return {"count": len(clean), "results": clean}


@router.get("/scan/performance")
async def scan_performance(db: Session = Depends(get_db)):
    """
    Strategy-level performance summary.
    Shows win rate, total signals, and avg PnL per strategy.
    Use this to test which strategies are performing across the NSE universe.
    """
    rows = db.query(
        ScanResult.strategy,
        func.count(ScanResult.id).label("total"),
        func.avg(ScanResult.outcome_pnl).label("avg_pnl"),
    ).group_by(ScanResult.strategy).all()

    result = []
    for r in rows:
        wins = db.query(func.count(ScanResult.id)).filter(
            ScanResult.strategy == r.strategy,
            ScanResult.outcome == "WIN"
        ).scalar() or 0
        losses = db.query(func.count(ScanResult.id)).filter(
            ScanResult.strategy == r.strategy,
            ScanResult.outcome == "LOSS"
        ).scalar() or 0
        pending = r.total - wins - losses

        result.append({
            "strategy": r.strategy,
            "total_signals": r.total,
            "wins": wins,
            "losses": losses,
            "pending": pending,
            "win_rate_pct": round(wins / r.total * 100, 1) if r.total else 0,
            "avg_pnl": round(r.avg_pnl or 0, 2),
        })

    result.sort(key=lambda x: x["win_rate_pct"], reverse=True)
    return {"strategy_performance": result}
