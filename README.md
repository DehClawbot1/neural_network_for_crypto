# Neural Network for Crypto

Public-data Polymarket system for **BTC-related markets**, **smart-wallet tracking**, **paper-trading simulation**, **historical model training**, and an isolated **live-test branch** for future authenticated execution experiments.

## What this project is

This repo is for:
- public market discovery
- public wallet / leaderboard analysis
- historical dataset building
- supervised model research
- path-replay backtesting
- paper-trading dashboards

On the default paper/research line, this repo is **not** for:
- connecting your live Polymarket account
- placing real orders
- real-money execution
- storing or requiring your private trading credentials

A separate branch, **`live-test`**, now exists for isolated live-execution scaffolding and testing.

## Safety / mode

Current intended mode on `main`:
- **public-data only**
- **paper-trading only**
- **research / backtesting only**

You do **not** need a Polymarket API key for the default paper setup.

On the separate `live-test` branch, authenticated client scaffolding exists for future testing, but that branch should be treated as isolated and experimental.

The project uses public endpoints only:
- **Gamma API** for market discovery
- **Data API** for leaderboard + public wallet trades
- **CLOB read endpoints** for price history
- optionally public **CLOB WebSocket** for live market updates

## Current architecture

## Runtime

### `run_bot.py`
Main launcher.

It now:
1. validates environment
2. checks existing weights
3. runs the research pipeline refresh
4. starts the continuous supervisor loop

### `supervisor.py`
Continuous monitoring loop for:
- fetching public BTC-related market/account activity
- scoring paper opportunities
- simulating paper positions
- updating logs for the dashboard

## Data collection

### `market_monitor.py`
Uses **Gamma** market discovery and tracks:
- `condition_id`
- `clob_token_ids`
- `yes_token_id`
- `no_token_id`
- liquidity / volume / last trade / end date

### `leaderboard_scraper.py`
Uses the public **Data API** to:
- fetch top crypto wallets
- scan recent public trades
- extract BTC-related signal candidates

### `clob_history.py`
Uses public **CLOB `/prices-history`** for token-level price history.

This is the correct data source for:
- forward-return labels
- TP-before-SL labels
- MFE / MAE
- replay simulation

## Dataset / features / labels

### `historical_dataset_builder.py`
Builds the project dataset around:
- one signal
- one timestamp
- one market
- only information available at that moment

It now merges:
- market microstructure fields
- rolling wallet metrics
- BTC context features
- wallet alpha summaries

### `wallet_alpha_builder.py`
Builds wallet quality features such as:
- rolling trade count
- rolling forward return
- rolling win rate
- rolling alpha proxy
- TP precision proxy
- recent streak

### `target_builder.py`
Builds BTC context features like:
- `btc_spot_return_5m`
- `btc_spot_return_15m`
- `btc_realized_vol_15m`
- `btc_volume_proxy`

### `contract_target_builder.py`
Builds event-style contract labels, including:
- `tp_before_sl_60m`
- `forward_return_15m`
- `mfe_60m`
- `mae_60m`

## Models / evaluation

### `supervised_models.py`
Trains supervised baseline models for:
- classification: `tp_before_sl_60m`
- regression: `forward_return_15m`

### `model_inference.py`
Loads trained supervised models and outputs:
- `p_tp_before_sl`
- `expected_return`
- `edge_score`

### `time_split_trainer.py`
Uses ordered train / validation / test splits instead of random splits.

### `walk_forward_evaluator.py`
Provides a simple walk-forward evaluation pass.

### `evaluator.py`
Writes research metrics such as:
- accuracy
- precision
- recall
- F1
- Sharpe-like metric
- drawdown

## Simulation / paper trading

### `pnl_engine.py`
Implements correct Polymarket-style share accounting.

Core formula:

```text
shares = capital_usdc / entry_price
pnl = shares * (exit_price - entry_price) - fees
```

### `position_manager.py`
Tracks open and closed paper positions using:
- `outcome_side` (`YES` / `NO`)
- `position_action` (`ENTER` / `EXIT`)
- share-based mark-to-market logic

