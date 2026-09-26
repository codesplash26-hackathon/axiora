import os
import asyncio
import functools
import multiprocessing
from concurrent.futures import Executor, ProcessPoolExecutor, ThreadPoolExecutor
from typing import Callable, Any, Optional

from backend.worker import warmup_worker, worker_ping

process_pool: Optional[Executor] = None


def get_worker_count() -> int:
    """Calculates safe physical worker allocation (minimum 1, maximum 4)."""
    cpu_count = multiprocessing.cpu_count()
    return max(1, min(cpu_count - 1, 4)) if cpu_count > 1 else 1


def init_pool():
    """
    Initialize worker executor pool.
    Defaults to ProcessPoolExecutor with spawn context for true multi-process isolation
    and complete elimination of Python's Global Interpreter Lock (GIL) contention.
    """
    global process_pool
    if process_pool is None:
        workers = get_worker_count()
        mode = os.getenv("EXECUTOR_MODE", "process").lower()
        if mode == "process":
            try:
                mp_ctx = multiprocessing.get_context("spawn")
                process_pool = ProcessPoolExecutor(
                    max_workers=workers,
                    mp_context=mp_ctx,
                    initializer=warmup_worker
                )
                # Warm-up ping to eagerly start worker processes
                list(process_pool.map(worker_ping, range(workers)))
            except Exception:
                # Resilient fallback to ThreadPoolExecutor if OS forbids spawn
                process_pool = ThreadPoolExecutor(max_workers=workers, initializer=warmup_worker)
                try:
                    list(process_pool.map(worker_ping, range(workers)))
                except Exception:
                    pass
        else:
            process_pool = ThreadPoolExecutor(max_workers=workers, initializer=warmup_worker)
            try:
                list(process_pool.map(worker_ping, range(workers)))
            except Exception:
                pass


def get_executor() -> Executor:
    """Returns or lazily creates the singleton executor pool."""
    global process_pool
    if process_pool is None:
        init_pool()
    return process_pool  # type: ignore


def shutdown_pool():
    """Gracefully shuts down worker processes on server termination."""
    global process_pool
    if process_pool is not None:
        process_pool.shutdown(wait=True)
        process_pool = None


def shutdown_executor():
    """Alias for shutdown_pool for backward compatibility."""
    shutdown_pool()


async def run_in_pool(func: Callable, *args, **kwargs) -> Any:
    """Execute function in worker pool asynchronously."""
    global process_pool
    if process_pool is None:
        init_pool()

    loop = asyncio.get_running_loop()
    if kwargs:
        func = functools.partial(func, **kwargs)

    return await loop.run_in_executor(process_pool, func, *args)

