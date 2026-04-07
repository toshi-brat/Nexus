from fastapi import APIRouter
from services.nse_fetcher import fetch_index_quotes, fetch_option_chain, fetch_top_movers
router = APIRouter(prefix="/api/market", tags=["market"])

@router.get("/indices")
async def get_indices(): return await fetch_index_quotes()

@router.get("/option-chain/{symbol}")
async def get_option_chain(symbol: str = "NIFTY"): return await fetch_option_chain(symbol.upper())

@router.get("/movers")
async def get_movers(): return await fetch_top_movers()
