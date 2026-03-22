from pathlib import Path

import pandas as pd


class WalletAlphaBuilder:
    """
    Estimate wallet quality from contract-level historical outcome labels.
    Research/paper-trading only.
    """

    def __init__(self, logs_dir="logs"):
        self.logs_dir = Path(logs_dir)
        self.contract_targets_file = self.logs_dir / "contract_targets.csv"
        self.output_file = self.logs_dir / "wallet_alpha.csv"

    def _safe_read(self, path):
        if not path.exists():
            return pd.DataFrame()
        try:
            return pd.read_csv(path, engine="python", on_bad_lines="skip")
        except Exception:
            return pd.DataFrame()

    def build(self):
        df = self._safe_read(self.contract_targets_file)
        if df.empty or "wallet_copied" not in df.columns or "future_return" not in df.columns:
            return pd.DataFrame()

        alpha = (
            df.groupby("wallet_copied")
            .agg(
                observations=("wallet_copied", "size"),
                avg_future_return=("future_return", "mean"),
                hit_rate=("target_up", "mean"),
                avg_confidence=("confidence", "mean") if "confidence" in df.columns else ("future_return", "mean"),
            )
            .reset_index()
            .sort_values(by=["avg_future_return", "hit_rate"], ascending=[False, False])
        )
        return alpha

    def write(self):
        alpha = self.build()
        if not alpha.empty:
            alpha.to_csv(self.output_file, index=False)
        return alpha
