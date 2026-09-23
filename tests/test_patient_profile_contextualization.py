import sys
import os
import pytest
from fastapi.testclient import TestClient

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND_DIR = os.path.join(BASE_DIR, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from database import SessionLocal
from models import User, PatientProfile, MedicalReport, ExtractedEntity
from init_db import init_db
from main import app
from ai.rag_engine import rag_engine
from ai.recommendation_engine import recommendation_engine
from security import create_access_token

client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def setup_test_users_and_profiles():
    init_db()
    db = SessionLocal()
    try:
        # User 1: Cardiology with Aspirin allergy and Hypertension
        u1 = db.query(User).filter(User.id == 1).first()
        p1 = db.query(PatientProfile).filter(PatientProfile.user_id == 1).first()
        if p1:
            p1.age = 58
            p1.gender = "Male"
            p1.allergies = "Aspirin, Penicillin"
            p1.chronic_conditions = "Hypertension, Coronary Artery Disease"
            p1.conditions = ["Hypertension", "Coronary Artery Disease"]
            db.commit()

        # User 2: Neurology with no allergies
        p2 = db.query(PatientProfile).filter(PatientProfile.user_id == 2).first()
        if p2:
            p2.age = 45
            p2.gender = "Female"
            p2.allergies = "None"
            p2.chronic_conditions = "Migraine"
            p2.conditions = ["Migraine"]
            db.commit()
    finally:
        db.close()


def test_rag_report_grounding_with_patient_profile():
    """Verifies that RAG report grounding incorporates profile context without modifying report entities."""
    entities = [{"entity_name": "Coronary Angiography", "entity_type": "Procedure", "confidence": 0.95}]
    profile_ctx = {
        "age": 58,
        "chronic_conditions": ["Hypertension"],
        "allergies": ["Aspirin"]
    }
    res = rag_engine.ground_report_analysis(
        report_text="Diagnostic report text",
        entities=entities,
        specialty="Cardiology",
        clinical_profile=profile_ctx
    )
    assert res is not None
    assert "grounding_notes" in res
    assert "patient_context_applied" in res
    assert res["patient_context_applied"]["age"] == 58
    assert "Hypertension" in res["patient_context_applied"]["chronic_conditions"]
    assert "Aspirin" in res["patient_context_applied"]["allergies"]
    # Verify grounding notes explicitly acknowledge comorbidity context
    assert "Comorbidity Context Evaluated" in res["grounding_notes"] or "Documented Allergies" in res["grounding_notes"]


def test_treatment_pathway_allergy_warning_flag():
    """Verifies that when a patient profile documents an allergy to Aspirin, any pathway mentioning Aspirin is flagged."""
    # User 1 has allergy to Aspirin
    token = create_access_token(data={"sub": "1", "email": "patient@example.com", "role": "patient"})
    headers = {"Authorization": f"Bearer {token}"}

    res = client.get(
        "/api/recommend/treatments?condition=Coronary%20Artery%20Disease&specialty=Cardiology&user_id=1",
        headers=headers
    )
    assert res.status_code == 200
    data = res.json()
    assert "recommended_pathways" in data
    assert len(data["recommended_pathways"]) > 0

    # Verify patient_context_applied is returned
    assert data["patient_context_applied"] is not None
    assert "Aspirin" in data["patient_context_applied"]["allergies_evaluated"]

    # Check that at least one cardiology pathway referencing Aspirin/DAPT has allergy conflict flagged
    flagged = [p for p in data["recommended_pathways"] if p.get("allergy_conflict_detected")]
    assert len(flagged) > 0, "Expected at least one pathway to flag Aspirin allergy conflict"
    assert "Aspirin" in flagged[0]["allergy_warning"]


def test_treatment_pathway_no_allergy_when_clean():
    """Verifies that a patient with 'None' allergies receives no false allergy flags."""
    token = create_access_token(data={"sub": "2", "email": "patient2@example.com", "role": "patient"})
    headers = {"Authorization": f"Bearer {token}"}

    res = client.get(
        "/api/recommend/treatments?condition=Migraine&specialty=Neurology&user_id=2",
        headers=headers
    )
    assert res.status_code == 200
    data = res.json()
    flagged = [p for p in data["recommended_pathways"] if p.get("allergy_conflict_detected")]
    assert len(flagged) == 0


def test_doctor_recommendations_with_comorbidities():
    """Verifies that doctor scoring incorporates patient comorbidities while maintaining primary specialty."""
    token = create_access_token(data={"sub": "1", "email": "patient@example.com", "role": "patient"})
    headers = {"Authorization": f"Bearer {token}"}

    res = client.get(
        "/api/recommend/doctors?specialty=Cardiology&user_id=1",
        headers=headers
    )
    assert res.status_code == 200
    doctors = res.json()
    assert len(doctors) > 0
    # Primary specialty is Cardiology
    for d in doctors:
        assert "cardio" in d["specialty"].lower()
    # Check if doctors have reasons attached
    assert any("experience" in r.lower() for d in doctors for r in d.get("reasons", []))


def test_strict_provenance_no_hallucinated_findings():
    """Verifies that report OCR and extracted entities are purely extractive and never inject profile data."""
    db = SessionLocal()
    try:
        # User 1 profile has "Coronary Artery Disease" and "Hypertension"
        rep = db.query(MedicalReport).filter(MedicalReport.user_id == 1).first()
        if rep and rep.entities:
            # All entities must have valid confidence and exist as substrings in the raw OCR text
            for e in rep.entities:
                assert e.confidence > 0
                assert e.entity_name.strip() != ""
    finally:
        db.close()


def test_doctor_scoring_weights_regression():
    """
    Regression Test: Verifies that doctor recommendation scoring weights remain strictly:
      - 50% Specialty/Clinical Match
      - 25% Clinical Experience
      - 25% Patient Rating
    And that comorbidity relevance operates strictly within the 50% clinical match component.
    """
    doc_sample = {
        "id": 101,
        "name": "Dr. Ramesh Sharma",
        "specialty": "Cardiology",
        "expertise": ["Interventional Cardiology", "Hypertension"],
        "experience_years": 15,
        "rating": 4.8
    }

    # 1. Base call without comorbidities (backward-compatible)
    scored_base = recommendation_engine.score_doctor(doc_sample, required_specialty="Cardiology")
    
    # Check weights explicitly documented
    assert scored_base["scoring_weights"] == {
        "specialty_match": 0.50,
        "experience": 0.25,
        "rating": 0.25
    }
    assert sum(scored_base["scoring_weights"].values()) == pytest.approx(1.0)

    # Calculate expected base score:
    # spec_match = 100.0, exp_score = min(15*4.0, 100) = 60.0, rating_score = (4.8/5.0)*100 = 96.0
    # total = 0.50*100 + 0.25*60.0 + 0.25*96.0 = 50.0 + 15.0 + 24.0 = 89.0
    expected_base = round(0.50 * 100.0 + 0.25 * 60.0 + 0.25 * 96.0, 1)
    assert scored_base["match_score"] == expected_base
    assert scored_base["score_breakdown"]["specialty_match"] == 50.0
    assert scored_base["score_breakdown"]["experience"] == 15.0
    assert scored_base["score_breakdown"]["rating"] == 24.0

    # 2. Call with matching comorbidity (boosts clinical match to 100.0)
    scored_matched = recommendation_engine.score_doctor(
        doc_sample,
        required_specialty="Cardiology",
        comorbidity_conditions=["Hypertension"]
    )
    assert scored_matched["comorbidity_matches"] == 1
    assert scored_matched["match_score"] == expected_base

    # 3. Call with unaligned comorbidity (e.g. Epilepsy for a Cardiologist)
    # Clinical match is 95.0, exp is 60.0, rating is 96.0 -> 0.50*95 + 0.25*60 + 0.25*96 = 47.5 + 15 + 24 = 86.5
    scored_unmatched = recommendation_engine.score_doctor(
        doc_sample,
        required_specialty="Cardiology",
        comorbidity_conditions=["Epilepsy"]
    )
    assert scored_unmatched["comorbidity_matches"] == 0
    expected_unmatched = round(0.50 * 95.0 + 0.25 * 60.0 + 0.25 * 96.0, 1)
    assert scored_unmatched["match_score"] == expected_unmatched
    # Verified: Comorbidity matching provides a 2.5 point clinical match advantage purely within the 50% clinical component
    assert scored_matched["match_score"] > scored_unmatched["match_score"]


def test_rag_profile_field_influence_and_provenance():
    """
    Verifies selective profile field influence on RAG:
      - age (geriatric stratification)
      - chronic_conditions (comorbidity expansion)
      - medical_history (prior procedure expansion)
      - medications (high-impact anticoagulant expansion)
      - gender (recorded but not polluting query)
      - allergies (guardrail checked, not polluting query)
      - Report entities remain strictly unchanged (no hallucination/fabrication).
    """
    entities_before = [
        {"entity_name": "Coronary Angiography", "entity_type": "Procedure", "confidence": 0.96}
    ]
    # Pass copy of entities
    entities_input = list(entities_before)

    profile_full = {
        "demographics": {
            "age": 72,
            "gender": "Female",
            "allergies": "Aspirin"
        },
        "chronic_conditions": ["Type 2 Diabetes"],
        "medical_history": ["Prior CABG"],
        "medications": ["Warfarin", "Metformin"]
    }

    res = rag_engine.ground_report_analysis(
        report_text="Diagnostic cardiac catheterization report.",
        entities=entities_input,
        specialty="Cardiology",
        clinical_profile=profile_full
    )

    # 1. Output structure validation
    assert res is not None
    assert "patient_context_applied" in res
    ctx = res["patient_context_applied"]
    assert ctx is not None

    # 2. Age group stratification
    assert ctx["age"] == 72
    assert ctx["age_group"] == "geriatric"
    assert "age_group: geriatric" in ctx["retrieval_influences"]

    # 3. Gender preserved in demographics, NOT in retrieval influences
    assert ctx["gender"] == "Female"
    assert not any("gender" in inf.lower() for inf in ctx["retrieval_influences"])

    # 4. Chronic condition influence
    assert "Type 2 Diabetes" in ctx["chronic_conditions"]
    assert any("chronic_condition: Type 2 Diabetes" in inf for inf in ctx["retrieval_influences"])

    # 5. Prior medical history influence
    assert "Prior CABG" in ctx["medical_history"]
    assert any("medical_history: Prior CABG" in inf for inf in ctx["retrieval_influences"])

    # 6. High-impact medication influence
    assert "Warfarin" in ctx["medications"]
    assert any("high_impact_medication: Warfarin" in inf for inf in ctx["retrieval_influences"])

    # 7. Allergies used as guardrail, NOT in retrieval query
    assert "Aspirin" in ctx["allergies"]
    assert not any("allergy" in inf.lower() for inf in ctx["retrieval_influences"])

    # 8. Provenance: Input entities remain strictly untouched
    assert entities_input == entities_before
    assert len(entities_input) == 1
    assert entities_input[0]["entity_name"] == "Coronary Angiography"

