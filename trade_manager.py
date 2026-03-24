from __future__ import annotations

import logging
from typing import Dict, List, Optional
from datetime import datetime

import pandas as pd

from trade_lifecycle import TradeLifecycle, TradeState

logger = logging.getLogger(__name__)

class TradeManager:
    """
    Manages a collection of TradeLifecycle instances, acting as the central
    runtime trade manager for the supervisor.
    """
    def __init__(self):
        self.active_trades: Dict[str, TradeLifecycle] = {}
        logger.info("[+] Initialized TradeManager.")

    def _get_trade_key(self, signal_row: pd.Series) -> str:
        """Generates a unique key for a trade based on market and outcome."""
        market = signal_row.get("market") or signal_row.get("market_title")
        outcome_side = signal_row.get("side") or signal_row.get("outcome_side")
        if not market or not outcome_side:
            raise ValueError(f"Missing market or outcome_side in signal: {signal_row.to_dict()}")
        return f"{market}-{outcome_side}"

    def handle_signal(self, signal_row: pd.Series, confidence: float, size_usdc: float) -> Optional[TradeLifecycle]:
        """
        Processes a new signal. If a trade already exists for this market/side,
        it updates it. Otherwise, it creates a new TradeLifecycle instance.
        """
        trade_key = self._get_trade_key(signal_row)
        market = signal_row.get("market") or signal_row.get("market_title")
        outcome_side = signal_row.get("side") or signal_row.get("outcome_side")
        token_id = signal_row.get("outcome_token_id")
        condition_id = signal_row.get("condition_id")
        entry_price = signal_row.get("price") # Assuming signal_row has an entry price

        if trade_key in self.active_trades:
            trade = self.active_trades[trade_key]
            logger.info(f"[!] Updating existing trade for {market} ({outcome_side}).")
            # For simplicity, if a trade is already open, we'll just log
            # In a real system, you'd re-evaluate position size, scale in/out etc.
            trade.on_signal(signal_row.to_dict()) # Log the new signal
            return trade
        else:
            trade = TradeLifecycle(
                market=market,
                token_id=token_id,
                condition_id=condition_id,
                outcome_side=outcome_side
            )
            trade.on_signal(signal_row.to_dict())
            trade.enter(size_usdc=size_usdc, entry_price=entry_price)
            self.active_trades[trade_key] = trade
            logger.info(f"[+] New trade initiated for {market} ({outcome_side}) with {size_usdc} USDC.")
            return trade

    def update_markets(self, market_prices: Dict[str, float]):
        """
        Updates current prices for all active trades and computes unrealized PnL.
        market_prices: a dict of {market_name: current_price}
        """
        for trade_key, trade in list(self.active_trades.items()): # Iterate over a copy
            if trade.market in market_prices:
                live_price = market_prices[trade.market]
                trade.update_market(live_price)
                logger.debug(f"Updated {trade.market} to price {live_price}. Unrealized PnL: {trade.unrealized_pnl:.2f}")
            else:
                logger.warning(f"Market price for {trade.market} not found. Skipping update.")

    def process_exits(self, current_timestamp: datetime):
        """
        Evaluates exit conditions for all active trades.
        This is a placeholder for real exit logic based on RL brain, stop losses, etc.
        """
        closed_trades: List[TradeLifecycle] = []
        for trade_key, trade in list(self.active_trades.items()):
            # Placeholder for actual exit logic (e.g., stop loss, RL exit signal)
            # For now, let's just close very old paper trades for demo purposes
            if trade.opened_at:
                opened_dt = datetime.fromisoformat(trade.opened_at)
                if (current_timestamp - opened_dt).total_seconds() > (24 * 3600 * 7): # Close after 7 days
                    trade.close(trade.current_price)
                    logger.info(f"[->] Closed old paper trade for {trade.market} ({trade.outcome_side}). Realized PnL: {trade.realized_pnl:.2f}")
                    closed_trades.append(trade)
        
        for trade in closed_trades:
            trade_key = self._get_trade_key(pd.Series({"market": trade.market, "outcome_side": trade.outcome_side}))
            del self.active_trades[trade_key]

        return closed_trades # Return list of closed trades for logging/persistence

    def get_open_positions(self) -> List[TradeLifecycle]:
        """Returns a list of all currently active TradeLifecycle instances."""
        return list(self.active_trades.values())

    def get_metrics(self) -> Dict[str, any]:
        """Aggregates key metrics from active trades."""
        total_unrealized_pnl = sum(trade.unrealized_pnl for trade in self.active_trades.values() if trade.state != TradeState.CLOSED)
        total_open_positions = len(self.active_trades)
        
        # Add more aggregated metrics as needed for the dashboard
        return {
            "total_unrealized_pnl": total_unrealized_pnl,
            "total_open_positions": total_open_positions,
            # Placeholder for live reconciliation
            "last_reconciled_at": datetime.now().isoformat(), 
        }

    def reconcile_live_positions(self, execution_client=None, reconciled_positions_df: pd.DataFrame | None = None):
        """
        Reconcile active trades from a reconciled live position book when available.
        Falls back to a no-op placeholder if no reconciled positions are supplied.
        """
        if reconciled_positions_df is None or reconciled_positions_df.empty:
            logger.info("[~] Reconciling live positions with exchange (no reconciled positions supplied).")
            return

        rebuilt_trades: Dict[str, TradeLifecycle] = {}
        for _, row in reconciled_positions_df.iterrows():
            market = row.get("market") or row.get("market_title") or str(row.get("condition_id") or row.get("token_id") or "unknown_market")
            outcome_side = row.get("outcome_side") or row.get("side") or "UNKNOWN"
            trade_key = f"{market}-{outcome_side}"
            trade = TradeLifecycle(
                market=str(market),
                token_id=row.get("token_id"),
                condition_id=row.get("condition_id"),
                outcome_side=str(outcome_side),
            )
            trade.entry_price = float(row.get("avg_entry_price", row.get("entry_price", 0.0)) or 0.0)
            trade.current_price = float(row.get("mark_price", row.get("current_price", trade.entry_price)) or trade.entry_price)
            trade.shares = float(row.get("shares", 0.0) or 0.0)
            trade.size_usdc = trade.shares * trade.entry_price
            trade.realized_pnl = float(row.get("realized_pnl", 0.0) or 0.0)
            trade.unrealized_pnl = float(row.get("unrealized_pnl", 0.0) or 0.0)
            trade.opened_at = row.get("last_fill_at") or datetime.now().isoformat()
            trade.state = TradeState.OPEN
            rebuilt_trades[trade_key] = trade

        self.active_trades = rebuilt_trades
        logger.info("[~] Reconciled %s live positions into TradeManager.", len(self.active_trades))
