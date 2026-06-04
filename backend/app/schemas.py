from enum import StrEnum
from typing import Literal
from pydantic import BaseModel, Field


AggressorSide = Literal["buy", "sell"]


class SourceQuality(StrEnum):
    complete = "complete"
    live_only = "live_only"
    partial_backfill = "partial_backfill"
    missing_gap = "missing_gap"
    rate_limited = "rate_limited"


class NormalizedTrade(BaseModel):
    symbol: str
    venue: str
    tradeId: str
    eventTime: int
    tradeTime: int
    receiveTime: int
    price: float
    quantity: float
    notional: float
    aggressorSide: AggressorSide
    isBuyerMaker: bool
    sourceCursor: str | None = None

    @property
    def dedupe_key(self) -> str:
        return f"{self.venue}:{self.symbol}:{self.tradeId}"


class DepthLevel(BaseModel):
    price: float
    quantity: float


class OrderBookState(BaseModel):
    symbol: str
    venue: str
    lastUpdateId: int
    bids: list[DepthLevel] = Field(default_factory=list)
    asks: list[DepthLevel] = Field(default_factory=list)
    bestBid: float | None = None
    bestAsk: float | None = None
    mid: float | None = None
    spread: float | None = None
    synced: bool = False
    sourceCursor: str | None = None
    receiveTime: int


class MarketDataMetrics(BaseModel):
    trade_ws_messages_received: int = 0
    trade_messages_normalized: int = 0
    trade_messages_deduped: int = 0
    trade_messages_persisted: int = 0
    trade_bus_publications: int = 0
    depth_ws_messages_received: int = 0
    depth_updates_applied: int = 0
    depth_resync_count: int = 0
    depth_status: str = "stopped"
    recorder_queue_size: int = 0
    recorder_flush_latency_ms: float = 0.0


class RecorderStatus(BaseModel):
    running: bool
    databasePath: str
    queuedTrades: int
    persistedTrades: int


class DiagnosticSnapshot(BaseModel):
    symbol: str
    liveTradeCount: int
    latestTrade: NormalizedTrade | None
    bestBid: float | None
    bestAsk: float | None
    depthSynced: bool
    depthLastUpdateId: int | None
