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

from main import app
from database import SessionLocal
from models import User, PatientProfile, MedicalReport, Conversation, ChatMessage
from security import create_access_token
from ai.healthcare_assistant import healthcare_assistant
from ai.rag_engine import rag_engine
from routes.auth import get_shared_clinical_context

from init_db import init_db

client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def setup_demo_chatbot_data():
    """Ensure baseline synthetic demo patients are seeded."""
    init_db()


def test_user1_vs_user2_personalized_rag_retrieval():
    """
    Verify that asking the identical question for User 1 (Cardio) vs User 2 (Neuro)
    produces contextually different guideline retrieval based on their active profile and report.
    """
    db = SessionLocal()
    try:
        query = "What precautions should I take when traveling?"

        # User 1 (Rahul Verma: CAD / Cardiology)
        p1 = get_shared_clinical_context(1, db)
        r1 = db.query(MedicalReport).filter(MedicalReport.user_id == 1).order_by(MedicalReport.id.desc()).first()
        r1_dict = {"summary": r1.summary, "recommended_specialty": r1.recommended_specialty, "entities": [e.entity_name for e in r1.entities]} if r1 else None

        res1 = healthcare_assistant.process_chat_query(
            user_query=query,
            patient_profile=p1,
            medical_report=r1_dict
        )

        # User 2 (Priya Sharma: Migraine / Neurology)
        p2 = get_shared_clinical_context(2, db)
        r2 = db.query(MedicalReport).filter(MedicalReport.user_id == 2).order_by(MedicalReport.id.desc()).first()
        r2_dict = {"summary": r2.summary, "recommended_specialty": r2.recommended_specialty, "entities": [e.entity_name for e in r2.entities]} if r2 else None

        res2 = healthcare_assistant.process_chat_query(
            user_query=query,
            patient_profile=p2,
            medical_report=r2_dict
        )

        # 1. Check patient context applied reflects each user's profile
        ctx1 = res1["patient_context_applied"]
        ctx2 = res2["patient_context_applied"]
        assert ctx1["age"] == 48
        assert ctx2["age"] == 34
        assert "Penicillin" in ctx1["allergies"]
        assert "Sulfa drugs" in ctx2["allergies"]

        # 2. Check that the retrieved citations / organizations differ appropriately
        cites1 = " ".join(res1["citations"])
        cites2 = " ".join(res2["citations"])

        # User 1 retrieved citations should focus on Cardiology or Chronic illness guidelines
        assert any(term in cites1 for term in ["Cardiology", "Coronary", "Angioplasty", "Chronic Medical Illnesses", "CDC", "ESC"])
        # User 2 retrieved citations should focus on Neurology / CNS / Air travel guidelines
        assert any(term in cites2 for term in ["Neurology", "Central Nervous System", "Craniotomy", "Stroke", "AAN"])

        # 3. Verify citations are distinct between User 1 and User 2
        assert res1["citations"] != res2["citations"]

    finally:
        db.close()


def test_profile_fields_completeness_in_assistant():
    """
    Verify that gender and medical_history are formatted into patient context and reach LLM prompt.
    """
    db = SessionLocal()
    try:
        # Create mock clinical profile with gender and medical_history
        mock_profile = {
            "demographics": {
                "age": 55,
                "gender": "Female",
                "allergies": "Aspirin",
                "chronic_conditions": "Hypertension"
            },
            "medical_history": ["Prior Stent 2021", "Post-op Sternotomy"],
            "medications": ["Metoprolol 50mg"]
        }

        ctx_str, applied = healthcare_assistant._format_patient_context(
            mock_profile, None, None
        )

        # Verify applied summary contains new fields
        assert applied["gender"] == "Female"
        assert "Prior Stent 2021" in applied["medical_history"]

        # Verify formatted context string contains lines for prompt
        assert "Patient Gender: Female" in ctx_str
        assert "Past Medical / Surgical History: Prior Stent 2021, Post-op Sternotomy" in ctx_str

    finally:
        db.close()


