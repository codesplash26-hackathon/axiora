import os
import asyncio
from backend.pool import get_executor, get_worker_count


def _worker_env_check():
    return {
        "OMP": os.environ.get("OMP_NUM_THREADS"),
        "MKL": os.environ.get("MKL_NUM_THREADS"),
        "OPENBLAS": os.environ.get("OPENBLAS_NUM_THREADS"),
    }


def _cpu_workload(n: int) -> int:
    return sum(i * i for i in range(n))


def test_worker_count_allocation():
    count = get_worker_count()
    assert 1 <= count <= 4


def test_worker_blas_pinning():
    pool = get_executor()
    future = pool.submit(_worker_env_check)
    env_vars = future.result(timeout=5)
    assert env_vars["OMP"] == "1"
    assert env_vars["MKL"] == "1"
    assert env_vars["OPENBLAS"] == "1"


def test_async_event_loop_offloading():
    async def run_offloaded_task():
        loop = asyncio.get_running_loop()
        pool = get_executor()
        res = await loop.run_in_executor(pool, _cpu_workload, 5000)
        return res

    result = asyncio.run(run_offloaded_task())
    assert result == 41654167500
