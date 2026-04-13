# NEXUS TRADING SYSTEM — Master LLM Context Sync

**IMPORTANT FOR ANY LLM OR AI AGENT READING THIS FILE:**
This document contains the absolute, comprehensive history and technical context of the "NEXUS Trading System" build. The user and a previous AI developed this system collaboratively. Use this document to instantly synchronize your memory with the project's architecture, mathematical models, and design philosophy so you can seamlessly continue development without asking redundant questions.

---

## 1. Project Vision & Core Philosophy
NEXUS is a production-grade, quantitative trading dashboard and autonomous algorithmic execution engine built specifically for the **Indian Stock Market (NSE/BSE)**. 

**The Goal:** Build an institutional-grade system (inspired by Renaissance Technologies) that removes human emotion. It ingests live market data, reads global sentiment via NLP, mathematically identifies high-probability setups, calculates precise position sizing via the Kelly Criterion, and either suggests them to the user via a UI or trades them autonomously.

## 2. Tech Stack & Architecture
* **Frontend:** React (TypeScript), Vite, Tailwind CSS (Custom "Nexus" dark mode design system), React Query, Lucide Icons, TradingView Advanced Chart Widget.
* **Backend:** Python, FastAPI, Pandas, SQLAlchemy, SQLite (`data/trade_journal.db`).
* **Broker Integration:** **INDmoney / INDstocks Developer API**. 
* **Failsafe Design:** EVERY external API integration (Broker, Reddit, News) has a built-in **Auto-Fallback Simulator**. If API keys are missing or the market is closed, the backend seamlessly generates realistic mock ticks, option chains, and NLP news headlines so the frontend UI never breaks and can be tested 24/7.

---

## 3. Data Ingestion Layer (`indstocks_feed.py` & `scraper.py`)
1. **Market Data:** Connects to the INDstocks REST/WebSocket APIs using JWT Auth. Fetches historical 15m/1D OHLCV data and live Option Chain snapshots (to calculate Put-Call Ratio and Max Pain).
2. **Social Sentiment Scraper:** 
   * **Reddit (`praw`):** Scrapes `r/IndianStreetBets` and `r/IndiaInvestments`.
   * **News RSS:** Scrapes Top 10 Indian business publishers (MoneyControl, Economic Times, LiveMint, Business Standard, CNBC, etc.).
3. **NLP Engine (`nlp.py`):** Uses a custom, lightweight financial lexicon to score scraped text from `-1.0` (Extreme Fear) to `1.0` (Extreme Greed), aggregating into a global Fear/Greed Index.

---

## 4. The NEXUS Brain (The 5 Quant Strategies)
The `QuantEngine` (`engine.py`) runs 5 independent mathematical strategies over the data. 

1. **OI Gravity (Iron Condor):** Sells non-directional premium when PCR is neutral (0.8-1.2) by building walls around the Max Pain strike.
2. **PCR Momentum Fade:** Fades extreme retail emotion. Buys Calls when PCR < 0.6 at the lower Bollinger Band. Buys Puts when PCR > 1.4 at the upper Bollinger Band.
3. **Volatility Breakout:** Triggers when current ATR compresses, followed by a sudden price breakout accompanied by a 2.5x volume surge.
4. **Sentiment Convergence:** A macro strategy. Triggers Long when price is structurally bullish (> 50 EMA) AND the NLP Sentiment Engine detects extreme internet euphoria (Score > 0.75).
5. **Renaissance Stat-Arb (Pairs Trading):** *Requested by user based on Jim Simons' Medallion Fund.* Tracks highly correlated assets (e.g., NIFTY and BANKNIFTY). Calculates a 20-period rolling Mean and StdDev of their price ratio. If the **Z-Score** breaks `+2.0` or `-2.0`, the math implies the relationship has temporarily broken. The bot enters a mean-reversion trade to fade the anomaly.

---

