import joblib
import pandas as pd
from typing import Dict, Any, Optional
import config

# Process-level model cache (persists within each isolated worker process)
_MODEL: Optional[Any] = None

CANONICAL_COLUMNS = [
    "male",
    "age",
    "currentSmoker",
    "cigsPerDay",
    "BPMeds",
    "prevalentStroke",
    "prevalentHyp",
    "diabetes",
    "totChol",
    "sysBP",
    "diaBP",
    "BMI",
    "heartRate",
    "glucose",
]


def get_model():
    """Lazily loads and caches the calibrated model inside the child worker process."""
    global _MODEL
    if _MODEL is None:
        if not config.MODEL_PATH.exists():
            raise FileNotFoundError(f"Model artifact not found at: {config.MODEL_PATH.resolve()}")
        _MODEL = joblib.load(config.MODEL_PATH)
    return _MODEL


def determine_triage_band(risk_score: float) -> str:
    """
    Standard ACC/AHA clinical 10-year cardiovascular risk stratification:
    - < 10%: Low Risk
    - 10% - 20%: Moderate Risk
    - >= 20%: High Risk
    """
    if risk_score < 0.10:
        return "Low"
    elif risk_score < 0.20:
        return "Moderate"
    else:
        return "High"


def predict_worker(patient_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Synchronous worker routine dispatched to ProcessPoolExecutor.
    1. Loads or reuses cached calibrated model.
    2. Maps patient dict to the aligned 14-biomarker feature vector.
    3. Computes calibrated probability and assigns the clinical triage band.
    """
    model = get_model()

    # Align input to exact canonical column ordering
    row_values = [patient_dict[col] for col in CANONICAL_COLUMNS]
    input_df = pd.DataFrame([row_values], columns=CANONICAL_COLUMNS)

    # Compute calibrated probability of TenYearCHD (Class 1)
    probabilities = model.predict_proba(input_df)
    risk_score = round(float(probabilities[0, 1]), 4)
    triage_band = determine_triage_band(risk_score)

    return {
        "risk_score": risk_score,
        "triage_band": triage_band,
        "calibrated": True,
        "model_version": "1.0.0",
    }
