from dataclasses import dataclass, field
from threading import Lock
from .schemas import MarketDataMetrics


@dataclass
class MetricsRegistry:
    _lock: Lock = field(default_factory=Lock)
    _values: MarketDataMetrics = field(default_factory=MarketDataMetrics)

    def increment(self, name: str, amount: int = 1) -> None:
        with self._lock:
            setattr(self._values, name, getattr(self._values, name) + amount)

    def set(self, name: str, value: int | float | str) -> None:
        with self._lock:
            setattr(self._values, name, value)

    def snapshot(self) -> MarketDataMetrics:
        with self._lock:
            return self._values.model_copy()


metrics = MetricsRegistry()
