import time
from typing import Any
from ...schemas import NormalizedTrade


def now_ms() -> int:
    return int(time.time() * 1000)


def normalize_aggregate_trade(payload: dict[str, Any], venue: str, symbol: str) -> NormalizedTrade:
    trade_id = payload.get("a", payload.get("t"))
    is_buyer_maker = bool(payload["m"])
    quantity = float(payload["q"])
    price = float(payload["p"])
    return NormalizedTrade(
        symbol=symbol.upper(),
        venue=venue,
        tradeId=str(trade_id),
        eventTime=int(payload.get("E", payload["T"])),
        tradeTime=int(payload["T"]),
        receiveTime=now_ms(),
        price=price,
        quantity=quantity,
        notional=price * quantity,
        aggressorSide="sell" if is_buyer_maker else "buy",
        isBuyerMaker=is_buyer_maker,
        sourceCursor=str(payload.get("l", trade_id)),
    )
