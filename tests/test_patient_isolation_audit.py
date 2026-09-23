"""
Comprehensive Patient Isolation & Cross-User Security Audit Test Suite.
Validates:
1. Check 1: Login for Rahul, Priya, Amit (username & email), wrong password rejection (401), logout.
2. Check 2 & 4: Server-side authorization, user_id override rejection (403), report_id ownership rejection (403),
   conversation_id ownership rejection (403), unauthenticated rejection (401), token invalidation upon logout (401).
3. Check 3: Patient context isolation across all 3 users.
"""

import os
import sys
import pytest
from fastapi.testclient import TestClient

BACKEND_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from main import app
from init_db import init_db
from database import SessionLocal
from models import User, PatientProfile, MedicalReport, Conversation, ChatMessage
from security import hash_password

client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def setup_audit_data():
    init_db()
    db = SessionLocal()
    try:
        # Verify/ensure users 1, 2, 3 have reports and distinct conversations
        r1 = db.query(MedicalReport).filter(MedicalReport.user_id == 1).first()
        if not r1:
            r1 = MedicalReport(
                user_id=1,
                filename="rahul_cardio_report.pdf",
                file_path="uploads/rahul_cardio_report.pdf",
                summary="Cardiology report for Rahul Verma. Severe CAD.",
                recommended_specialty="Cardiology",
                status="COMPLETED"
            )
            db.add(r1)
            db.commit()

        r2 = db.query(MedicalReport).filter(MedicalReport.user_id == 2).first()
        if not r2:
            r2 = MedicalReport(
                user_id=2,
                filename="priya_neuro_report.pdf",
                file_path="uploads/priya_neuro_report.pdf",
                summary="Neurology report for Priya Sharma. Chronic Migraine.",
                recommended_specialty="Neurology",
                status="COMPLETED"
            )
            db.add(r2)
            db.commit()

        r3 = db.query(MedicalReport).filter(MedicalReport.user_id == 3).first()
        if not r3:
            r3 = MedicalReport(
                user_id=3,
                filename="amit_ortho_report.pdf",
                file_path="uploads/amit_ortho_report.pdf",
                summary="Orthopedics report for Amit Patel. Knee Osteoarthritis.",
                recommended_specialty="Orthopedics",
                status="COMPLETED"
            )
            db.add(r3)
            db.commit()

        # Ensure conversations for user 1 and user 2
        c1 = db.query(Conversation).filter(Conversation.user_id == 1).first()
        if not c1:
            c1 = Conversation(user_id=1, title="Rahul Cardiology Inquiry")
            db.add(c1)
            db.commit()
            db.refresh(c1)
            m1 = ChatMessage(conversation_id=c1.id, sender="user", text="I have chest tightness.")
            db.add(m1)
            db.commit()

        c2 = db.query(Conversation).filter(Conversation.user_id == 2).first()
        if not c2:
            c2 = Conversation(user_id=2, title="Priya Migraine Inquiry")
            db.add(c2)
            db.commit()
            db.refresh(c2)
            m2 = ChatMessage(conversation_id=c2.id, sender="user", text="I have severe migraine headaches.")
            db.add(m2)
            db.commit()
    finally:
        db.close()


def test_check1_login_all_three_users():
    # Rahul
    res1 = client.post("/api/auth/login", json={"username": "demo_cardio", "password": "DemoPassword@123"})
    assert res1.status_code == 200
    assert res1.json()["user"]["full_name"] == "Rahul Verma"

    # Priya
    res2 = client.post("/api/auth/login", json={"username": "demo_neuro", "password": "DemoPassword@123"})
    assert res2.status_code == 200
    assert res2.json()["user"]["full_name"] == "Priya Sharma"

    # Amit
    res3 = client.post("/api/auth/login", json={"username": "demo_ortho", "password": "DemoPassword@123"})
    assert res3.status_code == 200
    assert res3.json()["user"]["full_name"] == "Amit Patel"

    # Wrong password
    res_bad = client.post("/api/auth/login", json={"username": "demo_cardio", "password": "WrongPassword!"})
    assert res_bad.status_code == 401

    # Logout
    tok = res1.json()["access_token"]
    res_logout = client.post("/api/auth/logout", headers={"Authorization": f"Bearer {tok}"})
    assert res_logout.status_code == 200


