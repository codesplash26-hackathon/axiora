import sys
from pathlib import Path

# Dynamically add project root (Axiora) to sys.path so config can be imported
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import json
import numpy as np
import pandas as pd
import config

BINARY_COLS = [
    "male",
    "currentSmoker",
    "BPMeds",
    "prevalentStroke",
    "prevalentHyp",
    "diabetes",
    "TenYearCHD",
]

CONTINUOUS_COLS = [
    "age",
    "cigsPerDay",
    "totChol",
    "sysBP",
    "diaBP",
    "BMI",
    "heartRate",
    "glucose",
]


def clean_dataset():
    if not config.RAW_DATASET_PATH.exists():
        raise FileNotFoundError(f"Source file not found at: {config.RAW_DATASET_PATH.resolve()}")

    config.PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    config.ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Load raw dataset
    df = pd.read_csv(config.RAW_DATASET_PATH)

    # 2. Remove non-physiological socioeconomic column
    if "education" in df.columns:
        df = df.drop(columns=["education"])

    # 3. Median imputation for continuous biomarkers
    medians = {}
    stds = {}

    for col in CONTINUOUS_COLS:
        median_val = float(df[col].median())
        std_val = float(df[col].std())
        medians[col] = round(median_val, 4)
        stds[col] = round(std_val, 4)
        df[col] = df[col].fillna(median_val)

    # 4. Mode imputation for binary features
    for col in BINARY_COLS:
        if col in df.columns:
            mode_val = int(df[col].mode()[0])
            df[col] = df[col].fillna(mode_val)

    # 5. Type casting
    for col in CONTINUOUS_COLS:
        df[col] = df[col].astype(np.float32)

    for col in BINARY_COLS:
        df[col] = df[col].astype(int)

    # 6. Save clean dataset
    df.to_csv(config.CLEAN_DATASET_PATH, index=False)

    # 7. Save metadata and baseline statistics
    summary = {
        "total_records": len(df),
        "total_features": df.shape[1],
        "target_variable": "TenYearCHD",
        "continuous_features": CONTINUOUS_COLS,
        "binary_features": BINARY_COLS,
        "population_medians": medians,
        "population_stds": stds,
    }

    summary_path = getattr(config, "DATA_SUMMARY_PATH", config.ARTIFACTS_DIR / "data_summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(f"Dataset successfully cleaned: {config.CLEAN_DATASET_PATH} ({df.shape[0]} rows, {df.shape[1]} cols)")
    print(f"Baseline summary exported: {summary_path}")


if __name__ == "__main__":
    clean_dataset()
