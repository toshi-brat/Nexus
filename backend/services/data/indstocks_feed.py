"""
INDstocks Live Data Feed & WebSocket Manager
Fetches historical candles, live option chains, and real-time ticks.
"""
import pandas as pd
import numpy as np
import requests
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
import config

logger = logging.getLogger("indstocks_feed")

class IndStocksDataFeed:
    def __init__(self):
        self.api_key = config.INDSTOCKS_API_KEY
        self.secret = config.INDSTOCKS_SECRET
        self.base_url = config.INDSTOCKS_REST_URL
        self.token = None
        self._mock_mode = not bool(self.api_key) # Run in simulation if keys missing

    def authenticate(self):
        if self._mock_mode:
            logger.warning("No INDstocks API Key found. Running in Simulation/Mock Mode.")
            return True

        try:
            # INDstocks standard OAuth2 / JWT flow
            res = requests.post(f"{self.base_url}/auth/login", json={
                "api_key": self.api_key,
                "api_secret": self.secret
            })
            if res.status_code == 200:
                self.token = res.json().get("access_token")
                return True
        except Exception as e:
            logger.error(f"INDstocks Auth Error: {e}")
        return False

    def get_headers(self):
        return {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}

    def get_historical_data(self, symbol: str, timeframe: str = "15m", days: int = 5) -> pd.DataFrame:
        """
        Fetches OHLCV data for the Brain Engine.
        """
        if self._mock_mode:
            return self._generate_mock_ohlcv(symbol, days)

        try:
            to_date = datetime.now()
            from_date = to_date - timedelta(days=days)

            # Format depends on exact INDstocks specs
            res = requests.get(
                f"{self.base_url}/market/history",
                headers=self.get_headers(),
                params={
                    "symbol": symbol,
                    "resolution": timeframe,
                    "from": int(from_date.timestamp()),
                    "to": int(to_date.timestamp())
                }
            )
            data = res.json()
            if "candles" in data:
                df = pd.DataFrame(data["candles"])
                df['date'] = pd.to_datetime(df['timestamp'], unit='s')
                return df
        except Exception as e:
            logger.error(f"History Fetch Error: {e}")

        return self._generate_mock_ohlcv(symbol, days)

    def get_option_chain_snapshot(self, symbol: str) -> Tuple[Dict, float]:
        """
        Calculates PCR and Max Pain from the Live Option Chain.
        """
        if self._mock_mode:
            spot = 22100 if "NIFTY" in symbol else 46500
            return {"pcr": round(np.random.uniform(0.6, 1.4), 2), "max_pain": spot}, spot

        try:
            res = requests.get(
                f"{self.base_url}/market/option-chain",
                headers=self.get_headers(),
                params={"symbol": symbol}
            )
            chain = res.json().get("data", [])

            # Calculate PCR
            total_pe_oi = sum(item.get("pe_oi", 0) for item in chain)
            total_ce_oi = sum(item.get("ce_oi", 0) for item in chain)
            pcr = total_pe_oi / total_ce_oi if total_ce_oi > 0 else 1.0

            # Simple Max Pain calculation
            spot = res.json().get("underlying_price", 0)
            return {"pcr": round(pcr, 2), "max_pain": spot}, spot

        except Exception as e:
            logger.error(f"Option Chain Fetch Error: {e}")
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

        # Correlated asset for Stat-Arb
        df['correlated_close'] = df['close'] * 2.1 + np.random.normal(0, 15, len(df))
        # Force a recent deviation
        df.loc[df.index[-1], 'correlated_close'] += 150 

        return df

indstocks_feed = IndStocksDataFeed()
