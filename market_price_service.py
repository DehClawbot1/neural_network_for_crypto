from datetime import datetime, timedelta, timezone

import asyncio
import json

import requests


class MarketPriceService:
    CLOB_HISTORY_URL = "https://clob.polymarket.com/prices-history"
    CLOB_PRICE_URL = "https://clob.polymarket.com/price"
    CLOB_WS_URL = "wss://ws-subscriptions-clob.polymarket.com/ws/market"

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

    async def stream_prices(self, token_ids, update_callback=None):
        try:
            import websockets
        except Exception:
            return

        async with websockets.connect(self.CLOB_WS_URL) as ws:
            await ws.send(json.dumps({
                "assets_ids": [str(t) for t in token_ids if t],
                "type": "market",
                "custom_feature_enabled": True,
            }))

            while True:
                msg = json.loads(await ws.recv())
                token_id = str(msg.get("asset_id") or msg.get("market") or "")
                price = msg.get("price") or msg.get("mid") or msg.get("best_ask") or msg.get("best_bid")
                if token_id and price is not None:
                    self.cache[token_id] = {"price": float(price), "timestamp": datetime.now(timezone.utc)}
                    if update_callback is not None:
                        update_callback(token_id, float(price), msg)

    def stream_prices_forever(self, token_ids, update_callback=None):
        asyncio.run(self.stream_prices(token_ids, update_callback=update_callback))
