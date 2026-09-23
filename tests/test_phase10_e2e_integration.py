"""
Tests for Phase 10: End-to-End Integration & Validation.

Validates the complete, coherent authenticated patient workflow across all phases (1–9):
1. Registration & Authentication (Phase 8)
2. Medical Document Ingestion & OCR + Clinical NER (Phase 2)
3. RAG-Grounded Report Analysis & Guideline Retrieval (Phases 3 & 7)
4. Multi-Criteria Hospital & Doctor Recommendations (Phase 4)
5. Treatment Cost & Length of Stay (LOS) ML Prediction + SHAP Explanation (Phase 5)
6. Personalized Medical Travel Plan Generation with A* Navigation & Recovery Stay (Phase 6)
7. Content-Based Recovery Accommodation & Graph Routing (Phase 6)
8. RAG-Grounded AI Healthcare Assistant Chat & Context Isolation (Phase 7)
9. Supporting 12C Features: Pharmacy, Appointments, Translation, Insurance, Emergency (Phase 9)
10. Strict Cross-Patient Isolation & IDOR Defense (Phase 8)
"""

import sys
import os
import uuid
import pytest
from fastapi.testclient import TestClient

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(os.path.dirname(CURRENT_DIR), "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from main import app
from init_db import init_db
from database import SessionLocal
from models import User, MedicalReport, TravelPlan, Appointment, Conversation, ChatMessage

client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def setup_phase10_db():
    """Initializes the database schema and seeded datasets."""
    init_db()


def test_e2e_authenticated_patient_complete_journey():
    """
    Coherent end-to-end patient journey:
    Registers a new patient, logs in, ingests a genuine medical report via OCR/NER,
    retrieves RAG-grounded analysis, gets hospital and doctor recommendations,
    predicts cost & LOS with SHAP explanations, generates a personalized travel plan,
    verifies A* routing & accommodation, consults AI healthcare assistant,
    and uses connected supporting services (appointments, pharmacies, translation, insurance).
    
    CRITICAL CONSTRAINT: Real dynamic IDs and context must be carried sequentially
    from each stage into the next. No hardcoded mock results.
    """
    # -------------------------------------------------------------------------
    # STAGE 1: Register and Authenticate New Patient
    # -------------------------------------------------------------------------
    uid = uuid.uuid4().hex[:8]
    patient_email = f"e2e_journey_{uid}@example.com"
    patient_password = "SecurePatientPassword2026!"
    patient_name = "Vikram Aditya"

    # Register
    reg_resp = client.post("/api/auth/register", json={
        "email": patient_email,
        "password": patient_password,
        "full_name": patient_name
    })
    assert reg_resp.status_code == 200, f"Registration failed: {reg_resp.text}"
    user_data = reg_resp.json()
    patient_id = user_data["id"]
    assert patient_id > 0
    assert user_data["email"] == patient_email

    # Login to acquire genuine Bearer JWT
    login_resp = client.post("/api/auth/login", json={
        "email": patient_email,
        "password": patient_password
    })
    assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
    login_json = login_resp.json()
    assert "access_token" in login_json
    token = login_json["access_token"]
    auth_headers = {"Authorization": f"Bearer {token}"}

    # -------------------------------------------------------------------------
    # STAGE 2: Upload Medical Document & Ingest via OCR + Clinical NER
    # -------------------------------------------------------------------------
    sample_doc_path = os.path.join(BACKEND_DIR, "uploads", "1.webp")
    assert os.path.exists(sample_doc_path), f"Real test document not found at {sample_doc_path}"

    with open(sample_doc_path, "rb") as f:
        file_bytes = f.read()

    upload_resp = client.post(
        "/api/reports/upload",
        files={"file": ("clinical_record.webp", file_bytes, "image/webp")},
        headers=auth_headers
    )
    assert upload_resp.status_code == 200, f"Upload failed: {upload_resp.text}"
    report_data = upload_resp.json()

    assert report_data["status"] == "COMPLETED"
    report_id = report_data["id"]
    assert report_id is not None
    
    # Confirm in DB that report is strictly owned by patient_id
    db = SessionLocal()
    try:
        db_rep = db.query(MedicalReport).filter(MedicalReport.id == report_id).first()
        assert db_rep is not None
        assert db_rep.user_id == patient_id
    finally:
        db.close()

    assert len(report_data.get("ocr_text", "")) > 20
    assert len(report_data.get("entities", [])) > 0

    recommended_specialty = report_data.get("recommended_specialty") or "Cardiology"
    extracted_summary = report_data.get("summary") or ""
    assert len(extracted_summary) > 10

    # -------------------------------------------------------------------------
    # STAGE 3: Retrieve RAG-Grounded Report Analysis & Guideline Citations
    # -------------------------------------------------------------------------
    get_report_resp = client.get(f"/api/reports/{report_id}", headers=auth_headers)
    assert get_report_resp.status_code == 200
    fetched_report = get_report_resp.json()
    assert fetched_report["id"] == report_id
    assert fetched_report["recommended_specialty"] == recommended_specialty

    # Verify report is listed in patient's personal medical vault
    vault_resp = client.get("/api/reports/", headers=auth_headers)
    assert vault_resp.status_code == 200
    user_reports = vault_resp.json()
    assert any(r["id"] == report_id for r in user_reports)

    # -------------------------------------------------------------------------
    # STAGE 4: Hospital & Doctor Recommendations Using Real Context
    # -------------------------------------------------------------------------
    # Query hospital recommendations carrying the actual specialty and report_id
    hosp_resp = client.get(
        f"/api/recommend/hospitals?specialty={recommended_specialty}&report_id={report_id}",
        headers=auth_headers
    )
    assert hosp_resp.status_code == 200, f"Hospital recommendation failed: {hosp_resp.text}"
    hospitals = hosp_resp.json()
    assert len(hospitals) > 0, "No hospitals returned from recommendation engine"

    # Capture top recommended hospital dynamically
    top_hospital = hospitals[0]
    hospital_id = top_hospital["id"]
    hospital_name = top_hospital["name"]
    hospital_city = top_hospital["city"]
    assert hospital_id > 0
    assert hospital_name != ""

    # Query doctor recommendations dynamically for the chosen hospital and specialty
    doc_resp = client.get(
        f"/api/recommend/doctors?hospital_id={hospital_id}&specialty={recommended_specialty}&report_id={report_id}",
        headers=auth_headers
    )
    assert doc_resp.status_code == 200, f"Doctor recommendation failed: {doc_resp.text}"
    doctors = doc_resp.json()
    assert len(doctors) > 0, "No doctors returned for hospital and specialty"

    top_doctor = doctors[0]
    doctor_id = top_doctor["id"]
    doctor_name = top_doctor["name"]
    assert doctor_id > 0

    # -------------------------------------------------------------------------
    # STAGE 5: Cost & Length of Stay (LOS) ML Prediction & SHAP Explanation
    # -------------------------------------------------------------------------
    # Predict cost and LOS using the actual condition and selected city
    cost_pred_resp = client.post(
        "/api/cost/predict",
        json={
            "treatment_name": "Coronary Angioplasty" if "cardio" in recommended_specialty.lower() else recommended_specialty,
            "city": hospital_city,
            "room_type": "Private AC Deluxe",
            "report_id": report_id,
            "hospital_id": hospital_id
        },
        headers=auth_headers
    )
    assert cost_pred_resp.status_code == 200, f"Cost prediction failed: {cost_pred_resp.text}"
    cost_data = cost_pred_resp.json()
    assert cost_data["estimated_avg_cost"] > 0
    assert cost_data["estimated_min_cost"] > 0
    assert cost_data["estimated_max_cost"] >= cost_data["estimated_min_cost"]
    assert cost_data["duration_days"] >= 1
    assert "shap_feature_impacts" in cost_data

    # Explain cost with genuine TreeSHAP feature contributions
    shap_resp = client.post(
        "/api/cost/explain",
        json={
            "treatment_name": "Coronary Angioplasty" if "cardio" in recommended_specialty.lower() else recommended_specialty,
            "city": hospital_city,
            "room_type": "Private AC Deluxe",
            "report_id": report_id,
            "hospital_id": hospital_id
        },
        headers=auth_headers
    )
    assert shap_resp.status_code == 200, f"SHAP explanation failed: {shap_resp.text}"
    shap_json = shap_resp.json()
    assert "shap_explanation" in shap_json
    assert len(shap_json["shap_explanation"]["breakdown"]) > 0

    # -------------------------------------------------------------------------
    # STAGE 6: Personalized Medical Travel Plan Generation with A* & Recovery Stay
    # -------------------------------------------------------------------------
    travel_req_payload = {
        "hospital_id": hospital_id,
        "doctor_id": doctor_id,
        "medical_condition": recommended_specialty,
        "report_id": report_id,
        "preferred_travel_date": "2026-09-25",
        "duration_days": 5,
        "budget_range": "Standard",
        "current_location": "Bengaluru"
    }

    travel_resp = client.post("/api/travel/plan", json=travel_req_payload, headers=auth_headers)
    assert travel_resp.status_code == 200, f"Travel plan creation failed: {travel_resp.text}"
    plan_json = travel_resp.json()
    plan_id = plan_json["id"]
    assert plan_id > 0
    assert plan_json["hospital_name"] == hospital_name
    assert plan_json["doctor_name"] == doctor_name
    assert len(plan_json["itinerary"]) >= 3
    assert plan_json["total_estimated_cost"] > 0

    # Verify content-matched recovery stay is populated
    assert plan_json.get("recommended_accommodation") is not None
    recovery_stay = plan_json["recommended_accommodation"]
    assert recovery_stay["name"] != ""
    assert recovery_stay["price_per_night"] > 0

    # Verify retrieval of saved travel plan via GET /api/travel/plan
    fetch_plan_resp = client.get("/api/travel/plan", headers=auth_headers)
    assert fetch_plan_resp.status_code == 200
    saved_plan = fetch_plan_resp.json()
    assert saved_plan["id"] == plan_id

    # -------------------------------------------------------------------------
    # STAGE 7: Spatial A* Route Pathfinding & Content-Based Stays
    # -------------------------------------------------------------------------
    # Interactive A* navigation pathfinding
    nav_resp = client.get("/api/travel/navigate?origin=Airport&destination=Hospital&metric=distance")
    assert nav_resp.status_code == 200
    nav_data = nav_resp.json()
    assert nav_data["distance_km"] > 0
    assert len(nav_data["turn_by_turn_waypoints"]) > 0
    assert nav_data["algorithm_telemetry"]["is_optimal"] is True

    # Content-based accommodations ranked for the patient's selected hospital
    acc_resp = client.get(f"/api/travel/accommodations?hospital_id={hospital_id}&budget_tier=Standard")
    assert acc_resp.status_code == 200
    accommodations = acc_resp.json()
    assert len(accommodations) > 0
    top_stay = accommodations[0]
    assert "match_score" in top_stay
    assert "match_percentage" in top_stay
    assert top_stay["match_score"] > 0

    # -------------------------------------------------------------------------
    # STAGE 8: RAG-Grounded AI Healthcare Assistant Consultation
    # -------------------------------------------------------------------------
    chat_payload = {
        "message": "What clinical guidelines apply to my diagnostic findings and travel?",
        "report_id": report_id,
        "hospital_id": hospital_id
    }
    chat_resp = client.post("/api/services/chat", json=chat_payload, headers=auth_headers)
    assert chat_resp.status_code == 200, f"AI Assistant chat failed: {chat_resp.text}"
    chat_data = chat_resp.json()
    assert chat_data["reply"] != ""
    assert chat_data["conversation_id"] is not None
    assert len(chat_data.get("citations", [])) > 0
    assert "guidance" in chat_data.get("disclaimer", "").lower() or "informational" in chat_data.get("disclaimer", "").lower()

    # Verify chat history persistence strictly scoped to authenticated user
    conv_id = chat_data["conversation_id"]
    hist_resp = client.get(f"/api/services/chat/history?conversation_id={conv_id}", headers=auth_headers)
    assert hist_resp.status_code == 200
    history = hist_resp.json()
    assert len(history) >= 2  # user message + assistant reply

    # -------------------------------------------------------------------------
    # STAGE 9: Connected Supporting 12C Services
    # -------------------------------------------------------------------------
    # 9.1 Pharmacy Finder (real seeded stock in destination city)
    pharmacy_resp = client.get(f"/api/services/pharmacies?city={hospital_city}")
    assert pharmacy_resp.status_code == 200
    pharmacies = pharmacy_resp.json()
    assert len(pharmacies) > 0
    assert any(p["city"].lower() == hospital_city.lower() for p in pharmacies)

    # 9.2 Appointment Booking with Authenticated User and Real Doctor/Hospital
    apt_payload = {
        "hospital_id": hospital_id,
        "doctor_id": doctor_id,
        "patient_name": patient_name,
        "appointment_date": "2026-09-26",
        "appointment_time": "10:00 AM",
        "reason": f"Evaluation for {recommended_specialty}"
    }
    apt_book_resp = client.post("/api/services/appointments", json=apt_payload, headers=auth_headers)
    assert apt_book_resp.status_code == 200, f"Appointment booking failed: {apt_book_resp.text}"
    apt_data = apt_book_resp.json()
    apt_id = apt_data["id"]
    assert apt_id > 0
    assert apt_data["user_id"] == patient_id
    assert apt_data["doctor_id"] == doctor_id
    assert apt_data["hospital_id"] == hospital_id

    # Retrieve patient's personal appointments
    my_apts_resp = client.get("/api/services/appointments", headers=auth_headers)
    assert my_apts_resp.status_code == 200
    my_apts = my_apts_resp.json()
    assert any(a["id"] == apt_id for a in my_apts)

    # 9.3 Medical Translation (preserving clinical instructions)
    trans_payload = {
        "text": "Please take prescribed cardiovascular medication with water after meals. Do not drive immediately after discharge.",
        "target_lang": "Hindi",
        "source_lang": "English"
    }
    trans_resp = client.post("/api/services/translate", json=trans_payload)
    assert trans_resp.status_code == 200
    trans_data = trans_resp.json()
    assert trans_data["target_lang"] == "Hindi"
    assert len(trans_data["translated_text"]) > 0

    # 9.4 Insurance Assistance (contextual to hospital and specialty)
    treatment_query = "Coronary Angioplasty" if "cardio" in recommended_specialty.lower() else recommended_specialty
    ins_resp = client.get(f"/api/services/insurance?hospital_id={hospital_id}&treatment={treatment_query}")
    assert ins_resp.status_code == 200
    providers = ins_resp.json()
    assert isinstance(providers, list)
    assert len(providers) > 0
    assert any(p.get("is_benchmark_simulated") is True for p in providers)

    # 9.5 Emergency Support (regional configured contacts with disclaimer)
    emerg_resp = client.get(f"/api/services/emergency?city={hospital_city}")
    assert emerg_resp.status_code == 200
    emerg_data = emerg_resp.json()
    assert "112" in emerg_data["emergency_number"] or "108" in emerg_data["emergency_number"]
    assert "region_note" in emerg_data
    assert "disclaimer" in emerg_data


def test_e2e_cross_user_isolation_and_security_defense():
    """
    Verifies that authenticating as Patient B strictly prevents accessing or manipulating
    Patient A's medical reports, travel plans, appointments, and conversation history.
    Also confirms that query parameters (e.g. ?user_id=) cannot bypass authorization.
    """
    # Create Patient A
    uid_a = uuid.uuid4().hex[:8]
    email_a = f"patient_a_{uid_a}@example.com"
    pwd_a = "PatientASecret123!"
    reg_a = client.post("/api/auth/register", json={"email": email_a, "password": pwd_a, "full_name": "Patient A"})
    assert reg_a.status_code == 200
    user_a_id = reg_a.json()["id"]

    login_a = client.post("/api/auth/login", json={"email": email_a, "password": pwd_a})
    token_a = login_a.json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # Upload report for Patient A
    sample_path = os.path.join(BACKEND_DIR, "uploads", "1.webp")
    with open(sample_path, "rb") as f:
        file_bytes = f.read()
    upload_a = client.post(
        "/api/reports/upload",
        files={"file": ("report_a.webp", file_bytes, "image/webp")},
        headers=headers_a
    )
    assert upload_a.status_code == 200
    report_a_id = upload_a.json()["id"]

    # Book appointment for Patient A
    apt_a = client.post(
        "/api/services/appointments",
        json={
            "hospital_id": 1,
            "doctor_id": 1,
            "patient_name": "Patient A",
            "appointment_date": "2026-09-28",
            "appointment_time": "09:30 AM",
            "reason": "Consultation Patient A"
        },
        headers=headers_a
    )
    assert apt_a.status_code == 200
    apt_a_id = apt_a.json()["id"]

    # Start conversation for Patient A
    chat_a = client.post(
        "/api/services/chat",
        json={"message": "Can I travel tomorrow?", "report_id": report_a_id, "hospital_id": 1},
        headers=headers_a
    )
    assert chat_a.status_code == 200
    conv_a_id = chat_a.json()["conversation_id"]

    # -------------------------------------------------------------------------
    # Register & Login as Patient B
    # -------------------------------------------------------------------------
    uid_b = uuid.uuid4().hex[:8]
    email_b = f"patient_b_{uid_b}@example.com"
    pwd_b = "PatientBSecret123!"
    reg_b = client.post("/api/auth/register", json={"email": email_b, "password": pwd_b, "full_name": "Patient B"})
    assert reg_b.status_code == 200
    user_b_id = reg_b.json()["id"]

    login_b = client.post("/api/auth/login", json={"email": email_b, "password": pwd_b})
    token_b = login_b.json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # 1. Patient B attempts to view Patient A's medical report -> HTTP 403
    cross_rep_resp = client.get(f"/api/reports/{report_a_id}", headers=headers_b)
    assert cross_rep_resp.status_code == 403
    assert "Forbidden" in cross_rep_resp.json()["detail"]

    # 2. Patient B attempts to create a travel plan using Patient A's report_id -> HTTP 403
    cross_plan_resp = client.post(
        "/api/travel/plan",
        json={
            "hospital_id": 1,
            "doctor_id": 1,
            "medical_condition": "Cardiology",
            "report_id": report_a_id,
            "preferred_travel_date": "2026-09-30",
            "duration_days": 5
        },
        headers=headers_b
    )
    assert cross_plan_resp.status_code == 403
    assert "Forbidden" in cross_plan_resp.json()["detail"]

    # 3. Patient B attempts to query appointments for Patient A using user_id param -> HTTP 403
    cross_apt_resp = client.get(f"/api/services/appointments?user_id={user_a_id}", headers=headers_b)
    assert cross_apt_resp.status_code == 403
    assert "Forbidden" in cross_apt_resp.json()["detail"]

    # 4. Patient B attempts to access Patient A's chat conversation history -> HTTP 403 or 404
    cross_chat_resp = client.get(f"/api/services/chat/history?conversation_id={conv_a_id}", headers=headers_b)
    assert cross_chat_resp.status_code in [403, 404]
    detail_lower = cross_chat_resp.json().get("detail", "").lower()
    assert "unauthorized" in detail_lower or "forbidden" in detail_lower or "not found" in detail_lower

    # 5. Patient B attempts to pass user_id=1 on authenticated profile update -> HTTP 403
    cross_prof_resp = client.put(
        f"/api/auth/profile?user_id={user_a_id}",
        json={"current_city": "Mumbai"},
        headers=headers_b
    )
    assert cross_prof_resp.status_code == 403


def test_e2e_unauthenticated_access_strictly_rejected():
    """
    Verifies that URL query parameters carrying navigation context (e.g. ?report_id=, ?user_id=)
    never bypass backend authentication or act as an authoritative source of medical records.
    """
    # Unauthenticated access to private medical report
    res_report = client.get("/api/reports/1?user_id=1")
    assert res_report.status_code in [401, 403]

    # Unauthenticated access to medical reports list
    res_list = client.get("/api/reports/?user_id=1")
    assert res_list.status_code in [401, 403]

    # Unauthenticated access to user profile
    res_profile = client.get("/api/auth/profile?user_id=1")
    assert res_profile.status_code in [401, 403]

    # Unauthenticated access to appointments
    res_apt = client.get("/api/services/appointments?user_id=1")
    assert res_apt.status_code in [401, 403]
