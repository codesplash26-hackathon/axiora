import asyncio
from fastapi import APIRouter, HTTPException
import config
from backend.schemas import (
    PatientInputSchema,
    PredictionResponse,
    ExplanationResponse,
    RecourseResponse
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
