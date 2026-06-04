from collections import defaultdict
import os
from statistics import pstdev
import httpx
from ..market_data.depth_bus import depth_bus
from ..market_data.trade_bus import trade_bus
from ..derived.time_candle_engine import time_candle_engine
from ..schemas import (
    CoverageMetadata,
    DomRow,
    FootprintCandle,
    FootprintLevel,
    MarketOrderBubble,
    NormalizedTrade,
    ProfileRow,
    SpeedTapeBar,
    VwapState,
    WorkspaceSnapshot,
    TimeCandle,
)


def bucket_price(price: float, step: float) -> float:
    return round(round(price / step) * step, 8)


async def build_workspace_snapshot(timeframe_sec: int = 60, limit: int = 240, price_step: float = 5.0) -> WorkspaceSnapshot:
    candle_snapshot = await time_candle_engine.snapshot(timeframe_sec, limit)
    candles = await load_time_candle_history(timeframe_sec, limit)
    if candle_snapshot.data:
        live_by_time = {candle.openTime: candle for candle in candle_snapshot.data}
        merged = [live_by_time.get(candle.openTime, candle) for candle in candles]
        known = {candle.openTime for candle in merged}
        merged.extend(candle for candle in candle_snapshot.data if candle.openTime not in known)
        candles = sorted(merged, key=lambda candle: candle.openTime)[-limit:]
    trades = trade_bus.recent(2000)
    newest_trades = trades[:200]
    depth = depth_bus.latest()
    profile = build_profile(trades, price_step, candles)
    return WorkspaceSnapshot(
        candles=candles,
        trades=newest_trades,
        dom=build_dom(depth, trades, profile, price_step),
        profile=profile,
        bubbles=build_market_order_bubbles(trades, timeframe_sec),
        speedTape=build_speed_tape(trades, candles),
        footprints=build_footprints(trades, timeframe_sec, price_step),
        vwap=build_vwap(trades),
        coverage=CoverageMetadata(
            availableStart=candle_snapshot.coverage.availableStart,
            availableEnd=candles[-1].closeTime if candles else candle_snapshot.coverage.availableEnd,
            sourceQuality="live_only" if os.environ.get("MOVETHEFLOW_DISABLE_LIVE") == "1" else "partial_backfill",
            source="exchange_klines_plus_live_buffer" if candles else "live_buffer",
        ),
        depth=depth,
    )


async def load_time_candle_history(timeframe_sec: int, limit: int) -> list[TimeCandle]:
    if os.environ.get("MOVETHEFLOW_DISABLE_LIVE") == "1":
        return []
    interval = {
        60: "1m",
        120: "2m",
        300: "5m",
        900: "15m",
        3600: "1h",
    }.get(timeframe_sec, "1m")
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            response = await client.get(
                "https://fapi.binance.com/fapi/v1/klines",
                params={"symbol": "BTCUSDT", "interval": interval, "limit": min(limit, 1000)},
            )
            response.raise_for_status()
            rows = response.json()
    except Exception:
        return []
    candles: list[TimeCandle] = []
    for row in rows:
        open_time = int(row[0])
        close_time = int(row[6])
        candles.append(
            TimeCandle(
                symbol="BTCUSDT",
                venue="binance_usdm",
                timeframeSec=timeframe_sec,
                openTime=open_time,
                closeTime=close_time,
                open=float(row[1]),
                high=float(row[2]),
                low=float(row[3]),
                close=float(row[4]),
                volume=float(row[5]),
                notional=float(row[7]),
                tradeCount=int(row[8]),
                isLive=False,
            )
        )
    return candles


def build_profile(trades: list[NormalizedTrade], price_step: float, candles: list[TimeCandle] | None = None) -> list[ProfileRow]:
    rows: dict[float, ProfileRow] = {}
    for candle in candles or []:
        price = bucket_price(candle.close, price_step)
        row = rows.setdefault(price, ProfileRow(price=price))
        buy = candle.volume if candle.close >= candle.open else 0.0
        sell = candle.volume if candle.close < candle.open else 0.0
        row.volume += candle.volume
        row.buyVolume += buy
        row.sellVolume += sell
        row.delta += buy - sell
    for trade in trades:
        price = bucket_price(trade.price, price_step)
        row = rows.setdefault(price, ProfileRow(price=price))
        buy = trade.quantity if trade.aggressorSide == "buy" else 0.0
        sell = trade.quantity if trade.aggressorSide == "sell" else 0.0
        row.volume += trade.quantity
        row.buyVolume += buy
        row.sellVolume += sell
        row.delta += buy - sell
    if not rows:
        return []
    poc_price = max(rows.values(), key=lambda row: row.volume).price
    for row in rows.values():
        row.isPoc = row.price == poc_price
    return sorted(rows.values(), key=lambda row: row.price)


