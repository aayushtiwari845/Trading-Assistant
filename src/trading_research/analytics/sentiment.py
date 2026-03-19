from __future__ import annotations

from collections import Counter
from typing import Any

POSITIVE_WORDS = {"beats", "growth", "surge", "upgrade", "strong", "record", "expand"}
NEGATIVE_WORDS = {"miss", "lawsuit", "downgrade", "decline", "risk", "weak", "cut"}


def score_text_sentiment(text: str) -> dict[str, Any]:
    tokens = {token.strip(".,:;!?").lower() for token in text.split()}
    positive = len(tokens & POSITIVE_WORDS)
    negative = len(tokens & NEGATIVE_WORDS)
    if positive > negative:
        sentiment = "positive"
    elif negative > positive:
        sentiment = "negative"
    else:
        sentiment = "neutral"

    total = max(positive + negative, 1)
    return {
        "sentiment": sentiment,
        "confidence": round(max(positive, negative) / total, 2),
    }


def aggregate_news_sentiment(news_articles: list[dict[str, Any]]) -> dict[str, Any]:
    per_article = []
    counter: Counter[str] = Counter()
    confidences = []
    for article in news_articles:
        text = f"{article.get('title', '')} {article.get('description', '')}".strip()
        scored = score_text_sentiment(text)
        scored["title"] = article.get("title", "")
        scored["source"] = article.get("source", "")
        scored["published_at"] = article.get("published_at")
        per_article.append(scored)
        counter[scored["sentiment"]] += 1
        confidences.append(scored["confidence"])

    total = max(sum(counter.values()), 1)
    overall = counter.most_common(1)[0][0] if counter else "neutral"
    return {
        "overall_sentiment": overall,
        "distribution_pct": {key: round(value / total * 100, 2) for key, value in counter.items()},
        "average_confidence": round(sum(confidences) / len(confidences), 2) if confidences else 0.0,
        "articles": per_article,
    }

