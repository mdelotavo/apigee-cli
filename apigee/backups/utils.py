import asyncio


async def run_blocking(fn, *args, **kwargs):
    return await asyncio.to_thread(fn, *args, **kwargs)
