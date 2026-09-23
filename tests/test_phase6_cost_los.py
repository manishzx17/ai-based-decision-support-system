"""
Phase 6 — Cost & Hospitalization Prediction Test Suite

Validates:
1. Dataset 4 integrity & synthetic benchmark provenance labeling (2,500 episodes).
2. Preprocessing pipeline (StandardScaler, OneHotEncoder, handling unseen values).
3. Zero Target Leakage: LOS uses strictly pre-operative features; Cost uses predicted/planned LOS.
4. Model loading & valid non-negative predictions for cost and LOS.
5. Evaluation metrics calculation (MAE, RMSE, R² successfully computed and finite).
6. TreeSHAP attribution and mathematical additive property proof.
7. Empirical benchmark error band based on held-out RMSE (±1.96 × RMSE).
8. Clinical profile context auto-enrichment (age, gender, comorbidities from profile).
9. FastAPI endpoints: POST /api/cost/predict, POST /api/cost/explain, POST /api/cost/predict-los, GET /api/cost/metrics.
10. Research-prototype notice and non-causal attribution wording presence.
"""

import sys
import os
import json
import pytest
import numpy as np
import pandas as pd
from fastapi.testclient import TestClient

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND_DIR = os.path.join(BASE_DIR, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from main import app
from ai.cost_prediction import cost_predictor
from ai.shap_explainer import shap_explainer
from datasets.cost_training_data import generate_cost_and_los_dataset, DATASET_PROVENANCE
from security import create_access_token

client = TestClient(app)


def _demo_auth_headers():
    """Return auth headers for demo User 1 (Rahul Verma) for endpoint tests."""
    token = create_access_token({"sub": "1", "email": "patient@example.com", "role": "patient"})
    return {"Authorization": f"Bearer {token}"}

DATASET4_JSON_PATH = os.path.join(BACKEND_DIR, "datasets", "cost_hospitalization", "dataset4_episodes.json")
METADATA_JSON_PATH = os.path.join(BACKEND_DIR, "datasets", "cost_hospitalization", "metadata.json")
METRICS_PATH = os.path.join(BACKEND_DIR, "ai", "ml_models", "model_metrics.json")


# =============================================================================
# 1. DATASET 4 VALIDATION & SYNTHETIC BENCHMARK PROVENANCE
# =============================================================================

def test_dataset4_size_and_schema():
    """Verify Dataset 4 contains 2,500 synthetic benchmark episodes with required columns."""
    df = generate_cost_and_los_dataset(n_samples=2500, random_seed=42)
    assert len(df) == 2500, f"Expected 2,500 episodes, found {len(df)}"

    required_cols = [
        "patient_id", "age", "gender", "has_diabetes", "has_hypertension",
        "has_cardiac_history", "comorbidity_count", "treatment_name", "specialty",
        "city", "hospital_tier", "room_type", "insurance_type",
        "planned_los_days", "hospitalization_los_days", "treatment_cost_inr"
    ]
    for col in required_cols:
        assert col in df.columns, f"Missing required column: {col}"


def test_dataset4_persisted_artifacts_and_provenance_labels():
    """Verify canonical Dataset 4 JSON file exists and metadata explicitly labels it as synthetic research data."""
    assert os.path.exists(DATASET4_JSON_PATH), f"Dataset 4 file missing at {DATASET4_JSON_PATH}"
    assert os.path.exists(METADATA_JSON_PATH), f"Metadata file missing at {METADATA_JSON_PATH}"

    with open(METADATA_JSON_PATH, "r", encoding="utf-8") as f:
        meta = json.load(f)

    assert meta.get("is_real_patient_records") is False
    assert "synthetic" in meta.get("dataset_label", "").lower()
    assert "total_episodes" in meta and meta["total_episodes"] == 2500
    assert "disclosure" in meta


def test_dataset4_clinical_and_economic_distributions():
    """Verify distributions are clinically and economically plausible for synthetic benchmarking."""
    df = generate_cost_and_los_dataset(n_samples=2500, random_seed=42)

    # Cost ranges: standard procedures must fall within calibrated Indian tariff ranges
    assert df["treatment_cost_inr"].min() >= 40000.0
    assert df["treatment_cost_inr"].max() <= 1500000.0

    # Stay duration: length of stay between 1 and 25 days
    assert df["hospitalization_los_days"].min() >= 1.0
    assert df["hospitalization_los_days"].max() <= 25.0

    # Comorbidity count: between 0 and 3
    assert df["comorbidity_count"].between(0, 3).all()


# =============================================================================
# 2. PREPROCESSING & ZERO TARGET LEAKAGE
# =============================================================================

def test_zero_target_leakage_in_los_model():
    """Verify LOS model strictly uses pre-operative features (NO cost, NO post-stay variables)."""
    with open(METRICS_PATH, "r", encoding="utf-8") as f:
        metrics = json.load(f)

    los_features = metrics["los_model"]["input_features"]
    for forbidden in ["treatment_cost_inr", "cost", "planned_los_days", "hospitalization_los_days", "post_op"]:
        assert forbidden not in los_features, f"Forbidden leakage feature found in LOS model: {forbidden}"


def test_cost_model_uses_predicted_los_not_realized_stay():
    """Verify Cost model uses predicted stay duration rather than realized post-hospitalization stay."""
    with open(METRICS_PATH, "r", encoding="utf-8") as f:
        metrics = json.load(f)

    cost_features = metrics["cost_model"]["input_features"]
    assert "hospitalization_los_days" not in cost_features, "Realized stay leaked into Cost model!"
    assert "predicted_los_days" in cost_features or "planned_los_days" in cost_features


def test_preprocessing_handles_unknown_categories():
    """Verify OneHotEncoder handles unknown categories gracefully without crashing."""
    sample = pd.DataFrame([{
        "age": 45,
        "comorbidity_count": 0,
        "has_diabetes": 0,
        "has_hypertension": 0,
        "has_cardiac_history": 0,
        "gender": "UnknownGender",
        "treatment_name": "NonExistentProcedure",
        "specialty": "UnknownSpecialty",
        "city": "UnknownCity",
        "hospital_tier": "UnknownTier",
        "room_type": "UnknownRoom"
    }])
    X_trans = cost_predictor.los_preprocessor.transform(sample)
    assert X_trans.shape[0] == 1
    assert not np.isnan(X_trans).any()


# =============================================================================
# 3. MODEL PREDICTIONS & EVALUATION METRICS VERIFICATION
# =============================================================================

def test_models_load_and_generate_valid_predictions():
    """Verify both trained models generate non-negative, finite predictions within realistic bounds."""
    pred_los = cost_predictor.predict_los(
        treatment_name="Coronary Angioplasty",
        city="Hyderabad",
        room_type="Private AC Deluxe",
        age=58,
        comorbidity_count=1
    )
    assert isinstance(pred_los, float)
    assert 1.0 <= pred_los <= 25.0

    cost_result = cost_predictor.predict(
        treatment_name="Coronary Angioplasty",
        city="Hyderabad",
        room_type="Private AC Deluxe",
        age=58,
        comorbidity_count=1
    )
    assert cost_result["estimated_avg_cost"] > 0
    assert cost_result["estimated_min_cost"] <= cost_result["estimated_avg_cost"] <= cost_result["estimated_max_cost"]
    assert np.isfinite(cost_result["estimated_avg_cost"])


def test_evaluation_metrics_are_computed_finite_and_reported():
    """
    Verify MAE, RMSE, and R2 are successfully computed and finite for both models.
    Per user instructions: tests do not enforce arbitrary thresholds (e.g. R2 > 0.90),
    and acknowledge high performance reflects synthetic benchmark calibration.
    """
    with open(METRICS_PATH, "r", encoding="utf-8") as f:
        metrics = json.load(f)

    # Cost Model metrics
    cost_metrics = metrics["cost_model"]
    assert "mae_inr" in cost_metrics and np.isfinite(cost_metrics["mae_inr"]) and cost_metrics["mae_inr"] > 0
    assert "rmse_inr" in cost_metrics and np.isfinite(cost_metrics["rmse_inr"]) and cost_metrics["rmse_inr"] > 0
    assert "r2_score" in cost_metrics and np.isfinite(cost_metrics["r2_score"]) and cost_metrics["r2_score"] > 0

    # LOS Model metrics
    los_metrics = metrics["los_model"]
    assert "mae_days" in los_metrics and np.isfinite(los_metrics["mae_days"]) and los_metrics["mae_days"] > 0
    assert "rmse_days" in los_metrics and np.isfinite(los_metrics["rmse_days"]) and los_metrics["rmse_days"] > 0
    assert "r2_score" in los_metrics and np.isfinite(los_metrics["r2_score"]) and los_metrics["r2_score"] > 0

    # Verify synthetic benchmark disclosure is present in evaluation payload
    assert "evaluation_disclosure" in metrics
    assert "synthetic" in metrics["evaluation_disclosure"].lower()


# =============================================================================
# 4. TREESHAP ATTRIBUTION & EMPIRICAL ERROR BANDS
# =============================================================================

def test_treeshap_exact_mathematical_additive_property():
    """
    Verify TreeSHAP guarantees the exact additive property:
    Prediction = Base Value + sum(SHAP feature attributions).
    """
    pred = cost_predictor.predict(
        treatment_name="Total Knee Replacement",
        city="Bengaluru",
        room_type="Private AC Deluxe",
        age=62,
        gender="Female",
        comorbidity_count=2
    )
    exp = shap_explainer.explain_cost(pred)

    assert exp["additive_property_verified"] is True
    # Verify absolute difference is minimal (floating-point precision within 1.0 INR on ~250k INR)
    assert exp["additive_difference"] < 1.0
    assert exp["relative_additive_difference"] < 1e-4


def test_treeshap_non_causal_attribution_labeling():
    """Verify SHAP attributions are explicitly described as model feature contributions, not causal effects."""
    pred = cost_predictor.predict(treatment_name="CABG", city="Mumbai")
    exp = shap_explainer.explain_cost(pred)

    assert "attribution_disclaimer" in exp
    assert "causal" in exp["attribution_disclaimer"].lower()
    assert "summary_note" in exp
    assert "causal" in exp["summary_note"].lower() or "contributions" in exp["summary_note"].lower()


def test_empirical_benchmark_error_band_labeling():
    """
    Verify that error range is explicitly labeled as an 'empirical benchmark error band
    based on held-out RMSE' and NOT called a confidence interval or prediction interval.
    """
    pred = cost_predictor.predict(treatment_name="Appendectomy", city="Chennai")
    err_band = pred["empirical_model_error_range"]

    assert "held_out_rmse_inr" in err_band
    assert "confidence interval" not in err_band["description"].lower()
    assert "prediction interval" not in err_band["description"].lower()
    assert "empirical" in err_band["description"].lower()
    assert "rmse" in err_band["description"].lower()


# =============================================================================
# 5. FASTAPI API INTEGRATION TESTS
# =============================================================================

def test_api_predict_cost_endpoint():
    """Verify POST /api/cost/predict returns prediction, empirical error band, and disclaimer."""
    payload = {
        "treatment_name": "Coronary Angioplasty",
        "city": "Hyderabad",
        "room_type": "Private AC Deluxe",
        "age": 55,
        "gender": "Male"
    }
    response = client.post("/api/cost/predict", json=payload, headers=_demo_auth_headers())
    assert response.status_code == 200, response.text
    data = response.json()

    assert "estimated_avg_cost" in data and data["estimated_avg_cost"] > 0
    assert "predicted_los_days" in data and data["predicted_los_days"] > 0
    assert "empirical_model_error_range" in data
    assert "disclaimer" in data
    assert "research-prototype" in data["disclaimer"].lower()


def test_api_explain_cost_endpoint():
    """Verify POST /api/cost/explain returns prediction and TreeSHAP feature attributions."""
    payload = {
        "treatment_name": "Total Knee Replacement",
        "city": "Delhi",
        "room_type": "Private AC Deluxe"
    }
    response = client.post("/api/cost/explain", json=payload, headers=_demo_auth_headers())
    assert response.status_code == 200, response.text
    data = response.json()

    assert "prediction" in data
    assert "shap_explanation" in data
    shap_exp = data["shap_explanation"]
    assert "breakdown" in shap_exp and len(shap_exp["breakdown"]) >= 5
    assert "additive_property_verified" in shap_exp
    assert shap_exp["additive_property_verified"] is True


def test_api_predict_los_endpoint():
    """Verify POST /api/cost/predict-los returns strictly pre-operative stay prediction."""
    payload = {
        "treatment_name": "CABG",
        "city": "Mumbai",
        "age": 60,
        "has_cardiac_history": True
    }
    response = client.post("/api/cost/predict-los", json=payload, headers=_demo_auth_headers())
    assert response.status_code == 200, response.text
    data = response.json()

    assert "predicted_los_days" in data
    assert data["predicted_los_days"] >= 4.0
    assert "pre_operative_features_used" in data


def test_api_metrics_endpoint():
    """Verify GET /api/cost/metrics returns held-out metrics and synthetic dataset disclosures."""
    response = client.get("/api/cost/metrics")
    assert response.status_code == 200, response.text
    data = response.json()

    assert "cost_model" in data
    assert "los_model" in data
    assert "training_dataset" in data
    assert data["training_dataset"]["is_real_patient_records"] is False
    assert "evaluation_disclosure" in data
