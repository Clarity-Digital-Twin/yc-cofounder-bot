from __future__ import annotations

import asyncio
import random
from collections.abc import Awaitable, Callable


async def retry_with_jitter(fn: Callable[[], Awaitable[bool]], retries: int = 2) -> bool:
    for _attempt in range(retries + 1):
        ok = await fn()
        if ok:
            return True
        await asyncio.sleep(0.4 + random.random() * 0.4)
    return False
