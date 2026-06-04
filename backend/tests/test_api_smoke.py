import os

os.environ["MOVETHEFLOW_DISABLE_LIVE"] = "1"

from fastapi.testclient import TestClient
from app.main import app


def test_health_and_metrics_endpoint_with_live_disabled() -> None:
    with TestClient(app) as client:
        health = client.get("/health")
        metrics = client.get("/api/metrics/market-data")
        recorder = client.get("/api/recorder/status")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"
    assert metrics.status_code == 200
    assert "trade_ws_messages_received" in metrics.json()
    assert recorder.status_code == 200
    assert recorder.json()["databasePath"].endswith("market_data.db")
