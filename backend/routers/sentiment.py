from fastapi import APIRouter
from services.news_scraper import fetch_all_news
from services.sentiment_analyzer import analyse_batch, aggregate_sentiment
from services.social_monitor import fetch_reddit_posts
import asyncio
from datetime import datetime

router = APIRouter(prefix="/api/sentiment", tags=["sentiment"])
_cache = {"updated": None, "data": None}

@router.get("")
async def get_sentiment():
    from datetime import datetime as dt
    now = dt.utcnow()
    if _cache["data"] and _cache["updated"] and (now-_cache["updated"]).seconds < 300:
        return _cache["data"]
    news, reddit = await asyncio.gather(fetch_all_news(5), fetch_reddit_posts(15))
    all_items = analyse_batch(news) + analyse_batch(reddit)
    summary = aggregate_sentiment(all_items)
    summary["news"] = analyse_batch(news)[:15]
    summary["reddit"] = analyse_batch(reddit)[:10]
    summary["updated"] = now.isoformat()
    _cache["data"] = summary; _cache["updated"] = now
    return summary
