import asyncio
import functools
from concurrent.futures import ProcessPoolExecutor
from typing import Callable, Any

from backend.worker import warmup_worker

process_pool: ProcessPoolExecutor = None  # type: ignore

def init_pool():
    global process_pool
    process_pool = ProcessPoolExecutor(max_workers=4, initializer=warmup_worker)


def shutdown_pool():
    global process_pool
    if process_pool is not None:
        process_pool.shutdown(wait=True)

async def run_in_pool(func: Callable, *args, **kwargs) -> Any:
    global process_pool
    if process_pool is None:
        raise RuntimeError("Process pool is not initialized")
    
    loop = asyncio.get_running_loop()
    if kwargs:
        func = functools.partial(func, **kwargs)
    
    return await loop.run_in_executor(process_pool, func, *args)
