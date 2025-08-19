from __future__ import annotations

import random
import asyncio
from typing import Awaitable, Callable


async def retry_with_jitter(fn: Callable[[], Awaitable[bool]], retries: int = 2) -> bool:
    for attempt in range(retries + 1):
        ok = await fn()
        if ok:
            return True
        await asyncio.sleep(0.4 + random.random() * 0.4)
    return False

