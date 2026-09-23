"""
Model Training Pipeline for 12C Medical Travel Decision Support System.
Trains two genuine XGBoost regression models:
1. Treatment Cost Predictor (Target: treatment_cost_inr)
2. Hospitalization Length of Stay (LOS) Predictor (Target: hospitalization_los_days)

Enforces strict zero-leakage constraints:
- LOS model uses strictly pre-operative baseline patient/clinical/facility factors (no cost, no post-outcome variables).
- Cost model uses planned/estimated LOS (not realized post-hospitalization stay).
Evaluates models on a held-out test split and persists all artifacts for runtime TreeSHAP inference.
"""

import os
import sys
import json
from typing import Dict, Any
import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import xgboost as xgb

# Add backend directory to sys.path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(CURRENT_DIR)
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from datasets.cost_training_data import generate_cost_and_los_dataset, DATASET_PROVENANCE

MODELS_DIR = os.path.join(CURRENT_DIR, "ml_models")
os.makedirs(MODELS_DIR, exist_ok=True)

# Feature Definitions
NUMERICAL_FEATURES_LOS = [
    "age", "comorbidity_count", "has_diabetes", "has_hypertension", "has_cardiac_history"
]
CATEGORICAL_FEATURES_LOS = [
    "gender", "treatment_name", "specialty", "city", "hospital_tier", "room_type"
]

NUMERICAL_FEATURES_COST = [
    "age", "comorbidity_count", "has_diabetes", "has_hypertension", "has_cardiac_history", "planned_los_days"
]
CATEGORICAL_FEATURES_COST = [
    "gender", "treatment_name", "specialty", "city", "hospital_tier", "room_type", "insurance_type"
]


