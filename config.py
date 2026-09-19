from pathlib import Path

# Base Directory (Project Root)
BASE_DIR = Path(__file__).resolve().parent

# Data Directories
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"

# Artifacts Directory
ARTIFACTS_DIR = BASE_DIR / "artifacts"
DATA_SUMMARY_PATH = ARTIFACTS_DIR / "data_summary.json"
RAW_MODEL_PATH = ARTIFACTS_DIR / "model_raw.joblib"
MODEL_PATH = ARTIFACTS_DIR / "model_calibrated.joblib"
SPLIT_DATA_PATH = ARTIFACTS_DIR / "split_data.joblib"
SHAP_BACKGROUND_PATH = ARTIFACTS_DIR / "shap_background.npy"

# Schema & Dataset Paths
RAW_DATASET_PATH = RAW_DATA_DIR / "framingham.csv"
CLEAN_DATASET_PATH = PROCESSED_DATA_DIR / "clean_framingham.csv"
FEATURE_SCHEMA_PATH = PROCESSED_DATA_DIR / "feature_schema.json"

# Core Service Configuration
HOST = "127.0.0.1"
PORT = 8000
SLA_TIMEOUT_SECONDS = 1.4
