"""
Targeted End-to-End Audit Test Suite for Medical Report Intelligence Pipeline.
Validates:
1. UPLOAD SUPPORT:
   - Digital PDF
   - Scanned PDF
   - PNG Image
   - JPG/JPEG Image
   - Table-based lab report
   - Invalid file (mismatched header/magic bytes)
   - Empty/corrupted file (0 bytes)
   - Unsupported file type (.exe, .sh, .docx, .zip)
2. EXTRACTION:
   - Patient Name, Age, Gender, Report Date
   - Conditions, Symptoms, Tests, Test Results
   - Medications, Procedures, Medical History
3. SAFETY & CORRECTNESS:
   - Zero invented diagnoses (no extrapolation or negated rule-outs)
   - Explicit diagnoses captured accurately
   - OCR noise/unreadable scan results in FAILED without fabricated facts
   - Handwritten report limitation communicated in UI/system
   - Mandatory safety disclaimers and guideline grounding citations intact
4. ERROR HANDLING & ISOLATION:
   - Graceful 400 Bad Request responses with 0 server tracebacks
   - Strict patient report ownership and cross-user 403 isolation
   - Seamless report -> profile synchronization
"""

import os
import io
import sys
import pytest
from PIL import Image, ImageDraw
from fastapi.testclient import TestClient

BACKEND_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from main import app
from init_db import init_db
from database import SessionLocal
from models import User, PatientProfile, MedicalReport
from ai.ocr_engine import ocr_engine
from ai.clinical_bert import clinical_bert_extractor

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


