import sys
import json
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import joblib
import pandas as pd
import numpy as np
import dice_ml
import config

CANONICAL_FEATURES: List[str] = [
    "male", "age", "currentSmoker", "cigsPerDay", "BPMeds",
    "prevalentStroke", "prevalentHyp", "diabetes", "totChol",
    "sysBP", "diaBP", "BMI", "heartRate", "glucose"
]


class SafeModelWrapper:
    """
    Wraps the calibrated classifier to guarantee all DataFrames passed
    by DiCE are sanitized back to float/int before inference by XGBoost,
    and enforces the clinical 20% high-risk decision threshold.
    """
    def __init__(self, base_model, threshold: float = 0.20):
        self.base_model = base_model
        self.threshold = threshold
        if hasattr(base_model, "classes_"):
            self.classes_ = base_model.classes_
        else:
            self.classes_ = np.array([0, 1])

    def set_target_threshold(self, baseline_prob: float):
        """Ensure baseline is strictly Class 1 and target is Class 0."""
        if baseline_prob >= 0.20:
            self.threshold = 0.20
        else:
            self.threshold = max(0.05, baseline_prob - 0.05)

    def _sanitize(self, X):
        if isinstance(X, pd.DataFrame):
            X_clean = X.copy()
            for col in X_clean.columns:
                if X_clean[col].dtype == "object":
                    X_clean[col] = pd.to_numeric(X_clean[col], errors="coerce").fillna(0.0)
            return X_clean
        return X

    def predict_proba(self, X):
        return self.base_model.predict_proba(self._sanitize(X))

    def predict(self, X):
        probs = self.predict_proba(X)
        if hasattr(probs, "ndim") and probs.ndim == 2 and probs.shape[1] >= 2:
            return (probs[:, 1] >= self.threshold).astype(int)
        return self.base_model.predict(self._sanitize(X))


_dice_data = None
_dice_model = None
_genetic_explainer = None
_schema = None
_actionable_features = None
_permitted_range = None
_active_patient_context = None


def load_schema() -> Dict[str, Any]:
    global _schema
    if _schema is None:
        if not config.FEATURE_SCHEMA_PATH.exists():
            raise FileNotFoundError(f"Feature schema missing at {config.FEATURE_SCHEMA_PATH}")
        with open(config.FEATURE_SCHEMA_PATH, "r", encoding="utf-8") as f:
            _schema = json.load(f)
    return _schema


def get_actionable_features() -> List[str]:
    global _actionable_features
    if _actionable_features is None:
        schema = load_schema()
        _actionable_features = schema["tiers"]["actionable"]
    return _actionable_features


def set_active_patient_context(patient_dict: Optional[Dict[str, Any]]):
    """Sets or clears the current active patient for dynamic range clamping."""
    global _active_patient_context
    _active_patient_context = patient_dict


def set_model_recourse_threshold(baseline_prob: float):
    """Aligns DiCE decision boundary with the patient's individual baseline risk."""
    global _dice_model
    init_dice_framework()
    if _dice_model is not None and hasattr(_dice_model.model, "set_target_threshold"):
        _dice_model.model.set_target_threshold(baseline_prob)