def test_check2_unauthenticated_protected_requests_return_401():
    endpoints = [
        ("GET", "/api/auth/profile"),
        ("GET", "/api/auth/profile/shared-context"),
        ("GET", "/api/reports/"),
        ("GET", "/api/reports/audit-logs"),
        ("POST", "/api/services/chat"),
        ("GET", "/api/services/chat/history"),
        ("GET", "/api/travel/plan"),
        ("POST", "/api/recommend/personalized"),
        ("GET", "/api/recommend/hospitals"),
    ]
    for method, ep in endpoints:
        if method == "GET":
            res = client.get(ep)
        else:
            res = client.post(ep, json={})
        assert res.status_code == 401, f"Expected 401 for unauthenticated {ep}, got {res.status_code}: {res.text}"


def test_check2_and_4_cross_user_id_override_attacks():
    # Login as User 1 (Rahul)
    tok1 = client.post("/api/auth/login", json={"username": "demo_cardio", "password": "DemoPassword@123"}).json()["access_token"]
    h1 = {"Authorization": f"Bearer {tok1}"}

    # Attempt to access User 2 profile with User 1 token
    res = client.get("/api/auth/profile?user_id=2", headers=h1)
    assert res.status_code == 403

    # Attempt to access User 3 profile with User 1 token
    res = client.get("/api/auth/profile?user_id=3", headers=h1)
    assert res.status_code == 403

    # Attempt to access User 2 shared context with User 1 token
    res = client.get("/api/auth/profile/shared-context?user_id=2", headers=h1)
    assert res.status_code == 403

    # Attempt to access User 2 reports with User 1 token
    res = client.get("/api/reports/?user_id=2", headers=h1)
    assert res.status_code == 403

    # Attempt to access User 2 recommendations with User 1 token
    res = client.get("/api/recommend/hospitals?user_id=2", headers=h1)
    assert res.status_code == 403

    # Attempt to access User 2 travel plan with User 1 token
    res = client.get("/api/travel/plan?user_id=2", headers=h1)
    assert res.status_code == 403

    # Attempt to access User 2 chat history with User 1 token
    res = client.get("/api/services/chat/history?user_id=2", headers=h1)
    assert res.status_code == 403

    # Attempt to query RAG with User 2 user_id override
    res = client.post("/api/services/rag/query?user_id=2", json={"query": "test", "use_clinical_profile": True}, headers=h1)
    assert res.status_code == 403

    # Login as User 2 (Priya) -> attempt to access User 1 data
    tok2 = client.post("/api/auth/login", json={"username": "demo_neuro", "password": "DemoPassword@123"}).json()["access_token"]
    h2 = {"Authorization": f"Bearer {tok2}"}

    res = client.get("/api/auth/profile?user_id=1", headers=h2)
    assert res.status_code == 403
    res = client.get("/api/reports/?user_id=1", headers=h2)
    assert res.status_code == 403

    # Login as User 3 (Amit) -> attempt to access User 1/User 2 data
    tok3 = client.post("/api/auth/login", json={"username": "demo_ortho", "password": "DemoPassword@123"}).json()["access_token"]
    h3 = {"Authorization": f"Bearer {tok3}"}

    res = client.get("/api/auth/profile?user_id=1", headers=h3)
    assert res.status_code == 403
    res = client.get("/api/auth/profile?user_id=2", headers=h3)
    assert res.status_code == 403
    res = client.get("/api/reports/?user_id=1", headers=h3)
    assert res.status_code == 403
    res = client.get("/api/reports/?user_id=2", headers=h3)
    assert res.status_code == 403


