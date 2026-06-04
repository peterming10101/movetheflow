from ..schemas import DepthLevel, OrderBookState


class OrderBook:
    def __init__(self, symbol: str, venue: str) -> None:
        self.symbol = symbol
        self.venue = venue
        self.last_update_id: int | None = None
        self.bids: dict[float, float] = {}
        self.asks: dict[float, float] = {}
        self._expect_first_diff = False

    def apply_snapshot(self, snapshot: dict, receive_time: int) -> OrderBookState:
        self.last_update_id = int(snapshot["lastUpdateId"])
        self.bids = {float(price): float(qty) for price, qty in snapshot["bids"] if float(qty) > 0}
        self.asks = {float(price): float(qty) for price, qty in snapshot["asks"] if float(qty) > 0}
        self._expect_first_diff = True
        return self.state(receive_time=receive_time, synced=True)

    def apply_diff(self, diff: dict, receive_time: int) -> tuple[bool, OrderBookState]:
        first_id = int(diff["U"])
        final_id = int(diff["u"])
        previous_final_id = int(diff.get("pu", final_id - 1))
        if self.last_update_id is None:
            return False, self.state(receive_time=receive_time, synced=False)
        if final_id <= self.last_update_id:
            return True, self.state(receive_time=receive_time, synced=True)
        if self._expect_first_diff:
            if first_id <= self.last_update_id <= final_id or previous_final_id == self.last_update_id:
                self._expect_first_diff = False
            else:
                return False, self.state(receive_time=receive_time, synced=False)
        elif previous_final_id != self.last_update_id:
            return False, self.state(receive_time=receive_time, synced=False)
        self._apply_side(self.bids, diff.get("b", []))
        self._apply_side(self.asks, diff.get("a", []))
        self.last_update_id = final_id
        return True, self.state(receive_time=receive_time, synced=True, source_cursor=str(final_id))

    def state(self, receive_time: int, synced: bool, source_cursor: str | None = None, levels: int = 1000) -> OrderBookState:
        bids = [
            DepthLevel(price=price, quantity=qty)
            for price, qty in sorted(self.bids.items(), reverse=True)[:levels]
        ]
        asks = [
            DepthLevel(price=price, quantity=qty)
            for price, qty in sorted(self.asks.items())[:levels]
        ]
        best_bid = bids[0].price if bids else None
        best_ask = asks[0].price if asks else None
        spread = best_ask - best_bid if best_bid is not None and best_ask is not None else None
        mid = (best_bid + best_ask) / 2 if best_bid is not None and best_ask is not None else None
        return OrderBookState(
            symbol=self.symbol,
            venue=self.venue,
            lastUpdateId=self.last_update_id or 0,
            bids=bids,
            asks=asks,
            bestBid=best_bid,
            bestAsk=best_ask,
            mid=mid,
            spread=spread,
            synced=synced,
            sourceCursor=source_cursor,
            receiveTime=receive_time,
        )

    @staticmethod
    def _apply_side(side: dict[float, float], updates: list[list[str]]) -> None:
        for price_raw, qty_raw in updates:
            price = float(price_raw)
            qty = float(qty_raw)
            if qty == 0:
                side.pop(price, None)
            else:
                side[price] = qty
