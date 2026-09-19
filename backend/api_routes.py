from fastapi import APIRouter
from fastapi.responses import ORJSONResponse

from backend.schemas import (
    ExplanationResponse,
    PatientInputSchema,
    PredictionResponse,
    RecourseResponse,
)

router = APIRouter(default_response_class=ORJSONResponse)