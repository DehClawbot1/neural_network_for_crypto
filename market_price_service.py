from datetime import datetime, timedelta, timezone

import requests


class MarketPriceService:
    CLOB_HISTORY_URL = "https://clob.polymarket.com/prices-history"
    CLOB_PRICE_URL = "https://clob.polymarket.com/price"

    def __init__(self, max_age_seconds=20):
        self.max_age_seconds = max_age_seconds
        self.cache = {}

    def _is_fresh(self, token_id):
        record = self.cache.get(str(token_id))
        if not record:
            return False
        age = (datetime.now(timezone.utc) - record["timestamp"]).total_seconds()
        return age <= self.max_age_seconds

    def get_latest_price(self, token_id, interval="1m"):
        if not token_id:
            return None
        token_id = str(token_id)
        if self._is_fresh(token_id):
            return self.cache[token_id]["price"]

        # Preferred live-like path
        try:
            response = requests.get(self.CLOB_PRICE_URL, params={"market": token_id}, timeout=10)
            if response.ok:
                payload = response.json()
                price = payload.get("price") or payload.get("mid") or payload.get("midpoint")
                if price is not None:
                    price = float(price)
                    self.cache[token_id] = {"price": price, "timestamp": datetime.now(timezone.utc)}
                    return price
        except Exception:
            pass

        # Fallback: recent history last print
        end_ts = int(datetime.now(timezone.utc).timestamp())
        start_ts = int((datetime.now(timezone.utc) - timedelta(hours=6)).timestamp())
        response = requests.get(
            self.CLOB_HISTORY_URL,
            params={
                "market": token_id,
                "startTs": start_ts,
                "endTs": end_ts,
                "interval": interval,
                "fidelity": 1,
            },
            timeout=20,
        )
        response.raise_for_status()
        history = response.json().get("history", [])
        if not history:
            return None
        price = float(history[-1].get("p", 0.0))
        self.cache[token_id] = {"price": price, "timestamp": datetime.now(timezone.utc)}
        return price

    def get_batch_prices(self, token_ids):
        prices = {}
        for token_id in token_ids:
            try:
                prices[str(token_id)] = self.get_latest_price(token_id)
            except Exception:
                prices[str(token_id)] = None
        return prices

    def get_latest_prices(self, token_ids):
        return self.get_batch_prices(token_ids)
