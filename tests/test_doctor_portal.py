import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.pool import init_pool, shutdown_pool

client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def setup_teardown_pool():
    init_pool()
    yield
    shutdown_pool()


@pytest.fixture(scope="module")
def auth_doctor_token():
    email = "dr.portal.test@axiora.lk"
    reg_payload = {
        "email": email,
        "password": "ClinicalPassword2026!",
        "fullName": "Dr. Nishantha Silva",
        "specialization": "Cardiology",
        "hospital": "Karapitiya National Hospital",
    }
    resp = client.post("/auth/doctor/register", json=reg_payload)
    if resp.status_code == 201:
        token = resp.json()["access_token"]
    else:
        login_resp = client.post(
            "/auth/doctor/login",
            json={"email": email, "password": "ClinicalPassword2026!"},
        )
        token = login_resp.json()["access_token"]
    return token


def test_doctor_portal_unauthorized_rejection():
    # Attempting to access doctor routes without token must be rejected with 401
    resp = client.get("/doctor/overview")
    assert resp.status_code == 401

    resp_patients = client.get("/doctor/patients")
    assert resp_patients.status_code == 401


def test_doctor_portal_patient_lifecycle_and_assessment(auth_doctor_token):
    headers = {"Authorization": f"Bearer {auth_doctor_token}"}

    # 1. Check initial cohort overview
    overview_resp = client.get("/doctor/overview", headers=headers)
    assert overview_resp.status_code == 200
    overview_data = overview_resp.json()
    assert "totalPatients" in overview_data

    # 2. Register a new patient with baseline clinical biomarkers
    patient_payload = {
        "fullName": "Dinesh Gunawardena",
        "age": 55,
        "sex": "Male",
        "contactPhone": "+94771239999",
        "baselineBiomarkers": {
            "male": 1,
            "age": 55,
            "currentSmoker": 1,
            "cigsPerDay": 20,
            "BPMeds": 0,
            "prevalentStroke": 0,
            "prevalentHyp": 1,
            "diabetes": 0,
            "totChol": 250,
            "sysBP": 150,
            "diaBP": 95,
            "BMI": 28.5,
            "heartRate": 76,
            "glucose": 88,
        },
    }
    create_resp = client.post("/doctor/patients", json=patient_payload, headers=headers)
    assert create_resp.status_code == 201
    created_patient = create_resp.json()
    pid = created_patient["patientId"]
    assert pid is not None
    assert created_patient["fullName"] == "Dinesh Gunawardena"

    # 3. Retrieve patient profile
    get_resp = client.get(f"/doctor/patients/{pid}", headers=headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["age"] == 55

    # 4. Update patient contact
    put_resp = client.put(f"/doctor/patients/{pid}", json={"contactPhone": "+94779998888"}, headers=headers)
    assert put_resp.status_code == 200
    assert put_resp.json()["contactPhone"] == "+94779998888"

    # 5. List patients with search
    list_resp = client.get("/doctor/patients", params={"search": "Dinesh"}, headers=headers)
    assert list_resp.status_code == 200
    patients = list_resp.json()
    assert len(patients) >= 1
    assert any(p["patientId"] == pid for p in patients)

    # 6. Execute clinical AI assessment for this patient
    assess_resp = client.post(f"/doctor/patients/{pid}/assess", json={}, headers=headers)
    assert assess_resp.status_code == 200
    assess_data = assess_resp.json()
    assert "assessment_id" in assess_data
    assert assess_data["patient_id"] == pid
    assert "prediction" in assess_data
    assert "explanation" in assess_data
    assert "recourse" in assess_data
    assessment_id = assess_data["assessment_id"]

    # Verify patient's latest risk band was updated
    updated_patient_resp = client.get(f"/doctor/patients/{pid}", headers=headers)
    assert updated_patient_resp.json()["latestRiskBand"] == assess_data["prediction"]["risk_band"]

    # 7. Save a doctor-reviewed action plan
    action_plan_payload = {
        "assessmentId": assessment_id,
        "selectedPathwayTitle": "Pathway 1 — Lifestyle Led Reduction",
        "projectedRiskPercentage": 19.1,
        "absoluteRiskReduction": 7.3,
        "targetBiomarkers": {"sysBP": 135, "BMI": 26.0},
        "recommendedChanges": [
            {"feature": "sysBP", "delta": -15, "unit": "mmHg", "baseline": 150, "target": 135}
        ],
        "clinicianNotes": "Prescribed DASH diet, low-sodium protocol, 30 min daily aerobic exercise.",
        "doctorConfirmed": True,
    }
    plan_resp = client.post(f"/doctor/patients/{pid}/action-plan", json=action_plan_payload, headers=headers)
    assert plan_resp.status_code == 200
    plan_data = plan_resp.json()
    assert plan_data["status"] == "success"

    # 8. Check patient history timeline
    history_resp = client.get(f"/doctor/patients/{pid}/history", headers=headers)
    assert history_resp.status_code == 200
    history = history_resp.json()
    assert len(history["assessments"]) >= 1
    assert len(history["actionPlans"]) >= 1
    assert history["actionPlans"][0]["selectedPathwayTitle"] == "Pathway 1 — Lifestyle Led Reduction"
