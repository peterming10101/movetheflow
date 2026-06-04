import asyncio
import sqlite3
import time
from pathlib import Path
from ..metrics import metrics
from ..schemas import NormalizedTrade, RecorderStatus


class SQLiteRecorder:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path
        self.queue: asyncio.Queue[NormalizedTrade] = asyncio.Queue(maxsize=100_000)
        self.persisted_trades = 0
        self.running = False

    def initialize(self) -> None:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.database_path) as conn:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS trades (
                  dedupe_key TEXT PRIMARY KEY,
                  symbol TEXT NOT NULL,
                  venue TEXT NOT NULL,
                  trade_id TEXT NOT NULL,
                  event_time INTEGER NOT NULL,
                  trade_time INTEGER NOT NULL,
                  receive_time INTEGER NOT NULL,
                  price REAL NOT NULL,
                  quantity REAL NOT NULL,
                  notional REAL NOT NULL,
                  aggressor_side TEXT NOT NULL,
                  is_buyer_maker INTEGER NOT NULL,
                  source_cursor TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS recorder_metadata (
                  key TEXT PRIMARY KEY,
                  value TEXT NOT NULL
                )
                """
            )

    async def enqueue(self, trade: NormalizedTrade) -> None:
        await self.queue.put(trade)
        metrics.set("recorder_queue_size", self.queue.qsize())

    async def run(self, stop: asyncio.Event) -> None:
        self.initialize()
        self.running = True
        try:
            while not stop.is_set():
                batch = await self._collect_batch()
                if batch:
                    self._persist_batch(batch)
                else:
                    await asyncio.sleep(0.05)
        finally:
            self.running = False

    async def _collect_batch(self) -> list[NormalizedTrade]:
        batch: list[NormalizedTrade] = []
        while len(batch) < 500 and not self.queue.empty():
            batch.append(self.queue.get_nowait())
        return batch

    def _persist_batch(self, batch: list[NormalizedTrade]) -> None:
        started = time.perf_counter()
        with sqlite3.connect(self.database_path) as conn:
            before = conn.total_changes
            conn.executemany(
                """
                INSERT OR IGNORE INTO trades VALUES (
                  ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                )
                """,
                [
                    (
                        t.dedupe_key,
                        t.symbol,
                        t.venue,
                        t.tradeId,
                        t.eventTime,
                        t.tradeTime,
                        t.receiveTime,
                        t.price,
                        t.quantity,
                        t.notional,
                        t.aggressorSide,
                        int(t.isBuyerMaker),
                        t.sourceCursor,
                    )
                    for t in batch
                ],
            )
            inserted = conn.total_changes - before
        self.persisted_trades += inserted
        metrics.increment("trade_messages_persisted", inserted)
        metrics.set("recorder_queue_size", self.queue.qsize())
        metrics.set("recorder_flush_latency_ms", (time.perf_counter() - started) * 1000)

    def status(self) -> RecorderStatus:
        return RecorderStatus(
            running=self.running,
            databasePath=str(self.database_path),
            queuedTrades=self.queue.qsize(),
            persistedTrades=self.persisted_trades,
        )
