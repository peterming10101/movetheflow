from fastapi import APIRouter, Query
from ..derived.workspace_engine import build_workspace_snapshot
from ..schemas import WorkspaceSnapshot

router = APIRouter(prefix="/api", tags=["workspace"])


@router.get("/workspace", response_model=WorkspaceSnapshot)
async def workspace_snapshot(
    timeframe: int = Query(default=60, ge=1, le=3600),
    limit: int = Query(default=240, ge=20, le=1000),
    priceStep: float = Query(default=5.0, gt=0, le=1000),
) -> WorkspaceSnapshot:
    return await build_workspace_snapshot(timeframe_sec=timeframe, limit=limit, price_step=priceStep)
