"""Streamlit dashboard. Analysis only: no trading, no API tokens."""
import time

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.backtest import backtest_digits, backtest_signals
from src.config import load_config
from src.data_client import DerivError, get_candles, get_ticks
from src.digits import (digit_frequency, digit_streaks, even_odd_ratio,
                        over_under)
from src.indicators import add_indicators
from src.signals import analyze

cfg = load_config()
st.set_page_config(page_title="Deriv Analyzer", layout="wide")
st.title("Deriv Analyzer")
st.caption("Analysis only. Not financial advice. Trading binary options is high risk.")

symbol = st.sidebar.selectbox("Symbol", cfg["symbols"])
tf_name = st.sidebar.selectbox("Timeframe", list(cfg["timeframes"]))
count = st.sidebar.slider("Candles", 100, 2000, cfg["candles"], 50)
payout = st.sidebar.slider("Payout (profit per 1 staked)", 0.5, 1.0, cfg["payout"], 0.01)
barrier = st.sidebar.slider("Digit barrier", 0, 9, 4)
auto = st.sidebar.checkbox("Auto-refresh every 5s")

try:
    candles = get_candles(symbol, cfg["timeframes"][tf_name], count, cfg["ws_url"])
    ticks = get_ticks(symbol, 1000, cfg["ws_url"])
except DerivError as exc:
    st.error(f"Could not load data: {exc}")
    st.stop()

ind = add_indicators(candles, cfg["indicators"])
tab_chart, tab_sig, tab_dig, tab_bt = st.tabs(
    ["Chart", "Signal", "Digits", "Backtest"])

with tab_chart:
    fig = go.Figure(go.Candlestick(
        x=ind["time"], open=ind["open"], high=ind["high"],
        low=ind["low"], close=ind["close"], name="Price"))
    for col, color in [("ema_fast", "orange"), ("ema_slow", "blue"),
                       ("bb_upper", "gray"), ("bb_lower", "gray")]:
        fig.add_trace(go.Scatter(x=ind["time"], y=ind[col], name=col,
                                 line=dict(width=1, color=color)))
    fig.update_layout(height=550, xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)
    rsi_fig = go.Figure(go.Scatter(x=ind["time"], y=ind["rsi"], name="RSI"))
    rsi_fig.add_hline(y=70, line_dash="dot")
    rsi_fig.add_hline(y=30, line_dash="dot")
    rsi_fig.update_layout(height=220, margin=dict(t=10))
    st.plotly_chart(rsi_fig, use_container_width=True)
    st.subheader("Live tick feed")
    st.dataframe(ticks.tail(15).iloc[::-1], use_container_width=True)

with tab_sig:
    res = analyze(candles, cfg["indicators"])
    st.metric("Signal", res["label"], f"score {res['score']:+.0f}")
    for reason in res["reasons"]:
        st.write("- " + reason)

with tab_dig:
    digits = ticks["digit"]
    st.bar_chart(digit_frequency(digits))
    c1, c2 = st.columns(2)
    c1.write("Even / Odd"); c1.json(even_odd_ratio(digits))
    c2.write(f"Over / Under {barrier}"); c2.json(over_under(digits, barrier))
    st.write("Streaks (current / longest)")
    st.json(digit_streaks(digits, barrier))
    st.caption("On synthetic indices digits are random; expect ~uniform frequencies.")

with tab_bt:
    r = backtest_signals(candles, payout, cfg=cfg["indicators"])
    st.subheader("Signal strategy (1-candle Rise/Fall)")
    st.json(r)
    st.write(f"Break-even win rate at this payout: {r['breakeven']}%")
    st.subheader("Digit baselines")
    for kind in ["even", "odd", "over", "under"]:
        st.write(kind, backtest_digits(ticks["digit"], kind, barrier, payout))

if auto:
    time.sleep(5)
    st.rerun()
