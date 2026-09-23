"""
Tests for Phase 9: Supporting 12C Features.

Verifies:
1. Pharmacy Finder:
   - Filter by city returning seeded backend data.
   - Search/filter by medication availability (e.g., stents, chemotherapy, insulin).
   - Empty response on non-existent medication.
2. Appointment Booking:
   - Authenticated creation with linked doctor and hospital.
   - Retrieval of user's own appointments.
   - IDOR prevention: cross-user appointment booking blocked with HTTP 403.
   - IDOR prevention: cross-user appointment retrieval blocked with HTTP 403.
   - Validation: 404 on non-existent doctor or hospital.
3. Medical Translation:
   - Functional translation capability preserving original clinical meaning and instructions.
   - Does NOT add unmentioned diagnoses, new medications, or clinical recommendations.
   - Multi-language functional support across regional Indian languages.
4. Insurance Assistance:
   - Seeded provider retrieval with policy and cashless details.
   - Contextual hospital & treatment coverage assistance.
   - Simulated benchmark turnaround time labeling.
5. Emergency & Local Health Support:
   - Configurable regional emergency contacts (India 112/108 demo) with non-universal notice.
   - Local health advisories, blood banks, and verified diagnostic centers.
"""

import sys
import os
import pytest
from fastapi.testclient import TestClient

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(os.path.dirname(CURRENT_DIR), "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from main import app
from init_db import init_db
from database import SessionLocal
from models import User, Hospital, Doctor, Pharmacy, InsuranceProvider, EmergencyContact, Appointment
from security import create_access_token

client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def setup_db():
    init_db()


def get_auth_headers(user_id=1, email="patient@example.com", role="patient"):
    token = create_access_token({"sub": str(user_id), "email": email, "role": role})
    return {"Authorization": f"Bearer {token}"}


# =========================================================================
# 1. Pharmacy Finder Tests
# =========================================================================

def test_pharmacy_finder_city_filter():
    """Verify filtering pharmacies by city returns backend seeded records with stock info."""
    response = client.get("/api/services/pharmacies?city=Hyderabad")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2
    for p in data:
        assert p["city"].lower() == "hyderabad"
        assert "name" in p
        assert "address" in p
        assert "medication_stock_summary" in p
        assert p["is_24_7"] is True


def test_pharmacy_finder_medicine_search():
    """Verify searching pharmacies by medication keyword filters stock correctly."""
    # Search for cardiac stents in Hyderabad
    resp_stents = client.get("/api/services/pharmacies?city=Hyderabad&medicine=stents")
    assert resp_stents.status_code == 200
    data_stents = resp_stents.json()
    assert len(data_stents) >= 1
    assert any("stents" in p["medication_stock_summary"].lower() for p in data_stents)

    # Search for oncology / chemotherapy in Delhi
    resp_onco = client.get("/api/services/pharmacies?city=Delhi&medicine=chemotherapy")
    assert resp_onco.status_code == 200
    data_onco = resp_onco.json()
    assert len(data_onco) >= 1
    assert "Delhi" in data_onco[0]["city"]

    # Search for a non-existent medication returns empty list
    resp_none = client.get("/api/services/pharmacies?city=Hyderabad&medicine=nonexistentmed999xyz")
    assert resp_none.status_code == 200
    assert resp_none.json() == []


# =========================================================================
# 2. Appointment Booking Tests
# =========================================================================

def test_appointment_booking_authenticated():
    """Verify authenticated user can book appointment with valid hospital and doctor."""
    headers = get_auth_headers(user_id=1)
    payload = {
        "hospital_id": 1,
        "doctor_id": 1,
        "patient_name": "Test Patient",
        "appointment_date": "2026-09-15",
        "appointment_time": "11:00 AM",
        "reason": "Pre-travel cardiology evaluation"
    }
    response = client.post("/api/services/appointments?user_id=1", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["hospital_id"] == 1
    assert data["doctor_id"] == 1
    assert data["patient_name"] == "Test Patient"
    assert data["status"] == "CONFIRMED"
    assert "id" in data


def test_appointment_retrieval_scoped_to_user():
    """Verify authenticated user can retrieve their own appointments."""
    headers = get_auth_headers(user_id=1)
    response = client.get("/api/services/appointments?user_id=1", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    for apt in data:
        assert apt["user_id"] == 1


def test_appointment_cross_user_booking_denied():
    """Verify attempting to book an appointment for another patient returns HTTP 403 Forbidden."""
    headers_user1 = get_auth_headers(user_id=1)
    payload = {
        "hospital_id": 1,
        "doctor_id": 1,
        "patient_name": "Victim Patient",
        "appointment_date": "2026-09-20",
        "appointment_time": "02:00 PM",
        "reason": "Unauthorized booking attempt"
    }
    # User 1 token but user_id=2 in query parameter
    response = client.post("/api/services/appointments?user_id=2", json=payload, headers=headers_user1)
    assert response.status_code == 403
    assert "Forbidden" in response.json()["detail"]


def test_appointment_cross_user_retrieval_denied():
    """Verify attempting to retrieve another patient's appointments returns HTTP 403 Forbidden."""
    headers_user1 = get_auth_headers(user_id=1)
    # User 1 tries to list User 2's appointments
    response = client.get("/api/services/appointments?user_id=2", headers=headers_user1)
    assert response.status_code == 403
    assert "Forbidden" in response.json()["detail"]


def test_appointment_booking_invalid_doctor_or_hospital():
    """Verify booking fails with 404 when hospital or doctor ID does not exist."""
    headers = get_auth_headers(user_id=1)
    payload_bad_hosp = {
        "hospital_id": 99999,
        "doctor_id": 1,
        "patient_name": "Test Patient",
        "appointment_date": "2026-09-25",
        "appointment_time": "10:00 AM",
        "reason": "Cardio Checkup"
    }
    resp1 = client.post("/api/services/appointments?user_id=1", json=payload_bad_hosp, headers=headers)
    assert resp1.status_code == 404
    assert "Hospital not found" in resp1.json()["detail"]

    payload_bad_doc = {
        "hospital_id": 1,
        "doctor_id": 99999,
        "patient_name": "Test Patient",
        "appointment_date": "2026-09-25",
        "appointment_time": "10:00 AM",
        "reason": "Cardio Checkup"
    }
    resp2 = client.post("/api/services/appointments?user_id=1", json=payload_bad_doc, headers=headers)
    assert resp2.status_code == 404
    assert "Doctor not found" in resp2.json()["detail"]


# =========================================================================
# 3. Medical Translation Tests
# =========================================================================

def test_medical_translation_preserves_clinical_content():
    """
    Verify that functional translation capability preserves the original medical
    meaning and instructions without adding unmentioned diagnoses, new medications,
    or unsolicited clinical advice. Does NOT claim clinical validation.
    """
    instruction = "Take medicine after food"
    response = client.post("/api/services/translate", json={
        "text": instruction,
        "source_lang": "English",
        "target_lang": "Telugu"
    })
    assert response.status_code == 200
    data = response.json()
    assert "translated_text" in data
    assert data["source_lang"] == "English"
    assert data["target_lang"] == "Telugu"

    # Functional integrity check: verify no unsolicited diagnoses or medications were hallucinated
    translated = data["translated_text"].lower()
    assert "chemotherapy" not in translated
    assert "cancer" not in translated
    assert "diabetes" not in translated
    assert "insulin" not in translated
    assert "aspirin" not in translated


def test_medical_translation_regional_languages():
    """Verify translation tool functionality across multiple regional languages."""
    phrase = "chest pain"
    for lang in ["Telugu", "Hindi", "Tamil", "Kannada"]:
        resp = client.post("/api/services/translate", json={
            "text": phrase,
            "source_lang": "English",
            "target_lang": lang
        })
        assert resp.status_code == 200
        res_json = resp.json()
        assert res_json["target_lang"] == lang
        assert len(res_json["translated_text"]) > 0


# =========================================================================
# 4. Insurance Assistance Tests
# =========================================================================

def test_insurance_assistance_providers():
    """Verify insurance endpoint returns seeded providers and coverage details."""
    response = client.get("/api/services/insurance")
    assert response.status_code == 200
    providers = response.json()
    assert isinstance(providers, list)
    assert len(providers) >= 3
    provider_names = [p["name"] for p in providers]
    assert "Star Health Insurance" in provider_names
    assert "HDFC ERGO Optima Secure" in provider_names


def test_insurance_assistance_hospital_context():
    """Verify coverage assistance returns enriched data with simulated benchmark labeling."""
    response = client.get("/api/services/insurance?hospital_id=1&treatment=Coronary%20Angioplasty")
    assert response.status_code == 200
    providers = response.json()
    assert len(providers) >= 1
    for p in providers:
        assert p.get("is_benchmark_simulated") is True
        assert "benchmark_turnaround_hours" in p
        assert "tpa_assistance" in p
        assert "Apollo Hospitals" in p["coverage_details"]
        assert "Coronary Angioplasty" in p["coverage_details"]


# =========================================================================
# 5. Emergency & Local Health Support Tests
# =========================================================================

def test_emergency_configured_contacts():
    """Verify emergency services return configured regional contacts (112/108) with non-universal notice."""
    response = client.get("/api/services/emergency?city=Hyderabad")
    assert response.status_code == 200
    data = response.json()
    assert "112" in data["emergency_number"] or "108" in data["emergency_number"]
    assert "region_note" in data
    assert "India" in data["region_note"]
    assert "trauma_centers" in data
    assert len(data["trauma_centers"]) >= 1
    assert "disclaimer" in data
    assert "EMERGENCY" in data["disclaimer"]


def test_local_health_advisories_and_blood_banks():
    """Verify local health information returns city advisories, blood banks, and diagnostic centers."""
    response = client.get("/api/services/local-health?city=Hyderabad")
    assert response.status_code == 200
    data = response.json()
    assert data["city"] == "Hyderabad"
    assert "advisories" in data
    assert len(data["advisories"]) >= 2
    assert "blood_banks" in data
    assert len(data["blood_banks"]) >= 1
    assert "diagnostic_centers" in data
    assert len(data["diagnostic_centers"]) >= 1
