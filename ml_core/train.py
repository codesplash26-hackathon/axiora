import sys
from pathlib import Path

# Dynamically add project root (Axiora) to sys.path so config can be imported
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, average_precision_score
from xgboost import XGBClassifier
import config

TARGET_COL = "TenYearCHD"


def train_base_model():
    if not config.CLEAN_DATASET_PATH.exists():
        raise FileNotFoundError(f"Cleaned dataset not found at: {config.CLEAN_DATASET_PATH.resolve()}")

    df = pd.read_csv(config.CLEAN_DATASET_PATH)

    # 1. Feature / Target Separation
    X = df.drop(columns=[TARGET_COL])
    y = df[TARGET_COL].astype(int)

    # 2. Stratified 3-Way Split: 70% Train, 15% Calibration, 15% Test
    X_train, X_temp, y_train, y_temp = train_test_split(
        X, y, test_size=0.30, random_state=42, stratify=y
    )
    X_calib, X_test, y_calib, y_test = train_test_split(
        X_temp, y_temp, test_size=0.50, random_state=42, stratify=y_temp
    )

    # 3. Calculate class imbalance weight: count(negative) / count(positive)
    pos_count = int(np.sum(y_train == 1))
    neg_count = int(np.sum(y_train == 0))
    scale_weight = round(neg_count / pos_count, 2)

    print(f"Training set: {len(X_train)} samples (Positive: {pos_count}, Negative: {neg_count})")
    print(f"Computed scale_pos_weight: {scale_weight}")

    # 4. Initialize and train XGBoost Classifier
    model = XGBClassifier(
        n_estimators=150,
        max_depth=4,
        learning_rate=0.04,
        subsample=0.8,
        colsample_bytree=0.8,
        scale_pos_weight=scale_weight,
        eval_metric="logloss",
        random_state=42,
        tree_method="hist",
    )

    model.fit(X_train, y_train)

    # 5. Baseline Evaluation on untouched Test Set
    raw_probs = model.predict_proba(X_test)[:, 1]
    roc_auc = roc_auc_score(y_test, raw_probs)
    pr_auc = average_precision_score(y_test, raw_probs)

    print(f"Raw Model Test ROC-AUC: {roc_auc:.4f}")
    print(f"Raw Model Test PR-AUC:  {pr_auc:.4f}")

    # 6. Save raw model artifact and data splits for calibration and evaluation
    config.ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, config.RAW_MODEL_PATH)
    joblib.dump(
        {
            "X_train": X_train,
            "y_train": y_train,
            "X_calib": X_calib,
            "y_calib": y_calib,
            "X_test": X_test,
            "y_test": y_test,
            "feature_names": list(X.columns),
        },
        config.SPLIT_DATA_PATH,
    )

    print(f"Raw model exported to: {config.RAW_MODEL_PATH}")
    print(f"Data partitions exported to: {config.SPLIT_DATA_PATH}")


if __name__ == "__main__":
    train_base_model()
