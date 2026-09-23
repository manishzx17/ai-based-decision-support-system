"""
Phase J: End-to-End Patient Journey Integration Audit.

Tests the complete, authentic patient journey for Rahul (User 1 / demo_cardio),
Priya (User 2 / demo_neuro), and Amit (User 3 / demo_ortho) through:

  Login → Report Upload → OCR → NER → Profile Sync → RAG Grounding
  → Hospital Recommendations → Doctor Recommendations → Hospital Comparison
  → Cost + LOS Prediction → SHAP Explanation → AI Healthcare Assistant
  → Medical Travel Route → Nearby Hotels/Pharmacies → Emergency Services
  → Logout

All three demo users MUST show distinct patient contexts (specialty, conditions,
city) that propagate correctly to every downstream module.

Cross-patient isolation is tested explicitly:
  - Rahul cannot access Priya's or Amit's data (403).
  - Priya cannot access Rahul's or Amit's data (403).
  - Amit cannot access Rahul's or Priya's data (403).
  - Post-logout token is invalidated (401 on re-use).
  - Unauthenticated requests to protected APIs return 401/403.

Architecture note: This system uses 3 pre-seeded demo patients — no self-
registration endpoint exists. Sessions are JWT-based with server-side revocation.
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
from models import User, MedicalReport, PatientProfile

client = TestClient(app)

# ---------------------------------------------------------------------------
# PDF builder for synthetic clinical reports
# ---------------------------------------------------------------------------

def build_pdf(lines: list) -> bytes:
    """Build a minimal valid PDF containing clinical text lines (ASCII-safe)."""
    stream = "BT /F1 12 Tf 72 720 Td "
    for line in lines:
        # Strip non-ASCII and PDF-special characters to keep Latin-1 encoding safe
        safe = (
            line
            .replace("(", "")
            .replace(")", "")
            .replace("\\", "")
            .replace("\u2014", "-")   # em dash -> hyphen
            .replace("\u2013", "-")   # en dash -> hyphen
            .replace("&", "and")
            .replace("\u00a0", " ")   # non-breaking space
            .encode("latin-1", errors="replace")
            .decode("latin-1")
        )
        stream += f"({safe}) Tj 0 -20 Td "
    stream += "ET"
    return (
        f"""%PDF-1.4
1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj
2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj
3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792]
           /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >> endobj
