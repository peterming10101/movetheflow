import pytest
from app.exchanges.binance_futures.normalizers import normalize_aggregate_trade
from app.market_data.trade_bus import TradeBus


def test_binance_aggregate_trade_normalizes_aggressor_buy() -> None:
    trade = normalize_aggregate_trade(
        {"a": 10, "E": 1000, "T": 900, "p": "50000.50", "q": "0.200", "m": False},
        venue="binance_usdm",
        symbol="BTCUSDT",
    )

    assert trade.tradeId == "10"
    assert trade.aggressorSide == "buy"
    assert trade.notional == pytest.approx(10000.10)
    assert trade.dedupe_key == "binance_usdm:BTCUSDT:10"


def test_binance_aggregate_trade_normalizes_aggressor_sell() -> None:
    trade = normalize_aggregate_trade(
        {"a": 11, "E": 1000, "T": 900, "p": "50000", "q": "0.100", "m": True},
        venue="binance_usdm",
        symbol="BTCUSDT",
    )

    assert trade.aggressorSide == "sell"
    assert trade.isBuyerMaker is True


def test_binance_raw_trade_payload_uses_trade_id() -> None:
    trade = normalize_aggregate_trade(
        {"t": 99, "E": 1000, "T": 900, "p": "50000", "q": "0.100", "m": True},
        venue="binance_usdm",
        symbol="BTCUSDT",
    )

    assert trade.tradeId == "99"
    assert trade.sourceCursor == "99"


def test_non_positive_trade_price_is_rejected() -> None:
    with pytest.raises(ValueError):
        normalize_aggregate_trade(
            {"t": 100, "E": 1000, "T": 900, "p": "0", "q": "0.100", "m": True},
            venue="binance_usdm",
            symbol="BTCUSDT",
        )


@pytest.mark.asyncio
async def test_trade_bus_dedupes_by_canonical_key() -> None:
    bus = TradeBus()
    trade = normalize_aggregate_trade(
        {"a": 12, "E": 1000, "T": 900, "p": "1", "q": "2", "m": False},
        venue="binance_usdm",
        symbol="BTCUSDT",
    )

    assert await bus.publish(trade) is True
    assert await bus.publish(trade) is False
    assert bus.live_count() == 1
