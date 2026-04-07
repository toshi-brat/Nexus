"""Sentiment analyser using VADER + finance keyword lexicon."""
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

_FINANCE_LEXICON = {
    "bullish":3.5,"bearish":-3.5,"rally":2.5,"surge":3.0,"plunge":-3.5,"crash":-4.0,
    "breakout":2.8,"breakdown":-2.8,"support":1.0,"resistance":-1.0,"buyback":2.5,
    "dividend":2.0,"layoffs":-3.0,"default":-4.5,"downgrade":-2.5,"upgrade":2.5,
    "record high":3.5,"52-week high":3.0,"52-week low":-3.0,"fii inflows":2.5,
    "fii outflows":-2.5,"rate hike":-2.0,"rate cut":2.5,"inflation":-1.5,
    "gdp growth":2.0,"recession":-4.0,"profit":.2,"loss":-2.0,"beat":2.0,"miss":-2.0,
}

_sia = SentimentIntensityAnalyzer()
_sia.lexicon.update(_FINANCE_LEXICON)

def score_text(text: str) -> float:
    if not text: return 0.0
    return round(_sia.polarity_scores(text.lower())["compound"], 3)

def analyse_batch(items: list) -> list:
    for item in items:
        s = score_text(item.get("title","") + " " + item.get("body",""))
        item["sentiment"] = s
        item["sentiment_label"] = "POSITIVE" if s>0.05 else "NEGATIVE" if s<-0.05 else "NEUTRAL"
        item["sentiment_color"] = "#00c278" if s>0.05 else "#ff3d57" if s<-0.05 else "#7880a0"
    return items

def aggregate_sentiment(items: list) -> dict:
    if not items:
        return {"score":0,"label":"NEUTRAL","feargreed":50,"positive":0,"negative":0,"neutral":0}
    scores = [i["sentiment"] for i in items]
    avg    = sum(scores)/len(scores)
    pos    = sum(1 for s in scores if s>0.05)
    neg    = sum(1 for s in scores if s<-0.05)
    neu    = len(scores)-pos-neg
    fg     = min(100,max(0,int(50 + avg*50)))
    label  = ("EXTREME GREED" if fg>80 else "GREED" if fg>60 else
              "NEUTRAL" if fg>40 else "FEAR" if fg>20 else "EXTREME FEAR")
    return {"score":round(avg,3),"label":label,"feargreed":fg,
            "positive":pos,"negative":neg,"neutral":neu,"total":len(items)}
