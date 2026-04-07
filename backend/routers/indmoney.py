"""
FastAPI router — IndMoney / INDstocks endpoints
Mounted at: /indmoney
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import List, Optional

from services.indmoney_connector import IndMoneyConnector, get_indmoney_client

router = APIRouter(prefix="/indmoney", tags=["IndMoney"])


def indmoney() -> IndMoneyConnector:
    try:
        return get_indmoney_client()
    except Exception:
        raise HTTPException(503, "IndMoney connector unavailable — check INDMONEY_ACCESS_TOKEN in .env")


# ── Auth ──────────────────────────────────────────────────────────────────────

@router.get("/profile", summary="User profile")
async def profile(client: IndMoneyConnector = Depends(indmoney)):
    return await client.get_profile()


@router.get("/funds", summary="Available margin & balance")
async def funds(client: IndMoneyConnector = Depends(indmoney)):
    return await client.get_funds()


# ── Portfolio ─────────────────────────────────────────────────────────────────

@router.get("/portfolio", summary="Full portfolio snapshot (holdings + positions + funds)")
async def portfolio_summary(client: IndMoneyConnector = Depends(indmoney)):
    return await client.get_portfolio_summary()


@router.get("/holdings", summary="Delivery / CNC holdings")
async def holdings(client: IndMoneyConnector = Depends(indmoney)):
    return await client.get_holdings()


@router.get("/positions", summary="Open intraday & F&O positions")
async def positions(client: IndMoneyConnector = Depends(indmoney)):
    return await client.get_positions()


# ── Market Data ───────────────────────────────────────────────────────────────

@router.get("/quotes", summary="Full market quotes")
async def quotes(
    symbols: str = Query(..., example="NSE:RELIANCE,NSE:NIFTY50"),
    client: IndMoneyConnector = Depends(indmoney),
):
    """Comma-separated symbols, e.g. NSE:RELIANCE,NSE:TCS"""
    return await client.get_quotes(symbols.split(","))


@router.get("/ltp", summary="Last Traded Price")
async def ltp(
    symbols: str = Query(..., example="NSE:RELIANCE,NSE:NIFTY50"),
    client: IndMoneyConnector = Depends(indmoney),
):
    return await client.get_ltp(symbols.split(","))


@router.get("/option-chain", summary="Option chain with Greeks")
async def option_chain(
    symbol: str = Query(..., example="NIFTY"),
    expiry: str = Query(..., example="2026-04-28"),
    client: IndMoneyConnector = Depends(indmoney),
):
    return await client.get_option_chain(symbol, expiry)


@router.get("/option-chain/expiries", summary="Available expiry dates")
async def expiry_dates(
    symbol: str = Query(..., example="BANKNIFTY"),
    client: IndMoneyConnector = Depends(indmoney),
):
    return await client.get_expiry_dates(symbol)


@router.get("/historical", summary="Historical OHLCV candles")
async def historical(
    symbol:    str = Query(..., example="NSE:NIFTY50"),
    interval:  str = Query("1d", example="5m"),
    from_date: Optional[str] = Query(None, example="2026-01-01"),
    to_date:   Optional[str] = Query(None, example="2026-04-07"),
    client: IndMoneyConnector = Depends(indmoney),
):
    return await client.get_historical(symbol, interval, from_date, to_date)


# ── Orders ────────────────────────────────────────────────────────────────────

class OrderRequest(BaseModel):
    symbol:           str
    exchange:         str          = "NSE"
    transaction_type: str                  # BUY | SELL
    order_type:       str          = "MARKET"
    quantity:         int
    product:          str          = "INTRADAY"
    limit_price:      Optional[float] = None
    stop_price:       Optional[float] = None


@router.post("/orders", summary="Place an order")
async def place_order(req: OrderRequest, client: IndMoneyConnector = Depends(indmoney)):
    return await client.place_order(**req.dict())


@router.get("/orders", summary="Order book")
async def order_book(client: IndMoneyConnector = Depends(indmoney)):
    return await client.get_order_book()


@router.post("/orders/{order_id}/cancel", summary="Cancel an order")
async def cancel_order(order_id: str, client: IndMoneyConnector = Depends(indmoney)):
    return await client.cancel_order(order_id)


@router.get("/trades", summary="Trade history")
async def trade_history(client: IndMoneyConnector = Depends(indmoney)):
    return await client.get_trade_history()


# ── Smart Orders (GTT / OCO) ──────────────────────────────────────────────────

class GTTRequest(BaseModel):
    symbol:         str
    exchange:       str          = "NSE"
    quantity:       int
    trigger_type:   str          = "oco"
    entry_price:    Optional[float] = None
    target_price:   Optional[float] = None
    stoploss_price: Optional[float] = None


@router.post("/gtt", summary="Place GTT / OCO smart order")
async def place_gtt(req: GTTRequest, client: IndMoneyConnector = Depends(indmoney)):
    return await client.place_gtt(**req.dict())


# ── WebSocket info ────────────────────────────────────────────────────────────

@router.get("/ws-info", summary="WebSocket connection details")
async def ws_info(client: IndMoneyConnector = Depends(indmoney)):
    return {
        "ws_url":     client.ws_url(),
        "subscribe":  {"action": "subscribe", "symbols": ["NSE:RELIANCE", "NSE:NIFTY50"]},
        "heartbeat":  "Send ping every 30 seconds",
        "max_symbols": 100,
    }
