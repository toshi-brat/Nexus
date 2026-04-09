"""
NEXUS - Autonomous Trading Daemon
Runs continuously, manages trailing stop-losses, and implements a self-correcting feedback loop.
"""
import asyncio
import logging
from datetime import datetime

from models.database import SessionLocal, Trade
from services.brain.engine import brain
from services.data.indstocks_feed import indstocks_feed
from services.brain.screener import screener

logger = logging.getLogger("autonomous_bot")

class AutonomousBot:
    def __init__(self):
        self.is_running = False
        self.symbols = ["NIFTY", "BANKNIFTY"]
        self.base_capital = 100000.0
        self.tick_count = 0

        # Feedback Loop: Reinforcement Modifiers
        # 1.0 is default. >1.0 scales up sizing on winning streaks. <1.0 scales down on losing streaks.
        self.strategy_performance = {}

    def get_modifier(self, strategy_name: str) -> float:
        if strategy_name not in self.strategy_performance:
            self.strategy_performance[strategy_name] = {"wins": 0, "losses": 0, "modifier": 1.0}
        return self.strategy_performance[strategy_name]["modifier"]

    def apply_feedback(self, strategy_name: str, is_win: bool):
        """Self-correcting feedback loop"""
        stats = self.strategy_performance.get(strategy_name, {"wins": 0, "losses": 0, "modifier": 1.0})

        if is_win:
            stats["wins"] += 1
            # Gradually increase trust (max 1.5x)
            stats["modifier"] = min(1.5, stats["modifier"] + 0.1)
            logger.info(f"FEEDBACK LOOP: {strategy_name} WON. Upgrading modifier to {stats['modifier']:.2f}")
        else:
            stats["losses"] += 1
            # Aggressively decrease trust on failure (min 0.2x) to protect capital
            stats["modifier"] = max(0.2, stats["modifier"] - 0.25)
            logger.warning(f"FEEDBACK LOOP: {strategy_name} FAILED. Downgrading modifier to {stats['modifier']:.2f}")

        self.strategy_performance[strategy_name] = stats

    def is_market_open(self):
        now = datetime.now().time()
        # Market hours: 9:15 AM to 3:30 PM (IST)
        # Bypassing for testing/simulator:
        return True 

    async def start(self):
        self.is_running = True
        logger.info("Nexus Autonomous Bot Started. Monitoring markets...")

        while self.is_running:
            if self.is_market_open():
                await self.tick()
            await asyncio.sleep(60) # Scan every 1 minute

    async def tick(self):
        db = SessionLocal()
        try:
            # 1. Manage existing positions (Trailing SL, TP, Exits)
            self.manage_open_trades(db)

            # 2. Scan for new setups
            self.scan_for_new_trades(db)

            # 3. Run Stock Screener for Swing Trades (Every 10 minutes)
            self.tick_count += 1
            if self.tick_count % 10 == 0:
                self.run_swing_screener(db)

        except Exception as e:
            logger.error(f"Autonomous Tick Error: {e}")
        finally:
            db.close()

    def manage_open_trades(self, db):
        open_trades = db.query(Trade).filter(Trade.status == "OPEN").all()

        for trade in open_trades:
            # Get live price for the symbol
            _, current_price = indstocks_feed.get_option_chain_snapshot(trade.symbol)

            if current_price == 0: continue

            # Calculate distance for Trailing SL
            is_long = trade.trade_type == "BUY"
            stop_loss = trade.stop_loss if trade.stop_loss is not None else trade.entry_price
            target = trade.target if trade.target is not None else trade.entry_price
            risk = abs(trade.entry_price - stop_loss)
            reward = abs(target - trade.entry_price)

            if risk == 0: continue

            pnl_points = (current_price - trade.entry_price) if is_long else (trade.entry_price - current_price)

            # 1. Check Target Hit (Win)
            if pnl_points >= reward:
                trade.status = "CLOSED"
                trade.exit_price = current_price
                trade.pnl = pnl_points * trade.qty
                trade.notes = (trade.notes or "") + "\n[AUTONOMOUS] Closed at Target."
                self.apply_feedback(trade.setup, is_win=True)
                db.commit()
                continue

            # 2. Check Stop Loss Hit (Loss)
            sl_points = (current_price - stop_loss) if is_long else (stop_loss - current_price)
            if sl_points <= 0:
                trade.status = "CLOSED"
                trade.exit_price = current_price
                trade.pnl = pnl_points * trade.qty
                trade.notes = (trade.notes or "") + "\n[AUTONOMOUS] Stopped out."
                self.apply_feedback(trade.setup, is_win=False)
                db.commit()
                continue

            # 3. Dynamic Trailing Stop Loss
            # If we are 50% towards the target, move SL to breakeven to eliminate risk
            if pnl_points >= (reward * 0.5):
                new_sl = trade.entry_price

                # If we are 80% towards the target, trail SL to lock in 50% of the reward
                if pnl_points >= (reward * 0.8):
                    new_sl = trade.entry_price + (reward * 0.5) if is_long else trade.entry_price - (reward * 0.5)

                # Only move SL forward, never backward
                if is_long and (trade.stop_loss is None or new_sl > trade.stop_loss):
                    trade.stop_loss = new_sl
                    trade.notes = (trade.notes or "") + f"\n[AUTONOMOUS] Trailing SL updated to {new_sl}"
                    db.commit()
                elif not is_long and (trade.stop_loss is None or new_sl < trade.stop_loss):
                    trade.stop_loss = new_sl
                    trade.notes = (trade.notes or "") + f"\n[AUTONOMOUS] Trailing SL updated to {new_sl}"
                    db.commit()

    def scan_for_new_trades(self, db):
        # Don't open new trades if we already have 3 active ones (Risk Limit)
        active_count = db.query(Trade).filter(Trade.status == "OPEN").count()
        if active_count >= 3: return

        for symbol in self.symbols:
            # 1. Fetch live data
            df = indstocks_feed.get_historical_data(symbol, timeframe="15m", days=5)
            options_data, current_price = indstocks_feed.get_option_chain_snapshot(symbol)
            sentiment_data = {"score": 0.5} # Fallback

            # 2. Run Engine
            signals = brain.run_all(symbol, df, options_data, sentiment_data, capital=self.base_capital)

            for signal in signals:
                modifier = self.get_modifier(signal.strategy_name)

                # If a strategy has failed too many times (modifier < 0.5), the bot "benches" it
                if modifier < 0.5:
                    logger.info(f"Skipping {signal.strategy_name} - currently benched by feedback loop.")
                    continue

                # Adjust sizing based on feedback loop trust modifier
                adjusted_qty = int(max(1, signal.suggested_qty * modifier))

                # Check if we already have this exact setup open to avoid duplicates
                exists = db.query(Trade).filter(Trade.status == "OPEN", Trade.setup == signal.strategy_name).first()
                if exists: continue

                # 3. Execute Paper Trade
                new_trade = Trade(
                    symbol=signal.symbol,
                    trade_type=signal.action,
                    instrument=signal.instrument,
                    qty=adjusted_qty,
                    entry_price=signal.entry_price,
                    stop_loss=signal.stop_loss,
                    target=signal.target_price,
                    setup=signal.strategy_name,
                    status="OPEN",
                    notes=f"[AUTONOMOUS ENTRY] Modifier: {modifier:.2f}\nRationale: {signal.rationale}"
                )
                db.add(new_trade)
                db.commit()
                logger.info(f"Autonomous Bot executed Paper Trade: {signal.strategy_name} on {symbol}")

    def run_swing_screener(self, db):
        logger.info("Autonomous Bot running Multi-Day Swing Screener...")
        shortlist = screener.scan_universe()

        for setup in shortlist:
            # Only paper trade if we don't already have an open swing trade for this stock
            exists = db.query(Trade).filter(Trade.status == "OPEN", Trade.symbol == setup["symbol"]).first()
            if exists: continue

            # Simple Swing Sizing: Risk 2% of capital
            entry = setup["close"]
            sl = entry * 0.95 # 5% stop loss for swings
            target = entry * 1.15 # 15% target (1:3 R/R)
            risk_per_share = entry - sl
            allocated_risk = self.base_capital * 0.02 # 2% risk
            qty = max(1, int(allocated_risk / risk_per_share))

            new_trade = Trade(
                symbol=setup["symbol"],
                trade_type="BUY",
                instrument="EQ",
                qty=qty,
                entry_price=entry,
                stop_loss=sl,
                target=target,
                setup=setup["setup"],
                status="OPEN",
                notes=f"[AUTONOMOUS SWING] {setup['rationale']}"
            )
            db.add(new_trade)
        db.commit()


bot = AutonomousBot()
