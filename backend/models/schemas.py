from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class TradeCreate(BaseModel):
    symbol: str; trade_type: str = "BUY"; instrument: str = "EQ"
    qty: int; entry_price: float; stop_loss: Optional[float] = None
    target: Optional[float] = None; setup: Optional[str] = None; notes: Optional[str] = None

class TradeUpdate(BaseModel):
    exit_price: Optional[float] = None; stop_loss: Optional[float] = None
    target: Optional[float] = None; status: Optional[str] = None
    notes: Optional[str] = None; setup: Optional[str] = None

class TradeOut(TradeCreate):
    id: int; exit_price: Optional[float]=None; status: str; entry_time: datetime
    exit_time: Optional[datetime]=None; pnl: Optional[float]=None; pnl_pct: Optional[float]=None
    class Config: from_attributes = True

class JournalCreate(BaseModel):
    date: str; mood: str = "Neutral"; market_view: str = "Neutral"
    pre_notes: Optional[str]=None; post_notes: Optional[str]=None
    lessons: Optional[str]=None; rules_followed: bool = True

class JournalOut(JournalCreate):
    id: int; trades_taken: int=0; winners: int=0; losers: int=0; daily_pnl: float=0.0
    class Config: from_attributes = True

class PortfolioHoldingCreate(BaseModel):
    symbol: str; qty: int; avg_price: float
    sector: Optional[str]=None; instrument: str="EQ"; notes: Optional[str]=None

class PortfolioHoldingOut(PortfolioHoldingCreate):
    id: int
    class Config: from_attributes = True
