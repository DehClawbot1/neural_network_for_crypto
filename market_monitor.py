import logging
from datetime import datetime

import pandas as pd
import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

GAMMA_MARKETS_URL = "https://gamma-api.polymarket.com/markets"


def fetch_btc_markets(limit=100, closed=False):
    """
    Fetch public Polymarket markets and filter for Bitcoin/BTC-related ones.
    This is for research/monitoring only.
    """
    params = {
        "limit": limit,
        "closed": str(closed).lower(),
    }

    response = requests.get(GAMMA_MARKETS_URL, params=params, timeout=20)
    response.raise_for_status()
    markets = response.json()

    btc_markets = []
    for market in markets:
        question = str(market.get("question", ""))
        title = str(market.get("title", ""))
        text_blob = f"{question} {title}".lower()

        if "bitcoin" in text_blob or "btc" in text_blob:
            btc_markets.append(
                {
                    "timestamp": datetime.utcnow().isoformat(),
                    "market_id": market.get("id"),
                    "question": question or title,
                    "active": market.get("active"),
                    "closed": market.get("closed"),
                    "liquidity": market.get("liquidity", 0),
                    "volume": market.get("volume", 0),
                    "end_date": market.get("endDate"),
                    "slug": market.get("slug"),
                    "url": f"https://polymarket.com/event/{market.get('slug')}" if market.get("slug") else None,
                }
            )

    logging.info("Fetched %s BTC-related markets.", len(btc_markets))
    return pd.DataFrame(btc_markets)


if __name__ == "__main__":
    df = fetch_btc_markets()
    if df.empty:
        print("No BTC-related markets found.")
    else:
        print(df.head()[["market_id", "question", "liquidity", "volume", "url"]])
