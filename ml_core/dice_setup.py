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
    by DiCE (which internally casts non-continuous features to object/str)
    are sanitized back to float/int before inference by XGBoost.
    """
    def __init__(self, base_model):
        self.base_model = base_model
        # Expose classes_ for scikit-learn compliance
        if hasattr(base_model, "classes_"):
            self.classes_ = base_model.classes_
        else:
            self.classes_ = np.array([0, 1])

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
        return self.base_model.predict(self._sanitize(X))


_dice_data = None
_dice_model = None
_genetic_explainer = None
_schema = None
_actionable_features = None
_permitted_range = None


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


def get_permitted_range() -> Dict[str, List[Any]]:
    global _permitted_range
    if _permitted_range is None:
        schema = load_schema()
        actionable = schema["tiers"]["actionable"]
        boundaries = schema["actionable_boundaries"]
        feature_types = schema.get("feature_types", {})

        p_range = {}
        for feat in actionable:
            b = boundaries[feat]
            f_type = feature_types.get(feat, "continuous")
            if f_type == "binary":
                p_range[feat] = [str(int(b["min"])), str(int(b["max"]))]
            else:
                p_range[feat] = [float(b["min"]), float(b["max"])]
        _permitted_range = p_range
    return _permitted_range


def init_dice_framework() -> Tuple[dice_ml.Data, dice_ml.Model, dice_ml.Dice]:
    global _dice_data, _dice_model, _genetic_explainer

    if _genetic_explainer is not None:
        return _dice_data, _dice_model, _genetic_explainer

    if not config.MODEL_PATH.exists():
        raise FileNotFoundError(f"Calibrated model missing at {config.MODEL_PATH}")
    if not config.CLEAN_DATASET_PATH.exists():
        raise FileNotFoundError(f"Cleaned dataset missing at {config.CLEAN_DATASET_PATH}")

    raw_calibrated = joblib.load(config.MODEL_PATH)
    safe_model = SafeModelWrapper(raw_calibrated)

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
    """Format input dictionary into a canonical single-row DataFrame."""
    row = {}
    for col in CANONICAL_FEATURES:
        if col not in patient_dict:
            raise ValueError(f"Missing clinical biomarker: '{col}'")
        row[col] = float(patient_dict[col])
    return pd.DataFrame([row], columns=CANONICAL_FEATURES)


if __name__ == "__main__":
    print("Initializing DiCE setup...")
    d, m, exp = init_dice_framework()
    print("Actionable Features:", get_actionable_features())
    print("Permitted Ranges:", get_permitted_range())
    print("DiCE Framework operational.")
