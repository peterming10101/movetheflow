import asyncio
from collections import deque
from ..metrics import metrics
from ..schemas import CandleSnapshot, CoverageMetadata, NormalizedTrade, TimeCandle


class TimeCandleEngine:
    def __init__(self, timeframes: tuple[int, ...] = (60, 300), history_size: int = 1000) -> None:
        self.timeframes = timeframes
        self.history_size = history_size
        self._closed: dict[int, deque[TimeCandle]] = {
            timeframe: deque(maxlen=history_size) for timeframe in timeframes
        }
        self._live: dict[int, TimeCandle] = {}
        self._subscribers: set[asyncio.Queue[TimeCandle]] = set()
        self._lock = asyncio.Lock()

    async def on_trade(self, trade: NormalizedTrade) -> list[TimeCandle]:
        updates: list[TimeCandle] = []
        async with self._lock:
            for timeframe in self.timeframes:
                updates.append(self._apply_trade(timeframe, trade))
            subscribers = list(self._subscribers)
        for candle in updates:
            for queue in subscribers:
                if not queue.full():
                    queue.put_nowait(candle)
            metrics.increment("candle_updates_published")
        return updates

    async def subscribe(self) -> asyncio.Queue[TimeCandle]:
        queue: asyncio.Queue[TimeCandle] = asyncio.Queue(maxsize=5000)
        async with self._lock:
            self._subscribers.add(queue)
        return queue

    async def unsubscribe(self, queue: asyncio.Queue[TimeCandle]) -> None:
        async with self._lock:
            self._subscribers.discard(queue)

    async def snapshot(self, timeframe_sec: int, limit: int = 200) -> CandleSnapshot:
        async with self._lock:
            candles = list(self._closed.get(timeframe_sec, []))
            live = self._live.get(timeframe_sec)
            if live:
                candles.append(live)
            candles = candles[-limit:]
        available_start = candles[0].openTime if candles else None
        available_end = candles[-1].closeTime if candles else None
        return CandleSnapshot(
            data=candles,
            coverage=CoverageMetadata(
                availableStart=available_start,
                availableEnd=available_end,
                sourceQuality="live_only",
                source="live_buffer",
            ),
        )

    def _apply_trade(self, timeframe_sec: int, trade: NormalizedTrade) -> TimeCandle:
        bucket_ms = timeframe_sec * 1000
        open_time = (trade.tradeTime // bucket_ms) * bucket_ms
        close_time = open_time + bucket_ms - 1
        live = self._live.get(timeframe_sec)
        if live is not None and live.openTime != open_time:
            self._closed[timeframe_sec].append(live.model_copy(update={"isLive": False}))
            live = None
        if live is None:
            live = TimeCandle(
                symbol=trade.symbol,
                venue=trade.venue,
                timeframeSec=timeframe_sec,
                openTime=open_time,
                closeTime=close_time,
                open=trade.price,
                high=trade.price,
                low=trade.price,
                close=trade.price,
                volume=0.0,
                notional=0.0,
                buyVolume=0.0,
                sellVolume=0.0,
                delta=0.0,
                tradeCount=0,
                isLive=True,
            )
        buy_volume = trade.quantity if trade.aggressorSide == "buy" else 0.0
        sell_volume = trade.quantity if trade.aggressorSide == "sell" else 0.0
        live = live.model_copy(
            update={
                "high": max(live.high, trade.price),
                "low": min(live.low, trade.price),
                "close": trade.price,
                "volume": live.volume + trade.quantity,
                "notional": live.notional + trade.notional,
                "buyVolume": live.buyVolume + buy_volume,
                "sellVolume": live.sellVolume + sell_volume,
                "delta": live.delta + buy_volume - sell_volume,
                "tradeCount": live.tradeCount + 1,
            }
        )
        self._live[timeframe_sec] = live
        return live


time_candle_engine = TimeCandleEngine()
