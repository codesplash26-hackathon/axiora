import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import joblib
import numpy as np
import shap
import config


def generate_shap_background(k: int = 50) -> np.ndarray:
    """
    Generate a compact k-means background dataset for SHAP TreeExplainer
    to guarantee sub-40ms local feature attribution.
    """
    if not config.SPLIT_DATA_PATH.exists():
        raise FileNotFoundError(f"Data partitions missing at {config.SPLIT_DATA_PATH}")

    splits = joblib.load(config.SPLIT_DATA_PATH)
    X_train = splits["X_train"]

    print(f"Computing K-Means medoid background (k={k}) over {len(X_train)} training records...")
    background_summary = shap.kmeans(X_train, k)
    background_data = np.asarray(background_summary.data, dtype=np.float32)

    config.ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    np.save(config.SHAP_BACKGROUND_PATH, background_data)
    print(f"SHAP background array saved: {config.SHAP_BACKGROUND_PATH} (shape: {background_data.shape})")

    return background_data


if __name__ == "__main__":
    generate_shap_background()
