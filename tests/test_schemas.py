import pytest
from pydantic import ValidationError
from backend.schemas import (
    PatientInputSchema,
    PredictionResponse,
    ExplanationResponse,
    FeatureAttribution,
    RecourseResponse,
    RecoursePathway,
    FeatureDelta,
)

@pytest.fixture
def valid_patient_payload():
    return {
        "male": 1,
        "age": 52,
        "currentSmoker": 1,
        "cigsPerDay": 15.0,
        "BPMeds": 0.0,
        "prevalentStroke": 0,
        "prevalentHyp": 1,
        "diabetes": 0,
        "totChol": 240.0,
        "sysBP": 150.0,
        "diaBP": 92.0,
        "BMI": 28.4,
        "heartRate": 75.0,
        "glucose": 85.0,
    }

def test_valid_patient_schema(valid_patient_payload):
    patient = PatientInputSchema(**valid_patient_payload)
    assert patient.age == 52
    assert patient.sysBP == 150.0
    assert patient.currentSmoker == 1

def test_sysbp_out_of_bounds_fails(valid_patient_payload):
    payload = valid_patient_payload.copy()
    payload["sysBP"] = 450.0  # Exceeds maximum biological ceiling (295 mmHg)
    with pytest.raises(ValidationError):
        PatientInputSchema(**payload)

def test_smoking_coherence_non_smoker_with_cigarettes(valid_patient_payload):
    payload = valid_patient_payload.copy()
    payload["currentSmoker"] = 0
    payload["cigsPerDay"] = 10.0  # Incoherent state
    with pytest.raises(ValidationError, match="cigsPerDay must be 0 if currentSmoker is 0"):
        PatientInputSchema(**payload)

def test_smoking_coherence_smoker_with_zero_cigarettes(valid_patient_payload):
    payload = valid_patient_payload.copy()
    payload["currentSmoker"] = 1
    payload["cigsPerDay"] = 0.0  # Incoherent state
    with pytest.raises(ValidationError, match="cigsPerDay must be greater than 0 if currentSmoker is 1"):
        PatientInputSchema(**payload)

def test_prediction_response_schema():
    pred = PredictionResponse(
        risk_score=0.31,
        risk_percentage=31.0,
        risk_band="High",
        requires_recourse=True,
    )
    assert pred.risk_band == "High"
    assert pred.requires_recourse is True

def test_recourse_response_schema():
    delta = FeatureDelta(
        feature="sysBP",
        display_name="Systolic Blood Pressure",
        baseline_value=160.0,
        target_value=130.0,
        delta=-30.0,
        unit="mmHg",
    )
    pathway = RecoursePathway(
        pathway_id=1,
        title="Lifestyle-Led",
        projected_risk_score=0.14,
        projected_risk_percentage=14.0,
        absolute_risk_reduction=45.0,
        changes=[delta],
        full_target_vector={"sysBP": 130.0},
    )
    response = RecourseResponse(
        patient_baseline_risk=0.59,
        pathways=[pathway],
        is_fallback=False,
    )
    assert len(response.pathways) == 1
    assert response.pathways[0].changes[0].delta == -30.0
