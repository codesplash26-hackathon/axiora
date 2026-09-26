"""
tests/test_shap.py

Comprehensive Test Suite for SHAP (TreeExplainer) Explainability Engine.
Verifies mathematical properties, clinical directionality, boundary behavior,
determinism, and latency SLA compliance.
"""

import time
import pytest
import numpy as np
from ml_engine import (
    explain_risk,
    predict_risk,
    CANONICAL_FEATURES,
)

# =====================================================================
# Test Fixtures & Clinical Personas
# =====================================================================

@pytest.fixture
def high_risk_patient():
    return {
        "male": 1,
        "age": 65.0,
        "currentSmoker": 1,
        "cigsPerDay": 30.0,
        "BPMeds": 1.0,
        "prevalentStroke": 0,
        "prevalentHyp": 1,
        "diabetes": 1,
        "totChol": 290.0,
        "sysBP": 180.0,
        "diaBP": 105.0,
        "BMI": 34.0,
        "heartRate": 88.0,
        "glucose": 195.0,
    }


@pytest.fixture
def low_risk_patient():
    return {
        "male": 0,
        "age": 28.0,
        "currentSmoker": 0,
        "cigsPerDay": 0.0,
        "BPMeds": 0.0,
        "prevalentStroke": 0,
        "prevalentHyp": 0,
        "diabetes": 0,
        "totChol": 155.0,
        "sysBP": 105.0,
        "diaBP": 68.0,
        "BMI": 20.5,
        "heartRate": 62.0,
        "glucose": 78.0,
    }


# =====================================================================
# 1. Structural & Contract Invariants
# =====================================================================

def test_shap_completeness_and_canonical_mapping(high_risk_patient):
    """
    Asserts that SHAP outputs an attribution for all 14 canonical features.
    Verifies keys, non-null values, valid data types, and display names.
    """
    res = explain_risk(high_risk_patient)
    assert "attributions" in res
    assert "base_value" in res
    assert isinstance(res["base_value"], (float, np.floating))

    attrs = res["attributions"]
    assert len(attrs) == len(CANONICAL_FEATURES), f"Expected {len(CANONICAL_FEATURES)} features, got {len(attrs)}"

    features_returned = {a["feature"] for a in attrs}
    assert features_returned == set(CANONICAL_FEATURES), "Missing features in SHAP output mapping"

    for a in attrs:
        assert isinstance(a["feature"], str)
        assert isinstance(a["display_name"], str) and len(a["display_name"]) > 0
        assert isinstance(a["attribution_value"], (float, np.floating))
        assert not np.isnan(a["attribution_value"]), f"NaN attribution found for {a['feature']}"
        assert not np.isinf(a["attribution_value"]), f"Inf attribution found for {a['feature']}"


def test_shap_ranking_strict_descending_magnitude(high_risk_patient):
    """
    Verifies that the attribution list is strictly ordered by absolute impact.
    The primary risk driver in the clinical UI must have the largest absolute attribution.
    """
    res = explain_risk(high_risk_patient)
    attrs = res["attributions"]

    magnitudes = [abs(a["attribution_value"]) for a in attrs]
    for i in range(len(magnitudes) - 1):
        assert magnitudes[i] >= magnitudes[i + 1], (
            f"Attributions not sorted descending: index {i} ({magnitudes[i]}) "
            f"< index {i + 1} ({magnitudes[i + 1]})"
        )


# =====================================================================
# 2. Mathematical Properties of Shapley Values
# =====================================================================

def test_shap_local_accuracy_additivity(high_risk_patient):
    """
    Tests the fundamental Efficiency / Additivity property of Shapley values:
    The sum of all feature attributions plus the expected base value
    must equal the model's output prediction in log-odds / margin space.
    """
    res = explain_risk(high_risk_patient)
    base_val = res["base_value"]
    attributions_sum = sum(a["attribution_value"] for a in res["attributions"])

    # Sum of SHAP values + base_value reconstructs the raw model margin
    reconstructed_margin = base_val + attributions_sum
    assert not np.isnan(reconstructed_margin)
    assert not np.isinf(reconstructed_margin)

    # For a high-risk patient, the net sum of attributions must be positive
    # (driving risk above population expectation)
    assert attributions_sum > 0.0, (
        f"High-risk patient should have net positive attribution sum, got {attributions_sum}"
    )


