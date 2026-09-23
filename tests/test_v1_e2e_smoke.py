"""
V1 Core End-to-End Smoke Test
Validates the complete unbroken decision support pipeline:
Upload → OCR/NER → Profile → RAG → Recommendations → Cost/LOS → Assistant
"""

import os
import sys
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
from models import MedicalReport, PatientProfile
from security import create_access_token

client = TestClient(app)


def build_sample_pdf(text_lines):
    """Builds a valid standalone PDF containing clinical text."""
    stream_content = "BT /F1 12 Tf 72 700 Td "
    for line in text_lines:
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


def test_v1_core_end_to_end_pipeline():
    """
    Executes the unbroken single-user/demo session V1 core pipeline:
    1. Upload: POST medical report PDF to /api/reports/upload
    2. OCR / NER: Verify OCR text and ClinicalBERT entities (Disease, Medication, Procedure)
    3. Profile: GET and PUT /api/auth/profile
    4. RAG: Verify RAG grounding notes & sources in report analysis
    5. Recommendations: GET /api/recommend/hospitals & /api/recommend/doctors
    6. Cost / LOS: POST /api/cost/predict & /api/cost/explain with SHAP
    7. Assistant: POST /api/services/chat with conversation continuity
    """
    token = create_access_token({"sub": "1", "email": "rahul.verma@example.com"})
    client.headers = {"Authorization": f"Bearer {token}"}
    # -------------------------------------------------------------
    # Step 1: Upload Medical Report (PDF)
    # -------------------------------------------------------------
    clinical_text = [
        "Patient Diagnosis: Severe Coronary Artery Disease with exertional angina.",
        "Coronary Angiography reveals LAD 85% proximal stenosis, RCA 70% lesion.",
        "Left ventricular ejection fraction (LVEF) is 52%.",
        "Advised: Percutaneous Coronary Intervention with Drug-Eluting Stents.",
        "Current Medications: Aspirin 75mg daily, Atorvastatin 40mg, Metoprolol 25mg."
    ]
    pdf_bytes = build_sample_pdf(clinical_text)

    upload_res = client.post(
        "/api/reports/upload",
        files={"file": ("angiography_cardio_report.pdf", pdf_bytes, "application/pdf")}
    )
    assert upload_res.status_code == 200, f"Upload failed: {upload_res.text}"
    report_data = upload_res.json()
    report_id = report_data["id"]
    assert report_id is not None
    assert report_data["status"] == "COMPLETED"

    # -------------------------------------------------------------
    # Step 2: OCR & Clinical NER Verification
    # -------------------------------------------------------------
    assert report_data["ocr_text"] is not None
    assert len(report_data["ocr_text"]) > 20
    assert report_data["recommended_specialty"] == "Cardiology"

    entities = report_data["entities"]
    assert len(entities) >= 2, "ClinicalBERT failed to extract entities"
    entity_types = {e["entity_type"] for e in entities}
    assert "Disease" in entity_types or "Procedure" in entity_types or "Medication" in entity_types

    # -------------------------------------------------------------
    # Step 3: Clinical Profile (auth.py profile endpoints)
    # -------------------------------------------------------------
    profile_get = client.get("/api/auth/profile")
    assert profile_get.status_code == 200
    current_prof = profile_get.json()
    assert current_prof["current_city"] is not None

    profile_put = client.put(
        "/api/auth/profile",
        json={
            "age": 52,
            "gender": "Male",
            "blood_group": "B+",
            "current_city": "Hyderabad",
            "allergies": "Penicillin",
            "chronic_conditions": "Hypertension, Coronary Artery Disease"
        }
    )
    assert profile_put.status_code == 200
    updated_prof = profile_put.json()
    assert updated_prof["age"] == 52
    assert "Coronary" in updated_prof["chronic_conditions"]

    # -------------------------------------------------------------
    # Step 4: Semantic RAG Grounding & Citations
    # -------------------------------------------------------------
    report_detail = client.get(f"/api/reports/{report_id}")
    assert report_detail.status_code == 200
    det = report_detail.json()
    assert det["grounding_notes"] is not None
    assert isinstance(det["grounding_sources"], list)
    assert len(det["grounding_sources"]) > 0
    first_source = det["grounding_sources"][0]
    assert "title" in first_source and "organization" in first_source

    # -------------------------------------------------------------
    # Step 5: Hospital, Doctor & Treatment Recommendations
    # -------------------------------------------------------------
    hosp_res = client.get(
        f"/api/recommend/hospitals?specialty={report_data['recommended_specialty']}&city=Hyderabad&report_id={report_id}"
    )
    assert hosp_res.status_code == 200
    hospitals = hosp_res.json()
    assert len(hospitals) > 0
    top_hospital = hospitals[0]
    assert top_hospital["recommendation_score"] is not None
    assert "Cardiology" in top_hospital["specialties"]

    doc_res = client.get(
        f"/api/recommend/doctors?specialty=Cardiology&hospital_id={top_hospital['id']}"
    )
    assert doc_res.status_code == 200
    doctors = doc_res.json()
    assert len(doctors) > 0
    assert doctors[0]["specialty"] == "Cardiology"

    # -------------------------------------------------------------
    # Step 6: Cost + LOS Prediction & SHAP Explainability
    # -------------------------------------------------------------
    cost_res = client.post(
        "/api/cost/predict",
        json={
            "treatment_name": "Coronary Angioplasty",
            "city": "Hyderabad",
            "room_type": "Single Deluxe",
            "report_id": report_id,
            "hospital_id": top_hospital["id"],
            "age": 52,
            "has_cardiac_history": True,
            "has_hypertension": True
        }
    )
    assert cost_res.status_code == 200
    cost_data = cost_res.json()
    assert cost_data["estimated_avg_cost"] > 0
    assert cost_data["predicted_los_days"] is not None
    assert cost_data["predicted_los_days"] > 0
    assert len(cost_data["shap_feature_impacts"]) > 0

    explain_res = client.post(
        "/api/cost/explain",
        json={
            "treatment_name": "Coronary Angioplasty",
            "city": "Hyderabad",
            "room_type": "Single Deluxe",
            "report_id": report_id,
            "hospital_id": top_hospital["id"],
            "age": 52
        }
    )
    assert explain_res.status_code == 200
    explain_data = explain_res.json()
    assert explain_data["shap_explanation"]["additive_property_verified"] is True
    assert len(explain_data["shap_explanation"]["breakdown"]) > 0

    # -------------------------------------------------------------
    # Step 7: Contextual AI Healthcare Assistant
    # -------------------------------------------------------------
    chat_res = client.post(
        "/api/services/chat",
        json={
            "message": "What clinical guidelines apply to my stent procedure and recovery?",
            "report_id": report_id,
            "hospital_id": top_hospital["id"]
        }
    )
    assert chat_res.status_code == 200
    chat_data = chat_res.json()
    assert chat_data["reply"] is not None
    assert chat_data["conversation_id"] is not None
    assert chat_data["grounding_status"] == "GROUNDED"
    assert len(chat_data["citations"]) > 0
    assert chat_data["disclaimer"] is not None

    # Multi-turn continuity check
    chat_turn2 = client.post(
        "/api/services/chat",
        json={
            "conversation_id": chat_data["conversation_id"],
            "message": "How long will I stay in the hospital?",
            "report_id": report_id
        }
    )
    assert chat_turn2.status_code == 200
    turn2_data = chat_turn2.json()
    assert turn2_data["conversation_id"] == chat_data["conversation_id"]

    # History retrieval
    hist_res = client.get(f"/api/services/chat/history?conversation_id={chat_data['conversation_id']}")
    assert hist_res.status_code == 200
    hist = hist_res.json()
    assert len(hist["messages"]) >= 4
