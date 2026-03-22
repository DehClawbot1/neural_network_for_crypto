from datetime import datetime
from pathlib import Path

import pandas as pd

from execution_client import ExecutionClient


class OrderManager:
    """
    Live-test order manager.
    Tracks submitted orders and reconciles their local status over time.
    """

    def __init__(self, logs_dir="logs"):
        self.logs_dir = Path(logs_dir)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.orders_file = self.logs_dir / "live_orders.csv"
        self.fills_file = self.logs_dir / "live_fills.csv"
        self.client = ExecutionClient()

    def _append(self, path: Path, row: dict):
        pd.DataFrame([row]).to_csv(path, mode="a", header=not path.exists(), index=False)

    def submit_entry(self, token_id, price, size, side="BUY", condition_id=None, outcome_side=None):
        response = self.client.create_and_post_order(token_id=token_id, price=price, size=size, side=side)
        order_id = response.get("orderID") or response.get("order_id") or response.get("id")
        row = {
            "timestamp": datetime.utcnow().isoformat(),
            "order_id": order_id,
            "token_id": token_id,
            "condition_id": condition_id,
            "outcome_side": outcome_side,
            "order_side": side,
            "price": price,
            "size": size,
            "status": response.get("status", "SUBMITTED"),
        }
        self._append(self.orders_file, row)
        return row, response

    def get_order_status(self, order_id):
        response = self.client.get_order(order_id)
        return response

    def cancel_stale_order(self, order_id):
        response = self.client.cancel_order(order_id)
        self._append(self.orders_file, {"timestamp": datetime.utcnow().isoformat(), "order_id": order_id, "status": "CANCELED"})
        return response

    def record_fill(self, fill_payload: dict):
        self._append(self.fills_file, {"timestamp": datetime.utcnow().isoformat(), **fill_payload})
        return fill_payload
