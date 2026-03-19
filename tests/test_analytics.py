from trading_research.analytics.risk import calculate_risk_metrics
from trading_research.analytics.sentiment import aggregate_news_sentiment


def test_sentiment_aggregation_returns_distribution():
    result = aggregate_news_sentiment(
        [{"title": "Company beats earnings with strong growth", "description": "", "source": "test"}]
    )
    assert result["overall_sentiment"] == "positive"
    assert "distribution_pct" in result


def test_risk_metrics_shape(sample_price_frame):
    result = calculate_risk_metrics(sample_price_frame)
    assert "volatility_pct" in result
    assert "max_drawdown_pct" in result

