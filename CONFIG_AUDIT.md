# Configuration & Filesystem Compliance Audit

This document records the audit comparing the codebase filesystem, data files, models, and scripts against the definitions in [`config.py`](file:///d:/CodeSplash/Axiora/config.py).

---

## 1. Summary Overview

| Config Variable | Defined Path in `config.py` | Exists on Disk? | Content / Status Compliance |
| :--- | :--- | :---: | :--- |
| `BASE_DIR` | `d:\CodeSplash\Axiora` | **Yes** | ✅ Project root is correct. |
| `DATA_DIR` | `data/` | **Yes** | ⚠️ Contains stray duplicate file `data/data_cleaned.csv`. |
| `RAW_DATA_DIR` | `data/raw/` | **Yes** | ✅ Exists. |
| `PROCESSED_DATA_DIR` | `data/processed/` | **Yes** | ✅ Exists. |
| `ARTIFACTS_DIR` | `artifacts/` | **Yes** | ⚠️ Contains `data_summary.json` (not declared in `config.py`). |
| `MODEL_PATH` | `artifacts/model_calibrated.joblib` | ❌ **No** | **Missing file**: Calibrated model has not yet been generated/saved. |
| `SHAP_BACKGROUND_PATH` | `artifacts/shap_background.npy` | ❌ **No** | **Missing file**: SHAP background array has not yet been generated. |
| `RAW_DATASET_PATH` | `data/raw/framingham.csv` | **Yes** | ⚠️ **Line Endings**: File uses classic Mac OS CR (`\r`) line endings. |
| `CLEAN_DATASET_PATH` | `data/processed/clean_framingham.csv` | **Yes** | ✅ Matches schema (4,240 rows, 15 columns). |
| `FEATURE_SCHEMA_PATH` | `data/processed/feature_schema.json` | **Yes** | ✅ Valid schema v1.0.0 with all 14 features, tiers, and bounds. |
| `HOST` / `PORT` | `127.0.0.1:8000` | **Yes** | ✅ Aligns with FastAPI Uvicorn config and Vite dev proxy. |
| `SLA_TIMEOUT_SECONDS` | `1.4` | **Yes** | ✅ Consumed by [`backend/main.py`](file:///d:/CodeSplash/Axiora/backend/main.py). |

---

## 2. Detailed Findings

### A. Missing Files Defined in `config.py`
1. **`artifacts/model_calibrated.joblib` (`MODEL_PATH`)**:
   - **Status**: **Missing**.
   - **Details**: `config.MODEL_PATH` expects the trained and calibrated XGBoost model here, but the folder only contains `.gitkeep` and `data_summary.json`.
2. **`artifacts/shap_background.npy` (`SHAP_BACKGROUND_PATH`)**:
   - **Status**: **Missing**.
   - **Details**: `config.SHAP_BACKGROUND_PATH` expects a precomputed numpy array for SHAP background samples here, but it does not exist.

---

### B. Content & Formatting Issues
1. **`data/raw/framingham.csv` (`RAW_DATASET_PATH`)**:
   - **Status**: File exists and contains all 4,240 records and 16 raw columns.
   - **Discrepancy**: Uses legacy classic Mac CR (`\r`, byte `0x0D`) line separators rather than standard CRLF (`\r\n`) or LF (`\n`). In editors and tools expecting LF/CRLF, the entire 191 KB file appears on a single line.

---

### C. Stray / Misplaced Files Not in `config.py`
1. **`data/data_cleaned.csv`**:
   - **Issue**: Located directly in `data/`. It is an unconfigured duplicate of `data/processed/clean_framingham.csv`.
2. **`artifacts/data_summary.json`**:
   - **Issue**: Present in `artifacts/`, generated during data preprocessing (contains population medians and stds), but **`config.py` does not define a variable for it** (e.g. `DATA_SUMMARY_PATH = ARTIFACTS_DIR / "data_summary.json"`).

---

### D. Codebase Scripts NOT Using `config.py`
Several scripts in [`ml_core`](file:///d:/CodeSplash/Axiora/ml_core) bypass `config.py` and use hardcoded, contradictory paths:

1. **[`ml_core/preprocess.py`](file:///d:/CodeSplash/Axiora/ml_core/preprocess.py#L12-L14)**:
   - Sets `OUTPUT_CSV = DATA_DIR / "data_cleaned.csv"` instead of using `config.CLEAN_DATASET_PATH` (`data/processed/clean_framingham.csv`).
   - Hardcodes `DATA_DIR = Path("data")` and `ARTIFACTS_DIR = Path("artifacts")` instead of importing from `config.py`.
2. **[`ml_core/schema_builder.py`](file:///d:/CodeSplash/Axiora/ml_core/schema_builder.py#L7-L11)**:
   - Looks for `data/processed/data_cleaned.csv` or `data/raw/data_cleaned.csv` instead of reading `config.CLEAN_DATASET_PATH` (`data/processed/clean_framingham.csv`).
   - Hardcodes `OUTPUT_SCHEMA = Path("data/processed/feature_schema.json")` instead of importing `config.FEATURE_SCHEMA_PATH`.
