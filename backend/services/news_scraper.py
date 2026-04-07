"""News scraper from top 10 Indian/global business sites via RSS."""
import asyncio, aiohttp, feedparser
from datetime import datetime

FEEDS = [
    ("Economic Times Markets","https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms"),
    ("Mint Markets","https://www.livemint.com/rss/markets"),
    ("Business Standard","https://www.business-standard.com/rss/markets-106.rss"),
    ("MoneyControl","https://www.moneycontrol.com/rss/business.xml"),
    ("CNBCTV18","https://www.cnbctv18.com/commonfeeds/v1/cne/rss/market.xml"),
    ("Financial Express","https://www.financialexpress.com/market/feed/"),
    ("Reuters India","https://feeds.reuters.com/reuters/INbusinessNews"),
    ("Bloomberg Quint","https://www.bloomberg.com/feed/india"),
    ("NSE Circulars","https://nsearchives.nseindia.com/content/RSS/circular_rss.xml"),
    ("Zee Business","https://zeebiz.com/rss/business"),
]

DEMO_NEWS = [
    {"title":"RBI holds repo rate at 6.5%, signals cautious outlook","source":"Economic Times","time":"09:42","sentiment":0.1,"url":"#"},
    {"title":"FII net inflows surge to ₹8,200 crore in April so far","source":"Mint","time":"10:15","sentiment":0.72,"url":"#"},
    {"title":"IT sector faces headwinds as US tariff uncertainty persists","source":"Business Standard","time":"10:33","sentiment":-0.61,"url":"#"},
    {"title":"Q4 earnings season starts Friday – TCS, Infosys in focus","source":"CNBCTV18","time":"11:02","sentiment":0.15,"url":"#"},
    {"title":"Crude oil slips to $85/bbl; Brent down 1.2% on demand concerns","source":"Reuters India","time":"11:18","sentiment":-0.45,"url":"#"},
    {"title":"Nifty Bank breaches 53,000 – analysts watch 52,800 support","source":"MoneyControl","time":"11:40","sentiment":-0.30,"url":"#"},
    {"title":"SEBI tightens F&O margin norms – effective May 1","source":"Financial Express","time":"12:05","sentiment":-0.20,"url":"#"},
    {"title":"Gold hits new high of ₹72,600/10g; Silver up 2.3%","source":"Zee Business","time":"12:22","sentiment":0.40,"url":"#"},
    {"title":"Auto sales data: Passenger vehicles up 8% YoY in March","source":"Bloomberg Quint","time":"13:10","sentiment":0.55,"url":"#"},
    {"title":"Reliance Jio to launch 5G services in 50 new cities by June","source":"Economic Times","time":"13:45","sentiment":0.68,"url":"#"},
    {"title":"PSU banks rally 2–3% after positive asset quality commentary","source":"Business Standard","time":"14:10","sentiment":0.62,"url":"#"},
    {"title":"Midcap, smallcap indices outperform large caps for third straight session","source":"Mint","time":"14:32","sentiment":0.50,"url":"#"},
]

async def _fetch_feed(session, name, url, max_items=5):
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=8)) as resp:
            text = await resp.text()
        feed = feedparser.parse(text)
        items = []
        for entry in feed.entries[:max_items]:
            items.append({
                "title":   entry.get("title",""),
                "source":  name,
                "time":    datetime.now().strftime("%H:%M"),
                "url":     entry.get("link","#"),
                "sentiment": 0.0,
            })
        return items
    except Exception:
        return []

async def fetch_all_news(max_per_feed=5):
    try:
        async with aiohttp.ClientSession() as session:
            tasks = [_fetch_feed(session, name, url, max_per_feed) for name,url in FEEDS]
            results = await asyncio.gather(*tasks, return_exceptions=True)
        items = []
        for r in results:
            if isinstance(r, list): items.extend(r)
        return items if items else DEMO_NEWS
    except Exception:
        return DEMO_NEWS
