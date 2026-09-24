"""
Root-level gateway for DiCE fallback solver module.
Exposes all components from ml_core.dice_fallback_solver.
"""
from ml_core.dice_fallback_solver import (
    init_fallback_solver,
    search_recourse_with_fallback,
    _vectorized_random_solver,
    _run_genetic_search
)

if __name__ == "__main__":
    sample_patient = {
        "male": 1, "age": 62.0, "currentSmoker": 1, "cigsPerDay": 20.0, "BPMeds": 0,
        "prevalentStroke": 0, "prevalentHyp": 1, "diabetes": 0, "totChol": 260.0,
        "sysBP": 160.0, "diaBP": 95.0, "BMI": 29.0, "heartRate": 80.0, "glucose": 110.0
    }
    res = search_recourse_with_fallback(sample_patient, total_CFs=3, genetic_maxiterations=1)
    print("Stress test result:", res["method_used"], f"{res['execution_time_ms']}ms", "Fallback:", res["fallback_triggered"])
