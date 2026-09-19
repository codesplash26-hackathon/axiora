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

@router.post("/explain", response_model=ExplanationResponse)
async def explain_risk(patient: PatientInputSchema):
    return ExplanationResponse(
        base_value=0.152,
        attributions=[
            {
                "feature": "sysBP",
                "attribution_value": 0.124,
                "direction": "increases_risk",
            },
            {
                "feature": "cigsPerDay",
                "attribution_value": 0.086,
                "direction": "increases_risk",
            },
            {
                "feature": "totChol",
                "attribution_value": 0.045,
                "direction": "increases_risk",
            },
            {
                "feature": "age",
                "attribution_value": 0.038,
                "direction": "increases_risk",
            },
            {
                "feature": "BMI",
                "attribution_value": -0.017,
                "direction": "decreases_risk",
            },
        ],
    )


@router.post("/recourse", response_model=RecourseResponse)
async def generate_recourse(patient: PatientInputSchema):
    return RecourseResponse(
        pathways=[
            {
                "strategy_label": "Lifestyle-Led",
                "projected_risk": 0.185,
                "target_features": {
                    "cigsPerDay": 0.0,
                    "BMI": 29.0,
                    "sysBP": 154.0,
                },
                "deltas": {
                    "cigsPerDay": -20.0,
                    "BMI": -2.4,
                    "sysBP": -14.0,
                },
            },
            {
                "strategy_label": "Medication-Led",
                "projected_risk": 0.172,
                "target_features": {
                    "sysBP": 140.0,
                    "totChol": 239.0,
                    "BPMeds": 1,
                },
                "deltas": {
                    "sysBP": -28.0,
                    "totChol": -45.0,
                    "BPMeds": 1,
                },
            },
        ]
    )