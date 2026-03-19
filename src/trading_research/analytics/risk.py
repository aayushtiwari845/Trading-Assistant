from __future__ import annotations

import numpy as np
import pandas as pd


def calculate_risk_metrics(
    price_frame: pd.DataFrame,
    benchmark_frame: pd.DataFrame | None = None,
) -> dict[str, float | None]:
    returns = price_frame["Close"].pct_change().dropna()
    if returns.empty:
        return {
            "volatility_pct": 0.0,
            "beta": None,
            "max_drawdown_pct": 0.0,
            "var_95_pct": 0.0,
            "var_99_pct": 0.0,
            "sharpe_ratio": 0.0,
            "sortino_ratio": 0.0,
        }

    cumulative = (1 + returns).cumprod()
    running_max = cumulative.cummax()
    drawdown = (cumulative / running_max) - 1

    volatility = float(returns.std() * np.sqrt(252) * 100)
    var_95 = float(np.percentile(returns, 5) * 100)
    var_99 = float(np.percentile(returns, 1) * 100)

    risk_free_daily = 0.04 / 252
    excess_returns = returns - risk_free_daily
    sharpe = float((excess_returns.mean() / excess_returns.std()) * np.sqrt(252)) if excess_returns.std() else 0.0

    downside = returns[returns < 0]
    downside_std = float(downside.std() * np.sqrt(252)) if not downside.empty else 0.0
    sortino = float(((returns.mean() * 252) - 0.04) / downside_std) if downside_std else 0.0

    beta = None
    if benchmark_frame is not None and not benchmark_frame.empty:
        benchmark_returns = benchmark_frame["Close"].pct_change().dropna()
        aligned = pd.concat([returns, benchmark_returns], axis=1, join="inner").dropna()
        if len(aligned) > 2 and aligned.iloc[:, 1].var() != 0:
            beta = float(aligned.iloc[:, 0].cov(aligned.iloc[:, 1]) / aligned.iloc[:, 1].var())

    return {
        "volatility_pct": round(volatility, 2),
        "beta": round(beta, 2) if beta is not None else None,
        "max_drawdown_pct": round(float(drawdown.min() * 100), 2),
        "var_95_pct": round(var_95, 2),
        "var_99_pct": round(var_99, 2),
        "sharpe_ratio": round(sharpe, 2),
        "sortino_ratio": round(sortino, 2),
        "average_daily_return_pct": round(float(returns.mean() * 100), 3),
        "average_annual_return_pct": round(float(returns.mean() * 252 * 100), 2),
    }
