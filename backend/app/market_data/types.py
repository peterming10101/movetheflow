import asyncio
from typing import TypeVar


T = TypeVar("T")
SubscriberQueue = asyncio.Queue[T]
