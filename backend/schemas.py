from pydantic import BaseModel, Field, model_validator
from typing import Literal, List

# ==========================================
# 1. Inbound Patient Payload Contract
# ==========================================
class PatientInputSchema(BaseModel):
    # Demographics & Immutable Markers
    male: int = Field(..., ge=0, le=1, description="Biological sex: 1 for male, 0 for female")
    age: int = Field(..., ge=20, le=100, description="Chronological age in years")

    # Medical History & Behavioral Indicators
    currentSmoker: int = Field(..., ge=0, le=1, description="Smoking status: 1 if currently smoking, 0 otherwise")
    cigsPerDay: float = Field(default=0.0, ge=0.0, le=70.0, description="Average cigarettes smoked per day")
    BPMeds: float = Field(default=0.0, ge=0.0, le=1.0, description="Currently on blood pressure medication: 1.0 or 0.0")
    prevalentStroke: int = Field(default=0, ge=0, le=1, description="History of stroke: 1 or 0")
    prevalentHyp: int = Field(default=0, ge=0, le=1, description="History of hypertension: 1 or 0")
    diabetes: int = Field(default=0, ge=0, le=1, description="Diagnosed diabetic: 1 or 0")

    # Actionable Continuous Biomarkers
    totChol: float = Field(..., ge=100.0, le=600.0, description="Total serum cholesterol in mg/dL")
    sysBP: float = Field(..., ge=95.0, le=295.0, description="Systolic blood pressure in mmHg")
    diaBP: float = Field(..., ge=50.0, le=160.0, description="Diastolic blood pressure in mmHg")
    BMI: float = Field(..., ge=15.0, le=55.0, description="Body Mass Index in kg/m^2")
    heartRate: float = Field(..., ge=40.0, le=180.0, description="Resting heart rate in beats per minute")
    glucose: float = Field(..., ge=40.0, le=400.0, description="Fasting blood glucose level in mg/dL")

    @model_validator(mode="after")
    def validate_smoking_coherence(self) -> "PatientInputSchema":
        """Cross-field validation: ensure non-smokers do not have non-zero cigsPerDay."""
        if self.currentSmoker == 0 and self.cigsPerDay > 0:
            raise ValueError("cigsPerDay must be 0 if currentSmoker is 0.")
        if self.currentSmoker == 1 and self.cigsPerDay == 0:
            raise ValueError("cigsPerDay must be greater than 0 if currentSmoker is 1.")
        return self


# ==========================================
# 2. Outbound Prediction Contract
# ==========================================
class PredictionResponse(BaseModel):
    risk_score: float = Field(..., ge=0.0, le=1.0, description="Calibrated 10-year CHD probability")
    risk_percentage: float = Field(..., ge=0.0, le=100.0, description="Display percentage (0 to 100)")
    risk_band: Literal["Low", "Borderline", "High"] = Field(..., description="Triage category")
    requires_recourse: bool = Field(..., description="True if risk >= 20% requiring counterfactual search")


# ==========================================
# 3. Outbound Diagnostic Explanation Contract
# ==========================================
class FeatureAttribution(BaseModel):
    feature: str = Field(..., description="Raw column name (e.g., sysBP)")
    display_name: str = Field(..., description="Plain-language clinical label")
    attribution_value: float = Field(..., description="SHAP attribution value (positive or negative)")
    patient_value: float = Field(..., description="Patient baseline value for this feature")
    direction: Literal["risk_increasing", "protective"] = Field(..., description="Impact direction on risk")

class ExplanationResponse(BaseModel):
    base_value: float = Field(..., description="Population baseline expected risk")
    risk_score: float = Field(..., ge=0.0, le=1.0, description="Individual calibrated risk score")
    attributions: List[FeatureAttribution] = Field(..., description="Ranked feature attributions")
