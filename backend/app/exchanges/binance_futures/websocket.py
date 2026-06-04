import asyncio
import json
from collections.abc import Awaitable, Callable
from typing import Any
import websockets


PayloadHandler = Callable[[dict[str, Any]], Awaitable[None]]


class BinanceWebSocketFeed:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")

    async def consume(self, stream: str, handler: PayloadHandler, stop: asyncio.Event) -> None:
        url = f"{self.base_url}/{stream}"
        while not stop.is_set():
            try:
                async with websockets.connect(url, ping_interval=20, ping_timeout=20) as ws:
                    async for message in ws:
                        if stop.is_set():
                            break
                        await handler(json.loads(message))
            except asyncio.CancelledError:
                raise
            except Exception:
                await asyncio.sleep(2)
