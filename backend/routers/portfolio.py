from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from models.database import get_db, PortfolioHolding
from models.schemas import PortfolioHoldingCreate, PortfolioHoldingOut
from services.broker_connector import broker
from typing import List

router = APIRouter(prefix="/api/portfolio", tags=["portfolio"])

@router.get("/live")
async def live():
    h = await broker.get_holdings()
    inv = sum(x["invested"] for x in h)
    cur = sum(x["current"] for x in h)
    return {"holdings":h,"summary":{"invested":round(inv,2),"current":round(cur,2),
            "pnl":round(cur-inv,2),"pnl_pct":round((cur-inv)/max(1,inv)*100,2)}}

@router.get("/holdings", response_model=List[PortfolioHoldingOut])
def get_holdings(db: Session = Depends(get_db)): return db.query(PortfolioHolding).all()

@router.post("/holdings", response_model=PortfolioHoldingOut)
def add_holding(p: PortfolioHoldingCreate, db: Session = Depends(get_db)):
    e = db.query(PortfolioHolding).filter_by(symbol=p.symbol.upper()).first()
    if e:
        for k,v in p.model_dump().items(): setattr(e,k,v)
        db.commit(); db.refresh(e); return e
    h = PortfolioHolding(**p.model_dump(), symbol=p.symbol.upper())
    db.add(h); db.commit(); db.refresh(h); return h

@router.delete("/holdings/{symbol}")
def del_holding(symbol:str, db:Session=Depends(get_db)):
    h=db.query(PortfolioHolding).filter_by(symbol=symbol.upper()).first()
    if h: db.delete(h); db.commit()
    return {"ok":True}
