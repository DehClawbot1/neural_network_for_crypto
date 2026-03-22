from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score


class Evaluator:
    def __init__(self, logs_dir="logs", weights_dir="weights"):
        self.logs_dir = Path(logs_dir)
        self.weights_dir = Path(weights_dir)
        self.dataset_file = self.logs_dir / "aligned_dataset.csv"
        self.model_file = self.weights_dir / "btc_direction_model.joblib"
        self.output_file = self.logs_dir / "supervised_eval.csv"

    def _safe_read(self, path):
        if not path.exists():
            return pd.DataFrame()
        try:
            return pd.read_csv(path, engine="python", on_bad_lines="skip")
        except Exception:
            return pd.DataFrame()

    def evaluate(self):
        df = self._safe_read(self.dataset_file)
        if df.empty or not self.model_file.exists() or "target_up" not in df.columns:
            return pd.DataFrame()

        saved = joblib.load(self.model_file)
        model = saved["model"]
        features = saved["features"]
        usable = [f for f in features if f in df.columns]
        if not usable:
            return pd.DataFrame()

        X = df[usable]
        y = df["target_up"].astype(int)
        preds = model.predict(X)

        strategy_returns = np.where(preds == 1, df["future_return"], -df["future_return"])
        sharpe = 0.0
        if np.std(strategy_returns) > 0:
            sharpe = float(np.mean(strategy_returns) / np.std(strategy_returns))

        cumulative = np.cumsum(strategy_returns)
        running_max = np.maximum.accumulate(cumulative)
        drawdown = cumulative - running_max
        max_drawdown = float(drawdown.min()) if len(drawdown) else 0.0

        result = pd.DataFrame([
            {
                "accuracy": accuracy_score(y, preds),
                "precision": precision_score(y, preds, zero_division=0),
                "recall": recall_score(y, preds, zero_division=0),
                "f1": f1_score(y, preds, zero_division=0),
                "mean_strategy_return": float(np.mean(strategy_returns)),
                "sharpe": sharpe,
                "max_drawdown": max_drawdown,
                "rows_evaluated": len(df),
            }
        ])
        result.to_csv(self.output_file, index=False)
        return result
