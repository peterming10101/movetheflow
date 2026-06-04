from typing import Any
import httpx


class BinanceFuturesRestClient:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")

    async def depth_snapshot(self, symbol: str, limit: int = 1000) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{self.base_url}/fapi/v1/depth",
                params={"symbol": symbol.upper(), "limit": limit},
            )
            response.raise_for_status()
            return response.json()
