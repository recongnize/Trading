"""Binance spot data source using the public REST API.

No API key required for public market data.  Supports all Binance spot
symbols (BTCUSDT, ETHUSDT, SOLUSDT, ...) and standard intervals.

Binance REST endpoint: https://api.binance.com/api/v3/klines
"""
from __future__ import annotations

import logging
import time

from pa_agent.data.base import (
    DataSource,
    DataSourceTransientError,
    KlineBar,
    normalize_kline_bar,
)

logger = logging.getLogger(__name__)

#: Map our timeframe strings -> Binance interval strings
_TF_MAP: dict[str, str] = {
    "1m":  "1m",
    "3m":  "3m",
    "5m":  "5m",
    "15m": "15m",
    "30m": "30m",
    "1h":  "1h",
    "2h":  "2h",
    "4h":  "4h",
    "1d":  "1d",
    "1w":  "1w",
    "1M":  "1M",
}

#: Binance base URLs (spot market).  The first entry is preferred; fallbacks
#: are tried in order when the primary is unreachable (e.g. api.binance.com
#: is sometimes blocked from China while data-api.binance.vision works).
_BINANCE_BASE_URLS: list[str] = [
    "https://data-api.binance.vision",
    "https://api1.binance.com",
    "https://api2.binance.com",
    "https://api3.binance.com",
    "https://api.binance.com",
]

#: Common crypto pairs for the symbol dropdown
_DEFAULT_SYMBOLS: list[str] = [
    "BTCUSDT",
    "ETHUSDT",
    "SOLUSDT",
    "BNBUSDT",
    "XRPUSDT",
    "DOGEUSDT",
    "ADAUSDT",
    "AVAXUSDT",
    "LINKUSDT",
    "DOTUSDT",
    "TRXUSDT",
    "MATICUSDT",
]


class BinanceSource(DataSource):
    """K-line data from Binance spot market (public REST API)."""

    def __init__(self) -> None:
        self._symbol: str = ""
        self._timeframe: str = ""
        self._connected: bool = False
        self._session = None  # requests.Session
        self._current_base: str = _BINANCE_BASE_URLS[0]

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def connect(self) -> None:
        try:
            import requests  # noqa: F401
            self._session = requests.Session()
            self._connected = True
            logger.info("BinanceSource connected (public REST API)")
        except ImportError as exc:
            raise DataSourceTransientError(
                "requests not installed — run: pip install requests"
            ) from exc

    def disconnect(self) -> None:
        if self._session is not None:
            self._session.close()
            self._session = None
        self._connected = False
        logger.info("BinanceSource disconnected")

    # ── Discovery ─────────────────────────────────────────────────────────────

    def list_symbols(self) -> list[str]:
        return list(_DEFAULT_SYMBOLS)

    def supported_timeframes(self) -> list[str]:
        return list(_TF_MAP.keys())

    # ── Subscription ──────────────────────────────────────────────────────────

    def subscribe(self, symbol: str, timeframe: str) -> None:
        if timeframe not in _TF_MAP:
            raise ValueError(
                f"Unsupported timeframe: {timeframe!r}. Use one of {list(_TF_MAP)}"
            )
        # Binance symbols are uppercase without separators (e.g. BTCUSDT)
        self._symbol = symbol.strip().upper().replace("-", "").replace("_", "")
        self._timeframe = timeframe
        logger.info("BinanceSource subscribed: %s %s", self._symbol, timeframe)

    def unsubscribe(self) -> None:
        self._symbol = ""
        self._timeframe = ""
        logger.info("BinanceSource unsubscribed")

    # ── Data fetch ────────────────────────────────────────────────────────────

    def latest_snapshot(self, n: int) -> list[KlineBar]:
        """Return *n* bars newest-first; bars[0] is the forming (unclosed) bar."""
        if not self._connected:
            raise DataSourceTransientError("Not connected — call connect() first")
        if not self._symbol or not self._timeframe:
            raise DataSourceTransientError("Not subscribed — call subscribe() first")

        import requests

        interval = _TF_MAP[self._timeframe]
        # Request a few extra bars in case the newest is still forming
        limit = max(n + 2, n)
        params = {"symbol": self._symbol, "interval": interval, "limit": limit}

        # Try the cached base URL first, then fall back through the list.
        bases_to_try = [self._current_base] + [
            b for b in _BINANCE_BASE_URLS if b != self._current_base
        ]
        raw = None
        last_exc: Exception | None = None
        for base in bases_to_try:
            url = f"{base}/api/v3/klines"
            try:
                resp = self._session.get(url, params=params, timeout=10)
                resp.raise_for_status()
                raw = resp.json()
                self._current_base = base  # remember the one that works
                break
            except requests.exceptions.Timeout as exc:
                last_exc = exc
                continue
            except requests.exceptions.HTTPError as exc:
                status = exc.response.status_code if exc.response is not None else "?"
                last_exc = exc
                # 4xx (except 429) won't be fixed by trying another domain
                if status is not None and 400 <= status < 500 and status != 429:
                    raise DataSourceTransientError(
                        f"Binance HTTP {status} for {self._symbol}: {exc}"
                    ) from exc
                continue
            except Exception as exc:  # noqa: BLE001
                last_exc = exc
                continue

        if raw is None:
            raise DataSourceTransientError(
                f"Binance request failed for {self._symbol} {interval}: "
                f"all base URLs unreachable. Last error: {last_exc}"
            )

        if not raw:
            raise DataSourceTransientError(
                f"Binance returned no data for {self._symbol} {interval}"
            )

        # raw is oldest-first; reverse to newest-first
        raw_newest_first = list(reversed(raw))

        bars: list[KlineBar] = []
        for i, k in enumerate(raw_newest_first):
            # k = [open_time, open, high, low, close, volume, close_time,
            #      quote_volume, trades, taker_buy_base, taker_buy_quote, ignore]
            ts_open = float(k[0])
            open_p = float(k[1])
            high_p = float(k[2])
            low_p = float(k[3])
            close_p = float(k[4])
            volume = float(k[5])
            quote_volume = float(k[7])  # turnover in quote asset (USDT)
            # bars[0] is the most recent bar — it may still be forming
            closed = i != 0
            bars.append(
                normalize_kline_bar(
                    KlineBar(
                        seq=i + 1,
                        ts_open=ts_open,
                        open=open_p,
                        high=high_p,
                        low=low_p,
                        close=close_p,
                        volume=volume,
                        amount=quote_volume,
                        closed=closed,
                    )
                )
            )
            if len(bars) >= n:
                break

        return bars
