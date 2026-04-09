"""
NEXUS Brain — Core Engine
Runs all strategies in an ensemble and aggregates the signals.
"""
import pandas as pd
from typing import Dict, List
from .models import TradeSignal
from .strategies import (
    OIGravityStrategy, 
    PCRMomentumFadeStrategy, 
    VolatilityBreakoutStrategy, 
    SentimentConvergenceStrategy,
    SimonsStatArbStrategy
)

class QuantEngine:
    def __init__(self):
        self.strategies = [
            OIGravityStrategy(),
            PCRMomentumFadeStrategy(),
            VolatilityBreakoutStrategy(),
            SentimentConvergenceStrategy(),
            SimonsStatArbStrategy()
        ]

    def run_all(self, symbol: str, df: pd.DataFrame, options: Dict, sentiment: Dict, capital: float = 100000.0) -> List[TradeSignal]:
        signals = []
        for strategy in self.strategies:
            try:
                signal = strategy.analyze(symbol, df, options, sentiment, capital)
                if signal:
                    signals.append(signal)
            except Exception as e:
                print(f"Error in {strategy.__class__.__name__}: {e}")
        return signals

brain = QuantEngine()
