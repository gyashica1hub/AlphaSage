"""
sentiment.py
------------
News headlines ka sentiment analyze karta hai.

Default: VADER (nltk) - lightweight, fast, free, no GPU/download hassle.
Upgrade path: FinBERT (transformers) - resume mein "fine-tuned FinBERT"
bolna ho toh neeco commented code use karo (finance-specific, zyada accurate,
lekin heavy model download hoga ~400MB).

NewsAPI free tier (100 req/day) se headlines fetch karte hain.
"""

import os
import requests
from textblob import TextBlob

NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")


def fetch_news_headlines(company_name: str, api_key: str = NEWS_API_KEY, page_size: int = 10) -> list:
    """
    NewsAPI free tier se company ke recent headlines fetch karta hai.
    """
    url = "https://newsapi.org/v2/everything"
    params = {
        "q": company_name,
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": page_size,
        "apiKey": api_key
    }
    if not api_key:
        return []
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        articles = response.json().get("articles", [])
        return [a["title"] for a in articles if a.get("title")]
    except requests.RequestException:
        return []


def analyze_sentiment(text: str) -> dict:
    """
    Ek headline/text ka sentiment score deta hai (TextBlob polarity).
    compound score: -1 (bahut negative) se +1 (bahut positive) tak
    """
    polarity = TextBlob(text).sentiment.polarity  # range: -1 to +1
    if polarity >= 0.05:
        label = "Positive"
    elif polarity <= -0.05:
        label = "Negative"
    else:
        label = "Neutral"
    return {"text": text, "compound": round(polarity, 3), "label": label}


def get_stock_sentiment_summary(company_name: str, api_key: str = NEWS_API_KEY) -> dict:
    """
    Company ke saare recent headlines ka average sentiment deta hai -
    yehi dashboard mein "Sentiment Score" ke naam se dikhega.
    """
    headlines = fetch_news_headlines(company_name, api_key)

    if not headlines:
        return {
            "company": company_name,
            "average_score": None,
            "overall_sentiment": "Unavailable",
            "headlines_analyzed": [],
            "source_status": "No news provider configured or no articles returned",
        }

    results = [analyze_sentiment(h) for h in headlines]
    avg_score = round(sum(r["compound"] for r in results) / len(results), 3)

    overall = "Positive" if avg_score >= 0.05 else ("Negative" if avg_score <= -0.05 else "Neutral")

    return {
        "company": company_name,
        "average_score": avg_score,
        "overall_sentiment": overall,
        "headlines_analyzed": results
    }


# ---------------- FinBERT upgrade (optional, heavier) ----------------
# from transformers import BertTokenizer, BertForSequenceClassification
# import torch
#
# tokenizer = BertTokenizer.from_pretrained("ProsusAI/finbert")
# model = BertForSequenceClassification.from_pretrained("ProsusAI/finbert")
#
# def finbert_sentiment(text: str) -> dict:
#     inputs = tokenizer(text, return_tensors="pt", truncation=True)
#     outputs = model(**inputs)
#     probs = torch.nn.functional.softmax(outputs.logits, dim=-1)
#     labels = ["positive", "negative", "neutral"]
#     return {"text": text, "label": labels[probs.argmax()], "confidence": float(probs.max())}


if __name__ == "__main__":
    print(get_stock_sentiment_summary("Reliance Industries"))
