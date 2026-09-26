# Axiora — Frontend Implementation Plan

## 1. Executive Summary & Objective
Implement a multi-view clinical interface for **Axiora** supporting two distinct interaction flows:
1. **Public Users (Anonymous & Open)**: Unauthenticated access to the full AI cardiovascular risk calculator, SHAP waterfall explanation, and DiCE counterfactual recourse recommendations.
2. **Doctors / Clinicians (Authenticated)**: Access via a top-level **[Doctor Portal 🩺]** button to a protected clinical dashboard to manage patient records, run assessments, review AI suggestions, adjust targets, and save confirmed action plans to Firestore.

All existing components and public user workflows remain **100% functional and intact**.

---

## 2. Component Hierarchy & File Structure

```text
frontend/src/
├── components/
│   │   # EXISTING COMPONENTS (PRESERVED & UNCHANGED)
│   ├── RiskAssessment.tsx              # Public risk assessment questionnaire form
│   ├── RiskAssessment.css
│   ├── PredictionResult.tsx            # Animated gauge & risk band classification
│   ├── PredictionResult.css
│   ├── ExplanationPage.tsx             # Interactive TreeSHAP feature attribution bars
│   ├── ExplanationPage.css
│   ├── RecoursePage.tsx                # DiCE counterfactual actionable pathway cards
│   ├── RecoursePage.css
│   │
│   │   # NEW DOCTOR PORTAL COMPONENTS
│   ├── DoctorLoginModal.tsx            # Doctor login modal (Email/Password + Quick Demo Login)
│   ├── DoctorLoginModal.css
│   │
│   └── doctor/                         # Dedicated Doctor Portal views
│       ├── DoctorNavbar.tsx            # Doctor navigation (Brand, Doctor Name, Hospital, Logout)
│       ├── DoctorOverviewCards.tsx     # Cohort statistics (Total, High, Borderline, Low Risk)
│       ├── PatientTable.tsx            # Searchable & filterable table of registered patients
│       ├── AddPatientModal.tsx         # Modal form to register a new patient
│       ├── PatientDetailView.tsx       # Patient profile, baseline markers, and timeline history
│       ├── AssessmentHistoryView.tsx   # Chronological card list of past assessments & plans
│       ├── ClinicalReviewModal.tsx     # Pathway selector, target adjuster & clinical notes
│       └── DoctorDashboard.css         # Styling for doctor portal components
│
├── pages/
│   └── DoctorDashboardPage.tsx         # Main container layout for authenticated doctor
│
├── App.tsx                             # Top-level orchestrator & view router
├── App.css
├── api.ts                              # Existing public API client (POST /api/assess)
└── doctorApi.ts                        # NEW: API client for /api/auth/* and /api/doctor/*
```

---

## 3. UI Navigation & View Routing

The application maintains a lightweight view-state router in `App.tsx`:

```typescript
type AppView = 
  | 'landing'           // Public: Landing page
  | 'assessment'        // Public: Health biomarker questionnaire
  | 'prediction'        // Public: Risk score & gauge
  | 'explanation'       // Public: SHAP feature waterfall
  | 'recourse'          // Public: DiCE actionable pathways
  | 'doctor-dashboard'; // Doctor: Protected clinical management portal
```

### 3.1 Public User Navigation Flow
```text
Landing Page
     │  Click "Start Health Assessment"
     ▼
Risk Assessment Form
     │  Submit Health Data
     ▼
Prediction Result (Gauge + Risk Category)
     │  Click "Explain Risk Attribution (SHAP)"
     ▼
SHAP Explanation Page (Feature Waterfall)
     │  Click "Explore Actionable Recourse Pathways"
     ▼
Recourse Page (DiCE Counterfactual Cards)
     │  Click "Print / Download Report"
     ▼
Printable Action Plan (Local only; no database record)
```

