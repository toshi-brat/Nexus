from fastapi import APIRouter
from services.brain.screener import screener

router = APIRouter(prefix="/screener", tags=["Stock Screener"])

@router.get("")
async def run_screener():
    # Scans the top 20 F&O stocks for swing setups
    results = screener.scan_universe()
    return {
        "status": "success",
        "scanned_count": len(screener.universe),
        "setups_found": len(results),
        "shortlist": results
    }
