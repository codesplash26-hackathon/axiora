"""
HL7 FHIR R4 Interoperability Subsystem for CardioRecourse CDSS.
Provides standard clinical export resources (RiskAssessment, CarePlan, Observation).
"""
from backend.fhir.fhir_builder import (
    build_fhir_risk_assessment,
    build_fhir_care_plan,
    build_fhir_observation,
    LOINC_MAP
)

__all__ = [
    "build_fhir_risk_assessment",
    "build_fhir_care_plan",
    "build_fhir_observation",
    "LOINC_MAP"
]
