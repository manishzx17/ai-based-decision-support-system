import sys
import os
import io
import pytest
from PIL import Image, ImageDraw

# Add project root and backend to sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND_DIR = os.path.join(BASE_DIR, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from ai.ocr_engine import ocr_engine
from ai.clinical_bert import clinical_bert_extractor


def create_sample_text_pdf(text_lines):
    """Creates a genuine, valid PDF containing specific text lines."""
    import pypdf
    # Build valid PDF using standard PDF syntax
    stream_content = "BT /F1 12 Tf 72 700 Td "
    for line in text_lines:
        safe_line = line.replace("(", "").replace(")", "")
        stream_content += f"({safe_line}) Tj 0 -18 Td "
    stream_content += "ET"

    pdf_bytes = f"""%PDF-1.4
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
    return pdf_bytes


def create_scanned_image_pdf(text_str):
    """Creates a scanned PDF containing a rasterized image with text."""
    img = Image.new("RGB", (600, 300), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.text((20, 50), text_str, fill=(0, 0, 0))
    buf = io.BytesIO()
    img.save(buf, format="PDF")
    return buf.getvalue()


def test_text_pdf_extraction():
    """Verifies that text-based PDFs are extracted natively from PDF streams."""
    lines = [
        "Patient: Vikram Sharma | Age: 45",
        "Clinical Observation: Chronic chest discomfort and dyspnea",
        "Impression: Coronary Artery Disease with 85% stenosis",
        "Plan: Coronary Angiography and Aspirin 75mg"
    ]
    pdf_bytes = create_sample_text_pdf(lines)
    extracted = ocr_engine.extract_text(pdf_bytes, "Vikram_Report.pdf")

    assert "Vikram Sharma" in extracted
    assert "Coronary Artery Disease" in extracted
    assert "85% stenosis" in extracted


def test_scanned_pdf_extraction():
    """Verifies that raster/scanned PDFs without digital text are OCR parsed via pypdfium2."""
    doc_text = "DIAGNOSTIC TEST REPORT\nPatient: Neha Gupta\nCondition: Acute Appendicitis"
    pdf_bytes = create_scanned_image_pdf(doc_text)

    extracted = ocr_engine.extract_text(pdf_bytes, "scanned_doc.pdf")
    assert isinstance(extracted, str)
    assert len(extracted) > 10
    # Should find at least parts of the text
    assert any(w in extracted.upper() for w in ["DIAGNOSTIC", "REPORT", "PATIENT", "NEHA", "APPENDICITIS"])


def test_real_image_ocr():
    """Verifies genuine OCR on the existing hospital scanned image (1.webp)."""
    webp_path = os.path.join(BACKEND_DIR, "uploads", "1.webp")
    assert os.path.exists(webp_path), "1.webp sample file must exist"

    with open(webp_path, "rb") as f:
        img_bytes = f.read()

    extracted = ocr_engine.extract_text(img_bytes, "1.webp")
    assert len(extracted) > 50

    # Must contain actual text from the real scanned ticket, NOT cardiology mock data!
    assert "Rajesh Verma" not in extracted
    assert any(term in extracted.upper() for term in ["JAGNYASENI", "HOSPITAL", "TICKET", "PATEL", "JHARSUGUDA"])


def test_ocr_text_validation():
    """Verifies validation detects empty, too short, or noise-heavy text."""
    # Empty text
    is_valid, msg = ocr_engine.validate_extracted_text("")
    assert not is_valid
    assert "blank" in msg.lower() or "no readable" in msg.lower()

    # Gibberish / noise text
    is_valid, msg = ocr_engine.validate_extracted_text("!@#$%^&*()_+=~`{}[]|:;'<>?,./")
    assert not is_valid

    # Too short
    is_valid, msg = ocr_engine.validate_extracted_text("Hi there")
    assert not is_valid

    # Genuine clinical text
    valid_text = "PATIENT CONSULTATION REPORT\nPatient Name: Anitha Rao | Age: 52\nImpression: Benign Meningioma"
    is_valid, msg = ocr_engine.validate_extracted_text(valid_text)
    assert is_valid


def test_content_driven_not_filename_driven():
    """
    CRITICAL: Verifies that entity extraction is driven purely by content,
    and NOT by filename tricks!
    """
    cardio_text = """CARDIOLOGY ASSESSMENT
