"""
Tests for unified ML engine gateway (Task A9) under pytest test suite.
"""
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ml_engine import (
    predict_risk,
    explain_risk,
    generate_recourse,
    validate_patient_dict,
    CANONICAL_FEATURES
)
import pytest
import time

SAMPLE_HIGH_RISK = {
    "male": 1, "age": 62.0, "currentSmoker": 1, "cigsPerDay": 20.0, "BPMeds": 0,
    "prevalentStroke": 0, "prevalentHyp": 1, "diabetes": 0, "totChol": 260.0,
    "sysBP": 160.0, "diaBP": 95.0, "BMI": 29.0, "heartRate": 80.0, "glucose": 110.0
}

SAMPLE_LOW_RISK = {
    "male": 0, "age": 35.0, "currentSmoker": 0, "cigsPerDay": 0.0, "BPMeds": 0,
    "prevalentStroke": 0, "prevalentHyp": 0, "diabetes": 0, "totChol": 165.0,
    "sysBP": 110.0, "diaBP": 72.0, "BMI": 21.0, "heartRate": 68.0, "glucose": 82.0
}


def test_handoff_consecutive_pipeline_latencies():
    t0 = time.perf_counter()
    pred_res = predict_risk(SAMPLE_HIGH_RISK)
    pred_ms = (time.perf_counter() - t0) * 1000.0

    assert "risk_probability" in pred_res
    assert pred_ms < 5.0

    t1 = time.perf_counter()
    explain_res = explain_risk(SAMPLE_HIGH_RISK)
    explain_ms = (time.perf_counter() - t1) * 1000.0

    assert "attributions" in explain_res
    assert explain_ms < 40.0

    t2 = time.perf_counter()
    recourse_res = generate_recourse(SAMPLE_HIGH_RISK, total_pathways=3)
    recourse_ms = (time.perf_counter() - t2) * 1000.0

    assert "pathways" in recourse_res
    assert recourse_ms < 950.0


def test_prediction_fidelity():
    high_pred = predict_risk(SAMPLE_HIGH_RISK)
    low_pred = predict_risk(SAMPLE_LOW_RISK)
    assert high_pred["risk_probability"] > low_pred["risk_probability"]


def test_shap_explanation_ranking():
    exp = explain_risk(SAMPLE_HIGH_RISK)
    attrs = exp["attributions"]
    magnitudes = [abs(a["attribution_value"]) for a in attrs]
    assert magnitudes == sorted(magnitudes, reverse=True)


def test_fallback_stress_test_under_200ms():
    t0 = time.perf_counter()
    res = generate_recourse(SAMPLE_HIGH_RISK, total_pathways=3, genetic_maxiterations=1)
    duration_ms = (time.perf_counter() - t0) * 1000.0

    assert res["fallback_triggered"] is True
    assert res["method_used"] == "random"
    assert duration_ms < 200.0


def test_input_validation():
    incomplete = SAMPLE_HIGH_RISK.copy()
    del incomplete["sysBP"]
    with pytest.raises(ValueError):
        predict_risk(incomplete)
