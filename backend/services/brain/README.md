# The NEXUS Brain (Quantitative Strategy Engine)

Welcome to the **NEXUS Brain**, the core algorithmic reasoning engine for the NEXUS Trading System. 

Instead of relying on AI hallucinations, this engine uses a pure-math, quantitative **Ensemble Modeling** approach. It runs raw market data through multiple, independent mathematical strategies and outputs high-probability trade setups for the user to review.

## The Human-in-the-Loop Philosophy
The Brain does not execute trades automatically. It acts as an elite quantitative analyst:
1. **Analyzes Data:** Pulls option chains, price history, and NLP sentiment.
2. **Triggers Rules:** Checks strict technical and statistical boundaries.
3. **Pitches Trades:** Outputs Entry, Target, Stop Loss, and a plain-English rationale.
4. **You Decide:** You click `[ Execute ]` in the dashboard to send it to IndMoney.

## Current Ensemble (5 Core Strategies)
We run four diametrically opposed strategies simultaneously to ensure we catch different market regimes (Range, Trend, Reversal, Macro).
See the `STRATEGIES_README.md` for exact mathematical formulas and parameters.

1. **OI Gravity (Range-Bound / Theta Decay):** Sells Credit Spreads/Iron Condors outside Open Interest walls.
2. **PCR Momentum Fade (Contrarian Reversal):** Fades extreme retail fear/greed using Put-Call Ratio and Bollinger Bands.
3. **Volatility Breakout (Trend Following):** Buys directional momentum after volatility compression (ATR lows) combined with volume surges.
4. **Sentiment Convergence (Macro / NLP)
5. **Renaissance Stat-Arb (Pairs Trading):** Identifies temporary pricing anomalies in highly correlated assets using Z-Scores (Inspired by Jim Simons).:** Trades strong directional trend (EMA 50) confirmed by FinBERT news sentiment.

## The Iteration Loop (How we improve)
We do not hardcode and pray. We use the **Paper Trading** module to track how these four perform.
* **Phase 1 (Current):** Run all 4. Log signals to the Paper Trading journal.
* **Phase 2 (Tweak):** Adjust ATR multipliers, PCR thresholds, and time-of-day filters based on win-rate.
* **Phase 3 (Alpha):** Combine the best parameters into a unified "NEXUS Alpha" strategy.

## File Structure
- `engine.py` — The core loop that instantiates and runs the ensemble.
- `strategies.py` — The mathematical logic for the 4 base strategies.
- `models.py` — The strictly typed `TradeSignal` output format.
