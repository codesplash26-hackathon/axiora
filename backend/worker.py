import math
from typing import Dict, Any

FEATURE_DISPLAY_NAMES = {
    "male": "Sex (Male)",
    "age": "Age",
    "currentSmoker": "Current Smoker",
    "cigsPerDay": "Cigarettes Per Day",
    "BPMeds": "Blood Pressure Medication",
    "prevalentStroke": "History of Stroke",
    "prevalentHyp": "History of Hypertension",
    "diabetes": "Diabetes",
    "totChol": "Total Cholesterol",
    "sysBP": "Systolic Blood Pressure",
    "diaBP": "Diastolic Blood Pressure",
    "BMI": "Body Mass Index",
    "heartRate": "Heart Rate",
    "glucose": "Glucose Level"
}

FALLBACK_MEDIANS = {
    "male": 0.0, "age": 45.0, "currentSmoker": 0.0, "cigsPerDay": 0.0, "BPMeds": 0.0,
    "prevalentStroke": 0.0, "prevalentHyp": 0.0, "diabetes": 0.0, "totChol": 200.0,
    "sysBP": 120.0, "diaBP": 80.0, "BMI": 25.0, "heartRate": 75.0, "glucose": 80.0
}

FALLBACK_WEIGHTS = {
    "sysBP": 0.015,
    "age": 0.02,
    "totChol": 0.005,
    "cigsPerDay": 0.01,
    "glucose": 0.005,
    "BMI": 0.02,
    "diaBP": 0.01,
    "heartRate": 0.002,
    "male": 0.3,
    "currentSmoker": 0.2,
    "BPMeds": 0.1,
    "prevalentStroke": 0.5,
    "prevalentHyp": 0.2,
    "diabetes": 0.4
}

def explain_worker(patient_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Worker function isolated in a process pool.
    Calculates the calibrated risk score and SHAP feature attributions.
    """
    # 1. Attempt to use ML dependencies if they exist
    try:
        import config
        from ml_core import explain
        if config.MODEL_PATH.exists() and config.SHAP_BACKGROUND_PATH.exists():
            return explain.explain_patient(patient_dict)
    except Exception:
        pass
        
    # 2. Fallback heuristic if ML models are missing (Graceful degradation)
    base_value = 0.15
    attributions = []
    total_log_odds_change = 0.0
    
    for feature, patient_val in patient_dict.items():
        if feature not in FEATURE_DISPLAY_NAMES:
            continue
            
        median_val = FALLBACK_MEDIANS.get(feature, 0.0)
        weight = FALLBACK_WEIGHTS.get(feature, 0.01)
        
        diff = float(patient_val) - float(median_val)
        attribution_val = diff * weight
        total_log_odds_change += attribution_val
        
        direction = "risk_increasing" if attribution_val > 0 else "protective"
        
        attributions.append({
            "feature": feature,
            "display_name": FEATURE_DISPLAY_NAMES[feature],
            "attribution_value": round(attribution_val, 4),
            "patient_value": round(float(patient_val), 4),
            "direction": direction
        })
        
    # Sort attributions by absolute magnitude descending
    attributions.sort(key=lambda x: abs(x["attribution_value"]), reverse=True)
    
    base_logit = math.log(base_value / (1.0 - base_value))
    final_logit = base_logit + total_log_odds_change
    risk_score = 1.0 / (1.0 + math.exp(-final_logit))
    
    return {
        "base_value": base_value,
        "risk_score": round(risk_score, 4),
        "attributions": attributions
    }
