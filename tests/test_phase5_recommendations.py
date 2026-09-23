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
from ai.recommendation_engine import recommendation_engine, RecommendationEngine
from datasets.providers_data import HOSPITALS_DATA, DOCTORS_DATA

client = TestClient(app)

# =============================================================================
# 1. DATASET 3 INTEGRITY & BENCHMARK PROVENANCE TESTS
# =============================================================================

def test_dataset3_counts_and_distribution():
    """Verify Dataset 3 scale: 60 hospitals, 210 doctors across 6 Indian medical hubs."""
    assert len(HOSPITALS_DATA) == 60, f"Expected 60 hospitals, got {len(HOSPITALS_DATA)}"
    assert len(DOCTORS_DATA) >= 210, f"Expected at least 210 doctors, got {len(DOCTORS_DATA)}"

    cities = {h["city"] for h in HOSPITALS_DATA}
    expected_cities = {"Hyderabad", "Bengaluru", "Chennai", "Mumbai", "Delhi-NCR", "Kolkata"}
    assert expected_cities.issubset(cities), f"Missing cities: {expected_cities - cities}"


def test_dataset3_hospital_structured_fields():
    """Verify hospital structured fields, cost tier, ratings, and capabilities."""
    for h in HOSPITALS_DATA:
        assert "id" in h
        assert "name" in h and len(h["name"]) > 0
        assert "city" in h
        assert "lat" in h and "lng" in h
        assert isinstance(h["specialties"], list) and len(h["specialties"]) >= 3
        assert "cost_tier" in h and h["cost_tier"] in ["Budget", "Moderate", "Premium", "Super-Specialty"]
        assert "quality_rating" in h and 4.0 <= h["quality_rating"] <= 5.0
        assert "accreditation" in h and len(h["accreditation"]) > 0
        assert isinstance(h["treatment_capabilities"], list)
        assert isinstance(h["insurance_accepted"], list) and len(h["insurance_accepted"]) >= 3
        assert "emergency_24x7" in h and isinstance(h["emergency_24x7"], bool)
        assert "icu_beds" in h and h["icu_beds"] > 0


def test_dataset3_doctor_structured_fields():
    """Verify doctor structured fields, expertise, and affiliation."""
    for d in DOCTORS_DATA:
        assert "id" in d
        assert "hospital_id" in d
        assert "name" in d and len(d["name"]) > 0
        assert "specialty" in d and len(d["specialty"]) > 0
        assert "experience_years" in d and d["experience_years"] >= 5
        assert "rating" in d and 4.0 <= d["rating"] <= 5.0
        assert "consultation_fee" in d and d["consultation_fee"] > 0
        assert isinstance(d["expertise"], list) and len(d["expertise"]) >= 1


def test_dataset3_synthetic_provenance_labeling():
    """Verify that records are explicitly flagged as synthetic research benchmark."""
    for h in HOSPITALS_DATA:
        assert "provenance" in h
        assert h["provenance"].get("is_synthetic_benchmark") is True
        assert "benchmark_purpose" in h["provenance"]

    for d in DOCTORS_DATA:
        assert "provenance" in d
        assert d["provenance"].get("is_synthetic_benchmark") is True


# =============================================================================
# 2. STAGE 1 TRANSPARENT ELIGIBILITY FILTERING TESTS
# =============================================================================

def test_stage1_specialty_eligibility_filtering():
    """Verify that hospitals lacking the required specialty are excluded with reasons."""
    oncology_prefs = {"specialty": "Oncology"}
    eligible, excluded = recommendation_engine.filter_eligible_hospitals(
        HOSPITALS_DATA,
        preferences=oncology_prefs
    )
    assert len(eligible) > 0
    # Every eligible hospital must have Oncology
    for h in eligible:
        assert any("onco" in s.lower() for s in h["specialties"])

    # Excluded hospitals must have an exclusion reason
    for x in excluded:
        assert "exclusion_reasons" in x
        assert any("Oncology" in r for r in x["exclusion_reasons"])


