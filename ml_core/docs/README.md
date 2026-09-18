# Machine Learning Core Documentation: Current Progress & Pipeline

> **Engine**: `CardioRecourse ML & Recourse Inference Engine`  
> **Status**: Milestone A0 / Dataset Ingested & Environment Operational  
> **Location**: [`ml_core/`](file:///d:/CodeSplash/Axiora/ml_core/)  
> **Primary Dataset**: [`data/raw/framingham.csv`](file:///d:/CodeSplash/Axiora/data/raw/framingham.csv)  

---

## 1. What Has Been Implemented So Far

The foundational data assets, runtime environment, and architectural contracts for the ML track have been established and verified.

### 1.1 Raw Dataset Acquisition & Verification
- **Dataset**: Framingham Heart Study 10-Year Cardiovascular Disease Risk cohort.
- **File Location**: [`data/raw/framingham.csv`](file:///d:/CodeSplash/Axiora/data/raw/framingham.csv)
- **Dataset Dimensions**: **4,240 records** across **16 columns**.
- **Target Variable**: `TenYearCHD` (Binary: `0` = No coronary heart disease event within 10 years, `1` = Hard CHD event occurred).
- **Target Distribution**:
  - `0`: 3,596 patients (~84.8%)
  - `1`: 644 patients (~15.2%)  
  *(Reflects typical clinical class imbalance, to be handled via `scale_pos_weight` in XGBoost).*

### 1.2 Canonical 15-Biomarker Schema Contract
The feature schema has been verified and locked against the raw dataset:
```python
CANONICAL_FEATURES = [
    "male",              # int: Biological sex (0 = Female, 1 = Male)
    "age",               # int: Patient age in years (30 - 75)
    "education",         # float: Education level category (1.0 - 4.0)
    "currentSmoker",     # int: Smoking status (0 = Non-smoker, 1 = Smoker)
    "cigsPerDay",        # float: Cigarette consumption (cigs/day)
    "BPMeds",            # float: Antihypertensive medication status (0 = No, 1 = Yes)
    "prevalentStroke",   # int: History of stroke (0 = No, 1 = Yes)
    "prevalentHyp",      # int: Prevalent hypertension (0 = No, 1 = Yes)
    "diabetes",          # int: Diabetic status (0 = No, 1 = Yes)
    "totChol",           # float: Total serum cholesterol (mg/dL)
    "sysBP",             # float: Systolic blood pressure (mmHg)
    "diaBP",             # float: Diastolic blood pressure (mmHg)
    "BMI",               # float: Body mass index (kg/m²)
    "heartRate",         # float: Heart rate (bpm)
    "glucose"            # float: Fasting blood glucose (mg/dL)
]
```

### 1.3 Path & Artifact Configuration ([`config.py`](file:///d:/CodeSplash/Axiora/config.py))
The ML pipeline paths are centralized and standardized:
- `RAW_DATASET_PATH = data/raw/framingham.csv`
- `CLEAN_DATASET_PATH = data/processed/clean_framingham.csv`
- `FEATURE_SCHEMA_PATH = data/processed/feature_schema.json`
- `MODEL_PATH = artifacts/model_calibrated.joblib`
- `SHAP_BACKGROUND_PATH = artifacts/shap_background.npy`

### 1.4 ML Environment Verification
All scientific and explainability dependencies are installed and verified:
- `xgboost` (v3.4.1): Gradient-boosted decision trees.
- `scikit-learn` (v1.4.2): Data preprocessing, stratification, and probability calibration (`CalibratedClassifierCV`).
- `shap` (v0.49.1): TreeExplainer local attribution.
- `dice-ml` (v0.12): Constrained counterfactual search with MAD distance and DPP diversity.
- `pandas` (v2.3.3) & `numpy` (v1.26.4): High-speed vectorized data manipulation.

---

## 2. Immediate Next Steps & Planned Architecture

The ML pipeline will be constructed across Track A according to [ARCHITECTURE.md](file:///d:/CodeSplash/Axiora/ARCHITECTURE.md) and [TASK_BOARD.md](file:///d:/CodeSplash/Axiora/TASK_BOARD.md):

```
                       data/raw/framingham.csv
                                 │
                 [A1: Ingestion] │
                                 ▼
                     ml_core/preprocess.py [A2]
                     (Median/Mode Imputation)
                                 │
                 ┌───────────────┴───────────────┐
                 ▼                               ▼
      data/processed/clean.csv       feature_schema.json
                 │
                 ▼
       ml_core/train.py [A3] ──► artifacts/model_raw.joblib
                 │
                 ▼
     ml_core/calibrate.py [A4] ──► artifacts/model_calibrated.joblib
                 │
                 ├──► ml_core/evaluate_calibration.py [A5] (Brier < 0.13)
                 │
                 ├──► ml_core/shap_background.py [A6] ──► artifacts/shap_background.npy
                 │
                 ├──► ml_core/explain.py [A7] (SHAP TreeExplainer < 40ms)
                 │
                 └──► ml_core/recourse.py [A8] + fallback.py [A9] (DiCE Recourse)
                                 │
                                 ▼
                      ml_core/pipeline.py [A9]
                      (Unified Worker Interface)
```

1. **Task A1 & A2 (Ingestion & Preprocessing)**: Create `ml_core/ingestion.py` and `ml_core/preprocess.py` to impute missing clinical values (median for continuous, mode for categorical) and output `data/processed/clean_framingham.csv` and `feature_schema.json`.
2. **Task A3 & A4 (Model Training & Probability Calibration)**: Train `XGBClassifier` with `scale_pos_weight` and wrap with Platt sigmoid scaling (`CalibratedClassifierCV(method='sigmoid', cv='prefit')`) to eliminate historical calibration drift.
3. **Task A5 (Brier Score Validation)**: Verify that Brier Score $< 0.13$ across 10 deciles of predicted risk.
4. **Task A6 & A7 (SHAP Attribution Engine)**: Generate the 50-sample K-Means medoid background dataset (`artifacts/shap_background.npy`) and wire up `TreeExplainer` with `check_additivity=False` for sub-40ms execution.
5. **Task A8 & A9 (DiCE Recourse & Fallback Engine)**: Configure constrained genetic counterfactual search locking immutable features (`age`, `male`), bounding mutable features (`sysBP`, `totChol`, `BMI`), and adding a sub-150ms Random fallback solver.

---

## 3. How to Verify the ML Pipeline

### Dataset Verification Command:
```powershell
python -c "import pandas as pd; df = pd.read_csv('data/raw/framingham.csv'); assert df.shape == (4240, 16); assert 'TenYearCHD' in df.columns; print('ML DATASET VERIFIED: 4,240 rows, 16 columns ready')"
```

### Run Unit Tests:
```powershell
pytest tests/
```
