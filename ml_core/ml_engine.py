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
    set_active_patient_context,
    set_model_recourse_threshold,
    SafeModelWrapper,
    CANONICAL_FEATURES
)
from ml_core.dice_fallback_solver import (
    init_fallback_solver,
    search_recourse_with_fallback
)

warnings.filterwarnings("ignore", category=FutureWarning)

_model = None
_schema = None
_boundaries = None
_feature_types = None
_engine_initialized = False


def _get_risk_category(probability: float) -> str:
    if probability < 0.10:
        return "Low"
    elif probability < 0.20:
        return "Borderline"
    else:
        return "High"


def validate_patient_dict(patient_dict: Any) -> pd.DataFrame:
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

    benchmark_df = pd.DataFrame([{
        "male": 1, "age": 55.0, "currentSmoker": 1, "cigsPerDay": 20.0, "BPMeds": 0,
        "prevalentStroke": 0, "prevalentHyp": 0, "diabetes": 0, "totChol": 220.0,
        "sysBP": 140.0, "diaBP": 90.0, "BMI": 27.0, "heartRate": 75.0, "glucose": 95.0
    }], columns=CANONICAL_FEATURES)
    _ = _model.predict_proba(benchmark_df)

    _engine_initialized = True


def predict_risk(patient_dict: Dict[str, Any]) -> Dict[str, Any]:
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
    initialize_engine()
    _ = validate_patient_dict(patient_dict)
    return explain_patient(patient_dict)


def _generate_clinical_fallback_candidates(baseline_row: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Generates guaranteed clinical improvement candidates if DiCE yields non-compliant pathways."""
    candidates = []

    # Pathway A: Blood Pressure & Smoking Cessation
    pA = baseline_row.copy()
    pA["cigsPerDay"] = 0.0
    pA["currentSmoker"] = 0
    pA["sysBP"] = max(118.0, round(float(baseline_row["sysBP"]) - 14.0, 1))
    pA["diaBP"] = max(76.0, round(float(baseline_row["diaBP"]) - 6.0, 1))
    if float(baseline_row["sysBP"]) >= 140.0:
        pA["BPMeds"] = 1
    candidates.append(pA)

    # Pathway B: Lipid & Metabolic Lifestyle Control
    pB = baseline_row.copy()
    pB["totChol"] = max(170.0, round(float(baseline_row["totChol"]) - 30.0, 1))
    pB["BMI"] = max(22.0, round(float(baseline_row["BMI"]) - 1.8, 1))
    pB["glucose"] = max(82.0, round(float(baseline_row["glucose"]) - 6.0, 1))
    pB["cigsPerDay"] = max(0.0, round(float(baseline_row["cigsPerDay"]) / 2.0, 1))
    if pB["cigsPerDay"] == 0.0:
        pB["currentSmoker"] = 0
    candidates.append(pB)

    # Pathway C: Comprehensive Optimal Recourse
    pC = baseline_row.copy()
    pC["cigsPerDay"] = 0.0
    pC["currentSmoker"] = 0
    pC["sysBP"] = max(115.0, round(min(float(baseline_row["sysBP"]) - 18.0, 125.0), 1))
    pC["diaBP"] = max(75.0, round(min(float(baseline_row["diaBP"]) - 8.0, 80.0), 1))
    pC["totChol"] = max(175.0, round(min(float(baseline_row["totChol"]) - 35.0, 200.0), 1))
    pC["BMI"] = max(23.0, round(float(baseline_row["BMI"]) - 2.2, 1))
    candidates.append(pC)

    return candidates


def generate_recourse(
    patient_dict: Dict[str, Any],
    total_pathways: int = 3,
    genetic_maxiterations: Optional[int] = None
) -> Dict[str, Any]:
    initialize_engine()
    query_df = validate_patient_dict(patient_dict)

    baseline_prob = float(_model.predict_proba(query_df)[0, 1])
    baseline_cat = _get_risk_category(baseline_prob)
    baseline_row = query_df.iloc[0].to_dict()

    # Set patient context and recourse decision threshold
    set_active_patient_context(patient_dict)
    set_model_recourse_threshold(baseline_prob)

    try:
        recourse_raw = search_recourse_with_fallback(
            query_instance=query_df,
            total_CFs=total_pathways,
            desired_class=0,
            max_timer_ms=950.0,
            genetic_maxiterations=genetic_maxiterations
        )
    finally:
        set_active_patient_context(None)

    cfs_df = recourse_raw.get("counterfactuals")
    actionable_feats = get_actionable_features()
    unidirectional_feats = ["sysBP", "diaBP", "totChol", "BMI", "glucose", "cigsPerDay"]

    valid_candidates: List[Dict[str, Any]] = []

    # 1. Process and sanitize raw counterfactual rows
    if cfs_df is not None and not cfs_df.empty:
        for idx in range(len(cfs_df)):
            row = cfs_df.iloc[idx].to_dict()

            # Strictly enforce directional bounds: values can NEVER increase
            for feat in unidirectional_feats:
                if feat in row:
                    row[feat] = min(float(row[feat]), float(baseline_row[feat]))

            # Strictly enforce smoking coherence
            if row.get("cigsPerDay", 0.0) <= 0.0:
                row["currentSmoker"] = 0
                row["cigsPerDay"] = 0.0
            if row.get("currentSmoker", 0) == 0:
                row["cigsPerDay"] = 0.0

            # Predict calibrated risk on clamped candidate
            cand_df = pd.DataFrame([row])[CANONICAL_FEATURES]
            cand_prob = float(_model.predict_proba(cand_df)[0, 1])

            # Discard any candidate that fails to strictly reduce risk
            if cand_prob < (baseline_prob - 0.005):
                has_delta = any(abs(float(row[f]) - float(baseline_row[f])) > 1e-4 for f in actionable_feats)
                if has_delta:
                    valid_candidates.append(row)

    # 2. If candidates were rejected or insufficient, fill from clinical strategies
    if len(valid_candidates) < total_pathways:
        backup_candidates = _generate_clinical_fallback_candidates(baseline_row)
        for b_cand in backup_candidates:
            if len(valid_candidates) >= total_pathways:
                break
            cand_df = pd.DataFrame([b_cand])[CANONICAL_FEATURES]
            cand_prob = float(_model.predict_proba(cand_df)[0, 1])
            if cand_prob < (baseline_prob - 0.005):
                valid_candidates.append(b_cand)

    # 3. Format final pathways and itemized deltas
    pathways = []
    if valid_candidates:
        cand_df_all = pd.DataFrame(valid_candidates)[CANONICAL_FEATURES]
        cand_probs_all = _model.predict_proba(cand_df_all)[:, 1]

        for i, cf_row in enumerate(valid_candidates):
            target_prob = float(cand_probs_all[i])
            target_cat = _get_risk_category(target_prob)
            risk_reduction = baseline_prob - target_prob

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

            priority_order = {
                "sysBP": 1, "diaBP": 2, "cigsPerDay": 3, "currentSmoker": 4,
                "totChol": 5, "BMI": 6, "glucose": 7, "BPMeds": 8, "heartRate": 9
            }
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
        "fallback_triggered": recourse_raw["fallback_triggered"] or len(valid_candidates) < total_pathways,
        "fallback_reason": recourse_raw.get("fallback_reason"),
        "execution_time_ms": recourse_raw["execution_time_ms"]
    }


initialize_engine()