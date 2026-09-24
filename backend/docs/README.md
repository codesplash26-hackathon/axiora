# Backend Engineering Documentation: Current Progress & Architecture

> **Service**: `CardioRecourse API`  
> **Status**: Milestone B0 (Skeleton) & Milestone B1 (Pydantic Contracts) **COMPLETED**  
> **Primary Files**:  
> - Application Factory: [`backend/main.py`](file:///d:/CodeSplash/Axiora/backend/main.py)  
> - Pydantic Data Contracts: [`backend/schemas.py`](file:///d:/CodeSplash/Axiora/backend/schemas.py)  
> - Contract Test Suite: [`tests/test_schemas.py`](file:///d:/CodeSplash/Axiora/tests/test_schemas.py)  
> **Framework**: FastAPI (v0.141+) on Uvicorn (v0.53+) with Pydantic V2 & ORJSON  

---

## 1. What Has Been Implemented So Far

The foundational backend microservice and the immutable Pydantic V2 data contracts have been built, strictly validated, and verified through unit tests.

### 1.1 Core Application Factory ([`backend/main.py`](file:///d:/CodeSplash/Axiora/backend/main.py))
- **FastAPI Instance**: Instantiated with OpenAPI metadata (`title="CardioRecourse API"`, `version="1.0.0"`).
- **ORJSON Serialization**: Defaulted to `ORJSONResponse` for C-optimized serialization speed.
- **CORS Middleware**: Pre-configured to allow frontend Vite dev servers (`http://localhost:5173`, `http://127.0.0.1:5173`).
- **Health Endpoint**: `GET /health` responding with service status and `SLA_TIMEOUT_SECONDS = 1.4`.

---

### 1.2 Pydantic V2 Data Contracts ([`backend/schemas.py`](file:///d:/CodeSplash/Axiora/backend/schemas.py))
The data contracts establish the immutable specification linking Track A (ML Core), Track B (Backend), and Track C (Frontend).

```
                      [ PatientInputSchema ]
                                 │
                   (POST /predict, /explain, /recourse)
                                 │
         ┌───────────────────────┼───────────────────────┐
         ▼                       ▼                       ▼
[ PredictionResponse ]  [ ExplanationResponse ]  [ RecourseResponse ]
  - risk_score            - base_value             - patient_baseline_risk
  - risk_percentage       - risk_score             - pathways [
  - risk_band             - attributions [             RecoursePathway:
  - requires_recourse         FeatureAttribution:        - title ("Lifestyle-Led")
                                - feature                - projected_risk_score
                                - display_name           - absolute_risk_reduction
                                - attribution_value      - changes [FeatureDelta]
                                - direction              - full_target_vector
                              ]                        ]
                                                   - is_fallback
```

#### 1. Inbound Patient Biomarker Contract (`PatientInputSchema`)
Validates incoming patient records across 14 canonical Framingham features with strict biological bounds:
- **Demographics & Binary History**: `male` (`0|1`), `age` (`20–100`), `BPMeds` (`0.0|1.0`), `prevalentStroke` (`0|1`), `prevalentHyp` (`0|1`), `diabetes` (`0|1`).
- **Continuous Clinical Biomarkers**:
  - `sysBP`: Systolic blood pressure (`95.0 – 295.0 mmHg`)
  - `diaBP`: Diastolic blood pressure (`50.0 – 160.0 mmHg`)
  - `totChol`: Total serum cholesterol (`100.0 – 600.0 mg/dL`)
  - `BMI`: Body Mass Index (`15.0 – 55.0 kg/m²`)
  - `heartRate`: Resting heart rate (`40.0 – 180.0 bpm`)
  - `glucose`: Fasting blood glucose (`40.0 – 400.0 mg/dL`)
- **Cross-Field Biological Coherence Validator (`validate_smoking_coherence`)**:
  - Enforces physiological coherence via `@model_validator(mode="after")`:
    - Non-smokers (`currentSmoker == 0`) must have `cigsPerDay == 0`.
    - Active smokers (`currentSmoker == 1`) must have `cigsPerDay > 0`.

#### 2. Outbound Prediction Contract (`PredictionResponse`)
- `risk_score`: Calibrated 10-year hard CHD probability $\in [0.0, 1.0]$.
- `risk_percentage`: Percentage formatted float $\in [0.0, 100.0]$.
- `risk_band`: Triage category (`"Low"` $<10\%$, `"Borderline"` $10\%-19.9\%$, `"High"` $\ge 20\%$).
- `requires_recourse`: Boolean flag (`True` if `risk_score >= 0.20`, gating downstream DiCE recourse calculations).

#### 3. Outbound Diagnostic Explanation Contract (`ExplanationResponse`)
- Encapsulates local SHAP feature attributions sorted by impact:
  - `FeatureAttribution`: Pairs raw column keys (`sysBP`) with clinical labels (`display_name: "Systolic Blood Pressure"`), the continuous attribution value ($\phi_j$), patient baseline reading, and impact direction (`"risk_increasing"` vs `"protective"`).

#### 4. Outbound Prescriptive Recourse Contract (`RecourseResponse`)
- Supports multi-pathway side-by-side clinical comparisons:
  - `FeatureDelta`: Itemized biomarker recommendations detailing `baseline_value`, `target_value`, signed `delta` ($target - baseline$), and measurement `unit`.
  - `RecoursePathway`: Represents a distinct clinical strategy (`title: "Lifestyle-Led"` vs `"Medication-Led"`), with `projected_risk_score`, `absolute_risk_reduction` (in percentage points), list of `changes`, and `full_target_vector`.
  - `RecourseResponse`: Bundles candidate pathways alongside `is_fallback` indicator (notifying the clinician if the 1.4s SLA random fallback solver was triggered).

---

### 1.3 Contract Test Suite ([`tests/test_schemas.py`](file:///d:/CodeSplash/Axiora/tests/test_schemas.py))
A dedicated Pytest test suite validates schema enforcement and error handling:
- **`test_valid_patient_schema`**: Confirms valid 14-biomarker patient vectors instantiate without errors.
- **`test_sysbp_out_of_bounds_fails`**: Asserts that unphysiological values (e.g. `sysBP = 450.0 mmHg`) raise a Pydantic `ValidationError`.
- **`test_smoking_coherence_non_smoker_with_cigarettes`**: Rejects incoherent states (`currentSmoker = 0` with `cigsPerDay = 10.0`).
- **`test_smoking_coherence_smoker_with_zero_cigarettes`**: Rejects incoherent states (`currentSmoker = 1` with `cigsPerDay = 0.0`).
- **`test_prediction_response_schema`**: Confirms triage gating logic (`requires_recourse = True` on high risk).
- **`test_recourse_response_schema`**: Validates deeply nested counterfactual pathway response models and delta calculations.

---

## 2. Immediate Next Steps & Planned Architecture

With Task B1 complete, the backend roadmap continues along Track B:

```
┌──────────────────────────────────────────────────────────┐
│                   backend/main.py                        │
└────────────┬───────────────────────────────┬─────────────┘
             │                               │
             ▼                               ▼
    ┌─────────────────┐             ┌─────────────────┐
    │ backend/routes/ │             │ backend/pool.py │
    ├─────────────────┤             ├─────────────────┤
    │ - /predict      │             │ ProcessPool     │
    │ - /explain      │ ──────────► │ Workers (OMP=1) │
    │ - /recourse     │             │ Bypasses GIL    │
    │ - /assess (SLA) │             └─────────────────┘
    └─────────────────┘
```

1. **Task B2 (Mock REST Endpoints)**: Scaffold mock endpoints for `/predict`, `/explain`, and `/recourse` using `schemas.py` to immediately unblock Track C (Frontend) development.
2. **Task B3 & B4 (ProcessPool Concurrency & Worker Pre-warming)**: Create `backend/pool.py` with `OMP_NUM_THREADS=1` and `worker.py` to isolate CPU-intensive SHAP/DiCE computations from the async event loop.
3. **Task B5 - B8 (Live REST Pipeline & SLA Guard)**: Wire up live models into endpoints and create the composite `/assess` route with the 1.4-second SLA watchdog failover.

---

## 3. How to Run & Verify the Backend

### Run Schema Contract Tests:
```powershell
pytest tests/test_schemas.py -v
```

### Start Server (Development Mode):
```powershell
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

### Automated Health Verification:
```powershell
python -c "from fastapi.testclient import TestClient; from backend.main import app; client = TestClient(app); r = client.get('/health'); assert r.status_code == 200; assert r.json()['status'] == 'online'; print('BACKEND VERIFIED: Health status online')"
```

### Interactive Documentation:
Inspect and test endpoints via Swagger UI:
👉 **`http://127.0.0.1:8000/docs`**
