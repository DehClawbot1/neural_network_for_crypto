import logging
from pathlib import Path

import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


class StrategyBacktester:
    """
    Simple paper-strategy evaluator over historical signal logs.
    This is a research replay tool, not a live execution system.
    """

    def __init__(self, logs_dir="logs"):
        self.logs_dir = Path(logs_dir)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.output_file = self.logs_dir / "backtest_summary.csv"

    def run(self, signals_df: pd.DataFrame):
        if signals_df is None or signals_df.empty:
            return pd.DataFrame()

        df = signals_df.copy()
        if "confidence" not in df.columns:
            return pd.DataFrame()

        def bucket(row):
            label = str(row.get("signal_label", ""))
            conf = float(row.get("confidence", 0.0))
            if "HIGHEST" in label:
                return conf * 1.2
            if "STRONG" in label:
                return conf * 0.8
            if "WATCH" in label:
                return conf * 0.2
            return 0.0

        df["backtest_score"] = df.apply(bucket, axis=1)

        summary = pd.DataFrame(
            [
                {
                    "rows_evaluated": len(df),
                    "avg_confidence": round(float(df["confidence"].mean()), 4),
                    "avg_backtest_score": round(float(df["backtest_score"].mean()), 4),
                    "highest_score": round(float(df["backtest_score"].max()), 4),
                    "top_signal_rows": int((df["signal_label"] == "HIGHEST-RANKED PAPER SIGNAL").sum()),
                }
            ]
        )
        return summary

    def write(self, signals_df: pd.DataFrame):
        summary = self.run(signals_df)
        if summary.empty:
            return summary

        summary.to_csv(self.output_file, index=False)
        logging.info("Saved backtest summary to %s", self.output_file)
        return summary


if __name__ == "__main__":
    logs_dir = Path("logs")
    signals_path = logs_dir / "signals.csv"
    if signals_path.exists():
        signals_df = pd.read_csv(signals_path)
        summary = StrategyBacktester(logs_dir=logs_dir).write(signals_df)
        print(summary)
    else:
        print("No signals.csv found yet. Run the supervisor first.")
