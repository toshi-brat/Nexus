"""
NEXUS — NSE Market Scanner
Runs stock-only strategies across the dynamic NSE equity universe.
Each strategy acts as a FILTER — stocks that pass a strategy condition
are surfaced as signals with confidence score, entry, target, SL, and Kelly sizing.

Strategy routing:
  Stocks only → VolatilityBreakoutStrategy, SimonsStatArbStrategy, SentimentConvergenceStrategy
"""

import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Dict, List, Optional
from uuid import uuid4

import pandas as pd

from services.brain.engine import brain
from services.brain.nse_universe import get_nse_equities
from services.brain.strategies import (
    VolatilityBreakoutStrategy,
    SentimentConvergenceStrategy,
    SimonsStatArbStrategy,
)
from services.data.indstocks_feed import indstocks_feed

logger = logging.getLogger("market_scanner")

# Equity-compatible strategies — run on every F&O stock
EQUITY_STRATEGIES = [
    VolatilityBreakoutStrategy(),
    SentimentConvergenceStrategy(),
    SimonsStatArbStrategy(),
]

EXCLUDE_SYMBOL_TOKENS = (
    "ETF",
    "BEES",
    "IETF",
    "GOLD",
    "SILVER",
    "LIQUID",
)


def _is_quality_equity_symbol(symbol: str) -> bool:
    s = (symbol or "").upper().strip()
    if not s:
        return False
    if any(token in s for token in EXCLUDE_SYMBOL_TOKENS):
        return False
    return True


def _normalize_stock_signal(raw: Dict, capital: float) -> Dict:
    entry = float(raw.get("entry") or 0)
    target = float(raw.get("target") or 0)
    stop = float(raw.get("stop_loss") or 0)
    kelly_pct = float(raw.get("kelly_pct") or 0)
    confidence = float(raw.get("confidence") or 0)
    risk = max(abs(entry - stop), 0.01)
    reward = abs(target - entry)
    rr = reward / risk

    # Convert derivative-style qty into practical EQ quantity sizing.
    allocated = float(raw.get("capital_allocated") or 0)
    if allocated <= 0:
        allocated = capital * 0.01
    eq_qty = max(1, int(allocated / max(entry, 1.0)))
    eq_allocated = round(eq_qty * entry, 2)

    recommendation_score = round((confidence * 0.60) + (min(kelly_pct, 10) * 2.0) + (min(rr, 5) * 4.0), 2)

    normalized = dict(raw)
    normalized["instrument"] = "EQ"
    normalized["legs"] = []
    normalized["qty"] = eq_qty
    normalized["capital_allocated"] = eq_allocated
    normalized["rr"] = round(rr, 2)
    normalized["recommendation_score"] = recommendation_score
    return normalized


def _scan_single(
    symbol: str,
    timeframe: str,
    days: int,
    capital: float,
    sentiment_score: float,
) -> List[Dict]:
    """Fetches data for one symbol and runs the appropriate strategy set."""
    results = []
    try:
        df = indstocks_feed.get_historical_data(symbol, timeframe=timeframe, days=days)
        if df is None or len(df) < 20:
            return results

        # Stocks-only scanner: no options-chain path.
        options_data = {"pcr": 1.0, "max_pain": df.iloc[-1]["close"]}
        strategies = EQUITY_STRATEGIES

        sentiment = {"score": sentiment_score}

        for strategy in strategies:
            try:
                signal = strategy.analyze(symbol, df.copy(), options_data, sentiment, capital)
                if signal:
                    results.append({
                        "symbol": signal.symbol,
                        "strategy": signal.strategy_name,
                        "action": signal.action,
                        "instrument": signal.instrument,
                        "entry": round(signal.entry_price, 2),
                        "target": round(signal.target_price, 2),
                        "stop_loss": round(signal.stop_loss, 2),
                        "confidence": round(signal.confidence_score * 100, 1),
                        "kelly_pct": signal.kelly_percentage,
                        "qty": signal.suggested_qty,
                        "capital_allocated": round(signal.capital_allocated, 2),
                        "rationale": signal.rationale,
                        "legs": signal.legs,
                        "scanned_at": datetime.now().isoformat(),
                        "is_index": False,
                    })
            except Exception as e:
                logger.debug(f"Strategy {strategy.__class__.__name__} error on {symbol}: {e}")

    except Exception as e:
        logger.warning(f"Scan failed for {symbol}: {e}")

    return results


