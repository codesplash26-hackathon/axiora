import asyncio
import time
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool

import config
from backend.auth.auth_handler import get_current_doctor
from backend.db.firestore_service import (
    create_patient,
    get_doctor_overview,
    get_patient,
    get_patient_history,
    list_patients,
    save_action_plan,
    save_assessment,
    update_patient,
)
from backend.pool import run_in_pool
from backend.schemas import (
    AssessmentResponse,
    ExplanationResponse,
    PatientInputSchema,
    PredictionResponse,
    RecourseResponse,
)
from backend.worker import explain_worker, predict_worker, recourse_worker

router = APIRouter(prefix="/doctor", tags=["Doctor Portal"])


# ---------------------------------------------------------------------------
# Pydantic Request & Response Models
# ---------------------------------------------------------------------------

class CreatePatientRequest(BaseModel):
    fullName: str = Field(..., min_length=2, description="Patient Full Name")
    age: int = Field(..., ge=18, le=120, description="Age in years")
    sex: str = Field(..., description="Female or Male")
    contactPhone: Optional[str] = Field("", description="Contact phone number")
    baselineBiomarkers: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Initial health metrics")


class UpdatePatientRequest(BaseModel):
    fullName: Optional[str] = None
    age: Optional[int] = None
    sex: Optional[str] = None
    contactPhone: Optional[str] = None
    baselineBiomarkers: Optional[Dict[str, Any]] = None


class DoctorAssessmentRequest(BaseModel):
    biomarkers: Optional[Dict[str, Any]] = Field(
        None, description="Optional override biomarkers for today's visit (defaults to patient's baseline)"
    )


class SaveActionPlanRequest(BaseModel):
    assessmentId: str = Field(..., description="Referenced assessment ID")
    selectedPathwayTitle: str = Field(..., description="Title of selected recourse pathway")
    projectedRiskPercentage: float = Field(..., description="Projected risk score percentage")
    absoluteRiskReduction: float = Field(..., description="Risk reduction percentage")
    targetBiomarkers: Dict[str, Any] = Field(default_factory=dict, description="Target biomarker values")
    recommendedChanges: List[Dict[str, Any]] = Field(default_factory=list, description="List of biomarker adjustments")
    clinicianNotes: Optional[str] = Field("", description="Doctor's clinical notes and prescription instructions")
    doctorConfirmed: bool = Field(True, description="Doctor confirmation flag")


class DoctorAssessmentResponse(AssessmentResponse):
    assessment_id: str
    patient_id: str


# ---------------------------------------------------------------------------
# Cohort & Overview Endpoints
# ---------------------------------------------------------------------------

@router.get("/overview")
async def get_overview(current_doctor: Dict[str, Any] = Depends(get_current_doctor)):
    """Returns clinical cohort statistics (Total, High, Borderline, Low risk counts)."""
    return await run_in_threadpool(get_doctor_overview, current_doctor["doctorId"])


@router.get("/patients")
async def get_patients(
    search: Optional[str] = Query(None, description="Filter by name or patient ID"),
    risk_band: Optional[str] = Query(None, description="Filter by risk band (High, Borderline, Low)"),
    current_doctor: Dict[str, Any] = Depends(get_current_doctor),
):
    """Lists all registered patients managed by the authenticated doctor."""
    return await run_in_threadpool(
        list_patients, current_doctor["doctorId"], search=search, risk_band=risk_band
    )


@router.post("/patients", status_code=status.HTTP_201_CREATED)
async def register_patient(
    payload: CreatePatientRequest,
    current_doctor: Dict[str, Any] = Depends(get_current_doctor),
):
    """Registers a new patient record under the authenticated doctor."""
    record = await run_in_threadpool(create_patient, current_doctor["doctorId"], payload.model_dump())
    return record


