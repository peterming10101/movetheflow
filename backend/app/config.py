from functools import lru_cache
from pathlib import Path
from pydantic import BaseModel


class Settings(BaseModel):
    symbol: str = "BTCUSDT"
    venue: str = "binance_usdm"
    binance_rest_base_url: str = "https://fapi.binance.com"
    binance_ws_base_url: str = "wss://fstream.binance.com/ws"
    data_dir: Path = Path("data")
    ui_depth_levels: int = 20
    depth_snapshot_limit: int = 1000

    @property
    def database_path(self) -> Path:
        return self.data_dir / "market_data.db"


@lru_cache
def get_settings() -> Settings:
    return Settings()
