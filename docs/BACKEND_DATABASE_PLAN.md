# Axiora — Backend & Database Implementation Plan

## 1. Executive Summary & Objective
Implement a secure, persistent clinical data layer for **CardioRecourse (Axiora)** using **Google Cloud Firestore** and **FastAPI**, enabling doctors to:
- Authenticate securely via JSON Web Tokens (JWT).
- Maintain managed patient cohorts.
- Execute AI risk assessments for patients.
- Store SHAP attributions, DiCE recourse pathways, and doctor-confirmed clinical action plans.
- Track longitudinal patient risk progression over time.

This plan preserves the existing **anonymous public assessment pipeline** (`/predict`, `/explain`, `/recourse`, `/assess`) without modifications, avoiding any merge conflicts.

---

## 2. Directory Structure & Merge-Conflict Protection
All database, authentication, and clinical portal logic is placed in isolated packages:

```text
backend/
├── auth/                       # Isolated Authentication
│   ├── __init__.py
│   ├── auth_handler.py         # JWT generation, token verification & password hashing
│   └── auth_routes.py          # /api/auth/doctor/login, /api/auth/doctor/register, /api/auth/me
├── db/                         # Isolated Database Layer
│   ├── __init__.py
│   ├── firebase.py             # Firebase Admin SDK initialization & client management
│   └── firestore_service.py    # CRUD operations for Doctors, Patients, Assessments, ActionPlans
├── portal/                     # Isolated Doctor Clinical Endpoints
│   ├── __init__.py
│   └── doctor_routes.py        # /api/doctor/patients, assessments, history, action plans
├── main.py                     # MODIFIED ONLY to mount new routers (2-3 lines added)
└── [EXISTING FILES UNTOUCHED]  # api_routes.py, pool.py, worker.py, model_pipeline.py, etc.
```

---

## 3. Cloud Firestore Data Model & Schema

```text
Firestore Root
│
├── doctors/{doctorId}
│     ├── doctorId: string (UUID / UID)
│     ├── email: string (unique, indexed)
│     ├── fullName: string ("Dr. Jane Smith")
│     ├── specialization: string ("Cardiology / General Practice")
│     ├── hospital: string ("National Hospital of Sri Lanka")
│     ├── passwordHash: string (bcrypt hash)
│     └── createdAt: timestamp
│
└── patients/{patientId}
      ├── patientId: string ("PID-001")
      ├── doctorId: string (indexed: foreign key to managing doctor)
      ├── fullName: string ("Jane Doe")
      ├── age: number
      ├── sex: string ("Female" / "Male")
      ├── contactPhone: string (optional)
      ├── baselineBiomarkers: map {
      │     male: 0, age: 55, currentSmoker: 1, cigsPerDay: 20,
      │     BPMeds: 0, prevalentStroke: 0, prevalentHyp: 1, diabetes: 0,
      │     totChol: 240, sysBP: 150, diaBP: 90, BMI: 29.0,
      │     heartRate: 75, glucose: 85
      │   }
      ├── latestRiskScore: number (0.264)
      ├── latestRiskBand: string ("High" | "Borderline" | "Low")
      ├── createdAt: timestamp
      ├── updatedAt: timestamp
      │
      ├── assessments/{assessmentId}  [Subcollection]
      │     ├── assessmentId: string (UUID)
      │     ├── assessedAt: timestamp
      │     ├── inputBiomarkers: map (exact numerical inputs sent to XGBoost)
      │     ├── riskScore: number (0.264)
      │     ├── riskPercentage: number (26.4)
      │     ├── riskBand: string ("High")
      │     ├── shapAttributions: list [
      │     │     { feature: "sysBP", attribution: 0.176, patientValue: 150.0, direction: "risk_increasing" }, ...
      │     │   ]
      │     └── pipelineLatencyMs: number
      │
      └── actionPlans/{planId}        [Subcollection]
            ├── planId: string (UUID)
            ├── assessmentId: string (FK reference to the assessment)
            ├── createdAt: timestamp
            ├── selectedPathwayTitle: string ("Pathway 1 — Lifestyle Optimization")
            ├── projectedRiskPercentage: number (18.2)
            ├── absoluteRiskReduction: number (8.2)
            ├── targetBiomarkers: map { sysBP: 135, totChol: 200, BMI: 25.5, ... }
            ├── recommendedChanges: list [
            │     { feature: "sysBP", delta: -15, unit: "mmHg", baseline: 150, target: 135 }
            │   ]
            ├── clinicianNotes: string ("Prescribed ACE inhibitor; advised 30min daily walk")
            └── doctorConfirmed: boolean (true)
```

