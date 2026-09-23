import os
import sys
import json
import pytest

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

from fastapi.testclient import TestClient
from main import app
from ai.cost_prediction import cost_predictor
from ai.shap_explainer import shap_explainer
from security import create_access_token

client = TestClient(app)


def _demo_auth_headers():
    """Return auth headers for demo User 1 for cost endpoint tests."""
    token = create_access_token({"sub": "1", "email": "patient@example.com", "role": "patient"})
    return {"Authorization": f"Bearer {token}"}

MODELS_DIR = os.path.join(os.path.dirname(__file__), "..", "backend", "ai", "ml_models")

def test_model_artifacts_and_metrics_exist():
    """Verify all required trained model artifacts and evaluation metrics are present on disk."""
    assert os.path.exists(os.path.join(MODELS_DIR, "cost_model.json")), "cost_model.json missing"
    assert os.path.exists(os.path.join(MODELS_DIR, "los_model.json")), "los_model.json missing"
    assert os.path.exists(os.path.join(MODELS_DIR, "preprocessor_cost.joblib")), "preprocessor_cost.joblib missing"
    assert os.path.exists(os.path.join(MODELS_DIR, "preprocessor_los.joblib")), "preprocessor_los.joblib missing"
    assert os.path.exists(os.path.join(MODELS_DIR, "model_metrics.json")), "model_metrics.json missing"

    with open(os.path.join(MODELS_DIR, "model_metrics.json"), "r") as f:
        metrics = json.load(f)

    # Verify actual held-out metrics are recorded
    assert "cost_model" in metrics
    assert "los_model" in metrics
    assert metrics["cost_model"]["mae_inr"] > 0
    assert metrics["cost_model"]["rmse_inr"] > 0
    assert 0.0 < metrics["cost_model"]["r2_score"] <= 1.0
    assert metrics["los_model"]["mae_days"] > 0
    assert metrics["los_model"]["rmse_days"] > 0
    assert 0.0 < metrics["los_model"]["r2_score"] <= 1.0

    # Dataset Disclosure Check (Correction 2):
    # Clearly document that 2,500 patient episodes are synthetic benchmark data, NOT real patient records
    assert metrics["training_dataset"]["dataset_type"] == "SYNTHETIC BENCHMARK DATA"
    assert metrics["training_dataset"]["is_real_patient_records"] is False
    assert "do not represent real patient records" in metrics["training_dataset"]["disclosure"].lower()

def test_target_leakage_exclusion():
    """
    Correction 1:
    Strict zero target leakage:
    - LOS model must exclude treatment cost and all post-outcome/post-hospitalization variables.
    - Cost model uses planned LOS or LOS predicted by the LOS model, never actual realized post-hospital stay.
    """
    with open(os.path.join(MODELS_DIR, "model_metrics.json"), "r") as f:
        metrics = json.load(f)

    los_features = metrics["los_model"]["input_features"]
    # Verify no cost or post-outcome variables in LOS features
    forbidden_terms = ["cost", "price", "tariff", "bill", "complication_post", "discharge", "actual_los"]
    for feat in los_features:
        for term in forbidden_terms:
            assert term not in feat.lower(), f"Target leakage detected: '{feat}' in LOS model features!"

    cost_features = metrics["cost_model"]["input_features"]
    assert "planned_los_days" in cost_features, "Cost model should use planned_los_days"
    assert "actual_los" not in cost_features, "Cost model must not use actual realized post-hospital stay"

def test_los_prediction_grounded():
    """Verify LOS model produces clinically sound stay durations across procedures."""
    los_angio = cost_predictor.predict_los(treatment_name="Coronary Angioplasty")
    los_cabg = cost_predictor.predict_los(treatment_name="CABG")
    los_craniotomy = cost_predictor.predict_los(treatment_name="Craniotomy")
    los_append = cost_predictor.predict_los(treatment_name="Appendectomy")

    assert 1.0 <= los_angio <= 6.0, f"Angioplasty LOS unexpected: {los_angio}"
    assert los_cabg > los_angio, "CABG should require longer hospital stay than angioplasty"
    assert los_craniotomy > los_append, "Craniotomy should require longer hospital stay than appendectomy"

