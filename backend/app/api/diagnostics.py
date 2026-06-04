from fastapi import APIRouter, Request
from ..market_data.depth_bus import depth_bus
from ..market_data.trade_bus import trade_bus
from ..schemas import DiagnosticSnapshot, RecorderStatus

router = APIRouter(prefix="/api", tags=["diagnostics"])


@router.get("/diagnostics", response_model=DiagnosticSnapshot)
async def diagnostics(request: Request) -> DiagnosticSnapshot:
    state = depth_bus.latest()
    return DiagnosticSnapshot(
        symbol=request.app.state.settings.symbol,
        liveTradeCount=trade_bus.live_count(),
        latestTrade=trade_bus.latest(),
        bestBid=state.bestBid if state else None,
        bestAsk=state.bestAsk if state else None,
        depthSynced=state.synced if state else False,
        depthLastUpdateId=state.lastUpdateId if state else None,
    )


@router.get("/recorder/status", response_model=RecorderStatus)
async def recorder_status(request: Request) -> RecorderStatus:
    return request.app.state.recorder.status()
