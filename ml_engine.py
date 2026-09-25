"""
CardioRecourse Unified Machine Learning & Recourse Gateway (Task A9)
Single production entry point invoking calibrated inference, SHAP explanations,
and DiCE counterfactual recourse with sub-150ms fallback.
"""
from ml_core.ml_engine import (
    predict_risk,
    explain_risk,
    generate_recourse,
    validate_patient_dict,
    initialize_engine,
    CANONICAL_FEATURES
)

__all__ = [
    "predict_risk",
    "explain_risk",
    "generate_recourse",
    "validate_patient_dict",
    "initialize_engine",
    "CANONICAL_FEATURES"
]

if __name__ == "__main__":
    test_patient = {
        "male": 1, "age": 62.0, "currentSmoker": 1, "cigsPerDay": 20.0, "BPMeds": 0,
        "prevalentStroke": 0, "prevalentHyp": 1, "diabetes": 0, "totChol": 260.0,
        "sysBP": 160.0, "diaBP": 95.0, "BMI": 29.0, "heartRate": 80.0, "glucose": 110.0
    }
    print("Testing root ml_engine gateway...")
    p = predict_risk(test_patient)
    print("Prediction:", p)
    e = explain_risk(test_patient)
    print("Explanation Top:", e["attributions"][0])
    r = generate_recourse(test_patient)
    print("Recourse Pathways:", r["pathways_count"], f"in {r['execution_time_ms']}ms")
