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

#### 2026-04-13 21:52:12 IST
- Cleaned up simulator bias in Stat-Arb mock path by removing hardcoded terminal anomaly injection.
- Updated `backend/services/data/indstocks_feed.py`:
  - removed `correlated_close += 150` forced spike in `_generate_mock_ohlcv()`,
  - retained correlated series behavior with mild noise/drift only.
- Updated `backend/services/brain/strategies.py`:
  - removed the fallback `correlated_close += 150` injection in `SimonsStatArbStrategy`,
  - fallback correlated series now uses neutral noise without forced Z-score distortion.

#### 2026-04-13 23:32:00 IST
- Deep research on free & safe NSE data feed alternatives to INDmoney (Angel One SmartAPI, Upstox v3, DhanHQ, Fyers API v3, NSE direct scrape) — documented safest layered strategy for historical OHLCV + live LTP + option chain (PCR/max-pain).

#### 2026-04-13 23:45:00 IST
- Expanded strategy universe from 20 stocks → full NSE F&O eligible universe (185 symbols).
- Created `backend/services/brain/nse_universe.py`:
  - `INDEX_SYMBOLS` list: NIFTY, BANKNIFTY, FINNIFTY, MIDCPNIFTY (all 5 strategies run on these).
  - `FNO_STOCKS` list: 181 NSE F&O eligible stocks (VolBreakout, StatArb, SentimentConvergence run on these).
  - Helper functions: `get_index_symbols()`, `get_fno_stocks()`, `get_full_universe()`.
- Created `backend/services/brain/market_scanner.py`:
  - `run_full_scan()` — concurrent 12-thread scan across all 185 symbols via `ThreadPoolExecutor`.
  - Automatic strategy routing: options strategies (OI Gravity, PCR Fade) skipped for equity stocks.
  - Results sorted by confidence desc → kelly_pct desc.
- Updated `backend/models/database.py`:
  - Added `ScanResult` table: symbol, strategy, action, instrument, entry/target/sl, confidence, kelly_pct, qty, capital_allocated, rationale, timeframe, days_lookback, is_index, outcome (PENDING/WIN/LOSS/SKIP), outcome_pnl, scanned_at, resolved_at.
- Updated `backend/routers/brain.py` — 3 new endpoints:
  - `GET /brain/scan` — runs full 185-symbol scan, saves results to DB.
  - `GET /brain/scan/history` — view historical signals filtered by strategy/symbol/outcome.
  - `GET /brain/scan/performance` — win rate + avg PnL per strategy for performance testing.

#### 2026-04-14 00:10:00 IST
- Created `frontend/src/pages/Strategy.tsx` (564 lines) — Strategy Scanner page:
  - 5 independent strategy cards (OI Gravity, PCR Fade, Vol Breakout, Sentiment Convergence, Stat-Arb).
  - Each card has its own isolated loading/error/signal state — NO automated fetch, manual-only.
  - Per-strategy "Run Strategy" button triggers individual scan via `/brain/scan?strategy=<filter>`.
  - Global "Run All 5" button runs all strategies concurrently via `Promise.allSettled`.
  - Capital input + timeframe selector (5m / 15m / 30m / 1h / 1d) at page level.
  - Results table per card: Symbol → Entry → Target → SL → Confidence% → R:R ratio.
  - "Paper" button on every signal row — writes to Trade Journal with full metadata pre-filled.
  - Signal count banner + empty state handling.
- Updated `frontend/src/lib/api.ts`: added `strategyApi.runScan()`, `.getHistory()`, `.getPerformance()`.
- Updated `frontend/src/App.tsx`: added `/strategy` route.
- Updated `frontend/src/components/layout/Sidebar.tsx`: added "Strategy" nav link with Target icon.

#### 2026-04-13 23:49:30 IST
- **Phase 1 started:** Added dynamic broad NSE universe loading for scanner runs (no longer hardcoded-only).
- Updated `backend/services/brain/nse_universe.py`:
  - Added live universe fetch from INDstocks instruments endpoint (`source=equity`).
  - Added caching (6h TTL) and safe fallback to static F&O list when live fetch fails.
  - Added `get_nse_equities(refresh=False)` API for scanner consumption.
