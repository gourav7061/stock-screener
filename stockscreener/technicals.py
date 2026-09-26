"""Compute technical indicators from price data."""

import pandas as pd
import numpy as np
from datetime import datetime, timezone
import sqlite3


def compute_sma(close: pd.Series, window: int) -> float:
    """Compute Simple Moving Average."""
    if len(close) < window:
        return np.nan
    return close.rolling(window=window).mean().iloc[-1]


def compute_rsi(close: pd.Series, window: int = 14) -> float:
    """Compute Relative Strength Index (RSI)."""
    if len(close) < window + 1:
        return np.nan

    delta = close.diff()
    gain = delta.where(delta > 0, 0).rolling(window=window).mean()
    loss = -delta.where(delta < 0, 0).rolling(window=window).mean()

    rs = gain / loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))

    return rsi.iloc[-1]


def compute_ema(close: pd.Series, window: int) -> float:
    """Compute Exponential Moving Average."""
    if len(close) < window:
        return np.nan
    return close.ewm(span=window).mean().iloc[-1]


def compute_macd(close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> tuple:
    """Compute MACD, Signal, and Histogram."""
    if len(close) < slow + signal:
        return np.nan, np.nan, np.nan

    ema_fast = close.ewm(span=fast).mean()
    ema_slow = close.ewm(span=slow).mean()
    macd = ema_fast - ema_slow
    macd_signal = macd.ewm(span=signal).mean()
    macd_hist = macd - macd_signal

    return macd.iloc[-1], macd_signal.iloc[-1], macd_hist.iloc[-1]


def compute_bollinger_bands(close: pd.Series, window: int = 20, num_std: int = 2) -> tuple:
    """Compute Bollinger Bands (upper, lower, middle, %B)."""
    if len(close) < window:
        return np.nan, np.nan, np.nan, np.nan

    middle = close.rolling(window=window).mean()
    std = close.rolling(window=window).std()
    upper = middle + (std * num_std)
    lower = middle - (std * num_std)

    # %B: position of price within bands
    percent_b = (close - lower) / (upper - lower)

    return upper.iloc[-1], lower.iloc[-1], middle.iloc[-1], percent_b.iloc[-1]


def compute_volume_spike_ratio(volume: pd.Series, window: int = 20) -> float:
    """Compute volume spike ratio (current / average)."""
    if len(volume) < window:
        return np.nan

    avg_vol = volume.rolling(window=window).mean().iloc[-1]
    if avg_vol == 0:
        return np.nan

    return volume.iloc[-1] / avg_vol


def compute_pct_change(close: pd.Series, days: int) -> float:
    """Compute percentage change over N days."""
    if len(close) <= days:
        return np.nan

    old = close.iloc[-days - 1]
    new = close.iloc[-1]
    return ((new - old) / old * 100)


def compute_52week_metrics(close: pd.Series) -> tuple:
    """Compute 52-week high/low, % from high, and low value."""
    if len(close) < 252:  # ~252 trading days per year
        return np.nan, np.nan, np.nan, np.nan

    recent_252 = close.tail(252)
    high_52w = recent_252.max()
    low_52w = recent_252.min()

    curr = close.iloc[-1]
    pct_from_high = ((curr - high_52w) / high_52w * 100)
    pct_from_low = ((curr - low_52w) / low_52w * 100)
    low_52w_25pct = low_52w * 1.25

    return pct_from_high, pct_from_low, low_52w, low_52w_25pct


def compute_technicals_for_ticker(price_df: pd.DataFrame) -> dict:
    """Compute all technical indicators for a single ticker's price history.

    Args:
        price_df: DataFrame with OHLCV columns (Close, Volume, etc.)

    Returns:
        Dict of indicator -> value
    """
    if price_df.empty or len(price_df) < 5:
        return {}

    close = price_df["Close"]
    volume = price_df["Volume"]

    latest_price = close.iloc[-1]
    sma20 = compute_sma(close, 20)
    sma50 = compute_sma(close, 50)
    sma150 = compute_sma(close, 150)
    sma200 = compute_sma(close, 200)
    sma220 = compute_sma(close, 220)
    ema220 = compute_ema(close, 220)
    rsi14 = compute_rsi(close, 14)
    macd, macd_signal, macd_hist = compute_macd(close)
    bb_upper, bb_lower, bb_mid, bb_percent_b = compute_bollinger_bands(close)
    volume_spike = compute_volume_spike_ratio(volume)
    pct_from_high, pct_from_low, low_52w, low_52w_25pct = compute_52week_metrics(close)

    pct_1d = compute_pct_change(close, 1)
    pct_1m = compute_pct_change(close, 21)
    pct_3m = compute_pct_change(close, 63)
    pct_1y = compute_pct_change(close, 251)

    avg_vol_20d = volume.tail(20).mean()

    return {
        "as_of_date": price_df.index[-1].strftime("%Y-%m-%d"),
        "price": round(float(latest_price), 2),
        "sma20": round(float(sma20), 2) if pd.notna(sma20) else None,
        "sma50": round(float(sma50), 2) if pd.notna(sma50) else None,
        "sma150": round(float(sma150), 2) if pd.notna(sma150) else None,
        "sma200": round(float(sma200), 2) if pd.notna(sma200) else None,
        "sma220": round(float(sma220), 2) if pd.notna(sma220) else None,
        "ema220": round(float(ema220), 2) if pd.notna(ema220) else None,
        "rsi14": round(float(rsi14), 2) if pd.notna(rsi14) else None,
        "macd": round(float(macd), 2) if pd.notna(macd) else None,
        "macd_signal": round(float(macd_signal), 2) if pd.notna(macd_signal) else None,
        "macd_hist": round(float(macd_hist), 2) if pd.notna(macd_hist) else None,
        "bb_upper": round(float(bb_upper), 2) if pd.notna(bb_upper) else None,
        "bb_lower": round(float(bb_lower), 2) if pd.notna(bb_lower) else None,
        "bb_mid": round(float(bb_mid), 2) if pd.notna(bb_mid) else None,
        "bb_percent_b": round(float(bb_percent_b), 2) if pd.notna(bb_percent_b) else None,
        "pct_change_1d": round(float(pct_1d), 2) if pd.notna(pct_1d) else None,
        "pct_change_1m": round(float(pct_1m), 2) if pd.notna(pct_1m) else None,
        "pct_change_3m": round(float(pct_3m), 2) if pd.notna(pct_3m) else None,
        "pct_change_1y": round(float(pct_1y), 2) if pd.notna(pct_1y) else None,
        "pct_from_52w_high": round(float(pct_from_high), 2) if pd.notna(pct_from_high) else None,
        "pct_from_52w_low": round(float(pct_from_low), 2) if pd.notna(pct_from_low) else None,
        "52w_low": round(float(low_52w), 2) if pd.notna(low_52w) else None,
        "52w_low_25pct": round(float(low_52w_25pct), 2) if pd.notna(low_52w_25pct) else None,
        "volume": int(volume.iloc[-1]) if pd.notna(volume.iloc[-1]) else None,
        "avg_volume_20d": int(avg_vol_20d) if pd.notna(avg_vol_20d) else None,
        "volume_spike_ratio": round(float(volume_spike), 2) if pd.notna(volume_spike) else None,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }


def compute_and_store_technicals(con: sqlite3.Connection, ticker: str):
    """Compute technicals for a ticker from its stored prices and update technicals_latest table."""
    cursor = con.cursor()
    cursor.execute("SELECT date, open, high, low, close, adj_close, volume FROM prices WHERE ticker = ? ORDER BY date",
                  (ticker,))

    rows = cursor.fetchall()
    if not rows:
        return

    # Convert to DataFrame (capitalized to match compute_technicals_for_ticker's yfinance-style column names)
    df = pd.DataFrame(rows, columns=["date", "Open", "High", "Low", "Close", "Adj Close", "Volume"])
    df["date"] = pd.to_datetime(df["date"])
    df = df.set_index("date")
    df = df.sort_index()

    # Compute technicals
    tech_dict = compute_technicals_for_ticker(df)

    if not tech_dict:
        return

    # Upsert into technicals_latest
    cursor.execute("""
        INSERT OR REPLACE INTO technicals_latest
        (ticker, as_of_date, price, sma20, sma50, sma150, sma200, sma220, ema220, ema12, ema26, rsi14,
         macd, macd_signal, macd_hist, bb_upper, bb_lower, bb_mid, bb_percent_b,
         pct_change_1d, pct_change_1m, pct_change_3m, pct_change_1y,
         pct_from_52w_high, pct_from_52w_low, "52w_low", "52w_low_25pct", volume, avg_volume_20d, volume_spike_ratio, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (ticker, tech_dict["as_of_date"], tech_dict["price"], tech_dict["sma20"], tech_dict["sma50"],
          tech_dict["sma150"], tech_dict["sma200"], tech_dict["sma220"], tech_dict["ema220"],
          None, None, tech_dict["rsi14"], tech_dict["macd"], tech_dict["macd_signal"],
          tech_dict["macd_hist"], tech_dict["bb_upper"], tech_dict["bb_lower"], tech_dict["bb_mid"],
          tech_dict["bb_percent_b"], tech_dict["pct_change_1d"], tech_dict["pct_change_1m"],
          tech_dict["pct_change_3m"], tech_dict["pct_change_1y"], tech_dict["pct_from_52w_high"],
          tech_dict["pct_from_52w_low"], tech_dict["52w_low"], tech_dict["52w_low_25pct"],
          tech_dict["volume"], tech_dict["avg_volume_20d"],
          tech_dict["volume_spike_ratio"], tech_dict["updated_at"]))

    con.commit()
