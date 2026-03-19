from __future__ import annotations

import pandas as pd


def calculate_technical_indicators(price_frame: pd.DataFrame) -> dict[str, float | str]:
    df = price_frame.copy()
    df["SMA_20"] = df["Close"].rolling(20).mean()
    df["SMA_50"] = df["Close"].rolling(50).mean()
    df["SMA_200"] = df["Close"].rolling(200).mean()
    df["EMA_12"] = df["Close"].ewm(span=12, adjust=False).mean()
    df["EMA_26"] = df["Close"].ewm(span=26, adjust=False).mean()

    delta = df["Close"].diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()
    rs = gain / loss.replace(0, pd.NA)
    df["RSI"] = 100 - (100 / (1 + rs))

    df["MACD"] = df["EMA_12"] - df["EMA_26"]
    df["MACD_signal"] = df["MACD"].ewm(span=9, adjust=False).mean()
    df["MACD_hist"] = df["MACD"] - df["MACD_signal"]

    rolling_std = df["Close"].rolling(20).std()
    df["BB_middle"] = df["SMA_20"]
    df["BB_upper"] = df["SMA_20"] + (2 * rolling_std)
    df["BB_lower"] = df["SMA_20"] - (2 * rolling_std)

    high_low = df["High"] - df["Low"]
    high_close = (df["High"] - df["Close"].shift()).abs()
    low_close = (df["Low"] - df["Close"].shift()).abs()
    true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    df["ATR"] = true_range.rolling(14).mean()
    df["Volume_SMA_20"] = df["Volume"].rolling(20).mean()

    latest = df.iloc[-1].fillna(0)
    current_price = float(latest["Close"])
    sma_200 = float(latest["SMA_200"]) if float(latest["SMA_200"]) else current_price
    rsi = float(latest["RSI"]) if float(latest["RSI"]) else 50.0

    return {
        "current_price": current_price,
        "sma_20": round(float(latest["SMA_20"]), 2),
        "sma_50": round(float(latest["SMA_50"]), 2),
        "sma_200": round(sma_200, 2),
        "ema_12": round(float(latest["EMA_12"]), 2),
        "ema_26": round(float(latest["EMA_26"]), 2),
        "rsi": round(rsi, 2),
        "macd": round(float(latest["MACD"]), 2),
        "macd_signal": round(float(latest["MACD_signal"]), 2),
        "macd_hist": round(float(latest["MACD_hist"]), 2),
        "bb_upper": round(float(latest["BB_upper"]), 2),
        "bb_lower": round(float(latest["BB_lower"]), 2),
        "atr": round(float(latest["ATR"]), 2),
        "volume_sma_20": round(float(latest["Volume_SMA_20"]), 2),
        "trend": "bullish" if current_price >= sma_200 else "bearish",
        "momentum": "overbought" if rsi >= 70 else "oversold" if rsi <= 30 else "neutral",
    }

