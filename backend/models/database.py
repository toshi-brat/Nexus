import os
from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import settings

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {},
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

class Trade(Base):
    __tablename__ = "trades"
    id          = Column(Integer, primary_key=True, index=True)
    symbol      = Column(String(50), nullable=False)
    trade_type  = Column(String(10), default="BUY")   # BUY / SELL
    instrument  = Column(String(20), default="EQ")     # EQ / CE / PE / FUT
    qty         = Column(Integer, nullable=False)
    entry_price = Column(Float, nullable=False)
    exit_price  = Column(Float)
    stop_loss   = Column(Float)
    target      = Column(Float)
    status      = Column(String(10), default="OPEN")   # OPEN / CLOSED
    entry_time  = Column(DateTime, default=datetime.utcnow)
    exit_time   = Column(DateTime)
    pnl         = Column(Float)
    pnl_pct     = Column(Float)
    setup       = Column(String(100))
    notes       = Column(Text)
    screenshot  = Column(String(255))
    updated_at  = Column(DateTime, default=datetime.utcnow)

class JournalEntry(Base):
    __tablename__ = "journal"
    id            = Column(Integer, primary_key=True, index=True)
    date          = Column(String(10), unique=True)
    mood          = Column(String(20), default="Neutral")
    market_view   = Column(String(20), default="Neutral")
    pre_notes     = Column(Text)
    post_notes    = Column(Text)
    lessons       = Column(Text)
    rules_followed= Column(Boolean, default=True)
    trades_taken  = Column(Integer, default=0)
    winners       = Column(Integer, default=0)
    losers        = Column(Integer, default=0)
    daily_pnl     = Column(Float, default=0.0)
    created_at    = Column(DateTime, default=datetime.utcnow)

class PortfolioHolding(Base):
    __tablename__ = "portfolio"
    id        = Column(Integer, primary_key=True, index=True)
    symbol    = Column(String(50), unique=True, nullable=False)
    qty       = Column(Integer, nullable=False)
    avg_price = Column(Float, nullable=False)
    sector    = Column(String(50))
    instrument= Column(String(20), default="EQ")
    notes     = Column(Text)
    added_at  = Column(DateTime, default=datetime.utcnow)


class ScanResult(Base):
    """Stores every strategy signal found during a full NSE scan run."""
    __tablename__ = "scan_results"
    id               = Column(Integer, primary_key=True, index=True)
    symbol           = Column(String(50), nullable=False, index=True)
    strategy         = Column(String(100), nullable=False, index=True)
    action           = Column(String(10))            # BUY / SELL
    instrument       = Column(String(20))            # OPT / EQ / FUT
    entry_price      = Column(Float)
    target_price     = Column(Float)
    stop_loss        = Column(Float)
    confidence       = Column(Float)                 # 0-100
    kelly_pct        = Column(Float)
    qty              = Column(Integer)
    capital_allocated= Column(Float)
    rationale        = Column(Text)
    timeframe        = Column(String(10))
    days_lookback    = Column(Integer)
    is_index         = Column(Boolean, default=False)
    outcome          = Column(String(10), default="PENDING")  # PENDING / WIN / LOSS / SKIP
    outcome_price    = Column(Float)
    outcome_pnl      = Column(Float)
    scanned_at       = Column(DateTime, default=datetime.utcnow)
    resolved_at      = Column(DateTime)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    os.makedirs(settings.DATABASE_DIR, exist_ok=True)
    Base.metadata.create_all(bind=engine)
