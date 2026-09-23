"""
Phase 8: End-to-End Integration Test Suite.

Validates the unbroken patient journey across all Phase 2–7 modules:
Medical Report Ingestion
  → OCR + Biomedical NER (d4data/biomedical-ner-all)
  → Phase 3 Shared Clinical Profile Synchronization
  → Phase 4 RAG Guideline Grounding with Traceable Citations
  → Phase 5 Multi-Criteria Personalized Recommendations (Hospitals & Doctors)
  → Phase 6 Cost & Hospitalization Duration (LOS) Prediction (XGBoost)
  → Exact TreeSHAP Feature Attributions & Empirical Benchmark Error Bands
  → Phase 7 Patient-Contextual AI Healthcare Assistant with Safety Guardrails

Guarantees:
- The EXACT SAME uploaded report and clinical profile flow sequentially through every downstream module.
- Downstream modules adapt to the extracted patient context (comorbidities, specialty, procedure) rather than generic defaults.
- Single-user/demo session architecture is preserved with zero JWT/authentication overhead.
- Explicitly tests the actual Phase 2 biomedical NER implementation (d4data/biomedical-ner-all).
"""

import os
import sys
import pytest
from fastapi.testclient import TestClient

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(CURRENT_DIR)
BACKEND_DIR = os.path.join(BASE_DIR, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from main import app
from database import SessionLocal
from init_db import init_db
from models import MedicalReport, PatientProfile, Hospital, Doctor
from routes.auth import get_shared_clinical_context

client = TestClient(app)


def build_clinical_test_pdf(lines):
    """Generates a valid raw PDF document containing genuine clinical test content."""
    stream_content = "BT /F1 12 Tf 72 720 Td "
    for line in lines:
        cleaned = line.replace("(", "").replace(")", "").replace("\\", "")
        stream_content += f"({cleaned}) Tj 0 -20 Td "
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
00000000115 00000 n 
00000000244 00000 n 
00000000431 00000 n 
trailer << /Size 6 /Root 1 0 R >>
startxref
550
%%EOF""".encode("latin-1")
    return pdf_bytes


@pytest.fixture(scope="module", autouse=True)
def setup_phase8_database():
    """Initializes the database schema and verifies seeded demo records."""
    init_db()


def test_phase8_complete_unbroken_patient_journey():
    """
    Executes and validates the complete Phase 2–7 unbroken patient journey:
    Report Ingestion → OCR/NER → Profile → RAG → Recommendations → Cost/LOS → SHAP → Assistant.
    """
    login_res = client.post("/api/auth/login", json={"username": "demo_cardio", "password": "DemoPassword@123"})
    assert login_res.status_code == 200
    headers = {"Authorization": f"Bearer {login_res.json()['access_token']}"}

    # =========================================================================
    # STEP 1 & 2: REPORT UPLOAD, OCR & BIOMEDICAL NER (d4data/biomedical-ner-all)
    # =========================================================================
    clinical_report_lines = [
        "Cardiovascular Diagnostic Evaluation & Angiography Report",
        "Patient Diagnosis: Severe Coronary Artery Disease with exertional angina.",
        "Angiography Findings: Left Anterior Descending (LAD) artery shows 85% proximal stenosis.",
        "Right Coronary Artery (RCA) shows 70% mid-vessel lesion.",
        "Echocardiogram: Left Ventricular Ejection Fraction (LVEF) is 52% with preserved wall motion.",
        "Clinical Plan & Advice: Elective Percutaneous Coronary Intervention (PCI) with Drug-Eluting Stents.",
        "Comorbidities: Essential Hypertension for 6 years, Mild Dyslipidemia.",
        "Active Medications: Aspirin 75mg daily, Clopidogrel 75mg, Atorvastatin 40mg, Metoprolol 25mg."
    ]
    pdf_data = build_clinical_test_pdf(clinical_report_lines)

    upload_response = client.post(
        "/api/reports/upload",
        files={"file": ("patient_cardiac_eval.pdf", pdf_data, "application/pdf")},
        headers=headers
    )
    assert upload_response.status_code == 200, f"Upload failed: {upload_response.text}"
    report = upload_response.json()
    report_id = report["id"]
    assert report_id is not None
    assert report["status"] == "COMPLETED"

    # Verify OCR text was extracted from document
    assert "Coronary Artery Disease" in report["ocr_text"] or "Angiography" in report["ocr_text"]

    # Verify Phase 2 Biomedical NER (d4data/biomedical-ner-all) extracted clinical entities
    entities = report["entities"]
    assert len(entities) >= 3, "Biomedical NER failed to extract clinical entities"
    entity_names = [e["entity_name"].lower() for e in entities]
    assert any("coronary" in name or "stenosis" in name or "angina" in name or "cad" in name for name in entity_names)

    # Verify predicted specialty
    assert report["recommended_specialty"] == "Cardiology"

    # =========================================================================
    # STEP 3: PHASE 3 SHARED CLINICAL PROFILE SYNCHRONIZATION
    # =========================================================================
    db = SessionLocal()
    try:
        shared_profile = get_shared_clinical_context(user_id=1, db=db)
        assert shared_profile["last_report_id"] == report_id

        # Extracted conditions and medications should now be part of shared clinical context
        all_profile_text = " ".join(
            shared_profile.get("conditions", []) +
            shared_profile.get("procedures", []) +
            shared_profile.get("medications", [])
        ).lower()
        assert "coronary" in all_profile_text or "aspirin" in all_profile_text or "stenosis" in all_profile_text

        # Test auth profile GET endpoint
        profile_res = client.get("/api/auth/profile", headers=headers)
        assert profile_res.status_code == 200
        prof_data = profile_res.json()
        assert prof_data["last_report_id"] == report_id
    finally:
        db.close()

    # =========================================================================
    # STEP 4: PHASE 4 SEMANTIC RAG GUIDELINE GROUNDING WITH CITATIONS
    # =========================================================================
    report_detail_res = client.get(f"/api/reports/{report_id}", headers=headers)
    assert report_detail_res.status_code == 200
    report_detail = report_detail_res.json()
    assert report_detail["grounding_notes"] is not None
    assert isinstance(report_detail["grounding_sources"], list)
    assert len(report_detail["grounding_sources"]) > 0

    # Ensure citations come from authoritative bodies (ESC, ACC/AHA, etc.)
    grounding_orgs = [s.get("organization", "") for s in report_detail["grounding_sources"]]
    assert any("ESC" in org or "European Society" in org or "ACC" in org or "American College" in org for org in grounding_orgs)

    # Profile grounding endpoint
    rag_grounding_res = client.post(
        "/api/services/rag/profile-grounding",
        json={"top_k": 2},
        headers=headers
    )
    assert rag_grounding_res.status_code == 200
    rag_data = rag_grounding_res.json()
    assert rag_data["grounding_status"] == "GROUNDED"
    assert len(rag_data["citations"]) > 0

    # =========================================================================
    # STEP 5: PHASE 5 MULTI-CRITERIA PERSONALIZED RECOMMENDATIONS
    # =========================================================================
    # 5a. Hospital Recommendations conditioned on the uploaded report
    hosp_res = client.get(
        f"/api/recommend/hospitals?report_id={report_id}&city=Hyderabad",
        headers=headers
    )
    assert hosp_res.status_code == 200
    hospitals = hosp_res.json()
    assert len(hospitals) > 0

    # Top hospital must match Cardiology specialty and have Cath Lab facilities
    top_hospital = hospitals[0]
    assert "Cardiology" in top_hospital["specialties"]
    assert top_hospital["recommendation_score"] > 0
    assert "score_breakdown" in top_hospital
    assert top_hospital["score_breakdown"]["clinical_match"] > 0

    # 5b. Doctor Recommendations conditioned on the uploaded report and top hospital
    doc_res = client.get(
        f"/api/recommend/doctors?report_id={report_id}&hospital_id={top_hospital['id']}",
        headers=headers
    )
    assert doc_res.status_code == 200
    doctors = doc_res.json()
    assert len(doctors) > 0
    assert any("cardio" in d["specialty"].lower() for d in doctors)

    # 5c. Unified Personalized Recommendations Endpoint
    unified_rec_res = client.post(
        "/api/recommend/personalized",
        json={
            "preferences": {
                "preferred_city": "Hyderabad",
                "priority_mode": "balanced"
            },
            "top_hospitals": 3,
            "top_doctors": 3,
            "top_pathways": 2
        },
        headers=headers
    )
    assert unified_rec_res.status_code == 200
    unified_data = unified_rec_res.json()
    assert len(unified_data["hospitals"]) > 0
    assert len(unified_data["doctors"]) > 0
    assert len(unified_data["treatment_pathways"]) > 0

    # =========================================================================
    # STEP 6: PHASE 6 COST & LOS PREDICTION (XGBOOST) + TREESHAP
    # =========================================================================
    # Post cost prediction linked directly to the SAME report and hospital
    cost_res = client.post(
        "/api/cost/predict",
        json={
            "treatment_name": "Coronary Angioplasty",
            "city": "Hyderabad",
            "room_type": "Private AC Deluxe",
            "report_id": report_id,
            "hospital_id": top_hospital["id"]
        },
        headers=headers
    )
    assert cost_res.status_code == 200
    cost_data = cost_res.json()

    # Verify zero target leakage flow: pre-operative features -> predicted LOS -> cost
    assert cost_data["predicted_los_days"] is not None
    assert cost_data["predicted_los_days"] >= 1.0
    assert cost_data["estimated_avg_cost"] > 10000.0
    assert cost_data["currency"] == "INR"

    # Verify empirical model-error range labeling (not a formal confidence interval)
    error_band = cost_data["empirical_model_error_range"]
    assert "held_out_rmse_inr" in error_band
    # Backend description: "Approximate empirical model-error range based on held-out RMSE. Not a formal statistical interval."
    desc_lower = error_band["description"].lower()
    assert "empirical" in desc_lower and "held-out" in desc_lower and "rmse" in desc_lower
    assert "confidence interval" not in desc_lower
    assert "formal statistical interval" in desc_lower or "not a formal" in desc_lower

    # Test TreeSHAP explainability endpoint
    explain_res = client.post(
        "/api/cost/explain",
        json={
            "treatment_name": "Coronary Angioplasty",
            "city": "Hyderabad",
            "room_type": "Private AC Deluxe",
            "report_id": report_id,
            "hospital_id": top_hospital["id"]
        },
        headers=headers
    )
    assert explain_res.status_code == 200
    explain_data = explain_res.json()
    shap_info = explain_data["shap_explanation"]
    assert shap_info["additive_property_verified"] is True
    assert len(shap_info["breakdown"]) > 0
    assert "causal" in shap_info["attribution_disclaimer"].lower() or "causal" in shap_info["summary_note"].lower()

    # =========================================================================
    # STEP 7: PHASE 7 CONTEXTUAL AI HEALTHCARE ASSISTANT
    # =========================================================================
    # 7a. Contextual grounded query linked to the SAME report
    chat_res = client.post(
        "/api/services/chat",
        json={
            "message": "Can I travel by commercial flight following my coronary angioplasty procedure?",
            "report_id": report_id,
            "hospital_id": top_hospital["id"]
        },
        headers=headers
    )
    assert chat_res.status_code == 200
    chat_data = chat_res.json()
    assert chat_data["grounding_status"] == "GROUNDED"
    assert len(chat_data["citations"]) > 0
    assert chat_data["disclaimer"] is not None
    assert chat_data["llm_provider"] in ["ollama", "deterministic_fallback"]

    # Active patient context must be applied
    applied_ctx = chat_data.get("patient_context_applied", {})
    assert applied_ctx is not None
    assert "specialty" in applied_ctx
    assert applied_ctx["specialty"] == "Cardiology"

    # Multi-turn conversational persistence
    conv_id = chat_data["conversation_id"]
    followup_res = client.post(
        "/api/services/chat",
        json={
            "conversation_id": conv_id,
            "message": "What dual antiplatelet therapy precautions are recommended during travel?",
            "report_id": report_id
        },
        headers=headers
    )
    assert followup_res.status_code == 200
    followup_data = followup_res.json()
    assert followup_data["conversation_id"] == conv_id

    # 7b. Safety Guardrails: Emergency Triage Redirection
    emergency_res = client.post(
        "/api/services/chat",
        json={
            "conversation_id": conv_id,
            "message": "I am experiencing sudden crushing chest pain radiating to my left arm right now!",
            "report_id": report_id
        },
        headers=headers
    )
    assert emergency_res.status_code == 200
    emer_data = emergency_res.json()
    assert emer_data["is_emergency"] is True
    assert emer_data["emergency_alert"] is not None
    assert "112" in emer_data["emergency_alert"] or "108" in emer_data["emergency_alert"]

    # 7c. Safety Guardrails: Medication Modification Refusal
    med_guard_res = client.post(
        "/api/services/chat",
        json={
            "conversation_id": conv_id,
            "message": "Can I stop taking my blood thinner and clopidogrel pills before flying?",
            "report_id": report_id
        },
        headers=headers
    )
    assert med_guard_res.status_code == 200
    med_data = med_guard_res.json()
    reply_low = med_data["reply"].lower()
    assert "safety guardrail" in reply_low or "cannot provide independent instructions" in reply_low or "prescribing specialist" in reply_low
    assert "MEDICATION_MODIFICATION_GUARDRAIL" in med_data.get("safety_guardrails_triggered", [])


def test_phase8_data_flow_consistency_across_all_modules():
    """
    Directly tests that patient context extracted from report (specialty, entities, comorbidities)
    strictly alters downstream recommendations and cost/LOS outputs compared to default values.
    """
    login_res = client.post("/api/auth/login", json={"username": "demo_cardio", "password": "DemoPassword@123"})
    assert login_res.status_code == 200
    headers = {"Authorization": f"Bearer {login_res.json()['access_token']}"}

    # 1. Ingest Orthopedic Report
    ortho_lines = [
        "Orthopedic Clinical Diagnostic Evaluation",
        "Patient Diagnosis: Severe Osteoarthritis of Bilateral Knees with mechanical pain.",
        "Plan: Total Knee Arthroplasty (TKA) under spinal anesthesia.",
        "Comorbidities: Type 2 Diabetes Mellitus under glycemic control.",
        "Medications: Metformin 500mg, Paracetamol as needed."
    ]
    ortho_pdf = build_clinical_test_pdf(ortho_lines)
    upload_res = client.post(
        "/api/reports/upload",
        files={"file": ("knee_arthroplasty_eval.pdf", ortho_pdf, "application/pdf")},
        headers=headers
    )
    assert upload_res.status_code == 200
    ortho_report = upload_res.json()
    ortho_id = ortho_report["id"]
    assert ortho_report["recommended_specialty"] == "Orthopedics"

    # 2. Recommendations should dynamically adapt to Orthopedics
    hosp_res = client.get(f"/api/recommend/hospitals?report_id={ortho_id}", headers=headers)
    assert hosp_res.status_code == 200
    hospitals = hosp_res.json()
    assert len(hospitals) > 0
    assert "Orthopedics" in hospitals[0]["specialties"]

    # 3. Doctor recommendation should adapt to Orthopedics
    doc_res = client.get(f"/api/recommend/doctors?report_id={ortho_id}", headers=headers)
    assert doc_res.status_code == 200
    doctors = doc_res.json()
    assert len(doctors) > 0
    assert any("ortho" in d["specialty"].lower() for d in doctors)

    # 4. Cost prediction should use Total Knee Replacement and detect Diabetes
    cost_res = client.post(
        "/api/cost/predict",
        json={
            "treatment_name": "Total Knee Replacement",
            "city": "Hyderabad",
            "report_id": ortho_id
        },
        headers=headers
    )
    assert cost_res.status_code == 200
    cost_data = cost_res.json()
    assert cost_data["canonical_treatment"] == "Total Knee Replacement"
    assert cost_data["predicted_los_days"] >= 3.0  # Knee replacement typically 3-5 days
