# Backend Engineering Documentation: Current Progress & Architecture

> **Service**: `CardioRecourse API`  
> **Status**: Milestone B0 / B1 Base Skeleton Operational  
> **Primary File**: [`backend/main.py`](file:///d:/CodeSplash/Axiora/backend/main.py)  
> **Framework**: FastAPI (v0.141+) on Uvicorn (v0.53+) with ORJSON  

---

## 1. What Has Been Implemented So Far

The foundational backend infrastructure has been stood up, configured, and verified.

### 1.1 Core Application Factory ([`backend/main.py`](file:///d:/CodeSplash/Axiora/backend/main.py))
- **FastAPI Instance**: Instantiated with OpenAPI metadata (`title="CardioRecourse API"`, `version="1.0.0"`).
- **ORJSON Default Serialization**: Configured with `default_response_class=ORJSONResponse` for ultra-fast, C-optimized JSON serialization and deserialization, essential for low-latency transmission of large numeric arrays (SHAP attributions and DiCE counterfactual matrices).
- **CORS Middleware**: Activated via `CORSMiddleware` with explicit support for frontend Vite dev origins:
  - `http://localhost:5173`
  - `http://127.0.0.1:5173`
  - Permissive methods (`allow_methods=["*"]`) and headers (`allow_headers=["*"]`) to support preflight `OPTIONS` requests during local development.

### 1.2 Centralized Configuration Integration ([`config.py`](file:///d:/CodeSplash/Axiora/config.py))
- The application dynamically imports runtime constants from `config.py`:
  - `HOST`: `"127.0.0.1"`
  - `PORT`: `8000`
  - `SLA_TIMEOUT_SECONDS`: `1.4` (Strict SLA latency ceiling for the diagnostic pipeline)

### 1.3 Health & Diagnostic Endpoint
- **Route**: `GET /health`
- **Tag**: `["System"]`
- **Output Contract**:
  ```json
  {
    "status": "online",
    "service": "CardioRecourse API",
    "sla_timeout_seconds": 1.4
  }
  ```
- **Verification**: Verifies that the Uvicorn event loop is active and configuration bounds are loaded.

### 1.4 Pinned Dependencies & Environment
- Environment is pinned in `requirements.txt` and verified within the project virtualenv:
  - `fastapi>=0.110.0` (active: `0.141.1`)
  - `uvicorn[standard]>=0.28.0` (active: `0.53.0`)
  - `pydantic>=2.6.0` (active: `2.13.5`)
  - `orjson>=3.9.0` (active: `3.12.0`)
  - `httpx>=0.27.0` (active: `0.28.1`)

---

## 2. Immediate Next Steps & Planned Architecture

The backend will be expanded across Track B according to [ARCHITECTURE.md](file:///d:/CodeSplash/Axiora/ARCHITECTURE.md) and [TASK_BOARD.md](file:///d:/CodeSplash/Axiora/TASK_BOARD.md):

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

1. **Task B1 (Pydantic v2 Contracts)**: Implement `backend/schemas.py` declaring the strict 15-feature canonical input model (`PatientBiomarkerInput`), `PredictionResponse`, `ExplanationResponse`, `RecourseResponse`, and composite `AssessmentResponse`.
2. **Task B2 & B4 (ProcessPool Concurrency)**: Implement `backend/pool.py` with `OMP_NUM_THREADS=1` and `MKL_NUM_THREADS=1` to isolate CPU-intensive SHAP and DiCE calculations from blocking the async event loop.
3. **Task B3 (Stateless De-identification)**: Implement `backend/security.py` to strip direct identifiers and enforce physiological boundary filters (HIPAA Safe Harbor / Sri Lanka PDPA No. 9 of 2022).
4. **Task B5 - B8 (REST Endpoints)**: Mount `/predict`, `/explain`, `/recourse`, and the composite `/assess` endpoint with the 1.4-second watchdog timeout.

---

## 3. How to Run & Verify the Backend

### Start Server (Development Mode):
```powershell
# From project root
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

### Automated Health Verification:
```powershell
python -c "from fastapi.testclient import TestClient; from backend.main import app; client = TestClient(app); r = client.get('/health'); assert r.status_code == 200; assert r.json()['status'] == 'online'; print('BACKEND VERIFIED: Health status online')"
```

### Interactive Documentation:
Once running, inspect and test endpoints via Swagger UI:
👉 **`http://127.0.0.1:8000/docs`**
