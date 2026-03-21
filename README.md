# Neural Network for Crypto

Self-learning Polymarket copy-trader built around PolyMarket signals. This repository hosts the workspace, environments, RL brain, execution logic, and automation scripts for the PolyTrade agent.

## Get the code on your PC

### 1) Clone the repository

```bash
git clone https://github.com/DehClawbot1/neural_network_for_crypto.git
cd neural_network_for_crypto
```

### 2) Create a Python virtual environment

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

```bash
pip install -r requirements.txt
```

## Configure secrets

Create a `.env` file in the project root.

Example:

```env
POLYMARKET_PRIVATE_KEY=your_level_1_private_key_here
POLYMARKET_API_KEY=
POLYMARKET_API_SECRET=
POLYMARKET_API_PASSPHRASE=
POLYMARKET_CHAIN_ID=137
```

Notes:
- `.env` is ignored by git and stays local on your PC.
- `private_keys.json` is also ignored.
- API key, secret, and passphrase can be derived by a setup script later.

## How to run

The full trading stack is still being scaffolded. Once the scripts are added, the expected flow will be:

### Run the setup/bootstrap step

```bash
python setup_api.py
```

This will:
- read your Level 1 private key
- derive Level 2 API credentials
- store them for runtime use

### Run the bot supervisor

```bash
python supervisor.py
```

Expected supervisor loop:
- fetch signals
- consult RL model
- place or skip trades
- track resolutions
- retrain model
- save weights into `weights/`
- update `daily_summary.txt`

## Project structure

Planned structure:

```text
neural_network_for_crypto/
├── README.md
├── requirements.txt
├── .gitignore
├── .env
├── weights/
├── setup_api.py
├── alpha_signal_scraper.py
├── main_bot.py
├── supervisor.py
└── daily_summary.txt
```

## Update the code later

To pull the latest version on your PC:

```bash
git pull origin main
```

## Current status

Right now this repository contains the initial scaffold:
- README
- gitignore
- requirements

The trading logic, RL environment, execution engine, and supervisor loop are the next pieces being built.
