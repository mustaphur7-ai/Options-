# deriv-analyzer

Free, open-source analysis tool for Deriv synthetic/forex markets
(Rise/Fall, Over/Under, Even/Odd). **Analysis only** - it never places
trades and never stores API tokens.

## Data source
Deriv public WebSocket API (no token, no paid API):
`wss://ws.derivws.com/websockets/v3?app_id=1089`
If you publish this for others, register your own free app ID at
https://api.deriv.com and change `ws_url` in `config.yaml`.

## Features
- Candles (1m/5m/15m) and ticks, cached locally as CSV
- RSI, MACD, Bollinger, EMA 20/50, Stochastic, ATR
- Last-digit frequency, even/odd, over/under, streaks
- Signal score (Bullish / Bearish / Neutral) with reasons
- Backtester: win rate, max losing streak, expected value, break-even rate
- Streamlit + Plotly dashboard

## Setup
```bash
git clone <your-repo-url>
cd deriv-analyzer
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```
Run tests: `pytest -q`

## Structure
```
src/ data_client.py indicators.py digits.py signals.py backtest.py config.py
app.py   tests/   config.yaml   .github/workflows/ci.yml
```

## Screenshots
_Add screenshots of the dashboard here._

## Risk disclaimer
Educational use only; not financial advice. Binary options are high risk and
you can lose your entire stake. Synthetic indices are random by design, so
backtests will usually show no real edge. Past results do not predict future
results.
