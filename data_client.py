"""Deriv public WebSocket client (market data only, no token needed)."""
import json
import threading
import time
from pathlib import Path
from typing import Any, Dict, Iterator

import pandas as pd
import websocket

WS_URL = "wss://ws.derivws.com/websockets/v3?app_id=1089"
CACHE_DIR = Path("data/cache")


class DerivError(Exception):
    """Raised when the Deriv API returns an error."""


def _request(payload: Dict[str, Any], url: str = WS_URL,
             retries: int = 3, timeout: int = 15) -> Dict[str, Any]:
    """Send one request and return the first response (with retries)."""
    last_exc: Exception = DerivError("unknown error")
    for attempt in range(retries):
        try:
            ws = websocket.create_connection(url, timeout=timeout)
            try:
                ws.send(json.dumps(payload))
                msg = json.loads(ws.recv())
            finally:
                ws.close()
            if "error" in msg:
                raise DerivError(msg["error"].get("message", "API error"))
            return msg
        except DerivError:
            raise
        except Exception as exc:  # network issues -> retry
            last_exc = exc
            time.sleep(1.5 * (attempt + 1))
    raise DerivError(f"Connection failed: {last_exc}")


def _cache_path(name: str) -> Path:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return CACHE_DIR / f"{name}.csv"


def get_candles(symbol: str, granularity: int = 60, count: int = 500,
                url: str = WS_URL) -> pd.DataFrame:
    """Fetch OHLC candles. Falls back to the local CSV cache if offline."""
    cache = _cache_path(f"{symbol}_{granularity}")
    payload = {
        "ticks_history": symbol, "adjust_start_time": 1,
        "count": min(count, 5000), "end": "latest",
        "style": "candles", "granularity": granularity,
    }
    try:
        msg = _request(payload, url)
        df = pd.DataFrame(msg["candles"])
        df["time"] = pd.to_datetime(df["epoch"], unit="s")
        df = df[["time", "open", "high", "low", "close"]].astype(
            {"open": float, "high": float, "low": float, "close": float})
        df.to_csv(cache, index=False)
        return df
    except DerivError:
        if cache.exists():
            return pd.read_csv(cache, parse_dates=["time"])
        raise


def last_digit(price: float, pip_size: int) -> int:
    """Last decimal digit of a quote, using the symbol's pip size."""
    return int(f"{price:.{pip_size}f}"[-1])


def get_ticks(symbol: str, count: int = 1000, url: str = WS_URL) -> pd.DataFrame:
    """Fetch recent ticks with their last digit."""
    cache = _cache_path(f"{symbol}_ticks")
    payload = {"ticks_history": symbol, "count": min(count, 5000),
               "end": "latest", "style": "ticks"}
    try:
        msg = _request(payload, url)
        pip = int(msg.get("pip_size", 2))
        hist = msg["history"]
        df = pd.DataFrame({"time": pd.to_datetime(hist["times"], unit="s"),
                           "price": [float(p) for p in hist["prices"]]})
        df["digit"] = [last_digit(p, pip) for p in df["price"]]
        df.to_csv(cache, index=False)
        return df
    except DerivError:
        if cache.exists():
            return pd.read_csv(cache, parse_dates=["time"])
        raise


def stream_ticks(symbol: str, url: str = WS_URL) -> Iterator[Dict[str, Any]]:
    """Yield live ticks forever; pings every 30s and auto-reconnects."""
    while True:
        try:
            ws = websocket.create_connection(url, timeout=10)
            ws.send(json.dumps({"ticks": symbol, "subscribe": 1}))
            stop = threading.Event()

            def pinger() -> None:
                while not stop.wait(30):
                    try:
                        ws.send(json.dumps({"ping": 1}))
                    except Exception:
                        return

            threading.Thread(target=pinger, daemon=True).start()
            try:
                while True:
                    try:
                        msg = json.loads(ws.recv())
                    except websocket.WebSocketTimeoutException:
                        continue
                    if "error" in msg:
                        raise DerivError(msg["error"].get("message", "error"))
                    if msg.get("msg_type") == "tick":
                        t = msg["tick"]
                        pip = int(t.get("pip_size", 2))
                        yield {"time": pd.to_datetime(t["epoch"], unit="s"),
                               "price": float(t["quote"]),
                               "digit": last_digit(float(t["quote"]), pip)}
            finally:
                stop.set()
                ws.close()
        except DerivError:
            raise
        except Exception:
            time.sleep(3)  # reconnect