Patient has exertional angina and severe Double Vessel Coronary Artery Disease.
Diagnostic Angiography reveals LAD 85% proximal stenosis and RCA 70% stenosis.
Advised elective Percutaneous Coronary Intervention (PCI).
Prescribed Aspirin 75mg OD and Atorvastatin 40mg HS."""

    # Even if the filename is 'Neurology_Scan.pdf', the content is Cardiology!
    entities = clinical_bert_extractor.extract_entities(cardio_text)
    specialty = clinical_bert_extractor.predict_recommended_specialty(cardio_text, entities)

    assert specialty == "Cardiology", f"Expected Cardiology but got {specialty}"
    names = [e["entity_name"].lower() for e in entities]
    assert any("coronary" in n or "angina" in n or "double vessel" in n for n in names)
    assert not any("meningioma" in n for n in names)


def test_structured_entity_types():
    """Verifies extraction of structured entities across multiple clinical classes."""
    text = """DIAGNOSTIC WORKUP & DISCHARGE SUMMARY
Patient: Ramesh K | Age: 58 | Sex: Male
Presenting complaint: Severe knee pain, joint stiffness, and antalgic gait for 3 years.
Physical Exam: Marked tenderness over medial compartment.
History: Known case of Hypertension for 5 years.
Investigations:
1. X-Ray Right Knee: Grade IV Osteoarthritis.
2. Blood Pressure: 130/85 mmHg.
3. Serum Creatinine: 1.1 mg/dL.
4. LVEF: 60%.
Plan: Elective Right Total Knee Arthroplasty (TKA).
Medications: Paracetamol 650mg TDS, Pantoprazole 40mg OD, Amlodipine 5mg OD."""

    entities = clinical_bert_extractor.extract_entities(text)
    types = {e["entity_type"] for e in entities}

    # Verify multiple entity classes extracted
    assert "Disease" in types
    assert "Symptom" in types
    assert "Procedure" in types
    assert "Medication" in types
    assert "TestResult" in types

    # Check that context snippets are actual lines from text
    for ent in entities:
        assert ent["context_snippet"] is not None
        assert len(ent["context_snippet"]) > 0


def test_upload_endpoint_integration():
    """Verifies FastAPI reports upload endpoint with image, validation, and zero fabrication on noise."""
    from fastapi.testclient import TestClient
    from main import app
    from init_db import init_db
    init_db()

    with TestClient(app) as client:
        # Authenticate User 1
        login_res = client.post("/api/auth/login", json={"username": "demo_cardio", "password": "DemoPassword@123"})
        assert login_res.status_code == 200
        headers = {"Authorization": f"Bearer {login_res.json()['access_token']}"}

        # 1. Genuine image upload
        webp_path = os.path.join(BACKEND_DIR, "uploads", "1.webp")
        if os.path.exists(webp_path):
            with open(webp_path, "rb") as f:
                files = {"file": ("1.webp", f.read(), "image/webp")}
            resp = client.post("/api/reports/upload", files=files, headers=headers)
            assert resp.status_code == 200
            data = resp.json()
            assert data["status"] == "COMPLETED"
            assert data["id"] is not None
            assert len(data["ocr_text"]) > 50
            # Structured info must be present in response
            assert "structured_info" in data
            if data["structured_info"]:
                assert "metadata" in data["structured_info"]
                assert "demographics" in data["structured_info"]
                assert "conditions" in data["structured_info"]
                assert "test_results" in data["structured_info"]

        # 2. Empty file rejected with 400
        resp_empty = client.post("/api/reports/upload", files={"file": ("empty.pdf", b"", "application/pdf")}, headers=headers)
        assert resp_empty.status_code == 400

        # 3. Unreadable noise image saved as FAILED without fabricated medical data
        noise_bytes = b"GIF89a\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;"
        resp_noise = client.post("/api/reports/upload", files={"file": ("noise.gif", noise_bytes, "image/gif")}, headers=headers)
        assert resp_noise.status_code == 200
        noise_data = resp_noise.json()
        assert noise_data["status"] == "FAILED"
        assert len(noise_data["entities"]) == 0


def test_structured_clinical_info_schema_and_constraints():
    """
    Verifies Phase 2 architectural constraints:
    1. recommended_specialty is excluded from StructuredClinicalInfo (belongs to Phase 5).
    2. Zero inferred diagnoses: extracts only explicitly reported conditions.
    3. Patient name, patient ID/MRN, and report date are treated as metadata/identifiers.
    4. All 8 clinical categories are structured.
    """
    report_text = """METRO HEALTHCARE CLINICAL DIAGNOSTIC REPORT
[SYNTHETIC BENCHMARK EVALUATION DATASET — NOT REAL CLINICAL DATA]
Patient Name: Anil Kumar    Patient ID: MRN-CRD-9988
Age: 56 Years    Gender: Male    Report Date: 12/08/2025

CHIEF COMPLAINTS & SYMPTOMS:
Patient presented with complaints of exertional angina, chest pain, and shortness of breath.

PAST MEDICAL HISTORY:
Known case of hypertension for 7 years. Past smoker.