def run_full_scan(
    timeframe: str = "15m",
    days: int = 10,
    capital: float = 100_000.0,
    sentiment_score: float = 0.5,
    max_workers: int = 12,
    batch_size: int = 120,
    pause_between_batches_sec: float = 1.0,
    max_symbols: Optional[int] = None,
    symbol_offset: int = 0,
    shortlist_limit: int = 5,
    strategy_filter: Optional[str] = None,
) -> Dict:
    """
    Main entry point. Scans the full NSE F&O universe concurrently.

    Args:
        timeframe:       Candle interval passed to indstocks_feed (e.g. '15m', '1d')
        days:            Lookback window in days
        capital:         Portfolio capital for Kelly sizing
        sentiment_score: Global sentiment score [0, 1] (0.5 = neutral)
        max_workers:     Thread pool size — keep ≤15 to avoid rate limits
        batch_size:      Number of symbols processed per batch
        pause_between_batches_sec: Delay between batches to reduce burst load
        max_symbols:     Optional cap for partial scans (e.g. 500 symbols)
        symbol_offset:   Start index inside universe (useful for rolling windows)
        shortlist_limit: Number of top ranked suggestions to surface
        strategy_filter: Optional strategy name substring to filter results

    Returns dict with keys: signals, summary, scan_meta
    """
    # Dynamic broad NSE equity universe (fallback handled in loader).
    equity_symbols = [s for s in get_nse_equities() if _is_quality_equity_symbol(s)]

    all_signals: List[Dict] = []
    errors: List[str] = []
    scanned = 0
    start_ts = time.time()

    all_work_items = [(s, False) for s in equity_symbols]
    if symbol_offset < 0:
        symbol_offset = 0
    work_items = all_work_items[symbol_offset:]
    if max_symbols is not None:
        work_items = work_items[: max(0, max_symbols)]

    if not work_items:
        return {
            "signals": [],
            "summary": {},
            "scan_meta": {
                "symbols_scanned": 0,
                "index_symbols": 0,
                "equity_symbols": len(equity_symbols),
                "signals_found": 0,
                "errors": 0,
                "elapsed_seconds": 0.0,
                "timeframe": timeframe,
                "days_lookback": days,
                "capital_base": capital,
                "batch_size": batch_size,
                "pause_between_batches_sec": pause_between_batches_sec,
                "max_symbols": max_symbols,
                "symbol_offset": symbol_offset,
                "batches_processed": 0,
                "scanned_at": datetime.now().isoformat(),
            },
        }

    logger.info(
        f"[MarketScanner] Starting full scan: {len(work_items)} symbols, "
        f"timeframe={timeframe}, days={days}, workers={max_workers}, "
        f"batch_size={batch_size}, pause={pause_between_batches_sec}s"
    )

    if batch_size <= 0:
        batch_size = 120

    batches_processed = 0
    for i in range(0, len(work_items), batch_size):
        batch = work_items[i:i + batch_size]
        batches_processed += 1
        logger.info(
            "[MarketScanner] Processing batch %s (%s symbols)",
            batches_processed,
            len(batch),
        )
        with ThreadPoolExecutor(max_workers=min(max_workers, len(batch))) as pool:
            futures = {
                pool.submit(
                    _scan_single, sym, timeframe, days, capital, sentiment_score
                ): sym
                for sym, _ in batch
            }

            for future in as_completed(futures):
                sym = futures[future]
                try:
                    results = future.result(timeout=30)
                    all_signals.extend(results)
                    scanned += 1
                except Exception as e:
                    errors.append(f"{sym}: {e}")
                    scanned += 1

        if i + batch_size < len(work_items) and pause_between_batches_sec > 0:
            time.sleep(pause_between_batches_sec)

    elapsed = round(time.time() - start_ts, 2)

    # Strategy filter
    if strategy_filter:
        flt = strategy_filter.lower()
        all_signals = [s for s in all_signals if flt in s["strategy"].lower()]

    # Normalize stock suggestions to EQ shape and rank by recommendation score.
    all_signals = [_normalize_stock_signal(s, capital=capital) for s in all_signals]
    all_signals.sort(
        key=lambda x: (x.get("recommendation_score", 0), x.get("confidence", 0), x.get("kelly_pct", 0)),
        reverse=True,
    )
    shortlist_limit = max(1, shortlist_limit)
    shortlist = all_signals[:shortlist_limit]

    # Per-strategy summary
    strategy_summary: Dict[str, Dict] = {}
    for sig in all_signals:
        name = sig["strategy"]
        if name not in strategy_summary:
            strategy_summary[name] = {"count": 0, "symbols": []}
        strategy_summary[name]["count"] += 1
        strategy_summary[name]["symbols"].append(sig["symbol"])

    logger.info(
        f"[MarketScanner] Done. Scanned {scanned} symbols in {elapsed}s. "
        f"Signals found: {len(all_signals)}. Errors: {len(errors)}"
    )

    run_id = str(uuid4())
    return {
        "run_id": run_id,
        "signals": all_signals,
        "shortlist": shortlist,
        "summary": strategy_summary,
        "scan_meta": {
            "symbols_scanned": scanned,
            "index_symbols": 0,
            "equity_symbols": len(equity_symbols),
            "signals_found": len(all_signals),
            "shortlist_count": len(shortlist),
            "errors": len(errors),
            "elapsed_seconds": elapsed,
            "timeframe": timeframe,
            "days_lookback": days,
            "capital_base": capital,
            "batch_size": batch_size,
            "pause_between_batches_sec": pause_between_batches_sec,
            "max_symbols": max_symbols,
            "symbol_offset": symbol_offset,
            "batches_processed": batches_processed,
            "shortlist_limit": shortlist_limit,
            "scanned_at": datetime.now().isoformat(),
        },
    }