def train_and_persist_models(random_seed: int = 42) -> Dict[str, Any]:
    print("Generating training dataset (2,500 samples)...")
    df = generate_cost_and_los_dataset(n_samples=2500, random_seed=random_seed)

    # 70% Train, 15% Validation, 15% Test split
    train_df, temp_df = train_test_split(df, test_size=0.30, random_state=random_seed)
    val_df, test_df = train_test_split(temp_df, test_size=0.50, random_state=random_seed)

    print(f"Dataset splits: Train={len(train_df)}, Val={len(val_df)}, Test={len(test_df)}")

    # =========================================================================
    # 1. TRAIN MODEL 2: HOSPITALIZATION DURATION (LOS) REGRESSOR
    # Strictly pre-operative features only (NO cost feature, NO post-outcome data)
    # =========================================================================
    print("\n--- Training Model 2: Hospitalization Length of Stay (LOS) ---")
    X_train_los = train_df[NUMERICAL_FEATURES_LOS + CATEGORICAL_FEATURES_LOS]
    y_train_los = train_df["hospitalization_los_days"]

    X_val_los = val_df[NUMERICAL_FEATURES_LOS + CATEGORICAL_FEATURES_LOS]
    y_val_los = val_df["hospitalization_los_days"]

    X_test_los = test_df[NUMERICAL_FEATURES_LOS + CATEGORICAL_FEATURES_LOS]
    y_test_los = test_df["hospitalization_los_days"]

    preprocessor_los = ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), NUMERICAL_FEATURES_LOS),
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), CATEGORICAL_FEATURES_LOS)
        ]
    )

    X_train_los_trans = preprocessor_los.fit_transform(X_train_los)
    X_val_los_trans = preprocessor_los.transform(X_val_los)
    X_test_los_trans = preprocessor_los.transform(X_test_los)

    # Get transformed feature names for SHAP attribution
    cat_names_los = preprocessor_los.named_transformers_["cat"].get_feature_names_out(CATEGORICAL_FEATURES_LOS)
    feature_names_los = list(NUMERICAL_FEATURES_LOS) + list(cat_names_los)

    model_los = xgb.XGBRegressor(
        n_estimators=180,
        max_depth=4,
        learning_rate=0.06,
        subsample=0.85,
        colsample_bytree=0.85,
        random_state=random_seed,
        n_jobs=-1
    )
    model_los.fit(
        X_train_los_trans, y_train_los,
        eval_set=[(X_val_los_trans, y_val_los)],
        verbose=False
    )

    # Evaluate LOS on held-out test set
    y_pred_los = model_los.predict(X_test_los_trans)
    y_pred_los = np.clip(y_pred_los, 1.0, 30.0)

    mae_los = float(mean_absolute_error(y_test_los, y_pred_los))
    rmse_los = float(np.sqrt(mean_squared_error(y_test_los, y_pred_los)))
    r2_los = float(r2_score(y_test_los, y_pred_los))

    print(f"Held-Out Test Metrics for LOS Model:")
    print(f"  MAE:  {mae_los:.3f} days")
    print(f"  RMSE: {rmse_los:.3f} days")
    print(f"  R²:   {r2_los:.4f}")

    # =========================================================================
    # 2. TRAIN MODEL 1: TREATMENT COST REGRESSOR
    # Strictly zero target leakage:
    # Deployment flow: pre-operative features -> LOS model -> predicted LOS -> cost model.
    # We generate 5-fold Out-Of-Fold (OOF) predicted LOS for train_df, and use Model 2
    # predictions for val_df and test_df. Realized post-stay is NEVER used.
    # =========================================================================
    print("\n--- Training Model 1: Treatment Cost Regressor with Out-Of-Fold Predicted LOS ---")
    from sklearn.model_selection import KFold

    kf = KFold(n_splits=5, shuffle=True, random_state=random_seed)
    oof_los = np.zeros(len(train_df))
    train_indices = train_df.index

    for fold, (trn_idx, val_idx) in enumerate(kf.split(train_df)):
        fold_X_tr = train_df.iloc[trn_idx][NUMERICAL_FEATURES_LOS + CATEGORICAL_FEATURES_LOS]
        fold_y_tr = train_df.iloc[trn_idx]["hospitalization_los_days"]
        fold_X_val = train_df.iloc[val_idx][NUMERICAL_FEATURES_LOS + CATEGORICAL_FEATURES_LOS]

        fold_preprocessor = ColumnTransformer(
            transformers=[
                ("num", StandardScaler(), NUMERICAL_FEATURES_LOS),
                ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), CATEGORICAL_FEATURES_LOS)
            ]
        )
        fold_X_tr_trans = fold_preprocessor.fit_transform(fold_X_tr)
        fold_X_val_trans = fold_preprocessor.transform(fold_X_val)

        fold_model = xgb.XGBRegressor(
            n_estimators=120,
            max_depth=4,
            learning_rate=0.06,
            random_state=random_seed + fold,
            n_jobs=-1
        )
        fold_model.fit(fold_X_tr_trans, fold_y_tr, verbose=False)
        oof_los[val_idx] = np.clip(fold_model.predict(fold_X_val_trans), 1.0, 30.0)

    # Attach predicted LOS feature to datasets
    train_cost_df = train_df.copy()
    train_cost_df["predicted_los_days"] = oof_los

    val_cost_df = val_df.copy()
    val_cost_df["predicted_los_days"] = np.clip(model_los.predict(X_val_los_trans), 1.0, 30.0)

    test_cost_df = test_df.copy()
    test_cost_df["predicted_los_days"] = np.clip(model_los.predict(X_test_los_trans), 1.0, 30.0)

    # Cost feature list uses predicted_los_days instead of realized stay
    COST_NUMERICAL = ["age", "comorbidity_count", "has_diabetes", "has_hypertension", "has_cardiac_history", "predicted_los_days"]
    COST_CATEGORICAL = ["gender", "treatment_name", "specialty", "city", "hospital_tier", "room_type", "insurance_type"]

    X_train_cost = train_cost_df[COST_NUMERICAL + COST_CATEGORICAL]
    y_train_cost = train_cost_df["treatment_cost_inr"]

    X_val_cost = val_cost_df[COST_NUMERICAL + COST_CATEGORICAL]
    y_val_cost = val_cost_df["treatment_cost_inr"]

    X_test_cost = test_cost_df[COST_NUMERICAL + COST_CATEGORICAL]
    y_test_cost = test_cost_df["treatment_cost_inr"]

    preprocessor_cost = ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), COST_NUMERICAL),
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), COST_CATEGORICAL)
        ]
    )

    X_train_cost_trans = preprocessor_cost.fit_transform(X_train_cost)
    X_val_cost_trans = preprocessor_cost.transform(X_val_cost)
    X_test_cost_trans = preprocessor_cost.transform(X_test_cost)

    cat_names_cost = preprocessor_cost.named_transformers_["cat"].get_feature_names_out(COST_CATEGORICAL)
    feature_names_cost = list(COST_NUMERICAL) + list(cat_names_cost)

    model_cost = xgb.XGBRegressor(
        n_estimators=220,
        max_depth=5,
        learning_rate=0.07,
        subsample=0.85,
        colsample_bytree=0.85,
        random_state=random_seed,
        n_jobs=-1
    )
    model_cost.fit(
        X_train_cost_trans, y_train_cost,
        eval_set=[(X_val_cost_trans, y_val_cost)],
        verbose=False
    )

    # Evaluate Cost on held-out test set
    y_pred_cost = model_cost.predict(X_test_cost_trans)
    y_pred_cost = np.clip(y_pred_cost, 30000.0, 2000000.0)

    mae_cost = float(mean_absolute_error(y_test_cost, y_pred_cost))
    rmse_cost = float(np.sqrt(mean_squared_error(y_test_cost, y_pred_cost)))
    r2_cost = float(r2_score(y_test_cost, y_pred_cost))

    print(f"Held-Out Test Metrics for Cost Model:")
    print(f"  MAE:  ₹{mae_cost:,.2f} INR")
    print(f"  RMSE: ₹{rmse_cost:,.2f} INR")
    print(f"  R²:   {r2_cost:.4f}")

    # =========================================================================
    # 3. PERSIST ARTIFACTS
    # =========================================================================
    print("\nSaving trained models, preprocessors, and metadata...")
    cost_model_path = os.path.join(MODELS_DIR, "cost_model.json")
    los_model_path = os.path.join(MODELS_DIR, "los_model.json")
    preprocessor_cost_path = os.path.join(MODELS_DIR, "preprocessor_cost.joblib")
    preprocessor_los_path = os.path.join(MODELS_DIR, "preprocessor_los.joblib")
    metrics_path = os.path.join(MODELS_DIR, "model_metrics.json")
    features_cost_path = os.path.join(MODELS_DIR, "feature_names_cost.json")
    features_los_path = os.path.join(MODELS_DIR, "feature_names_los.json")

    model_cost.save_model(cost_model_path)
    model_los.save_model(los_model_path)
    joblib.dump(preprocessor_cost, preprocessor_cost_path)
    joblib.dump(preprocessor_los, preprocessor_los_path)

    with open(features_cost_path, "w") as f:
        json.dump(feature_names_cost, f, indent=2)

    with open(features_los_path, "w") as f:
        json.dump(feature_names_los, f, indent=2)

    metrics_payload = {
        "cost_model": {
            "model_type": "XGBoost Regressor",
            "n_estimators": 220,
            "max_depth": 5,
            "learning_rate": 0.07,
            "mae_inr": round(mae_cost, 2),
            "rmse_inr": round(rmse_cost, 2),
            "r2_score": round(r2_cost, 4),
            "input_features": list(COST_NUMERICAL + COST_CATEGORICAL),
            "target_leakage_policy": "Zero Target Leakage Enforced: Cost model is trained using out-of-fold predicted stay duration and never ingests actual realized post-stay.",
            "error_band_definition": "Empirical benchmark error band based on held-out RMSE (±1.96 × held-out RMSE). Not a formal statistical confidence interval."
        },
        "los_model": {
            "model_type": "XGBoost Regressor",
            "n_estimators": 180,
            "max_depth": 4,
            "learning_rate": 0.06,
            "mae_days": round(mae_los, 3),
            "rmse_days": round(rmse_los, 3),
            "r2_score": round(r2_los, 4),
            "input_features": list(NUMERICAL_FEATURES_LOS + CATEGORICAL_FEATURES_LOS),
            "target_leakage_policy": "Strictly pre-operative baseline features only. Cost and post-hospitalization outcomes are excluded."
        },
        "training_dataset": {
            "dataset_name": "Dataset 4",
            "dataset_label": "Synthetic Research Benchmark Data",
            "is_real_patient_records": False,
            "calibration_source": "National Health Authority (NHA / PMJAY) standard package tariffs & GIPSA schedule of charges",
            "disclosure": "The 2,500 patient episodes in Dataset 4 are synthetic benchmark data generated for decision-support algorithm testing. High benchmark performance metrics reflect the synthetic data-generation process and do not establish real-world clinical validity."
        },
        "split": {
            "train_samples": len(train_df),
            "val_samples": len(val_df),
            "test_samples": len(test_df),
            "random_seed": random_seed
        },
        "evaluation_disclosure": "Because Dataset 4 is synthetic, high model evaluation metrics (MAE/RMSE/R²) reflect consistency with the calibrated economic simulation and must not be interpreted as real-world clinical or financial precision."
    }

    with open(metrics_path, "w") as f:
        json.dump(metrics_payload, f, indent=2)

    print(f"Artifacts successfully persisted to {MODELS_DIR}!")
    return metrics_payload


if __name__ == "__main__":
    train_and_persist_models()
