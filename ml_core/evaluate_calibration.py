import sys
from pathlib import Path

# Dynamically add project root (Axiora) to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import json
import joblib
import numpy as np
from sklearn.calibration import calibration_curve
from sklearn.metrics import brier_score_loss, roc_auc_score
import config

BRIER_CEILING = 0.13


def compute_ece(y_true: np.ndarray, y_prob: np.ndarray, n_bins: int = 10) -> float:
    """Computes Expected Calibration Error (ECE) across uniform bins."""
    bin_edges = np.linspace(0.0, 1.0, n_bins + 1)
    bin_assignments = np.digitize(y_prob, bin_edges) - 1

    ece = 0.0
    total_samples = len(y_true)

    for i in range(n_bins):
        bin_mask = bin_assignments == i
        bin_size = np.sum(bin_mask)
        if bin_size > 0:
            observed_frequency = np.mean(y_true[bin_mask])
            predicted_confidence = np.mean(y_prob[bin_mask])
            ece += (bin_size / total_samples) * np.abs(observed_frequency - predicted_confidence)

    return float(ece)


def evaluate_calibration():
    # 1. Load calibrated model and evaluation partition
    if not config.MODEL_PATH.exists():
        raise FileNotFoundError(f"Calibrated model missing: {config.MODEL_PATH.resolve()}")
    if not config.SPLIT_DATA_PATH.exists():
        raise FileNotFoundError(f"Split data missing: {config.SPLIT_DATA_PATH.resolve()}")

    model = joblib.load(config.MODEL_PATH)
    splits = joblib.load(config.SPLIT_DATA_PATH)

    X_test = splits["X_test"]
    y_test = np.array(splits["y_test"])

    # 2. Compute probabilities and test metrics
    y_prob = model.predict_proba(X_test)[:, 1]
    brier = float(brier_score_loss(y_test, y_prob))
    roc_auc = float(roc_auc_score(y_test, y_prob))
    ece = compute_ece(y_test, y_prob, n_bins=10)

    # 3. Decile reliability curve breakdown
    prob_true, prob_pred = calibration_curve(y_test, y_prob, n_bins=10, strategy="uniform")

    decile_breakdown = [
        {
            "bin": idx + 1,
            "mean_predicted_prob": round(float(pred), 4),
            "observed_event_rate": round(float(true), 4),
            "gap": round(float(abs(pred - true)), 4),
        }
        for idx, (true, pred) in enumerate(zip(prob_true, prob_pred))
    ]

    print("\n================ Calibration Decile Validation ================")
    print(f"Test Set Brier Score:          {brier:.4f} (Ceiling: < {BRIER_CEILING})")
    print(f"Expected Calibration Error (ECE): {ece:.4f}")
    print(f"Test Set ROC-AUC:              {roc_auc:.4f}")
    print("\n--- Decile Reliability Table ---")
    for d in decile_breakdown:
        print(f"Bin {d['bin']:02d} | Pred: {d['mean_predicted_prob']*100:5.2f}% | True: {d['observed_event_rate']*100:5.2f}% | Gap: {d['gap']*100:5.2f}%")
    print("================================================================")

    # 4. Strict Pass / Fail Check against Clinical Requirements
    assert brier < BRIER_CEILING, f"FAILED: Brier score {brier:.4f} exceeds clinical ceiling {BRIER_CEILING}"

    # 5. Export metrics for system audit
    metrics_path = config.ARTIFACTS_DIR / "calibration_metrics.json"
    metrics_payload = {
        "brier_score": round(brier, 4),
        "brier_ceiling": BRIER_CEILING,
        "ece": round(ece, 4),
        "roc_auc": round(roc_auc, 4),
        "deciles": decile_breakdown,
        "clinical_readiness": "PASSED" if brier < BRIER_CEILING else "FAILED",
    }

    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(metrics_payload, f, indent=2)

    print(f"\nCalibration metrics successfully exported to: {metrics_path}")


if __name__ == "__main__":
    evaluate_calibration()
