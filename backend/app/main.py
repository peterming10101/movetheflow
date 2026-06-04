import asyncio
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.diagnostics import router as diagnostics_router
from .api.metrics import router as metrics_router
from .config import get_settings
from .depth.depth_manager import DepthManager
from .exchanges.binance_futures.normalizers import normalize_aggregate_trade
from .exchanges.binance_futures.rest import BinanceFuturesRestClient
from .exchanges.binance_futures.websocket import BinanceWebSocketFeed
from .market_data.depth_bus import depth_bus
from .market_data.recorder import SQLiteRecorder
from .market_data.trade_bus import trade_bus
from .metrics import metrics


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    stop = asyncio.Event()
    recorder = SQLiteRecorder(settings.database_path)
    depth_manager = DepthManager(settings.symbol, settings.venue)
    rest = BinanceFuturesRestClient(settings.binance_rest_base_url)
    feed = BinanceWebSocketFeed(settings.binance_ws_base_url)
    tasks: list[asyncio.Task] = []

    app.state.settings = settings
    app.state.recorder = recorder

    if os.environ.get("MOVETHEFLOW_DISABLE_LIVE") == "1":
        recorder.initialize()
        yield
        return

    depth_queue: asyncio.Queue[dict] = asyncio.Queue(maxsize=20_000)

    async def trade_handler(payload: dict) -> None:
        metrics.increment("trade_ws_messages_received")
        trade = normalize_aggregate_trade(payload, settings.venue, settings.symbol)
        metrics.increment("trade_messages_normalized")
        published = await trade_bus.publish(trade)
        if published:
            await recorder.enqueue(trade)

    async def depth_handler(payload: dict) -> None:
        await depth_queue.put(payload)

    async def start_depth() -> None:
        feed_task = asyncio.create_task(
            feed.consume(f"{settings.symbol.lower()}@depth@100ms", depth_handler, stop)
        )
        try:
            await refresh_depth_snapshot(rest, depth_manager)
            while not stop.is_set():
                payload = await depth_queue.get()
                metrics.increment("depth_ws_messages_received")
                state = depth_manager.apply_diff(payload)
                await depth_bus.publish(state)
                if not state.synced:
                    await refresh_depth_snapshot(rest, depth_manager)
        finally:
            feed_task.cancel()

    async def refresh_depth_snapshot(rest_client: BinanceFuturesRestClient, manager: DepthManager) -> None:
        while not stop.is_set():
            try:
                snapshot = await rest_client.depth_snapshot(settings.symbol, settings.depth_snapshot_limit)
                await depth_bus.publish(manager.apply_snapshot(snapshot))
                return
            except Exception:
                metrics.set("depth_status", "snapshot_retry")
                await asyncio.sleep(1)

    tasks.append(asyncio.create_task(recorder.run(stop)))
    tasks.append(asyncio.create_task(feed.consume(f"{settings.symbol.lower()}@trade", trade_handler, stop)))
    tasks.append(asyncio.create_task(start_depth()))
    try:
        yield
    finally:
        stop.set()
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)


app = FastAPI(title="Movetheflow Market Data", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(diagnostics_router)
app.include_router(metrics_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