@router.get("/patients/{patient_id}")
async def get_patient_profile(
    patient_id: str,
    current_doctor: Dict[str, Any] = Depends(get_current_doctor),
):
    """Retrieves full profile for a specific patient."""
    patient = await run_in_threadpool(get_patient, current_doctor["doctorId"], patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found or not assigned to your account.")
    return patient


@router.put("/patients/{patient_id}")
async def update_patient_profile(
    patient_id: str,
    payload: UpdatePatientRequest,
    current_doctor: Dict[str, Any] = Depends(get_current_doctor),
):
    """Updates baseline patient information."""
    updates = {k: v for k, v in payload.model_dump().items() if v is not None}
    updated = await run_in_threadpool(update_patient, current_doctor["doctorId"], patient_id, updates)
    if not updated:
        raise HTTPException(status_code=404, detail="Patient not found or not assigned to your account.")
    return updated


@router.get("/patients/{patient_id}/history")
async def get_history(
    patient_id: str,
    current_doctor: Dict[str, Any] = Depends(get_current_doctor),
):
    """Returns chronological timeline of previous risk assessments and saved action plans."""
    patient = await run_in_threadpool(get_patient, current_doctor["doctorId"], patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found or not assigned to your account.")
    return await run_in_threadpool(get_patient_history, patient_id)


# ---------------------------------------------------------------------------
# Clinical Assessment & Action Plan Execution
# ---------------------------------------------------------------------------

@router.post("/patients/{patient_id}/assess", response_model=DoctorAssessmentResponse)
async def assess_doctor_patient(
    patient_id: str,
    payload: Optional[DoctorAssessmentRequest] = None,
    current_doctor: Dict[str, Any] = Depends(get_current_doctor),
):
    """
    Runs XGBoost risk prediction, SHAP waterfall explanation, and DiCE recourse pathways
    for a registered patient. Automatically persists the clinical assessment in Firestore.
    """
    patient = await run_in_threadpool(get_patient, current_doctor["doctorId"], patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found or not assigned to your account.")

    # Merge biomarkers: initialize with demographics from patient record
    biomarkers = {
        "age": patient.get("age"),
        "male": 1 if str(patient.get("sex", "")).lower() == "male" else 0,
    }
    biomarkers.update(patient.get("baselineBiomarkers", {}))
    if payload and payload.biomarkers:
        biomarkers.update(payload.biomarkers)

    # Ensure required clinical features are present
    try:
        validated_input = PatientInputSchema(**biomarkers)
    except Exception as e:
        raise HTTPException(
            status_code=422,
            detail=f"Incomplete patient biomarker profile for assessment: {str(e)}",
        )

    start_time = time.perf_counter()
    patient_dict = validated_input.model_dump()

    try:
        pred_task = run_in_pool(predict_worker, patient_dict)
        exp_task = run_in_pool(explain_worker, patient_dict)
        rec_task = run_in_pool(recourse_worker, patient_dict)

        pred_res, exp_res, rec_res = await asyncio.wait_for(
            asyncio.gather(pred_task, exp_task, rec_task),
            timeout=config.SLA_TIMEOUT_SECONDS,
        )

        latency_ms = round((time.perf_counter() - start_time) * 1000.0, 2)

        pred_obj = PredictionResponse(**pred_res)
        exp_obj = ExplanationResponse(**exp_res)
        rec_obj = RecourseResponse(**rec_res)

        # Persist clinical assessment to Firestore non-blockingly
        saved_rec = await run_in_threadpool(
            save_assessment,
            patient_id,
            {
                "riskScore": pred_obj.risk_score,
                "riskPercentage": pred_obj.risk_percentage,
                "riskBand": pred_obj.risk_band,
                "inputBiomarkers": patient_dict,
                "shapAttributions": [a.model_dump() for a in exp_obj.attributions],
                "pipelineLatencyMs": latency_ms,
            }
        )

        return DoctorAssessmentResponse(
            assessment_id=saved_rec["assessmentId"],
            patient_id=patient_id,
            prediction=pred_obj,
            explanation=exp_obj,
            recourse=rec_obj,
            total_latency_ms=latency_ms,
        )
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Clinical assessment SLA timeout exceeded.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Clinical inference error: {str(e)}")


@router.post("/patients/{patient_id}/action-plan")
async def save_patient_plan(
    patient_id: str,
    payload: SaveActionPlanRequest,
    current_doctor: Dict[str, Any] = Depends(get_current_doctor),
):
    """
    Saves a doctor-confirmed clinical action plan with custom notes into the patient's Firestore record.
    """
    patient = await run_in_threadpool(get_patient, current_doctor["doctorId"], patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found or not assigned to your account.")

    plan_record = await run_in_threadpool(save_action_plan, patient_id, payload.model_dump())
    return {
        "status": "success",
        "message": "Clinical action plan successfully saved to patient record.",
        "plan": plan_record,
    }