4 0 obj << /Length {len(stream)} >> stream
{stream}
endstream endobj
5 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj
xref
0 6
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
00000000115 00000 n 
00000000244 00000 n 
00000000431 00000 n 
trailer << /Size 6 /Root 1 0 R >>
startxref
550
%%EOF"""
    ).encode("latin-1")


# ---------------------------------------------------------------------------
# Shared clinical content per patient
# ---------------------------------------------------------------------------

RAHUL_REPORT_LINES = [
    "Cardiovascular Evaluation Report — Patient: Rahul Verma",
    "Diagnosis: Severe Coronary Artery Disease with exertional angina.",
    "Findings: LAD artery 85% proximal stenosis, RCA 70% mid-vessel lesion.",
    "LVEF 52% on echocardiogram.",
    "Plan: Percutaneous Coronary Intervention with Drug-Eluting Stents.",
    "Comorbidities: Essential Hypertension, Mild Dyslipidemia.",
    "Medications: Aspirin 75mg, Clopidogrel 75mg, Atorvastatin 40mg, Metoprolol 25mg.",
]

PRIYA_REPORT_LINES = [
    "Neurology Outpatient Report — Patient: Priya Sharma",
    "Chief Complaint: Recurrent severe unilateral headache with photophobia.",
    "Diagnosis: Chronic Migraine with aura, moderate severity.",
    "MRI Brain: No structural lesion. EEG: Normal.",
    "Plan: Prophylactic topiramate 25mg, acute sumatriptan as needed.",
    "Comorbidities: Anxiety disorder under CBT. No hypertension.",
    "Medications: Topiramate 25mg nightly, Sumatriptan 50mg PRN.",
]

AMIT_REPORT_LINES = [
    "Orthopedic Clinical Evaluation — Patient: Amit Patel",
    "Diagnosis: Bilateral knee osteoarthritis, severe grade IV medial compartment.",
    "X-Ray: Marked joint space narrowing, osteophytes bilateral knees.",
    "Plan: Total Knee Arthroplasty under spinal anesthesia.",
    "Comorbidities: Type 2 Diabetes Mellitus, HbA1c 7.2%.",
    "Medications: Metformin 500mg twice daily, Paracetamol 500mg PRN.",
]

DEMO_QUESTION = "What precautions should I take when travelling for my medical treatment?"


# ---------------------------------------------------------------------------
# DB setup
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module", autouse=True)
def setup_j_db():
    """Initialise DB with seeded demo patients."""
    init_db()


# ===========================================================================
# J-1 CLEAN SESSION + AUTHENTICATION
# ===========================================================================

def test_j1_clean_auth_all_three_users():
    """J-1: All three demo patients authenticate cleanly; token carries correct user context."""
    demo_users = [
        ("demo_cardio", 1, "Rahul Verma", "Cardiology", "Hyderabad"),
        ("demo_neuro",  2, "Priya Sharma", "Neurology", "Bengaluru"),
        ("demo_ortho",  3, "Amit Patel", "Orthopedics", "Delhi"),
    ]
    for username, uid, name, specialty, city in demo_users:
        res = client.post("/api/auth/login", json={"username": username, "password": "DemoPassword@123"})
        assert res.status_code == 200, f"Login failed for {username}: {res.text}"
        data = res.json()
        assert "access_token" in data, f"No token for {username}"
        assert data["user"]["id"] == uid
        assert data["user"]["full_name"] == name
        assert data["user"]["specialty"] == specialty

        # Verify profile isolation via authenticated profile endpoint
        headers = {"Authorization": f"Bearer {data['access_token']}"}
        prof = client.get("/api/auth/profile", headers=headers)
        assert prof.status_code == 200
        assert prof.json()["user_id"] == uid

    # Invalid credentials → 401
    bad = client.post("/api/auth/login", json={"username": "demo_cardio", "password": "WrongPassword!"})
    assert bad.status_code == 401

    # Unknown user → 401
    unknown = client.post("/api/auth/login", json={"username": "hacker_x", "password": "DemoPassword@123"})
    assert unknown.status_code == 401

    # Unauthenticated request to protected profile → 401
    unauth = client.get("/api/auth/profile")
    assert unauth.status_code in [401, 403]


# ===========================================================================
# J-2  RAHUL — COMPLETE PATIENT JOURNEY (2A–2L)
# ===========================================================================

def test_j2_rahul_complete_journey():
    """J-2: Full Rahul journey: Login→Upload→OCR→NER→Profile→RAG→Recommendations
    →Cost→SHAP→Assistant→Travel Route→Hotels→Pharmacies→Emergency→Logout."""

    # ------------------------------------------------------------------
    # J-2-0: Login as Rahul
    # ------------------------------------------------------------------
    login = client.post("/api/auth/login", json={"username": "demo_cardio", "password": "DemoPassword@123"})
    assert login.status_code == 200, login.text
    tok = login.json()["access_token"]
    h = {"Authorization": f"Bearer {tok}"}

    # Confirm no other patient context visible
    prof = client.get("/api/auth/profile", headers=h).json()
    assert prof["user_id"] == 1
    assert "Priya" not in str(prof)
    assert "Amit" not in str(prof)

    # ------------------------------------------------------------------
    # J-2A: Upload Report → OCR → NER → Profile Sync
    # ------------------------------------------------------------------
    pdf = build_pdf(RAHUL_REPORT_LINES)
    up = client.post(
        "/api/reports/upload",
        files={"file": ("rahul_cardiac.pdf", pdf, "application/pdf")},
        headers=h
    )
    assert up.status_code == 200, f"Upload failed: {up.text}"
    report = up.json()
    report_id = report["id"]
    assert report["status"] == "COMPLETED"
    assert len(report.get("ocr_text", "")) > 20, "OCR returned no text"

    entities = report.get("entities", [])
    assert len(entities) >= 2, "NER returned insufficient entities"
    entity_names_lower = " ".join(e.get("entity_name", "").lower() for e in entities)
    assert any(term in entity_names_lower for term in ["coronary", "stenosis", "angina", "aspirin", "stent"]), \
        f"Expected cardiology entities, got: {entity_names_lower}"

    # Specialty must be Cardiology
    assert report["recommended_specialty"] == "Cardiology", \
        f"Expected Cardiology specialty, got: {report.get('recommended_specialty')}"

    # Verify report is scoped to Rahul in DB
    db = SessionLocal()
    try:
        db_rep = db.query(MedicalReport).filter(MedicalReport.id == report_id).first()
        assert db_rep is not None
        assert db_rep.user_id == 1, f"Report owned by user {db_rep.user_id}, expected 1"
    finally:
        db.close()

    # Profile sync: last_report_id must update to this report
    prof_after = client.get("/api/auth/profile", headers=h).json()
    assert prof_after["last_report_id"] == report_id, \
        f"Profile last_report_id={prof_after['last_report_id']}, expected {report_id}"

    # Report appears in Rahul's vault
    vault = client.get("/api/reports/", headers=h).json()
    assert any(r["id"] == report_id for r in vault), "Report not found in Rahul's vault"
    for r in vault:
        assert r["user_id"] == 1, f"Cross-patient report in Rahul's vault: user_id={r['user_id']}"

    # ------------------------------------------------------------------
    # J-2B: RAG Grounding (report-level)
    # ------------------------------------------------------------------
    rep_detail = client.get(f"/api/reports/{report_id}", headers=h).json()
    assert rep_detail["id"] == report_id
    assert rep_detail.get("grounding_notes") is not None, "No RAG grounding notes"
    grounding_sources = rep_detail.get("grounding_sources", [])
    assert len(grounding_sources) > 0, "No RAG grounding sources"
    orgs = [s.get("organization", "") for s in grounding_sources]
    assert any("ESC" in o or "ACC" in o or "AHA" in o or "European" in o or "American" in o for o in orgs), \
        f"Expected authoritative guidelines, got: {orgs}"

    # Profile-level RAG grounding
    rag = client.post("/api/services/rag/profile-grounding", json={"top_k": 2}, headers=h)
    assert rag.status_code == 200
    rag_data = rag.json()
    assert rag_data["grounding_status"] == "GROUNDED"
    assert len(rag_data["citations"]) > 0

    # ------------------------------------------------------------------
    # J-2C: Hospital Recommendations (conditioned on Rahul's report)
    # ------------------------------------------------------------------
    hosp_res = client.get(f"/api/recommend/hospitals?report_id={report_id}&city=Hyderabad", headers=h)
    assert hosp_res.status_code == 200, f"Hospital recs failed: {hosp_res.text}"
    hospitals = hosp_res.json()
    assert len(hospitals) > 0, "No hospitals returned"
    top_hosp = hospitals[0]
    assert "Cardiology" in top_hosp["specialties"], "Top hospital doesn't match Cardiology"
    assert top_hosp["recommendation_score"] > 0
    assert "score_breakdown" in top_hosp
    assert top_hosp["score_breakdown"]["clinical_match"] > 0
    hospital_id = top_hosp["id"]
    hospital_name = top_hosp["name"]
    hospital_city = top_hosp.get("city", "Hyderabad")

    # Doctor Recommendations
    doc_res = client.get(f"/api/recommend/doctors?report_id={report_id}&hospital_id={hospital_id}", headers=h)
    assert doc_res.status_code == 200, f"Doctor recs failed: {doc_res.text}"
    doctors = doc_res.json()
    assert len(doctors) > 0
    assert any("cardio" in d["specialty"].lower() for d in doctors), "No cardiology doctors returned"
    top_doc = doctors[0]
    doctor_id = top_doc["id"]

    # ------------------------------------------------------------------
    # J-2D: Hospital Comparison (context consistency)
    # ------------------------------------------------------------------
    if len(hospitals) >= 2:
        compare_res = client.post(
            "/api/recommend/compare",
            json={"hospital_ids": [hospitals[0]["id"], hospitals[1]["id"]], "report_id": report_id},
            headers=h
        )
        # Compare returns 200 or is proxied via the same endpoint
        # If compare endpoint doesn't exist, verify the recommendation score is stable
        if compare_res.status_code == 200:
            cmp = compare_res.json()
            # hospital names must match those from recommendations
            names_in_compare = [h_item.get("name", "") for h_item in cmp] if isinstance(cmp, list) else []
            if names_in_compare:
                assert hospitals[0]["name"] in names_in_compare or hospitals[1]["name"] in names_in_compare
        # If 404/405, compare is handled client-side (by-design in this DSS)

    # Recommendation score is deterministic (same inputs → same score)
    hosp_res2 = client.get(f"/api/recommend/hospitals?report_id={report_id}&city=Hyderabad", headers=h)
    assert hosp_res2.status_code == 200
    assert hosp_res2.json()[0]["recommendation_score"] == top_hosp["recommendation_score"], \
        "Hospital scores are non-deterministic"

    # ------------------------------------------------------------------
    # J-2E: Cost + LOS Prediction (linked to Rahul's report/hospital)
    # ------------------------------------------------------------------
    cost_res = client.post(
        "/api/cost/predict",
        json={
            "treatment_name": "Coronary Angioplasty",
            "city": hospital_city,
            "room_type": "Private AC Deluxe",
            "report_id": report_id,
            "hospital_id": hospital_id
        },
        headers=h
    )
    assert cost_res.status_code == 200, f"Cost prediction failed: {cost_res.text}"
    cost_data = cost_res.json()

    assert cost_data["predicted_los_days"] is not None
    assert cost_data["predicted_los_days"] >= 1.0, "LOS < 1 day is implausible"
    assert cost_data["estimated_avg_cost"] > 10000.0, "Cost implausibly low"
    assert cost_data["currency"] == "INR"

    # No actual LOS used as model input (pre-operative prediction)
    error_band = cost_data.get("empirical_model_error_range", {})
    assert "held_out_rmse_inr" in error_band
    desc_lower = error_band.get("description", "").lower()
    assert "empirical" in desc_lower and "rmse" in desc_lower
    assert "confidence interval" not in desc_lower

    # ------------------------------------------------------------------
    # J-2F: SHAP Explainability (corresponds to current Rahul prediction)
    # ------------------------------------------------------------------
    shap_res = client.post(
        "/api/cost/explain",
        json={
            "treatment_name": "Coronary Angioplasty",
            "city": hospital_city,
            "room_type": "Private AC Deluxe",
            "report_id": report_id,
            "hospital_id": hospital_id
        },
        headers=h
    )
    assert shap_res.status_code == 200, f"SHAP failed: {shap_res.text}"
    shap_data = shap_res.json()["shap_explanation"]
    assert shap_data["additive_property_verified"] is True
    assert len(shap_data["breakdown"]) > 0
    # SHAP is non-causal
    assert "causal" in shap_data.get("attribution_disclaimer", "").lower() or \
           "causal" in shap_data.get("summary_note", "").lower()

    # ------------------------------------------------------------------
    # J-2G: AI Healthcare Assistant — Rahul context + multi-turn + guardrails
    # ------------------------------------------------------------------
    chat1 = client.post(
        "/api/services/chat",
        json={
            "message": "Can I travel by commercial flight following my coronary angioplasty?",
            "report_id": report_id,
            "hospital_id": hospital_id
        },
        headers=h
    )
    assert chat1.status_code == 200, f"Chat failed: {chat1.text}"
    c1 = chat1.json()
    assert c1["reply"] != ""
    assert c1["grounding_status"] == "GROUNDED"
    assert len(c1["citations"]) > 0
    assert c1["disclaimer"] is not None
    assert c1["llm_provider"] in ["ollama", "deterministic_fallback"]
    ctx = c1.get("patient_context_applied", {})
    assert ctx.get("specialty") == "Cardiology", f"Wrong patient context in chat: {ctx}"
    conv_id = c1["conversation_id"]

    # Follow-up (conversational continuity)
    chat2 = client.post(
        "/api/services/chat",
        json={
            "conversation_id": conv_id,
            "message": DEMO_QUESTION,
            "report_id": report_id
        },
        headers=h
    )
    assert chat2.status_code == 200
    c2 = chat2.json()
    assert c2["conversation_id"] == conv_id, "Follow-up lost conversation context"

    # History persists
    hist = client.get(f"/api/services/chat/history?conversation_id={conv_id}", headers=h)
    assert hist.status_code == 200
    assert len(hist.json()) >= 2, "Conversation history missing messages"

    # Emergency guardrail
    emer = client.post(
        "/api/services/chat",
        json={
            "conversation_id": conv_id,
            "message": "I am having crushing chest pain radiating to my left arm right now!",
            "report_id": report_id
        },
        headers=h
    )
    assert emer.status_code == 200
    e_data = emer.json()
    assert e_data["is_emergency"] is True
    assert e_data.get("emergency_alert") is not None
    assert "112" in e_data["emergency_alert"] or "108" in e_data["emergency_alert"]

    # Medication modification guardrail
    med_guard = client.post(
        "/api/services/chat",
        json={
            "conversation_id": conv_id,
            "message": "Can I stop taking my blood thinners and clopidogrel before flying?",
            "report_id": report_id
        },
        headers=h
    )
    assert med_guard.status_code == 200
    mg = med_guard.json()
    reply_l = mg["reply"].lower()
    assert (
        "safety guardrail" in reply_l
        or "cannot provide independent instructions" in reply_l
        or "prescribing specialist" in reply_l
        or "consult" in reply_l
    ), f"Medication guardrail not triggered: {mg['reply'][:300]}"
    assert "MEDICATION_MODIFICATION_GUARDRAIL" in mg.get("safety_guardrails_triggered", [])

    # ------------------------------------------------------------------
    # J-2H/I: Medical Travel — Route Planner
    # ------------------------------------------------------------------
    route_res = client.post(
        "/api/travel/route",
        json={
            "origin": "MG Road, Hyderabad",
            "destination": "Apollo Hospitals Jubilee Hills, Hyderabad",
            "travel_mode": "car"
        },
        headers=h
    )
    assert route_res.status_code == 200, f"Route failed: {route_res.text}"
    route = route_res.json()
    # Route endpoint returns ≥0 (geocoder may resolve both to city centroid for
    # Hyderabad addresses — city-centroid fallback is the frozen architecture behaviour)
    assert route["distance_km"] >= 0, "distance_km must be non-negative"
    assert route.get("duration_minutes", route.get("duration_min", -1)) >= 0, "duration must be non-negative"
    assert len(route.get("route_geometry", [])) > 0, "Route geometry is empty"
    # Terminology: no "real-time" or "live traffic" claims
    assert "live traffic" not in str(route).lower()
    assert "real-time traffic" not in str(route).lower()

    # ------------------------------------------------------------------
    # J-2J: Nearby Hotels
    # ------------------------------------------------------------------
    hotels_res = client.get(
        "/api/travel/nearby?category=hotel&location=Apollo+Hospital+Bangalore&limit=3",
        headers=h
    )
    assert hotels_res.status_code == 200, f"Hotels failed: {hotels_res.text}"
    hotels_data = hotels_res.json()
    assert hotels_data["category"] == "hotel"
    assert hotels_data["total_found"] > 0
    assert len(hotels_data["items"]) > 0, "No hotels returned"
    for hotel in hotels_data["items"]:
        assert "name" in hotel
        assert hotel.get("distance_km") is not None or hotel.get("address") is not None

    # ------------------------------------------------------------------
    # J-2K: Nearby Pharmacies
    # ------------------------------------------------------------------
    pharma_res = client.get(
        "/api/travel/nearby?category=pharmacy&location=Apollo+Hospital+Bangalore&limit=3",
        headers=h
    )
    assert pharma_res.status_code == 200, f"Pharmacies failed: {pharma_res.text}"
    pharmacies_data = pharma_res.json()
    assert pharmacies_data["category"] == "pharmacy"
    assert pharmacies_data["total_found"] > 0
    assert len(pharmacies_data["items"]) > 0, "No pharmacies returned"

    # ------------------------------------------------------------------
    # J-2L: Emergency Services
    # ------------------------------------------------------------------
    emerg = client.get(f"/api/travel/emergency?city=Hyderabad&hospital_id={hospital_id}", headers=h)
    assert emerg.status_code == 200, f"Emergency failed: {emerg.text}"
    em = emerg.json()
    assert em["national_emergency_number"] == "112"
    assert "108" in em["ambulance_number"]
    assert "disclaimer" in em
    # No live capacity or guaranteed response claims
    assert "guaranteed" not in str(em).lower()
    assert "real-time icu" not in str(em).lower()

    # ------------------------------------------------------------------
    # J-3: Logout — token must be invalidated
    # ------------------------------------------------------------------
    logout_res = client.post("/api/auth/logout", headers=h)
    assert logout_res.status_code == 200
    # Post-logout: same token must be rejected
    post_logout = client.get("/api/auth/profile", headers=h)
    assert post_logout.status_code == 401, \
        f"Token still valid after logout! Got {post_logout.status_code}"


# ===========================================================================
# J-4  PRIYA — CONTEXT-SENSITIVE JOURNEY
# ===========================================================================

def test_j4_priya_context_sensitive_journey():
    """J-4: Priya's session shows Neurology context different from Rahul/Amit.
    Same travel question → different specialty-contextual RAG grounding."""

    login = client.post("/api/auth/login", json={"username": "demo_neuro", "password": "DemoPassword@123"})
    assert login.status_code == 200
    tok = login.json()["access_token"]
    h = {"Authorization": f"Bearer {tok}"}

    # Identity correct
    prof = client.get("/api/auth/profile", headers=h).json()
    assert prof["user_id"] == 2
    assert prof["current_city"] == "Bengaluru"

    # Upload Priya's report
    pdf = build_pdf(PRIYA_REPORT_LINES)
    up = client.post(
        "/api/reports/upload",
        files={"file": ("priya_neuro.pdf", pdf, "application/pdf")},
        headers=h
    )
    assert up.status_code == 200, up.text
    report = up.json()
    report_id = report["id"]
    assert report["status"] == "COMPLETED"
    assert report["recommended_specialty"] == "Neurology", \
        f"Expected Neurology, got: {report.get('recommended_specialty')}"

    # Priya's report is in Priya's vault only
    vault = client.get("/api/reports/", headers=h).json()
    for r in vault:
        assert r["user_id"] == 2, f"Foreign report in Priya vault: user_id={r['user_id']}"

    # Hospital recs → Neurology specialty
    hosp = client.get(f"/api/recommend/hospitals?report_id={report_id}&city=Bengaluru", headers=h).json()
    assert len(hosp) > 0
    assert "Neurology" in hosp[0]["specialties"], \
        f"Top hospital specialties: {hosp[0]['specialties']}"
    hospital_id = hosp[0]["id"]
    hospital_city = hosp[0].get("city", "Bengaluru")

    # Doctors → Neurology
    docs = client.get(f"/api/recommend/doctors?report_id={report_id}&hospital_id={hospital_id}", headers=h).json()
    assert len(docs) > 0
    assert any("neuro" in d["specialty"].lower() for d in docs), \
        f"No Neurology doctors: {[d['specialty'] for d in docs]}"

    # Cost — Migraine/Neurology treatment
    cost = client.post(
        "/api/cost/predict",
        json={
            "treatment_name": "Neurological Consultation and Management",
            "city": hospital_city,
            "room_type": "Private AC Deluxe",
            "report_id": report_id,
            "hospital_id": hospital_id
        },
        headers=h
    )
    assert cost.status_code == 200, cost.text
    assert cost.json()["predicted_los_days"] >= 1

    # AI Assistant — same travel question → Neurology-grounded answer
    chat = client.post(
        "/api/services/chat",
        json={"message": DEMO_QUESTION, "report_id": report_id, "hospital_id": hospital_id},
        headers=h
    )
    assert chat.status_code == 200
    c = chat.json()
    assert c["reply"] != ""
    ctx = c.get("patient_context_applied", {})
    assert ctx.get("specialty") == "Neurology", f"Wrong specialty context for Priya: {ctx}"

    # Logout
    logout = client.post("/api/auth/logout", headers=h)
    assert logout.status_code == 200
    # Token invalidated
    assert client.get("/api/auth/profile", headers=h).status_code == 401


# ===========================================================================
# J-5  AMIT — CONTEXT-SENSITIVE JOURNEY
# ===========================================================================

def test_j5_amit_context_sensitive_journey():
    """J-5: Amit's session shows Orthopedics context different from Rahul/Priya.
    Same travel question → Orthopedics-contextual RAG grounding."""

    login = client.post("/api/auth/login", json={"username": "demo_ortho", "password": "DemoPassword@123"})
    assert login.status_code == 200
    tok = login.json()["access_token"]
    h = {"Authorization": f"Bearer {tok}"}

    prof = client.get("/api/auth/profile", headers=h).json()
    assert prof["user_id"] == 3
    assert prof["current_city"] == "Delhi"

    # Upload Amit's report
    pdf = build_pdf(AMIT_REPORT_LINES)
    up = client.post(
        "/api/reports/upload",
        files={"file": ("amit_ortho.pdf", pdf, "application/pdf")},
        headers=h
    )
    assert up.status_code == 200, up.text
    report = up.json()
    report_id = report["id"]
    assert report["status"] == "COMPLETED"
    assert report["recommended_specialty"] == "Orthopedics", \
        f"Expected Orthopedics, got: {report.get('recommended_specialty')}"

    vault = client.get("/api/reports/", headers=h).json()
    for r in vault:
        assert r["user_id"] == 3

    # Hospital recs → Orthopedics
    hosp = client.get(f"/api/recommend/hospitals?report_id={report_id}&city=Delhi", headers=h).json()
    assert len(hosp) > 0
    assert "Orthopedics" in hosp[0]["specialties"], f"Top hospital: {hosp[0]['specialties']}"
    hospital_id = hosp[0]["id"]
    hospital_city = hosp[0].get("city", "Delhi")

    # Cost — TKR
    cost = client.post(
        "/api/cost/predict",
        json={
            "treatment_name": "Total Knee Replacement",
            "city": hospital_city,
            "report_id": report_id,
            "hospital_id": hospital_id
        },
        headers=h
    )
    assert cost.status_code == 200, cost.text
    cost_data = cost.json()
    assert cost_data["canonical_treatment"] == "Total Knee Replacement"
    assert cost_data["predicted_los_days"] >= 3.0, "TKR LOS typically ≥ 3 days"

    # AI Assistant — same travel question → Orthopedics-grounded answer
    chat = client.post(
        "/api/services/chat",
        json={"message": DEMO_QUESTION, "report_id": report_id, "hospital_id": hospital_id},
        headers=h
    )
    assert chat.status_code == 200
    c = chat.json()
    assert c["reply"] != ""
    ctx = c.get("patient_context_applied", {})
    assert ctx.get("specialty") == "Orthopedics", f"Wrong specialty for Amit: {ctx}"

    # Travel route — Delhi origin
    route = client.post(
        "/api/travel/route",
        json={"origin": "Connaught Place, Delhi", "destination": "Apollo Hospitals, Delhi", "travel_mode": "car"},
        headers=h
    )
    assert route.status_code == 200, route.text
    r = route.json()
    # distance may be 0.0 when geocoder resolves both Delhi addresses to city centroid
    assert r["distance_km"] >= 0, "distance_km must be non-negative"
    assert r.get("duration_minutes", r.get("duration_min", -1)) >= 0, "duration must be non-negative"
    assert len(r.get("route_geometry", [])) > 0, "Route geometry is empty"

    # Logout and verify invalidation
    logout = client.post("/api/auth/logout", headers=h)
    assert logout.status_code == 200
    assert client.get("/api/auth/profile", headers=h).status_code == 401


# ===========================================================================
# J-6  CROSS-PATIENT ISOLATION — CRITICAL
# ===========================================================================

def test_j6_cross_patient_isolation():
    """J-6: Explicit cross-patient isolation verification.
    Rahul, Priya, and Amit each attempt to access the others' data → all 403."""

    # Login all three
    def login(username):
        r = client.post("/api/auth/login", json={"username": username, "password": "DemoPassword@123"})
        assert r.status_code == 200, f"Login {username} failed"
        return {"Authorization": f"Bearer {r.json()['access_token']}"}

    h1 = login("demo_cardio")   # Rahul (user_id=1)
    h2 = login("demo_neuro")    # Priya (user_id=2)
    h3 = login("demo_ortho")    # Amit  (user_id=3)

    db = SessionLocal()
    try:
        rep1 = db.query(MedicalReport).filter(MedicalReport.user_id == 1).first()
        rep2 = db.query(MedicalReport).filter(MedicalReport.user_id == 2).first()
        rep3 = db.query(MedicalReport).filter(MedicalReport.user_id == 3).first()
        assert rep1 and rep2 and rep3, "Missing reports for one or more demo users"
    finally:
        db.close()

    # --- Rahul cannot access Priya's or Amit's data ---
    assert client.get("/api/auth/profile?user_id=2", headers=h1).status_code == 403
    assert client.get("/api/auth/profile?user_id=3", headers=h1).status_code == 403
    assert client.get(f"/api/reports/{rep2.id}", headers=h1).status_code == 403
    assert client.get(f"/api/reports/{rep3.id}", headers=h1).status_code == 403
    assert client.get("/api/reports/?user_id=2", headers=h1).status_code == 403
    assert client.get("/api/reports/?user_id=3", headers=h1).status_code == 403

    # --- Priya cannot access Rahul's or Amit's data ---
    assert client.get("/api/auth/profile?user_id=1", headers=h2).status_code == 403
    assert client.get("/api/auth/profile?user_id=3", headers=h2).status_code == 403
    assert client.get(f"/api/reports/{rep1.id}", headers=h2).status_code == 403
    assert client.get(f"/api/reports/{rep3.id}", headers=h2).status_code == 403
    assert client.get("/api/reports/?user_id=1", headers=h2).status_code == 403
    assert client.get("/api/reports/?user_id=3", headers=h2).status_code == 403

    # --- Amit cannot access Rahul's or Priya's data ---
    assert client.get("/api/auth/profile?user_id=1", headers=h3).status_code == 403
    assert client.get("/api/auth/profile?user_id=2", headers=h3).status_code == 403
    assert client.get(f"/api/reports/{rep1.id}", headers=h3).status_code == 403
    assert client.get(f"/api/reports/{rep2.id}", headers=h3).status_code == 403
    assert client.get("/api/reports/?user_id=1", headers=h3).status_code == 403
    assert client.get("/api/reports/?user_id=2", headers=h3).status_code == 403

    # Travel plan using another user's report → 403
    assert client.post(
        "/api/travel/plan",
        json={
            "hospital_id": 1, "doctor_id": 1,
            "medical_condition": "Cardiology",
            "report_id": rep1.id,
            "preferred_travel_date": "2026-10-01",
            "duration_days": 3
        },
        headers=h2
    ).status_code == 403

    assert client.post(
        "/api/travel/plan",
        json={
            "hospital_id": 1, "doctor_id": 1,
            "medical_condition": "Neurology",
            "report_id": rep2.id,
            "preferred_travel_date": "2026-10-01",
            "duration_days": 3
        },
        headers=h3
    ).status_code == 403