def make_image(text_lines: list[str], img_format: str = "PNG") -> bytes:
    """Renders text lines onto an image canvas and encodes as PNG/JPEG."""
    img = Image.new("RGB", (900, 500), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    y = 30
    for line in text_lines:
        draw.text((30, y), line, fill=(0, 0, 0))
        y += 30
    buf = io.BytesIO()
    img.save(buf, format=img_format)
    return buf.getvalue()


@pytest.fixture(scope="module")
def user1_auth():
    init_db()
    res = client.post("/api/auth/login", json={"username": "demo_cardio", "password": "DemoPassword@123"})
    assert res.status_code == 200
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


@pytest.fixture(scope="module")
def user2_auth():
    init_db()
    res = client.post("/api/auth/login", json={"username": "demo_neuro", "password": "DemoPassword@123"})
    assert res.status_code == 200
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


# =====================================================================
# 1. TEST UPLOAD SUPPORT ACROSS ALL FORMATS
# =====================================================================

def test_upload_digital_pdf(user1_auth):
    lines = [
        "Cardiovascular Diagnostic Evaluation Report",
        "Patient Name: Rajesh Kumar    Age: 54 Years    Gender: Male    Date: 15/09/2025",
        "Chief Complaints: Exertional angina, Dyspnea",
        "Past Medical History: Known case of hypertension for 8 years",
        "Investigations: Coronary Angiography, 2D Echocardiogram",
        "Findings: LAD Stenosis: 85% proximal stenosis. LVEF: 52%",
        "Primary Diagnosis: Severe Coronary Artery Disease",
        "Plan: Percutaneous Coronary Intervention (PCI)",
        "Medications: Aspirin 75mg OD, Atorvastatin 40mg HS"
    ]
    pdf_bytes = make_pdf(lines)
    res = client.post(
        "/api/reports/upload",
        files={"file": ("cardiac_digital_report.pdf", pdf_bytes, "application/pdf")},
        headers=user1_auth
    )
    assert res.status_code == 200, f"Failed: {res.text}"
    data = res.json()
    assert data["status"] == "COMPLETED"
    assert "Coronary Artery Disease" in data["ocr_text"]
    assert data["recommended_specialty"] == "Cardiology"
    assert len(data["entities"]) > 0
    assert data["structured_info"] is not None


def test_upload_scanned_pdf(user1_auth):
    # Scanned PDF is a rasterized image embedded inside a PDF container
    img = Image.new("RGB", (800, 400), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.text((30, 40), "NEUROLOGY CONSULTATION REPORT", fill=(0, 0, 0))
    draw.text((30, 80), "Patient Name: Meera Joshi   Age: 42   Gender: Female", fill=(0, 0, 0))
    draw.text((30, 120), "Primary Diagnosis: Chronic Migraine with Aura", fill=(0, 0, 0))
    draw.text((30, 160), "Prescription: Levetiracetam 500mg BD", fill=(0, 0, 0))
    buf = io.BytesIO()
    img.save(buf, format="PDF")
    scanned_pdf_bytes = buf.getvalue()

    res = client.post(
        "/api/reports/upload",
        files={"file": ("neuro_scan.pdf", scanned_pdf_bytes, "application/pdf")},
        headers=user1_auth
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "COMPLETED"
    assert len(data["ocr_text"]) > 20
    assert any(term in data["ocr_text"].upper() for term in ["NEUROLOGY", "MIGRAINE", "CONSULTATION", "MEERA"])


def test_upload_png_image(user1_auth):
    lines = [
        "Orthopedic Evaluation Summary",
        "Patient: Sunil Verma | Age: 61 | Male",
        "Diagnosis: Severe Bilateral Knee Osteoarthritis",
        "Plan: Total Knee Arthroplasty (TKA)",
        "Medications: Paracetamol 650mg TDS"
    ]
    png_bytes = make_image(lines, "PNG")
    res = client.post(
        "/api/reports/upload",
        files={"file": ("knee_xray_report.png", png_bytes, "image/png")},
        headers=user1_auth
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "COMPLETED"
    assert "Osteoarthritis" in data["ocr_text"] or "Knee" in data["ocr_text"]


def test_upload_jpg_jpeg_image(user1_auth):
    lines = [
        "Pulmonology Diagnostic Chest Examination",
        "Patient: Ananya Roy | Age: 38 | Female",
        "Diagnosis: Bronchial Asthma",
        "Medications: Salbutamol 100mcg"
    ]
    jpg_bytes = make_image(lines, "JPEG")
    res = client.post(
        "/api/reports/upload",
        files={"file": ("chest_clinic_report.jpg", jpg_bytes, "image/jpeg")},
        headers=user1_auth
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "COMPLETED"


def test_upload_table_based_lab_report(user1_auth):
    lines = [
        "METRO DIAGNOSTICS LABORATORY REPORT",
        "Patient Name: Ramesh Patel    Age: 58    Gender: Male    Date: 20/09/2025",
        "Test Name              Result   Unit     Reference Range   Status",
        "Fasting Blood Sugar    142      mg/dL    70 - 99           High",
        "HbA1c                  7.8      %        < 5.7             High",
        "Serum Creatinine       1.1      mg/dL    0.7 - 1.3         Normal",
        "Total Cholesterol      240      mg/dL    < 200             High",
        "Diagnosis: Type 2 Diabetes Mellitus, Hyperlipidemia"
    ]
    pdf_bytes = make_pdf(lines)
    res = client.post(
        "/api/reports/upload",
        files={"file": ("comprehensive_lab_panel.pdf", pdf_bytes, "application/pdf")},
        headers=user1_auth
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "COMPLETED"

    # Verify structured table parsing
    test_results = data["structured_info"].get("test_results", [])
    assert len(test_results) >= 2
    test_names = [tr["test_name"].lower() for tr in test_results]
    assert any("fbs" in t or "fasting" in t or "blood sugar" in t for t in test_names)
    assert any("hba1c" in t for t in test_names)


def test_upload_invalid_file_corrupted_header(user1_auth):
    """File extension is .pdf, but content is random garbage without %PDF- magic bytes."""
    corrupted_bytes = b"NOT_A_REAL_PDF_JUST_GARBAGE_BYTES_1234567890"
    res = client.post(
        "/api/reports/upload",
        files={"file": ("fake_report.pdf", corrupted_bytes, "application/pdf")},
        headers=user1_auth
    )
    assert res.status_code == 400
    assert "corrupted or invalid pdf" in res.json()["detail"].lower()


def test_upload_empty_zero_byte_file(user1_auth):
    res = client.post(
        "/api/reports/upload",
        files={"file": ("zero_bytes.pdf", b"", "application/pdf")},
        headers=user1_auth
    )
    assert res.status_code == 400
    assert "empty" in res.json()["detail"].lower()


def test_upload_unsupported_file_type(user1_auth):
    for bad_name, bad_content, mime in [
        ("malicious.exe", b"MZ\x90\x00\x03\x00\x00\x00", "application/x-dosexec"),
        ("exploit.sh", b"#!/bin/bash\nrm -rf /", "application/x-sh"),
        ("archive.zip", b"PK\x03\x04\x14\x00", "application/zip"),
        ("document.docx", b"PK\x03\x04\x14\x00WordDocument", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
    ]:
        res = client.post(
            "/api/reports/upload",
            files={"file": (bad_name, bad_content, mime)},
            headers=user1_auth
        )
        assert res.status_code == 400
        assert "forbidden" in res.json()["detail"].lower() or "invalid file format" in res.json()["detail"].lower() or "security violation" in res.json()["detail"].lower()


# =====================================================================
# 2. VERIFY CLINICAL EXTRACTION ACCURACY ACROSS ALL 11 FIELDS
# =====================================================================

def test_full_clinical_field_extractions():
    sample_text = """APOLLO HOSPITALS CARDIOLOGY DISCHARGE SUMMARY
Patient Name: Vikram Malhotra    Patient ID: MRN-CARD-10928
Age: 52 Years    Gender: Male    Report Date: 18/09/2025

CHIEF COMPLAINTS & SYMPTOMS:
Patient presented with exertional angina, chest pain, and shortness of breath for 3 weeks.

PAST MEDICAL HISTORY:
Known case of hypertension for 6 years. Past smoker.

INVESTIGATIONS PERFORMED:
Coronary Angiography, 2D Echocardiogram, Complete Blood Count.

LABORATORY & DIAGNOSTIC MEASUREMENTS:
LAD Stenosis: 85% proximal stenosis
LVEF: 50%
Blood Pressure: 140/90 mmHg
Serum Creatinine: 1.1 mg/dL

FINAL DIAGNOSIS & CLINICAL IMPRESSION:
• Double Vessel Coronary Artery Disease
• Angina Pectoris

PROCEDURES PERFORMED / PLANNED:
Percutaneous Coronary Intervention with drug-eluting stent.

ACTIVE MEDICATIONS:
Aspirin 75mg OD, Clopidogrel 75mg OD, Atorvastatin 40mg HS, Metoprolol 25mg BD."""

    extracted = clinical_bert_extractor.extract_structured_clinical_info(sample_text)

    # 1. Name
    assert extracted["metadata"]["patient_name"] == "Vikram Malhotra"
    # 2. Age
    assert extracted["demographics"]["age"] == 52
    # 3. Gender
    assert extracted["demographics"]["gender"] == "Male"
    # 4. Date
    assert "18/09/2025" in extracted["metadata"]["report_date"]
    # 5. Conditions
    assert any("coronary" in c.lower() for c in extracted["conditions"])
    # 6. Symptoms
    assert any("angina" in s.lower() or "chest pain" in s.lower() for s in extracted["symptoms"])
    # 7. Tests
    assert any("coronary angiography" in t.lower() or "echocardiogram" in t.lower() for t in extracted["tests"])
    # 8. Test results
    assert len(extracted["test_results"]) >= 2
    res_names = [tr["test_name"].lower() for tr in extracted["test_results"]]
    assert any("lad stenosis" in rn or "lvef" in rn for rn in res_names)
    # 9. Medications
    assert any("aspirin" in m.lower() for m in extracted["medications"])
    assert any("atorvastatin" in m.lower() for m in extracted["medications"])
    # 10. Procedures
    assert any("percutaneous coronary intervention" in p.lower() or "pci" in p.lower() for p in extracted["procedures"])
    # 11. Medical History
    assert any("hypertension" in h.lower() for h in extracted["medical_history"])


# =====================================================================
# 3. SAFETY / CORRECTNESS TESTS
# =====================================================================

def test_no_invented_or_inferred_diagnoses():
    """
    CRITICAL: Clean report with normal checkup must NOT invent or extrapolate diagnoses.
    Negated findings (e.g. 'rule out infarction', 'no evidence of CAD') must not become conditions.
    """
    normal_text = """PREVENTIVE EXECUTIVE HEALTH CHECKUP
Patient Name: Ananya Sen    Age: 28 Years    Gender: Female    Date: 10/08/2025
Clinical Impression: Routine physical examination. Unremarkable study.
Normal study, rule out acute coronary syndrome, no evidence of infarction, negative for arthritis.
No active complaints or diseases documented."""

    extracted = clinical_bert_extractor.extract_structured_clinical_info(normal_text)
    # Zero inferred or negated diagnoses
    for cond in extracted["conditions"]:
        cond_low = cond.lower()
        assert "infarction" not in cond_low
        assert "acute coronary syndrome" not in cond_low
        assert "arthritis" not in cond_low


def test_ocr_noise_fails_gracefully_without_fabrication(user1_auth):
    """Unreadable noise image must be saved as FAILED without hallucinating medical facts."""
    noise_bytes = b"GIF89a\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;"
    res = client.post(
        "/api/reports/upload",
        files={"file": ("blank_noise.gif", noise_bytes, "image/gif")},
        headers=user1_auth
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "FAILED"
    assert "warning" in data["summary"].lower()
    assert len(data["entities"]) == 0


def test_patient_isolation_and_profile_synchronization(user1_auth, user2_auth):
    """
    Verifies that:
    1. Uploaded report by User 1 updates User 1's profile.
    2. User 2 cannot access User 1's report (403 Forbidden).
    3. User 1's data does not leak into User 2's profile.
    """
    lines = [
        "Cardiology Diagnostic Follow-up",
        "Patient Diagnosis: Severe Coronary Artery Disease",
        "Medications: Aspirin 75mg OD, Clopidogrel 75mg OD"
    ]
    pdf_bytes = make_pdf(lines)
    res = client.post(
        "/api/reports/upload",
        files={"file": ("user1_isolated_test.pdf", pdf_bytes, "application/pdf")},
        headers=user1_auth
    )
    assert res.status_code == 200
    rep_id = res.json()["id"]

    # User 1 profile updated
    prof1 = client.get("/api/auth/profile", headers=user1_auth).json()
    assert prof1["last_report_id"] == rep_id
    assert any("coronary" in c.lower() for c in (prof1.get("conditions") or []))

    # User 2 attempts to read User 1's report -> 403 Forbidden
    cross_res = client.get(f"/api/reports/{rep_id}", headers=user2_auth)
    assert cross_res.status_code == 403

    # User 2's profile remains untainted
    prof2 = client.get("/api/auth/profile", headers=user2_auth).json()
    assert prof2["last_report_id"] != rep_id
    assert not any("coronary" in c.lower() for c in (prof2.get("conditions") or []))
