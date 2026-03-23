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

    def _normalize_df(self, obj):
        if isinstance(obj, pd.DataFrame):
            return obj
        try:
            return pd.DataFrame(obj)
        except Exception:
            return pd.DataFrame()

    def reconcile(self):
        local_orders = self._safe_read(self.orders_file)
        local_trades = self._safe_read(self.trades_file)
        if not local_orders.empty and "status" in local_orders.columns:
            local_orders = local_orders[local_orders["status"].astype(str).str.upper().isin(["OPEN", "SUBMITTED"])]

        remote_orders_df = self._normalize_df(self.client.get_open_orders())
        remote_trades_df = self._normalize_df(self.client.get_trades())

        local_order_ids = set(local_orders.get("order_id", pd.Series(dtype=str)).dropna().astype(str).tolist())
        remote_order_ids = set(remote_orders_df.get("order_id", remote_orders_df.get("id", pd.Series(dtype=str))).dropna().astype(str).tolist())
        local_trade_ids = set(local_trades.get("trade_id", local_trades.get("fill_id", pd.Series(dtype=str))).dropna().astype(str).tolist())
        remote_trade_ids = set(remote_trades_df.get("trade_id", remote_trades_df.get("id", pd.Series(dtype=str))).dropna().astype(str).tolist())

        report = {
            "local_order_rows": len(local_orders),
            "remote_open_orders": len(remote_orders_df),
            "local_trade_rows": len(local_trades),
            "remote_trade_rows": len(remote_trades_df),
            "missing_local_orders": sorted(list(remote_order_ids - local_order_ids)),
            "missing_remote_orders": sorted(list(local_order_ids - remote_order_ids)),
            "missing_local_trades": sorted(list(remote_trade_ids - local_trade_ids)),
            "missing_remote_trades": sorted(list(local_trade_ids - remote_trade_ids)),
        }

        status_mismatches = []
        if not local_orders.empty and not remote_orders_df.empty:
            local_idx = local_orders.set_index("order_id", drop=False) if "order_id" in local_orders.columns else pd.DataFrame()
            remote_key = "order_id" if "order_id" in remote_orders_df.columns else "id" if "id" in remote_orders_df.columns else None
            if remote_key and not local_idx.empty:
                remote_idx = remote_orders_df.set_index(remote_key, drop=False)
                for order_id in sorted(local_order_ids & remote_order_ids):
                    lrow = local_idx.loc[order_id] if order_id in local_idx.index else None
                    rrow = remote_idx.loc[order_id] if order_id in remote_idx.index else None
                    if lrow is None or rrow is None:
                        continue
                    local_status = lrow.get("status")
                    remote_status = rrow.get("status")
                    local_size = lrow.get("size")
                    remote_size = rrow.get("size")
                    if str(local_status) != str(remote_status) or str(local_size) != str(remote_size):
                        status_mismatches.append(
                            {
                                "order_id": order_id,
                                "local_status": local_status,
                                "remote_status": remote_status,
                                "local_size": local_size,
                                "remote_size": remote_size,
                            }
                        )

        report["order_mismatches"] = status_mismatches
        return report, remote_orders_df, remote_trades_df

