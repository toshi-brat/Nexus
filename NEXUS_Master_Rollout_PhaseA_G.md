# NEXUS — Master Development Roadmap (Phase A → G)

**Document Type:** Official Development Rollout Plan  
**Adopted:** 2026-04-14  
**Scope:** Scanner stabilization → journal pipeline → outcome resolution → analytics → RAG memory → confidence layer → 60–90 day optimization  
**Operating Cadence:** Weekend/Monday pre-open scans + Friday post-close analytics  

---

## Overview

This is the canonical development sequence for NEXUS post-scanner-build. It supersedes earlier draft phase numbering. Scanner phases are labeled **A–G**. The AI learning layer phases are labeled **AI Phase 0–3** (separate document: `NEXUS_AI_Rollout_Plan.md`).

The philosophy: **no learning claims without outcome data.** Every phase builds on verified, resolved trade outcomes — not just signals fired. The system earns the right to optimize only after it has measured itself honestly.

---

## Phase A — Stabilize Scanner

**Duration:** 1–2 days  
**Status:** 🔲 Not started  
**Depends on:** Current scanner build (Phase 2 complete)

### Goal
A single scan run returns exactly the top 5 ranked, clean, equity-only candidates every time. No noise, no ETFs, no duplicate symbols, no option legs leaking into the equity path.

### Work Items

**`backend/services/brain/nse_universe.py`**
- Extend symbol exclusion list:
  - ETF tickers (NIFTYBEES, BANKBEES, LIQUIDBEES, JUNIORBEES, GOLDBEES, SILVERBEES, MAFANG, MOM100, etc.)
  - Index derivatives masquerading as equity (NIFTYIT, NIFTYMID150, etc.)
  - Any symbol ending in `ETF`, `BEES`, `FUND`, `NIFTY` when not in index list
  - Illiquid series: restrict to `EQ` only (drop `BE`, `BZ` from equity scan — too illiquid)
- Add `MIN_SYMBOL_LENGTH = 2` and `MAX_SYMBOL_LENGTH = 20` guards
- Log excluded symbol count at startup for visibility

**`backend/services/brain/market_scanner.py`**
- Hard-cap results to top 5 by `recommendation_score` (already ranked — just slice `[:5]`)
- Add deduplication: if same symbol appears in multiple strategy results, keep only the highest-scored entry
- Ensure `shortlist_limit` defaults to `5` in all code paths
- Add `scan_quality_flags` to `scan_meta`:
  - `symbols_scanned`, `symbols_excluded`, `signals_raw`, `signals_after_dedup`, `shortlist_count`

**`backend/routers/brain.py`**
- Set default `shortlist_limit=5` on `/brain/scan`
- Validate: if scan returns 0 results, return structured empty response (not 500)

### Success Test
```
POST /brain/scan → returns exactly 5 results (or fewer only if universe genuinely yields < 5)
All symbols are plain equity tickers (no BEES, no ETF suffix)
No duplicate symbols across strategy rows
scan_meta.shortlist_count == len(results)
```

---

## Phase B — Journal Pipeline

**Duration:** 1 day  
**Status:** 🔲 Not started  
**Depends on:** Phase A complete

### Goal
Every scan run's top 5 automatically land in the paper trade journal with full traceability. Running the same scan twice does not create duplicate trades.

### Work Items

**`backend/routers/brain.py`**
- `save_paper_trades=true` path: before inserting each shortlist item, check DB for existing trade where `symbol == signal.symbol AND strategy == signal.strategy AND run_id == current_run_id`
- If exists: skip insert, log "duplicate skipped"
- If not exists: insert with:
  - `notes` field: `f"run_id={run_id} | score={recommendation_score:.2f} | rr={rr:.2f}"`
  - `source = "scanner"` (new field on trades table — add migration)
  - `status = "OPEN"`
  - `entry_price` = signal's entry value
  - `target_price`, `stop_loss` = from signal

**`backend/models/database.py`**
- Add `source` column to `Trade` table: `String(20)`, default `"manual"`, values: `"manual"` | `"scanner"` | `"autonomous"`
- Add `run_id` column to `Trade` table: `String(50)`, nullable — populated only for scanner-sourced trades

**`frontend/src/pages/PaperTrade.tsx`**
- Add `source` badge on each trade row:
  - `scanner` → teal chip "Scanner"
  - `manual` → no badge (clean)
  - `autonomous` → purple chip "Auto"
- Add `run_id` tooltip on scanner-sourced trades: shows full run_id on hover

