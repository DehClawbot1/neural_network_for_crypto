import pandas as pd


class PNLEngine:
    """
    Correct paper PnL math for Polymarket-style share accounting.
    Research/paper-trading only.
    """

    @staticmethod
    def shares_from_capital(capital_usdc: float, entry_price: float) -> float:
        if not entry_price or entry_price <= 0:
            return 0.0
        return float(capital_usdc) / float(entry_price)

    @staticmethod
    def mark_to_market_pnl(capital_usdc: float, entry_price: float, current_price: float, side: str = "BUY") -> float:
        shares = PNLEngine.shares_from_capital(capital_usdc, entry_price)
        if str(side).upper() == "BUY":
            return shares * (float(current_price) - float(entry_price))
        return shares * (float(entry_price) - float(current_price))

    @staticmethod
    def summarize_trade(capital_usdc: float, entry_price: float, exit_price: float, side: str = "BUY") -> dict:
        shares = PNLEngine.shares_from_capital(capital_usdc, entry_price)
        pnl = PNLEngine.mark_to_market_pnl(capital_usdc, entry_price, exit_price, side=side)
        return {
            "capital_usdc": capital_usdc,
            "entry_price": entry_price,
            "exit_price": exit_price,
            "shares": shares,
            "pnl": pnl,
        }
