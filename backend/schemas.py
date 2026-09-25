from pydantic import BaseModel, Field, model_validator
from typing import Literal, List, Dict, Optional

# ==========================================
# 1. Inbound Patient Payload Contract
# ==========================================
class PatientInputSchema(BaseModel):
    male: int = Field(..., ge=0, le=1, description="Biological sex: 1 for male, 0 for female")
    age: float = Field(..., ge=18.0, le=120.0, description="Chronological age in years")
    currentSmoker: int = Field(..., ge=0, le=1, description="Smoking status: 1 if currently smoking, 0 otherwise")
    cigsPerDay: float = Field(default=0.0, ge=0.0, le=70.0, description="Average cigarettes smoked per day")
    BPMeds: float = Field(default=0.0, ge=0.0, le=1.0, description="Currently on blood pressure medication: 1.0 or 0.0")
    prevalentStroke: int = Field(default=0, ge=0, le=1, description="History of stroke: 1 or 0")
    prevalentHyp: int = Field(default=0, ge=0, le=1, description="History of hypertension: 1 or 0")
    diabetes: int = Field(default=0, ge=0, le=1, description="Diagnosed diabetic: 1 or 0")
    totChol: float = Field(..., ge=100.0, le=600.0, description="Total serum cholesterol in mg/dL")
    sysBP: float = Field(..., ge=95.0, le=295.0, description="Systolic blood pressure in mmHg")
    diaBP: float = Field(..., ge=50.0, le=160.0, description="Diastolic blood pressure in mmHg")
    BMI: float = Field(..., ge=15.0, le=55.0, description="Body Mass Index in kg/m^2")
    heartRate: float = Field(..., ge=40.0, le=180.0, description="Resting heart rate in beats per minute")
    glucose: float = Field(..., ge=40.0, le=400.0, description="Fasting blood glucose level in mg/dL")

    @model_validator(mode="after")
    def validate_smoking_coherence(self) -> "PatientInputSchema":
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


# ==========================================
# 4. Outbound Prescriptive Recourse Contract
# ==========================================
class FeatureDelta(BaseModel):
    feature: str = Field(..., description="Biomarker key (e.g., sysBP)")
    display_name: str = Field(..., description="Clinical title (e.g., Systolic Blood Pressure)")
    baseline_value: float = Field(..., description="Original patient value")
    target_value: float = Field(..., description="Recommended counterfactual goal")
    delta: float = Field(..., description="Numerical difference (target - baseline)")
    unit: str = Field(..., description="Measurement unit (e.g., mmHg, mg/dL)")


class RecoursePathway(BaseModel):
    pathway_id: int = Field(..., description="Identifier index (1, 2, or 3)")
    title: str = Field(..., description="Pathway strategy label (e.g., Lifestyle-Led)")
    projected_risk_score: float = Field(..., ge=0.0, le=1.0, description="Predicted risk after completing targets")
    projected_risk_percentage: float = Field(..., ge=0.0, le=100.0, description="Projected risk display percentage")
    absolute_risk_reduction: float = Field(..., description="Absolute drop in percentage points")
    changes: List[FeatureDelta] = Field(..., description="Itemized list of required changes")
    full_target_vector: Dict[str, float] = Field(..., description="Complete feature map with targets applied")


class RecourseResponse(BaseModel):
    patient_baseline_risk: float = Field(..., ge=0.0, le=1.0, description="Initial calibrated risk score")
    pathways: List[RecoursePathway] = Field(..., description="Available counterfactual options")
    is_fallback: bool = Field(default=False, description="True if generated by random fallback solver")

# ==========================================
# 5. Composite Assessment Contract (Task B8)
# ==========================================
class AssessmentResponse(BaseModel):
    prediction: PredictionResponse = Field(..., description="Calibrated risk assessment and triage category")
    explanation: ExplanationResponse = Field(..., description="SHAP feature attributions and risk drivers")
    recourse: RecourseResponse = Field(..., description="Prescriptive counterfactual pathways and target deltas")
    total_latency_ms: float = Field(..., description="Total server-side pipeline execution time in milliseconds")
