from ..exchanges.binance_futures.normalizers import now_ms
from ..metrics import metrics
from ..schemas import OrderBookState
from .order_book import OrderBook


class DepthManager:
    def __init__(self, symbol: str, venue: str) -> None:
        self.order_book = OrderBook(symbol=symbol, venue=venue)
        self.synced = False

    def apply_snapshot(self, snapshot: dict) -> OrderBookState:
        self.synced = True
        metrics.set("depth_status", "synced")
        return self.order_book.apply_snapshot(snapshot, receive_time=now_ms())

    def apply_diff(self, diff: dict) -> OrderBookState:
        ok, state = self.order_book.apply_diff(diff, receive_time=now_ms())
        if ok:
            self.synced = True
            metrics.increment("depth_updates_applied")
            metrics.set("depth_status", "synced")
        else:
            self.synced = False
            metrics.increment("depth_resync_count")
            metrics.set("depth_status", "resync_required")
        return state