---

## 4. Authentication & Security Architecture

1. **Role Model**:
   - Single authenticated role: `Doctor`.
   - Public users access inference anonymously without token.
   - Patients have no login credentials; they are managed records.
2. **Token Specification**:
   - Algorithm: `HS256`.
   - Expiration: 24 hours.
   - Payload:
     ```json
     {
       "sub": "doc_uuid_12345",
       "email": "dr.smith@hospital.org",
       "role": "doctor",
       "exp": 1790400000
     }
     ```
3. **Password Security**:
   - `passlib` with `bcrypt` rounds = 12. Plaintext passwords never stored.
4. **FastAPI Route Guard (`get_current_doctor`)**:
   - Extracts Bearer token from `Authorization` header.
   - Verifies signature, expiry, and doctor existence in Firestore.
   - Raises `HTTPException(status_code=401, detail="Invalid credentials or expired token")`.

---

## 5. API Endpoints Specification

### 5.1 Public Endpoints (Existing — Preserved)
- `POST /predict` — XGBoost risk score & risk band
- `POST /explain` — TreeSHAP waterfall feature attributions
- `POST /recourse` — DiCE counterfactual optimization pathways
- `POST /assess` — Combined composite pipeline

### 5.2 Authentication Endpoints (`backend/auth/auth_routes.py`)
- `POST /api/auth/doctor/register`
  - Body: `{ email, password, fullName, specialization, hospital }`
  - Response: `{ doctorId, token, message }`
- `POST /api/auth/doctor/login`
  - Body: `{ email, password }`
  - Response: `{ token, doctor: { id, email, fullName, hospital } }`
- `GET /api/auth/me`
  - Header: `Authorization: Bearer <token>`
  - Response: Doctor profile

### 5.3 Doctor Portal Endpoints (`backend/portal/doctor_routes.py`)
*All guarded by `Depends(get_current_doctor)`*

- `GET /api/doctor/overview`
  - Returns cohort metrics: `{ totalPatients, highRiskCount, borderlineCount, lowRiskCount }`.
- `GET /api/doctor/patients`
  - Query params: `search`, `risk_band`, `limit`, `offset`.
  - Returns list of patient summaries.
- `POST /api/doctor/patients`
  - Body: `{ fullName, age, sex, contactPhone, baselineBiomarkers }`.
  - Creates Firestore document and returns created patient record.
- `GET /api/doctor/patients/{patient_id}`
  - Returns complete patient profile and baseline biomarkers.
- `GET /api/doctor/patients/{patient_id}/history`
  - Returns chronological list of all previous assessments and confirmed action plans.
- `POST /api/doctor/patients/{patient_id}/assess`
  - Runs AI pipeline with current biomarker inputs.
  - Automatically saves the assessment result to `patients/{patientId}/assessments`.
  - Returns prediction, SHAP attributions, and candidate DiCE pathways.
- `POST /api/doctor/patients/{patient_id}/action-plan`
  - Body: `{ assessmentId, selectedPathwayTitle, projectedRisk, targetBiomarkers, recommendedChanges, clinicianNotes }`.
  - Saves to `patients/{patientId}/actionPlans`.
  - Updates patient's `latestRiskScore`, `latestRiskBand`, and `updatedAt`.

---

## 6. Implementation Steps

1. **Dependencies**:
   - Add `firebase-admin`, `python-jose[cryptography]`, `passlib[bcrypt]` to `.venv`.
2. **Firestore Connector (`backend/db/firebase.py`)**:
   - Initialize Firebase credentials using `GOOGLE_APPLICATION_CREDENTIALS` or a local `serviceAccountKey.json`.
   - Provide an offline/mock fallback mode so the application runs even if cloud credentials are temporarily unavailable.
3. **Firestore Service (`backend/db/firestore_service.py`)**:
   - Write CRUD functions: `create_doctor`, `get_doctor_by_email`, `create_patient`, `list_patients_by_doctor`, `save_patient_assessment`, `save_patient_action_plan`, `get_patient_history`.
4. **Auth Module (`backend/auth/`)**:
   - Implement `auth_handler.py` and `auth_routes.py`.
5. **Doctor Routes (`backend/portal/doctor_routes.py`)**:
   - Implement protected endpoints using existing `run_assessment_pipeline()` from `backend/pool.py`.
6. **Main Router Integration (`backend/main.py`)**:
   - Mount `auth_router` and `doctor_router` with `/api` prefix.
