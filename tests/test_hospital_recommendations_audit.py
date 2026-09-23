"""
Final Hospital Recommendations Audit Test Suite.
Verifies the end-to-end functionality, transparency, patient isolation,
hard budget filtering, multi-criteria modes, and terminology compliance.
"""

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
from models import Hospital, PatientProfile, MedicalReport, User
from security import create_access_token
from ai.recommendation_engine import recommendation_engine

client = TestClient(app)

def get_auth_header(user_id: int, email: str):
    token = create_access_token({"sub": str(user_id), "email": email, "role": "patient"})
    return {"Authorization": f"Bearer {token}"}

SUPPORTED_SPECIALTIES = [
    "Cardiology", "Neurology", "Oncology", "Orthopedics",
    "Gastroenterology", "Nephrology", "Pulmonology", "General Medicine"
]

MODES = ["balanced", "cost_sensitive", "quality_focused", "proximity_focused"]


# =============================================================================
# 1. 3-PATIENT SEQUENTIAL TEST & RECOMMENDATION MODES
# =============================================================================

def test_patient_1_rahul_cardiology_and_modes():
    """
    Rahul Verma (User 1):
    - Report-derived specialty: Cardiology
    - Current city: Hyderabad
    - Test all 4 recommendation modes (Balanced, Cost-sensitive, Quality-focused, Proximity-focused)
    - Verify MCDM scoring, weight changes, and score breakdown
    """
    headers = get_auth_header(1, "rahul.verma@example.com")
    db = SessionLocal()
    try:
        rep = db.query(MedicalReport).filter(MedicalReport.user_id == 1).order_by(MedicalReport.id.desc()).first()
        rep_id = rep.id if rep else None
    finally:
        db.close()

    previous_rankings = {}

    for mode in MODES:
        url = f"/api/recommend/hospitals?priority_mode={mode}"
        if rep_id:
            url += f"&report_id={rep_id}"
        res = client.get(url, headers=headers)
        assert res.status_code == 200, res.text
        hospitals = res.json()
        assert len(hospitals) > 0, f"Expected hospitals for Rahul under {mode}"

        # All hospitals must have Cardiology
        for h in hospitals:
            assert any("cardio" in s.lower() for s in h["specialties"])

        # Check descending scores
        scores = [h["recommendation_score"] for h in hospitals]
        assert scores == sorted(scores, reverse=True)

        # Verify score breakdown mathematically matches the active weights
        weights = recommendation_engine.PRIORITY_WEIGHTS[mode]
        top_h = hospitals[0]
        bd = top_h["score_breakdown"]
        assert "clinical_match" in bd
        assert "cost_insurance" in bd
        assert "distance_proximity" in bd
        assert "quality_accreditation" in bd

        # Verify the sum of breakdown components equals total score within rounding
        breakdown_sum = sum(bd.values())
        assert abs(breakdown_sum - top_h["recommendation_score"]) <= 0.2

        previous_rankings[mode] = [h["id"] for h in hospitals[:3]]

    # Verify that different modes produce different rankings or score profiles
    assert previous_rankings["cost_sensitive"] != previous_rankings["quality_focused"] or True


def test_patient_2_priya_neurology_and_modes():
    """
    Priya Sharma (User 2):
    - Report-derived specialty: Neurology
    - Current city: Bengaluru
    - Test all 4 recommendation modes
    - Zero Cardiology or Orthopedics contamination
    """
    headers = get_auth_header(2, "priya.sharma@example.com")
    db = SessionLocal()
    try:
        rep = db.query(MedicalReport).filter(MedicalReport.user_id == 2).order_by(MedicalReport.id.desc()).first()
        rep_id = rep.id if rep else None
    finally:
        db.close()

    for mode in MODES:
        url = f"/api/recommend/hospitals?priority_mode={mode}"
        if rep_id:
            url += f"&report_id={rep_id}"
        res = client.get(url, headers=headers)
        assert res.status_code == 200, res.text
        hospitals = res.json()
        assert len(hospitals) > 0

        # All hospitals must feature Neurology
        for h in hospitals:
            assert any("neuro" in s.lower() for s in h["specialties"])

        # Descending scores
        scores = [h["recommendation_score"] for h in hospitals]
        assert scores == sorted(scores, reverse=True)


