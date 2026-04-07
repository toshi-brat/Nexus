"""
IndMoney (INDstocks) API Connector
Docs   : https://api-docs.indstocks.com
Auth   : Bearer token — expires every 24 h
         Regenerate at: https://www.indstocks.com/app/api-trading
Prereq : Static IP must be whitelisted in your INDstocks dashboard.
"""

import asyncio
import logging
from typing import Optional, Dict, List
from datetime import datetime

import httpx

logger = logging.getLogger(__name__)
BASE_URL = "https://api.indstocks.com"


class IndMoneyConnector:
    """Async REST client for the INDstocks / IndMoney API."""

    def __init__(self, access_token: str):
        self.access_token = access_token
        self._client: Optional[httpx.AsyncClient] = None

    # ── Internal helpers ──────────────────────────────────────────────────────

    @property
    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": self.access_token,
            "Content-Type":  "application/json",
            "API-Version":   "v1",
        }

    async def _session(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=BASE_URL,
                headers=self._headers,
                timeout=10.0,
            )
        return self._client

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def _get(self, path: str, params: Dict = None) -> Dict:
        c = await self._session()
        try:
            r = await c.get(path, params=params)
            r.raise_for_status()
            return r.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"IndMoney GET {path} [{e.response.status_code}]: {e.response.text}")
            raise

    async def _post(self, path: str, body: Dict = None) -> Dict:
        c = await self._session()
        try:
            r = await c.post(path, json=body or {})
            r.raise_for_status()
            return r.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"IndMoney POST {path} [{e.response.status_code}]: {e.response.text}")
            raise

    # ── Profile & Funds ───────────────────────────────────────────────────────

    async def get_profile(self) -> Dict:
        """User profile and account details."""
        return await self._get("/user/profile")

    async def get_funds(self) -> Dict:
        """Available margin, balance, and buying power."""
        return await self._get("/user/funds")

    # ── Portfolio ─────────────────────────────────────────────────────────────

    async def get_holdings(self) -> List[Dict]:
        """Long-term delivery/CNC holdings."""
        data = await self._get("/portfolio/holdings")
        return data.get("data", data) if isinstance(data, dict) else data

    async def get_positions(self) -> List[Dict]:
        """Open intraday and F&O positions."""
        data = await self._get("/portfolio/positions")
        return data.get("data", data) if isinstance(data, dict) else data

    async def get_portfolio_summary(self) -> Dict:
        """Holdings + positions + funds in one aggregated snapshot."""
        holdings, positions, funds = await asyncio.gather(
            self.get_holdings(),
            self.get_positions(),
            self.get_funds(),
        )

        invested = sum(
            float(h.get("avg_price", 0)) * float(h.get("quantity", 0))
            for h in holdings
        )
        current_value = sum(
            float(h.get("ltp", 0)) * float(h.get("quantity", 0))
            for h in holdings
        )
        day_pnl = sum(
            float(p.get("day_pnl", 0)) for p in positions
        )
        pnl = current_value - invested

        return {
            "holdings":  holdings,
            "positions": positions,
            "funds":     funds,
            "summary": {
                "invested_value":  round(invested, 2),
                "current_value":   round(current_value, 2),
                "total_pnl":       round(pnl, 2),
                "total_pnl_pct":   round((pnl / invested * 100) if invested else 0, 2),
                "day_pnl":         round(day_pnl, 2),
                "holdings_count":  len(holdings),
                "open_positions":  len(positions),
            },
            "fetched_at": datetime.now().isoformat(),
        }

    # ── Market Data ───────────────────────────────────────────────────────────

    async def get_quotes(self, symbols: List[str]) -> Dict:
        """Full market depth quote. symbols: ['NSE:RELIANCE', 'NSE:NIFTY50']"""
        return await self._get("/market/quotes/full", {"symbols": ",".join(symbols)})

    async def get_ltp(self, symbols: List[str]) -> Dict:
        """Last Traded Price only (faster, lower overhead)."""
        return await self._get("/market/quotes/ltp", {"symbols": ",".join(symbols)})

    async def get_option_chain(self, symbol: str, expiry: str) -> Dict:
        """
        Option chain with full Greeks.
        symbol : 'NIFTY' | 'BANKNIFTY' | ...
        expiry : 'YYYY-MM-DD'
        """
        return await self._get("/market/option-chain", {"symbol": symbol, "expiry": expiry})

    async def get_historical(
        self,
        symbol: str,
        interval: str = "1d",
        from_date: Optional[str] = None,
        to_date:   Optional[str] = None,
    ) -> List[Dict]:
        """
        OHLCV candles. interval: '1m' | '5m' | '15m' | '1h' | '1d'
        10+ years of history available.
        """
        params = {"symbol": symbol, "interval": interval}
        if from_date: params["from"] = from_date
        if to_date:   params["to"]   = to_date
        data = await self._get("/market/historical", params)
        return data.get("candles", data) if isinstance(data, dict) else data

    async def get_expiry_dates(self, symbol: str) -> List[str]:
        """All available expiry dates for an F&O symbol."""
        data = await self._get("/market/expiry-dates", {"symbol": symbol})
        return data.get("data", data) if isinstance(data, dict) else data

    # ── Orders ────────────────────────────────────────────────────────────────

    async def place_order(
        self,
        symbol:           str,
        exchange:         str,
        transaction_type: str,          # "BUY" | "SELL"
        order_type:       str,          # "MARKET" | "LIMIT" | "STOP_LOSS" | "STOP_LOSS_MARKET"
        quantity:         int,
        product:          str = "INTRADAY",   # "CNC" | "INTRADAY" | "MARGIN"
        limit_price:      Optional[float] = None,
        stop_price:       Optional[float] = None,
    ) -> Dict:
        body = {
            "symbol":           symbol,
            "exchange":         exchange,
            "order_type":       order_type,
            "transaction_type": transaction_type,
            "quantity":         quantity,
            "product":          product,
        }
        if limit_price is not None: body["limit_price"] = limit_price
        if stop_price  is not None: body["stop_price"]  = stop_price
        return await self._post("/order/place", body)

    async def modify_order(self, order_id: str, quantity: int, limit_price: float) -> Dict:
        return await self._post("/order/modify", {"order_id": order_id, "qty": quantity, "limit_price": limit_price})

    async def cancel_order(self, order_id: str) -> Dict:
        return await self._post("/order/cancel", {"order_id": order_id})

    async def get_order_book(self) -> List[Dict]:
        data = await self._get("/order/book")
        return data.get("data", data) if isinstance(data, dict) else data

    async def get_trade_history(self) -> List[Dict]:
        data = await self._get("/trade/history")
        return data.get("data", data) if isinstance(data, dict) else data

    # ── Smart Orders / GTT ────────────────────────────────────────────────────

    async def place_gtt(
        self,
        symbol:          str,
        exchange:        str,
        quantity:        int,
        trigger_type:    str = "oco",          # "single" | "oco"
        entry_price:     Optional[float] = None,
        target_price:    Optional[float] = None,
        stoploss_price:  Optional[float] = None,
    ) -> Dict:
        """One-Cancels-Other GTT — ideal for options trades with SL + target."""
        body = {
            "symbol":       symbol,
            "exchange":     exchange,
            "quantity":     quantity,
            "trigger_type": trigger_type,
        }
        if entry_price    is not None: body["entry_price"]    = entry_price
        if target_price   is not None: body["target_price"]   = target_price
        if stoploss_price is not None: body["stoploss_price"] = stoploss_price
        return await self._post("/gtt/place", body)

    # ── WebSocket ─────────────────────────────────────────────────────────────

    def ws_url(self) -> str:
        """Connect and subscribe to live ticks via WebSocket."""
        return f"wss://api.indstocks.com/ws?token={self.access_token}"


# ─── Module-level singleton ───────────────────────────────────────────────────
_instance: Optional[IndMoneyConnector] = None

def get_indmoney_client(token: Optional[str] = None) -> IndMoneyConnector:
    """Return (or create) the module-level IndMoney connector."""
    global _instance
    if _instance is None or token:
        from config import settings
        _instance = IndMoneyConnector(token or settings.INDMONEY_ACCESS_TOKEN)
    return _instance
