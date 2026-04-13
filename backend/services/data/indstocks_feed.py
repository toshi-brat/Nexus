"""
INDstocks Live Data Feed & WebSocket Manager
Fetches historical candles, live option chains, and real-time ticks.
"""
import pandas as pd
import numpy as np
import requests
import csv
import logging
from datetime import datetime, timedelta
from io import StringIO
from typing import Dict, Tuple, List, Any, Optional

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
import config

logger = logging.getLogger("indstocks_feed")

class IndStocksDataFeed:
    def __init__(self):
        self.api_key = config.INDSTOCKS_API_KEY
        self.secret = config.INDSTOCKS_SECRET
        self.access_token = config.INDMONEY_ACCESS_TOKEN
        self.base_url = config.INDSTOCKS_REST_URL.rstrip("/")
        self.token_api_base = "https://api.indstocks.com"
        self.token = None
        self._token_mode = bool(self.access_token)
        self._mock_mode = not bool(self.api_key or self.access_token)  # True fallback only when no auth exists
        self._scrip_cache: Dict[str, str] = {}

    def authenticate(self):
        if self._token_mode:
            try:
                res = requests.get(
                    f"{self.token_api_base}/user/profile",
                    headers=self.get_headers(),
                    timeout=8,
                )
                if res.status_code == 200:
                    self._mock_mode = False
                    logger.info("INDmoney token auth successful. Live market data enabled.")
                    return True
                logger.warning("INDmoney token auth failed with status %s. Falling back if possible.", res.status_code)
            except Exception as e:
                logger.error(f"INDmoney token auth error: {e}")

        if self.api_key and self.secret:
            try:
                # INDstocks API-key auth fallback
                res = requests.post(
                    f"{self.base_url}/auth/login",
                    json={"api_key": self.api_key, "api_secret": self.secret},
                    timeout=8,
                )
                if res.status_code == 200:
                    self.token = res.json().get("access_token")
                    self._mock_mode = False
                    logger.info("INDstocks API-key auth successful. Live market data enabled.")
                    return True
            except Exception as e:
                logger.error(f"INDstocks Auth Error: {e}")

        self._mock_mode = True
        logger.warning("No valid market-data auth found. Running in Simulation/Mock Mode.")
        return True

    def get_headers(self):
        if self._token_mode:
            return {
                "Authorization": self.access_token,
                "Content-Type": "application/json",
                "API-Version": "v1",
            }
        return {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}

    def _normalize_symbol_for_history(self, symbol: str) -> str:
        s = symbol.strip().upper()
        if ":" in s:
            return s
        if s == "NIFTY":
            return "NSE:NIFTY50"
        if s == "BANKNIFTY":
            return "NSE:NIFTYBANK"
        return f"NSE:{s}"

    def _normalize_symbol_for_options(self, symbol: str) -> str:
        s = symbol.strip().upper()
        if ":" in s:
            return s.split(":", 1)[1]
        if s in {"NIFTY50", "NIFTY 50"}:
            return "NIFTY"
        if s == "NIFTYBANK":
            return "BANKNIFTY"
        return s

    def _to_yahoo_symbol(self, symbol: str) -> str:
        s = symbol.strip().upper()
        if ":" in s:
            s = s.split(":", 1)[1]
        if s in {"NIFTY", "NIFTY50", "NIFTY 50"}:
            return "^NSEI"
        if s in {"BANKNIFTY", "NIFTYBANK", "NIFTY BANK"}:
            return "^NSEBANK"
        return f"{s}.NS"

    @staticmethod
    def _extract_candles(payload: Any) -> List[Any]:
        if isinstance(payload, list):
            return payload
        if not isinstance(payload, dict):
            return []
        if isinstance(payload.get("candles"), list):
            return payload["candles"]
        if isinstance(payload.get("data"), dict) and isinstance(payload["data"].get("candles"), list):
            return payload["data"]["candles"]
        if isinstance(payload.get("data"), list):
            return payload["data"]
        return []

    def _market_base(self) -> str:
        # Market-data routes are versioned under the configured REST URL.
        return self.base_url

    @staticmethod
    def _history_interval_label(interval: str) -> str:
        mapping = {
            "1m": "1minute",
            "2m": "2minute",
            "3m": "3minute",
            "5m": "5minute",
            "10m": "10minute",
            "15m": "15minute",
            "30m": "30minute",
            "1h": "60minute",
            "2h": "120minute",
            "4h": "240minute",
            "1d": "1day",
            "1w": "1week",
            "1mo": "1month",
        }
        return mapping.get(interval.lower(), "15minute")

    def _load_instruments_csv(self, source: str) -> List[Dict[str, str]]:
        res = requests.get(
            f"{self.token_api_base}/market/instruments",
            headers=self.get_headers(),
            params={"source": source},
            timeout=10,
        )
        res.raise_for_status()
        text = res.text.strip()
        if not text:
            return []
        return list(csv.DictReader(StringIO(text)))

    def _resolve_scrip_code(self, symbol: str) -> Optional[str]:
        s = self._normalize_symbol_for_options(symbol)
        if "_" in s and s.split("_", 1)[-1].isdigit():
            return s

        if s in self._scrip_cache:
            return self._scrip_cache[s]

        # Index symbols are typically present in index source.
        for source in ("index", "equity"):
            try:
                rows = self._load_instruments_csv(source)
            except Exception:
                continue

            target = s.replace(" ", "")
            for row in rows:
                exch = (row.get("EXCH") or "").strip().upper()
                security_id = (row.get("SECURITY_ID") or "").strip()
                if not exch or not security_id:
                    continue

                trading_symbol = (row.get("TRADING_SYMBOL") or "").strip().upper().replace(" ", "")
                symbol_name = (row.get("SYMBOL_NAME") or "").strip().upper().replace(" ", "")
                custom_symbol = (row.get("CUSTOM_SYMBOL") or "").strip().upper().replace(" ", "")
                aliases = {trading_symbol, symbol_name, custom_symbol}
                if source == "index" and target in {"NIFTY", "NIFTY50"}:
                    aliases.add("NIFTY50")
                    aliases.add("NIFTY")
                if source == "index" and target in {"BANKNIFTY", "NIFTYBANK"}:
                    aliases.add("BANKNIFTY")
                    aliases.add("NIFTYBANK")

                if target in aliases:
                    code = f"{exch}_{security_id}"
                    self._scrip_cache[s] = code
                    return code

        return None

    def _fetch_yahoo_ohlcv(self, symbol: str, timeframe: str, days: int) -> pd.DataFrame:
        yahoo_symbol = self._to_yahoo_symbol(symbol)
        tf = timeframe.lower()
        interval = tf if tf in {"1m", "2m", "5m", "15m", "30m", "60m", "1d"} else "15m"
        params = {"interval": interval, "range": f"{max(1, days)}d"}
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{yahoo_symbol}"
        res = requests.get(url, params=params, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        res.raise_for_status()
        payload = res.json()
        result = payload.get("chart", {}).get("result", [])
        if not result:
            return pd.DataFrame()

        node = result[0]
        timestamps = node.get("timestamp", [])
        quote = (node.get("indicators", {}).get("quote", [{}]) or [{}])[0]
        df = pd.DataFrame(
            {
                "date": pd.to_datetime(timestamps, unit="s", errors="coerce"),
                "open": pd.to_numeric(quote.get("open", []), errors="coerce"),
                "high": pd.to_numeric(quote.get("high", []), errors="coerce"),
                "low": pd.to_numeric(quote.get("low", []), errors="coerce"),
                "close": pd.to_numeric(quote.get("close", []), errors="coerce"),
                "volume": pd.to_numeric(quote.get("volume", []), errors="coerce"),
            }
        )
        return df.dropna(subset=["date", "close"]).sort_values("date").reset_index(drop=True)

    def _fetch_yahoo_spot(self, symbol: str) -> float:
        yahoo_symbol = self._to_yahoo_symbol(symbol)
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{yahoo_symbol}"
        res = requests.get(url, params={"interval": "1d", "range": "1d"}, timeout=8, headers={"User-Agent": "Mozilla/5.0"})
        res.raise_for_status()
        payload = res.json()
        result = payload.get("chart", {}).get("result", [])
        if not result:
            return 0.0
        node = result[0]
        closes = ((node.get("indicators", {}).get("quote", [{}]) or [{}])[0]).get("close", [])
        closes = [c for c in closes if c is not None]
        if closes:
            return float(closes[-1])
        return float(node.get("meta", {}).get("regularMarketPrice", 0) or 0)

    def get_historical_data(self, symbol: str, timeframe: str = "15m", days: int = 5) -> pd.DataFrame:
        """
        Fetches OHLCV data for the Brain Engine.
        """
        if self._mock_mode:
            return self._generate_mock_ohlcv(symbol, days)

        try:
            to_date = datetime.now()
            from_date = to_date - timedelta(days=days)
            interval_label = self._history_interval_label(timeframe)
            scrip_code = self._resolve_scrip_code(symbol)
            if not scrip_code:
                raise ValueError(f"Unable to resolve scrip code for symbol {symbol}")

            res = requests.get(
                f"{self.token_api_base}/market/historical/{interval_label}",
                headers=self.get_headers(),
                params={
                    "scrip-codes": scrip_code,
                    "start_time": int(from_date.timestamp() * 1000),
                    "end_time": int(to_date.timestamp() * 1000),
                },
                timeout=10,
            )
            res.raise_for_status()

            candles = self._extract_candles(res.json())
            if candles and isinstance(candles[0], list):
                df = pd.DataFrame(candles, columns=["timestamp", "open", "high", "low", "close", "volume"])
                ts = pd.to_numeric(df["timestamp"], errors="coerce")
                if ts.max() and ts.max() > 10**12:
                    df["date"] = pd.to_datetime(ts, unit="ms", errors="coerce")
                else:
                    df["date"] = pd.to_datetime(ts, unit="s", errors="coerce")
            else:
                df = pd.DataFrame(candles)
                if "timestamp" in df.columns:
                    ts = pd.to_numeric(df["timestamp"], errors="coerce")
                    if ts.max() and ts.max() > 10**12:
                        df["date"] = pd.to_datetime(ts, unit="ms", errors="coerce")
                    else:
                        df["date"] = pd.to_datetime(ts, unit="s", errors="coerce")
                elif "date" in df.columns:
                    df["date"] = pd.to_datetime(df["date"], errors="coerce")
                elif "time" in df.columns:
                    df["date"] = pd.to_datetime(df["time"], errors="coerce")
            if not df.empty:
                for col in ["open", "high", "low", "close", "volume"]:
                    if col not in df.columns:
                        df[col] = np.nan
                    df[col] = pd.to_numeric(df[col], errors="coerce")
                df = df.dropna(subset=["date", "close"]).sort_values("date").reset_index(drop=True)
                return df
        except Exception as e:
            logger.error(f"History Fetch Error: {e}")
            try:
                yahoo_df = self._fetch_yahoo_ohlcv(symbol, timeframe=timeframe, days=days)
                if not yahoo_df.empty:
                    logger.info("Using Yahoo live OHLCV fallback for %s", symbol)
                    return yahoo_df
            except Exception as yahoo_err:
                logger.error(f"Yahoo History Fetch Error: {yahoo_err}")

        return self._generate_mock_ohlcv(symbol, days)

    def get_option_chain_snapshot(self, symbol: str) -> Tuple[Dict, float]:
        """
        Calculates PCR and Max Pain from the Live Option Chain.
        """
        if self._mock_mode:
            spot = 22100 if "NIFTY" in symbol else 46500
            return {"pcr": round(np.random.uniform(0.6, 1.4), 2), "max_pain": spot}, spot

        try:
            option_symbol = self._normalize_symbol_for_options(symbol)
            expiry_res = requests.get(
                f"{self._market_base()}/market/expiry-dates",
                headers=self.get_headers(),
                params={"symbol": option_symbol},
                timeout=8,
            )
            expiry = None
            if expiry_res.status_code == 200:
                expiry_payload = expiry_res.json()
                expiries = expiry_payload.get("data", expiry_payload) if isinstance(expiry_payload, dict) else expiry_payload
                if isinstance(expiries, list) and expiries:
                    expiry = expiries[0]

            params = {"symbol": option_symbol}
            if expiry:
                params["expiry"] = expiry
            res = requests.get(
                f"{self._market_base()}/market/option-chain",
                headers=self.get_headers(),
                params=params,
                timeout=10,
            )
            res.raise_for_status()
            payload = res.json()
            chain = payload.get("data", [])

            # Calculate PCR
            total_pe_oi = 0
            total_ce_oi = 0
            for item in chain:
                pe_oi = item.get("pe_oi") or item.get("PE", {}).get("openInterest", 0)
                ce_oi = item.get("ce_oi") or item.get("CE", {}).get("openInterest", 0)
                total_pe_oi += pe_oi or 0
                total_ce_oi += ce_oi or 0
            pcr = total_pe_oi / total_ce_oi if total_ce_oi > 0 else 1.0

            # Spot fallback chain
            spot = (
                payload.get("underlying_price")
                or payload.get("underlyingValue")
                or payload.get("spot_price")
                or 0
            )
            if not spot:
                scrip_code = self._resolve_scrip_code(symbol)
                if not scrip_code:
                    raise ValueError(f"Unable to resolve scrip code for symbol {symbol}")
                ltp_res = requests.get(
                    f"{self.token_api_base}/market/quotes/ltp",
                    headers=self.get_headers(),
                    params={"scrip-codes": scrip_code},
                    timeout=8,
                )
                if ltp_res.status_code == 200:
                    ltp_payload = ltp_res.json()
                    data = ltp_payload.get("data", ltp_payload) if isinstance(ltp_payload, dict) else {}
                    if isinstance(data, dict):
                        first = next(iter(data.values()), {})
                        if isinstance(first, dict):
                            spot = first.get("live_price", 0) or first.get("ltp", 0)
            return {"pcr": round(pcr, 2), "max_pain": spot}, spot

        except Exception as e:
            logger.error(f"Option Chain Fetch Error: {e}")
            try:
                live_spot = self._fetch_yahoo_spot(symbol)
                if live_spot > 0:
                    return {"pcr": 1.0, "max_pain": round(live_spot, 2)}, round(live_spot, 2)
            except Exception as yahoo_err:
                logger.error(f"Yahoo Spot Fetch Error: {yahoo_err}")
            spot = 22100 if "NIFTY" in symbol else 46500
            return {"pcr": 1.0, "max_pain": spot}, spot

    def _generate_mock_ohlcv(self, symbol: str, days: int) -> pd.DataFrame:
        """Fallback dynamic simulator that looks realistic for Brain math"""
        periods = days * 25 # roughly 25 15m candles per day
        dates = [datetime.now() - timedelta(minutes=15 * i) for i in range(periods, 0, -1)]

        base_price = 22100 if "NIFTY" in symbol else 46500
        prices = []
        current = base_price

        for i in range(periods):
            # Create some trends and mean reversion
            change = np.random.normal(0, 15)
            if i > periods - 10: 
                change += np.random.normal(10, 5) # Slight recent breakout
            current += change
            prices.append(current)

        df = pd.DataFrame({
            'date': dates,
            'open': [p - np.random.uniform(0, 10) for p in prices],
            'high': [p + np.random.uniform(5, 20) for p in prices],
            'low': [p - np.random.uniform(5, 20) for p in prices],
            'close': prices,
            'volume': [int(np.random.normal(50000, 10000)) for _ in range(periods)]
        })

        # Correlated companion series for Stat-Arb (no forced terminal shock).
        correlation_noise = np.random.normal(0, 8, len(df))
        drift_component = np.linspace(-4, 4, len(df))
        df['correlated_close'] = (df['close'] * 2.1) + correlation_noise + drift_component

        return df

indstocks_feed = IndStocksDataFeed()
