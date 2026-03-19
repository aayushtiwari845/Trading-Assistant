from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import logging
from typing import Any

import pandas as pd

LOGGER = logging.getLogger(__name__)

try:
    import yfinance as yf
except ImportError:  # pragma: no cover
    yf = None


@dataclass
class MarketDataBundle:
    price_history: list[dict[str, Any]]
    company_info: dict[str, Any]
    financials: dict[str, Any]
    analyst_ratings: dict[str, Any]


def _fallback_history(days: int = 365) -> list[dict[str, Any]]:
    now = datetime.now(timezone.utc)
    rows: list[dict[str, Any]] = []
    base_price = 100.0
    for offset in range(days):
        date = now - timedelta(days=(days - offset))
        close = round(base_price + offset * 0.05, 2)
        rows.append(
            {
                "Date": date.isoformat(),
                "Open": close - 0.7,
                "High": close + 1.0,
                "Low": close - 1.1,
                "Close": close,
                "Volume": 1_000_000 + offset * 1000,
            }
        )
    return rows


def fetch_market_data(
    ticker: str,
    period: str = "1y",
    include_info: bool = True,
    include_financials: bool = True,
    include_analyst_ratings: bool = True,
) -> MarketDataBundle:
    if not yf:
        LOGGER.warning("yfinance unavailable, using fallback market data for %s", ticker)
        return MarketDataBundle(
            price_history=_fallback_history(),
            company_info={"symbol": ticker, "longName": ticker, "sector": "Unknown", "industry": "Unknown"},
            financials={},
            analyst_ratings={"consensus": "N/A", "recent_ratings": []},
        )
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period)
        if hist.empty:
            history_rows = _fallback_history()
        else:
            hist = hist.reset_index()
            hist["Date"] = hist["Date"].astype(str)
            history_rows = hist.to_dict(orient="records")

        financials = {}
        if include_financials:
            financials = {
                "income_statement": getattr(stock, "financials", pd.DataFrame()).fillna(0).to_dict(),
                "balance_sheet": getattr(stock, "balance_sheet", pd.DataFrame()).fillna(0).to_dict(),
                "cash_flow": getattr(stock, "cashflow", pd.DataFrame()).fillna(0).to_dict(),
                "quarterly_financials": getattr(stock, "quarterly_financials", pd.DataFrame()).fillna(0).to_dict(),
            }

        recent_ratings = []
        consensus = "N/A"
        if include_analyst_ratings:
            recommendations = getattr(stock, "recommendations", None)
            if recommendations is not None and not recommendations.empty:
                tail = recommendations.tail(10).reset_index().astype(str)
                recent_ratings = tail.to_dict(orient="records")
                if "To Grade" in recommendations.columns:
                    consensus = recommendations["To Grade"].mode().iloc[0]

        company_info = {"symbol": ticker}
        if include_info:
            company_info = getattr(stock, "info", {}) or {"symbol": ticker}

        return MarketDataBundle(
            price_history=history_rows,
            company_info=company_info,
            financials=financials,
            analyst_ratings={
                "consensus": consensus,
                "recent_ratings": recent_ratings,
                "num_analysts": len(recent_ratings),
            },
        )
    except Exception as exc:  # pragma: no cover - network dependent
        LOGGER.warning("Market data lookup failed for %s: %s", ticker, exc)
        return MarketDataBundle(
            price_history=_fallback_history(),
            company_info={"symbol": ticker, "longName": ticker, "sector": "Unknown", "industry": "Unknown"},
            financials={},
            analyst_ratings={"consensus": "N/A", "recent_ratings": [], "num_analysts": 0},
        )


def price_history_frame(price_history: list[dict[str, Any]]) -> pd.DataFrame:
    frame = pd.DataFrame(price_history)
    if frame.empty:
        frame = pd.DataFrame(_fallback_history())
    if "Date" in frame.columns:
        frame["Date"] = pd.to_datetime(frame["Date"], errors="coerce", utc=True)
        frame = frame.sort_values("Date")
    for column in ["Open", "High", "Low", "Close", "Volume"]:
        if column in frame.columns:
            frame[column] = pd.to_numeric(frame[column], errors="coerce")
    return frame.reset_index(drop=True)