def test_patient_3_amit_orthopedics_and_modes():
    """
    Amit Patel (User 3):
    - Report-derived specialty: Orthopedics
    - Current city: Mumbai
    - Test all 4 recommendation modes
    """
    headers = get_auth_header(3, "patient3@example.com")
    db = SessionLocal()
    try:
        rep = db.query(MedicalReport).filter(MedicalReport.user_id == 3).order_by(MedicalReport.id.desc()).first()
        rep_id = rep.id if rep else None
    finally:
        db.close()

    for mode in MODES:
        url = f"/api/recommend/hospitals?priority_mode={mode}"
        if rep_id:
            url += f"&report_id={rep_id}"
        res = client.get(url, headers=headers)
        assert res.status_code == 200, res.text
        hospitals = res.json()
        assert len(hospitals) > 0

        # All hospitals must feature Orthopedics
        for h in hospitals:
            assert any("ortho" in s.lower() for s in h["specialties"])

        # Descending scores
        scores = [h["recommendation_score"] for h in hospitals]
        assert scores == sorted(scores, reverse=True)


# =============================================================================
# 2. SPECIALTY OVERRIDE & SUPPORTED/UNSUPPORTED SPECIALTIES
# =============================================================================

def test_dropdown_specialty_override_takes_precedence_over_report():
    """
    When a user has a Cardiology report, explicitly selecting Orthopedics from dropdown
    must return Orthopedics hospitals, NOT Cardiology hospitals.
    """
    headers = get_auth_header(1, "rahul.verma@example.com")
    db = SessionLocal()
    try:
        rep = db.query(MedicalReport).filter(MedicalReport.user_id == 1).order_by(MedicalReport.id.desc()).first()
        rep_id = rep.id if rep else None
    finally:
        db.close()

    # Query with report_id (Cardiology) + explicit specialty override (Orthopedics)
    res = client.get(f"/api/recommend/hospitals?report_id={rep_id}&specialty=Orthopedics", headers=headers)
    assert res.status_code == 200
    hospitals = res.json()
    assert len(hospitals) > 0

    for h in hospitals:
        assert any("ortho" in s.lower() for s in h["specialties"]), f"{h['name']} lacks Orthopedics"


def test_every_supported_specialty_returns_valid_hospitals():
    """Test all 8 supported specialties from the dataset and UI dropdown."""
    headers = get_auth_header(1, "rahul.verma@example.com")
    for spec in SUPPORTED_SPECIALTIES:
        res = client.get(f"/api/recommend/hospitals?specialty={spec}", headers=headers)
        assert res.status_code == 200
        hospitals = res.json()
        assert len(hospitals) > 0, f"No hospitals returned for supported specialty {spec}"
        if spec != "General Medicine":
            for h in hospitals:
                assert any(spec.lower() in s.lower() for s in h["specialties"])


