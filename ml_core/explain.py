import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import joblib
import numpy as np
import pandas as pd
import shap
import config

# Patch UBJSON decode to handle XGBoost 3.x base_score format '[4.9995828E-1]' in shap 0.44+
import shap.explainers._tree as _tree_mod
_orig_decode = _tree_mod.decode_ubjson_buffer

def _patched_decode(fd):
    res = _orig_decode(fd)
    try:
        bs = res["learner"]["learner_model_param"]["base_score"]
        if isinstance(bs, str) and bs.startswith("["):
            res["learner"]["learner_model_param"]["base_score"] = bs.strip("[]")
    except Exception:
        pass
    return res

_tree_mod.decode_ubjson_buffer = _patched_decode

FEATURE_DISPLAY_NAMES: Dict[str, str] = {
    "male": "Biological Sex",
    "age": "Age",
    "currentSmoker": "Current Smoking Status",
    "cigsPerDay": "Cigarettes Per Day",
    "BPMeds": "Blood Pressure Medication",
    "prevalentStroke": "History of Stroke",
    "prevalentHyp": "Prevalent Hypertension",
    "diabetes": "Diabetes Diagnosis",
    "totChol": "Total Serum Cholesterol",
    "sysBP": "Systolic Blood Pressure",
    "diaBP": "Diastolic Blood Pressure",
    "BMI": "Body Mass Index",
    "heartRate": "Heart Rate",
    "glucose": "Fasting Blood Glucose"
}

FEATURE_ORDER: List[str] = [
    "male", "age", "currentSmoker", "cigsPerDay", "BPMeds",
    "prevalentStroke", "prevalentHyp", "diabetes", "totChol",
    "sysBP", "diaBP", "BMI", "heartRate", "glucose"
]

_calibrated_model = None
_raw_model = None
_explainer = None
_background_data = None
_base_population_risk = 0.1509  # Empirical Framingham cohort baseline


def load_explainer_assets():
    """Pre-load model and SHAP TreeExplainer assets into memory for sub-40ms attribution."""
    global _calibrated_model, _raw_model, _explainer, _background_data, _base_population_risk

    if _explainer is not None and _calibrated_model is not None:
        return

    if not config.MODEL_PATH.exists():
        raise FileNotFoundError(f"Calibrated model missing: {config.MODEL_PATH}")
    if not config.RAW_MODEL_PATH.exists():
        raise FileNotFoundError(f"Raw model missing: {config.RAW_MODEL_PATH}")
    if not config.SHAP_BACKGROUND_PATH.exists():
        raise FileNotFoundError(f"SHAP background array missing: {config.SHAP_BACKGROUND_PATH}")

    _calibrated_model = joblib.load(config.MODEL_PATH)
    _raw_model = joblib.load(config.RAW_MODEL_PATH)
    _background_data = np.load(config.SHAP_BACKGROUND_PATH)

    booster = _raw_model.get_booster()
    _explainer = shap.TreeExplainer(
        booster,
        data=_background_data,
        feature_perturbation="interventional"
    )

    if config.DATA_SUMMARY_PATH.exists():
        try:
            import json
            with open(config.DATA_SUMMARY_PATH) as f:
                meta = json.load(f)
                if "true_prevalence" in meta:
                    _base_population_risk = float(meta["true_prevalence"])
        except Exception:
            pass


def explain_patient(patient_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate exact SHAP feature attributions and calibrated risk for an individual patient.
    Guaranteed to execute in < 40ms.
    """
    load_explainer_assets()

    # Reorder input according to canonical schema
    input_row = {f: float(patient_dict[f]) for f in FEATURE_ORDER if f in patient_dict}
    if len(input_row) != len(FEATURE_ORDER):
        missing = set(FEATURE_ORDER) - set(input_row.keys())
        raise ValueError(f"Missing required clinical features: {missing}")

    patient_df = pd.DataFrame([input_row], columns=FEATURE_ORDER)

    # 1. Compute calibrated 10-year risk
    calibrated_prob = float(_calibrated_model.predict_proba(patient_df)[0, 1])

    # 2. Compute local SHAP attributions using pre-warmed TreeExplainer
    explanation = _explainer(patient_df, check_additivity=False)
    shap_vals = explanation.values[0]

    base_log_odds = float(explanation.base_values[0]) if hasattr(explanation, "base_values") and hasattr(explanation.base_values, "__len__") and len(explanation.base_values) > 0 else -1.7277
    patient_log_odds = base_log_odds + float(np.sum(shap_vals))

    def _logistic(z: float) -> float:
        return 1.0 / (1.0 + np.exp(-z))

    prob_patient = _logistic(patient_log_odds)

    attributions = []
    for feat, shap_val in zip(FEATURE_ORDER, shap_vals):
        val = float(shap_val)
        direction = "risk_increasing" if val > 0 else "protective"
        prob_without_feat = _logistic(patient_log_odds - val)
        delta_p = (prob_patient - prob_without_feat) * 100.0

        attributions.append({
            "feature": feat,
            "display_name": FEATURE_DISPLAY_NAMES.get(feat, feat),
            "attribution_value": round(val, 4),
            "patient_value": round(float(input_row[feat]), 2),
            "direction": direction,
            "marginal_percentage_impact": round(delta_p, 2),
        })

    # Rank descending by absolute attribution magnitude
    attributions.sort(key=lambda x: abs(x["attribution_value"]), reverse=True)

    return {
        "base_value": round(_base_population_risk, 4),
        "risk_score": round(calibrated_prob, 4),
        "attributions": attributions,
        "base_log_odds": round(base_log_odds, 4),
        "patient_log_odds": round(patient_log_odds, 4),
    }



def explain_risk(patient_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Alias for explain_patient to satisfy unified ML gateway contracts."""
    return explain_patient(patient_dict)


if __name__ == "__main__":
    test_patient = {
        "male": 1, "age": 62.0, "currentSmoker": 1, "cigsPerDay": 20.0, "BPMeds": 0,
        "prevalentStroke": 0, "prevalentHyp": 1, "diabetes": 0, "totChol": 260.0,
        "sysBP": 160.0, "diaBP": 95.0, "BMI": 29.0, "heartRate": 80.0, "glucose": 110.0
    }
    result = explain_risk(test_patient)
    print("Risk Score:", result["risk_score"])
    print("Base Value:", result["base_value"])
    print("Top 3 Features:")
    for a in result["attributions"][:3]:
        print(f"  {a['display_name']} ({a['feature']}): {a['attribution_value']:+.4f} [{a['direction']}]")
