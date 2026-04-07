# Patch package for bugs 11-14

## Suggested commit message

fix: address bugs 11-14 in market fetching, dataset ingestion, wallet analytics, and pipeline order

## Suggested PR title

Fix bugs 11-14: market fetch scope, trade log input, wallet joins, and pipeline ordering

## Suggested PR body

### What this changes

This patch addresses four repo issues found during audit:

1. `fetch_btc_markets(closed=...)` now respects the `closed` argument instead of always fetching both open and closed markets.
2. `HistoricalDatasetBuilder` now reads `logs/execution_log.csv` instead of `daily_summary.txt` for structured trade merges.
3. `TraderAnalytics` now normalizes wallet keys before merging ranked signals and paper trades, preventing missed joins caused by full-vs-truncated wallet formats.
4. `run_research_pipeline()` now builds BTC targets before rebuilding the historical dataset, so a clean run does not produce a stale dataset without BTC target context.

### Why

These changes reduce duplicate API work, fix a broken training-data input contract, improve analytics merge reliability, and correct pipeline ordering for clean rebuilds.

### Patch

```diff
diff --git a/market_monitor.py b/market_monitor.py
@@
-def fetch_btc_markets(limit_per_page=100, closed=False, max_offset=2000):
+def fetch_btc_markets(limit_per_page=100, closed=False, max_offset=2000):
@@
-    markets = []
-    for closed_flag in [False, True]:
-        offset = 0
-        while True:
-            params = {
-                "limit": limit_per_page,
-                "offset": offset,
-                "closed": str(closed_flag).lower(),
-            }
-            response = requests.get(GAMMA_MARKETS_URL, params=params, timeout=20)
-            response.raise_for_status()
-            page_data = response.json()
-            if not page_data:
-                break
-            markets.extend(page_data)
-            offset += limit_per_page
-            if offset > max_offset:
-                break
+    markets = []
+    offset = 0
+    while True:
+        params = {
+            "limit": limit_per_page,
+            "offset": offset,
+            "closed": str(bool(closed)).lower(),
+        }
+        response = requests.get(GAMMA_MARKETS_URL, params=params, timeout=20)
+        response.raise_for_status()
+        page_data = response.json()
+        if not page_data:
+            break
+        markets.extend(page_data)
+        offset += limit_per_page
+        if offset > max_offset:
+            break
```

```diff
diff --git a/historical_dataset_builder.py b/historical_dataset_builder.py
@@
-        trades_df = self._safe_read("daily_summary.txt")
+        trades_df = self._safe_read("execution_log.csv")
```

```diff
diff --git a/trader_analytics.py b/trader_analytics.py
@@
 class TraderAnalytics:
@@
+    @staticmethod
+    def _normalize_wallet_key(series: pd.Series) -> pd.Series:
+        return series.fillna("").astype(str).str.lower().str.strip().str[:8]
+
     def build(self, signals_df: pd.DataFrame, trades_df: pd.DataFrame | None = None):
@@
-        base = (
-            signals_df.groupby("wallet_copied")
+        signals_df["wallet_key"] = self._normalize_wallet_key(signals_df["wallet_copied"])
+        base = (
+            signals_df.groupby("wallet_key")
             .agg(
-                ranked_signals=("wallet_copied", "size"),
+                ranked_signals=("wallet_key", "size"),
                 avg_confidence=("confidence", "mean"),
                 top_signal_count=("signal_label", lambda x: int((x == "HIGHEST-RANKED PAPER SIGNAL").sum())),
                 unique_markets=("market", "nunique"),
+                wallet_copied=("wallet_copied", "first"),
             )
             .reset_index()
             .sort_values(by=["avg_confidence", "ranked_signals"], ascending=[False, False])
         )
@@
-        if trades_df is not None and not trades_df.empty and "wallet_copied" in trades_df.columns:
+        if trades_df is not None and not trades_df.empty and "wallet_copied" in trades_df.columns:
             trades_df = trades_df.copy()
+            trades_df["wallet_key"] = self._normalize_wallet_key(trades_df["wallet_copied"])
             if "fill_price" in trades_df.columns:
                 trades_df["fill_price"] = pd.to_numeric(trades_df["fill_price"], errors="coerce")
             trade_counts = (
-                trades_df.groupby("wallet_copied")
-                .agg(paper_trades=("wallet_copied", "size"), avg_fill_price=("fill_price", "mean"))
+                trades_df.groupby("wallet_key")
+                .agg(paper_trades=("wallet_key", "size"), avg_fill_price=("fill_price", "mean"))
                 .reset_index()
             )
-            base = base.merge(trade_counts, on="wallet_copied", how="left")
+            base = base.merge(trade_counts, on="wallet_key", how="left")
@@
-        return base
+        return base.drop(columns=["wallet_key"], errors="ignore")
```

```diff
diff --git a/real_pipeline.py b/real_pipeline.py
@@
 def run_research_pipeline():
-    logging.info("Building historical dataset...")
-    HistoricalDatasetBuilder().write()
-
     logging.info("Building BTC direction targets...")
     TargetBuilder().write(days=30, horizon_minutes=60)
+
+    logging.info("Building historical dataset...")
+    HistoricalDatasetBuilder().write()
     DatasetAligner().write()
```