def get_permitted_range(patient_dict: Optional[Dict[str, Any]] = None) -> Dict[str, List[Any]]:
    """
    Returns feature ranges. If a patient is provided (or set in context),
    it dynamically clamps the upper bound of risk features to the patient's current value.
    Prevents DiCE from ever suggesting worsening biomarkers. Passing patient_dict directly
    guarantees thread safety under concurrent multi-tenant requests.
    """
    target_patient = patient_dict if patient_dict is not None else _active_patient_context
    schema = load_schema()
    actionable = schema["tiers"]["actionable"]
    boundaries = schema["actionable_boundaries"]
    feature_types = schema.get("feature_types", {})

    p_range = {}
    unidirectional_harmful = ["sysBP", "diaBP", "totChol", "BMI", "glucose", "cigsPerDay", "heartRate"]

    for feat in actionable:
        b = boundaries[feat]
        f_type = feature_types.get(feat, "continuous")

        if f_type == "binary":
            if target_patient is not None and feat in target_patient:
                curr_val = int(target_patient[feat])
                if feat == "currentSmoker":
                    p_range[feat] = ["0", str(curr_val)]
                elif feat == "BPMeds":
                    p_range[feat] = [str(curr_val), "1"]
                else:
                    p_range[feat] = [str(int(b["min"])), str(int(b["max"]))]
            else:
                p_range[feat] = [str(int(b["min"])), str(int(b["max"]))]
        else:
            min_val = float(b["min"])
            max_val = float(b["max"])
            if target_patient is not None and feat in target_patient:
                curr_val = float(target_patient[feat])
                if feat in unidirectional_harmful:
                    max_val = min(max_val, curr_val)
                    min_val = min(min_val, max_val)
            p_range[feat] = [min_val, max_val]

    return p_range


def init_dice_framework() -> Tuple[dice_ml.Data, dice_ml.Model, dice_ml.Dice]:
    global _dice_data, _dice_model, _genetic_explainer

    if _genetic_explainer is not None:
        return _dice_data, _dice_model, _genetic_explainer

    if not config.MODEL_PATH.exists():
        raise FileNotFoundError(f"Calibrated model missing at {config.MODEL_PATH}")
    if not config.CLEAN_DATASET_PATH.exists():
        raise FileNotFoundError(f"Cleaned dataset missing at {config.CLEAN_DATASET_PATH}")

    raw_calibrated = joblib.load(config.MODEL_PATH)
    safe_model = SafeModelWrapper(raw_calibrated, threshold=0.20)

    clean_df = pd.read_csv(config.CLEAN_DATASET_PATH)
    schema = load_schema()
    continuous_features = [
        k for k, v in schema.get("feature_types", {}).items() if v == "continuous"
    ]

    _dice_data = dice_ml.Data(
        dataframe=clean_df,
        continuous_features=continuous_features,
        outcome_name="TenYearCHD"
    )
    _dice_model = dice_ml.Model(model=safe_model, backend="sklearn")
    _genetic_explainer = dice_ml.Dice(_dice_data, _dice_model, method="genetic")

    return _dice_data, _dice_model, _genetic_explainer


def get_dice_data() -> dice_ml.Data:
    init_dice_framework()
    return _dice_data


def get_dice_model() -> dice_ml.Model:
    init_dice_framework()
    return _dice_model


def get_genetic_explainer() -> dice_ml.Dice:
    init_dice_framework()
    return _genetic_explainer


def format_query_instance(patient_dict: Dict[str, Any]) -> pd.DataFrame:
    schema = load_schema()
    feature_types = schema.get("feature_types", {})

    row = {}
    for col in CANONICAL_FEATURES:
        if col not in patient_dict:
            raise ValueError(f"Missing clinical biomarker: '{col}'")
        f_type = feature_types.get(col, "continuous")
        if f_type == "binary":
            row[col] = int(patient_dict[col])
        else:
            row[col] = float(patient_dict[col])
    return pd.DataFrame([row], columns=CANONICAL_FEATURES)

"""
Root-level gateway for DiCE setup module.
Exposes all components from ml_core.dice_setup.
"""
from ml_core.dice_setup import (
    SafeModelWrapper,
    CANONICAL_FEATURES,
    load_schema,
    get_actionable_features,
    get_permitted_range,
    set_active_patient_context,
    set_model_recourse_threshold,
    init_dice_framework,
    get_dice_data,
    get_dice_model,
    get_genetic_explainer,
    format_query_instance,
)

if __name__ == "__main__":
    print("Testing root dice_setup gateway...")
    d, m, exp = init_dice_framework()
    print("Root dice_setup operational.")