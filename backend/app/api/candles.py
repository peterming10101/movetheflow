from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
from ..derived.time_candle_engine import time_candle_engine
from ..schemas import CandleSnapshot

router = APIRouter(prefix="/api", tags=["candles"])


@router.get("/candles/time", response_model=CandleSnapshot)
async def time_candles(
    timeframe: int = Query(default=60, ge=1, le=3600),
    limit: int = Query(default=200, ge=1, le=1000),
) -> CandleSnapshot:
    return await time_candle_engine.snapshot(timeframe, limit)


@router.websocket("/ws/candles/time")
async def time_candle_stream(websocket: WebSocket, timeframe: int = 60) -> None:
    await websocket.accept()
    queue = await time_candle_engine.subscribe()
    try:
        while True:
            candle = await queue.get()
            if candle.timeframeSec == timeframe:
                await websocket.send_json(candle.model_dump())
    except WebSocketDisconnect:
        pass
    finally:
        await time_candle_engine.unsubscribe(queue)
