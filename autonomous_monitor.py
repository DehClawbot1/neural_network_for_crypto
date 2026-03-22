import logging
from pathlib import Path
from datetime import datetime

import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


class AutonomousMonitor:
    """
    Writes lightweight health/status summaries for the project.
    Research/paper-trading only.
    """

    def __init__(self, logs_dir="logs"):
        self.logs_dir = Path(logs_dir)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.output_file = self.logs_dir / "system_health.csv"

    def _latest_timestamp(self, df):
        if df is None or df.empty:
            return None
        for col in ["timestamp", "updated_at", "created_at", "opened_at", "closed_at"]:
            if col in df.columns:
                ts = pd.to_datetime(df[col], errors="coerce").dropna()
                if not ts.empty:
                    return ts.max().strftime("%Y-%m-%d %H:%M:%S")
        return None

    def write_status(self, signals_df=None, trades_df=None, alerts_df=None, open_positions_df=None):
        record = {
            "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            "signal_rows": 0 if signals_df is None else len(signals_df),
            "trade_rows": 0 if trades_df is None else len(trades_df),
            "alert_rows": 0 if alerts_df is None else len(alerts_df),
            "open_positions": 0 if open_positions_df is None else len(open_positions_df),
            "signals_growing": "yes" if signals_df is not None and len(signals_df) > 0 else "no",
            "positions_active": "yes" if open_positions_df is not None and len(open_positions_df) > 0 else "no",
            "last_signal_timestamp": self._latest_timestamp(signals_df),
            "last_trade_timestamp": self._latest_timestamp(trades_df),
            "last_alert_timestamp": self._latest_timestamp(alerts_df),
            "last_position_timestamp": self._latest_timestamp(open_positions_df),
            "status": "ok",
        }
        df = pd.DataFrame([record])
        df.to_csv(self.output_file, mode="a", header=not self.output_file.exists(), index=False)
        logging.info("Saved autonomous health status to %s", self.output_file)
