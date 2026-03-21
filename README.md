# Neural Network for Crypto: PolyMarket Paper-Trader

This repository contains an autonomous, Reinforcement Learning (RL) powered copy-trading bot designed for PolyMarket.

Currently configured for **Paper-Trading Only**, the bot uses a Proximal Policy Optimization (PPO) neural network to filter and evaluate trade signals from the most profitable crypto traders on the platform, simulating executions to forward-test its accuracy without risking live capital.

## 🧠 System Architecture

The pipeline consists of five core components working in sequence:

1. **`api_setup.py` (The Validator)**  
   Validates the local `.env` configuration to ensure the bot is strictly locked into paper-trading mode. Generates a safe template if one does not exist.

2. **`leaderboard_scraper.py` (The Eyes)**  
   Polls the PolyMarket Data API to identify the Top 5 most profitable traders in the `CRYPTO` category. It then scans their on-chain activity for recent bets specifically on Bitcoin (BTC) price markets.

3. **`polytrade_env.py` (The Logic)**  
   A custom `gymnasium` environment. It defines how the bot perceives incoming signals (Trader Win Rate, Trade Size, Price, Time Left) and maps out the possible actions (Ignore, Follow Small, Follow Large).

4. **`rl_trainer.py` (The Trainer)**  
   Utilizes `stable-baselines3` to train the PPO model within the custom environment. It learns to maximize simulated profit by penalizing bad copy-trades and rewarding successful ones, saving its brain to `weights/ppo_polytrader.zip`.

5. **`supervisor.py` (The Heartbeat)**  
   The continuous autonomous loop. It scrapes live signals, enriches them with market context, ranks paper-trading opportunities, feeds normalized features through the trained RL model, and logs hypothetical fills, including simulated slippage, to `logs/daily_summary.txt`.

6. **`market_monitor.py` (The Market Context Layer)**  
   Fetches public Polymarket market data and filters BTC-related markets for real-time research context.

7. **`feature_builder.py` (The Feature Layer)**  
   Merges scraped signals with market context and builds normalized features for scoring and paper-trading evaluation.

8. **`signal_engine.py` (The Ranking Layer)**  
   Scores each candidate into safe research labels such as `IGNORE`, `WATCH`, `PAPER_SMALL`, and `PAPER_LARGE`, with confidence and reason text.

## 🚀 Installation & Setup

### 1) Get the code

```bash
git clone https://github.com/DehClawbot1/neural_network_for_crypto.git
cd neural_network_for_crypto
```

### 2) Create a virtual environment

**Windows PowerShell**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**Windows CMD**

```cmd
python -m venv .venv
.venv\Scripts\activate.bat
```

### 3) Install dependencies

Ensure you have Python 3.9+ installed, then run:

```bash
pip install -r requirements.txt
```

### 4) Initialize the environment

Run the setup script to generate your secure paper-trading configuration:

```bash
python api_setup.py
```

This will create a `.env` file with simulated starting balances.

**Do not add live L1/L2 keys to this file.**

## 🤖 Execution Guide

To run the full paper-trading simulation, execute the following steps in order.

### Step 1: Train the neural network

Generate the initial weights for the bot's decision engine:

```bash
python rl_trainer.py
```

This creates:
- `weights/ppo_polytrader.zip`

### Step 2: Start the autonomous supervisor

Launch the zero-intervention observation and execution loop:

```bash
python supervisor.py
```

During each cycle, the supervisor will:
- fetch BTC-related market context
- scrape public wallet activity
- build normalized features
- rank the top paper-trading opportunities
- simulate paper fills

### Step 3: Monitor performance and opportunities

Check these output files:

```text
logs/daily_summary.txt
logs/signals.csv
```

- `logs/daily_summary.txt` records mock fills and simulated slippage
- `logs/signals.csv` records ranked opportunities, confidence, and reason strings

## 📁 Repository Structure

```text
neural_network_for_crypto/
├── README.md
├── requirements.txt
├── .gitignore
├── .env                 # generated locally, ignored by git
├── api_setup.py
├── leaderboard_scraper.py
├── market_monitor.py
├── feature_builder.py
├── signal_engine.py
├── polytrade_env.py
├── rl_trainer.py
├── supervisor.py
├── logs/
│   ├── daily_summary.txt
│   └── signals.csv
└── weights/
    └── ppo_polytrader.zip
```

## 🔒 Safety Notes

- This project is configured for **paper trading only**.
- Live API credentials are not required for the current architecture.
- `api_setup.py` warns if live trading keys are present.
- `supervisor.py` does **not** place real trades.
- All executions are simulated and logged locally.

## ✅ Current Status

The repository now includes:
- live signal scraping from PolyMarket data endpoints
- BTC market context monitoring
- feature building for real-time research
- confidence-ranked paper-trading opportunities
- a custom Gymnasium environment
- PPO training via Stable Baselines3
- a paper-trading supervisor loop
- safe `.env` validation for simulation mode
- local logging for forward-testing

This is a forward-testing and simulation architecture intended to validate behavior safely before any discussion of real capital or live execution.
