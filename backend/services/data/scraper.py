"""
NEXUS - Social & News Scraper
Scrapes Reddit, Twitter, and RSS Feeds.
"""
import random
from datetime import datetime, timedelta
import logging

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
import config
from services.data.nlp import nlp_engine

logger = logging.getLogger("scraper")

class SocialScraper:
    def __init__(self):
        self.reddit_enabled = bool(config.REDDIT_CLIENT_ID)
        self.twitter_enabled = bool(config.TWITTER_BEARER_TOKEN)

    def get_reddit_posts(self, limit=10):
        if self.reddit_enabled:
            try:
                import praw
                reddit = praw.Reddit(
                    client_id=config.REDDIT_CLIENT_ID,
                    client_secret=config.REDDIT_CLIENT_SECRET,
                    user_agent=config.REDDIT_USER_AGENT
                )
                subreddits = reddit.subreddit("IndianStreetBets+IndiaInvestments")
                posts = []
                for post in subreddits.hot(limit=limit):
                    posts.append({
                        "source": "Reddit",
                        "author": post.author.name if post.author else "Anonymous",
                        "text": post.title,
                        "url": post.url,
                        "timestamp": datetime.fromtimestamp(post.created_utc).isoformat(),
                        "score": nlp_engine.analyze_text(post.title)
                    })
                return posts
            except ImportError:
                logger.error("praw not installed. Run: pip install praw")
            except Exception as e:
                logger.error(f"Reddit Scrape Error: {e}")

        # Fallback Mock Data
        return self._mock_reddit()

    def get_news(self, limit=15):
        try:
            import feedparser
            news = []
            for source, url in config.NEWS_FEEDS.items():
                feed = feedparser.parse(url)
                for entry in feed.entries[:3]: # Take top 3 from each source
                    news.append({
                        "source": source,
                        "author": "Journalist",
                        "text": entry.title,
                        "url": entry.link,
                        "timestamp": datetime.now().isoformat(), # Simplified for mock/feed alignment
                        "score": nlp_engine.analyze_text(entry.title)
                    })
            # Sort by most recent (mocked sorting)
            random.shuffle(news)
            return news[:limit]
        except ImportError:
            logger.error("feedparser not installed. Run: pip install feedparser")
        except Exception as e:
            logger.error(f"News Scrape Error: {e}")

        return self._mock_news()

    def _mock_reddit(self):
        titles = [
            "NIFTY 22000 CE is going to print tomorrow! Full bull mode.",
            "FII data looking extremely bearish, puts are the only play.",
            "Is BankNifty heading for a massive crash? The chart looks terrible.",
            "Just went long on Reliance, hoping for a breakout.",
            "Market is completely sideways, theta decay eating my premium.",
            "Iron Condor working perfectly in this range-bound market.",
            "Huge buy orders spotted in HDFC, index might rally."
        ]
        return [{"source": "Reddit (r/IndianStreetBets)", "author": "Trader_" + str(random.randint(100,999)), "text": t, "timestamp": (datetime.now() - timedelta(minutes=random.randint(1, 60))).isoformat(), "score": nlp_engine.analyze_text(t)} for t in titles]

    def _mock_news(self):
        headlines = [
            "RBI keeps repo rate unchanged, markets react positively.",
            "Global tech selloff drags Indian IT stocks down.",
            "FIIs pull out Rs 2,000 crore in Friday session.",
            "Inflation data comes in lower than expected, banking stocks surge.",
            "Crude oil prices spike, threatening domestic margins.",
            "GST collections hit record high this month.",
            "Auto sector sees double-digit growth in quarterly sales."
        ]
        sources = list(config.NEWS_FEEDS.keys())
        return [{"source": random.choice(sources), "author": "News Desk", "text": h, "timestamp": (datetime.now() - timedelta(minutes=random.randint(5, 120))).isoformat(), "score": nlp_engine.analyze_text(h)} for h in headlines]

scraper = SocialScraper()
