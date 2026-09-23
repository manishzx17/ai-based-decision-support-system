import pytest
import os
import sys
import json

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from fastapi.testclient import TestClient
from main import app
from database import SessionLocal
import models
from ai.recommendation_engine import recommendation_engine
from ai.cost_prediction import cost_predictor
from security import create_access_token

client = TestClient(app)

@pytest.fixture(scope="module")
def auth_headers():
    db = SessionLocal()
    try:
        user = db.query(models.User).filter(models.User.id == 1).first()
        if not user:
            user = models.User(
                id=1,
                email="patient@example.com",
                hashed_password="hashed_demo_pw",
                full_name="Rahul Verma",
                role="patient"
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        token = create_access_token({"sub": str(user.id), "email": user.email})
        return {"Authorization": f"Bearer {token}"}
    finally:
        db.close()


def test_hard_budget_filter_strict_exclusion():
    """
    Verify max_budget acts as a TRUE hard eligibility filter:
    Any hospital whose estimated_cost_tier > max_budget is strictly excluded.
    """
    with open("backend/datasets/providers/hospitals.json") as f:
        hospitals = json.load(f)

    # 1. Budget 200,000 INR
    el_200k, ex_200k = recommendation_engine.filter_eligible_hospitals(
        hospitals,
        preferences={"specialty": "Cardiology", "max_budget": 200000.0}
    )
    assert len(el_200k) > 0, "Expected at least 1 hospital under 200k"
    for h in el_200k:
        assert h["estimated_cost_tier"] <= 200000.0, f"Hospital {h['name']} exceeded budget ceiling"

    # 2. Budget 100,000 INR (lower than minimum dataset tier 150,000 INR)
    el_100k, ex_100k = recommendation_engine.filter_eligible_hospitals(
        hospitals,
        preferences={"specialty": "Cardiology", "max_budget": 100000.0}
    )
    assert len(el_100k) == 0, f"Expected 0 hospitals under 100k, found {len(el_100k)}"
    assert len(ex_100k) == len(hospitals)

    # 3. Budget 300,000 INR
    el_300k, _ = recommendation_engine.filter_eligible_hospitals(
        hospitals,
        preferences={"specialty": "Cardiology", "max_budget": 300000.0}
    )
    for h in el_300k:
        assert h["estimated_cost_tier"] <= 300000.0


def test_api_hard_budget_filter_endpoint(auth_headers):
    """
    Verify /api/recommend/hospitals enforces hard budget filtering via HTTP.
    """
    res_200k = client.get("/api/recommend/hospitals?specialty=Cardiology&max_budget=200000", headers=auth_headers)
    assert res_200k.status_code == 200
    hospitals_200k = res_200k.json()
    assert len(hospitals_200k) > 0
    for h in hospitals_200k:
        assert h["estimated_cost_tier"] <= 200000.0, f"{h['name']} cost {h['estimated_cost_tier']} exceeds 200k"

    # Budget 100k should return []
    res_100k = client.get("/api/recommend/hospitals?specialty=Cardiology&max_budget=100000", headers=auth_headers)
    assert res_100k.status_code == 200
    assert res_100k.json() == []


def test_four_priority_modes_weights_and_ranking_shift():
    """
    Verify Balanced, Cost Sensitive, Quality Focused, and Proximity Focused modes
    shift rankings and have weights summing to 1.0.
    """
    for mode, weights in recommendation_engine.PRIORITY_WEIGHTS.items():
        total_w = sum(weights.values())
        assert abs(total_w - 1.0) < 1e-6, f"Mode {mode} weights sum to {total_w} != 1.0"

    with open("backend/datasets/providers/hospitals.json") as f:
        hospitals = json.load(f)

    # Score across modes
    modes = ["balanced", "cost_sensitive", "quality_focused", "proximity_focused"]
    rankings = {}
    for m in modes:
        scored = [
            recommendation_engine.score_hospital(
                h,
                required_specialty="Cardiology",
                patient_city="Hyderabad",
                max_budget=300000.0,
                preferred_insurance="Star Health",
                priority_mode=m
            )
            for h in hospitals if any("cardio" in s.lower() for s in h.get("specialties", []))
        ]
        scored.sort(key=lambda x: x["recommendation_score"], reverse=True)
        rankings[m] = [s["name"] for s in scored[:3]]

    # Cost-sensitive should rank lower cost facility #1
    assert "KIMS" in rankings["cost_sensitive"][0] or "Care" in rankings["cost_sensitive"][0]
    # Quality-focused top 3 should include high rating facilities (Apollo / AIG / Yashoda)
    top_quality = " ".join(rankings["quality_focused"])
    assert "Apollo" in top_quality or "AIG" in top_quality or "Yashoda" in top_quality


def test_hospital_details_rich_metadata(auth_headers):
    """
    Verify Hospital Details endpoint returns all rich unutilized fields:
    address, specialties, treatment_capabilities, accreditation, icu_beds, emergency_24x7, cost_tier.
    """
    res = client.get("/api/recommend/hospitals/1", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()

    assert "address" in data and len(data["address"]) > 0
    assert "specialties" in data and isinstance(data["specialties"], list) and len(data["specialties"]) > 0
    assert "treatment_capabilities" in data and isinstance(data["treatment_capabilities"], list) and len(data["treatment_capabilities"]) > 0
    assert "accreditation" in data and "NABH" in data["accreditation"]
    assert "icu_beds" in data and data["icu_beds"] > 0
    assert "emergency_24x7" in data
    assert "cost_tier" in data and len(data["cost_tier"]) > 0
    assert "estimated_cost_tier" in data and data["estimated_cost_tier"] > 0


def test_clinical_recovery_timeline_endpoint(auth_headers):
    """
    Verify /api/cost/recovery-timeline endpoint:
    - Uses predicted LOS from XGBoost
    - Returns 4 structured milestone phases
    - Returns RAG guideline citations
    - Contains safety disclaimer
    """
    res = client.post("/api/cost/recovery-timeline", json={
        "treatment_name": "Coronary Angioplasty",
        "city": "Hyderabad",
        "age": 55,
        "comorbidity_count": 0
    }, headers=auth_headers)
    assert res.status_code == 200
    data = res.json()

    assert data["treatment_name"] == "Coronary Angioplasty"
    assert "predicted_los_days" in data and data["predicted_los_days"] > 0
    assert "total_recovery_window_days" in data and data["total_recovery_window_days"] >= 4
    assert len(data["milestones"]) == 4

    phases = [m["phase"] for m in data["milestones"]]
    assert phases == ["Phase 1", "Phase 2", "Phase 3", "Phase 4"]

    statuses = [m["clearance_status"] for m in data["milestones"]]
    assert "Inpatient Care" in statuses
    assert "Fit for Travel" in statuses

    assert len(data["clinical_guideline_sources"]) > 0
    assert "CLINICAL DECISION SUPPORT NOTICE" in data["safety_disclaimer"]


def test_clinical_recovery_timeline_comorbidity_sensitivity(auth_headers):
    """
    Verify patient comorbidity profile prolongs predicted stay and affects timeline.
    """
    res_healthy = client.post("/api/cost/recovery-timeline", json={
        "treatment_name": "Coronary Angioplasty",
        "city": "Hyderabad",
        "age": 30,
        "has_diabetes": False,
        "has_hypertension": False,
        "has_cardiac_history": False
    }, headers=auth_headers)
    res_complex = client.post("/api/cost/recovery-timeline", json={
        "treatment_name": "Coronary Angioplasty",
        "city": "Hyderabad",
        "age": 70,
        "has_diabetes": True,
        "has_hypertension": True,
        "has_cardiac_history": True
    }, headers=auth_headers)

    los_healthy = res_healthy.json()["predicted_los_days"]
    los_complex = res_complex.json()["predicted_los_days"]
    assert los_complex > los_healthy, f"Expected complex patient LOS ({los_complex}) > healthy ({los_healthy})"


def test_finder_vs_comparison_score_consistency(auth_headers):
    """
    Verify same hospital produces identical score and breakdown in finder and comparison.
    """
    res_finder = client.get(
        "/api/recommend/hospitals?specialty=Cardiology&city=Hyderabad&max_budget=400000&insurance=Star%20Health&priority_mode=cost_sensitive",
        headers=auth_headers
    )
    assert res_finder.status_code == 200
    finder_hospitals = res_finder.json()
    assert len(finder_hospitals) > 0

    top_id = finder_hospitals[0]["id"]
    finder_score = finder_hospitals[0]["recommendation_score"]
    finder_bd = finder_hospitals[0]["score_breakdown"]

    res_comp = client.post(
        "/api/recommend/compare?specialty=Cardiology&city=Hyderabad&max_budget=400000&insurance=Star%20Health&priority_mode=cost_sensitive",
        json=[top_id],
        headers=auth_headers
    )
    assert res_comp.status_code == 200
    comp_hospitals = res_comp.json()["compared_hospitals"]
    assert len(comp_hospitals) == 1

    comp_score = comp_hospitals[0]["recommendation_score"]
    comp_bd = comp_hospitals[0]["score_breakdown"]

    assert abs(finder_score - comp_score) < 1e-4, f"Finder score {finder_score} != Comp score {comp_score}"
    for k in finder_bd:
        assert abs(finder_bd[k] - comp_bd[k]) < 1e-4, f"Breakdown mismatch on {k}"
