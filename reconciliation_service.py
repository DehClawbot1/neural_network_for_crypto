from pathlib import Path

import pandas as pd

from execution_client import ExecutionClient


class ReconciliationService:
    """
    Live-test reconciliation against remote open orders and trades.
    """

    def __init__(self, logs_dir="logs"):
        self.logs_dir = Path(logs_dir)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.orders_file = self.logs_dir / "live_orders.csv"
        self.trades_file = self.logs_dir / "live_fills.csv"
        self.client = ExecutionClient()

    def _safe_read(self, path):
        if not path.exists():
            return pd.DataFrame()
        try:
            return pd.read_csv(path, engine="python", on_bad_lines="skip")
        except Exception:
            return pd.DataFrame()

    def reconcile(self):
        local_orders = self._safe_read(self.orders_file)
        local_trades = self._safe_read(self.trades_file)

        remote_orders = self.client.get_open_orders()
        remote_trades = self.client.get_trades()

        remote_orders_df = pd.DataFrame(remote_orders) if not isinstance(remote_orders, pd.DataFrame) else remote_orders
        remote_trades_df = pd.DataFrame(remote_trades) if not isinstance(remote_trades, pd.DataFrame) else remote_trades

        report = {
            "local_order_rows": len(local_orders),
            "remote_open_orders": len(remote_orders_df),
            "local_trade_rows": len(local_trades),
            "remote_trade_rows": len(remote_trades_df),
            "open_order_mismatch": len(local_orders) != len(remote_orders_df),
            "trade_mismatch": len(local_trades) != len(remote_trades_df),
        }
        return report, remote_orders_df, remote_trades_df
