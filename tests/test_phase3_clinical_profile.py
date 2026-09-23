"""
Phase 3 — Clinical Profile Test Suite
Validates:
1. Phase 2 StructuredClinicalInfo -> Clinical Profile mapping
2. Profile persistence in database
3. Profile retrieval and update via API
4. Correct handling of empty/missing fields
5. Zero inferred clinical information (exact fidelity)
6. Shared patient context availability for downstream phases
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

from database import SessionLocal, engine
from models import PatientProfile, MedicalReport, User
from routes.auth import (
    sync_clinical_profile_from_structured_info,
    get_shared_clinical_context
)
from init_db import init_db
from main import app
from security import create_access_token


@pytest.fixture(scope="module", autouse=True)
def setup_database():
    init_db()
    db = SessionLocal()
    # Ensure default demo user exists
    user = db.query(User).filter(User.id == 1).first()
    if not user:
        user = User(id=1, email="patient@example.com", hashed_password="pw", full_name="Demo Patient", role="patient")
        db.add(user)
        db.commit()
    db.close()


def test_phase2_to_clinical_profile_mapping():
    """
    Test 1: Phase 2 -> Clinical Profile mapping
    Verifies that all 8 clinical categories + demographics map accurately into PatientProfile.
    """
    phase2_structured = {
        "metadata": {
            "patient_name": "Suresh Patel",
            "patient_id": "MRN-CRD-1024",
            "report_date": "15/08/2025"
        },
        "demographics": {
            "age": 62,
            "gender": "Male"
        },
        "conditions": ["Coronary Artery Disease", "Double Vessel Disease"],
        "symptoms": ["chest pain", "exertional angina", "dyspnea"],
        "tests": ["Coronary Angiography", "2D Echocardiogram"],
        "test_results": [
            {"test_name": "LAD Stenosis", "value": "85%", "unit": "%", "reference_range": "< 50%", "status": "Critical"},
            {"test_name": "LVEF", "value": "52%", "unit": "%", "reference_range": "50% - 70%", "status": "Normal"},
            {"test_name": "Blood Pressure", "value": "142/88", "unit": "mmHg", "reference_range": "90/60 - 120/80 mmHg", "status": "High"}
        ],
        "medications": ["Aspirin 75mg OD", "Atorvastatin 40mg HS", "Metoprolol 25mg BD"],
        "procedures": ["Percutaneous Coronary Intervention", "Coronary Angiography"],
        "medical_history": ["Known case of hypertension for 6 years", "Past smoker"]
    }

    profile = PatientProfile(user_id=1, age=30, gender="Other")
    sync_clinical_profile_from_structured_info(profile, phase2_structured, report_id=101)

    # Demographics
    assert profile.age == 62
    assert profile.gender == "Male"

    # Conditions (Explicit only)
    assert "Coronary Artery Disease" in profile.conditions
    assert "Double Vessel Disease" in profile.conditions
    assert "Coronary Artery Disease" in profile.chronic_conditions

    # Symptoms
    assert "chest pain" in profile.symptoms
    assert "exertional angina" in profile.symptoms

    # Tests & Measurements
    assert "Coronary Angiography" in profile.tests
    assert len(profile.test_results) == 3
    tr_names = [t["test_name"] for t in profile.test_results]
    assert "LAD Stenosis" in tr_names
    assert "LVEF" in tr_names

    # Medications
    assert "Aspirin 75mg OD" in profile.medications
    assert "Atorvastatin 40mg HS" in profile.medications

    # Procedures
    assert "Percutaneous Coronary Intervention" in profile.procedures

    # Medical History
    assert any("hypertension" in h for h in profile.medical_history)
    assert profile.last_report_id == 101


def test_profile_persistence_in_database():
    """
    Test 2: Profile persistence
    Verifies that mapped clinical profile fields persist to SQLite database across sessions.
    """
    db = SessionLocal()
    try:
        profile = db.query(PatientProfile).filter(PatientProfile.user_id == 1).first()
        if not profile:
            profile = PatientProfile(user_id=1)
            db.add(profile)

        sample_structured = {
            "demographics": {"age": 55, "gender": "Female"},
            "conditions": ["Grade IV Osteoarthritis"],
            "symptoms": ["knee pain", "antalgic gait"],
            "tests": ["X-Ray Knee Bilateral"],
            "test_results": [
                {"test_name": "Blood Pressure", "value": "128/82", "unit": "mmHg", "reference_range": "90/60 - 120/80 mmHg", "status": "Normal"}
            ],
            "medications": ["Paracetamol 650mg TDS"],
            "procedures": ["Total Knee Arthroplasty"],
            "medical_history": ["Duration: 4 years"]
        }

        sync_clinical_profile_from_structured_info(profile, sample_structured, report_id=999)
        db.commit()

        # Expire cache and reload from raw database connection
        db.expire_all()
        reloaded = db.query(PatientProfile).filter(PatientProfile.user_id == 1).first()

        assert reloaded is not None
        assert reloaded.age == 55
        assert reloaded.gender == "Female"
        assert "Grade IV Osteoarthritis" in reloaded.conditions
        assert "knee pain" in reloaded.symptoms
        assert "Total Knee Arthroplasty" in reloaded.procedures
        assert reloaded.last_report_id == 999
        assert isinstance(reloaded.test_results, list)
        assert len(reloaded.test_results) >= 1
    finally:
        db.close()


def test_profile_retrieval_and_update_api():
    """
    Test 3: Profile retrieval and update via API
    Verifies GET /api/auth/profile and PUT /api/auth/profile endpoints.
    """
    token = create_access_token(data={"sub": "1", "email": "rahul.verma@example.com", "role": "patient"})
    headers = {"Authorization": f"Bearer {token}"}
    with TestClient(app) as client:
        # GET profile
        get_res = client.get("/api/auth/profile?user_id=1", headers=headers)
        assert get_res.status_code == 200
        pdata = get_res.json()
        assert pdata["user_id"] == 1
        assert "conditions" in pdata
        assert "symptoms" in pdata
        assert "test_results" in pdata
        assert "medications" in pdata

        # PUT profile update
        update_payload = {
            "age": 58,
            "gender": "Female",
            "blood_group": "AB+",
            "current_city": "Bengaluru",
            "allergies": "Sulfa drugs",
            "chronic_conditions": "Osteoarthritis, Hypertension",
            "conditions": ["Osteoarthritis", "Hypertension"],
            "symptoms": ["joint stiffness", "knee pain"],
            "tests": ["X-Ray Knee"],
            "test_results": [
                {"test_name": "Blood Pressure", "value": "130/85", "unit": "mmHg", "reference_range": "120/80", "status": "Normal"}
            ],
            "medications": ["Paracetamol 650mg TDS", "Amlodipine 5mg OD"],
            "procedures": ["Total Knee Arthroplasty"],
            "medical_history": ["Known hypertensive for 5 years"]
        }

        put_res = client.put("/api/auth/profile?user_id=1", json=update_payload, headers=headers)
        assert put_res.status_code == 200
        updated = put_res.json()
        assert updated["age"] == 58
        assert updated["current_city"] == "Bengaluru"
        assert updated["allergies"] == "Sulfa drugs"
        assert "Osteoarthritis" in updated["conditions"]
        assert "Amlodipine 5mg OD" in updated["medications"]


def test_handling_of_empty_and_missing_fields():
    """
    Test 4: Correct handling of empty/missing fields
    Ensures empty dictionaries, None fields, or missing categories do not crash or corrupt the profile.
    """
    profile = PatientProfile(
        user_id=1,
        age=45,
        gender="Male",
        conditions=["Hypertension"],
        symptoms=["headache"],
        medications=["Telmisartan 40mg OD"]
    )

    # 1. Empty structured info dict
    sync_clinical_profile_from_structured_info(profile, {})
    assert profile.age == 45
    assert profile.gender == "Male"
    assert profile.conditions == ["Hypertension"]

    # 2. None fields inside structured info
    sparse_info = {
        "demographics": {"age": None, "gender": None},
        "conditions": [],
        "symptoms": None,
        "tests": [],
        "test_results": None,
        "medications": [],
        "procedures": None,
        "medical_history": []
    }
    sync_clinical_profile_from_structured_info(profile, sparse_info)
    # Existing valid data is preserved
    assert profile.age == 45
    assert profile.gender == "Male"
    assert "Hypertension" in profile.conditions
    assert "headache" in profile.symptoms
    assert "Telmisartan 40mg OD" in profile.medications


def test_no_inferred_clinical_information():
    """
    Test 5: No inferred clinical information
    Verifies that the clinical profile strictly contains explicit findings
    and does NOT extrapolate or fabricate unstated diagnoses or clinical entities.
    """
    strict_phase2_output = {
        "demographics": {"age": 50, "gender": "Male"},
        "conditions": ["Type 2 Diabetes Mellitus"],
        "symptoms": ["fatigue"],
        "tests": ["HbA1c Test"],
        "test_results": [
            {"test_name": "HbA1c", "value": "8.5%", "unit": "%", "reference_range": "< 5.7%", "status": "High"}
        ],
        "medications": ["Metformin 500mg BD"],
        "procedures": [],
        "medical_history": ["Known diabetic for 3 years"]
    }

    profile = PatientProfile(user_id=1)
    sync_clinical_profile_from_structured_info(profile, strict_phase2_output)

    # Explicit condition is present
    assert profile.conditions == ["Type 2 Diabetes Mellitus"]

    # Inferred diagnoses must NOT exist
    unwanted_inferences = [
        "Cardiovascular Disease",
        "Diabetic Retinopathy",
        "Diabetic Nephropathy",
        "Chronic Kidney Disease",
        "Hypertension",
        "Peripheral Neuropathy"
    ]
    for inference in unwanted_inferences:
        assert inference not in profile.conditions, f"Diagnosis '{inference}' must not be inferred!"
        assert inference not in (profile.chronic_conditions or "")


def test_shared_clinical_context_downstream_readiness():
    """
    Test 6: Shared patient context availability
    Verifies that get_shared_clinical_context returns unified structured context
    ready to be consumed by downstream modules (RAG, Recommendations, Cost, Assistant).
    """
    db = SessionLocal()
    try:
        context = get_shared_clinical_context(user_id=1, db=db)

        assert isinstance(context, dict)
        assert "user_id" in context
        assert "demographics" in context
        assert "conditions" in context
        assert "symptoms" in context
        assert "tests" in context
        assert "test_results" in context
        assert "medications" in context
        assert "procedures" in context
        assert "medical_history" in context

        # Check API endpoint for shared context
        token = create_access_token(data={"sub": "1", "email": "rahul.verma@example.com", "role": "patient"})
        headers = {"Authorization": f"Bearer {token}"}
        with TestClient(app) as client:
            res = client.get("/api/auth/profile/shared-context?user_id=1", headers=headers)
            assert res.status_code == 200
            api_ctx = res.json()
            assert api_ctx["user_id"] == 1
            assert isinstance(api_ctx["conditions"], list)
            assert isinstance(api_ctx["demographics"], dict)
    finally:
        db.close()


if __name__ == "__main__":
    pytest.main(["-v", __file__])