def test_check2_and_4_cross_user_report_ownership_override_attacks():
    db = SessionLocal()
    try:
        user2_rep = db.query(MedicalReport).filter(MedicalReport.user_id == 2).first()
        user1_rep = db.query(MedicalReport).filter(MedicalReport.user_id == 1).first()
        assert user2_rep is not None
        assert user1_rep is not None
        u2_rep_id = user2_rep.id
        u1_rep_id = user1_rep.id
    finally:
        db.close()

    tok1 = client.post("/api/auth/login", json={"username": "demo_cardio", "password": "DemoPassword@123"}).json()["access_token"]
    h1 = {"Authorization": f"Bearer {tok1}"}

    # 1. User 1 requests User 2's report directly -> 403
    res = client.get(f"/api/reports/{u2_rep_id}", headers=h1)
    assert res.status_code == 403

    # 2. User 1 tries to sync profile from User 2's report -> 403
    res = client.post(f"/api/auth/profile/sync-from-report/{u2_rep_id}", headers=h1)
    assert res.status_code == 403

    # 3. User 1 passes User 2's report_id to recommendations -> 403
    res = client.get(f"/api/recommend/hospitals?report_id={u2_rep_id}", headers=h1)
    assert res.status_code == 403

    # 4. User 1 passes User 2's report_id to chat -> 403
    res = client.post("/api/services/chat", json={"message": "Analyze report", "report_id": u2_rep_id}, headers=h1)
    assert res.status_code == 403

    # 5. User 1 passes User 2's report_id to travel plan -> 403
    res = client.post("/api/travel/plan", json={
        "hospital_id": 1,
        "doctor_id": 1,
        "medical_condition": "Cardiac Surgery",
        "current_location": "Hyderabad",
        "preferred_travel_date": "2026-10-15",
        "report_id": u2_rep_id
    }, headers=h1)
    assert res.status_code == 403

    # Vice versa: User 2 requests User 1's report -> 403
    tok2 = client.post("/api/auth/login", json={"username": "demo_neuro", "password": "DemoPassword@123"}).json()["access_token"]
    h2 = {"Authorization": f"Bearer {tok2}"}
    res = client.get(f"/api/reports/{u1_rep_id}", headers=h2)
    assert res.status_code == 403


def test_check2_and_4_cross_user_conversation_ownership_override_attacks():
    db = SessionLocal()
    try:
        user2_conv = db.query(Conversation).filter(Conversation.user_id == 2).first()
        user1_conv = db.query(Conversation).filter(Conversation.user_id == 1).first()
        assert user2_conv is not None
        assert user1_conv is not None
        u2_conv_id = user2_conv.id
        u1_conv_id = user1_conv.id
    finally:
        db.close()

    tok1 = client.post("/api/auth/login", json={"username": "demo_cardio", "password": "DemoPassword@123"}).json()["access_token"]
    h1 = {"Authorization": f"Bearer {tok1}"}

    # 1. User 1 requests User 2's conversation history -> 403
    res = client.get(f"/api/services/chat/history?conversation_id={u2_conv_id}", headers=h1)
    assert res.status_code == 403

    # 2. User 1 attempts to send chat message into User 2's conversation -> 403
    res = client.post("/api/services/chat", json={
        "message": "Intrusion test message",
        "conversation_id": u2_conv_id
    }, headers=h1)
    assert res.status_code == 403

    # Vice versa: User 2 requests User 1's conversation -> 403
    tok2 = client.post("/api/auth/login", json={"username": "demo_neuro", "password": "DemoPassword@123"}).json()["access_token"]
    h2 = {"Authorization": f"Bearer {tok2}"}
    res = client.get(f"/api/services/chat/history?conversation_id={u1_conv_id}", headers=h2)
    assert res.status_code == 403


def test_check2_token_invalidation_and_reuse_rejection():
    # Test for User 1, 2, and 3
    for username in ["demo_cardio", "demo_neuro", "demo_ortho"]:
        login_res = client.post("/api/auth/login", json={"username": username, "password": "DemoPassword@123"})
        assert login_res.status_code == 200
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Active token succeeds
        assert client.get("/api/auth/profile", headers=headers).status_code == 200

        # Logout invalidates
        logout_res = client.post("/api/auth/logout", headers=headers)
        assert logout_res.status_code == 200

        # Reusing logged-out token returns 401
        reuse_res = client.get("/api/auth/profile", headers=headers)
        assert reuse_res.status_code == 401
        assert "logged out" in reuse_res.json()["detail"].lower() or "revoked" in reuse_res.json()["detail"].lower()
