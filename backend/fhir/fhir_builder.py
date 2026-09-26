from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

# Canonical LOINC Codes for ASCVD Biomarkers
LOINC_MAP = {
    "sysBP": {"code": "8480-6", "display": "Systolic blood pressure", "unit": "mm[Hg]"},
    "diaBP": {"code": "8462-4", "display": "Diastolic blood pressure", "unit": "mm[Hg]"},
    "totChol": {"code": "2093-3", "display": "Cholesterol [Mass/volume] in Serum or Plasma", "unit": "mg/dL"},
    "glucose": {"code": "2339-0", "display": "Glucose [Mass/volume] in Blood", "unit": "mg/dL"},
    "BMI": {"code": "39156-5", "display": "Body mass index (BMI) [Ratio]", "unit": "kg/m2"},
    "heartRate": {"code": "8867-4", "display": "Heart rate", "unit": "/min"},
    "cigsPerDay": {"code": "64234-8", "display": "Cigarettes smoked per day", "unit": "{cigarettes}/d"},
}


def build_fhir_observation(
    feature: str,
    value: float,
    patient_id: str,
    effective_datetime: Optional[str] = None
) -> Dict[str, Any]:
    """Generates an HL7 FHIR R4 Observation resource."""
    meta = LOINC_MAP.get(feature, {"code": "unknown", "display": feature, "unit": ""})
    dt = effective_datetime or datetime.now(timezone.utc).isoformat()
    return {
        "resourceType": "Observation",
        "id": f"obs-{patient_id}-{feature}",
        "status": "final",
        "category": [
            {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                        "code": "vital-signs",
                        "display": "Vital Signs"
                    }
                ]
            }
        ],
        "code": {
            "coding": [
                {
                    "system": "http://loinc.org",
                    "code": meta["code"],
                    "display": meta["display"]
                }
            ],
            "text": meta["display"]
        },
        "subject": {"reference": f"Patient/{patient_id}"},
        "effectiveDateTime": dt,
        "valueQuantity": {
            "value": round(float(value), 1),
            "unit": meta["unit"],
            "system": "http://unitsofmeasure.org"
        }
    }


def build_fhir_risk_assessment(
    assessment_record: Dict[str, Any],
    patient_id: str
) -> Dict[str, Any]:
    """Generates an HL7 FHIR R4 RiskAssessment resource."""
    prob = float(assessment_record.get("riskScore", 0.0))
    band = str(assessment_record.get("riskBand", "Unknown"))
    assessed_at = assessment_record.get("assessedAt", datetime.now(timezone.utc).isoformat())

    return {
        "resourceType": "RiskAssessment",
        "id": assessment_record.get("assessmentId", f"ra-{patient_id}"),
        "status": "final",
        "subject": {"reference": f"Patient/{patient_id}"},
        "occurrenceDateTime": assessed_at,
        "method": {
            "coding": [
                {
                    "system": "http://snomed.info/sct",
                    "code": "70901000087109",
                    "display": "Framingham cardiovascular disease risk score calculation"
                }
            ],
            "text": "CardioRecourse Platt-Calibrated XGBoost ASCVD Classifier"
        },
        "prediction": [
            {
                "outcome": {
                    "coding": [
                        {
                            "system": "http://snomed.info/sct",
                            "code": "49436004",
                            "display": "Coronary heart disease (10-year prospective risk)"
                        }
                    ],
                    "text": "10-Year ASCVD Risk"
                },
                "probabilityDecimal": round(prob, 4),
                "qualitativeRisk": {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/risk-probability",
                            "code": band.lower(),
                            "display": f"{band} Risk"
                        }
                    ],
                    "text": band
                }
            }
        ],
        "note": [
            {
                "text": f"Pipeline Latency: {assessment_record.get('pipelineLatencyMs', 0.0)}ms. SHAP feature attributions calculated in log-odds margin space."
            }
        ]
    }


def build_fhir_care_plan(
    action_plan_record: Dict[str, Any],
    patient_id: str
) -> Dict[str, Any]:
    """Generates an HL7 FHIR R4 CarePlan resource representing DiCE recourse recommendations."""
    plan_id = action_plan_record.get("planId", f"cp-{patient_id}")
    created_at = action_plan_record.get("createdAt", datetime.now(timezone.utc).isoformat())
    activities = []

    for change in action_plan_record.get("recommendedChanges", []):
        feat = change.get("feature", "")
        meta = LOINC_MAP.get(feat, {"code": "unknown", "display": change.get("display_name", feat), "unit": change.get("unit", "")})
        activities.append({
            "detail": {
                "kind": "CommunicationRequest",
                "code": {
                    "coding": [
                        {
                            "system": "http://loinc.org",
                            "code": meta["code"],
                            "display": meta["display"]
                        }
                    ],
                    "text": f"Adjust {change.get('display_name', feat)}"
                },
                "status": "scheduled",
                "doNotPerform": False,
                "description": f"Target {meta['display']} to {change.get('target_value')} {change.get('unit')} (Delta: {change.get('delta')})"
            }
        })

    return {
        "resourceType": "CarePlan",
        "id": plan_id,
        "status": "active",
        "intent": "plan",
        "subject": {"reference": f"Patient/{patient_id}"},
        "period": {
            "start": created_at
        },
        "title": action_plan_record.get("selectedPathwayTitle", "Personalized ASCVD Recourse Plan"),
        "description": f"Prescriptive counterfactual pathway achieving projected risk of {action_plan_record.get('projectedRiskPercentage', 0.0)}% (-{action_plan_record.get('absoluteRiskReduction', 0.0)}% absolute reduction).",
        "activity": activities,
        "note": [
            {"text": action_plan_record.get("clinicianNotes", "")}
        ] if action_plan_record.get("clinicianNotes") else []
    }
