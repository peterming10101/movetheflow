import asyncio
from collections import deque
from .types import SubscriberQueue
from ..metrics import metrics
from ..schemas import NormalizedTrade


class TradeBus:
    def __init__(self, live_buffer_size: int = 20_000) -> None:
        self._seen: set[str] = set()
        self._live_buffer: deque[NormalizedTrade] = deque(maxlen=live_buffer_size)
        self._subscribers: set[SubscriberQueue[NormalizedTrade]] = set()
        self._lock = asyncio.Lock()

    async def publish(self, trade: NormalizedTrade) -> bool:
        async with self._lock:
            if trade.dedupe_key in self._seen:
                metrics.increment("trade_messages_deduped")
                return False
            self._seen.add(trade.dedupe_key)
            self._live_buffer.append(trade)
            subscribers = list(self._subscribers)
        for queue in subscribers:
            if not queue.full():
                queue.put_nowait(trade)
        metrics.increment("trade_bus_publications")
        return True

    async def subscribe(self) -> SubscriberQueue[NormalizedTrade]:
        queue: SubscriberQueue[NormalizedTrade] = asyncio.Queue(maxsize=10_000)
        async with self._lock:
            self._subscribers.add(queue)
        return queue

    async def unsubscribe(self, queue: SubscriberQueue[NormalizedTrade]) -> None:
        async with self._lock:
            self._subscribers.discard(queue)

    def latest(self) -> NormalizedTrade | None:
        return self._live_buffer[-1] if self._live_buffer else None

    def live_count(self) -> int:
        return len(self._live_buffer)


trade_bus = TradeBus()
