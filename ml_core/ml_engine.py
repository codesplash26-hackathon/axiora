import sys
import time
import json
import warnings
from pathlib import Path
from typing import Dict, Any, List, Optional, Union

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import joblib
import numpy as np
import pandas as pd
import config

from ml_core.explain import explain_patient, load_explainer_assets, FEATURE_DISPLAY_NAMES
from ml_core.dice_setup import (
    load_schema,
    get_actionable_features,
    get_permitted_range,
    SafeModelWrapper,
    CANONICAL_FEATURES
)
from ml_core.dice_fallback_solver import (
    init_fallback_solver,
    search_recourse_with_fallback
)

# Suppress pandas setting item incompatible dtype warnings from DiCE
warnings.filterwarnings("ignore", category=FutureWarning)

_model = None
_schema = None
_boundaries = None
_feature_types = None
_engine_initialized = False


def _get_risk_category(probability: float) -> str:
    """Categorize calibrated 10-year CVD risk score according to clinical practice."""
    if probability < 0.10:
        return "Low"
    elif probability < 0.20:
        return "Borderline"
    else:
        return "High"


def validate_patient_dict(patient_dict: Any) -> pd.DataFrame:
    """
    Validate input payload against the canonical 14-feature clinical schema.
    Rejects malformed, incomplete, or physiologically invalid dictionaries.
    """
    if not isinstance(patient_dict, dict):
        raise ValueError(f"Patient input must be a dictionary, received {type(patient_dict).__name__}")

    missing_fields = [f for f in CANONICAL_FEATURES if f not in patient_dict]
    if missing_fields:
        raise ValueError(f"Payload validation failed. Missing required biomarkers: {missing_fields}")

    schema = load_schema()
    types_map = schema.get("feature_types", {})
    cleaned_row = {}

    for f in CANONICAL_FEATURES:
        raw_val = patient_dict[f]
        if raw_val is None:
            raise ValueError(f"Feature '{f}' cannot be None.")

        try:
            val_float = float(raw_val)
        except (ValueError, TypeError):
            raise ValueError(f"Feature '{f}' must be numeric, received '{raw_val}'")

        if np.isnan(val_float) or np.isinf(val_float):
            raise ValueError(f"Feature '{f}' contains NaN or infinite value.")

        f_type = types_map.get(f, "continuous")
        if f_type == "binary":
            int_val = int(val_float)
            if int_val not in (0, 1):
                raise ValueError(f"Binary feature '{f}' must be 0 or 1, received {val_float}")
            cleaned_row[f] = int_val
        else:
            if val_float <= 0 and f in ("age", "sysBP", "diaBP", "BMI", "heartRate", "glucose", "totChol"):
                raise ValueError(f"Physiological feature '{f}' must be positive, received {val_float}")
            cleaned_row[f] = val_float

    return pd.DataFrame([cleaned_row], columns=CANONICAL_FEATURES)


def initialize_engine():
    """
    Pre-warm and cache models, explainers, and schemas in memory
    to eliminate cold-start latencies.
    """
    global _model, _schema, _boundaries, _feature_types, _engine_initialized

    if _engine_initialized:
        return

    if not config.MODEL_PATH.exists():
        raise FileNotFoundError(f"Calibrated model artifact missing: {config.MODEL_PATH}")

    _model = joblib.load(config.MODEL_PATH)
    _schema = load_schema()
    _boundaries = _schema.get("actionable_boundaries", {})
    _feature_types = _schema.get("feature_types", {})

    load_explainer_assets()
    init_fallback_solver()

    # Pre-warm inference pipeline with a benchmark patient
    benchmark_df = pd.DataFrame([{
        "male": 1, "age": 55.0, "currentSmoker": 1, "cigsPerDay": 20.0, "BPMeds": 0,
        "prevalentStroke": 0, "prevalentHyp": 0, "diabetes": 0, "totChol": 220.0,
        "sysBP": 140.0, "diaBP": 90.0, "BMI": 27.0, "heartRate": 75.0, "glucose": 95.0
    }], columns=CANONICAL_FEATURES)
    _ = _model.predict_proba(benchmark_df)

    _engine_initialized = True


