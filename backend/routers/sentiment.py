from fastapi import APIRouter
from services.data.scraper import scraper
from services.data.nlp import nlp_engine
import statistics

router = APIRouter(prefix="/sentiment", tags=["Sentiment Hub"])

@router.get("")
async def get_sentiment():
    reddit_posts = scraper.get_reddit_posts(limit=8)
    news_posts = scraper.get_news(limit=12)

    all_posts = reddit_posts + news_posts

    # Calculate global score (-1 to 1) -> mapped to (0 to 100) for Fear/Greed index
    raw_score = nlp_engine.aggregate_score(all_posts)
    # Map [-1, 1] to [0, 100]
    fear_greed_index = int(((raw_score + 1) / 2) * 100)

    # Group by classification
    bullish = len([p for p in all_posts if p['score'] > 0])
    bearish = len([p for p in all_posts if p['score'] < 0])
    neutral = len([p for p in all_posts if p['score'] == 0])

    return {
        "fear_greed_index": fear_greed_index,
        "raw_score": raw_score,
        "distribution": {"bullish": bullish, "bearish": bearish, "neutral": neutral},
        "news": news_posts,
        "social": reddit_posts
    }
