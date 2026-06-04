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
    trade_messages_rejected: int = 0
    trade_messages_persisted: int = 0
    trade_bus_publications: int = 0
    depth_ws_messages_received: int = 0
    depth_updates_applied: int = 0
    depth_resync_count: int = 0
    depth_status: str = "stopped"
    candle_updates_published: int = 0
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


class TimeCandle(BaseModel):
    symbol: str
    venue: str
    timeframeSec: int
    openTime: int
    closeTime: int
    open: float
    high: float
    low: float
    close: float
    volume: float
    notional: float
    buyVolume: float = 0.0
    sellVolume: float = 0.0
    delta: float = 0.0
    tradeCount: int = 0
    isLive: bool = True


class CoverageMetadata(BaseModel):
    requestedStart: int | None = None
    requestedEnd: int | None = None
    availableStart: int | None = None
    availableEnd: int | None = None
    missingRanges: list[tuple[int, int]] = Field(default_factory=list)
    sourceQuality: SourceQuality = SourceQuality.live_only
    source: str = "live_buffer"


class CandleSnapshot(BaseModel):
    data: list[TimeCandle]
    coverage: CoverageMetadata