- Updated `backend/services/brain/market_scanner.py`:
  - Switched scanner universe source from static `get_fno_stocks()` to dynamic `get_nse_equities()`.
- Updated `backend/routers/brain.py` docs/comments to reflect broad NSE dynamic scan semantics.

#### 2026-04-13 23:53:23 IST
- Added **sequential batch processing** to NSE scanner to avoid running full universe in one burst.
- Updated `backend/services/brain/market_scanner.py`:
  - New controls: `batch_size`, `pause_between_batches_sec`, `max_symbols`, `symbol_offset`.
  - Scanner now processes symbols batch-by-batch with optional pause between batches.
  - Added richer `scan_meta` (batch count, offsets, caps) for operational tracking.
- Updated `backend/routers/brain.py` `/brain/scan` endpoint:
  - Exposed new query params for batch scan control (weekend-friendly throttled runs).
- Smoke-tested scanner with small sample:
  - `max_symbols=40`, `batch_size=20`, `pause_between_batches_sec=0.2`,
  - completed 2 batches sequentially without burst fanout.

#### 2026-04-13 23:54:45 IST
- Updated scanner to **stocks-only mode** (no options/F&O analysis in scan path).
- Updated `backend/services/brain/market_scanner.py`:
  - Removed index/options strategy routing from full scan flow.
  - Scanner now runs only equity-compatible strategies:
    - VolatilityBreakout
    - SentimentConvergence
    - SimonsStatArb
  - Removed option-chain dependency from scanner symbol evaluation.
  - `scan_meta.index_symbols` now remains `0` in this mode.
- Updated `backend/routers/brain.py` docs for `/brain/scan` to reflect stocks-only behavior.

#### 2026-04-13 23:56:47 IST
- Added **quality prefilter** to dynamic NSE universe ingestion to reduce noisy/unusable symbols before scan:
  - switched to prefer `TRADING_SYMBOL` over verbose company-name fields,
  - restricted to tradable NSE equity series (`EQ`, `BE`, `BZ`),
  - enforced symbol hygiene regex and removed symbols containing spaces.
- Updated `backend/services/brain/nse_universe.py` with this prefilter logic.
- Result: dynamic universe reduced from ~3167 symbols to ~2624 cleaner scanner candidates.

#### 2026-04-14 00:12:27 IST
- Implemented **Phase 2: Candidate Quality + Journal Pipeline** for stock scanner.
- Updated `backend/services/brain/market_scanner.py`:
  - Added stock signal normalization:
    - forces `instrument="EQ"`,
    - strips option legs (`legs=[]`),
    - converts qty/capital sizing to equity-compatible values.
  - Added ranking metrics:
    - computed `rr`,
    - computed `recommendation_score`,
    - generated `shortlist` from top-ranked signals.
  - Added run metadata:
    - `run_id` for traceability,
    - `shortlist_count` and `shortlist_limit` in `scan_meta`.
  - Added symbol-quality exclusion tokens (ETF/BEES/liquid-style non-stock symbols).
- Updated `backend/routers/brain.py` `/brain/scan`:
  - New query param: `shortlist_limit`,
  - New query param: `save_paper_trades`,
  - `save_paper_trades=true` logs shortlist entries to `trades` table with `run_id` and score in notes.
- Validation:
  - `/brain/scan` now returns `run_id`, `shortlist`, and normalized `EQ` suggestions,
  - scanner-created paper trade successfully appears in `/api/trades`.

---

## 11. Master Development Roadmap (Adopted 2026-04-14)

The canonical build sequence from current state to a self-optimizing trading system. Scanner phases labeled **A–G**. AI layer phases labeled **AI Phase 0–3** (see `NEXUS_AI_Rollout_Plan.md`).

**Core principle:** No learning claims without outcome data. Phase C (Outcome Resolver) is the critical gate — nothing downstream is valid without it.

### Phase A — Stabilize Scanner (1–2 days)
- Tighten stock universe filters: extend ETF/BEES/index-derivative exclusion list, restrict to `EQ` series only
- Hard-cap every scan run to exactly top 5 ranked candidates (`recommendation_score` desc)
- Add deduplication: one entry per symbol across all strategies in a single run
- Add `scan_quality_flags` to `scan_meta` for operational visibility

