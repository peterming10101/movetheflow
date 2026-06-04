from app.depth.order_book import OrderBook


def test_snapshot_builds_best_bid_ask_and_spread() -> None:
    book = OrderBook("BTCUSDT", "binance_usdm")
    state = book.apply_snapshot(
        {
            "lastUpdateId": 100,
            "bids": [["49999", "1.0"], ["49998", "2.0"]],
            "asks": [["50001", "1.5"], ["50002", "1.0"]],
        },
        receive_time=1,
    )

    assert state.synced is True
    assert state.bestBid == 49999
    assert state.bestAsk == 50001
    assert state.spread == 2
    assert state.mid == 50000


def test_sequential_diff_updates_quantities_and_removes_zero_levels() -> None:
    book = OrderBook("BTCUSDT", "binance_usdm")
    book.apply_snapshot(
        {
            "lastUpdateId": 100,
            "bids": [["49999", "1.0"]],
            "asks": [["50001", "1.5"]],
        },
        receive_time=1,
    )

    ok, state = book.apply_diff(
        {"U": 101, "u": 101, "pu": 100, "b": [["49999", "0"], ["49998", "4"]], "a": [["50001", "2"]]},
        receive_time=2,
    )

    assert ok is True
    assert state.lastUpdateId == 101
    assert state.bestBid == 49998
    assert state.bestAsk == 50001
    assert state.asks[0].quantity == 2


def test_first_diff_after_snapshot_can_bridge_snapshot_update_id() -> None:
    book = OrderBook("BTCUSDT", "binance_usdm")
    book.apply_snapshot(
        {
            "lastUpdateId": 100,
            "bids": [["49999", "1.0"]],
            "asks": [["50001", "1.5"]],
        },
        receive_time=1,
    )

    ok, state = book.apply_diff(
        {"U": 95, "u": 101, "pu": 94, "b": [["50000", "2"]], "a": []},
        receive_time=2,
    )

    assert ok is True
    assert state.lastUpdateId == 101
    assert state.bestBid == 50000


def test_depth_gap_is_rejected_and_marks_unsynced() -> None:
    book = OrderBook("BTCUSDT", "binance_usdm")
    book.apply_snapshot(
        {
            "lastUpdateId": 100,
            "bids": [["49999", "1.0"]],
            "asks": [["50001", "1.5"]],
        },
        receive_time=1,
    )

    ok, state = book.apply_diff(
        {"U": 105, "u": 106, "pu": 104, "b": [], "a": []},
        receive_time=2,
    )

    assert ok is False
    assert state.synced is False
    assert state.lastUpdateId == 100