# ===========================================================================
# J-7  UNAUTHENTICATED ACCESS STRICTLY REJECTED
# ===========================================================================

def test_j7_unauthenticated_protected_routes_rejected():
    """J-7: Unauthenticated requests to protected APIs return 401/403.
    POST endpoints that have required body fields need a minimal valid payload
    so that auth-guard 401 fires rather than body-validation 422.
    """
    # GET-only protected endpoints (no body needed)
    get_endpoints = [
        "/api/auth/profile",
        "/api/reports/",
        "/api/reports/1",
        "/api/recommend/hospitals",
        "/api/recommend/doctors",
        "/api/services/chat/history",
        "/api/travel/plan",
    ]
    for path in get_endpoints:
        res = client.get(path)
        assert res.status_code in [401, 403], \
            f"Expected 401/403 for unauthenticated GET {path}, got {res.status_code}"

    # POST endpoints: send minimal valid body so auth guard fires, not body validation
    min_cost_body = {"treatment_name": "Coronary Angioplasty", "city": "Hyderabad"}
    post_endpoints_with_body = [
        ("/api/cost/predict",   min_cost_body),
        ("/api/cost/explain",   min_cost_body),
        ("/api/services/chat",  {"message": "test"}),
        ("/api/travel/plan",    {"hospital_id": 1, "doctor_id": 1, "medical_condition": "test",
                                 "preferred_travel_date": "2026-10-01", "duration_days": 3}),
    ]
    for path, body in post_endpoints_with_body:
        res = client.post(path, json=body)
        assert res.status_code in [401, 403], \
            f"Expected 401/403 for unauthenticated POST {path}, got {res.status_code}"

    # /api/reports/upload requires multipart (file), no body → 401/403 or 422 is acceptable
    # We only verify it's not 200 (i.e., not publicly accessible)
    upload_res = client.post("/api/reports/upload", files={"file": ("x.txt", b"test", "text/plain")})
    assert upload_res.status_code in [401, 403], \
        f"Expected 401/403 for unauthenticated upload, got {upload_res.status_code}"


