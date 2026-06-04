from fastapi import APIRouter
from ..metrics import metrics
from ..schemas import MarketDataMetrics

router = APIRouter(prefix="/api/metrics", tags=["metrics"])


@router.get("/market-data", response_model=MarketDataMetrics)
async def market_data_metrics() -> MarketDataMetrics:
    return metrics.snapshot()
