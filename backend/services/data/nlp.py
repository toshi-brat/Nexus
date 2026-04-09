"""
NEXUS - NLP Sentiment Engine
Analyzes text using Financial Lexicons and VADER (if available).
Returns a score between -1.0 (Extreme Fear) and 1.0 (Extreme Greed).
"""
import re

class SentimentEngine:
    def __init__(self):
        # Lightweight Financial Lexicon (Fallback if NLTK/FinBERT is heavy)
        self.bullish_words = {'bull', 'bullish', 'long', 'buy', 'breakout', 'calls', 'call', 'ce', 'profit', 'surge', 'rally', 'up', 'high', 'target', 'support', 'growth', 'upgrade'}
        self.bearish_words = {'bear', 'bearish', 'short', 'sell', 'breakdown', 'puts', 'put', 'pe', 'loss', 'crash', 'drop', 'down', 'low', 'resistance', 'decline', 'downgrade'}

    def analyze_text(self, text: str) -> float:
        if not text: return 0.0

        text = str(text).lower()
        words = set(re.findall(r'\b\w+\b', text))

        bull_count = len(words.intersection(self.bullish_words))
        bear_count = len(words.intersection(self.bearish_words))

        total = bull_count + bear_count
        if total == 0:
            return 0.0

        # Score from -1 to 1
        score = (bull_count - bear_count) / total
        return round(score, 2)

    def aggregate_score(self, items: list) -> float:
        if not items: return 0.0
        scores = [self.analyze_text(item.get('text', '')) for item in items]
        scores = [s for s in scores if s != 0.0] # Ignore neutral noise
        if not scores: return 0.0
        return round(sum(scores) / len(scores), 2)

nlp_engine = SentimentEngine()