## 5. Risk Management & Position Sizing
* **The Half-Kelly Criterion (`strategies.py`):** Calculates sizing based on the formula: `f = W - ((1 - W) / R)` where `W` is historical win rate and `R` is the Risk/Reward ratio of the specific setup.
* **Safety Caps:** The raw Kelly output is halved (Half-Kelly) to reduce volatility drawdown, and hard-capped so no single trade ever risks more than **10%** of the user's inputted capital base.
* **Swing Trade Cap:** Swing trades are hard-capped to a strict **2%** risk per trade.

---

## 6. The Autonomous Daemon (`autonomous.py`)
To make NEXUS self-sufficient, an asynchronous daemon runs alongside the FastAPI server.
* **Tick Rate:** Scans the market every 60 seconds (9:15 AM - 3:30 PM).
* **Execution:** If a strategy fires, it mathematically sizes the trade and automatically commits it to the SQLite `trades` table. (Max 3 concurrent open trades allowed).
* **Dynamic Trailing Stop-Loss:**
  * Moves SL to **Breakeven** when the trade is 50% toward the target.
  * Trails SL to **lock in 50% of total profit** when the trade is 80% toward the target.
* **Reinforcement Learning (Feedback Loop):** Tracks the win/loss record of each strategy. Winning strategies get their sizing modifier bumped (up to 1.5x). Losing strategies get heavily penalized. If a strategy's modifier drops below `0.5x`, the bot temporarily "benches" it until market conditions change.

---

## 7. The Swing Screener (`screener.py`)
* **Universe:** Restricted to the 20 most highly liquid NSE F&O stocks (Reliance, HDFC, Infy, etc.) to ensure technicals are respected.
* **Timeframe:** Daily (`1D`) candles, 100-day lookback.
* **Setups:** 
  1. *Volume Breakout:* Price > 20 & 50 SMA, Volume > 2.5x average, RSI > 60.
  2. *Mean Reversion:* Price in structural uptrend (20 SMA > 50 SMA) but RSI crashed < 30 (Dip Buy).
* The Autonomous Bot scans this universe every 10 minutes.

---

## 8. Frontend UI / UX (`Analysis.tsx` & Dashboard)
* **TradingView Integration:** Uses the official TradingView Advanced Chart Widget. No API keys needed. The UI dynamically maps internal symbols (`NIFTY`) to TV symbols (`NSE:NIFTY`). 
* **Split-Screen Command Center:** Left side = Live TradingView Chart. Right side = Feed of Intraday Option setups + Live Swing Screener setups. Clicking a stock on the screener instantly loads it in the TradingView chart.
* **Execution Workflow:** 
  * *Paper Trade:* Saves to the local SQLite DB for tracking Win Rate, PnL, and AI notes.
  * *Stage in IndMoney:* Loops over the strategy's exact options legs and fires live POST requests to the INDstocks API to execute real money.

---

## Context Restored
If you are an AI reading this, you now know exactly what the codebase looks like, what libraries are used, and the mathematical philosophies governing the logic. You may proceed to answer the user's next request seamlessly.

---

## 9. Change Log Discipline (Mandatory)
- **Rule:** Every time any code/config/behavior is changed in this project, append an entry to this file with the exact **date and time** and a brief summary of what changed.
- This log must be maintained continuously so this document always contains a full running history of system changes.

### Change Log Entries

#### 2026-04-13 21:24:38 IST
- Integrated live-data-first behavior in `indstocks_feed.py` with robust fallback handling.
- Added INDmoney scrip-code based historical mapping via instruments master and corrected historical interval path handling.
- Tuned swing screener logic (`screener.py`) to improve actionable output in quiet markets:
  - relaxed breakout thresholds,
  - added ranked momentum watchlist fallback,
  - introduced `score` and `signal_strength` (`A/B/C`).
- Added screener API filters in `backend/routers/screener.py`:
  - `min_strength` query param (`A|B|C`),
  - `limit` query param for top-N results.
- Added paper-trade delete support:
  - API client `DELETE` helper and `tradesApi.deleteTrade(...)` in `frontend/src/lib/api.ts`,
  - delete action button + mutation in `frontend/src/pages/PaperTrade.tsx`.
- Confirmed journal tracking behavior: "Add to Journal" writes to `trades` table (paper-trade log), while daily notes are stored separately in `journal`.
