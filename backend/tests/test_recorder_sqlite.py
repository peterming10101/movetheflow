import sqlite3
from app.exchanges.binance_futures.normalizers import normalize_aggregate_trade
from app.market_data.recorder import SQLiteRecorder


def test_recorder_initializes_sqlite_wal_and_dedupes(tmp_path) -> None:
    recorder = SQLiteRecorder(tmp_path / "market_data.db")
    recorder.initialize()
    trade = normalize_aggregate_trade(
        {"a": 50, "E": 1000, "T": 900, "p": "2", "q": "3", "m": False},
        venue="binance_usdm",
        symbol="BTCUSDT",
    )

    recorder._persist_batch([trade, trade])

    with sqlite3.connect(recorder.database_path) as conn:
        journal_mode = conn.execute("PRAGMA journal_mode").fetchone()[0]
        rows = conn.execute("SELECT trade_id, price, quantity FROM trades").fetchall()

    assert journal_mode == "wal"
    assert rows == [("50", 2.0, 3.0)]
    assert recorder.persisted_trades == 1
