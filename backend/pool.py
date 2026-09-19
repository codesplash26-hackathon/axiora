import os
import asyncio
import multiprocessing
from concurrent.futures import ProcessPoolExecutor
from typing import Optional, Any, Callable
from functools import partial

# Global pool instance
_POOL: Optional[ProcessPoolExecutor] = None


def _init_worker():
    """
    Worker process initializer.
    Restricts low-level linear algebra libraries to a single thread per worker
    to avoid CPU core oversubscription and thrashing.
    """
    os.environ["OMP_NUM_THREADS"] = "1"
    os.environ["MKL_NUM_THREADS"] = "1"
    os.environ["OPENBLAS_NUM_THREADS"] = "1"
    os.environ["NUMEXPR_NUM_THREADS"] = "1"


def get_worker_count() -> int:
    """Calculates safe physical worker allocation (minimum 1, maximum 4)."""
    cpu_count = multiprocessing.cpu_count()
    return max(1, min(cpu_count - 1, 4)) if cpu_count > 1 else 1


def get_executor() -> ProcessPoolExecutor:
    """Returns or lazily creates the singleton process pool."""
    global _POOL
    if _POOL is None:
        workers = get_worker_count()
        _POOL = ProcessPoolExecutor(
            max_workers=workers,
            initializer=_init_worker,
        )
    return _POOL


def shutdown_executor():
    """Gracefully shuts down worker processes on server termination."""
    global _POOL
    if _POOL is not None:
        _POOL.shutdown(wait=True)
        _POOL = None


async def run_in_pool(func: Callable, *args: Any, **kwargs: Any) -> Any:
    """
    Asynchronously delegates CPU-bound tasks to the ProcessPoolExecutor
    without blocking the FastAPI asyncio event loop.
    """
    loop = asyncio.get_running_loop()
    executor = get_executor()
    if kwargs:
        target = partial(func, *args, **kwargs)
        return await loop.run_in_executor(executor, target)
    return await loop.run_in_executor(executor, func, *args)


async def warmup_pool(warmup_fn: Callable, sample_payload: Any):
    """
    Pre-warms all workers in the pool by executing a dummy inference task.
    Forces cold process spawning and unpickling during server startup.
    """
    workers = get_worker_count()
    tasks = [run_in_pool(warmup_fn, sample_payload) for _ in range(workers)]
    await asyncio.gather(*tasks, return_exceptions=True)