### 3.2 Doctor Navigation Flow
```text
Any Page Header -> Click [Doctor Portal 🩺]
     │
     ▼
Doctor Login Modal
     │  Submit credentials (or 1-click Demo Doctor Login)
     ▼
Doctor Dashboard
  ├── Cohort Overview (Total, High, Borderline, Low Risk)
  ├── Search & Filter Patients
  └── Click on Patient row (e.g. "Jane Doe - PID-001")
           │
           ▼
     Patient Detail View
       ├── Demographics & Baseline Biomarkers
       ├── Assessment History Timeline
       │
       └── Click [Run New Assessment]
                │
                ▼
          Pre-filled Assessment Form (with patient's baseline data)
                │  Submit with today's readings
                ▼
          AI Analysis (Prediction + SHAP + DiCE)
                │
                ▼
          Clinical Review & Decision Panel
            ├── Compare Pathway A (Lifestyle) vs Pathway B (Medical)
            ├── Adjust target thresholds (e.g. SBP from 130 -> 135 mmHg)
            ├── Enter Clinical Notes ("Advised low-sodium diet; review in 6 wks")
            │
            └── Click [Save to Patient Record]
                     │
                     ▼
          Persisted to Firestore -> Patient History Updated
```

---

## 4. Detailed Feature Specifications

### 4.1 Navbar Entry Button
- Positioned in the top-right header on the public landing page:
  ```tsx
  <button className="btn-doctor-portal" onClick={() => setShowDoctorLogin(true)}>
    <Stethoscope size={18} /> Doctor Portal
  </button>
  ```
- Styled with clinical blue-teal accents to remain prominent without cluttering the public experience.

### 4.2 Doctor Login Modal (`DoctorLoginModal.tsx`)
- Form fields: Email, Password.
- **1-Click Demo Login button**:
  - Automatically signs in as `dr.smith@cardiorecourse.lk` with mock data for judging/testing without typing credentials.
- Remembers session token in `localStorage.setItem('axiora_doctor_token', token)`.

### 4.3 Cohort Overview Cards (`DoctorOverviewCards.tsx`)
- **Total Patients Managed**: Gray/slate badge.
- **High Risk ($\ge 20\%$)**: Rose/red badge with pulse alert.
- **Borderline ($10\% - 20\%$)**: Amber badge.
- **Low Risk ($< 10\%$)**: Emerald green badge.

### 4.4 Patient Roster Table (`PatientTable.tsx`)
- **Columns**:
  - `PID` (e.g. `PID-001`)
  - `Name` (e.g. `Jane Doe`)
  - `Age / Sex` (e.g. `55 / Female`)
  - `Latest Risk` (`26.4% [High]`)
  - `Last Assessed` (`25 Sep 2026`)
  - `Actions` (`[View Record]`, `[Quick Assess]`)
- **Search bar**: Instant client-side filtering by name or PID.
- **Filter pills**: `All`, `High Risk`, `Borderline`, `Low Risk`.

### 4.5 Patient Detail & History (`PatientDetailView.tsx`)
- Profile card with contact info and baseline vitals.
- Chronological timeline cards of past assessments:
  - Date and risk change indicator (e.g. `↓ 4.3% reduction since last visit`).
  - Stored doctor notes and selected recourse strategy.

### 4.6 Clinical Review & Save Modal (`ClinicalReviewModal.tsx`)
- Displays side-by-side DiCE pathways.
- Selected pathway highlights target biomarker metrics.
- Doctor can override target values.
- Textarea for clinical notes.
- Primary CTA: **"Confirm & Save to Firestore"** (`POST /api/doctor/patients/{id}/action-plan`).

---

## 5. Frontend Implementation Steps

1. **Step 1: Doctor API Client (`doctorApi.ts`)**:
   - Create auth state helper (`getToken()`, `setToken()`, `logout()`).
   - Add TypeScript interfaces: `Doctor`, `PatientSummary`, `PatientDetail`, `AssessmentHistoryItem`, `SaveActionPlanPayload`.
   - Implement fetch wrappers for all `/api/doctor/*` endpoints.
2. **Step 2: Doctor Login Modal**:
   - Create `DoctorLoginModal.tsx` and `DoctorLoginModal.css`.
   - Add the **[Doctor Portal 🩺]** button to the navbar in `App.tsx`.
3. **Step 3: Doctor Dashboard Views**:
   - Build `DoctorNavbar.tsx` and `DoctorOverviewCards.tsx`.
   - Build `PatientTable.tsx` and `AddPatientModal.tsx`.
4. **Step 4: Patient Detail & Assessment Execution**:
   - Build `PatientDetailView.tsx` with assessment history.
   - Wire "Run New Assessment" to prefill biomarker fields into the existing `handleAnalyzePatient` pipeline.
5. **Step 5: Clinical Review & Firestore Persistence**:
   - Implement `ClinicalReviewModal.tsx` to review DiCE pathways, edit targets, enter notes, and commit to Firestore.
   - Update patient record view upon saving.
