from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models.database import get_db, Trade, JournalEntry
from models.schemas import TradeCreate, TradeUpdate, TradeOut, JournalCreate, JournalOut
from typing import List, Optional
from datetime import datetime

router = APIRouter(prefix="/api/trades", tags=["trades"])

@router.get("", response_model=List[TradeOut])
def get_trades(status:Optional[str]=None, db:Session=Depends(get_db)):
    q=db.query(Trade)
    if status: q=q.filter(Trade.status==status.upper())
    return q.order_by(Trade.entry_time.desc()).all()

@router.post("", response_model=TradeOut)
def create_trade(p:TradeCreate, db:Session=Depends(get_db)):
    t=Trade(**p.model_dump()); db.add(t); db.commit(); db.refresh(t); return t

@router.put("/{tid}", response_model=TradeOut)
def update_trade(tid:int, p:TradeUpdate, db:Session=Depends(get_db)):
    t=db.query(Trade).get(tid)
    if not t: raise HTTPException(404,"Not found")
    for k,v in p.model_dump(exclude_unset=True).items(): setattr(t,k,v)
    if p.exit_price and t.status=="OPEN":
        t.status="CLOSED"; t.exit_time=datetime.utcnow()
        inv=t.entry_price*t.qty; rec=p.exit_price*t.qty
        t.pnl=round((rec-inv) if t.trade_type=="BUY" else (inv-rec),2)
        t.pnl_pct=round(t.pnl/max(1,inv)*100,2)
    t.updated_at=datetime.utcnow(); db.commit(); db.refresh(t); return t

@router.delete("/{tid}")
def del_trade(tid:int, db:Session=Depends(get_db)):
    t=db.query(Trade).get(tid)
    if not t: raise HTTPException(404,"Not found")
    db.delete(t); db.commit(); return {"ok":True}

@router.get("/stats")
def stats(db:Session=Depends(get_db)):
    closed=db.query(Trade).filter(Trade.status=="CLOSED").all()
    if not closed: return {"total":0,"win_rate":0,"total_pnl":0,"avg_win":0,"avg_loss":0,"expectancy":0}
    w=[t for t in closed if (t.pnl or 0)>0]; l=[t for t in closed if (t.pnl or 0)<=0]
    wr=len(w)/len(closed)*100
    aw=sum(t.pnl for t in w)/max(1,len(w)); al=sum(t.pnl for t in l)/max(1,len(l))
    return {"total":len(closed),"winners":len(w),"losers":len(l),"win_rate":round(wr,1),
            "total_pnl":round(sum(t.pnl or 0 for t in closed),2),
            "avg_win":round(aw,2),"avg_loss":round(al,2),
            "expectancy":round(wr/100*aw+(1-wr/100)*al,2)}

@router.get("/journal", response_model=List[JournalOut])
def get_journal(db:Session=Depends(get_db)):
    return db.query(JournalEntry).order_by(JournalEntry.date.desc()).all()

@router.post("/journal", response_model=JournalOut)
def upsert_journal(p:JournalCreate, db:Session=Depends(get_db)):
    e=db.query(JournalEntry).filter_by(date=p.date).first()
    if e:
        for k,v in p.model_dump().items(): setattr(e,k,v)
    else:
        e=JournalEntry(**p.model_dump()); db.add(e)
    db.commit(); db.refresh(e); return e
