import sys
from pathlib import Path

# Dynamically add project root (Axiora) to sys.path so config can be imported
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import joblib
import numpy as np
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import brier_score_loss, roc_auc_score
import config


def calibrate_model():
    # 1. Verify required prerequisites from Task A3 exist
    if not config.RAW_MODEL_PATH.exists():
        raise FileNotFoundError(f"Raw model artifact missing: {config.RAW_MODEL_PATH.resolve()}")
    if not config.SPLIT_DATA_PATH.exists():
        raise FileNotFoundError(f"Split data artifact missing: {config.SPLIT_DATA_PATH.resolve()}")

    # 2. Load trained raw XGBoost model and held-out partitions
    raw_model = joblib.load(config.RAW_MODEL_PATH)
    splits = joblib.load(config.SPLIT_DATA_PATH)

    X_calib = splits["X_calib"]
    y_calib = splits["y_calib"]
    X_test = splits["X_test"]
    y_test = splits["y_test"]

    print(f"Calibrating base model over {len(X_calib)} held-out samples...")

    # 3. Fit Platt Sigmoid Scaling
    # In scikit-learn >= 1.6, cv='prefit' is replaced by FrozenEstimator
    try:
        from sklearn.frozen import FrozenEstimator
        calibrated_model = CalibratedClassifierCV(
            estimator=FrozenEstimator(raw_model),
            method="sigmoid",
        )
    except ImportError:
        # Fallback for scikit-learn < 1.6
        calibrated_model = CalibratedClassifierCV(
            estimator=raw_model,
            method="sigmoid",
            cv="prefit",
        )

    calibrated_model.fit(X_calib, y_calib)

    # 4. Compare probability distributions on untouched Test Set
    raw_test_probs = raw_model.predict_proba(X_test)[:, 1]
    calib_test_probs = calibrated_model.predict_proba(X_test)[:, 1]

    raw_brier = brier_score_loss(y_test, raw_test_probs)
    calib_brier = brier_score_loss(y_test, calib_test_probs)
    calib_auc = roc_auc_score(y_test, calib_test_probs)

    print("\n================ Calibration Results ================")
    print(f"Raw Model Test Mean Predicted Risk:        {np.mean(raw_test_probs) * 100:.2f}%")
    print(f"Calibrated Model Test Mean Predicted Risk:   {np.mean(calib_test_probs) * 100:.2f}%")
    print(f"True Test Set Prevalence:                  {np.mean(y_test) * 100:.2f}%")
    print(f"Raw Brier Score (lower is better):         {raw_brier:.4f}")
    print(f"Calibrated Brier Score:                    {calib_brier:.4f}")
    print(f"Calibrated Test ROC-AUC:                   {calib_auc:.4f}")
    print("=====================================================")

    # 5. Persist the production calibrated model to config.MODEL_PATH
    joblib.dump(calibrated_model, config.MODEL_PATH)
    print(f"\nProduction calibrated model exported to: {config.MODEL_PATH}")


if __name__ == "__main__":
    calibrate_model()