### Success Test
```
POST /brain/scan?save_paper_trades=true → 5 trades appear in /api/trades
POST same scan again → no duplicates created, response notes "X duplicates skipped"
GET /api/trades → source field = "scanner" on those rows
PaperTrade.tsx shows "Scanner" badge on those rows
```

---

## Phase C — Outcome Resolver

**Duration:** 2–3 days  
**Status:** 🔲 Not started  
**Depends on:** Phase B complete + at least 1 day of open trades in journal

### Goal
An automated job evaluates all open paper trades against subsequent OHLC candles and marks each as `WIN` / `LOSS` / `OPEN` / `SKIP` with realized R-multiple. This is the most critical phase — **no learning or analytics can be trusted without it.**

### Work Items

**`backend/services/brain/outcome_resolver.py`** ← new file

```
Class: OutcomeResolver

Methods:
  resolve_all_open(db: Session) -> ResolverRunSummary
    — queries all trades where status == "OPEN" and source in ("scanner", "autonomous")
    — for each: calls _resolve_single_trade(trade, db)
    — returns: { resolved: int, still_open: int, errors: int }

  _resolve_single_trade(trade: Trade, db: Session) -> str (outcome)
    Flow:
      1. Fetch OHLCV candles from entry_time to now (daily candles, indstocks_feed)
      2. Walk candles forward from entry_time:
          — if any candle LOW ≤ trade.stop_loss → LOSS, record realized_pnl
          — if any candle HIGH ≥ trade.target_price → WIN, record realized_pnl
          — if neither hit and candle count < max_days → OPEN (check again later)
          — if candle count ≥ max_days (default 10) → SKIP (expired, no outcome)
      3. Compute:
          realized_r = (exit_price - entry_price) / (entry_price - stop_loss)
          realized_pnl_pct = (exit_price - entry_price) / entry_price * 100
      4. Update trade: status, outcome, realized_pnl, realized_r, resolved_at
      5. Return outcome string

  resolve_single(trade_id: int, db: Session) -> Trade
    — resolves one specific trade by id (for manual trigger)

Config:
  RESOLVER_MAX_DAYS = 10     (default holding period limit)
  RESOLVER_CANDLE_INTERVAL = "1d"
```

**`backend/models/database.py`** — New columns on `Trade`
```
outcome         String(10)   — WIN | LOSS | OPEN | SKIP, default OPEN
realized_pnl    Float        — actual pnl in INR when resolved
realized_pnl_pct Float       — pnl as % of entry
realized_r      Float        — R-multiple (1.0 = hit target, -1.0 = hit SL)
resolved_at     DateTime     — when outcome was determined
resolver_notes  Text         — e.g. "Hit SL on day 3, candle low 1408.5"
```

**`backend/routers/brain.py`** — New endpoints
```
POST /brain/resolve
  — triggers OutcomeResolver.resolve_all_open(db)
  — returns ResolverRunSummary

POST /brain/resolve/{trade_id}
  — resolves a single trade by id
  — returns updated Trade

GET /brain/scan/performance  (update existing)
  — now reads from resolved trades (outcome != OPEN)
  — returns: win_rate, avg_r, expectancy, total_resolved per strategy
```

**`backend/tasks/resolver_scheduler.py`** ← new file
```
— runs OutcomeResolver.resolve_all_open() once per day at 4:00 PM IST (post-market)
— uses APScheduler (already in requirements or add it)
— logs summary to console and appends to data/resolver_log.jsonl
```

### Success Test
```
Open paper trades exist with entry/target/sl populated
POST /brain/resolve → at least some trades get WIN/LOSS/SKIP status
GET /api/trades → resolved trades show outcome, realized_r, realized_pnl_pct
GET /brain/scan/performance → returns win_rate based on resolved trades (not just signal count)
Scheduler fires at 4:00 PM IST without manual trigger
```

---

## Phase D — Weekly Analytics

**Duration:** 2 days  
**Status:** 🔲 Not started  
**Depends on:** Phase C complete + at least 10 resolved trades

### Goal
A Friday post-close report endpoint that measures system performance honestly: win rate, R-expectancy, failure patterns, and regime slices. Simple UI section to view it.

### Work Items

**`backend/services/analytics/weekly_report.py`** ← new file