def test_stage1_budget_ceiling_filtering():
    """Verify that strict budget ceiling excludes hospitals exceeding the budget."""
    low_budget_prefs = {"specialty": "Cardiology", "max_budget_inr": 250000.0}
    eligible, excluded = recommendation_engine.filter_eligible_hospitals(
        HOSPITALS_DATA,
        preferences=low_budget_prefs
    )
    # Excluded premium hospitals should cite budget ceiling
    for x in excluded:
        if x.get("estimated_cost_tier", 0) > 250000.0:
            assert any("budget" in r.lower() for r in x["exclusion_reasons"])


def test_stage1_doctor_specialty_filtering():
    """Verify that doctors are filtered by required clinical specialty."""
    neuro_prefs = {"specialty": "Neurology"}
    eligible, excluded = recommendation_engine.filter_eligible_doctors(
        DOCTORS_DATA,
        preferences=neuro_prefs
    )
    assert len(eligible) > 0
    for d in eligible:
        assert "neuro" in d["specialty"].lower()


# =============================================================================
# 3. STAGE 2 BASELINE WEIGHTS & SCORING INVARIANTS (35/25/20/20)
# =============================================================================

def test_baseline_weights_sum_to_one_and_exclude_availability():
    """Verify that baseline weights are strictly 35/25/20/20 and availability is 0%."""
    weights = recommendation_engine.DEFAULT_WEIGHTS
    assert weights["clinical_match"] == 0.35
    assert weights["cost_insurance"] == 0.25
    assert weights["distance"] == 0.20
    assert weights["quality_accreditation"] == 0.20
    assert "availability" not in weights
    assert sum(weights.values()) == pytest.approx(1.0)


def test_hospital_score_breakdown_matches_total():
    """Verify that hospital recommendation score equals sum of weighted components."""
    sample_hosp = HOSPITALS_DATA[0]
    scored = recommendation_engine.score_hospital(
        sample_hosp,
        required_specialty="Cardiology",
        patient_city="Hyderabad",
        max_budget=500000.0,
        preferred_insurance="Star Health",
        priority_mode="balanced"
    )
    bd = scored["score_breakdown"]
    total = sum(bd.values())
    assert scored["recommendation_score"] == pytest.approx(round(total, 1), abs=0.15)
    # Check max point bounds
    assert bd["clinical_match"] <= 35.0
    assert bd["cost_insurance"] <= 25.0
    assert bd["distance_proximity"] <= 20.0
    assert bd["quality_accreditation"] <= 20.0


def test_priority_modes_transparent_weight_shifting():
    """Verify that priority modes shift weights transparently."""
    modes = ["balanced", "cost_sensitive", "quality_focused", "proximity_focused"]
    for mode in modes:
        weights = recommendation_engine.PRIORITY_WEIGHTS[mode]
        assert sum(weights.values()) == pytest.approx(1.0)
        assert "availability" not in weights

    # Cost sensitive shifts cost weight to 40%
    assert recommendation_engine.PRIORITY_WEIGHTS["cost_sensitive"]["cost_insurance"] == 0.40
    # Quality focused shifts quality weight to 35%
    assert recommendation_engine.PRIORITY_WEIGHTS["quality_focused"]["quality_accreditation"] == 0.35
    # Proximity focused shifts distance weight to 40%
    assert recommendation_engine.PRIORITY_WEIGHTS["proximity_focused"]["distance"] == 0.40


# =============================================================================
# 4. PERSONALIZATION SENSITIVITY TESTS
# =============================================================================

def test_personalization_sensitivity_by_city():
    """Changing patient city must reorder top recommended hospitals based on distance."""
    profile = {"conditions": ["Coronary Artery Disease"], "demographics": {"current_city": "Hyderabad"}}
    
    res_hyd = recommendation_engine.get_personalized_recommendations(
        clinical_profile=profile,
        preferences={"preferred_city": "Hyderabad", "priority_mode": "proximity_focused"}
    )
    res_mum = recommendation_engine.get_personalized_recommendations(
        clinical_profile=profile,
        preferences={"preferred_city": "Mumbai", "priority_mode": "proximity_focused"}
    )
    top_hyd = res_hyd["recommended_hospitals"][0]
    top_mum = res_mum["recommended_hospitals"][0]

    assert top_hyd["city"] == "Hyderabad"
    assert top_mum["city"] == "Mumbai"
    assert top_hyd["id"] != top_mum["id"]


