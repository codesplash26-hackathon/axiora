import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from backend.db.firebase import get_firestore_client


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Doctor Operations
# ---------------------------------------------------------------------------

def create_doctor(doctor_data: Dict[str, Any]) -> Dict[str, Any]:
    db = get_firestore_client()
    doctor_id = doctor_data.get("doctorId") or str(uuid.uuid4())
    record = {
        "doctorId": doctor_id,
        "email": doctor_data["email"].strip().lower(),
        "fullName": doctor_data.get("fullName", "").strip(),
        "specialization": doctor_data.get("specialization", "Cardiology / General Practice"),
        "hospital": doctor_data.get("hospital", "Axiora Health Network"),
        "passwordHash": doctor_data["passwordHash"],
        "createdAt": _utc_now_iso(),
    }
    db.collection("doctors").document(doctor_id).set(record)
    return record


def get_doctor_by_email(email: str) -> Optional[Dict[str, Any]]:
    db = get_firestore_client()
    clean_email = email.strip().lower()
    docs = list(db.collection("doctors").where("email", "==", clean_email).stream())
    if not docs:
        return None
    return docs[0].to_dict()


def get_doctor_by_id(doctor_id: str) -> Optional[Dict[str, Any]]:
    db = get_firestore_client()
    doc = db.collection("doctors").document(doctor_id).get()
    if not doc.exists:
        return None
    return doc.to_dict()


# ---------------------------------------------------------------------------
# Patient Operations
# ---------------------------------------------------------------------------

def create_patient(doctor_id: str, patient_data: Dict[str, Any]) -> Dict[str, Any]:
    db = get_firestore_client()
    patient_id = patient_data.get("patientId")
    if not patient_id:
        existing = list(db.collection("patients").where("doctorId", "==", doctor_id).stream())
        patient_id = f"PID-{len(existing) + 1:03d}"

    record = {
        "patientId": patient_id,
        "doctorId": doctor_id,
        "fullName": patient_data.get("fullName", "").strip(),
        "age": int(patient_data.get("age", 50)),
        "sex": str(patient_data.get("sex", "Female")),
        "contactPhone": str(patient_data.get("contactPhone", "")),
        "baselineBiomarkers": dict(patient_data.get("baselineBiomarkers", {})),
        "latestRiskScore": patient_data.get("latestRiskScore", None),
        "latestRiskPercentage": patient_data.get("latestRiskPercentage", None),
        "latestRiskBand": str(patient_data.get("latestRiskBand", "Not Assessed")),
        "createdAt": _utc_now_iso(),
        "updatedAt": _utc_now_iso(),
    }
    db.collection("patients").document(patient_id).set(record)
    return record


def get_patient(doctor_id: str, patient_id: str) -> Optional[Dict[str, Any]]:
    db = get_firestore_client()
    doc = db.collection("patients").document(patient_id).get()
    if not doc.exists:
        return None
    data = doc.to_dict()
    if data and data.get("doctorId") == doctor_id:
        return data
    return None


def list_patients(
    doctor_id: str,
    search: Optional[str] = None,
    risk_band: Optional[str] = None,
) -> List[Dict[str, Any]]:
    db = get_firestore_client()
    docs = list(db.collection("patients").where("doctorId", "==", doctor_id).stream())
    results = [d.to_dict() for d in docs if d.to_dict()]

    if search:
        s = search.strip().lower()
        results = [
            p for p in results
            if s in p.get("fullName", "").lower() or s in p.get("patientId", "").lower()
        ]

    if risk_band and risk_band.lower() != "all":
        results = [
            p for p in results
            if p.get("latestRiskBand", "").lower() == risk_band.strip().lower()
        ]

    results.sort(key=lambda p: p.get("updatedAt", ""), reverse=True)
    return results


