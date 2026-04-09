"""
NEXUS Brain — Quantitative Strategy Engine
Pure mathematical rules engine for identifying high-probability options trades.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class TradeSignal:
    symbol: str
    strategy_name: str
    action: str          # "BUY" | "SELL"
    instrument: str      # "OPT" | "FUT" | "EQ"
    legs: List[Dict]     # [{"strike": 22000, "type": "CE", "action": "SELL", "qty": 50}, ...]
    entry_price: float
    target_price: float
    stop_loss: float
    confidence_score: float  # 0.0 to 1.0
    rationale: str


class QuantEngine:
    """Mathematical rules engine for trade generation."""

    def __init__(self):
        pass

    def _calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate base technical indicators."""
        df = df.copy()
        # EMAs
        df['EMA_20'] = df['close'].ewm(span=20, adjust=False).mean()
        df['EMA_50'] = df['close'].ewm(span=50, adjust=False).mean()

        # RSI (14)
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))

        # ATR (14) for volatility/stop-loss calculation
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = np.max(ranges, axis=1)
        df['ATR'] = true_range.rolling(14).mean()

        return df

    def analyze_mean_reversion(self, symbol: str, df: pd.DataFrame) -> Optional[TradeSignal]:
        """
        Mean Reversion Strategy:
        Looks for price > 3 ATRs away from 20 EMA + RSI extremes.
        """
        if len(df) < 50:
            return None

        df = self._calculate_indicators(df)
        latest = df.iloc[-1]

        distance_from_ema = latest['close'] - latest['EMA_20']
        atr = latest['ATR']
        rsi = latest['RSI']

        # 1. Overbought -> Short signal (Credit Call Spread)
        if distance_from_ema > (2.5 * atr) and rsi > 75:
            strike = round(latest['close'] / 50) * 50 + 100 # Round to nearest OTM strike
            return TradeSignal(
                symbol=symbol,
                strategy_name="Mean Reversion (Overbought)",
                action="SELL",
                instrument="OPT",
                legs=[
                    {"strike": strike, "type": "CE", "action": "SELL", "qty": 50},
                    {"strike": strike + 100, "type": "CE", "action": "BUY", "qty": 50} # Hedge
                ],
                entry_price=latest['close'],
                target_price=latest['EMA_20'], # Target is reversion to mean
                stop_loss=latest['close'] + (1.5 * atr),
                confidence_score=0.82,
                rationale=f"Price is {distance_from_ema:.1f} points (>2.5 ATR) above 20 EMA with RSI at {rsi:.1f}. High probability of reversion to mean."
            )

        # 2. Oversold -> Long signal (Credit Put Spread)
        elif distance_from_ema < -(2.5 * atr) and rsi < 25:
            strike = round(latest['close'] / 50) * 50 - 100
            return TradeSignal(
                symbol=symbol,
                strategy_name="Mean Reversion (Oversold)",
                action="BUY",
                instrument="OPT",
                legs=[
                    {"strike": strike, "type": "PE", "action": "SELL", "qty": 50},
                    {"strike": strike - 100, "type": "PE", "action": "BUY", "qty": 50}
                ],
                entry_price=latest['close'],
                target_price=latest['EMA_20'],
                stop_loss=latest['close'] - (1.5 * atr),
                confidence_score=0.79,
                rationale=f"Price is {abs(distance_from_ema):.1f} points (>2.5 ATR) below 20 EMA with RSI at {rsi:.1f}. High probability of bounce."
            )

        return None

    def analyze_options_data(self, symbol: str, spot_price: float, chain_data: Dict) -> Optional[TradeSignal]:
        """
        Analyzes option chain data (PCR, Max Pain, Volume buildup) 
        to suggest Iron Condors or Strangles.
        """
        # Note: chain_data would be the parsed output from nse_fetcher
        try:
            # Simplified mock logic for the architecture demonstration
            pcr = chain_data.get("pcr", 1.0)
            max_pain = chain_data.get("max_pain", spot_price)

            if 0.8 < pcr < 1.2:
                # Market is balanced, suggest non-directional Iron Condor
                upper_bound = max_pain + 300
                lower_bound = max_pain - 300

                return TradeSignal(
                    symbol=symbol,
                    strategy_name="Delta Neutral (Iron Condor)",
                    action="SELL",
                    instrument="OPT",
                    legs=[
                        {"strike": upper_bound, "type": "CE", "action": "SELL", "qty": 50},
                        {"strike": upper_bound + 100, "type": "CE", "action": "BUY", "qty": 50},
                        {"strike": lower_bound, "type": "PE", "action": "SELL", "qty": 50},
                        {"strike": lower_bound - 100, "type": "PE", "action": "BUY", "qty": 50}
                    ],
                    entry_price=spot_price,
                    target_price=spot_price, # Max profit at expiry if spot == entry
                    stop_loss=0, # Managed via leg premiums
                    confidence_score=0.85,
                    rationale=f"PCR is neutral at {pcr:.2f}. Max pain is {max_pain}. Market is likely to consolidate. Selling strangles outside the expected range."
                )
        except Exception as e:
            pass

        return None

brain = QuantEngine()
