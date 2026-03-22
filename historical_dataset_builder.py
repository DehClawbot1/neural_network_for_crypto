import logging
from pathlib import Path

import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


class HistoricalDatasetBuilder:
    """
    Consolidates project logs into a single ML-friendly historical dataset.
    Research/paper-trading only.
    """

    def __init__(self, logs_dir="logs"):
        self.logs_dir = Path(logs_dir)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.output_file = self.logs_dir / "historical_dataset.csv"

    def _safe_read(self, filename):
        path = self.logs_dir / filename
        if not path.exists():
            return pd.DataFrame()
        try:
            return pd.read_csv(path, engine="python", on_bad_lines="skip")
        except Exception:
            return pd.DataFrame()

    def build(self):
        signals_df = self._safe_read("signals.csv")
        trades_df = self._safe_read("daily_summary.txt")
        markets_df = self._safe_read("markets.csv")
        alerts_df = self._safe_read("alerts.csv")

        if signals_df.empty:
            return pd.DataFrame()

        dataset = signals_df.copy()

        if not trades_df.empty:
            dataset = dataset.merge(
                trades_df[[c for c in trades_df.columns if c in ["market", "wallet_copied", "fill_price", "size_usdc", "action_type"]]],
                on=[c for c in ["market", "wallet_copied"] if c in dataset.columns and c in trades_df.columns],
                how="left",
            )

        if not markets_df.empty and "market" in dataset.columns and "question" in markets_df.columns:
            latest_markets = markets_df.drop_duplicates(subset=["question"], keep="last")
            dataset = dataset.merge(
                latest_markets[[c for c in latest_markets.columns if c in ["question", "liquidity", "volume", "last_trade_price", "url"]]],
                left_on="market",
                right_on="question",
                how="left",
            )

        if not alerts_df.empty and "market" in dataset.columns and "market" in alerts_df.columns:
            alert_counts = alerts_df.groupby("market").size().reset_index(name="alert_count")
            dataset = dataset.merge(alert_counts, on="market", how="left")
            dataset["alert_count"] = dataset["alert_count"].fillna(0).astype(int)

        return dataset

    def write(self):
        dataset = self.build()
        if dataset.empty:
            return dataset

        dataset.to_csv(self.output_file, index=False)
        logging.info("Saved historical dataset to %s", self.output_file)
        return dataset
