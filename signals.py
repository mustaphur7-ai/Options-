"""Combine indicators into a simple Bullish / Bearish / Neutral score."""
from typing import Any, Dict, List

import numpy as np
import pandas as pd

from .indicators import add_indicators

THRESHOLD = 2


def score_series(d: pd.DataFrame) -> pd.Series:
    """Vectorised score per row (d must already contain indicators)."""
    s = pd.Series(0, index=d.index, dtype=float)
    s += np.where(d["rsi"] < 30, 1, np.where(d["rsi"] > 70, -1, 0))
    s += np.where(d["macd_hist"] > 0, 1, -1)
    s += np.where(d["close"] < d["bb_lower"], 1,
                  np.where(d["close"] > d["bb_upper"], -1, 0))
    s += np.where(d["ema_fast"] > d["ema_slow"], 1, -1)
    s += np.where(d["stoch_k"] < 20, 1, np.where(d["stoch_k"] > 80, -1, 0))
    return s


def label_from_score(score: float) -> str:
    if score >= THRESHOLD:
        return "Bullish"
    if score <= -THRESHOLD:
        return "Bearish"
    return "Neutral"


def analyze(df: pd.DataFrame, cfg: Dict[str, Any] = None) -> Dict[str, Any]:
    """Latest signal with human-readable reasons."""
    d = add_indicators(df, cfg).dropna()
    if d.empty:
        return {"score": 0, "label": "Neutral", "reasons": ["Not enough data"]}
    r = d.iloc[-1]
    reasons: List[str] = []
    if r["rsi"] < 30:
        reasons.append(f"RSI {r['rsi']:.1f} oversold (+1)")
    elif r["rsi"] > 70:
        reasons.append(f"RSI {r['rsi']:.1f} overbought (-1)")
    else:
        reasons.append(f"RSI {r['rsi']:.1f} neutral (0)")
    reasons.append("MACD histogram positive (+1)" if r["macd_hist"] > 0
                   else "MACD histogram negative (-1)")
    if r["close"] < r["bb_lower"]:
        reasons.append("Price below lower Bollinger band (+1)")
    elif r["close"] > r["bb_upper"]:
        reasons.append("Price above upper Bollinger band (-1)")
    else:
        reasons.append("Price inside Bollinger bands (0)")
    reasons.append("EMA fast above slow (+1)" if r["ema_fast"] > r["ema_slow"]
                   else "EMA fast below slow (-1)")
    if r["stoch_k"] < 20:
        reasons.append(f"Stochastic {r['stoch_k']:.1f} oversold (+1)")
    elif r["stoch_k"] > 80:
        reasons.append(f"Stochastic {r['stoch_k']:.1f} overbought (-1)")
    else:
        reasons.append(f"Stochastic {r['stoch_k']:.1f} neutral (0)")
    score = float(score_series(d).iloc[-1])
    return {"score": score, "label": label_from_score(score), "reasons": reasons,
            "atr": float(r["atr"])}
