# NEXUS Strategies Guide & Formulas

This document details the exact entry and exit parameters for the 4 ensemble strategies currently running in `strategies.py`. 
Use this guide to understand *why* the Brain is suggesting a trade, and what parameters to tweak during our daily reviews.

---

### 1. OI Gravity Engine (Range-Bound / Theta Decay)
**Philosophy:** Markets chop around max pain. Retail buys lottery tickets; institutions sell them. We side with the sellers.
* **Condition:** Put-Call Ratio (PCR) is neutral (`0.8 <= PCR <= 1.2`).
* **Trigger:** Current price is near Max Pain.
* **Action:** `SELL` an Iron Condor. 
* **Calculation:** Short Call Strike = `Max Pain + 300` / Short Put Strike = `Max Pain - 300`. Buy 100 points further out for margin protection.
* **Tweak Candidates:** Try widening to 400 points. Add a VIX minimum (>13) to ensure premiums are worth the risk.

### 2. PCR Momentum Fade (Contrarian Reversal)
**Philosophy:** Retail traders panic at the absolute bottom and top. We fade extremes.
* **Condition 1:** Extreme Fear (`PCR < 0.6`) OR Extreme Greed (`PCR > 1.4`).
* **Condition 2:** Price pierces the Bollinger Bands (`20 SMA ± 2 STD`).
* **Action:** `BUY` a Call (Oversold) or `BUY` a Put (Overbought).
* **Calculation:** Stop Loss is exactly 1 Standard Deviation below entry. Target is the 20 SMA.
* **Tweak Candidates:** Adjust PCR boundaries specifically for Nifty vs BankNifty. 0.6 might be right for Nifty, but 0.5 for BankNifty.

### 3. Volatility Breakout (Trend Following)
**Philosophy:** Long periods of low volatility lead to explosive directional moves.
* **Condition:** Average True Range (ATR 14) drops to a 10-day minimum. Volatility is compressed.
* **Trigger:** Volume spikes to > 1.5x the 10-day average volume AND price breaks the 3-day high.
* **Action:** `BUY` Directional (Call/Put).
* **Calculation:** Stop loss is `1 * ATR`. Target is `3 * ATR` (1:3 Risk/Reward).
* **Tweak Candidates:** Wait for 5-minute close above the high to avoid false wicks. Change Volume multiplier to 2.0x.

### 4. Sentiment Convergence (Macro / NLP)
**Philosophy:** Technicals are useless if a major macro event happens. We align price action with AI sentiment.
* **Condition:** Price is trading above the 50-EMA.
* **Trigger:** FinBERT NLP sentiment score on top 10 news sites is overwhelmingly bullish (`Score > 0.75`).
* **Action:** `BUY` Directional Call Spread.
* **Calculation:** Stop loss is a daily close below the 50-EMA.
* **Tweak Candidates:** Combine this with FII/DII net buying data from the NSE fetcher.

---

### 5. Renaissance Stat-Arb (Pairs Trading / Cointegration)
**Philosophy:** Inspired by Jim Simons and Renaissance Technologies (The Medallion Fund). The core of their early success was identifying temporary pricing anomalies in highly correlated assets (e.g., NIFTY vs BANKNIFTY). They didn't care *why* the price moved; they cared that the mathematical relationship broke.
* **Condition:** Two assets have a historical correlation ratio (e.g., BankNifty is typically ~2.1x Nifty). 
* **Calculation:** We calculate the rolling 20-period Mean and Standard Deviation of this ratio to find the **Z-Score**.
* **Trigger:** If the Z-Score breaks `+2.0` or `-2.0`, the relationship has become statistically improbable. 
* **Action:** We fade the anomaly. If Nifty drops but BankNifty doesn't, we go Long Nifty (expecting it to catch up) or Short BankNifty (expecting it to correct).
* **Tweak Candidates:** Decrease the lookback window from 20 days to 20 minutes (high-frequency intraday). This is where statistical arbitrage shines. Ensure slippage and trading costs are near zero, as the edges are tiny but frequent.
