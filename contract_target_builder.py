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

    def build(self, horizon_rows=12, tp_move=0.04, sl_move=0.03):
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
            group["forward_return_15m"] = (group["future_price"] - group["current_price"]) / group["current_price"]
            group["target_up"] = (group["forward_return_15m"] > 0).astype(int)

            tp_labels = []
            mfe_values = []
            mae_values = []
            for idx, row in group.iterrows():
                entry_price = float(row.get("current_price", 0.5))
                future_window = group.iloc[idx + 1 : idx + 1 + horizon_rows]
                if future_window.empty:
                    tp_labels.append(None)
                    mfe_values.append(None)
                    mae_values.append(None)
                    continue

                moves = (future_window["current_price"].astype(float) - entry_price).tolist()
                mfe = max(moves) if moves else None
                mae = min(moves) if moves else None
                tp_hit_idx = next((i for i, move in enumerate(moves) if move >= tp_move), None)
                sl_hit_idx = next((i for i, move in enumerate(moves) if move <= -sl_move), None)
                tp_before_sl = int(tp_hit_idx is not None and (sl_hit_idx is None or tp_hit_idx < sl_hit_idx))

                tp_labels.append(tp_before_sl)
                mfe_values.append(mfe)
                mae_values.append(mae)

            group["tp_before_sl_60m"] = tp_labels
            group["mfe_60m"] = mfe_values
            group["mae_60m"] = mae_values
            grouped_rows.append(group)

        result = pd.concat(grouped_rows, ignore_index=True).dropna(subset=["future_price", "forward_return_15m"])
        return result

    def write(self, horizon_rows=12, tp_move=0.04, sl_move=0.03):
        df = self.build(horizon_rows=horizon_rows, tp_move=tp_move, sl_move=sl_move)
        if not df.empty:
            df.to_csv(self.output_file, index=False)
        return df
