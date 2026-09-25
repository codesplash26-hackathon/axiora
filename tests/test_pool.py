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


def test_recourse_worker_fallback_preserves_actual_risk():
    """
    Verifies that when recourse generation encounters an error, the fallback
    does NOT return a hardcoded 0.428 risk, but instead computes genuine patient baseline risk.
    """
    from unittest.mock import patch
    from backend.worker import recourse_worker

    sample_patient = {
        "male": 1, "age": 40.0, "currentSmoker": 0, "cigsPerDay": 0.0, "BPMeds": 0,
        "prevalentStroke": 0, "prevalentHyp": 0, "diabetes": 0, "totChol": 180.0,
        "sysBP": 120.0, "diaBP": 80.0, "BMI": 23.0, "heartRate": 70.0, "glucose": 85.0
    }

    with patch("ml_engine.generate_recourse", side_effect=RuntimeError("Simulated recourse failure")):
        result = recourse_worker(sample_patient)
        assert result["is_fallback"] is True
        assert result["pathways"] == []
        # The baseline risk must be calculated dynamically, not hardcoded 0.428
        assert result["patient_baseline_risk"] != 0.428
        assert 0.0 <= result["patient_baseline_risk"] <= 1.0