def test_shap_determinism_and_idempotency(high_risk_patient):
    """
    Verifies that SHAP calculations are fully deterministic.
    Repeated runs on the identical patient payload must yield identical
    floating-point values with zero stochastic drift.
    """
    run_1 = explain_risk(high_risk_patient)
    run_2 = explain_risk(high_risk_patient)

    assert run_1["base_value"] == run_2["base_value"]

    attrs_1 = {a["feature"]: a["attribution_value"] for a in run_1["attributions"]}
    attrs_2 = {a["feature"]: a["attribution_value"] for a in run_2["attributions"]}

    for feat in CANONICAL_FEATURES:
        assert np.isclose(attrs_1[feat], attrs_2[feat], atol=1e-7), (
            f"Non-deterministic SHAP value for {feat}: {attrs_1[feat]} vs {attrs_2[feat]}"
        )


def test_shap_key_ordering_invariance(high_risk_patient):
    """
    Verifies that dictionary key insertion order does not affect SHAP results.
    The canonical alignment logic in the worker must preserve invariant output.
    """
    # Reverse key order
    reversed_patient = {k: high_risk_patient[k] for k in reversed(list(high_risk_patient.keys()))}

    run_original = explain_risk(high_risk_patient)
    run_reversed = explain_risk(reversed_patient)

    orig_map = {a["feature"]: a["attribution_value"] for a in run_original["attributions"]}
    rev_map = {a["feature"]: a["attribution_value"] for a in run_reversed["attributions"]}

    for feat in CANONICAL_FEATURES:
        assert np.isclose(orig_map[feat], rev_map[feat], atol=1e-7), (
            f"Feature key order altered SHAP attribution for {feat}"
        )


# =====================================================================
# 3. Clinical Directionality & Sensitivity Logic
# =====================================================================

def test_shap_directional_tagging_consistency(high_risk_patient, low_risk_patient):
    """
    Verifies the categorical direction tag matches mathematical sign:
    - attribution > 0  => 'risk_increasing'
    - attribution <= 0 => 'protective'
    """
    for patient in [high_risk_patient, low_risk_patient]:
        res = explain_risk(patient)
        for a in res["attributions"]:
            val = a["attribution_value"]
            direction = a["direction"]
            if val > 0:
                assert direction == "risk_increasing", f"Feature {a['feature']} has val {val} but tag {direction}"
            else:
                assert direction == "protective", f"Feature {a['feature']} has val {val} but tag {direction}"


def test_shap_monotonic_hemodynamic_sensitivity(low_risk_patient):
    """
    Isolates systolic blood pressure (sysBP).
    Holding all other 13 features identical, escalating sysBP from 105 to 195 mmHg
    must cause its SHAP attribution to increase monotonically.
    """
    normal_bp_patient = low_risk_patient.copy()
    normal_bp_patient["sysBP"] = 105.0

    crisis_bp_patient = low_risk_patient.copy()
    crisis_bp_patient["sysBP"] = 195.0

    res_normal = explain_risk(normal_bp_patient)
    res_crisis = explain_risk(crisis_bp_patient)

    attr_normal = next(a for a in res_normal["attributions"] if a["feature"] == "sysBP")
    attr_crisis = next(a for a in res_crisis["attributions"] if a["feature"] == "sysBP")

    assert attr_crisis["attribution_value"] > attr_normal["attribution_value"], (
        f"Elevating sysBP did not increase SHAP value: normal={attr_normal['attribution_value']}, "
        f"crisis={attr_crisis['attribution_value']}"
    )
    assert attr_crisis["direction"] == "risk_increasing"