```
Class: WeeklyReportBuilder

Methods:
  build(db: Session, weeks_back: int = 4) -> WeeklyReport
    — pulls all resolved trades from last N weeks
    — computes:
        win_rate_by_strategy: { strategy: str, wins: int, losses: int, skips: int, win_rate: float }
        avg_r_by_strategy:    { strategy: str, avg_r: float, expectancy: float }
        regime_slices:        { regime: str, win_rate: float, sample_size: int }
        top_failure_patterns:
          — most common setup conditions in losing trades
          — e.g. "7/9 losses had RSI > 68 at entry"
          — e.g. "6/9 losses occurred on Mondays"
        best_performers:      top 3 symbols by win rate (min 3 trades)
        worst_performers:     bottom 3 symbols by win rate (min 3 trades)
        weekly_pnl_series:    [ { week: str, pnl_pct: float, trade_count: int } ]

Dataclass: WeeklyReport
  generated_at: str
  period_start: str
  period_end: str
  total_resolved: int
  overall_win_rate: float
  overall_expectancy: float
  win_rate_by_strategy: List[dict]
  avg_r_by_strategy: List[dict]
  regime_slices: List[dict]
  top_failure_patterns: List[str]
  best_performers: List[dict]
  worst_performers: List[dict]
  weekly_pnl_series: List[dict]
```

**`backend/routers/analytics.py`** ← new file
```
GET /analytics/weekly-report
  — params: weeks_back (default 4)
  — returns WeeklyReport JSON

GET /analytics/strategy-performance
  — returns win_rate + expectancy per strategy (all-time)

GET /analytics/symbol-performance
  — returns per-symbol win rate sorted desc
```

**`frontend/src/pages/Analytics.tsx`** ← new page
```
Sections:
  — Overall stats bar: total trades, win rate, avg R, expectancy
  — Strategy performance table: strategy | wins | losses | win_rate | avg_R | expectancy
  — Weekly P&L sparkline chart (weekly_pnl_series)
  — Regime slice table: regime | win_rate | sample_size
  — Top failure patterns: bulleted list of plain-English patterns
  — Best/worst performers: two side-by-side tables

Data source: GET /analytics/weekly-report (manual refresh button)
No auto-polling
```

**`frontend/src/App.tsx` + `Sidebar.tsx`**
- Add `/analytics` route
- Add "Analytics" nav link with BarChart2 icon

### Success Test
```
GET /analytics/weekly-report → non-empty JSON with all fields
Analytics page loads and renders all sections
Strategy performance table shows at least 1 row with real resolved data
Weekly P&L chart renders (even if only 1 data point)
```

---

## Phase E — RAG Memory

**Duration:** 4–6 days  
**Status:** 🔲 Not started  
**Depends on:** Phase C complete (resolved outcomes needed for lessons) + Groq API key  
**Reference:** See `NEXUS_AI_Rollout_Plan.md` → AI Phase 0 + AI Phase 1

### Goal
ChromaDB lesson store is live. Every closed trade writes a lesson. Every new signal retrieval includes similar past outcomes as context. "Ask AI" button live on Strategy page.

### Key Files
```
backend/services/ai/nexus_llm.py
backend/services/ai/memory_store.py
backend/services/ai/prompts.py
backend/services/ai/rag_pipeline.py
backend/services/ai/feedback_loop.py
backend/services/ai/context_builder.py
backend/routers/ai.py
frontend/src/components/ai/SignalExplainPanel.tsx
frontend/src/components/ai/TradeReviewCard.tsx
```

For full file-by-file spec, see `NEXUS_AI_Rollout_Plan.md` sections **Phase 0** and **Phase 1**.

### Entry Gate
- Phase C must be complete (resolved trades are the raw material for lessons)
- `GROQ_API_KEY` set in `.env` (free from console.groq.com)
- At least 10 resolved trades in DB before Phase E ships (so first RAG queries return real context)

---

## Phase F — Confidence Layer

**Duration:** 3–4 days  
**Status:** 🔲 Not started  
**Depends on:** Phase E complete + at least 30 closed trades in ChromaDB

### Goal
AI-adjusted confidence scores on every signal, thresholded flagging of low-confidence suggestions, regime-strategy correlation surfaced per scan. Human always in the loop — no autonomous overrides.

### Key Files
```
backend/services/ai/rag_pipeline.py     ← add confidence modifier logic
backend/services/ai/context_builder.py ← add regime win rate computation
backend/routers/ai.py                  ← add /ai/regime, /ai/performance-summary
frontend/src/pages/Strategy.tsx        ← add AI confidence badge, regime badge
frontend/src/pages/Overview.tsx        ← add DailyBriefWidget
frontend/src/components/ai/DailyBriefWidget.tsx
```

For full spec, see `NEXUS_AI_Rollout_Plan.md` section **Phase 2**.

