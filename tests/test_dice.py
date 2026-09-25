"""
tests/test_dice.py

Comprehensive Test Suite for Prescriptive Recourse (DiCE) & Heuristic Fallback Engine.
Thoroughly verifies mathematical risk reduction, clinical immutability,
monotonicity, physiological boundaries, pathway diversity, and SLA constraints.
"""

import json
import time
import pytest
import numpy as np
from pathlib import Path

import config
from ml_engine import (
    generate_recourse,
    predict_risk,
    CANONICAL_FEATURES,
)
from ml_core.dice_fallback_solver import (
    search_recourse_with_fallback,
    init_fallback_solver,
)


# =====================================================================
# Fixtures & Clinical Personas
# =====================================================================

@pytest.fixture(scope="module")
def feature_schema():
    """Loads the single source of truth for feature tiers and bounds."""
    assert config.FEATURE_SCHEMA_PATH.exists(), f"Schema missing at {config.FEATURE_SCHEMA_PATH}"
    with open(config.FEATURE_SCHEMA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def high_risk_patient():
    """Representative high-risk hypertensive smoker."""
    return {
        "male": 1,
        "age": 62.0,
        "currentSmoker": 1,
        "cigsPerDay": 20.0,
        "BPMeds": 0.0,
        "prevalentStroke": 0,
        "prevalentHyp": 1,
        "diabetes": 0,
        "totChol": 260.0,
        "sysBP": 160.0,
        "diaBP": 95.0,
        "BMI": 29.0,
        "heartRate": 80.0,
        "glucose": 110.0,
    }


@pytest.fixture
def extreme_comorbid_patient():
    """Elderly diabetic patient with chronic cardiovascular history."""
    return {
        "male": 1,
        "age": 68.0,
        "currentSmoker": 1,
        "cigsPerDay": 30.0,
        "BPMeds": 1.0,
        "prevalentStroke": 1,
        "prevalentHyp": 1,
        "diabetes": 1,
        "totChol": 285.0,
        "sysBP": 185.0,
        "diaBP": 105.0,
        "BMI": 33.2,
        "heartRate": 88.0,
        "glucose": 190.0,
    }


@pytest.fixture
def low_risk_patient():
    """Healthy young control (already below intervention threshold)."""
    return {
        "male": 0,
        "age": 35.0,
        "currentSmoker": 0,
        "cigsPerDay": 0.0,
        "BPMeds": 0.0,
        "prevalentStroke": 0,
        "prevalentHyp": 0,
        "diabetes": 0,
        "totChol": 165.0,
        "sysBP": 110.0,
        "diaBP": 72.0,
        "BMI": 21.0,
        "heartRate": 68.0,
        "glucose": 82.0,
    }


# =====================================================================
# 1. Structural Contracts & Output Invariants
# =====================================================================

def test_recourse_output_contract_completeness(high_risk_patient):
    """
    Verifies that generate_recourse returns all required top-level
    metadata, pathway payloads, and execution metrics.
    """
    res = generate_recourse(high_risk_patient, total_pathways=3)

    assert "current_risk" in res
    assert "pathways" in res
    assert "pathways_count" in res
    assert "fallback_triggered" in res
    assert "method_used" in res
    assert "execution_time_ms" in res

    assert isinstance(res["current_risk"], float)
    assert 0.0 <= res["current_risk"] <= 1.0
    assert res["pathways_count"] >= 2, "Recourse must generate at least 2 distinct pathways"
    assert len(res["pathways"]) == res["pathways_count"]


def test_recourse_pathway_internal_schema(high_risk_patient):
    """
    Verifies the internal schema of every individual counterfactual pathway:
    projected risk, absolute reduction, target biomarkers, and delta list.
    """
    res = generate_recourse(high_risk_patient, total_pathways=3)

    for idx, p in enumerate(res["pathways"]):
        assert "projected_risk" in p, f"Pathway {idx} missing projected_risk"
        assert "risk_reduction" in p, f"Pathway {idx} missing risk_reduction"
        assert "target_biomarkers" in p, f"Pathway {idx} missing target_biomarkers"
        assert "deltas" in p, f"Pathway {idx} missing deltas"

        # Check biomarker dictionary keys
        target = p["target_biomarkers"]
        assert set(target.keys()) == set(CANONICAL_FEATURES), f"Pathway {idx} biomarkers do not match canonical schema"


# =====================================================================
# 2. Mathematical Rigor & Directional Invariants
# =====================================================================

def test_recourse_strict_risk_reduction(high_risk_patient):
    """
    Mathematical Invariant:
    Every proposed counterfactual pathway MUST strictly reduce risk:
    projected_risk < current_risk and risk_reduction > 0.
    """
    res = generate_recourse(high_risk_patient, total_pathways=3)
    base_risk = res["current_risk"]

    for idx, p in enumerate(res["pathways"]):
        proj_risk = p["projected_risk"]
        reduction = p["risk_reduction"]

        assert proj_risk < base_risk, (
            f"Pathway {idx} failed to reduce risk: projected ({proj_risk:.4f}) >= baseline ({base_risk:.4f})"
        )
        assert np.isclose(reduction, base_risk - proj_risk, atol=1e-4), (
            f"Pathway {idx} risk_reduction mismatch: reported {reduction:.4f} vs calculated {base_risk - proj_risk:.4f}"
        )


def test_actionable_deltas_mathematical_consistency(high_risk_patient):
    """
    Asserts delta arithmetic and direction tag consistency:
    - delta = target_value - current_value
    - target < current => 'decrease'
    - target > current => 'increase'
    - target == current => 'maintain'
    """
    res = generate_recourse(high_risk_patient, total_pathways=3)

    for p in res["pathways"]:
        assert len(p["deltas"]) > 0, "Counterfactual pathway must propose at least one actionable change"
        for d in p["deltas"]:
            feat = d["feature"]
            curr = d["current_value"]
            targ = d["target_value"]
            delta = d["delta"]
            direction = d["direction"]

            # Exact delta calculation check
            assert np.isclose(delta, targ - curr, atol=1e-3), (
                f"Delta mismatch for {feat}: delta ({delta}) != target ({targ}) - current ({curr})"
            )

            # Directional label audit
            if targ < curr:
                assert direction == "decrease", f"Expected 'decrease' for {feat}, got {direction}"
            elif targ > curr:
                assert direction == "increase", f"Expected 'increase' for {feat}, got {direction}"
            else:
                assert direction == "maintain", f"Expected 'maintain' for {feat}, got {direction}"


# =====================================================================
# 3. Clinical Immutability & Monotonicity Constraints
# =====================================================================

def test_clinical_immutability_fixed_features(high_risk_patient, extreme_comorbid_patient):
    """
    Clinical Invariant (Zero-Tolerance):
    Immutable features (age, male) MUST NEVER be modified by any pathway.
    Algorithms cannot propose changing biological sex or reversing chronological age.
    """
    for patient in [high_risk_patient, extreme_comorbid_patient]:
        res = generate_recourse(patient, total_pathways=3)
        for p in res["pathways"]:
            target = p["target_biomarkers"]
            assert target["age"] == patient["age"], (
                f"ILLEGAL MUTATION: Age modified from {patient['age']} to {target['age']}"
            )
            assert target["male"] == patient["male"], (
                f"ILLEGAL MUTATION: Biological sex modified from {patient['male']} to {target['male']}"
            )


def test_clinical_monotonicity_chronic_disease_history(extreme_comorbid_patient):
    """
    Monotonicity Invariant:
    A patient with a documented history of diabetes, hypertension, or stroke
    cannot have their diagnostic history erased (1.0 -> 0.0 is medically invalid).
    """
    res = generate_recourse(extreme_comorbid_patient, total_pathways=3)

    for p in res["pathways"]:
        target = p["target_biomarkers"]
        for mono_feat in ["prevalentStroke", "prevalentHyp", "diabetes"]:
            if extreme_comorbid_patient[mono_feat] == 1:
                assert target[mono_feat] == 1, (
                    f"ILLEGAL DISEASE REVERSAL: Monotonic feature '{mono_feat}' was reverted to 0"
                )


# =====================================================================
# 4. Physiological Feasibility & Behavioral Coherence
# =====================================================================

def test_physiological_clamping_bounds_compliance(high_risk_patient, feature_schema):
    """
    Ensures that all suggested target values remain strictly within the
    clinically safe, valid ranges defined in feature_schema.json.
    (e.g., DiCE must never propose lowering sysBP below 95 mmHg or BMI below 15).
    """
    res = generate_recourse(high_risk_patient, total_pathways=3)

    default_bounds = {
        "sysBP": [95.0, 295.0],
        "diaBP": [50.0, 160.0],
        "totChol": [100.0, 600.0],
        "BMI": [15.0, 55.0],
        "heartRate": [40.0, 180.0],
        "glucose": [40.0, 400.0],
        "cigsPerDay": [0.0, 70.0],
        "age": [18.0, 120.0],
        "male": [0.0, 1.0],
        "BPMeds": [0.0, 1.0],
        "prevalentStroke": [0.0, 1.0],
        "prevalentHyp": [0.0, 1.0],
        "diabetes": [0.0, 1.0],
        "currentSmoker": [0.0, 1.0],
    }

    permitted_ranges = {}
    try:
        from dice_setup import get_permitted_range
        pr = get_permitted_range()
        if isinstance(pr, dict):
            permitted_ranges = pr
    except Exception:
        pass

    for p in res["pathways"]:
        target = p["target_biomarkers"]
        for feat, target_val in target.items():
            bounds = permitted_ranges.get(feat) or default_bounds.get(feat)
            if bounds and isinstance(bounds, (list, tuple)) and len(bounds) == 2:
                try:
                    min_val = float(bounds[0])
                    max_val = float(bounds[1])
                    val = float(target_val)
                    assert min_val <= val <= max_val, (
                        f"Target value for {feat} ({val}) violated physiological bounds [{min_val}, {max_val}]"
                    )
                except (ValueError, TypeError):
                    continue


def test_smoking_behavioral_coherence(high_risk_patient):
    """
    Behavioral Coherence Check:
    If a pathway recommends smoking cessation (cigsPerDay -> 0.0),
    currentSmoker status must not remain active smoker (must align to 0).
    """
    res = generate_recourse(high_risk_patient, total_pathways=3)

    for p in res["pathways"]:
        target = p["target_biomarkers"]
        if target["cigsPerDay"] == 0.0:
            assert target["currentSmoker"] == 0, (
                "Coherence violation: cigsPerDay is 0.0, but currentSmoker remained 1"
            )


# =====================================================================
# 5. Pathway Diversity & Alternative Interventions
# =====================================================================

def test_recourse_pathway_diversity(high_risk_patient):
    """
    Diversity Requirement:
    DiCE must generate distinct, non-duplicate clinical recommendations.
    No two returned pathways should propose the exact same target biomarker vector.
    """
    res = generate_recourse(high_risk_patient, total_pathways=3)
    pathways = res["pathways"]

    vectors = []
    for p in pathways:
        vec = tuple(round(p["target_biomarkers"][f], 3) for f in CANONICAL_FEATURES)
        vectors.append(vec)

    unique_vectors = set(vectors)
    assert len(unique_vectors) == len(pathways), (
        f"Duplicate pathways generated: {len(unique_vectors)} unique out of {len(pathways)}"
    )


# =====================================================================
# 6. Fallback Triggering & SLA Conformance
# =====================================================================

def test_genetic_exhaustion_fallback_recovery(high_risk_patient):
    """
    Stress-tests the algorithmic fallback watchdog:
    By artificially limiting genetic iterations to 1, we force DiCE to fail convergence.
    Verifies that the heuristic fallback triggers automatically, outputs valid
    risk-reducing pathways, and finishes in under 200 ms.
    """
    t0 = time.perf_counter()
    res = generate_recourse(high_risk_patient, total_pathways=3, genetic_maxiterations=1)
    duration_ms = (time.perf_counter() - t0) * 1000.0

    assert res["fallback_triggered"] is True, "Fallback solver did not trigger under iteration exhaustion"
    assert res["method_used"] == "random", f"Expected method 'random', got {res['method_used']}"
    assert res["pathways_count"] >= 2, "Fallback failed to output at least 2 pathways"
    assert duration_ms < 200.0, f"Fallback execution too slow: {duration_ms:.2f}ms >= 200.0ms"

    for p in res["pathways"]:
        assert p["projected_risk"] < res["current_risk"], "Fallback pathway failed to reduce risk"


def test_direct_heuristic_fallback_solver(extreme_comorbid_patient):
    """
    Directly invokes search_recourse_with_fallback to verify deterministic
    sub-100ms performance on severe clinical presentations.
    """
    t0 = time.perf_counter()
    res = search_recourse_with_fallback(extreme_comorbid_patient, total_CFs=3, genetic_maxiterations=1)
    duration_ms = (time.perf_counter() - t0) * 1000.0

    assert res["fallback_triggered"] is True
    assert res["execution_time_ms"] < 100.0, f"Internal fallback timing exceeded: {res['execution_time_ms']}ms"
    assert duration_ms < 150.0, f"Total direct fallback runtime exceeded 150ms: {duration_ms:.2f}ms"

    # Identify the returned raw counterfactual container (cfs, cfs_df, counterfactuals, etc.)
    cf_key = next((k for k in ["cfs", "cfs_df", "counterfactuals", "cf_list", "cfs_found", "pathways"] if k in res), None)
    assert cf_key is not None, f"No counterfactual key found in solver output. Available keys: {list(res.keys())}"
    assert len(res[cf_key]) >= 1, f"Expected counterfactual rows in res['{cf_key}']"


def test_recourse_execution_sla_under_950ms(high_risk_patient):
    """
    End-to-End SLA Benchmark:
    Verifies that standard DiCE recourse generation completes well within
    the allocated sub-950ms recourse latency budget.
    """
    # Warmup
    _ = generate_recourse(high_risk_patient, total_pathways=2)

    t0 = time.perf_counter()
    res = generate_recourse(high_risk_patient, total_pathways=3)
    duration_ms = (time.perf_counter() - t0) * 1000.0

    assert duration_ms < 950.0, (
        f"Recourse SLA violated! Completed in {duration_ms:.2f}ms (Budget: < 950.0ms)"
    )
    assert res["pathways_count"] >= 2


def test_heuristic_fallback_biomarker_non_worsening_low_baseline():
    """
    Clinical Safety Test:
    Patients with already-low baseline biomarkers (e.g. totChol 145, sysBP 112)
    must NEVER have those biomarkers increased/worsened in clinical fallback pathways.
    """
    from ml_core.ml_engine import _generate_clinical_fallback_candidates

    low_baseline = {
        "male": 0,
        "age": 45.0,
        "currentSmoker": 0,
        "cigsPerDay": 0.0,
        "BPMeds": 0,
        "prevalentStroke": 0,
        "prevalentHyp": 0,
        "diabetes": 0,
        "totChol": 145.0,
        "sysBP": 112.0,
        "diaBP": 72.0,
        "BMI": 20.5,
        "heartRate": 58.0,
        "glucose": 78.0
    }

    candidates = _generate_clinical_fallback_candidates(low_baseline)
    assert len(candidates) >= 2

    biomarkers = ["sysBP", "diaBP", "totChol", "BMI", "glucose", "heartRate", "cigsPerDay"]
    for i, cand in enumerate(candidates):
        for feat in biomarkers:
            assert cand[feat] <= low_baseline[feat], (
                f"Candidate {i} worsened {feat}: baseline={low_baseline[feat]}, candidate={cand[feat]}"
            )


def test_permitted_range_thread_safety_direct_patient_dict():
    """
    Concurrency Safety Test:
    get_permitted_range accepts patient_dict directly and clamps boundaries
    without mutating or requiring global active patient context.
    """
    from ml_core.dice_setup import get_permitted_range, set_active_patient_context

    # Ensure no global context is active
    set_active_patient_context(None)

    patient_a = {"sysBP": 130.0, "totChol": 190.0, "cigsPerDay": 10.0, "heartRate": 65.0}
    patient_b = {"sysBP": 160.0, "totChol": 260.0, "cigsPerDay": 25.0, "heartRate": 85.0}

    pr_a = get_permitted_range(patient_a)
    pr_b = get_permitted_range(patient_b)

    assert pr_a["sysBP"][1] == 130.0
    assert pr_b["sysBP"][1] == 160.0
    assert pr_a["totChol"][1] == 190.0
    assert pr_b["totChol"][1] == 260.0