"""Technical indicators implemented with pandas only (no extra libs)."""
from typing import Any, Dict

import numpy as np
import pandas as pd


def ema(s: pd.Series, n: int) -> pd.Series:
    return s.ewm(span=n, adjust=False).mean()


def rsi(s: pd.Series, n: int = 14) -> pd.Series:
    delta = s.diff()
    gain = delta.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean()
    rs = gain / loss.replace(0, np.nan)
    return (100 - 100 / (1 + rs)).fillna(100.0).where(loss.notna())


def macd(s: pd.Series, fast: int = 12, slow: int = 26, sig: int = 9):
    line = ema(s, fast) - ema(s, slow)
    signal = ema(line, sig)
    return line, signal, line - signal


def bollinger(s: pd.Series, n: int = 20, k: float = 2.0):
    mid = s.rolling(n).mean()
    sd = s.rolling(n).std()
    return mid - k * sd, mid, mid + k * sd


def stochastic(df: pd.DataFrame, n: int = 14, smooth: int = 3):
    low = df["low"].rolling(n).min()
    high = df["high"].rolling(n).max()
    k = 100 * (df["close"] - low) / (high - low).replace(0, np.nan)
    return k, k.rolling(smooth).mean()


def atr(df: pd.DataFrame, n: int = 14) -> pd.Series:
    prev = df["close"].shift()
    tr = pd.concat([df["high"] - df["low"],
                    (df["high"] - prev).abs(),
                    (df["low"] - prev).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1 / n, adjust=False).mean()


def add_indicators(df: pd.DataFrame, cfg: Dict[str, Any] = None) -> pd.DataFrame:
    """Return a copy of df with all indicator columns added."""
    cfg = cfg or {}
    m = cfg.get("macd", [12, 26, 9])
    bb = cfg.get("bollinger", [20, 2.0])
    st = cfg.get("stoch", [14, 3])
    out = df.copy()
    c = out["close"]
    out["rsi"] = rsi(c, cfg.get("rsi_period", 14))
    out["macd"], out["macd_signal"], out["macd_hist"] = macd(c, *m)
    out["bb_lower"], out["bb_mid"], out["bb_upper"] = bollinger(c, *bb)
    out["ema_fast"] = ema(c, cfg.get("ema_fast", 20))
    out["ema_slow"] = ema(c, cfg.get("ema_slow", 50))
    out["stoch_k"], out["stoch_d"] = stochastic(out, *st)
    out["atr"] = atr(out, cfg.get("atr_period", 14))
    return out
