"""
NEXUS - NSE F&O Eligible Universe
Full list of NSE F&O approved stocks (SEBI circular, ~180 scrips).
Used by the Market Scanner to run strategies across the broadest liquid universe.
"""

from __future__ import annotations

import csv
import logging
import re
import time
from io import StringIO
from typing import List

import requests

from config import settings

logger = logging.getLogger("nse_universe")

# ──────────────────────────────────────────────────────────────────────────────
# INDICES (Options strategies: OI Gravity, PCR Fade run ONLY on these)
# ──────────────────────────────────────────────────────────────────────────────
INDEX_SYMBOLS = [
    "NIFTY",
    "BANKNIFTY",
    "FINNIFTY",
    "MIDCPNIFTY",
]

# ──────────────────────────────────────────────────────────────────────────────
# NSE F&O ELIGIBLE STOCKS (full SEBI-approved list as of April 2026)
# Volatility Breakout, Stat-Arb, Sentiment Convergence run on ALL of these.
# ──────────────────────────────────────────────────────────────────────────────
FNO_STOCKS = [
    # Nifty 50 core
    "RELIANCE", "HDFCBANK", "ICICIBANK", "INFY", "TCS",
    "HINDUNILVR", "SBIN", "BHARTIARTL", "BAJFINANCE", "KOTAKBANK",
    "LT", "AXISBANK", "ASIANPAINT", "MARUTI", "TITAN",
    "SUNPHARMA", "ULTRACEMCO", "WIPRO", "HCLTECH", "NTPC",
    "POWERGRID", "ONGC", "COALINDIA", "BPCL", "IOC",
    "TATAMOTORS", "M&M", "TECHM", "BAJAJFINSV", "ADANIPORTS",
    "GRASIM", "JSWSTEEL", "TATASTEEL", "HINDALCO", "DRREDDY",
    "CIPLA", "EICHERMOT", "HEROMOTOCO", "DIVISLAB", "NESTLEIND",
    "BRITANNIA", "TATACONSUM", "LTIM", "INDUSINDBK", "APOLLOHOSP",

    # Nifty Next 50 / Midcap F&O
    "ADANIENT", "ADANIGREEN", "ADANIPOWER", "ADANITRANS",
    "AMBUJACEM", "AUROPHARMA", "BANDHANBNK", "BANKBARODA",
    "BERGEPAINT", "BIOCON", "BOSCHLTD", "CANBK",
    "CHOLAFIN", "COLPAL", "CONCOR", "CUMMINSIND",
    "DABUR", "DLF", "ESCORTS", "FEDERALBNK",
    "GAIL", "GMRAIRPORT", "GODREJCP", "GODREJPROP",
    "HDFCAMC", "HDFCLIFE", "HINDPETRO", "IDFCFIRSTB",
    "IGL", "INDHOTEL", "INDUSTOWER", "INFY",
    "IRCTC", "ITC", "JINDALSTEL", "JUBLFOOD",
    "L&TFH", "LICHSGFIN", "LUPIN", "MANAPPURAM",
    "MARICO", "MFSL", "MPHASIS", "MRF",
    "MUTHOOTFIN", "NAUKRI", "NAVINFLUOR", "NMDC",
    "OBEROIRLTY", "OFSS", "PAGEIND", "PEL",
    "PERSISTENT", "PETRONET", "PFC", "PIDILITIND",
    "PIIND", "PNB", "POLYCAB", "RAMCOCEM",
    "REC", "SAIL", "SBICARD", "SBILIFE",
    "SIEMENS", "SRF", "STARTCART", "SUDARSCHEM",
    "SUPREMEIND", "TATACOMM", "TATAELXSI", "TATAPOW",
    "TRENT", "TVSMOTOR", "UBL", "UCOBANK",
    "UNIONBANK", "UPL", "VEDL", "VOLTAS",
    "WHIRLPOOL", "ZEEL", "ZOMATO", "NYKAA",
    "PAYTM", "POLICYBZR", "DELHIVERY", "MAPMYINDIA",

    # PSU Banks & Financials
    "CANARABANK", "INDIANB", "PNB", "BANKBARODA",
    "MAHABANK", "IOB", "UCOBANK",

    # Pharma & Healthcare
    "ALKEM", "TORNTPHARM", "IPCA", "AJANTPHARM",
    "ABBOTINDIA", "PFIZER", "SANOFI", "GLAXO",

    # IT Pack
    "COFORGE", "LTTS", "MASTEK", "NIITTECH",
    "HEXAWARE", "KPIT", "SONACOMS",

    # Auto Ancillary
    "MOTHERSON", "BALKRISIND", "APOLLOTYRE",
    "MINDA", "ENDURANCE", "EXIDEIND",

    # Infra & Capital Goods
    "BHEL", "THERMAX", "ABCAPITAL",
    "CESC", "TORNTPOWER", "TATAPOWER",

    # Consumer / FMCG
    "VBL", "MCDOWELL-N", "RADICO", "UNITDSPR",
    "EMAMILTD", "JUBLPHARMA",

    # Metals & Mining
    "HINDCOPPER", "NATIONALUM", "MOIL",

    # Real Estate
    "PHOENIXLTD", "PRESTIGE", "BRIGADE",

    # Specialty Chemicals
    "DEEPAKNTR", "AAPL", "ATUL", "VINATIORGA",
    "CLEAN", "FINEORG",
]

