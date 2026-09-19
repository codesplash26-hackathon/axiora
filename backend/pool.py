import os
import multiprocessing
from concurrent.futures import ProcessPoolExecutor
from typing import Optional

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
