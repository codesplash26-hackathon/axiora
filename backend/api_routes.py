import asyncio
from fastapi import APIRouter, HTTPException
import config
from backend.schemas import PatientInputSchema, ExplanationResponse
from backend.pool import run_in_pool
from backend.worker import explain_worker

router = APIRouter()

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