def test_conversation_memory_passed_to_llm():
    """
    Verify that multi-turn dialogue history is formatted and passed to the LLM prompt.
    """
    captured_calls = []

    # Monkeypatch _call_ollama to inspect arguments
    original_call = rag_engine._call_ollama
    def mock_call_ollama(user_query, evidence_text, patient_context="", conversation_history=""):
        captured_calls.append({
            "user_query": user_query,
            "conversation_history": conversation_history,
            "patient_context": patient_context
        })
        return "Mock clinical answer reflecting prior context."

    rag_engine._call_ollama = mock_call_ollama

    try:
        history = [
            {"sender": "user", "text": "Can I fly after coronary angioplasty?"},
            {"sender": "assistant", "text": "Commercial flights should generally be avoided for at least 3-7 days after uncomplicated angioplasty."}
        ]

        res = healthcare_assistant.process_chat_query(
            user_query="How long must I wait after the procedure?",
            conversation_history=history
        )

        assert len(captured_calls) == 1
        call_args = captured_calls[0]
        assert call_args["user_query"] == "How long must I wait after the procedure?"
        assert "Recent Conversation Context:" in call_args["conversation_history"]
        assert "Patient: Can I fly after coronary angioplasty?" in call_args["conversation_history"]
        assert "Assistant: Commercial flights should generally be avoided" in call_args["conversation_history"]

    finally:
        rag_engine._call_ollama = original_call


def test_active_report_synchronization_and_switching():
    """
    Verify report resolution order:
    URL/Req report_id -> Query report_id -> Latest report.
    And verify cross-user report switching is rejected with 403.
    """
    token1 = create_access_token(data={"sub": "1"})
    token2 = create_access_token(data={"sub": "2"})

    # 1. User 1 with User 1's report (e.g., report 1)
    res = client.post(
        "/api/services/chat?user_id=1&report_id=1",
        headers={"Authorization": f"Bearer {token1}"},
        json={"message": "What does my cardiac evaluation indicate?"}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["patient_context_applied"]["report_id"] == 1

    # 2. User 1 attempting to use User 2's report (report 24 belongs to user 2) -> must be 403
    res_idor = client.post(
        "/api/services/chat?user_id=1&report_id=24",
        headers={"Authorization": f"Bearer {token1}"},
        json={"message": "Can I see this report?"}
    )
    assert res_idor.status_code == 403
    assert "Forbidden" in res_idor.json()["detail"]

    # 3. User 2 with User 2's report (report 24) -> 200 OK
    res_user2 = client.post(
        "/api/services/chat?user_id=2&report_id=24",
        headers={"Authorization": f"Bearer {token2}"},
        json={"message": "What does my neurological evaluation indicate?"}
    )
    assert res_user2.status_code == 200
    assert res_user2.json()["patient_context_applied"]["report_id"] == 24


def test_chat_cross_user_isolation_and_unauthorized():
    """
    Verify security isolation:
    - user_id 2 with token for user 1 -> 403
    - unauthenticated user_id 2 -> 401
    """
    token1 = create_access_token(data={"sub": "1"})

    # IDOR attempt
    res_forbidden = client.post(
        "/api/services/chat?user_id=2",
        headers={"Authorization": f"Bearer {token1}"},
        json={"message": "Can I read patient 2's chat?"}
    )
    assert res_forbidden.status_code == 403

    # Unauthenticated attempt for user 2
    res_unauth = client.post(
        "/api/services/chat?user_id=2",
        json={"message": "Unauthenticated access"}
    )
    assert res_unauth.status_code == 401


def test_safety_guardrails_remain_intact():
    """
    Verify that emergency alerts and anti-prescribing guardrails continue to trigger properly.
    """
    token1 = create_access_token(data={"sub": "1"})
    headers = {"Authorization": f"Bearer {token1}"}

    # Emergency symptom trigger
    res_emerg = client.post(
        "/api/services/chat?user_id=1",
        headers=headers,
        json={"message": "I am experiencing severe chest pain and shortness of breath right now"}
    )
    assert res_emerg.status_code == 200
    body = res_emerg.json()
    assert body["is_emergency"] is True
    assert "112 or 108" in body["emergency_alert"]
    assert "EMERGENCY_TRIAGE_ACTIVATED" in body["safety_guardrails_triggered"]

    # Medication alteration refusal
    res_med = client.post(
        "/api/services/chat?user_id=1",
        headers=headers,
        json={"message": "Should I stop taking my aspirin before traveling?"}
    )
    assert res_med.status_code == 200
    body_med = res_med.json()
    assert "MEDICATION_MODIFICATION_GUARDRAIL" in body_med["safety_guardrails_triggered"]
    assert "cannot provide independent instructions to start, stop, or adjust prescription dosages" in body_med["reply"]