### `path_replay_simulator.py`
Replays future price paths bar by bar and computes:
- entry time
- exit time
- holding time
- exit reason
- gross / net pnl
- MFE
- MAE
- max drawdown during trade

### `strategy_layers.py`
Starts separating:
- prediction layer
- entry rule layer
- exit rule layer

## Live-test branch additions

The `live-test` branch now contains scaffolding such as:
- `execution_client.py`
- `order_manager.py`
- `reconciliation_service.py`
- `live_risk_manager.py`
- `db.py`
- `incident_manager.py`

Those files are intended for isolated authenticated execution experiments and stronger monitoring / operational safety, and should not be confused with the paper-only main line.

Recent `live-test` work also added:
- backend alert normalization (`alert_id`, `severity`, `status`, `source_module`, `message`)
- system health snapshots in `logs/system_health.csv`
- service heartbeats in `logs/service_heartbeats.csv`
- incident lifecycle logging in `logs/incidents.csv`
- dashboard-side anomaly detection, reconciliation, and readiness checks

## UI

### `dashboard.py`
Streamlit dashboard on `live-test` now uses a monitoring-oriented layout:
- **System Status**
- **Signals & Opportunities**
- **Positions & PnL**
- **Markets, Whales & Alerts**
- **Models & Data Quality**

Recent `live-test` UI improvements include:
- real data freshness panels instead of fake refresh timestamps
- sidebar dashboard controls and global filters
- top opportunity cards with safer `N/A` handling
- ranked opportunity table with CSV export
- grouped recommended paper actions
- paper equity / drawdown charts
- richer positions and closed-trade ledger views
- market / whale / alert monitoring subtabs
- model performance and data-quality readiness views
- debug raw logs moved into a collapsible section

## Quick start

## 1) Install

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Current requirements include the newer modeling stack used by the refactor, including packages such as:
- `scikit-learn`
- `joblib`
- `lightgbm`
- `catboost`

## 2) Create / validate local env

```bash
python api_setup.py
```

## 3) Run the system

```bash
python run_bot.py
```

In another terminal:

```bash
python -m streamlit run dashboard.py
```

Optional local API:

```bash
python -m uvicorn web_api:app --reload
```

Docs:

```text
http://127.0.0.1:8000/docs
```

## Recommended Windows usage

If the repo already exists locally on the paper branch:

```powershell
git pull origin main
python -m pip install -r requirements.txt
python run_bot.py
```

If you want the separate live-test branch instead:

```powershell
git fetch origin
git checkout live-test
git pull origin live-test
python -m pip install -r requirements.txt
python run_bot.py
```

And in a second PowerShell window:

```powershell
python -m streamlit run dashboard.py
```

## Main output files

Generated in `logs/`:

- `signals.csv`
- `daily_summary.txt`
- `markets.csv`
- `whales.csv`
- `market_distribution.csv`
- `alerts.csv`
- `positions.csv`
- `closed_positions.csv`
- `historical_dataset.csv`
- `btc_targets.csv`
- `contract_targets.csv`
- `wallet_alpha.csv`
- `wallet_alpha_history.csv`
- `supervised_eval.csv`
- `time_split_eval.csv`
- `path_replay_backtest.csv`
- `model_status.csv`

## Current reality

This repo is improving fast, but it is still a **research system under active refactor**.

The newer supervised / event-driven path is the direction of travel.
The older dummy RL path still exists in parts of the codebase, but it should no longer be treated as the core intelligence for the real goal.

## Troubleshooting

### `ModuleNotFoundError` when starting

Usually this means dependencies were not refreshed after a newer modeling/UI pass.

Run:

```powershell
python -m pip install -r requirements.txt
```

Then retry:

```powershell
python run_bot.py
```

If the error mentions a specific package like `joblib`, `lightgbm`, or `catboost`, reinstalling from `requirements.txt` should fix it.

## Next intended direction

- use Gamma/Data/CLOB more directly across the pipeline
- improve wallet rolling metrics further
- improve token-level historical labeling
- rank signals primarily from trained model outputs
- keep the whole project in paper/research mode
