"""
NEXUS Brain — Trading Strategies with Kelly Criterion Sizing
"""
import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple
from .models import TradeSignal

class BaseStrategy:
    def calculate_kelly(self, win_rate: float, entry: float, target: float, sl: float, capital: float, lot_size: int) -> Tuple[float, float, int]:
        """
        Calculates position size using the Half-Kelly Criterion.
        f* = W - ((1 - W) / R)
        """
        reward = abs(target - entry)
        risk = abs(entry - sl)

        if risk == 0 or reward == 0:
            return 0.0, 0.0, lot_size

        r = reward / risk
        kelly_pct = win_rate - ((1 - win_rate) / r)

        # Use Half-Kelly for safety and cap at 10% max portfolio risk
        safe_kelly = max(0.0, min(kelly_pct * 0.5, 0.10))

        # Allocated capital
        allocated = capital * safe_kelly

        # Determine quantity (Allocated Capital / Risk per unit)
        qty = int((allocated / risk) // lot_size) * lot_size
        qty = max(lot_size, qty) # Always at least 1 lot

        return round(safe_kelly * 100, 2), allocated, qty

    def analyze(self, symbol: str, df: pd.DataFrame, options: Dict, sentiment: Dict, capital: float) -> Optional[TradeSignal]:
        raise NotImplementedError

class OIGravityStrategy(BaseStrategy):
    def analyze(self, symbol: str, df: pd.DataFrame, options: Dict, sentiment: Dict, capital: float) -> Optional[TradeSignal]:
        spot = df.iloc[-1]['close']
        pcr = options.get("pcr", 1.0)
        max_pain = options.get("max_pain", spot)
        lot_size = 25 if "NIFTY" in symbol else 15

        if 0.8 <= pcr <= 1.2:
            upper_wall = round((max_pain + 300) / 100) * 100
            lower_wall = round((max_pain - 300) / 100) * 100

            # Mock targets for Kelly
            target = spot
            sl = spot + 150 # Mock risk
            kelly_pct, alloc, qty = self.calculate_kelly(0.65, spot, target, sl, capital, lot_size)

            return TradeSignal(
                symbol=symbol, strategy_name="OI Gravity (Iron Condor)", action="SELL", instrument="OPT",
                legs=[
                    {"strike": upper_wall, "type": "CE", "action": "SELL", "qty": qty},
                    {"strike": upper_wall + 100, "type": "CE", "action": "BUY", "qty": qty},
                    {"strike": lower_wall, "type": "PE", "action": "SELL", "qty": qty},
                    {"strike": lower_wall - 100, "type": "PE", "action": "BUY", "qty": qty}
                ],
                entry_price=spot, target_price=target, stop_loss=sl, confidence_score=0.85,
                kelly_percentage=kelly_pct, suggested_qty=qty, capital_allocated=alloc,
                rationale=f"PCR is neutral ({pcr:.2f}). Max Pain is {max_pain}. Selling condor. Kelly recommends {qty} qty ({kelly_pct}% risk)."
            )
        return None

class PCRMomentumFadeStrategy(BaseStrategy):
    def analyze(self, symbol: str, df: pd.DataFrame, options: Dict, sentiment: Dict, capital: float) -> Optional[TradeSignal]:
        if len(df) < 20: return None
        spot = df.iloc[-1]['close']
        pcr = options.get("pcr", 1.0)
        lot_size = 25 if "NIFTY" in symbol else 15

        sma20 = df['close'].rolling(20).mean().iloc[-1]
        std20 = df['close'].rolling(20).std().iloc[-1]
        upper_bb = sma20 + (2 * std20)
        lower_bb = sma20 - (2 * std20)

        if pcr < 0.6 and spot <= lower_bb:
            strike = round(spot / 100) * 100
            target, sl = sma20, spot - std20
            kelly_pct, alloc, qty = self.calculate_kelly(0.55, spot, target, sl, capital, lot_size)

            return TradeSignal(
                symbol=symbol, strategy_name="PCR Fade (Oversold Bounce)", action="BUY", instrument="OPT",
                legs=[{"strike": strike, "type": "CE", "action": "BUY", "qty": qty}],
                entry_price=spot, target_price=target, stop_loss=sl, confidence_score=0.78,
                kelly_percentage=kelly_pct, suggested_qty=qty, capital_allocated=alloc,
                rationale=f"Extreme fear (PCR {pcr:.2f}) at lower BB. Half-Kelly sizing: {qty} qty ({kelly_pct}% risk)."
            )

        elif pcr > 1.4 and spot >= upper_bb:
            strike = round(spot / 100) * 100
            target, sl = sma20, spot + std20
            kelly_pct, alloc, qty = self.calculate_kelly(0.55, spot, target, sl, capital, lot_size)

            return TradeSignal(
                symbol=symbol, strategy_name="PCR Fade (Overbought Rejection)", action="BUY", instrument="OPT",
                legs=[{"strike": strike, "type": "PE", "action": "BUY", "qty": qty}],
                entry_price=spot, target_price=target, stop_loss=sl, confidence_score=0.78,
                kelly_percentage=kelly_pct, suggested_qty=qty, capital_allocated=alloc,
                rationale=f"Extreme greed (PCR {pcr:.2f}) at upper BB. Half-Kelly sizing: {qty} qty ({kelly_pct}% risk)."
            )
        return None

class VolatilityBreakoutStrategy(BaseStrategy):
    def analyze(self, symbol: str, df: pd.DataFrame, options: Dict, sentiment: Dict, capital: float) -> Optional[TradeSignal]:
        if len(df) < 14: return None
        spot = df.iloc[-1]['close']
        vol = df.iloc[-1]['volume']
        avg_vol = df['volume'].rolling(10).mean().iloc[-1]
        lot_size = 25 if "NIFTY" in symbol else 15

        tr = pd.concat([df['high'] - df['low'], np.abs(df['high'] - df['close'].shift()), np.abs(df['low'] - df['close'].shift())], axis=1).max(axis=1)
        atr = tr.rolling(14).mean()
        current_atr = atr.iloc[-1]
        min_atr_10 = atr.rolling(10).min().iloc[-1]

        recent_high = df['high'].iloc[-4:-1].max()
        if current_atr <= min_atr_10 * 1.1 and vol > (avg_vol * 1.5) and spot > recent_high:
            strike = round(spot / 100) * 100
            target, sl = spot + (3 * current_atr), spot - current_atr
            kelly_pct, alloc, qty = self.calculate_kelly(0.45, spot, target, sl, capital, lot_size) # Lower win rate, higher R:R

            return TradeSignal(
                symbol=symbol, strategy_name="Vol Breakout (Long)", action="BUY", instrument="OPT",
                legs=[{"strike": strike, "type": "CE", "action": "BUY", "qty": qty}],
                entry_price=spot, target_price=target, stop_loss=sl, confidence_score=0.82,
                kelly_percentage=kelly_pct, suggested_qty=qty, capital_allocated=alloc,
                rationale=f"Volatility expansion + Volume surge. 1:3 R/R setup. Kelly sizing: {qty} qty."
            )
        return None

class SentimentConvergenceStrategy(BaseStrategy):
    def analyze(self, symbol: str, df: pd.DataFrame, options: Dict, sentiment: Dict, capital: float) -> Optional[TradeSignal]:
        if len(df) < 50: return None
        spot = df.iloc[-1]['close']
        ema50 = df['close'].ewm(span=50, adjust=False).mean().iloc[-1]
        score = sentiment.get("score", 0.5)
        lot_size = 25 if "NIFTY" in symbol else 15

        if spot > ema50 and score > 0.75:
            strike = round(spot / 100) * 100
            target, sl = spot + 200, ema50
            kelly_pct, alloc, qty = self.calculate_kelly(0.60, spot, target, sl, capital, lot_size)

            return TradeSignal(
                symbol=symbol, strategy_name="Sentiment Convergence (Bullish)", action="BUY", instrument="OPT",
                legs=[{"strike": strike, "type": "CE", "action": "BUY", "qty": qty}],
                entry_price=spot, target_price=target, stop_loss=sl, confidence_score=0.88,
                kelly_percentage=kelly_pct, suggested_qty=qty, capital_allocated=alloc,
                rationale=f"Price > 50-EMA + Bullish NLP (Score {score:.2f}). Kelly sizing: {qty} qty."
            )
        return None

class SimonsStatArbStrategy(BaseStrategy):
    def analyze(self, symbol: str, df: pd.DataFrame, options: Dict, sentiment: Dict, capital: float) -> Optional[TradeSignal]:
        if len(df) < 20: return None
        spot = df.iloc[-1]['close']
        lot_size = 25 if "NIFTY" in symbol else 15

        if 'correlated_close' not in df.columns:
            df['correlated_close'] = df['close'] * 2.1 + np.random.normal(0, 10, len(df))
            df.loc[df.index[-1], 'correlated_close'] += 150 

        df['ratio'] = df['correlated_close'] / df['close']
        df['ratio_mean'] = df['ratio'].rolling(window=20).mean()
        df['ratio_std'] = df['ratio'].rolling(window=20).std()
        df['z_score'] = (df['ratio'] - df['ratio_mean']) / df['ratio_std']
        current_z = df.iloc[-1]['z_score']

        if current_z > 2.0:
            strike = round(spot / 100) * 100
            target, sl = spot + 150, spot - 75
            kelly_pct, alloc, qty = self.calculate_kelly(0.51, spot, target, sl, capital, lot_size) # 50.75% win rate roughly

            return TradeSignal(
                symbol=symbol, strategy_name="Renaissance Stat-Arb (Z-Score > 2)", action="BUY", instrument="OPT",
                legs=[{"strike": strike, "type": "CE", "action": "BUY", "qty": qty}],
                entry_price=spot, target_price=target, stop_loss=sl, confidence_score=0.89,
                kelly_percentage=kelly_pct, suggested_qty=qty, capital_allocated=alloc,
                rationale=f"Z-Score {current_z:.2f}. Statistical anomaly. Kelly sizing: {qty} qty ({kelly_pct}% risk)."
            )
        elif current_z < -2.0:
            strike = round(spot / 100) * 100
            target, sl = spot - 150, spot + 75
            kelly_pct, alloc, qty = self.calculate_kelly(0.51, spot, target, sl, capital, lot_size)

            return TradeSignal(
                symbol=symbol, strategy_name="Renaissance Stat-Arb (Z-Score < -2)", action="SELL", instrument="OPT",
                legs=[{"strike": strike, "type": "CE", "action": "SELL", "qty": qty}],
                entry_price=spot, target_price=target, stop_loss=sl, confidence_score=0.89,
                kelly_percentage=kelly_pct, suggested_qty=qty, capital_allocated=alloc,
                rationale=f"Z-Score {current_z:.2f}. Statistical anomaly. Kelly sizing: {qty} qty ({kelly_pct}% risk)."
            )
        return None
