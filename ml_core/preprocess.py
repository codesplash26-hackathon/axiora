import json
from pathlib import Path
import numpy as np
import pandas as pd

# Define paths relative to the project root (C:\Backup\Axiora\axiora)
DATA_DIR = Path("data")
ARTIFACTS_DIR = Path("artifacts")
ARTIFACTS_DIR.mkdir(exist_ok=True)

# Updated raw input path
INPUT_CSV = DATA_DIR / "raw" / "framingham.csv"
OUTPUT_CSV = DATA_DIR / "data_cleaned.csv"
OUTPUT_SUMMARY = ARTIFACTS_DIR / "data_summary.json"

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
    if not INPUT_CSV.exists():
        raise FileNotFoundError(f"Source file not found at: {INPUT_CSV.resolve()}")

    # 1. Load raw dataset
    df = pd.read_csv(INPUT_CSV)

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
    df.to_csv(OUTPUT_CSV, index=False)

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

    with open(OUTPUT_SUMMARY, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(f"Dataset successfully cleaned: {OUTPUT_CSV} ({df.shape[0]} rows, {df.shape[1]} cols)")
    print(f"Baseline summary exported: {OUTPUT_SUMMARY}")


if __name__ == "__main__":
    clean_dataset()