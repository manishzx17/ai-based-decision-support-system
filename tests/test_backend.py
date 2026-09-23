import sys
import os

# Add project root and backend to sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND_DIR = os.path.join(BASE_DIR, "backend")

if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import pytest
from ai.ocr_engine import ocr_engine
from ai.clinical_bert import clinical_bert_extractor
from ai.recommendation_engine import recommendation_engine
from ai.cost_prediction import cost_predictor
from ai.shap_explainer import shap_explainer
from ai.astar_navigation import astar_navigator
from ai.translator import medical_translator

def test_ocr_extraction():
    # 1. Test genuine digital text PDF
    pdf_bytes = b"""%PDF-1.4
1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj
2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj
3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >> endobj
4 0 obj << /Length 135 >> stream
BT
/F1 12 Tf
72 712 Td
(Patient Name: John Doe) Tj
0 -18 Td
(Diagnosis: Acute Bronchitis) Tj
0 -18 Td
(Prescription: Amoxicillin 500mg TDS) Tj
ET
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
508
%%EOF"""
    extracted_pdf = ocr_engine.extract_text(pdf_bytes, "Pulmonology_Bronchitis.pdf")
    assert isinstance(extracted_pdf, str)
    assert "Bronchitis" in extracted_pdf
    assert "John Doe" in extracted_pdf

    # 2. Test genuine scanned image OCR
    webp_path = os.path.join(BACKEND_DIR, "uploads", "1.webp")
    if os.path.exists(webp_path):
        with open(webp_path, "rb") as f:
            img_bytes = f.read()
        extracted_img = ocr_engine.extract_text(img_bytes, "1.webp")
        assert len(extracted_img) > 20
        assert any(k in extracted_img for k in ["JAGNYASENI", "HOSPITAL", "TICKET", "PATEL", "OPD", "BARSHARANI"])

def test_clinical_bert_entity_extraction():
    text = "Patient presents with exertional angina and LAD 85% proximal stenosis. Advised Percutaneous Coronary Intervention with Aspirin 75mg."
    entities = clinical_bert_extractor.extract_entities(text)
    assert len(entities) >= 3
    types = [e["entity_type"] for e in entities]
    assert "Symptom" in types or "Procedure" in types or "Medication" in types or "Disease" in types

def test_weighted_recommendation_scoring():
    hospital = {
        "id": 1,
        "name": "Apollo Hospitals Jubilee Hills",
        "city": "Hyderabad",
        "specialties": ["Cardiology", "Oncology"],
        "rating": 4.9,
        "distance_km": 4.2,
        "insurance_accepted": ["Star Health"],
        "facilities": ["24x7 ICU", "Cath Lab"],
        "availability_status": "High"
    }

    scored = recommendation_engine.score_hospital(hospital, required_specialty="Cardiology")
    assert "recommendation_score" in scored
    assert scored["recommendation_score"] >= 80.0
    assert len(scored["shap_reasons"]) >= 2

def test_xgboost_cost_prediction_and_shap():
    pred = cost_predictor.predict(
        treatment_name="Coronary Angioplasty",
        city="Hyderabad",
        room_type="Private AC Deluxe",
        duration_days=4
    )
    assert pred["estimated_min_cost"] > 0
    assert pred["estimated_max_cost"] > pred["estimated_min_cost"]
    assert "shap_feature_impacts" in pred

    explanation = shap_explainer.explain_cost(pred)
    assert "breakdown" in explanation
    assert len(explanation["breakdown"]) >= 3

def test_astar_navigation():
    route = astar_navigator.plan_route("Airport", "Hospital")
    assert route["distance_km"] > 0
    assert route["estimated_travel_time_minutes"] > 0
    assert len(route["turn_by_turn_waypoints"]) >= 3

def test_medical_translation():
    res = medical_translator.translate("Take medicine after food", "English", "Telugu")
    assert res["original_text"] == "Take medicine after food"
    assert len(res["translated_text"]) > 0

if __name__ == "__main__":
    test_ocr_extraction()
    test_clinical_bert_entity_extraction()
    test_weighted_recommendation_scoring()
    test_xgboost_cost_prediction_and_shap()
    test_astar_navigation()
    test_medical_translation()
    print("ALL BACKEND AI UNIT TESTS PASSED CLEANLY!")