### Phase B — Journal Pipeline (1 day)
- Auto-save shortlist to paper journal on every scan (`save_paper_trades=true` default)
- Prevent duplicate inserts: check `symbol + strategy + run_id` before insert
- Add `source` column to `Trade` table (`manual` | `scanner` | `autonomous`)
- Add `run_id` column to `Trade` table — populated for all scanner-sourced trades
- Show `source` badge on PaperTrade.tsx rows

### Phase C — Outcome Resolver (2–3 days) ← CRITICAL GATE
- New file: `backend/services/brain/outcome_resolver.py`
- Walks OHLC candles forward from each trade's entry: marks `WIN` / `LOSS` / `OPEN` / `SKIP`
- Computes `realized_r` and `realized_pnl_pct` per trade
- New columns on `Trade`: `outcome`, `realized_pnl`, `realized_pnl_pct`, `realized_r`, `resolved_at`, `resolver_notes`
- New endpoints: `POST /brain/resolve`, `POST /brain/resolve/{trade_id}`
- APScheduler job: auto-resolves all open trades daily at 4:00 PM IST
- Updates `/brain/scan/performance` to use resolved trade data (not raw signal count)

### Phase D — Weekly Analytics (2 days)
- New file: `backend/services/analytics/weekly_report.py` — builds full Friday report
- Metrics: win rate by strategy, avg R / expectancy, regime slices, top failure patterns, best/worst symbols
- New router: `backend/routers/analytics.py` — endpoints: `/analytics/weekly-report`, `/analytics/strategy-performance`, `/analytics/symbol-performance`
- New page: `frontend/src/pages/Analytics.tsx` — full report UI, manual refresh only

### Phase E — RAG Memory (4–6 days)
- Full AI layer infrastructure (see `NEXUS_AI_Rollout_Plan.md` → AI Phase 0 + AI Phase 1)
- Groq LLM client, ChromaDB lesson store, RAG pipeline, feedback loop, context builder
- "Ask AI" button live on Strategy page, AI Lesson card on PaperTrade page
- Entry gate: Phase C must be complete + `GROQ_API_KEY` set + 10+ resolved trades

### Phase F — Confidence Layer (3–4 days)
- AI-adjusted confidence scores on every signal (see `NEXUS_AI_Rollout_Plan.md` → AI Phase 2)
- Regime-based win rate multiplier: `ai_confidence = base × regime_win_rate_multiplier`
- Thresholding: Green ≥ 70%, Yellow 50–69%, Red < 50% (signals never hidden — human decides)
- Daily brief widget on Overview page

### Phase G — 60–90 Day Optimization (Ongoing from ~Day 60)
- Weekly minor parameter adjustments only — one parameter per strategy per week max
- Every adjustment logged in this MD with: `{ parameter, old_value, new_value, reason, sample_size }`
- Track out-of-sample result the following week; revert if 2 consecutive weeks show regression
- Alpha Candidate Score = `(win_rate × avg_R × sample_size_weight) - regime_volatility_penalty`
- Target: Alpha Score > 0.6 for 2+ strategies by Week 12

### Operating Cadence
- **Weekend / Mon pre-open:** Run batched NSE scan → log top 5 paper trades
- **Daily 4 PM auto:** Outcome resolver fires (APScheduler)
- **Friday post-close:** Weekly analytics report + AI coaching query + MD changelog update

---

## 12. AI Layer Plan (Separate from Scanner Phases)

The AI learning layer is documented in full in `NEXUS_AI_Rollout_Plan.md`. Summary:
- **AI Phase 0:** Groq LLM + ChromaDB infrastructure + signal explainer (runs in parallel with Scanner Phase E)
- **AI Phase 1:** Feedback loop — auto-write lessons to ChromaDB on every trade close
- **AI Phase 2:** Regime classifier + AI confidence modifiers + daily brief
- **AI Phase 3:** Free-form coach, benching alerts, entry refinement rules
- LLM stack: Groq API (primary, free) | Ollama optional stub only (not built)
- "Learning" mechanism: RAG over growing ChromaDB lesson library — not model fine-tuning

