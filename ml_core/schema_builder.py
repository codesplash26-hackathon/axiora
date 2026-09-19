import sys
from pathlib import Path

# Dynamically add project root (Axiora) to sys.path so config can be imported
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import json
import numpy as np
import pandas as pd
import config

FEATURE_TIERS = {
    "immutable": ["age", "male"],
    "monotonic": ["prevalentStroke", "prevalentHyp", "diabetes"],
    "actionable": [
        "sysBP",
        "diaBP",
        "totChol",
        "BMI",
        "glucose",
        "cigsPerDay",
        "currentSmoker",
        "BPMeds",
        "heartRate",
    ],
}

ACTIONABLE_BOUNDS = {
    "sysBP": {
        "min": 95.0,
        "max": 240.0,
        "max_step": 25.0,
        "unit": "mmHg",
        "description": "Systolic Blood Pressure",
    },
    "diaBP": {
        "min": 60.0,
        "max": 140.0,
        "max_step": 15.0,
        "unit": "mmHg",
        "description": "Diastolic Blood Pressure",
    },
    "totChol": {
        "min": 120.0,
        "max": 450.0,
        "max_step": 50.0,
        "unit": "mg/dL",
        "description": "Total Serum Cholesterol",
    },
    "BMI": {
        "min": 18.5,
        "max": 50.0,
        "max_step": 4.0,
        "unit": "kg/m^2",
        "description": "Body Mass Index",
    },
    "glucose": {
        "min": 60.0,
        "max": 300.0,
        "max_step": 30.0,
        "unit": "mg/dL",
        "description": "Fasting Blood Glucose",
    },
    "cigsPerDay": {
        "min": 0.0,
        "max": 60.0,
        "max_step": 20.0,
        "unit": "cigs/day",
        "description": "Cigarettes Smoked Per Day",
    },
    "heartRate": {
        "min": 45.0,
        "max": 130.0,
        "max_step": 15.0,
        "unit": "bpm",
        "description": "Heart Rate / Pulse",
    },
    "currentSmoker": {
        "min": 0,
        "max": 1,
        "max_step": 1,
        "unit": "binary",
        "description": "Current Smoking Status",
    },
    "BPMeds": {
        "min": 0,
        "max": 1,
        "max_step": 1,
        "unit": "binary",
        "description": "Blood Pressure Medication",
    },
}

CONTINUOUS_FEATURES = [
    "age",
    "cigsPerDay",
    "totChol",
    "sysBP",
    "diaBP",
    "BMI",
    "heartRate",
    "glucose",
]


def calculate_mad(series: pd.Series) -> float:
    """Computes strictly positive Median Absolute Deviation (MAD)."""
    median_val = np.median(series)
    abs_deviations = np.abs(series - median_val)
    mad_val = float(np.median(abs_deviations))

    if mad_val == 0.0:
        mad_val = float(np.mean(abs_deviations))
    if mad_val == 0.0:
        mad_val = 1.0

    return round(mad_val, 4)


def build_schema():
    if not config.CLEAN_DATASET_PATH.exists():
        raise FileNotFoundError(f"Cleaned dataset not found at: {config.CLEAN_DATASET_PATH.resolve()}")

    df = pd.read_csv(config.CLEAN_DATASET_PATH)

    mad_dict = {}
    for col in CONTINUOUS_FEATURES:
        mad_dict[col] = calculate_mad(df[col])

    schema_payload = {
        "schema_version": "1.0.0",
        "total_input_features": 14,
        "target_variable": "TenYearCHD",
        "tiers": FEATURE_TIERS,
        "actionable_boundaries": ACTIONABLE_BOUNDS,
        "mad_scales": mad_dict,
        "feature_types": {
            col: "continuous" if col in CONTINUOUS_FEATURES else "binary"
            for col in (
                FEATURE_TIERS["immutable"]
                + FEATURE_TIERS["monotonic"]
                + FEATURE_TIERS["actionable"]
            )
        },
    }

    config.FEATURE_SCHEMA_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(config.FEATURE_SCHEMA_PATH, "w", encoding="utf-8") as f:
        json.dump(schema_payload, f, indent=2)

    print(f"Feature schema successfully exported to: {config.FEATURE_SCHEMA_PATH}")
    print(f"MAD scaling factors calculated for {len(mad_dict)} continuous features.")


if __name__ == "__main__":
    build_schema()
