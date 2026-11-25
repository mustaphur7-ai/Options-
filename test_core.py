import numpy as np
import pandas as pd

from src.backtest import backtest_digits, backtest_signals, max_losing_streak
from src.data_client import last_digit
from src.digits import digit_frequency, even_odd_ratio, streaks
from src.indicators import add_indicators
from src.signals import analyze


def make_df(n: int = 300) -> pd.DataFrame:
    rng = np.random.default_rng(1)
    close = 100 + np.cumsum(rng.normal(0, 1, n))
    return pd.DataFrame({
        "time": pd.date_range("2024-01-01", periods=n, freq="min"),
        "open": close - 0.1, "high": close + 0.5,
        "low": close - 0.5, "close": close})


def test_indicators_columns():
    out = add_indicators(make_df())
    for col in ["rsi", "macd", "bb_upper", "ema_fast", "stoch_k", "atr"]:
        assert col in out.columns
    assert out["rsi"].dropna().between(0, 100).all()


def test_digits():
    d = pd.Series([1, 2, 3, 4, 4, 6])
    assert digit_frequency(d).sum() > 99
    assert even_odd_ratio(d)["even_pct"] == 66.67
    assert streaks(pd.Series([True, True, False, True]))["longest"] == 2


def test_last_digit():
    assert last_digit(1234.560, 3) == 0
    assert last_digit(99.97, 2) == 7


def test_signal_and_backtest():
    df = make_df()
    assert analyze(df)["label"] in {"Bullish", "Bearish", "Neutral"}
    r = backtest_signals(df, 0.9)
    assert 0 <= r["win_rate"] <= 100
    assert max_losing_streak(pd.Series([True, False, False, True])) == 2
    assert backtest_digits(pd.Series([2, 4, 6]), "even")["win_rate"] == 100.0
