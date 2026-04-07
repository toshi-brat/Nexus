"""Reddit monitor via PRAW with demo fallback."""
import asyncio
from config import settings

DEMO_REDDIT = [
    {"sub":"IndianStreetBets","title":"BANKNIFTY weekly options are printing today!","score":847,"comments":124,"sentiment":0.7,"sentiment_label":"POSITIVE","time":"14m ago"},
    {"sub":"IndiaInvestments","title":"FII bought ₹8200 cr today – market may gap up tomorrow","score":432,"comments":67,"sentiment":0.6,"sentiment_label":"POSITIVE","time":"28m ago"},
    {"sub":"Nifty50","title":"Nifty forming perfect cup & handle on daily – target 25,500?","score":318,"comments":89,"sentiment":0.4,"sentiment_label":"POSITIVE","time":"41m ago"},
    {"sub":"IndianStreetBets","title":"Lost 40k on NIFTY PE today. Revenge trading is real.","score":276,"comments":203,"sentiment":-0.8,"sentiment_label":"NEGATIVE","time":"1h ago"},
    {"sub":"IndiaInvestments","title":"My SIP strategy – 18 months in, lessons learnt","score":241,"comments":58,"sentiment":0.3,"sentiment_label":"POSITIVE","time":"1h 20m ago"},
    {"sub":"Nifty50","title":"VIX below 14 – complacency or genuine strength?","score":189,"comments":44,"sentiment":-0.1,"sentiment_label":"NEUTRAL","time":"2h ago"},
    {"sub":"IndianStreetBets","title":"PSU banks looking very strong – BUY or trap?","score":156,"comments":91,"sentiment":0.25,"sentiment_label":"POSITIVE","time":"2h 15m ago"},
    {"sub":"IndiaInvestments","title":"IT sector panic – INFY, TCS both down 5%+ WTD","score":134,"comments":62,"sentiment":-0.6,"sentiment_label":"NEGATIVE","time":"3h ago"},
]

async def fetch_reddit_posts(limit=15):
    if settings.USE_DEMO_DATA or not settings.REDDIT_CLIENT_ID:
        return DEMO_REDDIT[:limit]
    try:
        import praw
        reddit = praw.Reddit(
            client_id=settings.REDDIT_CLIENT_ID,
            client_secret=settings.REDDIT_CLIENT_SECRET,
            user_agent=settings.REDDIT_USER_AGENT,
        )
        posts=[]
        subs = ["IndianStreetBets","IndiaInvestments","Nifty50","IndianStockMarket"]
        loop = asyncio.get_event_loop()
        for sub in subs:
            sub_posts = await loop.run_in_executor(None, lambda s=sub: list(reddit.subreddit(s).hot(limit=5)))
            for p in sub_posts:
                posts.append({"sub":sub,"title":p.title,"score":p.score,"comments":p.num_comments,
                               "time":f"{int((asyncio.get_event_loop().time()-p.created_utc)/60)}m ago",
                               "url":f"https://reddit.com{p.permalink}","sentiment":0.0,"sentiment_label":"NEUTRAL"})
        return posts[:limit]
    except Exception as e:
        print(f"Reddit error: {e}"); return DEMO_REDDIT[:limit]
