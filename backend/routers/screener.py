from fastapi import APIRouter, Query
from services.brain.screener import screener

router = APIRouter(prefix="/screener", tags=["Stock Screener"])

@router.get("")
async def run_screener(
    min_strength: str = Query("C", pattern="^[ABCabc]$"),
    limit: int = Query(5, ge=1, le=20),
):
    # Scans the top 20 F&O stocks for swing setups
    results = screener.scan_universe()
    threshold_map = {"A": 3, "B": 2, "C": 1}
    normalized = min_strength.upper()
    threshold = threshold_map.get(normalized, 1)
    filtered = [
        row for row in results
        if threshold_map.get(str(row.get("signal_strength", "C")).upper(), 1) >= threshold
    ]
    filtered = filtered[:limit]
    return {
        "status": "success",
        "scanned_count": len(screener.universe),
        "min_strength": normalized,
        "limit": limit,
        "setups_found": len(filtered),
        "shortlist": filtered
    }
