import asyncio
from fastapi import APIRouter, HTTPException, status
from backend.schemas import (
    PatientInputSchema,
    PredictionResponse,
    ExplanationResponse,
    RecourseResponse,
)
from backend.pool import run_in_pool
from backend.worker import predict_worker
import config

router = APIRouter()


@router.get("/health", tags=["System"])
async def health_check():
    return {
        "status": "healthy",
        "service": "CardioRecourse API",
        "model_loaded": config.MODEL_PATH.exists(),
    }


@router.post(
    "/predict",
    response_model=PredictionResponse,
    status_code=status.HTTP_200_OK,
    tags=["Clinical Inference"],
)
async def predict_risk(patient: PatientInputSchema):
    """
    Computes calibrated 10-year cardiovascular disease risk.
    Dispatches computation to isolated ProcessPoolExecutor worker.
    Enforces SLA timeout constraint (1.4 seconds).
    """
    try:
        # Offload CPU inference to process pool worker with SLA deadline
        result = await asyncio.wait_for(
            run_in_pool(predict_worker, patient.model_dump()),
            timeout=config.SLA_TIMEOUT_SECONDS,
        )
        return PredictionResponse(**result)

    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=f"Inference exceeded SLA deadline of {config.SLA_TIMEOUT_SECONDS}s",
        )
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Model artifact unavailable: {str(e)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal prediction failure: {str(e)}",
        )


@router.post(
    "/explain",
    response_model=ExplanationResponse,
    status_code=status.HTTP_200_OK,
    tags=["Explainability"],
)
async def explain_risk(patient: PatientInputSchema):
    """Placeholder route for SHAP attribution (Task B6)."""
    return ExplanationResponse(
        base_value=0.15,
        risk_score=0.22,
        attributions=[],
    )


@router.post(
    "/recourse",
    response_model=RecourseResponse,
    status_code=status.HTTP_200_OK,
    tags=["Recourse"],
)
async def generate_recourse(patient: PatientInputSchema):
    """Placeholder route for DiCE counterfactual recourse (Task B7)."""
    return RecourseResponse(
        patient_baseline_risk=0.22,
        pathways=[],
        is_fallback=False,
    )