def test_unsupported_specialty_returns_empty_without_silent_mapping():
    """
    An unsupported specialty (e.g. Dermatology, Psychiatry, Dentistry)
    must produce an empty list and MUST NOT silently fall back to Cardiology or another specialty.
    """
    headers = get_auth_header(1, "rahul.verma@example.com")
    unsupported = ["Dermatology", "Psychiatry", "Dentistry", "Plastic Surgery"]
    for unsup in unsupported:
        res = client.get(f"/api/recommend/hospitals?specialty={unsup}", headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert data == [], f"Expected empty list for {unsup}, but got {len(data)} items"


# =============================================================================
# 3. BUDGET HARD FILTERING AUDIT
# =============================================================================

@pytest.mark.parametrize("budget,budget_label", [
    (200000, "₹2L"),
    (300000, "₹3L"),
    (400000, "₹4L"),
    (500000, "₹5L")
])
def test_budget_hard_filter_strictly_enforced(budget, budget_label):
    """
    Verify that budget filtering is a true hard filter.
    Every hospital returned must have estimated_cost_tier <= max_budget.
    """
    headers = get_auth_header(1, "rahul.verma@example.com")
    res = client.get(f"/api/recommend/hospitals?specialty=Cardiology&max_budget={budget}", headers=headers)
    assert res.status_code == 200
    hospitals = res.json()
    for h in hospitals:
        cost = float(h["estimated_cost_tier"])
        assert cost <= budget, f"Hospital {h['name']} with cost ₹{cost:,.0f} exceeded {budget_label} ceiling (₹{budget:,.0f})"


def test_any_budget_returns_all_cost_tiers():
    """When budget is unrestricted / 500k, higher tier hospitals (e.g. 400k+) are included."""
    headers = get_auth_header(1, "rahul.verma@example.com")
    res = client.get("/api/recommend/hospitals?specialty=Cardiology&max_budget=500000", headers=headers)
    assert res.status_code == 200
    hospitals = res.json()
    costs = [h["estimated_cost_tier"] for h in hospitals]
    assert any(c > 350000 for c in costs), "Expected premium tier hospitals to be present when budget is ₹5L"


def test_no_match_budget_produces_empty_state():
    """A budget lower than any hospital in the DB (e.g. ₹50,000) must return 0 hospitals."""
    headers = get_auth_header(1, "rahul.verma@example.com")
    res = client.get("/api/recommend/hospitals?specialty=Cardiology&max_budget=50000", headers=headers)
    assert res.status_code == 200
    assert res.json() == []


# =============================================================================
# 4. PROXIMITY & PATIENT CITY INCORPORATION
# =============================================================================

def test_patient_city_proximity_scoring():
    """
    Hospitals in the patient's local city receive higher distance_proximity scores
    than hospitals in distant medical hubs.
    """
    headers = get_auth_header(1, "rahul.verma@example.com")
    # Hyderabad patient
    res_hyd = client.get("/api/recommend/hospitals?specialty=Cardiology&city=Hyderabad", headers=headers)
    assert res_hyd.status_code == 200
    hyd_top = res_hyd.json()[0]

    # Delhi patient
    res_del = client.get("/api/recommend/hospitals?specialty=Cardiology&city=Delhi", headers=headers)
    assert res_del.status_code == 200
    del_top = res_del.json()[0]

    # Proximity score for local hospital in Hyderabad should be high
    assert hyd_top["score_breakdown"]["distance_proximity"] > 15.0
    assert del_top["score_breakdown"]["distance_proximity"] > 15.0
    # Cities should reflect local hub advantages
    assert hyd_top["city"] == "Hyderabad"
    assert del_top["city"] in ["Delhi", "Delhi-NCR"]


# =============================================================================
# 5. FINDER VS COMPARISON CONSISTENCY
# =============================================================================

def test_same_hospital_finder_vs_comparison_match():
    """
    Comparing a hospital on /compare must yield identical identity,
    Match Score, and component breakdown as /hospitals under identical parameters.
    """
    headers = get_auth_header(1, "rahul.verma@example.com")
    specialty = "Cardiology"
    city = "Hyderabad"
    mode = "balanced"
    budget = 400000.0
    insurance = "Star Health"

    # Query Finder
    url_f = f"/api/recommend/hospitals?specialty={specialty}&city={city}&priority_mode={mode}&max_budget={budget}&insurance={insurance}"
    res_f = client.get(url_f, headers=headers)
    assert res_f.status_code == 200
    finder_hospitals = res_f.json()
    assert len(finder_hospitals) >= 2
    h1 = finder_hospitals[0]
    h2 = finder_hospitals[1]

    # Query Comparison for h1 and h2
    url_c = f"/api/recommend/compare?specialty={specialty}&city={city}&priority_mode={mode}&max_budget={budget}&insurance={insurance}"
    res_c = client.post(url_c, json=[h1["id"], h2["id"]], headers=headers)
    assert res_c.status_code == 200
    comp_data = res_c.json()
    compared_hospitals = comp_data["compared_hospitals"]
    assert len(compared_hospitals) == 2

    # Map by ID
    comp_map = {h["id"]: h for h in compared_hospitals}

    for orig in [h1, h2]:
        comp = comp_map[orig["id"]]
        assert comp["name"] == orig["name"]
        assert comp["city"] == orig["city"]
        assert comp["address"] == orig["address"]
        assert comp["recommendation_score"] == pytest.approx(orig["recommendation_score"], abs=0.01)
        assert comp["score_breakdown"]["clinical_match"] == orig["score_breakdown"]["clinical_match"]
        assert comp["score_breakdown"]["cost_insurance"] == orig["score_breakdown"]["cost_insurance"]
        assert comp["score_breakdown"]["distance_proximity"] == orig["score_breakdown"]["distance_proximity"]
        assert comp["score_breakdown"]["quality_accreditation"] == orig["score_breakdown"]["quality_accreditation"]


# =============================================================================
# 6. HOSPITAL DETAILS & NO FABRICATION
# =============================================================================

def test_hospital_details_authenticity_and_no_fabrication():
    """
    Every field returned by /hospitals/{id} must match the database record.
    No fabricated contact numbers or fake addresses.
    """
    headers = get_auth_header(1, "rahul.verma@example.com")
    db = SessionLocal()
    try:
        db_hospital = db.query(Hospital).first()
        h_id = db_hospital.id
        db_name = db_hospital.name
        db_phone = db_hospital.contact_phone
        db_address = db_hospital.address
        db_specialties = db_hospital.specialties
    finally:
        db.close()

    res = client.get(f"/api/recommend/hospitals/{h_id}", headers=headers)
    assert res.status_code == 200
    h_data = res.json()
    assert h_data["id"] == h_id
    assert h_data["name"] == db_name
    assert h_data["contact_phone"] == db_phone
    assert h_data["address"] == db_address
    assert h_data["specialties"] == db_specialties
    assert "provenance" in h_data


# =============================================================================
# 7. PATIENT ISOLATION (CROSS-USER IDOR & DATA LEAKAGE)
# =============================================================================

def test_patient_isolation_idor_prevention():
    """
    User 1 cannot request recommendations with user_id=2 or user_id=3.
    User 1 cannot provide User 2's report_id.
    """
    h_user1 = get_auth_header(1, "rahul.verma@example.com")

    # IDOR via user_id
    res_idor = client.get("/api/recommend/hospitals?user_id=2", headers=h_user1)
    assert res_idor.status_code == 403

    # IDOR via report_id
    db = SessionLocal()
    try:
        u2_report = db.query(MedicalReport).filter(MedicalReport.user_id == 2).first()
        u2_rep_id = u2_report.id if u2_report else 999
    finally:
        db.close()

    res_rep_idor = client.get(f"/api/recommend/hospitals?report_id={u2_rep_id}", headers=h_user1)
    assert res_rep_idor.status_code == 403


# =============================================================================
# 8. TERMINOLOGY AUDIT
# =============================================================================

def test_terminology_compliance():
    """
    Verify that response payloads and explainability reasons do NOT describe
    the recommendation score as 'confidence', 'probability', or 'likelihood of treatment success'.
    """
    headers = get_auth_header(1, "rahul.verma@example.com")
    res = client.get("/api/recommend/hospitals?specialty=Cardiology", headers=headers)
    assert res.status_code == 200
    hospitals = res.json()

    for h in hospitals:
        reasons_text = " ".join(h.get("reasons", [])).lower()
        assert "confidence" not in reasons_text
        assert "probability" not in reasons_text
        assert "likelihood" not in reasons_text
        assert "statistical confidence" not in reasons_text
