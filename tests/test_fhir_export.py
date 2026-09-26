import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.fhir.fhir_builder import (
    build_fhir_risk_assessment,
    build_fhir_care_plan,
    build_fhir_observation,
    LOINC_MAP
)

client = TestClient(app)


def test_fhir_observation_builder():
    obs = build_fhir_observation("sysBP", 145.0, "PID-TEST-01")
    assert obs["resourceType"] == "Observation"
    assert obs["status"] == "final"
    assert obs["subject"]["reference"] == "Patient/PID-TEST-01"
    assert obs["code"]["coding"][0]["code"] == "8480-6"
    assert obs["valueQuantity"]["value"] == 145.0
    assert obs["valueQuantity"]["unit"] == "mm[Hg]"


def test_fhir_risk_assessment_builder():
    record = {
        "assessmentId": "asm-12345",
        "riskScore": 0.285,
        "riskBand": "High",
        "assessedAt": "2026-09-26T09:00:00Z",
        "pipelineLatencyMs": 42.5
    }
    ra = build_fhir_risk_assessment(record, "PID-TEST-01")
    assert ra["resourceType"] == "RiskAssessment"
    assert ra["id"] == "asm-12345"
    assert ra["status"] == "final"
    assert ra["prediction"][0]["probabilityDecimal"] == 0.285
    assert ra["prediction"][0]["qualitativeRisk"]["text"] == "High"


def test_fhir_care_plan_builder():
    plan = {
        "planId": "cp-999",
        "selectedPathwayTitle": "Lifestyle & Hemodynamic Recourse",
        "projectedRiskPercentage": 14.5,
        "absoluteRiskReduction": 14.0,
        "recommendedChanges": [
            {
                "feature": "sysBP",
                "display_name": "Systolic Blood Pressure",
                "target_value": 125.0,
                "delta": -25.0,
                "unit": "mmHg"
            },
            {
                "feature": "totChol",
                "display_name": "Total Cholesterol",
                "target_value": 180.0,
                "delta": -50.0,
                "unit": "mg/dL"
            }
        ],
        "clinicianNotes": "Initiate low-sodium diet and daily walking."
    }
    cp = build_fhir_care_plan(plan, "PID-TEST-01")
    assert cp["resourceType"] == "CarePlan"
    assert cp["id"] == "cp-999"
    assert cp["status"] == "active"
    assert len(cp["activity"]) == 2
    assert "low-sodium diet" in cp["note"][0]["text"]


def test_fhir_rest_endpoints_integration():
    # 1. Register a doctor
    email = "dr.fhir@hospital.lk"
    password = "SecurePassword123"
    reg = client.post("/auth/doctor/register", json={
        "email": email,
        "password": password,
        "fullName": "Dr. FHIR Interop",
        "specialization": "Cardiology",
        "hospital": "National Hospital"
    })
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Register a patient
    pt_resp = client.post("/doctor/patients", json={
        "fullName": "Silva Perera",
        "age": 60,
        "sex": "Male",
        "contactPhone": "0771234567",
        "baselineBiomarkers": {
            "male": 1, "age": 60.0, "currentSmoker": 1, "cigsPerDay": 20.0, "BPMeds": 0,
            "prevalentStroke": 0, "prevalentHyp": 1, "diabetes": 0, "totChol": 250.0,
            "sysBP": 160.0, "diaBP": 95.0, "BMI": 28.0, "heartRate": 78.0, "glucose": 105.0
        }
    }, headers=headers)
    assert pt_resp.status_code == 201
    pt_id = pt_resp.json()["patientId"]

    # 3. Export observations
    obs_resp = client.get(f"/doctor/patients/{pt_id}/fhir/observations", headers=headers)
    assert obs_resp.status_code == 200
    bundle = obs_resp.json()
    assert bundle["resourceType"] == "Bundle"
    assert bundle["total"] >= 5

    # 4. Run clinical assessment for patient
    asm_resp = client.post(f"/doctor/patients/{pt_id}/assess", headers=headers)
    assert asm_resp.status_code == 200

    # 5. Export FHIR RiskAssessment
    ra_resp = client.get(f"/doctor/patients/{pt_id}/fhir/risk-assessment", headers=headers)
    assert ra_resp.status_code == 200
    ra_data = ra_resp.json()
    assert ra_data["resourceType"] == "RiskAssessment"
    assert ra_data["prediction"][0]["probabilityDecimal"] > 0

    # 6. Save Action Plan
    plan_resp = client.post(f"/doctor/patients/{pt_id}/action-plan", json={
        "assessmentId": asm_resp.json()["assessment_id"],
        "selectedPathwayTitle": "Optimal Recourse Pathway",
        "projectedRiskPercentage": 15.2,
        "absoluteRiskReduction": 18.5,
        "recommendedChanges": [
            {"feature": "sysBP", "display_name": "Systolic BP", "target_value": 125.0, "delta": -35.0, "unit": "mmHg"}
        ],
        "clinicianNotes": "Confirmed statin and ACE inhibitor titration."
    }, headers=headers)
    assert plan_resp.status_code == 200

    # 7. Export FHIR CarePlan
    cp_resp = client.get(f"/doctor/patients/{pt_id}/fhir/care-plan", headers=headers)
    assert cp_resp.status_code == 200
    cp_data = cp_resp.json()
    assert cp_data["resourceType"] == "CarePlan"
    assert cp_data["status"] == "active"
    assert len(cp_data["activity"]) == 1
