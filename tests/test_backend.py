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
    dummy_bytes = b"Cardiology Report LAD 85% Stenosis"
    extracted = ocr_engine.extract_text(dummy_bytes, "Cardiology_Angiography.pdf")
    assert isinstance(extracted, str)
    assert len(extracted) > 20

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
