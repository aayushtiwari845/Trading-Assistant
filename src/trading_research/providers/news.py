from __future__ import annotations

from datetime import datetime, timezone
import logging
from typing import Any

import requests

from trading_research.config import settings

LOGGER = logging.getLogger(__name__)


def fetch_recent_news(ticker: str, company_name: str | None = None, limit: int = 10) -> list[dict[str, Any]]:
    query = company_name or ticker
    articles: list[dict[str, Any]] = []

    if settings.news_api_key:
        try:
            response = requests.get(
                "https://newsapi.org/v2/everything",
                params={
                    "q": query,
                    "pageSize": limit,
                    "sortBy": "publishedAt",
                    "language": "en",
                    "apiKey": settings.news_api_key,
                },
                timeout=20,
            )
            response.raise_for_status()
            payload = response.json()
            for article in payload.get("articles", []):
                articles.append(
                    {
                        "title": article.get("title", ""),
                        "description": article.get("description", ""),
                        "source": article.get("source", {}).get("name", "NewsAPI"),
                        "published_at": article.get("publishedAt"),
                        "url": article.get("url"),
                    }
                )
        except Exception as exc:  # pragma: no cover - network dependent
            LOGGER.warning("News API fetch failed for %s: %s", ticker, exc)

    if articles:
        return articles[:limit]

    now = datetime.now(timezone.utc).isoformat()
    return [
        {
            "title": f"{ticker} market coverage unavailable in offline mode",
            "description": "Configure NEWS_API_KEY or Finnhub to enrich sentiment analysis with live news.",
            "source": "fallback",
            "published_at": now,
            "url": None,
        }
    ]

