"""Simple Rise/Fall backtester. Ties count as losses (as on Deriv)."""
from typing import Any, Dict

import pandas as pd

from .indicators import add_indicators
from .signals import THRESHOLD, score_series


def max_losing_streak(wins: pd.Series) -> int:
    longest = current = 0
    for w in wins:
        current = 0 if w else current + 1
        longest = max(longest, current)
    return longest


def backtest_signals(df: pd.DataFrame, payout: float = 0.9, horizon: int = 1,
                     cfg: Dict[str, Any] = None) -> Dict[str, Any]:
    """Trade every Bullish (Rise) / Bearish (Fall) signal for `horizon` candles."""
    d = add_indicators(df, cfg).dropna().copy()
    d["score"] = score_series(d)
    future = d["close"].shift(-horizon)
    sig = pd.Series(0, index=d.index)
    sig[d["score"] >= THRESHOLD] = 1
    sig[d["score"] <= -THRESHOLD] = -1
    mask = (sig != 0) & future.notna()
    trades = d[mask]
    if trades.empty:
        return {"trades": 0, "win_rate": 0.0, "max_losing_streak": 0,
                "ev_per_unit": 0.0, "breakeven": round(100 / (1 + payout), 2)}
    wins = ((sig[mask] == 1) & (future[mask] > trades["close"])) | \
           ((sig[mask] == -1) & (future[mask] < trades["close"]))
    win_rate = float(wins.mean())
    ev = win_rate * payout - (1 - win_rate)
    return {
        "trades": int(len(trades)),
        "win_rate": round(win_rate * 100, 2),
        "max_losing_streak": max_losing_streak(wins),
        "ev_per_unit": round(ev, 4),
        "breakeven": round(100 / (1 + payout), 2),
    }


def backtest_digits(digits: pd.Series, kind: str = "even", barrier: int = 4,
                    payout: float = 0.95) -> Dict[str, Any]:
    """Baseline: always bet one digit outcome on every tick."""
    wins = {"even": digits % 2 == 0, "odd": digits % 2 == 1,
            "over": digits > barrier, "under": digits < barrier}[kind]
    wr = float(wins.mean()) if len(wins) else 0.0
    return {"trades": int(len(wins)), "win_rate": round(wr * 100, 2),
            "max_losing_streak": max_losing_streak(wins),
            "ev_per_unit": round(wr * payout - (1 - wr), 4)}
