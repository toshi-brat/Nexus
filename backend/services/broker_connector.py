"""Broker connector – Zerodha / Upstox / Dhan with demo fallback."""
import asyncio
from config import settings

DEMO_HOLDINGS = [
    {"symbol":"RELIANCE","qty":10,"avg_price":2820.00,"ltp":2940.50,"instrument":"EQ","sector":"Energy","exchange":"NSE"},
    {"symbol":"TCS","qty":5,"avg_price":3498.00,"ltp":3621.75,"instrument":"EQ","sector":"IT","exchange":"NSE"},
    {"symbol":"HDFC BANK","qty":15,"avg_price":1580.00,"ltp":1641.20,"instrument":"EQ","sector":"Banking","exchange":"NSE"},
    {"symbol":"INFOSYS","qty":8,"avg_price":1860.00,"ltp":1892.40,"instrument":"EQ","sector":"IT","exchange":"NSE"},
    {"symbol":"TITAN","qty":4,"avg_price":3200.00,"ltp":3180.60,"instrument":"EQ","sector":"Consumer","exchange":"NSE"},
    {"symbol":"BAJFINANCE","qty":3,"avg_price":7100.00,"ltp":7248.30,"instrument":"EQ","sector":"NBFC","exchange":"NSE"},
    {"symbol":"NIFTY26APR25000CE","qty":50,"avg_price":120.00,"ltp":85.00,"instrument":"CE","sector":"Index Option","exchange":"NFO"},
    {"symbol":"BANKNIFTY26APR48000PE","qty":25,"avg_price":180.00,"ltp":210.00,"instrument":"PE","sector":"Index Option","exchange":"NFO"},
]

for h in DEMO_HOLDINGS:
    invested = h["avg_price"]*h["qty"]
    current  = h["ltp"]*h["qty"]
    h["invested"]  = round(invested,2)
    h["current"]   = round(current,2)
    h["pnl"]       = round(current-invested,2)
    h["pnl_pct"]   = round((current-invested)/invested*100,2)

class BrokerConnector:
    def __init__(self): self.broker = settings.BROKER if settings.ENABLE_BROKER_SYNC else None
    async def get_holdings(self):
        if not self.broker: return DEMO_HOLDINGS
        try:
            if self.broker=="zerodha": return await self._zerodha_holdings()
            if self.broker=="upstox":  return await self._upstox_holdings()
            if self.broker=="dhan":    return await self._dhan_holdings()
        except Exception as e: print(f"Broker error: {e}")
        return DEMO_HOLDINGS
    async def _zerodha_holdings(self):
        from kiteconnect import KiteConnect
        kite = KiteConnect(api_key=settings.ZERODHA_API_KEY)
        kite.set_access_token(settings.ZERODHA_ACCESS_TOKEN)
        loop=asyncio.get_event_loop()
        raw=await loop.run_in_executor(None,kite.holdings)
        return [{"symbol":h["tradingsymbol"],"qty":h["quantity"],"avg_price":h["average_price"],
                 "ltp":h["last_price"],"exchange":h["exchange"],"instrument":"EQ","sector":"",
                 "invested":round(h["average_price"]*h["quantity"],2),
                 "current":round(h["last_price"]*h["quantity"],2),
                 "pnl":round(h["pnl"],2),"pnl_pct":round(h["pnl"]/max(1,h["average_price"]*h["quantity"])*100,2)} for h in raw]
    async def _upstox_holdings(self):
        import upstox_client
        config=upstox_client.Configuration(access_token=settings.UPSTOX_ACCESS_TOKEN)
        api=upstox_client.PortfolioApi(upstox_client.ApiClient(config))
        loop=asyncio.get_event_loop()
        resp=await loop.run_in_executor(None,lambda: api.get_holdings())
        return [{"symbol":h.trading_symbol,"qty":h.quantity,"avg_price":h.average_price,
                 "ltp":h.last_price,"exchange":h.exchange,"instrument":"EQ","sector":"",
                 "invested":round(h.average_price*h.quantity,2),
                 "current":round(h.last_price*h.quantity,2),
                 "pnl":round(h.pnl,2),"pnl_pct":round(h.pnl_percentage,2)} for h in resp.data]
    async def _dhan_holdings(self):
        from dhanhq import dhanhq
        dhan=dhanhq(settings.DHAN_CLIENT_ID,settings.DHAN_ACCESS_TOKEN)
        loop=asyncio.get_event_loop()
        resp=await loop.run_in_executor(None,dhan.get_holdings)
        return [{"symbol":h["tradingSymbol"],"qty":int(h["totalQty"]),"avg_price":float(h["avgCostPrice"]),
                 "ltp":float(h["lastTradedPrice"]),"exchange":h["exchangeSegment"],"instrument":"EQ","sector":"",
                 "invested":round(float(h["avgCostPrice"])*int(h["totalQty"]),2),
                 "current":round(float(h["lastTradedPrice"])*int(h["totalQty"]),2),
                 "pnl":round(float(h["unrealizedProfit"]),2),"pnl_pct":0.0} for h in resp.get("data",[])]

broker = BrokerConnector()
