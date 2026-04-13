"""
NEXUS - Quantitative Stock Screener for Swing Trading
Scans a universe of highly liquid NSE stocks to find multi-day swing setups.
"""
import pandas as pd
import numpy as np
import logging
from typing import List, Dict

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from services.data.indstocks_feed import indstocks_feed

logger = logging.getLogger("stock_screener")

class SwingScreener:
    def __init__(self):
        # Universe of highly liquid F&O stocks for swing trading
        self.universe = [
            "RELIANCE", "HDFCBANK", "ICICIBANK", "INFY", "TCS", 
            "ITC", "LT", "AXISBANK", "KOTAKBANK", "SBIN", 
            "TATAMOTORS", "MARUTI", "SUNPHARMA", "HINDUNILVR", "BAJFINANCE", 
            "BHARTIARTL", "ASIANPAINT", "M&M", "TITAN", "ULTRACEMCO"
        ]
        self.breakout_volume_multiple = 1.8
        self.min_breakout_rsi = 58
        self.max_ranked_results = 5

    @staticmethod
    def signal_strength(score: float) -> str:
        if score >= 0.9:
            return "A"
        if score >= 0.7:
            return "B"
        return "C"

    def calculate_rsi(self, series: pd.Series, period: int = 14) -> pd.Series:
        delta = series.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))

    def scan_universe(self) -> List[Dict]:
        logger.info(f"Initiating Swing Screener across {len(self.universe)} stocks...")
        shortlist = []
        ranked_candidates = []

        for symbol in self.universe:
            try:
                # Fetch 100 days of DAILY ('1D') data for swing analysis
                df = indstocks_feed.get_historical_data(symbol, timeframe="1D", days=100)
                if len(df) < 50:
                    continue

                close = df['close'].iloc[-1]
                vol = df['volume'].iloc[-1]

                # Technical Indicators
                df['sma_20'] = df['close'].rolling(window=20).mean()
                df['sma_50'] = df['close'].rolling(window=50).mean()
                df['vol_20_avg'] = df['volume'].rolling(window=20).mean()
                df['rsi_14'] = self.calculate_rsi(df['close'])

                sma20 = df['sma_20'].iloc[-1]
                sma50 = df['sma_50'].iloc[-1]
                vol20 = df['vol_20_avg'].iloc[-1]
                rsi = df['rsi_14'].iloc[-1]
                if pd.isna(sma20) or pd.isna(sma50) or pd.isna(vol20) or pd.isna(rsi) or vol20 <= 0:
                    continue

                vol_ratio = vol / vol20
                trend_strength = ((close / sma20) - 1) + ((close / sma50) - 1)
                rsi_score = max(0.0, (rsi - 50) / 50)
                score = round((vol_ratio * 0.45) + (trend_strength * 100 * 0.35) + (rsi_score * 0.20), 3)

                # Setup 1: Volume Breakout (High Momentum)
                # Price is above 20 & 50 SMA, Volume is 2.5x the average, RSI > 60
                if close > sma20 and close > sma50 and vol_ratio > self.breakout_volume_multiple and rsi >= self.min_breakout_rsi:
                    strength = self.signal_strength(score)
                    shortlist.append({
                        "symbol": symbol,
                        "setup": "Volume Breakout",
                        "close": round(close, 2),
                        "rsi": round(rsi, 2),
                        "score": score,
                        "signal_strength": strength,
                        "rationale": f"Volume surge ({vol_ratio:.1f}x avg) with bullish trend above SMA20/50. Swing continuation probability elevated."
                    })
                    continue

                # Setup 2: Deep Pullback / Mean Reversion
                # Price is in a long term uptrend (SMA50) but short term oversold (RSI < 30)
                if sma20 > sma50 and rsi < 30 and close < df['close'].iloc[-10:-1].min():
                    strength = self.signal_strength(score)
                    shortlist.append({
                        "symbol": symbol,
                        "setup": "Mean Reversion (Dip Buy)",
                        "close": round(close, 2),
                        "rsi": round(rsi, 2),
                        "score": score,
                        "signal_strength": strength,
                        "rationale": f"Stock is structurally bullish but heavily oversold (RSI: {rsi:.1f}). Favorable R:R for a bounce."
                    })
                    continue

                # Backup ranking candidate for quiet sessions (used only if no strict setup is found).
                if close > sma50 and rsi >= 52 and vol_ratio >= 1.15:
                    strength = self.signal_strength(score)
                    ranked_candidates.append({
                        "symbol": symbol,
                        "setup": "Momentum Watchlist",
                        "close": round(close, 2),
                        "rsi": round(rsi, 2),
                        "score": score,
                        "signal_strength": strength,
                        "rationale": f"Trend-positive profile with improving momentum (vol {vol_ratio:.2f}x, RSI {rsi:.1f})."
                    })

            except Exception as e:
                logger.error(f"Screener Error on {symbol}: {e}")

        if not shortlist and ranked_candidates:
            ranked_candidates.sort(key=lambda x: x["score"], reverse=True)
            return ranked_candidates[: self.max_ranked_results]

        shortlist.sort(key=lambda x: x.get("score", 0), reverse=True)
        return shortlist

screener = SwingScreener()
