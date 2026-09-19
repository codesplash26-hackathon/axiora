import joblib
import numpy as np
import pandas as pd
import pytest
import config


@pytest.fixture(scope="module")
def model():
    assert config.MODEL_PATH.exists(), f"Model artifact missing at {config.MODEL_PATH}"
    return joblib.load(config.MODEL_PATH)


@pytest.fixture(scope="module")
def split_data():
    assert config.SPLIT_DATA_PATH.exists(), f"Split data missing at {config.SPLIT_DATA_PATH}"
    return joblib.load(config.SPLIT_DATA_PATH)


@pytest.fixture
def low_risk_patient(split_data):
    return pd.DataFrame(
        [
            {
                "male": 0,
                "age": 35.0,
                "currentSmoker": 0,
                "cigsPerDay": 0.0,
                "BPMeds": 0.0,
                "prevalentStroke": 0,
                "prevalentHyp": 0,
                "diabetes": 0,
                "totChol": 160.0,
                "sysBP": 110.0,
                "diaBP": 72.0,
                "BMI": 21.5,
                "heartRate": 65.0,
                "glucose": 80.0,
            }
        ],
        columns=split_data["feature_names"],
    )


@pytest.fixture
def high_risk_patient(split_data):
    return pd.DataFrame(
        [
            {
                "male": 1,
                "age": 68.0,
                "currentSmoker": 1,
                "cigsPerDay": 30.0,
                "BPMeds": 1.0,
                "prevalentStroke": 0,
                "prevalentHyp": 1,
                "diabetes": 1,
                "totChol": 285.0,
                "sysBP": 185.0,
                "diaBP": 105.0,
                "BMI": 33.2,
                "heartRate": 88.0,
                "glucose": 190.0,
            }
        ],
        columns=split_data["feature_names"],
    )


def test_model_loading_and_interface(model):
    assert hasattr(model, "predict_proba"), "Calibrated model must implement predict_proba"
    assert hasattr(model, "predict"), "Calibrated model must implement predict"


def test_probability_bounds_and_normalization(model, low_risk_patient):
    probs = model.predict_proba(low_risk_patient)
    assert probs.shape == (1, 2)
    assert 0.0 <= probs[0, 0] <= 1.0
    assert 0.0 <= probs[0, 1] <= 1.0
    assert np.isclose(probs[0, 0] + probs[0, 1], 1.0, atol=1e-5)


def test_clinical_risk_contrast(model, low_risk_patient, high_risk_patient):
    low_prob = model.predict_proba(low_risk_patient)[0, 1]
    high_prob = model.predict_proba(high_risk_patient)[0, 1]

    # Clinical sanity: High-risk patient must score strictly higher than low-risk
    assert high_prob > low_prob
    # Margin check: High risk should be at least 2.5x higher than low risk
    assert high_prob >= (low_prob * 2.5)


def test_monotonic_systolic_bp_sensitivity(model, low_risk_patient):
    # Assess baseline risk at normal blood pressure (110 mmHg)
    baseline_prob = model.predict_proba(low_risk_patient)[0, 1]

    # Elevate systolic BP to severe hypertension (180 mmHg) holding everything else constant
    escalated_patient = low_risk_patient.copy()
    escalated_patient.loc[0, "sysBP"] = 180.0
    escalated_prob = model.predict_proba(escalated_patient)[0, 1]

    assert escalated_prob > baseline_prob, "Escalating systolic BP must increase predicted CHD risk"


def test_full_test_partition_inference(model, split_data):
    X_test = split_data["X_test"]
    probs = model.predict_proba(X_test)[:, 1]

    assert len(probs) == len(X_test)
    assert not np.isnan(probs).any(), "Model returned NaN probabilities on test set"
    assert (probs >= 0.0).all() and (probs <= 1.0).all(), "All probabilities must be in [0.0, 1.0]"

    # Population calibration bounds: mean predicted risk should align near true prevalence (~12% - 18%)
    mean_risk = np.mean(probs)
    assert 0.10 <= mean_risk <= 0.20, f"Mean risk {mean_risk:.4f} drifted outside acceptable prevalence window"
