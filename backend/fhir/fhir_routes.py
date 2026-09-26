from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, status
from starlette.concurrency import run_in_threadpool

from backend.auth.auth_handler import get_current_doctor
from backend.db.firestore_service import get_patient, get_patient_history
from backend.fhir.fhir_builder import (
    build_fhir_risk_assessment,
    build_fhir_care_plan,
    build_fhir_observation
)

router = APIRouter(prefix="/doctor/patients/{patient_id}/fhir", tags=["HL7 FHIR Interoperability"])


@router.get("/risk-assessment")
async def export_fhir_risk_assessment(
    patient_id: str,
    current_doctor: Dict[str, Any] = Depends(get_current_doctor)
):
    """Exports the patient's latest clinical risk assessment as an HL7 FHIR R4 RiskAssessment resource."""
    patient = await run_in_threadpool(get_patient, current_doctor["doctorId"], patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found or not assigned to your account.")

    history = await run_in_threadpool(get_patient_history, patient_id)
    assessments = history.get("assessments", [])
    if not assessments:
        raise HTTPException(status_code=404, detail="No assessments recorded for this patient.")

    latest_assessment = assessments[0]
    return build_fhir_risk_assessment(latest_assessment, patient_id)


@router.get("/care-plan")
async def export_fhir_care_plan(
    patient_id: str,
    current_doctor: Dict[str, Any] = Depends(get_current_doctor)
):
    """Exports the patient's latest confirmed DiCE action plan as an HL7 FHIR R4 CarePlan resource."""
    patient = await run_in_threadpool(get_patient, current_doctor["doctorId"], patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found or not assigned to your account.")

    history = await run_in_threadpool(get_patient_history, patient_id)
    action_plans = history.get("actionPlans", [])
    if not action_plans:
        raise HTTPException(status_code=404, detail="No confirmed action plan found for this patient.")

    latest_plan = action_plans[0]
    return build_fhir_care_plan(latest_plan, patient_id)


@router.get("/observations")
async def export_fhir_observations(
    patient_id: str,
    current_doctor: Dict[str, Any] = Depends(get_current_doctor)
):
    """Exports the patient's baseline biomarkers as standard HL7 FHIR R4 Observation resources."""
    patient = await run_in_threadpool(get_patient, current_doctor["doctorId"], patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found or not assigned to your account.")

    biomarkers = patient.get("baselineBiomarkers", {})
    observations = []
    for feat, val in biomarkers.items():
        try:
            obs = build_fhir_observation(feat, float(val), patient_id)
            observations.append(obs)
        except Exception:
            continue

    return {
        "resourceType": "Bundle",
        "type": "collection",
        "total": len(observations),
        "entry": [{"resource": obs} for obs in observations]
    }
