import time
import pytest
import numpy as np
from ml_engine import (
    predict_risk,
    explain_risk,
    generate_recourse,
    validate_patient_dict,
    CANONICAL_FEATURES
)

SAMPLE_HIGH_RISK_PATIENT = {
    "male": 1,
    "age": 62.0,
    "currentSmoker": 1,
    "cigsPerDay": 20.0,
    "BPMeds": 0,
    "prevalentStroke": 0,
    "prevalentHyp": 1,
    "diabetes": 0,
    "totChol": 260.0,
    "sysBP": 160.0,
    "diaBP": 95.0,
    "BMI": 29.0,
    "heartRate": 80.0,
    "glucose": 110.0
}

SAMPLE_LOW_RISK_PATIENT = {
    "male": 0,
    "age": 35.0,
    "currentSmoker": 0,
    "cigsPerDay": 0.0,
    "BPMeds": 0,
    "prevalentStroke": 0,
    "prevalentHyp": 0,
    "diabetes": 0,
    "totChol": 165.0,
    "sysBP": 110.0,
    "diaBP": 72.0,
    "BMI": 21.0,
    "heartRate": 68.0,
    "glucose": 82.0
}


def test_handoff_consecutive_pipeline_latencies():
    """
    Handoff Verification Check:
    Verify that passing a single patient dictionary executes prediction (<5 ms),
    SHAP attribution (<40 ms), and recourse generation (<950 ms) consecutively without errors.
    """
    patient = SAMPLE_HIGH_RISK_PATIENT.copy()

    # 1. Prediction Timing (< 5ms SLA)
    t0 = time.perf_counter()
    pred_res = predict_risk(patient)
    pred_ms = (time.perf_counter() - t0) * 1000.0

    assert "risk_probability" in pred_res
    assert "risk_category" in pred_res
    assert 0.0 <= pred_res["risk_probability"] <= 1.0
    assert pred_ms < 5.0, f"Prediction SLA violated: {pred_ms:.2f}ms >= 5.0ms"

    # 2. SHAP Attribution Timing (< 40ms SLA)
    t1 = time.perf_counter()
    explain_res = explain_risk(patient)
    explain_ms = (time.perf_counter() - t1) * 1000.0

    assert "base_value" in explain_res
    assert "attributions" in explain_res
    assert len(explain_res["attributions"]) == 14
    assert explain_ms < 40.0, f"SHAP attribution SLA violated: {explain_ms:.2f}ms >= 40.0ms"

    # 3. Recourse Generation Timing (< 950ms SLA)
    t2 = time.perf_counter()
    recourse_res = generate_recourse(patient, total_pathways=3)
    recourse_ms = (time.perf_counter() - t2) * 1000.0

    assert "pathways" in recourse_res
    assert recourse_res["pathways_count"] >= 2
    assert recourse_ms < 950.0, f"Recourse generation SLA violated: {recourse_ms:.2f}ms >= 950.0ms"

    print(f"\n[PASS] Handoff Latency Verification:")
    print(f"  - Prediction:         {pred_ms:.2f} ms  (SLA: < 5 ms)")
    print(f"  - SHAP Attribution:   {explain_ms:.2f} ms (SLA: < 40 ms)")
    print(f"  - Recourse Generation:{recourse_ms:.2f} ms (SLA: < 950 ms)")


def test_prediction_fidelity_and_banding():
    """Verify calibrated probability bounds and clinical risk banding."""
    high_pred = predict_risk(SAMPLE_HIGH_RISK_PATIENT)
    low_pred = predict_risk(SAMPLE_LOW_RISK_PATIENT)

    assert high_pred["risk_category"] in ("Borderline", "High")
    assert low_pred["risk_category"] == "Low"
    assert high_pred["risk_probability"] > low_pred["risk_probability"]
    assert high_pred["is_high_risk"] is True or high_pred["risk_category"] == "High"


def test_shap_explanation_ranking_and_consistency():
    """Verify SHAP attributions are correctly ranked and have consistent directions."""
    exp = explain_risk(SAMPLE_HIGH_RISK_PATIENT)
    attrs = exp["attributions"]

    # Verify descending sort by absolute magnitude
    magnitudes = [abs(a["attribution_value"]) for a in attrs]
    assert magnitudes == sorted(magnitudes, reverse=True), "Attributions must be sorted descending by magnitude"

    # Verify attributes schema
    for a in attrs:
        assert a["feature"] in CANONICAL_FEATURES
        assert isinstance(a["display_name"], str)
        assert a["direction"] in ("risk_increasing", "protective")
        if a["attribution_value"] > 0:
            assert a["direction"] == "risk_increasing"
        else:
            assert a["direction"] == "protective"


