"""NSE data fetcher using nsepython + demo fallback."""
import asyncio, random, math
from datetime import datetime
from config import settings

def _demo_indices():
    t = datetime.now()
    s = t.hour*3600+t.minute*60+t.second
    def w(base,amp): return round(base + amp*math.sin(s/3600*math.pi), 2)
    return {
        "NIFTY 50":    {"last":w(24847,120),"change":198.45, "pct":0.81,"open":24649,"high":24918,"low":24632,"prev":24649},
        "SENSEX":      {"last":w(81920,400),"change":587.20, "pct":0.72,"open":81333,"high":82050,"low":81280,"prev":81333},
        "BANKNIFTY":   {"last":w(53218,200),"change":-128.70,"pct":-0.24,"open":53347,"high":53480,"low":53050,"prev":53347},
        "NIFTY IT":    {"last":w(38240,180),"change":445.60, "pct":1.18,"open":37794,"high":38350,"low":37720,"prev":37794},
        "NIFTY MIDCAP":{"last":w(56100,250),"change":310.40, "pct":0.56,"open":55789,"high":56280,"low":55680,"prev":55789},
        "VIX":         {"last":w(13.42,0.8),"change":-0.38, "pct":-2.75,"open":13.80,"high":14.20,"low":13.10,"prev":13.80},
        "GOLD":        {"last":w(72450,200),"change":380.00, "pct":0.53,"open":72070,"high":72600,"low":72000,"prev":72070},
        "USD/INR":     {"last":w(83.84,0.2),"change":0.12,  "pct":0.14, "open":83.72,"high":83.95,"low":83.65,"prev":83.72},
    }

def _demo_movers():
    gainers = [
        {"symbol":"RELIANCE","ltp":2940.50,"change":61.30,"pct":2.13,"vol":"3.2M"},
        {"symbol":"TCS","ltp":3621.75,"change":63.40,"pct":1.78,"vol":"1.1M"},
        {"symbol":"HDFC BANK","ltp":1641.20,"change":22.60,"pct":1.40,"vol":"5.8M"},
        {"symbol":"INFY","ltp":1892.40,"change":24.80,"pct":1.33,"vol":"2.4M"},
        {"symbol":"TITAN","ltp":3180.60,"change":39.40,"pct":1.25,"vol":"0.9M"},
        {"symbol":"BAJFINANCE","ltp":7248.30,"change":84.20,"pct":1.18,"vol":"1.3M"},
        {"symbol":"WIPRO","ltp":476.80,"change":5.20,"pct":1.10,"vol":"3.7M"},
    ]
    losers = [
        {"symbol":"COALINDIA","ltp":438.10,"change":-8.20,"pct":-1.84,"vol":"4.1M"},
        {"symbol":"ONGC","ltp":264.30,"change":-3.80,"pct":-1.42,"vol":"6.2M"},
        {"symbol":"NTPC","ltp":362.40,"change":-4.40,"pct":-1.20,"vol":"3.9M"},
        {"symbol":"POWERGRID","ltp":294.60,"change":-2.70,"pct":-0.91,"vol":"2.1M"},
        {"symbol":"BPCL","ltp":312.80,"change":-2.70,"pct":-0.86,"vol":"3.3M"},
        {"symbol":"HINDUNILVR","ltp":2382.10,"change":-18.40,"pct":-0.77,"vol":"0.8M"},
        {"symbol":"SUNPHARMA","ltp":1628.50,"change":-11.20,"pct":-0.68,"vol":"1.4M"},
    ]
    for g in gainers: g["ltp"] = round(g["ltp"]*(1+random.uniform(-0.002,0.002)),2)
    for l in losers:  l["ltp"] = round(l["ltp"]*(1+random.uniform(-0.002,0.002)),2)
    return {"gainers":gainers,"losers":losers}

def _demo_option_chain(symbol="NIFTY"):
    spot = 24847 if symbol=="NIFTY" else 53218
    strikes=[spot-500,spot-250,spot,spot+250,spot+500]
    chain=[]
    for s in strikes:
        itm = s < spot
        chain.append({
            "strike":s,
            "ce_oi":random.randint(50,500)*100,"ce_chg_oi":random.randint(-50,150)*100,
            "ce_ltp":round(max(0.5, spot-s+random.uniform(-20,20)) if itm else random.uniform(10,80),2),
            "ce_iv":round(random.uniform(12,22),2),"ce_vol":random.randint(1000,50000),
            "ce_delta":round(random.uniform(0.4,0.9) if itm else random.uniform(0.1,0.4),2),
            "pe_oi":random.randint(50,500)*100,"pe_chg_oi":random.randint(-50,150)*100,
            "pe_ltp":round(max(0.5, s-spot+random.uniform(-20,20)) if not itm else random.uniform(10,80),2),
            "pe_iv":round(random.uniform(12,22),2),"pe_vol":random.randint(1000,50000),
            "pe_delta":round(random.uniform(-0.9,-0.4) if not itm else random.uniform(-0.4,-0.1),2),
        })
    return {"symbol":symbol,"spot":spot,"expiry":"26-APR-2026","chain":chain,
            "pcr":round(random.uniform(0.8,1.4),2),"max_pain":spot}

async def fetch_index_quotes():
    if settings.USE_DEMO_DATA: return _demo_indices()
    try:
        import nsepython as nse
        loop = asyncio.get_event_loop()
        data = await loop.run_in_executor(None, nse.nse_get_all_indices)
        result={}
        for idx in data.get("data",[]):
            name=idx["index"]
            result[name]={"last":idx["last"],"change":idx["change"],"pct":idx["percentChange"],
                          "open":idx["open"],"high":idx["high"],"low":idx["low"],"prev":idx["previousClose"]}
        return result
    except Exception as e:
        print(f"NSE fetch error: {e}"); return _demo_indices()

async def fetch_option_chain(symbol="NIFTY"):
    if settings.USE_DEMO_DATA: return _demo_option_chain(symbol)
    try:
        import nsepython as nse
        loop = asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: nse.expiry_list(symbol,"list"))
        return data
    except Exception as e:
        print(f"Option chain error: {e}"); return _demo_option_chain(symbol)

async def fetch_top_movers():
    if settings.USE_DEMO_DATA: return _demo_movers()
    try:
        import nsepython as nse
        loop = asyncio.get_event_loop()
        gainers = await loop.run_in_executor(None, lambda: nse.nse_get_top_gainers())
        losers  = await loop.run_in_executor(None, lambda: nse.nse_get_top_losers())
        return {"gainers": gainers[:7], "losers": losers[:7]}
    except Exception as e:
        print(f"Movers error: {e}"); return _demo_movers()
