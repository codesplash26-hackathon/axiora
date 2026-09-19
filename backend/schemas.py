from pydantic import BaseModel, Field
from typing import List, Literal

class FeatureAttribution(BaseModel):
    feature: str = Field(..., description="Canonical column key, e.g., sysBP, totChol")
    display_name: str = Field(..., description="Clinical label, e.g., Systolic Blood Pressure")
    attribution_value: float = Field(..., description="Raw SHAP contribution value")
    patient_value: float = Field(..., description="Patient's input value")
    direction: Literal["risk_increasing", "protective"] = Field(..., description="Direction of the effect")

class ExplanationResponse(BaseModel):
    base_value: float = Field(..., description="Population baseline risk, e.g., ~0.15")
    risk_score: float = Field(..., description="Individual calibrated risk score in [0.0, 1.0]")
    attributions: List[FeatureAttribution] = Field(..., description="List of feature attributions")

class PatientInputSchema(BaseModel):
    male: int = Field(..., description="0 = Female, 1 = Male")
    age: float = Field(..., description="Age in years")
    currentSmoker: int = Field(..., description="0 = No, 1 = Yes")
    cigsPerDay: float = Field(..., description="Cigarettes per day")
    BPMeds: int = Field(..., description="0 = No, 1 = Yes")
    prevalentStroke: int = Field(..., description="0 = No, 1 = Yes")
    prevalentHyp: int = Field(..., description="0 = No, 1 = Yes")
    diabetes: int = Field(..., description="0 = No, 1 = Yes")
    totChol: float = Field(..., description="Total Cholesterol mg/dL")
    sysBP: float = Field(..., description="Systolic Blood Pressure mmHg")
    diaBP: float = Field(..., description="Diastolic Blood Pressure mmHg")
    BMI: float = Field(..., description="Body Mass Index")
    heartRate: float = Field(..., description="Heart Rate beats/min")
    glucose: float = Field(..., description="Glucose level mg/dL")