# De-duplicate while preserving order
seen = set()
_deduped = []
for s in FNO_STOCKS:
    if s not in seen:
        seen.add(s)
        _deduped.append(s)
FNO_STOCKS = _deduped

# Full combined universe
ALL_SYMBOLS = INDEX_SYMBOLS + FNO_STOCKS

_DYNAMIC_CACHE: List[str] = []
_CACHE_TS: float = 0.0
_CACHE_TTL_SECONDS = 60 * 60 * 6  # 6h


def _download_nse_equity_symbols() -> List[str]:
    """
    Fetch the full NSE equity universe from INDstocks instruments master.
    Requires INDMONEY_ACCESS_TOKEN.
    """
    token = settings.INDMONEY_ACCESS_TOKEN
    if not token:
        raise RuntimeError("INDMONEY_ACCESS_TOKEN missing for dynamic NSE universe fetch")

    res = requests.get(
        "https://api.indstocks.com/market/instruments",
        headers={"Authorization": token, "API-Version": "v1"},
        params={"source": "equity"},
        timeout=20,
    )
    res.raise_for_status()

    rows = list(csv.DictReader(StringIO(res.text)))
    symbols: List[str] = []
    seen = set()
    # Keep NSE trading symbols that are practically usable in strategy scans.
    allowed_symbol = re.compile(r"^[A-Z0-9&\-.]{1,20}$")
    for row in rows:
        exch = (row.get("EXCH") or "").strip().upper()
        series = (row.get("SERIES") or "").strip().upper()
        symbol = (row.get("TRADING_SYMBOL") or row.get("SYMBOL_NAME") or "").strip().upper()
        if exch != "NSE" or not symbol:
            continue
        # Strictly focus on active equity series for cleaner scanner universe.
        if series not in {"EQ", "BE", "BZ"}:
            continue
        # Drop verbose company-name style entries and malformed symbols.
        if " " in symbol or not allowed_symbol.match(symbol):
            continue
        if symbol in seen:
            continue
        seen.add(symbol)
        symbols.append(symbol)
    return symbols

def get_index_symbols():
    return list(INDEX_SYMBOLS)

def get_fno_stocks():
    return list(FNO_STOCKS)

def get_full_universe():
    return list(ALL_SYMBOLS)


def get_nse_equities(refresh: bool = False) -> List[str]:
    """
    Return dynamic full NSE equity universe with cache + fallback.
    """
    global _DYNAMIC_CACHE, _CACHE_TS

    now = time.time()
    if not refresh and _DYNAMIC_CACHE and (now - _CACHE_TS) < _CACHE_TTL_SECONDS:
        return list(_DYNAMIC_CACHE)

    try:
        dynamic = _download_nse_equity_symbols()
        if dynamic:
            _DYNAMIC_CACHE = dynamic
            _CACHE_TS = now
            logger.info("Loaded dynamic NSE equity universe: %s symbols", len(dynamic))
            return list(dynamic)
    except Exception as exc:
        logger.warning("Dynamic NSE universe fetch failed. Falling back to static F&O list. Error: %s", exc)

    # Safe fallback if live instrument dump is unavailable.
    return get_fno_stocks()
