"""NEXUS Trading System – FastAPI Backend
Run: python main.py   →  http://localhost:8000/docs
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import asyncio, sys, os
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))
from config import settings
from models.database import create_tables
from routers import market, sentiment, portfolio, trades
from services.nse_fetcher import fetch_index_quotes

app = FastAPI(title="NEXUS Trading API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.on_event("startup")
async def startup():
    os.makedirs("data", exist_ok=True)
    create_tables()
    print(f"\n⚡ NEXUS Backend ready — http://{settings.HOST}:{settings.PORT}/docs\n")

app.include_router(market.router)
app.include_router(sentiment.router)
app.include_router(portfolio.router)
app.include_router(trades.router)

@app.get("/api/health")
async def health(): return {"status":"ok","time":datetime.utcnow().isoformat()}

class WSManager:
    def __init__(self): self.conns=[]
    async def connect(self,ws): await ws.accept(); self.conns.append(ws)
    def disconnect(self,ws):
        if ws in self.conns: self.conns.remove(ws)
    async def broadcast(self,data):
        dead=[]
        for ws in self.conns:
            try: await ws.send_json(data)
            except: dead.append(ws)
        for ws in dead: self.disconnect(ws)

mgr = WSManager()

@app.websocket("/ws/market")
async def ws_market(ws:WebSocket):
    await mgr.connect(ws)
    try:
        while True:
            data = await fetch_index_quotes()
            await ws.send_json({"type":"indices","data":data,"ts":datetime.utcnow().isoformat()})
            await asyncio.sleep(3)
    except WebSocketDisconnect:
        mgr.disconnect(ws)

if __name__=="__main__":
    import uvicorn
    uvicorn.run("main:app",host=settings.HOST,port=settings.PORT,reload=settings.DEBUG)