def test_cost_prediction_and_empirical_error_range():
    """
    Correction 2:
    Verify uncertainty range is labeled as an approximate empirical model-error range
    based on held-out residuals, not a formal confidence interval.
    """
    res = cost_predictor.predict(
        treatment_name="CABG",
        city="Mumbai",
        room_type="Private AC Deluxe"
    )

    assert res["estimated_avg_cost"] > 100000.0
    assert "empirical_model_error_range" in res

    error_range = res["empirical_model_error_range"]
    assert "lower_bound" in error_range
    assert "upper_bound" in error_range
    assert "held_out_rmse_inr" in error_range
    assert "formal confidence interval" in error_range["description"].lower() or "not a formal" in error_range["description"].lower()
    assert "approximate empirical model-error range" in error_range["description"].lower()

    # Check bounds consistency: upper > avg > lower
    assert error_range["upper_bound"] >= res["estimated_avg_cost"] >= error_range["lower_bound"]

def test_treeshap_additive_property():
    """
    Verify TreeSHAP satisfies the mathematical additive property:
    Prediction = Base Value + sum(SHAP attributions)
    
    Correction 1: Validate additive property to <= 1e-4 relative discrepancy.
    Verify full-precision values across multiple procedures and document exact maximum discrepancy.
    """
    test_procedures = [
        ("Coronary Angioplasty", "Hyderabad", 3),
        ("CABG", "Mumbai", 8),
        ("Total Knee Replacement", "Bengaluru", 5),
        ("Craniotomy", "Delhi", 7),
        ("Appendectomy", "Chennai", 2)
    ]

    for treatment, city, stay in test_procedures:
        res = cost_predictor.predict(
            treatment_name=treatment,
            city=city,
            room_type="Private AC Deluxe",
            duration_days=stay
        )

        assert "base_value" in res
        assert "additive_difference" in res
        assert "relative_additive_difference" in res

        # Relative discrepancy strictly validated to <= 1e-4
        rel_diff = res["relative_additive_difference"]
        abs_diff = res["additive_difference"]
        pred = res["estimated_avg_cost"]

        assert rel_diff <= 1e-4, f"Additive consistency violated for {treatment}: rel_diff={rel_diff} > 1e-4"
        
        # Absolute difference is purely float32 precision across 39 terms on 300,000+ numbers (<= 0.50 INR)
        assert abs_diff <= 0.50, f"Absolute difference {abs_diff} exceeds float32 ULP bounds on {pred}"

        # Verify SHAP explanation breakdown
        expl = shap_explainer.explain_cost(res)
        assert expl["additive_property_verified"] is True
        assert expl["additive_precision_metrics"]["meets_strict_tolerance"] is True
        assert len(expl["breakdown"]) >= 5

def test_prediction_sensitivity_across_contexts():
    """Verify cost model changes meaningfully across high-risk vs routine procedures and tiers."""
    low_acuity = cost_predictor.predict(
        treatment_name="Appendectomy",
        city="Chennai",
        room_type="General Ward",
        duration_days=2,
        comorbidity_count=0,
        has_diabetes=0,
        has_hypertension=0
    )

    high_acuity = cost_predictor.predict(
        treatment_name="CABG",
        city="Mumbai",
        room_type="Super Deluxe Suite",
        duration_days=8,
        comorbidity_count=3,
        has_diabetes=1,
        has_hypertension=1,
        has_cardiac_history=1
    )

    assert high_acuity["estimated_avg_cost"] > low_acuity["estimated_avg_cost"] * 2.0, \
        "High acuity multi-morbid CABG should cost substantially more than simple Appendectomy"

def test_api_predict_and_explain_endpoints():
    """Verify FastAPI /api/cost/predict and /api/cost/explain endpoints work seamlessly."""
    # 1. /api/cost/predict
    resp1 = client.post("/api/cost/predict", json={
        "treatment_name": "Total Knee Replacement",
        "city": "Bengaluru",
        "room_type": "Private AC Deluxe"
    }, headers=_demo_auth_headers())
    assert resp1.status_code == 200
    data1 = resp1.json()
    assert data1["treatment_name"] == "Total Knee Replacement"
    assert data1["estimated_avg_cost"] > 50000.0
    assert data1["predicted_los_days"] > 0
    assert data1["los_source"] == "predicted_by_los_model"

    # 2. /api/cost/explain
    resp2 = client.post("/api/cost/explain", json={
        "treatment_name": "Total Knee Replacement",
        "city": "Bengaluru",
        "room_type": "Private AC Deluxe",
        "duration_days": 5
    }, headers=_demo_auth_headers())
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert "prediction" in data2
    assert "shap_explanation" in data2
    assert data2["prediction"]["los_source"] == "user_planned"
    assert len(data2["shap_explanation"]["breakdown"]) > 0

    # 3. /api/cost/metrics
    resp3 = client.get("/api/cost/metrics")
    assert resp3.status_code == 200
    metrics = resp3.json()
    assert "cost_model" in metrics
    assert "los_model" in metrics
    assert metrics["split"]["random_seed"] == 42