def predict_risk(patient_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate calibrated 10-year cardiovascular risk probability and categorical tier.
    Guaranteed SLA: < 5ms execution.
    """
    initialize_engine()
    df = validate_patient_dict(patient_dict)

    prob = float(_model.predict_proba(df)[0, 1])
    risk_category = _get_risk_category(prob)

    return {
        "risk_probability": round(prob, 4),
        "risk_category": risk_category,
        "calibrated_percentage": round(prob * 100, 2),
        "is_high_risk": bool(prob >= 0.20)
    }


def explain_risk(patient_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compute local SHAP feature attributions and population baseline risk.
    Guaranteed SLA: < 40ms execution.
    """
    initialize_engine()
    _ = validate_patient_dict(patient_dict)
    return explain_patient(patient_dict)


def generate_recourse(
    patient_dict: Dict[str, Any],
    total_pathways: int = 3,
    genetic_maxiterations: Optional[int] = None
) -> Dict[str, Any]:
    """
    Generate 2-3 structured counterfactual recourse pathways with baseline-versus-target deltas.
    Guaranteed SLA: < 950ms execution (with sub-150ms fallback engine).
    """
    initialize_engine()
    query_df = validate_patient_dict(patient_dict)

    # 1. Baseline risk assessment
    baseline_prob = float(_model.predict_proba(query_df)[0, 1])
    baseline_cat = _get_risk_category(baseline_prob)
    baseline_row = query_df.iloc[0].to_dict()

    # 2. Counterfactual optimization with automated fallback
    recourse_raw = search_recourse_with_fallback(
        query_instance=query_df,
        total_CFs=total_pathways,
        desired_class=0,
        max_timer_ms=950.0,
        genetic_maxiterations=genetic_maxiterations
    )

    cfs_df = recourse_raw["counterfactuals"]
    actionable_feats = get_actionable_features()
    pathways = []

    if cfs_df is not None and not cfs_df.empty:
        # Re-predict calibrated probabilities for each counterfactual profile
        cf_features_df = cfs_df[CANONICAL_FEATURES].copy()
        cf_probs = _model.predict_proba(cf_features_df)[:, 1]

        for i in range(len(cfs_df)):
            cf_row = cfs_df.iloc[i].to_dict()
            target_prob = float(cf_probs[i])
            target_cat = _get_risk_category(target_prob)
            risk_reduction = max(0.0, baseline_prob - target_prob)

            deltas = []
            for feat in actionable_feats:
                base_v = float(baseline_row[feat])
                target_v = float(cf_row[feat])
                delta_v = target_v - base_v

                if abs(delta_v) > 1e-4:
                    b_info = _boundaries.get(feat, {})
                    f_type = _feature_types.get(feat, "continuous")
                    direction = "decrease" if delta_v < 0 else "increase"

                    deltas.append({
                        "feature": feat,
                        "display_name": FEATURE_DISPLAY_NAMES.get(feat, feat),
                        "current_value": int(base_v) if f_type == "binary" else round(base_v, 1),
                        "target_value": int(target_v) if f_type == "binary" else round(target_v, 1),
                        "delta": int(delta_v) if f_type == "binary" else round(delta_v, 1),
                        "unit": b_info.get("unit", ""),
                        "direction": direction,
                        "description": b_info.get("description", "")
                    })

            # Sort deltas by clinical priority (BP and Smoking first, then Lipids, then BMI/Glucose)
            priority_order = {"sysBP": 1, "diaBP": 2, "cigsPerDay": 3, "currentSmoker": 4, "totChol": 5, "BMI": 6, "glucose": 7, "BPMeds": 8, "heartRate": 9}
            deltas.sort(key=lambda d: priority_order.get(d["feature"], 99))

            pathways.append({
                "pathway_id": i + 1,
                "name": f"Pathway {i + 1}",
                "projected_risk": round(target_prob, 4),
                "projected_category": target_cat,
                "risk_reduction": round(risk_reduction, 4),
                "risk_reduction_percentage": round(risk_reduction * 100, 2),
                "deltas_count": len(deltas),
                "deltas": deltas,
                "target_biomarkers": {k: cf_row[k] for k in CANONICAL_FEATURES}
            })

    # Sort pathways by lowest projected risk
    pathways.sort(key=lambda p: p["projected_risk"])
    for idx, p in enumerate(pathways):
        p["pathway_id"] = idx + 1
        p["name"] = f"Pathway {idx + 1}"

    return {
        "current_risk": round(baseline_prob, 4),
        "current_category": baseline_cat,
        "pathways_count": len(pathways),
        "pathways": pathways,
        "method_used": recourse_raw["method_used"],
        "fallback_triggered": recourse_raw["fallback_triggered"],
        "fallback_reason": recourse_raw.get("fallback_reason"),
        "execution_time_ms": recourse_raw["execution_time_ms"]
    }


# Auto-initialize on import
initialize_engine()


if __name__ == "__main__":
    patient = {
        "male": 1, "age": 62.0, "currentSmoker": 1, "cigsPerDay": 20.0, "BPMeds": 0,
        "prevalentStroke": 0, "prevalentHyp": 1, "diabetes": 0, "totChol": 260.0,
        "sysBP": 160.0, "diaBP": 95.0, "BMI": 29.0, "heartRate": 80.0, "glucose": 110.0
    }
    print("--- 1. Predict Risk ---")
    pred = predict_risk(patient)
    print("Prediction:", pred)

    print("\n--- 2. Explain Risk ---")
    exp = explain_risk(patient)
    print(f"Base: {exp['base_value']}, Risk: {exp['risk_score']}")
    print("Top feature:", exp["attributions"][0])

    print("\n--- 3. Generate Recourse ---")
    rec = generate_recourse(patient)
    print(f"Recourse found {rec['pathways_count']} pathways via {rec['method_used']} in {rec['execution_time_ms']}ms")
    if rec["pathways"]:
        print("First pathway deltas:")
        for d in rec["pathways"][0]["deltas"]:
            print(f"  {d['display_name']}: {d['current_value']} -> {d['target_value']} ({d['delta']:+} {d['unit']})")
