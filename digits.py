"""Last-digit analysis for synthetic indices."""
from typing import Dict, List

import pandas as pd


def digit_frequency(digits: pd.Series) -> pd.Series:
    """Percentage frequency of each digit 0-9."""
    counts = digits.value_counts().reindex(range(10), fill_value=0)
    return (counts / max(len(digits), 1) * 100).round(2)


def even_odd_ratio(digits: pd.Series) -> Dict[str, float]:
    even = float((digits % 2 == 0).mean() * 100) if len(digits) else 0.0
    return {"even_pct": round(even, 2), "odd_pct": round(100 - even, 2)}


def over_under(digits: pd.Series, barrier: int = 4) -> Dict[str, float]:
    if not len(digits):
        return {"over_pct": 0.0, "under_pct": 0.0}
    over = float((digits > barrier).mean() * 100)
    under = float((digits < barrier).mean() * 100)
    return {"over_pct": round(over, 2), "under_pct": round(under, 2)}


def streaks(flags: pd.Series) -> Dict[str, int]:
    """Current and longest run of True values."""
    longest = current = 0
    for f in flags:
        current = current + 1 if f else 0
        longest = max(longest, current)
    return {"current": current, "longest": longest}


def digit_streaks(digits: pd.Series, barrier: int = 4) -> Dict[str, Dict[str, int]]:
    return {
        "even": streaks(digits % 2 == 0),
        "odd": streaks(digits % 2 == 1),
        "over": streaks(digits > barrier),
        "under": streaks(digits < barrier),
    }


def expected_pct(kind: str, barrier: int = 4) -> float:
    """Theoretical percentage if digits are uniform (fair)."""
    return {"even": 50.0, "odd": 50.0,
            "over": (9 - barrier) * 10.0, "under": barrier * 10.0}[kind]


def digit_list(digits: pd.Series, last: int = 20) -> List[int]:
    return [int(d) for d in digits.tail(last)]