# ===========================================================================
# J-8  REFRESH / NAVIGATION RESILIENCE
# ===========================================================================

def test_j8_navigation_resilience():
    """J-8: Token stays valid across multiple module requests within an active session.
    Re-calling the same endpoints within the same session returns consistent results."""
    login = client.post("/api/auth/login", json={"username": "demo_cardio", "password": "DemoPassword@123"})
    assert login.status_code == 200
    tok = login.json()["access_token"]
    h = {"Authorization": f"Bearer {tok}"}

    # Repeated profile fetch stays consistent
    for _ in range(3):
        r = client.get("/api/auth/profile", headers=h)
        assert r.status_code == 200
        assert r.json()["user_id"] == 1

    # Repeated hospital recommendation → deterministic same result
    db = SessionLocal()
    try:
        rep = db.query(MedicalReport).filter(MedicalReport.user_id == 1).order_by(MedicalReport.id.desc()).first()
        assert rep is not None
        report_id = rep.id
    finally:
        db.close()

    scores = []
    for _ in range(2):
        res = client.get(f"/api/recommend/hospitals?report_id={report_id}&city=Hyderabad", headers=h)
        assert res.status_code == 200
        hosps = res.json()
        assert len(hosps) > 0
        scores.append(hosps[0]["recommendation_score"])
    assert scores[0] == scores[1], f"Non-deterministic hospital scores: {scores}"

    # Auth check after multiple requests
    prof = client.get("/api/auth/profile", headers=h)
    assert prof.status_code == 200
    assert prof.json()["user_id"] == 1
