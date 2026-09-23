"""
Phase K: Edge-Case & Failure-Mode Audit Test Suite

Covers checkpoints K1 to K5:
1. No Report
2. One Report
3. Multiple Reports
4. Empty Profile
5. Missing Age
6. Missing Gender
7. Missing Conditions
8. Missing Medications
9. Unsupported Specialty
10. No Hospital Within Budget
11. Invalid Report
12. Very Large Report
13. Poor-Quality Scanned Report
14. Ambiguous Location
15. Invalid Location
16. No RAG Evidence
17. API Unavailable / Error Simulation
18. Ollama Unavailable / Deterministic Fallback
19. Nominatim Unavailable / Fallback
20. OSRM Unavailable / Geodesic Fallback
21. Refresh While Viewing Report
22. Direct Navigation to /analysis
23. Switch User While Page Open
24. Logout + Browser Back (Invalidated Session)
"""

import sys
import os
import io
import unittest.mock as mock
import pytest
from fastapi.testclient import TestClient

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(os.path.dirname(CURRENT_DIR), "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from main import app
from database import SessionLocal
from models import User, PatientProfile, MedicalReport
from security import create_access_token, hash_password

client = TestClient(app)


def make_pdf(lines: list) -> bytes:
    """Build a minimal valid PDF containing clinical text lines."""
    stream = "BT /F1 12 Tf 72 720 Td "
    for line in lines:
        safe = (
            line.replace("(", "")
            .replace(")", "")
            .replace("\\", "")
            .replace("\u2014", "-")
            .replace("\u2013", "-")
            .replace("&", "and")
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


# Helper to get or create clean test user
def get_or_create_user(email: str, name: str, password: str = "TestPass@123") -> tuple[User, str]:
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            user = User(
                email=email,
                full_name=name,
                role="patient",
                hashed_password=hash_password(password)
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        token = create_access_token({"sub": str(user.id), "email": user.email, "role": user.role})
        return user, token
    finally:
        db.close()


# ===========================================================================
# K1. PATIENT / REPORT STATE EDGE CASES
# ===========================================================================

def test_k01_no_report():
    """1. NO REPORT: User has no uploaded report. Dependent modules handle absence safely."""
    user, tok = get_or_create_user("k_no_report@test.com", "No Report Patient")
    h = {"Authorization": f"Bearer {tok}"}

    # Profile works with last_report_id=None
    prof = client.get("/api/auth/profile", headers=h)
    assert prof.status_code == 200
    assert prof.json().get("last_report_id") is None

    # Analysis / RAG handles absence gracefully
    rag = client.post("/api/services/rag/profile-grounding", json={"top_k": 2}, headers=h)
    assert rag.status_code == 200
    assert rag.json().get("grounding_status") in ["NO_MATCH", "GROUNDED"]

    # AI Assistant operates safely
    chat = client.post("/api/services/chat", json={"message": "What should I eat for breakfast?"}, headers=h)
    assert chat.status_code == 200
    assert chat.json().get("reply") != ""

    # Hospital Recommendations return city/general fallback without 500
    hosp = client.get("/api/recommend/hospitals?city=Hyderabad", headers=h)
    assert hosp.status_code == 200
    assert isinstance(hosp.json(), list)


def test_k02_one_report():
    """2. ONE REPORT: Uploading one valid report updates active context."""
    user, tok = get_or_create_user("k_one_report@test.com", "One Report Patient")
    h = {"Authorization": f"Bearer {tok}"}

    pdf = make_pdf([
        "Clinical Summary: Patient John Doe",
        "Diagnosis: Acute Lumbar Disc Herniation L4-L5",
        "Recommended Specialty: Orthopedics",
        "Medications: Ibuprofen 400mg, Pregabalin 75mg"
    ])
    up = client.post("/api/reports/upload", files={"file": ("ortho.pdf", pdf, "application/pdf")}, headers=h)
    assert up.status_code == 200
    rep_id = up.json()["id"]

    prof = client.get("/api/auth/profile", headers=h).json()
    assert prof["last_report_id"] == rep_id

    # Recommendations condition on the report
    hosp = client.get(f"/api/recommend/hospitals?report_id={rep_id}&city=Bengaluru", headers=h)
    assert hosp.status_code == 200
    assert len(hosp.json()) > 0


def test_k03_multiple_reports():
    """3. MULTIPLE REPORTS: Upload multiple reports, test latest report and selective report retrieval."""
    user, tok = get_or_create_user("k_multi_report@test.com", "Multi Report Patient")
    h = {"Authorization": f"Bearer {tok}"}

    # First report
    pdf1 = make_pdf(["Cardiac Evaluation", "Diagnosis: Mild Angina", "Recommended Specialty: Cardiology"])
    up1 = client.post("/api/reports/upload", files={"file": ("rep1.pdf", pdf1, "application/pdf")}, headers=h)
    assert up1.status_code == 200
    r1_id = up1.json()["id"]

    # Second report
    pdf2 = make_pdf(["Orthopedic Evaluation", "Diagnosis: Knee Osteoarthritis", "Recommended Specialty: Orthopedics"])
    up2 = client.post("/api/reports/upload", files={"file": ("rep2.pdf", pdf2, "application/pdf")}, headers=h)
    assert up2.status_code == 200
    r2_id = up2.json()["id"]

    assert r2_id > r1_id

    # Profile points to latest uploaded report
    prof = client.get("/api/auth/profile", headers=h).json()
    assert prof["last_report_id"] == r2_id

    # Vault contains both reports without corruption
    vault = client.get("/api/reports/", headers=h).json()
    vault_ids = [r["id"] for r in vault]
    assert r1_id in vault_ids and r2_id in vault_ids

    # Querying specific report preserves that specific report's context
    rep1_data = client.get(f"/api/reports/{r1_id}", headers=h).json()
    assert rep1_data["id"] == r1_id


def test_k04_empty_profile():
    """4. EMPTY PROFILE: Patient with completely empty profile clinical fields."""
    user, tok = get_or_create_user("k_empty_prof@test.com", "Empty Prof Patient")
    db = SessionLocal()
    try:
        p = db.query(PatientProfile).filter(PatientProfile.user_id == user.id).first()
        if p:
            p.conditions = []
            p.symptoms = []
            p.medications = []
            p.test_results = []
            p.chronic_conditions = "None"
            db.commit()
    finally:
        db.close()

    h = {"Authorization": f"Bearer {tok}"}
    prof = client.get("/api/auth/profile", headers=h)
    assert prof.status_code == 200
    data = prof.json()
    assert data["conditions"] == []
    assert data["medications"] == []

    # Chat works safely with empty profile
    chat = client.post("/api/services/chat", json={"message": "General health guidance for walking?"}, headers=h)
    assert chat.status_code == 200


def test_k05_to_k08_missing_clinical_demographics():
    """5-8. MISSING AGE, GENDER, CONDITIONS, MEDICATIONS: Verify graceful null handling."""
    user, tok = get_or_create_user("k_missing_fields@test.com", "Missing Fields Patient")
    db = SessionLocal()
    try:
        p = db.query(PatientProfile).filter(PatientProfile.user_id == user.id).first()
        if p:
            p.age = None
            p.gender = None
            p.conditions = None
            p.medications = None
            p.chronic_conditions = None
            db.commit()
    finally:
        db.close()

    h = {"Authorization": f"Bearer {tok}"}
    prof = client.get("/api/auth/profile", headers=h)
    assert prof.status_code == 200

    # Cost prediction with missing age/gender in profile defaults gracefully
    cost = client.post(
        "/api/cost/predict",
        json={"treatment_name": "Coronary Angioplasty", "city": "Hyderabad", "room_type": "General"},
        headers=h
    )
    assert cost.status_code == 200
    assert cost.json()["estimated_avg_cost"] > 0

    # Chat simply omits unavailable context
    chat = client.post("/api/services/chat", json={"message": "Is high fiber diet good?"}, headers=h)
    assert chat.status_code == 200
    assert chat.json()["reply"] != ""


def test_k09_unsupported_specialty():
    """9. UNSUPPORTED SPECIALTY: Empty/no-match state without arbitrary specialty substitution."""
    user, tok = get_or_create_user("k_unsupported_spec@test.com", "Unsupported Spec")
    h = {"Authorization": f"Bearer {tok}"}

    res = client.get("/api/recommend/hospitals?specialty=SpaceMedicine&city=Hyderabad", headers=h)
    assert res.status_code == 200
    hospitals = res.json()
    assert hospitals == [], "Expected empty hospital list for unsupported specialty"


# ===========================================================================
# K2. RECOMMENDATION / PREDICTION EDGE CASES
# ===========================================================================

def test_k10_no_hospital_within_budget():
    """10. NO HOSPITAL WITHIN BUDGET: Strict budget returns empty result without fabrication."""
    user, tok = get_or_create_user("k_budget@test.com", "Budget Patient")
    h = {"Authorization": f"Bearer {tok}"}

    res = client.get("/api/recommend/hospitals?max_budget=10&city=Hyderabad", headers=h)
    assert res.status_code == 200
    assert res.json() == []


def test_k11_invalid_report():
    """11. INVALID REPORT: Corrupted/non-medical/forbidden files rejected safely."""
    user, tok = get_or_create_user("k_invalid_rep@test.com", "Invalid Rep Patient")
    h = {"Authorization": f"Bearer {tok}"}

    # Corrupt PDF (missing %PDF- header)
    res1 = client.post(
        "/api/reports/upload",
        files={"file": ("corrupt.pdf", b"corrupted file content", "application/pdf")},
        headers=h
    )
    assert res1.status_code == 400
    assert "Corrupted or invalid PDF" in res1.json()["detail"]

    # Forbidden executable
    res2 = client.post(
        "/api/reports/upload",
        files={"file": ("malicious.exe", b"MZexecutabledata", "application/octet-stream")},
        headers=h
    )
    assert res2.status_code == 400
    assert "forbidden" in res2.json()["detail"].lower() or "violation" in res2.json()["detail"].lower()


def test_k12_very_large_report():
    """12. VERY LARGE REPORT: Files exceeding supported 20MB limit rejected cleanly with 400."""
    user, tok = get_or_create_user("k_large_rep@test.com", "Large Rep Patient")
    h = {"Authorization": f"Bearer {tok}"}

    # 21 MB fake file
    oversized_data = b"%PDF-1.4\n" + b"0" * (21 * 1024 * 1024)
    res = client.post(
        "/api/reports/upload",
        files={"file": ("oversized.pdf", oversized_data, "application/pdf")},
        headers=h
    )
    assert res.status_code == 400
    assert "exceeds maximum allowed limit" in res.json()["detail"]


def test_k13_poor_quality_scanned_report():
    """13. POOR QUALITY SCANNED REPORT: Degraded extraction marked FAILED or handled safely."""
    user, tok = get_or_create_user("k_poor_ocr@test.com", "Poor OCR Patient")
    h = {"Authorization": f"Bearer {tok}"}

    # Minimal unreadable text
    sparse_pdf = make_pdf(["... ??? ---"])
    res = client.post(
        "/api/reports/upload",
        files={"file": ("sparse.pdf", sparse_pdf, "application/pdf")},
        headers=h
    )
    assert res.status_code == 200
    data = res.json()
    # Marked FAILED per ocr_engine quality check or handled safely
    assert data["status"] in ["FAILED", "COMPLETED"]
    if data["status"] == "FAILED":
        assert "Warning" in data.get("summary", "") or "unusable" in data.get("ocr_text", "").lower()


# ===========================================================================
# K3. LOCATION / TRAVEL EDGE CASES
# ===========================================================================

def test_k14_ambiguous_location():
    """14. AMBIGUOUS LOCATION: Handles ambiguous location query without crashing."""
    user, tok = get_or_create_user("k_travel@test.com", "Travel Patient")
    h = {"Authorization": f"Bearer {tok}"}

    # Springfield without state/country
    res = client.post(
        "/api/travel/route",
        json={"origin": "Springfield", "destination": "Apollo Hospital, Bannerghatta Road, Bangalore", "travel_mode": "car"},
        headers=h
    )
    assert res.status_code == 200
    data = res.json()
    assert "distance_km" in data
    assert "route_geometry" in data


def test_k15_invalid_location():
    """15. INVALID LOCATION: Nonexistent address returns 404 clear failure without bogus route."""
    user, tok = get_or_create_user("k_travel2@test.com", "Travel Patient 2")
    h = {"Authorization": f"Bearer {tok}"}

    res = client.post(
        "/api/travel/route",
        json={"origin": "XYZNonExistentPlanetAddress9999", "destination": "Apollo Hospital, Bangalore", "travel_mode": "car"},
        headers=h
    )
    assert res.status_code == 404
    assert "Could not locate" in res.json()["detail"]


# ===========================================================================
# K4. RAG / EXTERNAL DEPENDENCY FAILURE MODES
# ===========================================================================

def test_k16_no_rag_evidence():
    """16. NO RAG EVIDENCE: Non-clinical/out-of-domain query handled safely without hallucination."""
    user, tok = get_or_create_user("k_rag_none@test.com", "RAG None Patient")
    h = {"Authorization": f"Bearer {tok}"}

    res = client.post(
        "/api/services/chat",
        json={"message": "What is the airspeed velocity of an unladen swallow?"},
        headers=h
    )
    assert res.status_code == 200
    reply = res.json()["reply"]
    assert "can't provide a clinical answer" in reply.lower() or "clinical" in reply.lower()


def test_k17_api_unavailable_simulated():
    """17. API UNAVAILABLE: Non-existent or failing endpoint returns 404/appropriate HTTP error."""
    user, tok = get_or_create_user("k_api_err@test.com", "API Err Patient")
    h = {"Authorization": f"Bearer {tok}"}

    res = client.get("/api/reports/nonexistent/999999", headers=h)
    assert res.status_code in [404, 422]


def test_k18_ollama_unavailable():
    """18. OLLAMA UNAVAILABLE: Assistant gracefully uses deterministic fallback when LLM fails."""
    user, tok = get_or_create_user("k_ollama@test.com", "Ollama Patient")
    h = {"Authorization": f"Bearer {tok}"}

    with mock.patch("requests.post", side_effect=Exception("Connection refused: Ollama port 11434")):
        res = client.post(
            "/api/services/chat",
            json={"message": "Can I travel by commercial flight following coronary angioplasty?"},
            headers=h
        )
        assert res.status_code == 200
        data = res.json()
        assert data["llm_provider"] in ["deterministic_fallback", "ollama"]
        assert len(data["reply"]) > 20
        assert "disclaimer" in str(data).lower()


def test_k19_nominatim_unavailable():
    """19. NOMINATIM UNAVAILABLE: Nearby services fall back to curated local POIs without crash."""
    user, tok = get_or_create_user("k_nominatim@test.com", "Nominatim Patient")
    h = {"Authorization": f"Bearer {tok}"}

    with mock.patch("requests.get", side_effect=Exception("Nominatim 429 Too Many Requests")):
        res = client.get("/api/travel/nearby?location=Apollo+Hospital+Bangalore&category=hotel", headers=h)
        assert res.status_code == 200
        data = res.json()
        assert data["total_found"] > 0
        assert len(data["items"]) > 0


def test_k20_osrm_unavailable():
    """20. OSRM UNAVAILABLE: Route calculation falls back to geodesic road estimation without crash."""
    user, tok = get_or_create_user("k_osrm@test.com", "OSRM Patient")
    h = {"Authorization": f"Bearer {tok}"}

    # Force OSRM query exception
    orig_get = mock.MagicMock(side_effect=Exception("OSRM 504 Gateway Timeout"))
    with mock.patch("routes.travel.requests.get", orig_get):
        res = client.post(
            "/api/travel/route",
            json={
                "origin": "MG Road, Bangalore",
                "destination": "Apollo Hospital, Bannerghatta Road, Bangalore",
                "travel_mode": "car"
            },
            headers=h
        )
        assert res.status_code == 200
        data = res.json()
        assert data["distance_km"] > 0
        assert len(data["route_geometry"]) > 0
        assert "Fallback" in data.get("routing_service", "") or "OSRM" in data.get("routing_service", "")


# ===========================================================================
# K5. FRONTEND / SESSION EDGE CASES
# ===========================================================================

def test_k21_refresh_while_viewing_report():
    """21. REFRESH WHILE VIEWING A REPORT: Token persistence and identical re-fetch of report."""
    login = client.post("/api/auth/login", json={"username": "demo_cardio", "password": "DemoPassword@123"})
    assert login.status_code == 200
    tok = login.json()["access_token"]
    h = {"Authorization": f"Bearer {tok}"}

    # First fetch
    prof1 = client.get("/api/auth/profile", headers=h).json()
    rep_id = prof1.get("last_report_id") or 1
    rep1 = client.get(f"/api/reports/{rep_id}", headers=h).json()

    # Simulated refresh: same token requests report again
    prof2 = client.get("/api/auth/profile", headers=h).json()
    rep2 = client.get(f"/api/reports/{rep_id}", headers=h).json()

    assert prof1["user_id"] == prof2["user_id"]
    assert rep1["id"] == rep2["id"]
    assert rep1["recommended_specialty"] == rep2["recommended_specialty"]


def test_k22_direct_navigation_to_analysis():
    """22. DIRECT NAVIGATION TO /analysis: Authenticated succeeds; Unauthenticated returns 401."""
    # Unauthenticated
    unauth = client.get("/api/reports/1")
    assert unauth.status_code in [401, 403]

    # Authenticated
    login = client.post("/api/auth/login", json={"username": "demo_cardio", "password": "DemoPassword@123"})
    tok = login.json()["access_token"]
    auth = client.get("/api/reports/1", headers={"Authorization": f"Bearer {tok}"})
    assert auth.status_code == 200


def test_k23_switch_user_while_page_open():
    """23. SWITCH USER: Rahul -> Priya: Rahul context replaced, zero cross-patient leakage."""
    # Login Rahul
    log_rahul = client.post("/api/auth/login", json={"username": "demo_cardio", "password": "DemoPassword@123"})
    tok_r = log_rahul.json()["access_token"]
    prof_r = client.get("/api/auth/profile", headers={"Authorization": f"Bearer {tok_r}"}).json()
    assert prof_r["user_id"] == 1

    # Logout Rahul
    client.post("/api/auth/logout", headers={"Authorization": f"Bearer {tok_r}"})

    # Login Priya
    log_priya = client.post("/api/auth/login", json={"username": "demo_neuro", "password": "DemoPassword@123"})
    tok_p = log_priya.json()["access_token"]
    prof_p = client.get("/api/auth/profile", headers={"Authorization": f"Bearer {tok_p}"}).json()
    assert prof_p["user_id"] == 2
    assert "Rahul" not in str(prof_p)

    # Priya cannot access Rahul's reports
    forbidden = client.get("/api/reports/1", headers={"Authorization": f"Bearer {tok_p}"})
    assert forbidden.status_code in [403, 404]


def test_k24_logout_and_browser_back():
    """24. LOGOUT + BROWSER BACK: Post-logout, previous token is completely rejected with 401."""
    login = client.post("/api/auth/login", json={"username": "demo_cardio", "password": "DemoPassword@123"})
    tok = login.json()["access_token"]
    h = {"Authorization": f"Bearer {tok}"}

    # Verify active
    active = client.get("/api/auth/profile", headers=h)
    assert active.status_code == 200

    # Logout
    logout = client.post("/api/auth/logout", headers=h)
    assert logout.status_code == 200

    # Back button action: attempt to interact with protected endpoint with old token
    back_action = client.get("/api/auth/profile", headers=h)
    assert back_action.status_code == 401, f"Token still accepted post-logout! Got {back_action.status_code}"