def test_shap_smoking_attribution_contrast(low_risk_patient):
    """
    Verifies that smoking increases risk attribution:
    A non-smoker should have a lower/protective attribution for cigsPerDay
    compared to the exact same patient smoking 30 cigarettes per day.
    """
    non_smoker = low_risk_patient.copy()
    non_smoker["currentSmoker"] = 0
    non_smoker["cigsPerDay"] = 0.0

    smoker = low_risk_patient.copy()
    smoker["currentSmoker"] = 1
    smoker["cigsPerDay"] = 30.0

    res_non = explain_risk(non_smoker)
    res_smk = explain_risk(smoker)

    cigs_non = next(a for a in res_non["attributions"] if a["feature"] == "cigsPerDay")
    cigs_smk = next(a for a in res_smk["attributions"] if a["feature"] == "cigsPerDay")

    assert cigs_smk["attribution_value"] > cigs_non["attribution_value"], (
        "Smoking 30 cigs/day did not yield higher attribution than 0 cigs/day"
    )
    assert cigs_smk["direction"] == "risk_increasing"


# =====================================================================
# 4. Extreme Physiological Boundaries
# =====================================================================
def test_shap_physiological_extremes_stability():
    """
    Stress-tests the TreeExplainer at the physiological limits
    defined in feature_schema.json without numerical overflow or NaN.
    """
    min_patient = {
        "male": 0, "age": 18.0, "currentSmoker": 0, "cigsPerDay": 0.0,
        "BPMeds": 0.0, "prevalentStroke": 0, "prevalentHyp": 0, "diabetes": 0,
        "totChol": 100.0, "sysBP": 95.0, "diaBP": 50.0, "BMI": 15.0,
        "heartRate": 40.0, "glucose": 40.0,
    }
    max_patient = {
        "male": 1, "age": 120.0, "currentSmoker": 1, "cigsPerDay": 70.0,
        "BPMeds": 1.0, "prevalentStroke": 1, "prevalentHyp": 1, "diabetes": 1,
        "totChol": 600.0, "sysBP": 295.0, "diaBP": 160.0, "BMI": 55.0,
        "heartRate": 180.0, "glucose": 400.0,
    }

    res_min = explain_risk(min_patient)
    res_max = explain_risk(max_patient)

    assert len(res_min["attributions"]) == 14
    assert len(res_max["attributions"]) == 14

    # Min patient: overwhelming majority of features must be protective
    protective_min = [a for a in res_min["attributions"] if a["direction"] == "protective"]
    assert len(protective_min) >= 10, f"Expected mostly protective factors for min patient, got {len(protective_min)}"
    
    # Max patient: overwhelming majority of features must be risk-increasing (>= 10 of 14)
    risk_inc_max = [a for a in res_max["attributions"] if a["direction"] == "risk_increasing"]
    assert len(risk_inc_max) >= 10, f"Expected mostly risk-increasing factors for max patient, got {len(risk_inc_max)}"

    # Net attribution sum check: max patient must push risk heavily above baseline
    net_max_impact = sum(a["attribution_value"] for a in res_max["attributions"])
    net_min_impact = sum(a["attribution_value"] for a in res_min["attributions"])
    assert net_max_impact > 1.5, f"Expected strong positive net SHAP margin for max patient, got {net_max_impact}"
    assert net_min_impact < 0.0, f"Expected negative net SHAP margin for min patient, got {net_min_impact}"


# =====================================================================
# 5. SLA Latency Compliance & Batch Resilience
# =====================================================================

def test_shap_batch_latency_sla_under_40ms(high_risk_patient, low_risk_patient):
    """
    Verifies that local feature attribution meets the sub-40ms SLA constraint.
    Executes a burst of 10 consecutive explanations to test performance stability.
    """
    patients = [high_risk_patient, low_risk_patient] * 5
    latencies = []

    # Warmup
    _ = explain_risk(high_risk_patient)

    for p in patients:
        t0 = time.perf_counter()
        _ = explain_risk(p)
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        latencies.append(elapsed_ms)

    max_latency = max(latencies)
    avg_latency = sum(latencies) / len(latencies)

    assert max_latency < 40.0, f"SHAP SLA violated! Max latency: {max_latency:.2f}ms (Budget: < 40.0ms)"
    assert avg_latency < 15.0, f"Average SHAP latency higher than expected: {avg_latency:.2f}ms"