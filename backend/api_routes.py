from fastapi import APIRouter
from fastapi.responses import ORJSONResponse

from backend.schemas import (
    ExplanationResponse,
    PatientInputSchema,
    PredictionResponse,
    RecourseResponse,
)

router = APIRouter(default_response_class=ORJSONResponse)


@router.post("/predict", response_model=PredictionResponse)
async def predict_risk(patient: PatientInputSchema):
    # Mock response matching Persona 1 (Arthur Perera, 62yo)
    return PredictionResponse(
        risk_score=0.428,
        risk_band="High",
    )


    