### Confidence Threshold Rules
```
AI Adjusted Confidence ≥ 70%  → Green badge, proceed normally
AI Adjusted Confidence 50–69% → Yellow badge, "Proceed with caution"
AI Adjusted Confidence < 50%  → Red badge, "AI flags low confidence"
                                 Signal still shown — human decides
                                 Never hidden or auto-skipped
```

---

## Phase G — 60–90 Day Optimization

**Duration:** Ongoing, starting ~Day 60  
**Status:** 🔲 Not started  
**Depends on:** Phase F complete + 8+ weeks of weekly analytics data

### Goal
Weekly minor parameter adjustments based on out-of-sample performance. Build an alpha candidate score to converge toward a final, stable strategy blend. Nothing changes unless the data supports it.

### Operating Cadence

**Weekend / Monday Pre-Open**
```
1. Run batched NSE scan (batch_size=20, max_symbols=200, pause=0.5s)
2. Log top 5 to paper journal (save_paper_trades=true)
3. Check /ai/benching-alerts — any strategy to pause this week?
4. Review DailyBriefWidget for regime + watchlist heading into the week
```

**Friday Post-Close**
```
1. POST /brain/resolve → resolve all open trades from the week
2. GET /analytics/weekly-report → review win rate, avg R, failure patterns
3. Read AI coaching note (GET /ai/ask "What should I adjust this week?")
4. Log any parameter adjustment with reason in LLM_MASTER_CONTEXT.md changelog
5. Do not change more than 1 parameter per strategy per week
```

### Adjustment Rules
- Only adjust parameters with at least 10 observations for that strategy in the current regime
- Document every adjustment in the MD changelog with: `{ parameter, old_value, new_value, reason, sample_size }`
- Track "out-of-sample result" in the following week's analytics — did the adjustment help?
- Revert if 2 consecutive weeks show no improvement or regression

### Alpha Candidate Score (Phase G Target Metric)
```
Alpha Score = (Win Rate × Avg R × Sample Size Weight) - Regime Volatility Penalty

Where:
  Sample Size Weight = min(1.0, resolved_trades / 30)  — penalizes thin data
  Regime Volatility Penalty = std_dev(win_rate_across_regimes) × 0.5

Target by Week 12: Alpha Score > 0.6 for at least 2 strategies
Target by Week 16: A dominant strategy blend identified (1 primary + 1 confirmation)
```

---

## Operating Cadence Summary

| Cadence | Action | Tool |
|---|---|---|
| **Weekend / Mon pre-open** | Run batched scan, log top 5 trades | `POST /brain/scan?save_paper_trades=true` |
| **Daily (4 PM auto)** | Resolve open trades against OHLC | `resolver_scheduler.py` (APScheduler) |
| **Friday post-close** | Generate weekly analytics report | `GET /analytics/weekly-report` |
| **Friday post-close** | AI coaching query | `POST /ai/ask` |
| **Friday post-close** | Log any parameter change to MD | Manual, with reasoning |
| **Weekly** | AI generates strategy lesson | `rag_pipeline.generate_strategy_weekly_lesson()` |

---

## Phase Dependency Chain

```
A (Scanner Stabilize)
  └── B (Journal Pipeline)
        └── C (Outcome Resolver)  ← CRITICAL GATE — nothing learns without this
              ├── D (Weekly Analytics)
              └── E (RAG Memory)
                    └── F (Confidence Layer)
                          └── G (60–90 Day Optimization)
```

No phase may be skipped. Each phase's success test must pass before the next begins.

---

## File Delivery Summary

| Phase | New Files | Modified Files |
|---|---|---|
| **A** | — | `nse_universe.py`, `market_scanner.py`, `brain.py` |
| **B** | — | `brain.py`, `database.py`, `PaperTrade.tsx`, `api.ts` |
| **C** | `outcome_resolver.py`, `resolver_scheduler.py` | `database.py`, `brain.py` |
| **D** | `weekly_report.py`, `analytics.py` (router), `Analytics.tsx` | `App.tsx`, `Sidebar.tsx` |
| **E** | `nexus_llm.py`, `memory_store.py`, `prompts.py`, `rag_pipeline.py`, `feedback_loop.py`, `context_builder.py`, `ai.py` (router), `SignalExplainPanel.tsx`, `TradeReviewCard.tsx` | `brain.py`, `trades endpoint`, `PaperTrade.tsx`, `api.ts`, `database.py` |
| **F** | `DailyBriefWidget.tsx` | `rag_pipeline.py`, `context_builder.py`, `ai.py`, `Strategy.tsx`, `Overview.tsx` |
| **G** | — | Parameter configs, weekly changelog entries |

