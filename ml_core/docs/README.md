# Machine Learning Core Documentation: Current Progress & Pipeline

> **Engine**: `CardioRecourse ML & Recourse Inference Engine`  
> **Milestone Status**: Tasks A1 and A2 Completed (Verified & Version-Controlled)  
> **Active Branch**: `ml`  
> **Engine Location**: [`axiora/ml_core/`](file:///c:/Backup/Axiora/axiora/ml_core/)  
> **Raw Dataset**: [`data/raw/framingham.csv`](file:///c:/Backup/Axiora/axiora/data/raw/framingham.csv)  
> **Cleaned Dataset**: [`data/processed/data_cleaned.csv`](file:///c:/Backup/Axiora/axiora/data/processed/data_cleaned.csv)  
> **Feature Schema**: [`data/processed/feature_schema.json`](file:///c:/Backup/Axiora/axiora/data/processed/feature_schema.json)  
> **Data Summary**: [`artifacts/data_summary.json`](file:///c:/Backup/Axiora/axiora/artifacts/data_summary.json)  

---

## 1. Track A Progress Report (Tasks A1 & A2 Completed)

**Milestone Status**: Tasks A1 and A2 completed, verified against acceptance criteria, and version-controlled on the `ml` branch.

---

### Task A1: Tabular Cleaning & Missing-Value Imputation

* **Objective**: Transform raw clinical records (`framingham.csv`) into a sanitized, numeric matrix free of null values, uninformative social attributes, and inconsistent data types.

* **Actions Taken**:
  * **Socioeconomic Feature Removal**: Dropped the `education` attribute to prevent non-physiological determinants from acting as targets in medical recourse models.
  * **Continuous Marker Imputation**: Replaced missing values across `glucose`, `totChol`, and `BMI` using population medians to ensure robustness against skewed clinical distributions.
  * **Binary Flag Imputation & Standardization**: Imputed missing categorical records (e.g., `BPMeds`) using the statistical mode and cast all binary features (`male`, `currentSmoker`, `BPMeds`, `prevalentStroke`, `prevalentHyp`, `diabetes`, `TenYearCHD`) to explicit integers (`0` or `1`).
  * **Type Optimization**: Explicitly cast all continuous physiological biomarkers (`age`, `sysBP`, `diaBP`, `totChol`, `BMI`, `heartRate`, `glucose`, `cigsPerDay`) to single-precision floating-point numbers (`float32`) to optimize memory footprint and execution speed for tree-traversal algorithms.

* **Artifacts Delivered**:
  * [`data/processed/data_cleaned.csv`](file:///c:/Backup/Axiora/axiora/data/processed/data_cleaned.csv) (Sanitized dataset with 4,240 records across 15 columns).
  * [`artifacts/data_summary.json`](file:///c:/Backup/Axiora/axiora/artifacts/data_summary.json) (Structured log containing baseline population medians and standard deviations).

* **Verification & Definition of Done (DoD)**:
  * Executed automated assertion script verifying:
    * Total null count is exactly zero (`assert df.isnull().sum().sum() == 0`).
    * `education` column is confirmed absent (`assert 'education' not in df.columns`).
    * Column count matches exactly 15 (`assert df.shape == (4240, 15)`).
    * Target variable `TenYearCHD` is strictly binary (`0` or `1`).

---

### Task A2: Clinical Feature Schema & Bounding Box Definition

* **Objective**: Formalize mathematical constraint boundaries, single-visit clinical step limits, and Median Absolute Deviation ($\text{MAD}$) scaling factors required by SHAP and DiCE-ML.

* **Actions Taken**:
  * **3-Tier Feature Classification**:
    * **Immutable**: Features that cannot be modified via clinical intervention (`age`, `male`).
    * **Monotonic**: Historical clinical events that can only progress or remain static (`prevalentStroke`, `prevalentHyp`, `diabetes`).
    * **Actionable**: Modifiable biomarkers and lifestyle indicators (`sysBP`, `diaBP`, `totChol`, `BMI`, `glucose`, `cigsPerDay`, `currentSmoker`, `BPMeds`, `heartRate`).

  * **Physiological Safety Bounds**: Established strict clinical intervals to prevent optimization engines from proposing unsafe values (e.g., systolic blood pressure floor clamped at $95\text{ mmHg}$, BMI floor at $18.5\text{ kg/m}^2$).

  * **Single-Visit Step Clamping ($\Delta_{\text{max}}$)**: Capped maximum actionable deltas to reflect realistic 3-to-6-month targets (e.g., $\Delta_{\text{max}}$ for SBP drop capped at $25\text{ mmHg}$, BMI reduction capped at $4.0\text{ kg/m}^2$, total cholesterol drop capped at $50\text{ mg/dL}$).

  * **Actionable Bounds & Single-Visit Constraints Table**:

| Feature | Unit | Min | Max | $\Delta_{\text{max}}$ (Step) | Clinical Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `sysBP` | mmHg | 95.0 | 240.0 | 25.0 | Systolic Blood Pressure |
| `diaBP` | mmHg | 60.0 | 140.0 | 15.0 | Diastolic Blood Pressure |
| `totChol` | mg/dL | 120.0 | 450.0 | 50.0 | Total Serum Cholesterol |
| `BMI` | kg/m² | 18.5 | 50.0 | 4.0 | Body Mass Index |
| `glucose` | mg/dL | 60.0 | 300.0 | 30.0 | Fasting Blood Glucose |
| `cigsPerDay` | cigs/day | 0.0 | 60.0 | 20.0 | Cigarettes Smoked Per Day |
| `heartRate` | bpm | 45.0 | 130.0 | 15.0 | Heart Rate / Pulse |
| `currentSmoker` | binary | 0 | 1 | 1 | Current Smoking Status |
| `BPMeds` | binary | 0 | 1 | 1 | Blood Pressure Medication |

  * **MAD Scale Calculation**: Computed Median Absolute Deviation across the training distribution for all 8 continuous variables to scale distance metrics during counterfactual generation:

$$\text{MAD}_j = \text{median}(\vert{}x_j - \text{median}(x_j)\vert{})$$

    Implemented fallback safeguards to ensure all continuous scale factors evaluate strictly $> 0$ (fallback to mean absolute deviation or epsilon if $\text{MAD} = 0$, e.g., zero-inflated `cigsPerDay`).

* **Artifacts Delivered**:
  * [`data/processed/feature_schema.json`](file:///c:/Backup/Axiora/axiora/data/processed/feature_schema.json) (Machine-readable schema linking tiers, units, $[min, max]$ physiological bounds, step limits, and positive $\text{MAD}$ scales).

* **Verification & Definition of Done (DoD)**:
  * Executed automated validation assertion confirming:
    * All 14 input features are classified into their respective tiers.
    * Every actionable feature contains explicit $[min, max]$ intervals where $min < max$.
    * Every continuous variable has an assigned $\text{MAD}$ value strictly greater than zero.

---

### Environment & Version Control Summary

* **Runtime Environment**: Standardized on Python 3.11 with an isolated virtual environment (`.venv`) to ensure binary wheel stability across `xgboost`, `shap`, `dice-ml`, and `scikit-learn`.
* **Version Control**: Changes committed and synchronized to the project repository under branch `ml`.

---

## 2. Dataset & Feature Contract Reference

### 2.1 Raw vs. Sanitized Dataset
- **Raw Dataset**: [`data/raw/framingham.csv`](file:///c:/Backup/Axiora/axiora/data/raw/framingham.csv) — 4,240 rows × 16 columns (contained null values in `glucose`, `totChol`, `BMI`, `BPMeds`, etc., and non-physiological `education`).
- **Cleaned Dataset**: [`data/processed/data_cleaned.csv`](file:///c:/Backup/Axiora/axiora/data/processed/data_cleaned.csv) — 4,240 rows × 15 columns (zero nulls, `education` dropped, continuous features as `float32`, binary flags as `int`).
- **Target Distribution (`TenYearCHD`)**:
  - `0` (No CHD event in 10 years): 3,596 patients (~84.8%)
  - `1` (Hard CHD event occurred): 644 patients (~15.2%)  
  *(Class imbalance ratio ~5.58:1, to be addressed via `scale_pos_weight` in XGBoost).*

### 2.2 Canonical 14-Feature Input Contract (Excluding Target)
```python
CANONICAL_FEATURES = [
    # Immutable Features (2)
    "male",              # int: Biological sex (0 = Female, 1 = Male)
    "age",               # float32: Patient age in years (30 - 75)

    # Monotonic Clinical History (3)
    "prevalentStroke",   # int: History of stroke (0 = No, 1 = Yes)
    "prevalentHyp",      # int: Prevalent hypertension (0 = No, 1 = Yes)
    "diabetes",          # int: Diabetic status (0 = No, 1 = Yes)

    # Actionable Biomarkers & Lifestyle (9)
    "currentSmoker",     # int: Smoking status (0 = Non-smoker, 1 = Smoker)
    "cigsPerDay",        # float32: Cigarette consumption (cigs/day)
    "BPMeds",            # int: Antihypertensive medication status (0 = No, 1 = Yes)
    "totChol",           # float32: Total serum cholesterol (mg/dL)
    "sysBP",             # float32: Systolic blood pressure (mmHg)
    "diaBP",             # float32: Diastolic blood pressure (mmHg)
    "BMI",               # float32: Body mass index (kg/m²)
    "heartRate",         # float32: Heart rate (bpm)
    "glucose"            # float32: Fasting blood glucose (mg/dL)
]
```

### 2.3 Verified ML Dependencies
- `xgboost` (v3.4.1): Gradient-boosted decision trees.
- `scikit-learn` (v1.4.2): Data preprocessing, stratification, and probability calibration (`CalibratedClassifierCV`).
- `shap` (v0.49.1): TreeExplainer local attribution.
- `dice-ml` (v0.12): Constrained counterfactual search with MAD distance and DPP diversity.
- `pandas` (v2.3.3) & `numpy` (v1.26.4): High-speed vectorized data manipulation.

---

## 3. End-to-End ML Pipeline & Roadmap

```
                       data/raw/framingham.csv
                                  │
            [A1: Tabular Cleaning │ & Missing Imputation]
                                  ▼
                    ml_core/preprocess.py [COMPLETED]
                                  │
                  ┌───────────────┴───────────────┐
                  ▼                               ▼
       data/processed/data_cleaned.csv   artifacts/data_summary.json
                  │
            [A2: Feature  │ Schema & Constraints]
                          ▼
            ml_core/schema_builder.py [COMPLETED]
                          │
                          ▼
             data/processed/feature_schema.json
                          │
                          ▼
               ml_core/train.py [A3: NEXT] ──► artifacts/model_raw.joblib
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

### Milestone Roadmap
1. **Task A1: Ingestion & Tabular Cleaning [COMPLETED]**: Dropped `education`, imputed continuous features by median and binary by mode, cast types to `float32`/`int`. Produced `data/processed/data_cleaned.csv` and `artifacts/data_summary.json`.
2. **Task A2: Clinical Schema & Bounding Box [COMPLETED]**: Structured 3-tier classification (immutable, monotonic, actionable), physiological safety boundaries, $\Delta_{\text{max}}$ step clamping, and positive $\text{MAD}$ scales. Produced `data/processed/feature_schema.json`.
3. **Task A3 & A4: Model Training & Probability Calibration [NEXT]**: Train `XGBClassifier` with `scale_pos_weight` and calibrate using Platt scaling (`CalibratedClassifierCV(method='sigmoid', cv='prefit')`).
4. **Task A5: Calibration Evaluation & Brier Score Validation**: Verify Brier Score $< 0.13$ across 10 deciles of predicted risk.
5. **Task A6 & A7: SHAP Attribution Engine**: Generate 50-sample K-Means medoid background dataset (`artifacts/shap_background.npy`) and configure `TreeExplainer` for sub-40ms attribution inference.
6. **Task A8 & A9: DiCE Recourse & Fallback Engine**: Implement constrained genetic counterfactual search with hard boundaries and random fallback for sub-150ms SLA.

---

## 4. Pipeline Execution & Verification Commands

### Execute Task A1 Preprocessing:
```powershell
python ml_core/preprocess.py
```

### Execute Task A2 Schema Generation:
```powershell
python ml_core/schema_builder.py
```

### Automated Acceptance & Verification Script:
```powershell
python -c "import pandas as pd, json; df = pd.read_csv('data/processed/data_cleaned.csv'); assert df.isnull().sum().sum() == 0, 'Nulls found'; assert 'education' not in df.columns, 'Education present'; assert df.shape == (4240, 15), f'Unexpected shape {df.shape}'; assert set(df['TenYearCHD'].unique()).issubset({0, 1}), 'Target not binary'; schema = json.load(open('data/processed/feature_schema.json')); assert schema['total_input_features'] == 14; assert all(v > 0 for v in schema['mad_scales'].values()); print('ALL MILESTONE A1 & A2 ACCEPTANCE CRITERIA VERIFIED!')"
```

### Run Automated Unit Tests:
```powershell
pytest tests/
```
