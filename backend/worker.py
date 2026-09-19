import joblib
import pandas as pd
from typing import Dict, Any, Optional
import config

# Process-level model cache (persists within each child worker process)
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


def determine_risk_band(risk_score: float) -> str:
    """
    Categorizes risk according to ACC/AHA guidelines:
    - < 10%: Low
    - 10% - 20%: Borderline
    - >= 20%: High
    """
    if risk_score < 0.10:
        return "Low"
    elif risk_score < 0.20:
        return "Borderline"
    else:
        return "High"


def predict_worker(patient_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Synchronous worker routine executed within ProcessPoolExecutor.
    1. Loads or reuses cached calibrated model.
    2. Maps incoming patient dict to canonical 14-feature order.
    3. Computes calibrated probability and formats the PredictionResponse payload.
    """
    model = get_model()

    # Align input to canonical column ordering
    row_values = [patient_dict[col] for col in CANONICAL_COLUMNS]
    input_df = pd.DataFrame([row_values], columns=CANONICAL_COLUMNS)

    # Compute calibrated probability of TenYearCHD (Class 1)
    probabilities = model.predict_proba(input_df)
    risk_score = round(float(probabilities[0, 1]), 4)
    risk_percentage = round(risk_score * 100.0, 2)
    risk_band = determine_risk_band(risk_score)
    requires_recourse = bool(risk_score >= 0.20)

    return {
        "risk_score": risk_score,
        "risk_percentage": risk_percentage,
        "risk_band": risk_band,
        "requires_recourse": requires_recourse,
    }
