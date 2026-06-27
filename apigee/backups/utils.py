import asyncio
from .config import get_global_semaphore


async def run_blocking(fn, *args, semaphore=None, **kwargs):
    # prefer explicit semaphore
    sem = semaphore or get_global_semaphore()

    if sem:
        async with sem:
            return await asyncio.to_thread(fn, *args, **kwargs)

    return await asyncio.to_thread(fn, *args, **kwargs)
