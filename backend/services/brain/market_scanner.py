"""
NEXUS — NSE Market Scanner
Runs all 5 strategies across the full NSE F&O universe concurrently.
Each strategy acts as a FILTER — stocks that pass a strategy condition
are surfaced as signals with confidence score, entry, target, SL, and Kelly sizing.

Strategy routing:
  Index only  → OIGravityStrategy, PCRMomentumFadeStrategy   (need option chain)
  All stocks  → VolatilityBreakoutStrategy, SimonsStatArbStrategy, SentimentConvergenceStrategy
"""

import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Dict, List, Optional

import pandas as pd

from services.brain.engine import brain
from services.brain.nse_universe import get_index_symbols, get_fno_stocks
from services.brain.strategies import (
    OIGravityStrategy,
    PCRMomentumFadeStrategy,
    VolatilityBreakoutStrategy,
    SentimentConvergenceStrategy,
    SimonsStatArbStrategy,
)
from services.data.indstocks_feed import indstocks_feed

logger = logging.getLogger("market_scanner")

# Strategies that need a live option chain — only run on index symbols
OPTIONS_ONLY_STRATEGIES = {OIGravityStrategy, PCRMomentumFadeStrategy}

# Equity-compatible strategies — run on every F&O stock
EQUITY_STRATEGIES = [
    VolatilityBreakoutStrategy(),
    SentimentConvergenceStrategy(),
    SimonsStatArbStrategy(),
]

# Index strategies (reuse instances)
INDEX_STRATEGIES = [
    OIGravityStrategy(),
    PCRMomentumFadeStrategy(),
    VolatilityBreakoutStrategy(),
    SentimentConvergenceStrategy(),
    SimonsStatArbStrategy(),
]


def _scan_single(
    symbol: str,
    is_index: bool,
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

        if is_index:
            options_data, spot = indstocks_feed.get_option_chain_snapshot(symbol)
            strategies = INDEX_STRATEGIES
        else:
            # For equities: no real option chain — pass empty options dict
            options_data = {"pcr": 1.0, "max_pain": df.iloc[-1]["close"]}
            spot = df.iloc[-1]["close"]
            strategies = EQUITY_STRATEGIES

        sentiment = {"score": sentiment_score}

        for strategy in strategies:
            # Skip options-only strategies for equity symbols
            if not is_index and type(strategy) in OPTIONS_ONLY_STRATEGIES:
                continue
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
                        "is_index": is_index,
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
        strategy_filter: Optional strategy name substring to filter results

    Returns dict with keys: signals, summary, scan_meta
    """
    index_symbols = get_index_symbols()
    fno_stocks = get_fno_stocks()

    all_signals: List[Dict] = []
    errors: List[str] = []
    scanned = 0
    start_ts = time.time()

    work_items = (
        [(s, True) for s in index_symbols] +
        [(s, False) for s in fno_stocks]
    )

    logger.info(
        f"[MarketScanner] Starting full scan: {len(work_items)} symbols, "
        f"timeframe={timeframe}, days={days}, workers={max_workers}"
    )

    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {
            pool.submit(
                _scan_single, sym, is_idx, timeframe, days, capital, sentiment_score
            ): sym
            for sym, is_idx in work_items
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

    elapsed = round(time.time() - start_ts, 2)

    # Strategy filter
    if strategy_filter:
        flt = strategy_filter.lower()
        all_signals = [s for s in all_signals if flt in s["strategy"].lower()]

    # Sort: confidence desc, then kelly desc
    all_signals.sort(key=lambda x: (x["confidence"], x["kelly_pct"] or 0), reverse=True)

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

    return {
        "signals": all_signals,
        "summary": strategy_summary,
        "scan_meta": {
            "symbols_scanned": scanned,
            "index_symbols": len(index_symbols),
            "equity_symbols": len(fno_stocks),
            "signals_found": len(all_signals),
            "errors": len(errors),
            "elapsed_seconds": elapsed,
            "timeframe": timeframe,
            "days_lookback": days,
            "capital_base": capital,
            "scanned_at": datetime.now().isoformat(),
        },
    }
