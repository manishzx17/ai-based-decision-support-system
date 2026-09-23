"""
Final Cost & Length of Stay (LOS) Prediction Audit Test Suite.
Verifies the end-to-end functionality, strict zero target leakage,
LOS -> Cost dependency, TreeSHAP additive property, scenario sensitivity,
empirical error band terminology, and academic/data limitation disclosures.
"""

import sys
import os
import json
import pytest
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
from security import create_access_token

client = TestClient(app)


def _demo_auth_headers():
    """Return auth headers for demo User 1 for endpoint tests."""
    token = create_access_token({"sub": "1", "email": "patient@example.com", "role": "patient"})
    return {"Authorization": f"Bearer {token}"}
METRICS_PATH = os.path.join(BACKEND_DIR, "ai", "ml_models", "model_metrics.json")


# =============================================================================
# 1. LOS PREDICTION TESTS
# =============================================================================

def test_los_prediction_loads_and_runs_end_to_end():
    """Verify XGBoost LOS model loads cleanly and generates valid positive stay predictions."""
    assert cost_predictor.los_model is not None
    assert cost_predictor.los_preprocessor is not None

    los = cost_predictor.predict_los(
        treatment_name="Coronary Angioplasty",
        city="Hyderabad",
        age=52
    )
    assert isinstance(los, float)
    assert 1.0 <= los <= 30.0


def test_los_prediction_scenario_sensitivity():
    """
    Verify LOS model response across controlled scenarios:
    - Age sensitivity: older patients with higher surgical risk
    - Comorbidity sensitivity: multi-comorbid patients vs healthy
    - Procedure sensitivity: major surgery (CABG, Craniotomy) vs minor (Appendectomy)
    - Specialty sensitivity: Cardiothoracic vs General Surgery
    """
    # 1. Procedure & Specialty sensitivity
    los_angio = cost_predictor.predict_los(treatment_name="Coronary Angioplasty", specialty="Cardiology")
    los_cabg = cost_predictor.predict_los(treatment_name="CABG", specialty="Cardiothoracic Surgery")
    los_craniotomy = cost_predictor.predict_los(treatment_name="Craniotomy", specialty="Neurosurgery")
    los_append = cost_predictor.predict_los(treatment_name="Appendectomy", specialty="General Surgery")

    assert los_cabg > los_angio, f"CABG stay ({los_cabg}) must exceed Angioplasty stay ({los_angio})"
    assert los_craniotomy > los_append, f"Craniotomy stay ({los_craniotomy}) must exceed Appendectomy stay ({los_append})"

    # 2. Comorbidity sensitivity
    los_healthy = cost_predictor.predict_los(
        treatment_name="Total Knee Replacement",
        age=60,
        comorbidity_count=0,
        has_diabetes=0,
        has_hypertension=0,
        has_cardiac_history=0
    )
    los_comorbid = cost_predictor.predict_los(
        treatment_name="Total Knee Replacement",
        age=60,
        comorbidity_count=3,
        has_diabetes=1,
        has_hypertension=1,
        has_cardiac_history=1
    )
    assert los_comorbid >= los_healthy, "Patients with 3 comorbidities should have >= stay than patients with 0"


# =============================================================================
# 2. COST PREDICTION & LOS -> COST DEPENDENCY
# =============================================================================

def test_cost_prediction_loads_and_runs_end_to_end():
    """Verify XGBoost Cost model loads cleanly and generates valid cost estimates."""
    assert cost_predictor.cost_model is not None
    assert cost_predictor.cost_preprocessor is not None

    res = cost_predictor.predict(
        treatment_name="Coronary Angioplasty",
        city="Hyderabad"
    )
    assert res["estimated_avg_cost"] > 50000.0
    assert res["currency"] == "INR"
    assert "duration_days" in res
    assert "predicted_los_days" in res


def test_los_to_cost_dependency_and_runtime_leakage():
    """
    CRITICAL:
    1. Verify predicted LOS from the LOS model is used as the LOS input to the cost model at runtime.
    2. Verify actual/realized LOS is NOT supplied to the runtime cost prediction model.
    3. Changing predicted/planned LOS changes downstream cost input appropriately.
    """
    # Case A: User specifies no duration -> LOS model predicts stay
    res_auto = cost_predictor.predict(
        treatment_name="CABG",
        city="Mumbai",
        duration_days=None
    )
    assert res_auto["los_source"] == "predicted_by_los_model"
    auto_los = res_auto["predicted_los_days"]
    assert auto_los > 0

    # Case B: User specifies planned stay duration
    res_planned_short = cost_predictor.predict(
        treatment_name="CABG",
        city="Mumbai",
        duration_days=4
    )
    assert res_planned_short["los_source"] == "user_planned"
    assert res_planned_short["duration_days"] == 4

    res_planned_long = cost_predictor.predict(
        treatment_name="CABG",
        city="Mumbai",
        duration_days=12
    )
    assert res_planned_long["duration_days"] == 12

    # Longer stay must increase total hospitalization cost
    assert res_planned_long["estimated_avg_cost"] > res_planned_short["estimated_avg_cost"]

    # Verify input feature schema: actual realized post-stay is NEVER a feature
    with open(METRICS_PATH, "r") as f:
        metrics = json.load(f)
    cost_features = metrics["cost_model"]["input_features"]
    assert "actual_los" not in cost_features
    assert "hospitalization_los_days" not in cost_features
    assert "predicted_los_days" in cost_features or "planned_los_days" in cost_features


# =============================================================================
# 3. CRITICAL LEAKAGE AUDIT (TRAINING & RUNTIME)
# =============================================================================

