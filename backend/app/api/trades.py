from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
from ..market_data.trade_bus import trade_bus
from ..schemas import NormalizedTrade

router = APIRouter(prefix="/api", tags=["trades"])


@router.get("/trades/recent", response_model=list[NormalizedTrade])
async def recent_trades(limit: int = Query(default=100, ge=1, le=1000)) -> list[NormalizedTrade]:
    return trade_bus.recent(limit)


@router.websocket("/ws/trades")
async def trade_stream(websocket: WebSocket) -> None:
    await websocket.accept()
    queue = await trade_bus.subscribe()
    try:
        while True:
            trade = await queue.get()
            await websocket.send_json(trade.model_dump())
    except WebSocketDisconnect:
        pass
    finally:
        await trade_bus.unsubscribe(queue)
