export type AggressorSide = "buy" | "sell";

export type Trade = {
  symbol: string;
  venue: string;
  tradeId: string;
  eventTime: number;
  tradeTime: number;
  receiveTime: number;
  price: number;
  quantity: number;
  notional: number;
  aggressorSide: AggressorSide;
  isBuyerMaker: boolean;
  sourceCursor: string | null;
};

export type TimeCandle = {
  symbol: string;
  venue: string;
  timeframeSec: number;
  openTime: number;
  closeTime: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  notional: number;
  buyVolume: number;
  sellVolume: number;
  delta: number;
  tradeCount: number;
  isLive: boolean;
};

export type CoverageMetadata = {
  requestedStart: number | null;
  requestedEnd: number | null;
  availableStart: number | null;
  availableEnd: number | null;
  missingRanges: Array<[number, number]>;
  sourceQuality: string;
  source: string;
};

export type CandleSnapshot = {
  data: TimeCandle[];
  coverage: CoverageMetadata;
};

export type ProfileRow = {
  price: number;
  volume: number;
  buyVolume: number;
  sellVolume: number;
  delta: number;
  isPoc: boolean;
};

export type DomRow = {
  price: number;
  bid: number;
  ask: number;
  buyPrint: number;
  sellPrint: number;
  profileVolume: number;
  delta: number;
};

export type MarketOrderBubble = {
  candleOpenTime: number;
  price: number;
  side: AggressorSide;
  quantity: number;
  notional: number;
  label: string;
};

export type SpeedTapeBar = {
  time: number;
  value: number;
  buyVolume: number;
  sellVolume: number;
};

export type FootprintLevel = {
  price: number;
  bidVolume: number;
  askVolume: number;
  delta: number;
};

export type FootprintCandle = {
  openTime: number;
  closeTime: number;
  levels: FootprintLevel[];
};

export type VwapState = {
  vwap: number | null;
  upperBand: number | null;
  lowerBand: number | null;
};

export type WorkspaceSnapshot = {
  candles: TimeCandle[];
  trades: Trade[];
  dom: DomRow[];
  profile: ProfileRow[];
  bubbles: MarketOrderBubble[];
  speedTape: SpeedTapeBar[];
  footprints: FootprintCandle[];
  vwap: VwapState;
  coverage: CoverageMetadata;
  depth: unknown;
};

export type DiagnosticSnapshot = {
  symbol: string;
  liveTradeCount: number;
  latestTrade: Trade | null;
  bestBid: number | null;
  bestAsk: number | null;
  depthSynced: boolean;
  depthLastUpdateId: number | null;
};

export type Metrics = {
  trade_ws_messages_received: number;
  trade_messages_normalized: number;
  trade_messages_deduped: number;
  trade_messages_rejected: number;
  trade_messages_persisted: number;
  trade_bus_publications: number;
  depth_ws_messages_received: number;
  depth_updates_applied: number;
  depth_resync_count: number;
  depth_status: string;
  candle_updates_published: number;
  recorder_queue_size: number;
  recorder_flush_latency_ms: number;
};
