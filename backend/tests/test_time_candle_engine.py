import pytest
from app.derived.time_candle_engine import TimeCandleEngine
from app.schemas import NormalizedTrade


def trade(trade_id: str, trade_time: int, price: float, quantity: float, side: str) -> NormalizedTrade:
    return NormalizedTrade(
        symbol="BTCUSDT",
        venue="binance_usdm",
        tradeId=trade_id,
        eventTime=trade_time,
        tradeTime=trade_time,
        receiveTime=trade_time,
        price=price,
        quantity=quantity,
        notional=price * quantity,
        aggressorSide=side,
        isBuyerMaker=side == "sell",
        sourceCursor=trade_id,
    )


@pytest.mark.asyncio
async def test_time_candle_aggregates_ohlcv_and_delta() -> None:
    engine = TimeCandleEngine(timeframes=(60,))

    await engine.on_trade(trade("1", 60_000, 100.0, 1.0, "buy"))
    await engine.on_trade(trade("2", 61_000, 105.0, 2.0, "sell"))
    await engine.on_trade(trade("3", 62_000, 95.0, 0.5, "buy"))
    snapshot = await engine.snapshot(60)

    candle = snapshot.data[0]
    assert candle.open == 100.0
    assert candle.high == 105.0
    assert candle.low == 95.0
    assert candle.close == 95.0
    assert candle.volume == pytest.approx(3.5)
    assert candle.buyVolume == pytest.approx(1.5)
    assert candle.sellVolume == pytest.approx(2.0)
    assert candle.delta == pytest.approx(-0.5)
    assert candle.tradeCount == 3
    assert candle.isLive is True


@pytest.mark.asyncio
async def test_time_candle_closes_immutably_when_new_bucket_starts() -> None:
    engine = TimeCandleEngine(timeframes=(60,))

    await engine.on_trade(trade("1", 60_000, 100.0, 1.0, "buy"))
    await engine.on_trade(trade("2", 120_000, 110.0, 1.0, "buy"))
    first_snapshot = await engine.snapshot(60)
    closed_before_more_trades = first_snapshot.data[0]

    await engine.on_trade(trade("3", 121_000, 90.0, 5.0, "sell"))
    await engine.on_trade(trade("4", 122_000, 130.0, 2.0, "buy"))
    snapshot = await engine.snapshot(60)

    assert len(snapshot.data) == 2
    assert snapshot.data[0].openTime == 60_000
    assert snapshot.data[0].isLive is False
    assert snapshot.data[0].close == 100.0
    assert snapshot.data[0] == closed_before_more_trades
    assert snapshot.data[1].openTime == 120_000
    assert snapshot.data[1].isLive is True
    assert snapshot.data[1].high == 130.0
    assert snapshot.data[1].low == 90.0