def test_personalization_sensitivity_by_specialty():
    """Changing clinical specialty must recommend matching hospitals and specialists."""
    cardio_profile = {"conditions": ["Angina", "Coronary Artery Disease"]}
    ortho_profile = {"conditions": ["Knee Osteoarthritis", "Total Knee Arthroplasty"]}

    res_cardio = recommendation_engine.get_personalized_recommendations(
        clinical_profile=cardio_profile,
        preferences={"preferred_city": "Hyderabad"}
    )
    res_ortho = recommendation_engine.get_personalized_recommendations(
        clinical_profile=ortho_profile,
        preferences={"preferred_city": "Hyderabad"}
    )

    top_cardio_doc = res_cardio["recommended_doctors"][0]
    top_ortho_doc = res_ortho["recommended_doctors"][0]

    assert "cardio" in top_cardio_doc["specialty"].lower()
    assert "ortho" in top_ortho_doc["specialty"].lower()


# =============================================================================
# 5. RAG EVIDENCE-GROUNDED TREATMENT PATHWAYS TESTS
# =============================================================================

def test_treatment_pathways_grounded_exclusively_in_rag():
    """Treatment pathways must come from Phase 4 RAG guidelines, not fabricated claims."""
    pathways = recommendation_engine.match_treatment_pathways(
        condition="Coronary Artery Disease",
        specialty="Cardiology"
    )
    assert len(pathways) >= 1
    p1 = pathways[0]
    assert "pathway_name" in p1
    assert "description" in p1
    assert "grounding_sources" in p1 and len(p1["grounding_sources"]) > 0
    # Citations must reference legitimate medical organizations (ESC, ACC, etc.)
    source_orgs = [s["organization"] for s in p1["grounding_sources"]]
    assert any("ESC" in org or "European Society" in org or "ACC" in org or "Cardiology" in org for org in source_orgs)


# =============================================================================
# 6. FASTAPI ENDPOINTS INTEGRATION TESTS
# =============================================================================

def test_api_recommend_personalized_endpoint():
    """Verify POST /api/recommend/personalized returns complete decision support payload."""
    payload = {
        "clinical_profile": {
            "conditions": ["Coronary Artery Disease", "Angina"],
            "symptoms": ["Chest pain on exertion"],
            "current_city": "Hyderabad"
        },
        "preferences": {
            "preferred_city": "Hyderabad",
            "insurance_provider": "Star Health",
            "priority_mode": "balanced"
        },
        "top_hospitals": 3,
        "top_doctors": 3,
        "top_pathways": 2
    }
    response = client.post("/api/recommend/personalized", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()

    assert data["priority_mode"] == "balanced"
    assert data["active_weights"]["clinical_match"] == 0.35
    assert len(data["hospitals"]) == 3
    assert len(data["doctors"]) == 3
    assert len(data["treatment_pathways"]) >= 1
    assert "synthetic_benchmark_notice" in data
    assert "eligibility_audit" in data

    # Hospital fields check
    h0 = data["hospitals"][0]
    assert "score_breakdown" in h0
    assert "clinical_match" in h0["score_breakdown"]


def test_api_recommend_hospitals_endpoint():
    """Verify GET /api/recommend/hospitals with priority_mode query parameter."""
    response = client.get("/api/recommend/hospitals?specialty=Cardiology&city=Hyderabad&priority_mode=quality_focused")
    assert response.status_code == 200, response.text
    hospitals = response.json()
    assert len(hospitals) > 0
    top = hospitals[0]
    assert top["city"] == "Hyderabad"
    assert "recommendation_score" in top
    assert top["recommendation_score"] > 80.0


def test_api_recommend_doctors_endpoint():
    """Verify GET /api/recommend/doctors with specialty and expertise."""
    response = client.get("/api/recommend/doctors?specialty=Cardiology&city=Hyderabad")
    assert response.status_code == 200, response.text
    doctors = response.json()
    assert len(doctors) > 0
    top = doctors[0]
    assert "match_score" in top
    assert "expertise" in top
    assert isinstance(top["expertise"], list)
