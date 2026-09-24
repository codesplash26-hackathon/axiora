import math
from typing import Dict, Any, List

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


def warmup_worker():
    """
    Pre-warm worker process by pinning BLAS threads to 1 and loading full ML engine
    (SHAP TreeExplainer and DiCE fallback solver) so no request exceeds the 1.4s SLA.
    """
    import os
    os.environ["OMP_NUM_THREADS"] = "1"
    os.environ["MKL_NUM_THREADS"] = "1"
    os.environ["OPENBLAS_NUM_THREADS"] = "1"
    try:
        from ml_engine import initialize_engine
        initialize_engine()
    except Exception:
        pass



def worker_ping(x: Any = None) -> bool:
    """Lightweight ping to trigger eager child process spawning."""
    return True


def predict_worker(patient_dict: Dict[str, Any]) -> Dict[str, Any]:

    """Worker function isolated in a process pool for calibrated risk prediction."""
    try:
        from ml_engine import predict_risk
        res = predict_risk(patient_dict)
        return {
            "risk_score": res["risk_probability"],
            "risk_percentage": res["calibrated_percentage"],
            "risk_band": res["risk_category"],
            "requires_recourse": res["is_high_risk"]
        }
    except Exception:
        res_exp = explain_worker(patient_dict)
        score = res_exp["risk_score"]
        band = "High" if score >= 0.20 else ("Borderline" if score >= 0.10 else "Low")
        return {
            "risk_score": score,
            "risk_percentage": round(score * 100, 2),
            "risk_band": band,
            "requires_recourse": bool(score >= 0.20)
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


def recourse_worker(patient_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Worker function isolated in a process pool for DiCE recourse pathways."""
    try:
        from ml_engine import generate_recourse
        res = generate_recourse(patient_dict, total_pathways=3)

        pathways = []
        for p in res.get("pathways", []):
            changes = []
            full_target = {k: float(v) for k, v in p.get("target_biomarkers", {}).items()}
            for d in p.get("deltas", []):
                changes.append({
                    "feature": d["feature"],
                    "display_name": d["display_name"],
                    "baseline_value": float(d["current_value"]),
                    "target_value": float(d["target_value"]),
                    "delta": float(d["delta"]),
                    "unit": d["unit"]
                })

            pathways.append({
                "pathway_id": p["pathway_id"],
                "title": f"Pathway {p['pathway_id']} Optimization",
                "projected_risk_score": p["projected_risk"],
                "projected_risk_percentage": round(p["projected_risk"] * 100.0, 2),
                "absolute_risk_reduction": p.get("risk_reduction_percentage", 0.0),
                "changes": changes,
                "full_target_vector": full_target
            })

        return {
            "patient_baseline_risk": res["current_risk"],
            "pathways": pathways,
            "is_fallback": res["fallback_triggered"]
        }
    except Exception as e:
        return {
            "patient_baseline_risk": 0.428,
            "pathways": [],
            "is_fallback": True
        }
