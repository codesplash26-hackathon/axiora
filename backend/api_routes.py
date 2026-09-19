from fastapi import APIRouter

from backend.schemas import (
    ExplanationResponse,
    FeatureAttribution,
    FeatureDelta,
    PatientInputSchema,
    PredictionResponse,
    RecoursePathway,
    RecourseResponse,
)

router = APIRouter(tags=["Clinical Assessment"])


@router.post("/predict", response_model=PredictionResponse)
async def predict_risk(patient: PatientInputSchema):
    return PredictionResponse(
        risk_score=0.428,
        risk_percentage=42.8,
        risk_band="High",
        requires_recourse=True,
    )


@router.post("/explain", response_model=ExplanationResponse)
async def explain_risk(patient: PatientInputSchema):
    return ExplanationResponse(
        base_value=0.152,
        risk_score=0.428,
        attributions=[
            FeatureAttribution(
                feature="sysBP",
                display_name="Systolic Blood Pressure",
                attribution_value=0.124,
                patient_value=patient.sysBP,
                direction="risk_increasing",
            ),
            FeatureAttribution(
                feature="cigsPerDay",
                display_name="Cigarettes Per Day",
                attribution_value=0.086,
                patient_value=patient.cigsPerDay,
                direction="risk_increasing",
            ),
            FeatureAttribution(
                feature="totChol",
                display_name="Total Cholesterol",
                attribution_value=0.045,
                patient_value=patient.totChol,
                direction="risk_increasing",
            ),
            FeatureAttribution(
                feature="age",
                display_name="Patient Age",
                attribution_value=0.038,
                patient_value=float(patient.age),
                direction="risk_increasing",
            ),
            FeatureAttribution(
                feature="BMI",
                display_name="Body Mass Index",
                attribution_value=-0.017,
                patient_value=patient.BMI,
                direction="protective",
            ),
        ],
    )


@router.post("/recourse", response_model=RecourseResponse)
async def generate_recourse(patient: PatientInputSchema):
    lifestyle_changes = [
        FeatureDelta(
            feature="cigsPerDay",
            display_name="Cigarettes Per Day",
            baseline_value=patient.cigsPerDay,
            target_value=0.0,
            delta=-patient.cigsPerDay,
            unit="cigs/day",
        ),
        FeatureDelta(
            feature="BMI",
            display_name="Body Mass Index",
            baseline_value=patient.BMI,
            target_value=27.0,
            delta=round(27.0 - patient.BMI, 1),
            unit="kg/m2",
        ),
        FeatureDelta(
            feature="sysBP",
            display_name="Systolic Blood Pressure",
            baseline_value=patient.sysBP,
            target_value=140.0,
            delta=round(140.0 - patient.sysBP, 1),
            unit="mmHg",
        ),
    ]

    medication_changes = [
        FeatureDelta(
            feature="sysBP",
            display_name="Systolic Blood Pressure",
            baseline_value=patient.sysBP,
            target_value=130.0,
            delta=round(130.0 - patient.sysBP, 1),
            unit="mmHg",
        ),
        FeatureDelta(
            feature="totChol",
            display_name="Total Cholesterol",
            baseline_value=patient.totChol,
            target_value=195.0,
            delta=round(195.0 - patient.totChol, 1),
            unit="mg/dL",
        ),
        FeatureDelta(
            feature="BPMeds",
            display_name="Blood Pressure Medication",
            baseline_value=patient.BPMeds,
            target_value=1.0,
            delta=1.0 - patient.BPMeds,
            unit="status",
        ),
    ]

    return RecourseResponse(
        patient_baseline_risk=0.428,
        pathways=[
            RecoursePathway(
                pathway_id=1,
                title="Lifestyle-Led Optimization",
                projected_risk_score=0.185,
                projected_risk_percentage=18.5,
                absolute_risk_reduction=24.3,
                changes=lifestyle_changes,
                full_target_vector={
                    "sysBP": 140.0,
                    "cigsPerDay": 0.0,
                    "BMI": 27.0,
                },
            ),
            RecoursePathway(
                pathway_id=2,
                title="Medication-Led Optimization",
                projected_risk_score=0.162,
                projected_risk_percentage=16.2,
                absolute_risk_reduction=26.6,
                changes=medication_changes,
                full_target_vector={
                    "sysBP": 130.0,
                    "totChol": 195.0,
                    "BPMeds": 1.0,
                },
            ),
        ],
        is_fallback=False,
    )
