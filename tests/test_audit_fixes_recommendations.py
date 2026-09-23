import sys
import os
import pytest
from fastapi.testclient import TestClient

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND_DIR = os.path.join(BASE_DIR, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from main import app
from database import SessionLocal
from models import User, PatientProfile, MedicalReport, ExtractedEntity, Doctor
from security import create_access_token
from ai.recommendation_engine import recommendation_engine

client = TestClient(app)

@pytest.fixture
def auth_header_user1():
    token = create_access_token({"sub": "1", "role": "patient", "email": "patient@example.com"})
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def auth_header_user2():
    token = create_access_token({"sub": "2", "role": "patient", "email": "patient2@example.com"})
    return {"Authorization": f"Bearer {token}"}

# =============================================================================
# 1. SUPPORTED SPECIALTIES TESTS (HOSPITALS & DOCTORS)
# =============================================================================

def test_all_supported_hospital_specialties(auth_header_user1):
    """Verify that all 8 supported specialties filter to hospitals with that department."""
    specialties = [
        "Cardiology", "Neurology", "Oncology", "Orthopedics",
        "Gastroenterology", "Nephrology", "Pulmonology", "General Medicine"
    ]
    for spec in specialties:
        res = client.get(f"/api/recommend/hospitals?specialty={spec}", headers=auth_header_user1)
        assert res.status_code == 200, res.text
        data = res.json()
        assert len(data) > 0, f"Expected hospitals for {spec}"
        # Every hospital must contain the specialty (or general medicine broad)
        if spec != "General Medicine":
            for h in data:
                assert any(spec.lower() in s.lower() for s in h["specialties"]), f"Hospital {h['name']} lacks {spec}"
        # Verify ranking is strictly descending
        scores = [h["recommendation_score"] for h in data]
        assert scores == sorted(scores, reverse=True), f"Hospitals for {spec} not sorted descending"


def test_all_supported_doctor_specialties_including_nephrology(auth_header_user1):
    """Verify that all 8 supported doctor specialties (including Nephrology) return genuine matching specialists."""
    specialties = [
        "Cardiology", "Neurology", "Oncology", "Orthopedics",
        "Gastroenterology", "Nephrology", "Pulmonology", "General Medicine"
    ]
    for spec in specialties:
        res = client.get(f"/api/recommend/doctors?specialty={spec}", headers=auth_header_user1)
        assert res.status_code == 200, res.text
        doctors = res.json()
        assert len(doctors) > 0, f"Expected doctors for {spec}"
        # Every doctor must have the matching specialty
        for d in doctors:
            assert spec.lower() in d["specialty"].lower(), f"Doctor {d['name']} with specialty {d['specialty']} returned for {spec}"
        # Scores must be sorted descending
        scores = [d["match_score"] for d in doctors]
        assert scores == sorted(scores, reverse=True), f"Doctors for {spec} not sorted descending"


def test_nephrology_doctors_are_genuine_specialists(auth_header_user1):
    """Verify Nephrology specialists have realistic qualifications, ratings, and subspecialty expertise."""
    res = client.get("/api/recommend/doctors?specialty=Nephrology", headers=auth_header_user1)
    assert res.status_code == 200
    doctors = res.json()
    assert len(doctors) >= 4, f"Expected multiple Nephrologists, got {len(doctors)}"
    for doc in doctors:
        assert doc["specialty"] == "Nephrology"
        assert "Nephrology" in doc["qualification"] or "DM" in doc["qualification"] or "DNB" in doc["qualification"]
        assert doc["experience_years"] >= 10
        assert doc["rating"] >= 4.5
        assert isinstance(doc["expertise"], list) and len(doc["expertise"]) > 0

# =============================================================================
# 2. UNSUPPORTED SPECIALTY HANDLING (NO UNRELATED PROVIDERS)
# =============================================================================

def test_unsupported_specialty_hospitals_returns_empty(auth_header_user1):
    """If 0 hospitals match the specialty, return empty list and do not leak unrelated hospitals."""
    res = client.get("/api/recommend/hospitals?specialty=Dermatology", headers=auth_header_user1)
    assert res.status_code == 200
    assert res.json() == [], "Expected empty hospital list for unsupported specialty Dermatology"

    res_psych = client.get("/api/recommend/hospitals?specialty=Psychiatry", headers=auth_header_user1)
    assert res_psych.status_code == 200
    assert res_psych.json() == [], "Expected empty hospital list for unsupported specialty Psychiatry"


def test_unsupported_specialty_doctors_returns_empty(auth_header_user1):
    """If 0 doctors match the specialty, return empty list and do not leak unrelated doctors."""
    res = client.get("/api/recommend/doctors?specialty=Dermatology", headers=auth_header_user1)
    assert res.status_code == 200
    assert res.json() == [], "Expected empty doctor list for unsupported specialty Dermatology"

    res_psych = client.get("/api/recommend/doctors?specialty=Psychiatry", headers=auth_header_user1)
    assert res_psych.status_code == 200
    assert res_psych.json() == [], "Expected empty doctor list for unsupported specialty Psychiatry"

# =============================================================================
# 3. AUTHENTICATION & USER/REPORT ISOLATION (IDOR PROTECTION)
# =============================================================================

def test_unauthenticated_access_rejected_on_foreign_user():
    """Unauthenticated request attempting to query a foreign user must be rejected with 401."""
    res = client.get("/api/recommend/hospitals?user_id=2")
    assert res.status_code == 401

    res_doc = client.get("/api/recommend/doctors?user_id=2")
    assert res_doc.status_code == 401


def test_cross_user_user_id_tampering_rejected_with_403(auth_header_user1):
    """User 1 attempting to request User 2 recommendations must be rejected with 403."""
    res = client.get("/api/recommend/hospitals?user_id=2", headers=auth_header_user1)
    assert res.status_code == 403
    assert "Forbidden" in res.json()["detail"]

    res_doc = client.get("/api/recommend/doctors?user_id=2", headers=auth_header_user1)
    assert res_doc.status_code == 403

    res_comp = client.post("/api/recommend/compare?user_id=2", json=[1, 2], headers=auth_header_user1)
    assert res_comp.status_code == 403


def test_cross_user_report_id_access_rejected_with_403(auth_header_user1, auth_header_user2):
    """User 1 attempting to use User 2's report_id must be rejected with 403."""
    db = SessionLocal()
    try:
        # Find a report belonging to User 2
        user2_report = db.query(MedicalReport).filter(MedicalReport.user_id == 2).first()
        if not user2_report:
            # Create a report for User 2
            user2_report = MedicalReport(
                user_id=2,
                filename="user2_neuro_report.pdf",
                recommended_specialty="Neurology"
            )
            db.add(user2_report)
            db.commit()
            db.refresh(user2_report)
        u2_rep_id = user2_report.id
    finally:
        db.close()

    # User 1 tries to access recommendations with User 2's report_id
    res_h = client.get(f"/api/recommend/hospitals?report_id={u2_rep_id}", headers=auth_header_user1)
    assert res_h.status_code == 403
    assert "Medical report does not belong" in res_h.json()["detail"]

    res_d = client.get(f"/api/recommend/doctors?report_id={u2_rep_id}", headers=auth_header_user1)
    assert res_d.status_code == 403

    res_t = client.get(f"/api/recommend/treatments?report_id={u2_rep_id}", headers=auth_header_user1)
    assert res_t.status_code == 403

    res_comp = client.post(f"/api/recommend/compare?report_id={u2_rep_id}", json=[1, 2], headers=auth_header_user1)
    assert res_comp.status_code == 403

    # But User 2 accessing their own report must succeed (200)
    res_own = client.get(f"/api/recommend/hospitals?report_id={u2_rep_id}", headers=auth_header_user2)
    assert res_own.status_code == 200

# =============================================================================
# 4. ACTIVE REPORT RESOLUTION & RECOMMENDATION DYNAMICS
# =============================================================================

def test_report_derived_specialty_and_dropdown_override(auth_header_user1):
    """Without specialty param, uses report specialty. With explicit specialty param, overrides report."""
    db = SessionLocal()
    try:
        rep1 = db.query(MedicalReport).filter(MedicalReport.user_id == 1).first()
        assert rep1 is not None
        rep_id = rep1.id
        rep_spec = rep1.recommended_specialty or "Cardiology"
    finally:
        db.close()

    # Fallback to report specialty when specialty param omitted
    res_fallback = client.get(f"/api/recommend/hospitals?report_id={rep_id}", headers=auth_header_user1)
    assert res_fallback.status_code == 200
    top_fallback = res_fallback.json()[0]
    assert any(rep_spec.lower() in s.lower() for s in top_fallback["specialties"])

    # Explicit specialty override overrides report specialty
    override_spec = "Orthopedics"
    res_override = client.get(f"/api/recommend/hospitals?report_id={rep_id}&specialty={override_spec}", headers=auth_header_user1)
    assert res_override.status_code == 200
    top_override = res_override.json()[0]
    assert any("ortho" in s.lower() for s in top_override["specialties"])

# =============================================================================
# 5. FINDER VS COMPARISON SCORE CONSISTENCY
# =============================================================================

def test_finder_vs_comparison_score_consistency(auth_header_user1):
    """Compare page must produce exact same scores and breakdowns as Hospital Finder across priority modes."""
    modes = ["balanced", "cost_sensitive", "quality_focused", "proximity_focused"]
    budget = 400000.0
    insurance = "HDFC ERGO"
    city = "Hyderabad"
    spec = "Cardiology"

    for mode in modes:
        # Query Finder
        url_finder = f"/api/recommend/hospitals?specialty={spec}&city={city}&priority_mode={mode}&max_budget={budget}&insurance={insurance}"
        res_finder = client.get(url_finder, headers=auth_header_user1)
        assert res_finder.status_code == 200
        finder_h1 = res_finder.json()[0]

        # Query Compare with same context
        url_compare = f"/api/recommend/compare?specialty={spec}&city={city}&priority_mode={mode}&max_budget={budget}&insurance={insurance}"
        res_compare = client.post(url_compare, json=[finder_h1["id"]], headers=auth_header_user1)
        assert res_compare.status_code == 200
        compare_h1 = res_compare.json()["compared_hospitals"][0]

        assert finder_h1["recommendation_score"] == pytest.approx(compare_h1["recommendation_score"], abs=0.01), \
            f"Mode {mode} score mismatch: Finder={finder_h1['recommendation_score']} vs Compare={compare_h1['recommendation_score']}"

        assert finder_h1["score_breakdown"]["clinical_match"] == compare_h1["score_breakdown"]["clinical_match"]
        assert finder_h1["score_breakdown"]["cost_insurance"] == compare_h1["score_breakdown"]["cost_insurance"]
        assert finder_h1["score_breakdown"]["distance_proximity"] == compare_h1["score_breakdown"]["distance_proximity"]
        assert finder_h1["score_breakdown"]["quality_accreditation"] == compare_h1["score_breakdown"]["quality_accreditation"]

# =============================================================================
# 6. EXACT WEIGHT PRESERVATION TESTS
# =============================================================================

def test_hospital_exact_scoring_weights():
    """Verify hospital scoring formula remains strictly 35% Clinical, 25% Cost, 20% Proximity, 20% Quality."""
    weights = recommendation_engine.DEFAULT_WEIGHTS
    assert weights["clinical_match"] == 0.35
    assert weights["cost_insurance"] == 0.25
    assert weights["distance"] == 0.20
    assert weights["quality_accreditation"] == 0.20
    assert "availability" not in weights
    assert sum(weights.values()) == pytest.approx(1.0)


def test_doctor_exact_scoring_weights():
    """Verify doctor scoring formula remains strictly 50% Clinical, 25% Experience, 25% Rating."""
    sample_doc = {
        "id": 999,
        "name": "Dr. Test",
        "specialty": "Cardiology",
        "experience_years": 20,
        "rating": 5.0,
        "expertise": ["Coronary Angioplasty"]
    }
    scored = recommendation_engine.score_doctor(sample_doc, required_specialty="Cardiology")
    weights = scored["scoring_weights"]
    assert weights["specialty_match"] == 0.50
    assert weights["experience"] == 0.25
    assert weights["rating"] == 0.25
    assert sum(weights.values()) == pytest.approx(1.0)

    # 50% of 100 = 50.0; 25% of 80 = 20.0; 25% of 100 = 25.0 -> Total = 95.0
    bd = scored["score_breakdown"]
    assert bd["specialty_match"] == 50.0
    assert bd["experience"] == 20.0
    assert bd["rating"] == 25.0
    assert scored["match_score"] == 95.0