DIAGNOSTIC INVESTIGATIONS PERFORMED:
Investigations: Coronary Angiography, 2D Echocardiogram, Electrocardiogram.

LABORATORY & DIAGNOSTIC MEASUREMENTS:
LAD Stenosis: 85% proximal stenosis
LVEF: 50%
Blood Pressure: 145/92 mmHg
Serum Creatinine: 1.2 mg/dL

FINAL DIAGNOSIS & CLINICAL IMPRESSION:
• Double Vessel Coronary Artery Disease
• Angina Pectoris

PROCEDURES PERFORMED / RECOMMENDED:
Coronary Angiography, Percutaneous Coronary Intervention.

ACTIVE MEDICATIONS:
Rx: Aspirin 75mg OD, Atorvastatin 40mg HS, Metoprolol 25mg BD."""

    structured = clinical_bert_extractor.extract_structured_clinical_info(report_text)

    # 1. Constraint: No recommended_specialty in structured clinical info
    assert "recommended_specialty" not in structured, "recommended_specialty must NOT be present in StructuredClinicalInfo (Phase 5)"

    # 2. Constraint: Document Metadata separated as identifiers
    meta = structured.get("metadata", {})
    assert meta.get("patient_name") == "Anil Kumar"
    assert meta.get("patient_id") == "MRN-CRD-9988"
    assert meta.get("report_date") == "12/08/2025"

    # 3. Demographics
    demo = structured.get("demographics", {})
    assert demo.get("age") == 56
    assert demo.get("gender") == "Male"

    # 4. Explicit conditions only (no inferred diagnoses)
    conds = structured.get("conditions", [])
    assert any("Coronary Artery Disease" in c for c in conds)
    assert not any("Meningioma" in c or "Osteoarthritis" in c for c in conds)

    # 5. Symptoms
    syms = structured.get("symptoms", [])
    assert any("chest pain" in s.lower() or "angina" in s.lower() for s in syms)

    # 6. Tests
    tests = structured.get("tests", [])
    assert any("Angiography" in t or "Echocardiogram" in t for t in tests)

    # 7. Structured Test Results (Values, Units, Reference Range, Status)
    test_results = structured.get("test_results", [])
    assert len(test_results) >= 2
    tr_names = [tr["test_name"] for tr in test_results]
    assert any("LVEF" in n or "Stenosis" in n or "Blood Pressure" in n for n in tr_names)
    for tr in test_results:
        assert "value" in tr and len(tr["value"]) > 0
        assert "unit" in tr

    # 8. Medications with dosage & frequency
    meds = structured.get("medications", [])
    assert any("Aspirin" in m for m in meds)
    assert any("Atorvastatin" in m for m in meds)

    # 9. Procedures
    procs = structured.get("procedures", [])
    assert any("Coronary Angiography" in p or "Percutaneous Coronary Intervention" in p for p in procs)

    # 10. Medical History
    history = structured.get("medical_history", [])
    assert any("hypertension" in h.lower() or "smoker" in h.lower() for h in history)


def test_synthetic_benchmark_dataset_structure():
    """Verifies that the 30 synthetic benchmark reports and validated ground_truth.json exist."""
    dataset_dir = os.path.join(BACKEND_DIR, "datasets", "medical_reports")
    reports_dir = os.path.join(dataset_dir, "reports")
    gt_path = os.path.join(dataset_dir, "ground_truth.json")

    assert os.path.exists(dataset_dir), "medical_reports dataset directory must exist"
    assert os.path.exists(reports_dir), "medical_reports/reports directory must exist"
    assert os.path.exists(gt_path), "ground_truth.json must exist"

    with open(gt_path, "r") as f:
        import json
        ground_truth = json.load(f)

    assert len(ground_truth) == 30, "Must contain exactly 30 benchmark reports"

    # Check format variations
    formats = {item["format"] for item in ground_truth}
    assert "digital_pdf" in formats
    assert "scanned_pdf" in formats
    assert "image_png" in formats

    # Check specialty variation across 8 specialties
    specialties = {item["specialty_domain"] for item in ground_truth}
    assert len(specialties) >= 7
    assert "Cardiology" in specialties
    assert "Neurology" in specialties
    assert "Orthopedics" in specialties
    assert "Oncology" in specialties

    # Verify each ground-truth file physically exists on disk
    for item in ground_truth:
        file_path = os.path.join(reports_dir, item["filename"])
        assert os.path.exists(file_path), f"Report file {item['filename']} must exist on disk"
        assert os.path.getsize(file_path) > 500, f"Report file {item['filename']} must not be empty"


if __name__ == "__main__":
    pytest.main(["-v", __file__])

