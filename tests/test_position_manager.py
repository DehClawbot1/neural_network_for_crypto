from unittest.mock import patch

import pandas as pd

from position_manager import PositionManager


@patch("position_manager.MarketPriceService")
def test_open_position_success(mock_price_service_cls, tmp_path):
    pm = PositionManager(logs_dir=tmp_path)

    signal = {
        "market_title": "Test Market",
        "token_id": "token_123",
        "outcome_side": "YES",
        "confidence": 0.85,
    }

    result = pm.open_position(signal, size_usdc=10.0, fill_price=0.5)

    assert result is True
    open_positions = pm.get_open_positions()
    assert len(open_positions) == 1
    assert open_positions.iloc[0]["token_id"] == "token_123"
    assert float(open_positions.iloc[0]["shares"]) == 20.0
    assert float(open_positions.iloc[0]["confidence_at_entry"]) == 0.85


@patch("position_manager.MarketPriceService")
def test_open_position_respects_max_limit(mock_price_service_cls, tmp_path):
    pm = PositionManager(logs_dir=tmp_path, max_open_positions=1)

    signal1 = {"market_title": "M1", "token_id": "t1"}
    signal2 = {"market_title": "M2", "token_id": "t2"}

    assert pm.open_position(signal1, 10.0, 0.5) is True
    assert pm.open_position(signal2, 10.0, 0.5) is False


@patch("position_manager.MarketPriceService")
def test_close_position_uses_quote_and_removes_open_position(mock_price_service_cls, tmp_path):
    mock_price_service = mock_price_service_cls.return_value
    mock_price_service.get_quote.return_value = {"best_bid": 0.75, "price": 0.76}

    pm = PositionManager(logs_dir=tmp_path)
    signal = {"market_title": "Test Market", "token_id": "token_123", "outcome_side": "YES"}
    pm.open_position(signal, size_usdc=10.0, fill_price=0.5)

    position_to_close = pm.get_open_positions().iloc[0].to_dict()
    closed_df = pm.close_position(position_to_close, reason="take_profit")

    assert not closed_df.empty
    assert closed_df.iloc[0]["status"] == "CLOSED"
    assert closed_df.iloc[0]["close_reason"] == "take_profit"
    assert float(closed_df.iloc[0]["exit_price"]) == 0.75
    assert pm.get_open_positions().empty


@patch("position_manager.MarketPriceService")
def test_update_mark_to_market_stores_spread_and_bid_size(mock_price_service_cls, tmp_path):
    mock_price_service = mock_price_service_cls.return_value
    mock_price_service.get_batch_prices.return_value = {
        "token_123": {"price": 0.62, "spread": 0.03, "best_bid_size": 150.0}
    }

    pm = PositionManager(logs_dir=tmp_path)
    signal = {"market_title": "Test Market", "token_id": "token_123", "outcome_side": "YES", "confidence": 0.85}
    pm.open_position(signal, size_usdc=10.0, fill_price=0.5)

    updated = pm.update_mark_to_market()

    assert not updated.empty
    row = updated.iloc[0]
    assert float(row["current_price"]) == 0.62
    assert float(row["spread"]) == 0.03
    assert float(row["bid_size"]) == 150.0
