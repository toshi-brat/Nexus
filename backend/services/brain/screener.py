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

    def calculate_rsi(self, series: pd.Series, period: int = 14) -> pd.Series:
        delta = series.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))

    def scan_universe(self) -> List[Dict]:
        logger.info(f"Initiating Swing Screener across {len(self.universe)} stocks...")
        shortlist = []

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

                # Setup 1: Volume Breakout (High Momentum)
                # Price is above 20 & 50 SMA, Volume is 2.5x the average, RSI > 60
                if close > sma20 and close > sma50 and vol > (vol20 * 2.5) and rsi > 60:
                    shortlist.append({
                        "symbol": symbol,
                        "setup": "Volume Breakout",
                        "close": round(close, 2),
                        "rsi": round(rsi, 2),
                        "rationale": f"Massive volume surge ({vol/vol20:.1f}x avg) with bullish momentum. Strong swing continuation expected."
                    })
                    continue

                # Setup 2: Deep Pullback / Mean Reversion
                # Price is in a long term uptrend (SMA50) but short term oversold (RSI < 30)
                if sma20 > sma50 and rsi < 30 and close < df['close'].iloc[-10:-1].min():
                    shortlist.append({
                        "symbol": symbol,
                        "setup": "Mean Reversion (Dip Buy)",
                        "close": round(close, 2),
                        "rsi": round(rsi, 2),
                        "rationale": f"Stock is structurally bullish but heavily oversold (RSI: {rsi:.1f}). Favorable R:R for a bounce."
                    })
                    continue

            except Exception as e:
                logger.error(f"Screener Error on {symbol}: {e}")

        return shortlist

screener = SwingScreener()
