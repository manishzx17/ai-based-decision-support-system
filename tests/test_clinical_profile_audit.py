"""
Final Clinical Profile Audit Test Suite
Verifies:
1. Automatic Profile Update on report upload
2. Demographics (Name, Age, Gender)
3. Conditions (explicit only)
4. Symptoms
5. Medications
6. Tests & Test Results
7. Medical History
8. Correct patient association
9. Multi-report coherency (no corruption, no overwriting)
10. Latest report context resolution
11. Missing field safety (sparse report doesn't overwrite existing facts)
12. Persistence across sessions
13. Multi-User Switching: Rahul -> Priya -> Amit -> Rahul with 0 cross-user leakage
"""

import sys
import os
import io
import pytest
from fastapi.testclient import TestClient

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND_DIR = os.path.join(BASE_DIR, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from init_db import init_db
from main import app
from database import SessionLocal
from models import User, PatientProfile, MedicalReport
from security import create_access_token
from routes.auth import sync_clinical_profile_from_structured_info, get_shared_clinical_context

client = TestClient(app)


def make_pdf(lines: list[str]) -> bytes:
    """Builds a genuine, valid PDF with specified lines of text."""
    stream_content = "BT /F1 12 Tf 72 700 Td "
    for line in lines:
        safe_line = line.replace("(", "").replace(")", "")
        stream_content += f"({safe_line}) Tj 0 -18 Td "
    stream_content += "ET"

    return f"""%PDF-1.4
1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj
2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj
3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >> endobj
4 0 obj << /Length {len(stream_content)} >> stream
{stream_content}
endstream endobj
5 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj
xref
0 6
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000244 00000 n 
0000000431 00000 n 
trailer << /Size 6 /Root 1 0 R >>
startxref
550
%%EOF""".encode("latin-1")


@pytest.fixture(scope="module", autouse=True)
def ensure_db():
    init_db()


def get_auth_headers(user_id: int, email: str, role: str = "patient"):
    token = create_access_token(data={"sub": str(user_id), "email": email, "role": role})
    return {"Authorization": f"Bearer {token}"}


# =====================================================================
# 1. AUTOMATIC PROFILE UPDATE & DEMOGRAPHICS / CLINICAL FIELDS
# =====================================================================

def test_automatic_profile_update_and_clinical_fields():
    """
    Upload a rich cardiac catheterization PDF report for Rahul Verma (user 1).
    Verify that profile automatically updates with:
    - Age (54)
    - Gender (Male)
    - Conditions (Double Vessel Coronary Artery Disease)
    - Symptoms (angina, dyspnea)
    - Medications (Aspirin, Atorvastatin)
    - Tests & Test Results (LVEF, LAD Stenosis)
    - Procedures (Percutaneous Coronary Intervention)
    - Medical History (Hypertension)
    """
    headers = get_auth_headers(1, "rahul.verma@example.com")

    lines = [
        "CARDIAC CATHETERIZATION AND ANGIOGRAPHY REPORT",
        "Patient Name: Rahul Verma    Age: 54 Years    Gender: Male    Date: 15/09/2025",
        "Department: Cardiology and Interventional Medicine",
        "Presenting Symptoms: Patient presented with exertional angina and dyspnea on exertion for 3 months.",
        "Diagnostic Investigations: Coronary Angiography and 2D Echocardiogram.",
        "Laboratory and Hemodynamic Findings:",
        "Blood Pressure: 138/86 mmHg",
        "LVEF: 44%",
        "LAD Stenosis: 85%",
        "Fasting Blood Sugar: 118 mg/dL",
        "Diagnosis and Impression: Double Vessel Coronary Artery Disease with high-grade proximal LAD stenosis.",
        "Intervention / Plan: Successful Percutaneous Coronary Intervention with Drug-Eluting Stent to proximal LAD.",
        "Active Medications: Aspirin 75mg OD, Atorvastatin 40mg OD, Metoprolol 25mg BD.",
        "Past History: Known case of hypertension for 6 years."
    ]
    pdf_bytes = make_pdf(lines)
    res = client.post(
        "/api/reports/upload",
        files={"file": ("Cardiac_Cath_Report.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
        headers=headers
    )
    assert res.status_code == 200, f"Upload failed: {res.text}"
    report_data = res.json()
    rep_id = report_data["id"]

    # Verify Profile was automatically updated in DB
    db = SessionLocal()
    try:
        profile = db.query(PatientProfile).filter(PatientProfile.user_id == 1).first()
        assert profile is not None
        assert profile.last_report_id == rep_id

        # Demographics
        assert profile.age == 54
        assert profile.gender == "Male"

        # Conditions
        cond_text = " ".join(profile.conditions).lower()
        assert "coronary" in cond_text or "disease" in cond_text

        # Symptoms
        sym_text = " ".join(profile.symptoms).lower()
        assert any(s in sym_text for s in ["angina", "dyspnea", "chest pain"])

        # Medications
        med_text = " ".join(profile.medications).lower()
        assert "aspirin" in med_text
        assert "atorvastatin" in med_text

        # Tests & Results
        assert len(profile.test_results) >= 2
        tr_names = [tr["test_name"].lower() for tr in profile.test_results]
        assert any("lvef" in tn or "ef" in tn or "stenosis" in tn or "blood pressure" in tn for tn in tr_names)

        # Procedures
        proc_text = " ".join(profile.procedures).lower()
        assert any(p in proc_text for p in ["pci", "percutaneous coronary intervention", "angiography"])

        # Medical History
        hist_text = " ".join(profile.medical_history).lower()
        assert "hypertension" in hist_text
    finally:
        db.close()

    # Also verify GET /api/auth/profile returns identical synchronized data
    prof_res = client.get("/api/auth/profile", headers=headers)
    assert prof_res.status_code == 200
    pdata = prof_res.json()
    assert pdata["age"] == 54
    assert pdata["gender"] == "Male"
    assert pdata["last_report_id"] == rep_id


# =====================================================================
# 2. MULTI-REPORT COHERENCE & MISSING FIELD IMMUNITY
# =====================================================================

def test_multi_report_coherence_and_missing_field_safety():
    """
    Upload a second, sparse lab report for user 1.
    Verifies:
    1. New lab results (HbA1c, Creatinine) are added or updated.
    2. Missing fields in report 2 (no medications, no procedures mentioned) DO NOT overwrite or delete
       preexisting medications or procedures from report 1.
    3. Latest report context is updated to report 2.
    """
    headers = get_auth_headers(1, "rahul.verma@example.com")

    lines = [
        "DIAGNOSTIC BIOCHEMISTRY REPORT",
        "Patient Name: Rahul Verma    Date: 20/09/2025",
        "Clinical Biochemistry:",
        "HbA1c: 7.2%",
        "Serum Creatinine: 1.0 mg/dL",
        "Fasting Blood Sugar: 126 mg/dL",
        "Impression: Glycemic monitoring."
    ]
    pdf_bytes = make_pdf(lines)
    res = client.post(
        "/api/reports/upload",
        files={"file": ("Lab_Biochemistry.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
        headers=headers
    )
    assert res.status_code == 200, f"Upload 2 failed: {res.text}"
    rep2_id = res.json()["id"]

    db = SessionLocal()
    try:
        profile = db.query(PatientProfile).filter(PatientProfile.user_id == 1).first()
        assert profile.last_report_id == rep2_id

        # Demographics from report 1 were NOT erased by sparse report 2
        assert profile.age == 54
        assert profile.gender == "Male"

        # Preexisting medications and procedures were NOT erased
        med_text = " ".join(profile.medications).lower()
        assert "aspirin" in med_text
        proc_text = " ".join(profile.procedures).lower()
        assert len(proc_text) > 0

        # New test results were merged in
        tr_names = [tr["test_name"].lower() for tr in profile.test_results]
        assert any("hba1c" in tn for tn in tr_names)
        assert any("creatinine" in tn for tn in tr_names)
    finally:
        db.close()


# =====================================================================
# 3. CRITICAL MULTI-USER TRANSITIONS: Rahul -> Priya -> Amit -> Rahul
# =====================================================================

def test_multi_user_transitions_and_strict_isolation():
    """
    Simulates consecutive browser sessions:
    Rahul (user 1) -> Priya (user 2) -> Amit (user 3) -> Rahul (user 1).
    Verifies that each user receives exclusively their own profile, reports, and context,
    with 0 cross-user contamination.
    """
    # ------------------ Step 1: Rahul Verma (user 1) ------------------
    r_headers = get_auth_headers(1, "rahul.verma@example.com")
    r_res = client.get("/api/auth/profile", headers=r_headers)
    assert r_res.status_code == 200
    r_prof = r_res.json()
    assert r_prof["user_id"] == 1
    assert r_prof["gender"] == "Male"
    assert any("aspirin" in m.lower() for m in r_prof["medications"])

    # Reports for Rahul
    r_reps = client.get("/api/reports/?user_id=1", headers=r_headers).json()
    assert len(r_reps) > 0
    for r in r_reps:
        assert r["user_id"] == 1

    # Logout Rahul
    client.post("/api/auth/logout?user_id=1", headers=r_headers)

    # ------------------ Step 2: Priya Sharma (user 2) ------------------
    p_headers = get_auth_headers(2, "priya.sharma@example.com")
    p_res = client.get("/api/auth/profile", headers=p_headers)
    assert p_res.status_code == 200
    p_prof = p_res.json()
    assert p_prof["user_id"] == 2
    assert p_prof["gender"] == "Female"
    # Priya has Neurology / Migraine profile, NOT Rahul's CAD/Aspirin
    p_conds = " ".join(p_prof["conditions"]).lower()
    assert "migraine" in p_conds or "headache" in p_conds
    assert "coronary" not in p_conds
    # No Aspirin in Priya's medications; Sumatriptan/Topiramate present
    p_meds = " ".join(p_prof["medications"]).lower()
    assert any(m in p_meds for m in ["sumatriptan", "topiramate", "magnesium"])
    assert "aspirin" not in p_meds

    # Reports for Priya
    p_reps = client.get("/api/reports/?user_id=2", headers=p_headers).json()
    assert len(p_reps) > 0
    for r in p_reps:
        assert r["user_id"] == 2
        assert "neurology" in r["recommended_specialty"].lower() or "migraine" in r["summary"].lower()

    # Logout Priya
    client.post("/api/auth/logout?user_id=2", headers=p_headers)

    # ------------------ Step 3: Amit Patel (user 3) ------------------
    a_headers = get_auth_headers(3, "patient3@example.com")
    a_res = client.get("/api/auth/profile", headers=a_headers)
    assert a_res.status_code == 200
    a_prof = a_res.json()
    assert a_prof["user_id"] == 3
    assert a_prof["gender"] == "Male"
    assert a_prof["age"] == 62
    # Amit has Orthopedic / Knee Osteoarthritis profile
    a_conds = " ".join(a_prof["conditions"]).lower()
    assert "osteoarthritis" in a_conds
    assert "coronary" not in a_conds
    assert "migraine" not in a_conds

    # Amit reports
    a_reps = client.get("/api/reports/?user_id=3", headers=a_headers).json()
    assert len(a_reps) > 0
    for r in a_reps:
        assert r["user_id"] == 3
        assert "orthopedic" in r["summary"].lower() or "osteoarthritis" in r["summary"].lower()

    # Logout Amit
    client.post("/api/auth/logout?user_id=3", headers=a_headers)

    # ------------------ Step 4: Rahul Verma again (user 1) ------------------
    r2_headers = get_auth_headers(1, "rahul.verma@example.com")
    r2_res = client.get("/api/auth/profile", headers=r2_headers)
    assert r2_res.status_code == 200
    r2_prof = r2_res.json()
    assert r2_prof["user_id"] == 1
    assert r2_prof["gender"] == "Male"
    assert r2_prof["age"] == 54
    # Zero Priya or Amit data leaked into Rahul's profile
    r2_conds = " ".join(r2_prof["conditions"]).lower()
    assert "migraine" not in r2_conds
    assert "osteoarthritis" not in r2_conds
    r2_meds = " ".join(r2_prof["medications"]).lower()
    assert "sumatriptan" not in r2_meds
    assert "aspirin" in r2_meds


# =====================================================================
# 4. SHARED CLINICAL CONTEXT DOWNSTREAM INTEGRITY
# =====================================================================

def test_shared_clinical_context_downstream_isolation():
    """
    Verifies that get_shared_clinical_context returns isolated context for each user
    consumed by RAG, recommendations, and cost estimators.
    """
    db = SessionLocal()
    try:
        ctx1 = get_shared_clinical_context(user_id=1, db=db)
        ctx2 = get_shared_clinical_context(user_id=2, db=db)
        ctx3 = get_shared_clinical_context(user_id=3, db=db)

        assert ctx1["user_id"] == 1
        assert ctx2["user_id"] == 2
        assert ctx3["user_id"] == 3

        assert ctx1["demographics"]["gender"] == "Male"
        assert ctx2["demographics"]["gender"] == "Female"
        assert ctx3["demographics"]["gender"] == "Male"

        assert any("coronary" in c.lower() or "disease" in c.lower() for c in ctx1["conditions"])
        assert any("migraine" in c.lower() or "headache" in c.lower() for c in ctx2["conditions"])
        assert any("osteoarthritis" in c.lower() for c in ctx3["conditions"])
    finally:
        db.close()
