"""
kraken_client.py  —  Fetches market data from Kraken public API (no key needed).
"""

import requests
import pandas as pd
from datetime import datetime
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


BASE = "https://api.kraken.com/0/public"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json",
}

def _session():
    """Requests session with retries and proper headers."""
    s = requests.Session()
    retry = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
    s.mount("https://", HTTPAdapter(max_retries=retry))
    s.headers.update(HEADERS)
    return s


def get_ticker(pair="XBTUSD"):
    try:
        r = _session().get(f"{BASE}/Ticker", params={"pair": pair}, timeout=15)
        r.raise_for_status()
        data = r.json()
        if data.get("error"):
            return {"error": str(data["error"])}
        res = list(data["result"].values())[0]
        return {
            "pair":   pair,
            "last":   float(res["c"][0]),
            "bid":    float(res["b"][0]),
            "ask":    float(res["a"][0]),
            "high":   float(res["h"][1]),
            "low":    float(res["l"][1]),
            "volume": float(res["v"][1]),
        }
    except Exception as e:
        return {"error": str(e)}


def get_ohlc(pair="XBTUSD", interval=60):
    """interval in minutes: 1,5,15,30,60,240,1440"""
    try:
        r = _session().get(f"{BASE}/OHLC", params={"pair": pair, "interval": interval}, timeout=15)
        r.raise_for_status()
        data = r.json()
        if data.get("error"):
            return pd.DataFrame()
        raw = list(data["result"].values())[0]
        df = pd.DataFrame(raw, columns=["time","open","high","low","close","vwap","volume","count"])
        df["time"] = pd.to_datetime(df["time"], unit="s")
        for c in ["open","high","low","close","volume"]:
            df[c] = df[c].astype(float)
        return df[["time","open","high","low","close","volume"]].copy()
    except Exception:
        return pd.DataFrame()


def add_indicators(df):
    if df.empty or len(df) < 26:
        return df
    c = df["close"]

    # RSI 14
    d = c.diff()
    gain = d.clip(lower=0).rolling(14).mean()
    loss = (-d.clip(upper=0)).rolling(14).mean()
    df["rsi"] = 100 - 100 / (1 + gain / loss.replace(0, 1e-9))

    # MACD
    e12 = c.ewm(span=12).mean()
    e26 = c.ewm(span=26).mean()
    df["macd"]        = e12 - e26
    df["macd_signal"] = df["macd"].ewm(span=9).mean()
    df["macd_hist"]   = df["macd"] - df["macd_signal"]

    # Bollinger Bands 20
    sma = c.rolling(20).mean()
    std = c.rolling(20).std()
    df["bb_upper"] = sma + 2 * std
    df["bb_mid"]   = sma
    df["bb_lower"] = sma - 2 * std

    return df