def test_training_and_runtime_zero_target_leakage_policy():
    """
    Verify zero target leakage policy in training and runtime:
    - LOS model uses strictly pre-operative features (no cost, no post-stay, no complication post).
    - Cost model is trained using out-of-fold predicted stay, not realized stay.
    """
    with open(METRICS_PATH, "r") as f:
        metrics = json.load(f)

    # Check LOS features
    los_inputs = metrics["los_model"]["input_features"]
    forbidden_los = ["cost", "price", "tariff", "bill", "los_days", "discharge", "actual"]
    for feat in los_inputs:
        for f_word in forbidden_los:
            assert f_word not in feat.lower(), f"Forbidden target leakage word '{f_word}' in LOS feature: {feat}"

    # Check Cost features
    cost_inputs = metrics["cost_model"]["input_features"]
    assert "treatment_cost_inr" not in cost_inputs
    assert "hospitalization_los_days" not in cost_inputs


# =============================================================================
# 4. SHAP EXPLAINABILITY & MATHEMATICAL ADDITIVE PROPERTY
# =============================================================================

def test_shap_mathematical_additive_property():
    """
    Verify TreeSHAP satisfies the exact mathematical additive relationship:
    Base Value + sum(SHAP feature attributions) == Model Prediction
    Tolerance: relative discrepancy <= 1e-4
    """
    scenarios = [
        ("Coronary Angioplasty", "Hyderabad", 3),
        ("CABG", "Mumbai", 8),
        ("Total Knee Replacement", "Bengaluru", 5),
        ("Craniotomy", "Delhi", 7)
    ]

    for treatment, city, stay in scenarios:
        res = cost_predictor.predict(
            treatment_name=treatment,
            city=city,
            duration_days=stay
        )
        assert res["relative_additive_difference"] <= 1e-4
        assert res["additive_difference"] <= 0.50

        # Verify explanation
        expl = shap_explainer.explain_cost(res)
        assert expl["additive_property_verified"] is True
        assert len(expl["breakdown"]) >= 5
        # Verify feature names correspond to actual model features
        feature_names = [b["feature"] for b in expl["breakdown"]]
        assert any("Procedure Complexity" in fn for fn in feature_names)
        assert any("Hospitalization Length" in fn for fn in feature_names)
        assert any("Destination City" in fn for fn in feature_names)


# =============================================================================
# 5. ERROR BAND & TERMINOLOGY AUDIT
# =============================================================================

def test_empirical_error_band_terminology_compliance():
    """
    Verify the displayed prediction error band:
    1. Is labeled as empirical / benchmark-based (±1.96 × held-out RMSE).
    2. Does NOT claim to be a formal 'confidence interval', '95% confidence interval',
       or 'prediction probability'.
    """
    res = cost_predictor.predict(treatment_name="Total Knee Replacement", city="Bengaluru")
    assert "empirical_model_error_range" in res

    error_range = res["empirical_model_error_range"]
    assert "lower_bound" in error_range
    assert "upper_bound" in error_range
    assert "held_out_rmse_inr" in error_range
    assert error_range["upper_bound"] >= res["estimated_avg_cost"] >= error_range["lower_bound"]

    desc = error_range["description"]
    assert "not a formal statistical confidence interval" in desc.lower() or "not a formal" in desc.lower()
    assert "empirical" in desc.lower()


# =============================================================================
# 6. ACADEMIC & DATA LIMITATION AUDIT
# =============================================================================

def test_academic_and_synthetic_dataset_disclosure():
    """
    Verify that:
    1. Dataset 4 is clearly disclosed as synthetic research benchmark data.
    2. The project does NOT claim that high R² proves real-world clinical effectiveness.
    3. The synthetic nature is explicitly documented.
    """
    with open(METRICS_PATH, "r") as f:
        metrics = json.load(f)

    ds_info = metrics.get("training_dataset", {})
    assert ds_info.get("is_real_patient_records") is False
    assert ds_info.get("dataset_type") == "SYNTHETIC BENCHMARK DATA"
    assert "synthetic benchmark data" in ds_info.get("disclosure", "").lower()
    assert "do not represent real patient records" in ds_info.get("disclosure", "").lower()


# =============================================================================
# 7. EDGE CASES & RUNTIME ROBUSTNESS
# =============================================================================

def test_edge_cases_unseen_values_and_extreme_inputs():
    """
    Verify graceful handling of:
    - Unseen / unsupported procedure (canonicalizes safely)
    - Unseen / unsupported specialty (defaults to General Surgery)
    - Extreme age (e.g. 18 or 95)
    - Multiple / zero comorbidities
    - Missing optional fields
    """
    # 1. Unseen procedure and extreme age
    res_edge1 = cost_predictor.predict(
        treatment_name="Robotic Transcatheter Valve Repair Unknown",
        city="Unknown Metro",
        age=95,
        comorbidity_count=5,
        has_diabetes=1,
        has_hypertension=1,
        has_cardiac_history=1
    )
    assert res_edge1["estimated_avg_cost"] > 10000.0
    assert res_edge1["duration_days"] >= 1

    # 2. Young age and zero comorbidities
    res_edge2 = cost_predictor.predict(
        treatment_name="Appendectomy",
        age=18,
        comorbidity_count=0,
        has_diabetes=0,
        has_hypertension=0,
        has_cardiac_history=0
    )
    assert res_edge2["estimated_avg_cost"] > 10000.0
    assert res_edge2["duration_days"] >= 1

    # 3. None / missing values via API endpoint
    api_res = client.post("/api/cost/predict", json={
        "treatment_name": "Coronary Angioplasty"
    }, headers=_demo_auth_headers())
    assert api_res.status_code == 200
    api_data = api_res.json()
    assert api_data["estimated_avg_cost"] > 10000.0
