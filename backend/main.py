"""
NEXUS Trading System — FastAPI Backend
Run: python main.py
"""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from models.database import create_tables
from routers import market, portfolio, sentiment, trades
from routers.brain import router as brain_router
from routers.indmoney import router as indmoney_router
from routers.screener import router as screener_router

app = FastAPI(
    title=settings.APP_NAME,
    description="Algorithmic trading intelligence platform — IndMoney + NSE + Sentiment",
    version="1.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(market.router,    prefix="/api/v1")
app.include_router(portfolio.router, prefix="/api/v1")
app.include_router(sentiment.router, prefix="/api/v1")
app.include_router(trades.router,    prefix="/api/v1")
app.include_router(indmoney_router,  prefix="/api/v1")
app.include_router(brain_router,     prefix="/api/v1")
app.include_router(screener_router,  prefix="/api/v1")


@app.on_event("startup")
async def startup():
    create_tables()


@app.get("/health")
async def health():
    return {"status": "ok", "app": settings.APP_NAME}


if __name__ == "__main__":
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
