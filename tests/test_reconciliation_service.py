from unittest.mock import patch

import pandas as pd

from reconciliation_service import ReconciliationService


@patch("reconciliation_service.ExecutionClient")
def test_reconcile_filters_out_closed_local_orders(mock_client_cls, tmp_path):
    logs = tmp_path

    pd.DataFrame(
        [
            {"order_id": "open-1", "status": "SUBMITTED"},
            {"order_id": "filled-1", "status": "FILLED"},
            {"order_id": "closed-1", "status": "CANCELED"},
        ]
    ).to_csv(logs / "live_orders.csv", index=False)
    pd.DataFrame([{"trade_id": "trade-1", "order_id": "filled-1"}]).to_csv(logs / "live_fills.csv", index=False)

    client = mock_client_cls.return_value
    client.get_open_orders.return_value = [{"order_id": "open-1", "status": "OPEN"}]
    client.get_trades.return_value = [{"trade_id": "trade-1", "order_id": "filled-1"}]

    service = ReconciliationService(logs_dir=logs)
    report, remote_orders_df, remote_trades_df = service.reconcile()

    assert report["missing_remote_orders"] == []
    assert report["missing_local_orders"] == []
    assert report["missing_local_trades"] == []
    assert report["missing_remote_trades"] == []
    assert len(remote_orders_df) == 1
    assert len(remote_trades_df) == 1


@patch("reconciliation_service.ExecutionClient")
def test_reconcile_reports_status_and_size_mismatch_for_open_orders(mock_client_cls, tmp_path):
    pd.DataFrame(
        [{"order_id": "open-1", "status": "SUBMITTED", "size": 10}]
    ).to_csv(tmp_path / "live_orders.csv", index=False)
    pd.DataFrame([]).to_csv(tmp_path / "live_fills.csv", index=False)

    client = mock_client_cls.return_value
    client.get_open_orders.return_value = [{"order_id": "open-1", "status": "OPEN", "size": 12}]
    client.get_trades.return_value = []

    service = ReconciliationService(logs_dir=tmp_path)
    report, _, _ = service.reconcile()

    assert len(report["order_mismatches"]) == 1
    mismatch = report["order_mismatches"][0]
    assert mismatch["order_id"] == "open-1"
    assert str(mismatch["local_status"]) == "SUBMITTED"
    assert str(mismatch["remote_status"]) == "OPEN"
