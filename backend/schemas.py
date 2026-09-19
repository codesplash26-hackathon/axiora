from pydantic import BaseModel, Field, model_validator
from typing import Literal

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

    model_config = {
        "json_schema_extra": {
            "example": {
                "male": 1,
                "age": 62,
                "currentSmoker": 1,
                "cigsPerDay": 20.0,
                "BPMeds": 0.0,
                "prevalentStroke": 0,
                "prevalentHyp": 1,
                "diabetes": 0,
                "totChol": 255.0,
                "sysBP": 165.0,
                "diaBP": 95.0,
                "BMI": 29.5,
                "heartRate": 82.0,
                "glucose": 88.0,
            }
        }
    }
