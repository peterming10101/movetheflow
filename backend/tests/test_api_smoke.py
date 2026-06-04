import os

os.environ["MOVETHEFLOW_DISABLE_LIVE"] = "1"

from fastapi.testclient import TestClient
from app.main import app


def test_health_and_metrics_endpoint_with_live_disabled() -> None:
    with TestClient(app) as client:
        health = client.get("/health")
        metrics = client.get("/api/metrics/market-data")
        recorder = client.get("/api/recorder/status")
        candles = client.get("/api/candles/time?timeframe=60&limit=10")
        trades = client.get("/api/trades/recent?limit=10")
        workspace = client.get("/api/workspace?timeframe=60&limit=20")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"
    assert metrics.status_code == 200
    assert "trade_ws_messages_received" in metrics.json()
    assert recorder.status_code == 200
    assert recorder.json()["databasePath"].endswith("market_data.db")
    assert candles.status_code == 200
    assert candles.json()["coverage"]["sourceQuality"] == "live_only"
    assert trades.status_code == 200
    assert trades.json() == []
    assert workspace.status_code == 200
    assert "dom" in workspace.json()
    assert "speedTape" in workspace.json()