def build_dom(depth, trades: list[NormalizedTrade], profile: list[ProfileRow], price_step: float) -> list[DomRow]:
    quantities: dict[float, DomRow] = {}
    if depth:
        for level in depth.bids:
            price = bucket_price(level.price, price_step)
            quantities.setdefault(price, DomRow(price=price)).bid += level.quantity
        for level in depth.asks:
            price = bucket_price(level.price, price_step)
            quantities.setdefault(price, DomRow(price=price)).ask += level.quantity
    for row in profile:
        dom_row = quantities.setdefault(row.price, DomRow(price=row.price))
        dom_row.profileVolume = row.volume
        dom_row.delta = row.delta
    for trade in trades[:800]:
        price = bucket_price(trade.price, price_step)
        dom_row = quantities.setdefault(price, DomRow(price=price))
        if trade.aggressorSide == "buy":
            dom_row.buyPrint += trade.quantity
        else:
            dom_row.sellPrint += trade.quantity
    if depth and depth.mid is not None:
        center = bucket_price(depth.mid, price_step)
        prices = [center + (i * price_step) for i in range(-55, 56)]
    else:
        prices = sorted(quantities)
    rows = [quantities.get(price, DomRow(price=price)) for price in prices]
    return sorted(rows, key=lambda row: row.price, reverse=True)


def build_market_order_bubbles(trades: list[NormalizedTrade], timeframe_sec: int) -> list[MarketOrderBubble]:
    grouped: dict[tuple[int, str], tuple[float, float, float]] = defaultdict(lambda: (0.0, 0.0, 0.0))
    bucket_ms = timeframe_sec * 1000
    for trade in trades[:1000]:
        bucket = (trade.tradeTime // bucket_ms) * bucket_ms
        key = (bucket, trade.aggressorSide)
        quantity, notional, price_total = grouped[key]
        grouped[key] = (quantity + trade.quantity, notional + trade.notional, price_total + trade.price * trade.quantity)
    bubbles: list[MarketOrderBubble] = []
    for (open_time, side), (quantity, notional, price_total) in grouped.items():
        if notional < 25_000:
            continue
        price = price_total / quantity if quantity else 0.0
        bubbles.append(
            MarketOrderBubble(
                candleOpenTime=open_time,
                price=price,
                side=side,
                quantity=quantity,
                notional=notional,
                label=str(int(quantity)),
            )
        )
    return sorted(bubbles, key=lambda bubble: bubble.candleOpenTime)[-24:]


def build_speed_tape(trades: list[NormalizedTrade], candles: list[TimeCandle] | None = None) -> list[SpeedTapeBar]:
    rows: dict[int, tuple[float, float]] = defaultdict(lambda: (0.0, 0.0))
    for candle in candles or []:
        buy = candle.volume if candle.close >= candle.open else 0.0
        sell = candle.volume if candle.close < candle.open else 0.0
        rows[candle.openTime] = (buy, sell)
    for trade in trades[:2000]:
        bucket = (trade.tradeTime // 1000) * 1000
        buy, sell = rows[bucket]
        if trade.aggressorSide == "buy":
            buy += trade.quantity
        else:
            sell += trade.quantity
        rows[bucket] = (buy, sell)
    return [
        SpeedTapeBar(time=time, value=buy - sell, buyVolume=buy, sellVolume=sell)
        for time, (buy, sell) in sorted(rows.items())[-180:]
    ]


def build_footprints(trades: list[NormalizedTrade], timeframe_sec: int, price_step: float) -> list[FootprintCandle]:
    buckets: dict[int, dict[float, FootprintLevel]] = {}
    bucket_ms = timeframe_sec * 1000
    for trade in trades[:2000]:
        open_time = (trade.tradeTime // bucket_ms) * bucket_ms
        price = bucket_price(trade.price, price_step)
        levels = buckets.setdefault(open_time, {})
        level = levels.setdefault(price, FootprintLevel(price=price))
        if trade.aggressorSide == "buy":
            level.askVolume += trade.quantity
        else:
            level.bidVolume += trade.quantity
        level.delta = level.askVolume - level.bidVolume
    footprints: list[FootprintCandle] = []
    for open_time, levels in sorted(buckets.items())[-24:]:
        footprints.append(
            FootprintCandle(
                openTime=open_time,
                closeTime=open_time + bucket_ms - 1,
                levels=sorted(levels.values(), key=lambda level: level.price, reverse=True)[:32],
            )
        )
    return footprints


def build_vwap(trades: list[NormalizedTrade]) -> VwapState:
    if not trades:
        return VwapState()
    total_volume = sum(trade.quantity for trade in trades)
    if total_volume <= 0:
        return VwapState()
    vwap = sum(trade.price * trade.quantity for trade in trades) / total_volume
    prices = [trade.price for trade in trades[:1000]]
    deviation = pstdev(prices) if len(prices) > 1 else 0.0
    return VwapState(vwap=vwap, upperBand=vwap + deviation, lowerBand=vwap - deviation)