def test_recourse_pathways_and_deltas():
    """Verify structured counterfactual pathways with baseline-versus-target deltas."""
    rec = generate_recourse(SAMPLE_HIGH_RISK_PATIENT, total_pathways=3)
    pathways = rec["pathways"]

    assert len(pathways) >= 2, "Recourse must return 2-3 pathways"
    base_risk = rec["current_risk"]

    for p in pathways:
        assert p["projected_risk"] < base_risk, "Counterfactual must reduce risk"
        assert p["risk_reduction"] > 0
        assert len(p["deltas"]) > 0, "Pathway must specify actionable deltas"

        # Verify immutable features (age, male) are locked
        target_bio = p["target_biomarkers"]
        assert target_bio["age"] == SAMPLE_HIGH_RISK_PATIENT["age"]
        assert target_bio["male"] == SAMPLE_HIGH_RISK_PATIENT["male"]

        # Verify monotonic disease histories are never reversed
        for mono in ("prevalentStroke", "prevalentHyp", "diabetes"):
            if SAMPLE_HIGH_RISK_PATIENT[mono] == 1:
                assert target_bio[mono] == 1, f"Monotonic feature '{mono}' was illegally reverted"

        for d in p["deltas"]:
            assert "feature" in d
            assert "current_value" in d
            assert "target_value" in d
            assert "delta" in d
            assert "direction" in d
            assert d["direction"] in ("decrease", "increase", "maintain")


def test_fallback_solver_stress_test():
    """
    Task A8 Verification Check:
    Run a stress test that artificially limits genetic iterations to 1;
    verify that the fallback triggers automatically, outputs valid class-flipping counterfactuals,
    and completes in under 200 ms.
    """
    t0 = time.perf_counter()
    res = generate_recourse(SAMPLE_HIGH_RISK_PATIENT, total_pathways=3, genetic_maxiterations=1)
    duration_ms = (time.perf_counter() - t0) * 1000.0

    assert res["fallback_triggered"] is True, "Fallback should have automatically triggered"
    assert res["method_used"] == "random", f"Expected method 'random', got {res['method_used']}"
    assert res["pathways_count"] >= 2, "Fallback must generate at least 2 pathways"
    assert duration_ms < 200.0, f"Fallback execution exceeded 200ms limit: {duration_ms:.2f}ms"

    for p in res["pathways"]:
        assert p["projected_risk"] < res["current_risk"], "Fallback pathway must reduce risk"

    print(f"\n[PASS] Fallback Stress Test (maxiterations=1):")
    print(f"  - Fallback Triggered: {res['fallback_triggered']}")
    print(f"  - Method:             {res['method_used']}")
    print(f"  - Duration:           {duration_ms:.2f} ms (Target: < 200 ms)")


def test_input_payload_validation_rejects_malformed():
    """Verify input dictionary validation rejects malformed payloads."""
    # 1. Missing required keys
    incomplete_patient = SAMPLE_HIGH_RISK_PATIENT.copy()
    del incomplete_patient["sysBP"]
    with pytest.raises(ValueError, match="Missing required clinical features|Missing required biomarkers"):
        predict_risk(incomplete_patient)

    # 2. Non-numeric value
    bad_type_patient = SAMPLE_HIGH_RISK_PATIENT.copy()
    bad_type_patient["glucose"] = "hyperglycemic"
    with pytest.raises(ValueError, match="must be numeric"):
        predict_risk(bad_type_patient)

    # 3. None / NaN values
    none_patient = SAMPLE_HIGH_RISK_PATIENT.copy()
    none_patient["totChol"] = None
    with pytest.raises(ValueError, match="cannot be None"):
        predict_risk(none_patient)

    # 4. Invalid binary value
    bad_binary_patient = SAMPLE_HIGH_RISK_PATIENT.copy()
    bad_binary_patient["diabetes"] = 5
    with pytest.raises(ValueError, match="must be 0 or 1"):
        predict_risk(bad_binary_patient)

    # 5. Non-dictionary input
    with pytest.raises(ValueError, match="must be a dictionary"):
        predict_risk(["not", "a", "dict"])


if __name__ == "__main__":
    print("=" * 65)
    print("RUNNING CARDIORRECOURSE ML ENGINE END-TO-END VERIFICATION (TASK A9)")
    print("=" * 65)

    test_handoff_consecutive_pipeline_latencies()
    test_prediction_fidelity_and_banding()
    test_shap_explanation_ranking_and_consistency()
    test_recourse_pathways_and_deltas()
    test_fallback_solver_stress_test()
    test_input_payload_validation_rejects_malformed()

    print("\n" + "=" * 65)
    print("ALL E2E VERIFICATIONS PASSED! TRACK A IS COMPLETELY FINISHED.")
    print("=" * 65)
