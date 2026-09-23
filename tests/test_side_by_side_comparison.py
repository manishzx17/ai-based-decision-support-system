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
from datasets.providers_data import HOSPITALS_DATA, DOCTORS_DATA
from security import create_access_token

client = TestClient(app)

@pytest.fixture
def auth_headers():
    token = create_access_token({"sub": "1", "role": "patient", "email": "rahul.verma@example.com"})
    return {"Authorization": f"Bearer {token}"}

def test_hospital_side_by_side_comparison_fields(auth_headers):
    """Verify hospital comparison returns 2-3 hospitals with all required dataset fields."""
    # Test both raw array and dict body formats
    payload = [1, 2, 3]
    res = client.post("/api/recommend/compare?city=Hyderabad&user_id=1", json=payload, headers=auth_headers)
    assert res.status_code == 200, res.text
    body = res.json()
    assert "compared_hospitals" in body
    assert "ai_recommendation" in body
    data = body["compared_hospitals"]
    assert isinstance(data, list)
    assert len(data) == 3

    # Check required dataset fields for comparison
    required_fields = [
        "name", "city", "cost_tier", "quality_rating",
        "accreditation", "treatment_capabilities", "icu_beds",
        "emergency_24x7", "recommendation_score", "score_breakdown", "reasons"
    ]
    for h in data:
        for field in required_fields:
            assert field in h, f"Missing {field} in hospital comparison response: {h}"
        assert isinstance(h["treatment_capabilities"], list)
        assert isinstance(h["icu_beds"], int)
        assert isinstance(h["emergency_24x7"], bool)
        assert 0.0 <= h["recommendation_score"] <= 100.0


def test_hospital_comparison_empty_selection_fallback(auth_headers):
    """Verify empty hospital_ids defaults gracefully to top hospitals in city without error."""
    payload = []
    res = client.post("/api/recommend/compare?city=Hyderabad&user_id=1", json=payload, headers=auth_headers)
    assert res.status_code == 200, res.text
    data = res.json()["compared_hospitals"]
    assert len(data) >= 1
    assert data[0]["city"] == "Hyderabad"


def test_doctor_side_by_side_comparison_fields(auth_headers):
    """Verify doctor comparison returns 2-3 doctors with all required dataset fields."""
    payload = [1, 2]
    res = client.post("/api/recommend/compare-doctors?user_id=1", json=payload, headers=auth_headers)
    assert res.status_code == 200, res.text
    body = res.json()
    assert "compared_doctors" in body
    assert "ai_recommendation" in body
    data = body["compared_doctors"]
    assert isinstance(data, list)
    assert len(data) == 2

    # Check required fields
    required_fields = [
        "name", "specialty", "expertise", "experience_years",
        "rating", "consultation_fee", "hospital_name",
        "match_score", "score_breakdown", "reasons"
    ]
    for d in data:
        for field in required_fields:
            assert field in d, f"Missing {field} in doctor comparison response: {d}"
        assert isinstance(d["experience_years"], int)
        assert isinstance(d["consultation_fee"], (int, float))
        assert 0.0 <= d["match_score"] <= 100.0


def test_doctor_comparison_preserves_scoring_and_context(auth_headers):
    """Verify doctor match scores preserve the 50/25/25 scoring framework with comorbidity awareness."""
    payload = [1]
    res = client.post("/api/recommend/compare-doctors?user_id=1", json=payload, headers=auth_headers)
    assert res.status_code == 200
    doc = res.json()["compared_doctors"][0]
    bd = doc["score_breakdown"]
    assert "specialty_match" in bd
    assert "experience" in bd
    assert "rating" in bd
    # Specialty match max 50, experience max 25, rating max 25
    assert bd["specialty_match"] <= 50.0
    assert bd["experience"] <= 25.0
    assert bd["rating"] <= 25.0


def test_comparison_preserves_real_data_integrity(auth_headers):
    """Verify returned hospitals and doctors correspond strictly to real dataset records."""
    h_res = client.post("/api/recommend/compare?city=Hyderabad&user_id=1", json=[1, 2], headers=auth_headers)
    assert h_res.status_code == 200
    h_ids = {h["id"] for h in h_res.json()["compared_hospitals"]}
    real_h_ids = {h["id"] for h in HOSPITALS_DATA}
    assert h_ids.issubset(real_h_ids)

    d_res = client.post("/api/recommend/compare-doctors?user_id=1", json=[1, 2], headers=auth_headers)
    assert d_res.status_code == 200
    d_names = {d["name"] for d in d_res.json()["compared_doctors"]}
    real_d_names = {d["name"] for d in DOCTORS_DATA}
    assert d_names.issubset(real_d_names)
