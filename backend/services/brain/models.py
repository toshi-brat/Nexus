"""
Data models for the NEXUS Brain Quant Engine.
"""
from dataclasses import dataclass
from typing import List, Dict, Optional

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
    # New Kelly Sizing fields
    kelly_percentage: float = 0.0
    suggested_qty: int = 50
    capital_allocated: float = 0.0
