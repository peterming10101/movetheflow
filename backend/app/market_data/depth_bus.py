import asyncio
from .types import SubscriberQueue
from ..schemas import OrderBookState


class DepthBus:
    def __init__(self) -> None:
        self._latest: OrderBookState | None = None
        self._subscribers: set[SubscriberQueue[OrderBookState]] = set()
        self._lock = asyncio.Lock()

    async def publish(self, state: OrderBookState) -> None:
        async with self._lock:
            self._latest = state
            subscribers = list(self._subscribers)
        for queue in subscribers:
            if not queue.full():
                queue.put_nowait(state)

    async def subscribe(self) -> SubscriberQueue[OrderBookState]:
        queue: SubscriberQueue[OrderBookState] = asyncio.Queue(maxsize=1000)
        async with self._lock:
            self._subscribers.add(queue)
        return queue

    async def unsubscribe(self, queue: SubscriberQueue[OrderBookState]) -> None:
        async with self._lock:
            self._subscribers.discard(queue)

    def latest(self) -> OrderBookState | None:
        return self._latest


depth_bus = DepthBus()
