import pytest
from backend.db.firestore_service import (
    create_doctor,
    get_doctor_by_email,
    get_doctor_by_id,
    create_patient,
    get_patient,
    list_patients,
    update_patient,
    save_assessment,
    save_action_plan,
    get_patient_history,
    get_doctor_overview,
)


def test_doctor_crud():
    doc_data = {
        "email": "doctor.test@axiora.lk",
        "fullName": "Dr. Sarah Perera",
        "specialization": "Cardiology",
        "hospital": "Teaching Hospital Colombo",
        "passwordHash": "hashed_pw_xyz",
    }
    created = create_doctor(doc_data)
    assert created["doctorId"] is not None
    assert created["email"] == "doctor.test@axiora.lk"

    # Fetch by email
    fetched_email = get_doctor_by_email("doctor.test@axiora.lk")
    assert fetched_email is not None
    assert fetched_email["fullName"] == "Dr. Sarah Perera"

    # Fetch by ID
    fetched_id = get_doctor_by_id(created["doctorId"])
    assert fetched_id is not None
    assert fetched_id["hospital"] == "Teaching Hospital Colombo"


def test_patient_crud_and_overview():
    doctor_id = "doc_test_123"

    p1 = create_patient(doctor_id, {
        "fullName": "Jane Silva",
        "age": 55,
        "sex": "Female",
        "latestRiskScore": 0.264,
        "latestRiskPercentage": 26.4,
        "latestRiskBand": "High",
    })
    assert p1["patientId"] is not None
    assert p1["fullName"] == "Jane Silva"

    p2 = create_patient(doctor_id, {
        "fullName": "Kamal Fernando",
        "age": 48,
        "sex": "Male",
        "latestRiskScore": 0.145,
        "latestRiskPercentage": 14.5,
        "latestRiskBand": "Borderline",
    })

    p3 = create_patient(doctor_id, {
        "fullName": "Sunil De Silva",
        "age": 35,
        "sex": "Male",
        "latestRiskScore": 0.052,
        "latestRiskPercentage": 5.2,
        "latestRiskBand": "Low",
    })

    # List all
    all_patients = list_patients(doctor_id)
    assert len(all_patients) >= 3

    # Filter by risk band
    high_risk_patients = list_patients(doctor_id, risk_band="High")
    assert any(p["patientId"] == p1["patientId"] for p in high_risk_patients)

    # Search by name
    searched = list_patients(doctor_id, search="Kamal")
    assert len(searched) == 1
    assert searched[0]["fullName"] == "Kamal Fernando"

    # Overview counts
    overview = get_doctor_overview(doctor_id)
    assert overview["totalPatients"] >= 3
    assert overview["highRiskCount"] >= 1
    assert overview["borderlineCount"] >= 1
    assert overview["lowRiskCount"] >= 1

    # Update patient
    updated = update_patient(doctor_id, p1["patientId"], {"contactPhone": "+94771234567"})
    assert updated is not None
    assert updated["contactPhone"] == "+94771234567"


def test_assessment_and_action_plan_subcollections():
    doctor_id = "doc_test_subcol"
    patient = create_patient(doctor_id, {
        "fullName": "Rohan Wickrama",
        "age": 60,
        "sex": "Male",
        "latestRiskBand": "Pending",
    })
    pid = patient["patientId"]

    # Save assessment
    assessment = save_assessment(pid, {
        "riskScore": 0.285,
        "riskPercentage": 28.5,
        "riskBand": "High",
        "inputBiomarkers": {"sysBP": 155, "totChol": 245},
        "shapAttributions": [{"feature": "sysBP", "attribution": 0.15}],
        "pipelineLatencyMs": 145.2,
    })
    assert assessment["assessmentId"] is not None

    # Patient latest risk should be updated
    updated_patient = get_patient(doctor_id, pid)
    assert updated_patient["latestRiskPercentage"] == 28.5
    assert updated_patient["latestRiskBand"] == "High"

    # Save action plan
    plan = save_action_plan(pid, {
        "assessmentId": assessment["assessmentId"],
        "selectedPathwayTitle": "Lifestyle Optimization",
        "projectedRiskPercentage": 19.2,
        "absoluteRiskReduction": 9.3,
        "clinicianNotes": "Reduce salt intake and take 30 min brisk walks daily",
        "doctorConfirmed": True,
    })
    assert plan["planId"] is not None

    # Fetch history
    history = get_patient_history(pid)
    assert len(history["assessments"]) == 1
    assert history["assessments"][0]["riskBand"] == "High"
    assert len(history["actionPlans"]) == 1
    assert history["actionPlans"][0]["projectedRiskPercentage"] == 19.2
