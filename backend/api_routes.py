import asyncio
import time
from fastapi import APIRouter, HTTPException
import config
from backend.schemas import (
    PatientInputSchema,
    PredictionResponse,
    ExplanationResponse,
    RecourseResponse,
    AssessmentResponse,
)
from backend.pool import run_in_pool
from backend.worker import predict_worker, explain_worker, recourse_worker

router = APIRouter(tags=["Clinical Assessment"])


@router.post("/predict", response_model=PredictionResponse)
async def predict_patient_risk(patient: PatientInputSchema):
    try:
        result = await asyncio.wait_for(
            run_in_pool(predict_worker, patient.model_dump()),
            timeout=config.SLA_TIMEOUT_SECONDS
        )
        return PredictionResponse(**result)
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Prediction SLA timeout exceeded.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/explain", response_model=ExplanationResponse)
async def explain_patient_risk(patient: PatientInputSchema):
    try:
        result = await asyncio.wait_for(
            run_in_pool(explain_worker, patient.model_dump()),
            timeout=config.SLA_TIMEOUT_SECONDS
        )
        return ExplanationResponse(**result)
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Inference SLA timeout exceeded.")
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=f"ML artifacts missing: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/recourse", response_model=RecourseResponse)
async def generate_patient_recourse(patient: PatientInputSchema):
    try:
        result = await asyncio.wait_for(
            run_in_pool(recourse_worker, patient.model_dump()),
            timeout=config.SLA_TIMEOUT_SECONDS
        )
        return RecourseResponse(**result)
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Recourse generation SLA timeout exceeded.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/assess", response_model=AssessmentResponse)
async def assess_patient(patient: PatientInputSchema):
    """
    Executes prediction, SHAP explanation, and counterfactual recourse in parallel.
    Enforces the strict 1.4-second SLA deadline across the combined workload.
    """
    start_time = time.perf_counter()
    patient_dict = patient.model_dump()

    try:
        pred_task = run_in_pool(predict_worker, patient_dict)
        exp_task = run_in_pool(explain_worker, patient_dict)
        rec_task = run_in_pool(recourse_worker, patient_dict)

        pred_res, exp_res, rec_res = await asyncio.wait_for(
            asyncio.gather(pred_task, exp_task, rec_task),
            timeout=config.SLA_TIMEOUT_SECONDS
        )

        latency_ms = round((time.perf_counter() - start_time) * 1000.0, 2)

        return AssessmentResponse(
            prediction=PredictionResponse(**pred_res),
            explanation=ExplanationResponse(**exp_res),
            recourse=RecourseResponse(**rec_res),
            total_latency_ms=latency_ms,
        )
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Assessment SLA timeout exceeded.")
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=f"ML artifacts missing: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
