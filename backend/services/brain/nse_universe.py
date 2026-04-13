"""
NEXUS - NSE F&O Eligible Universe
Full list of NSE F&O approved stocks (SEBI circular, ~180 scrips).
Used by the Market Scanner to run strategies across the broadest liquid universe.
"""

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

def get_index_symbols():
    return list(INDEX_SYMBOLS)

def get_fno_stocks():
    return list(FNO_STOCKS)

def get_full_universe():
    return list(ALL_SYMBOLS)
