from pathlib import Path

import pandas as pd


class ContractTargetBuilder:
    """
    Build contract-level labels from ranked signal history and subsequent contract-price movement.
    Research/paper-trading only.
    """

    def __init__(self, logs_dir="logs"):
        self.logs_dir = Path(logs_dir)
        self.signals_file = self.logs_dir / "signals.csv"
        self.output_file = self.logs_dir / "contract_targets.csv"

    def _safe_read(self, path):
        if not path.exists():
            return pd.DataFrame()
        try:
            return pd.read_csv(path, engine="python", on_bad_lines="skip")
        except Exception:
            return pd.DataFrame()

    def build(self, horizon_rows=5):
        df = self._safe_read(self.signals_file)
        if df.empty or "market" not in df.columns or "current_price" not in df.columns:
            return pd.DataFrame()

        df = df.copy()
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce") if "timestamp" in df.columns else pd.NaT
        df = df.sort_values(["market", "timestamp"]).reset_index(drop=True)

        grouped_rows = []
        for market, group in df.groupby("market"):
            group = group.reset_index(drop=True)
            group["future_price"] = group["current_price"].shift(-horizon_rows)
            group["future_return"] = (group["future_price"] - group["current_price"]) / group["current_price"]
            group["target_up"] = (group["future_return"] > 0).astype(int)
            grouped_rows.append(group)

        result = pd.concat(grouped_rows, ignore_index=True).dropna(subset=["future_price", "future_return"])
        return result

    def write(self, horizon_rows=5):
        df = self.build(horizon_rows=horizon_rows)
        if not df.empty:
            df.to_csv(self.output_file, index=False)
        return df