def update_patient(doctor_id: str, patient_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    patient = get_patient(doctor_id, patient_id)
    if not patient:
        return None

    db = get_firestore_client()
    clean_updates = dict(updates)
    clean_updates["updatedAt"] = _utc_now_iso()
    # Don't allow changing primary key identifiers
    clean_updates.pop("patientId", None)
    clean_updates.pop("doctorId", None)

    db.collection("patients").document(patient_id).update(clean_updates)
    patient.update(clean_updates)
    return patient


# ---------------------------------------------------------------------------
# Assessment & Action Plan Operations (Subcollections)
# ---------------------------------------------------------------------------

def save_assessment(patient_id: str, assessment_data: Dict[str, Any]) -> Dict[str, Any]:
    db = get_firestore_client()
    assessment_id = assessment_data.get("assessmentId") or str(uuid.uuid4())
    record = {
        "assessmentId": assessment_id,
        "patientId": patient_id,
        "assessedAt": _utc_now_iso(),
        "inputBiomarkers": dict(assessment_data.get("inputBiomarkers", {})),
        "riskScore": float(assessment_data.get("riskScore", 0.0)),
        "riskPercentage": float(assessment_data.get("riskPercentage", 0.0)),
        "riskBand": str(assessment_data.get("riskBand", "Unknown")),
        "shapAttributions": list(assessment_data.get("shapAttributions", [])),
        "pipelineLatencyMs": float(assessment_data.get("pipelineLatencyMs", 0.0)),
    }

    patient_ref = db.collection("patients").document(patient_id)
    patient_ref.collection("assessments").document(assessment_id).set(record)

    # Update patient's latest risk profile
    patient_ref.update({
        "latestRiskScore": record["riskScore"],
        "latestRiskPercentage": record["riskPercentage"],
        "latestRiskBand": record["riskBand"],
        "baselineBiomarkers": record["inputBiomarkers"],
        "updatedAt": record["assessedAt"],
    })
    return record


def save_action_plan(patient_id: str, action_plan_data: Dict[str, Any]) -> Dict[str, Any]:
    db = get_firestore_client()
    plan_id = action_plan_data.get("planId") or str(uuid.uuid4())
    record = {
        "planId": plan_id,
        "patientId": patient_id,
        "assessmentId": str(action_plan_data.get("assessmentId", "")),
        "createdAt": _utc_now_iso(),
        "selectedPathwayTitle": str(action_plan_data.get("selectedPathwayTitle", "Standard Clinical Pathway")),
        "projectedRiskPercentage": float(action_plan_data.get("projectedRiskPercentage", 0.0)),
        "absoluteRiskReduction": float(action_plan_data.get("absoluteRiskReduction", 0.0)),
        "targetBiomarkers": dict(action_plan_data.get("targetBiomarkers", {})),
        "recommendedChanges": list(action_plan_data.get("recommendedChanges", [])),
        "clinicianNotes": str(action_plan_data.get("clinicianNotes", "")).strip(),
        "doctorConfirmed": bool(action_plan_data.get("doctorConfirmed", True)),
    }

    patient_ref = db.collection("patients").document(patient_id)
    patient_ref.collection("actionPlans").document(plan_id).set(record)
    patient_ref.update({"updatedAt": record["createdAt"]})
    return record


def get_patient_history(patient_id: str) -> Dict[str, Any]:
    db = get_firestore_client()
    patient_ref = db.collection("patients").document(patient_id)

    assessments = [
        d.to_dict() for d in patient_ref.collection("assessments").stream() if d.to_dict()
    ]
    assessments.sort(key=lambda a: a.get("assessedAt", ""), reverse=True)

    action_plans = [
        d.to_dict() for d in patient_ref.collection("actionPlans").stream() if d.to_dict()
    ]
    action_plans.sort(key=lambda p: p.get("createdAt", ""), reverse=True)

    return {
        "patientId": patient_id,
        "assessments": assessments,
        "actionPlans": action_plans,
    }


def get_doctor_overview(doctor_id: str) -> Dict[str, Any]:
    patients = list_patients(doctor_id)
    total = len(patients)
    high_risk = sum(1 for p in patients if p.get("latestRiskBand", "").lower() == "high")
    borderline = sum(1 for p in patients if p.get("latestRiskBand", "").lower() == "borderline")
    low_risk = sum(1 for p in patients if p.get("latestRiskBand", "").lower() == "low")
    not_assessed = sum(
        1 for p in patients
        if p.get("latestRiskBand", "").lower() in ("not assessed", "pending")
        or p.get("latestRiskScore") is None
    )

    return {
        "totalPatients": total,
        "highRiskCount": high_risk,
        "borderlineCount": borderline,
        "lowRiskCount": low_risk,
        "notAssessedCount": not_assessed,
    }
