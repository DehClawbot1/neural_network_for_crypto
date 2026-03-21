import os
import logging
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def validate_environment():
    """
    Validates the presence and structure of the .env file for paper-trading.
    Strictly enforces simulation mode and ignores/warns about live cryptographic keys.
    """
    logging.info("Validating local environment setup for Paper Trading...")

    env_path = ".env"

    # 1. Check if .env exists, create a safe template if it doesn't
    if not os.path.exists(env_path):
        logging.warning("[-] .env file not found. Generating a safe simulation template...")
        with open(env_path, "w", encoding="utf-8") as f:
            f.write("# PolyMarket Bot - Paper Trading Configuration\n")
            f.write("PAPER_TRADE_MODE=True\n")
            f.write("SIMULATED_STARTING_BALANCE=1000\n")
            f.write("MAX_RISK_PER_TRADE=50\n")
        logging.info("[+] Safe .env template created. Please review variables.")
        return False

    # 2. Load and verify environment variables
    load_dotenv()

    mode = os.getenv("PAPER_TRADE_MODE")
    balance = os.getenv("SIMULATED_STARTING_BALANCE")

    # 3. Guardrail: Warn if live keys are accidentally present
    if os.getenv("POLY_API_KEY") or os.getenv("PK_LEVEL_1"):
        logging.warning(
            "[!] WARNING: Live API keys detected in .env. This system is restricted to PAPER TRADING ONLY. Live keys will be ignored."
        )

    if str(mode).lower() == "true" and balance:
        logging.info(f"[+] Environment validated. Running in PAPER_TRADE_MODE with ${balance} simulated balance.")
        return True
    else:
        logging.error(
            "[-] Invalid .env configuration. Please ensure PAPER_TRADE_MODE=True and SIMULATED_STARTING_BALANCE are set."
        )
        return False


if __name__ == "__main__":
    is_valid = validate_environment()
    if is_valid:
        print("\n[+] System is cleared for autonomous paper-trading execution. You may start supervisor.py.")
    else:
        print("\n[-] Validation failed or template generated. Please check your .env file and run again.")
