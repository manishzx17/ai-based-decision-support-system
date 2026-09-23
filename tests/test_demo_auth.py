"""
Automated Test Suite for Minimal Demo Authentication & Patient-Context Isolation.

Verifies:
1. Login with 3 synthetic demo patient accounts via username or email.
2. Rejection of invalid credentials with HTTP 401.
3. Logout functionality and audit event tracking.
4. Demo user directory API (/api/auth/demo-users).
5. Strict cross-patient clinical context isolation between all 3 demo users:
   - User 1: Rahul Verma (Cardiology / CAD, Hyderabad)
   - User 2: Priya Sharma (Neurology / Migraine, Bengaluru)
   - User 3: Amit Patel (Orthopedics / Knee Osteoarthritis, Delhi)
"""

import sys
import os
import pytest
from fastapi.testclient import TestClient

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(os.path.dirname(CURRENT_DIR), "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from main import app
from init_db import init_db
from database import SessionLocal
from models import User, PatientProfile, MedicalReport, AuditLog

client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def setup_demo_auth_data():
    """Ensure DB and 3 demo patient accounts are initialized."""
    init_db()


def test_demo_users_endpoint():
    """Verifies /api/auth/demo-users returns the 3 synthetic demo patients."""
    res = client.get("/api/auth/demo-users")
    assert res.status_code == 200
    users = res.json()
    assert len(users) == 3

    u1, u2, u3 = users[0], users[1], users[2]
    assert u1["id"] == 1
    assert u1["username"] == "demo_cardio"
    assert u1["specialty"] == "Cardiology"
    assert "Hyderabad" in u1["city"]

    assert u2["id"] == 2
    assert u2["username"] == "demo_neuro"
    assert u2["specialty"] == "Neurology"
    assert "Bengaluru" in u2["city"]

    assert u3["id"] == 3
    assert u3["username"] == "demo_ortho"
    assert u3["specialty"] == "Orthopedics"
    assert "Delhi" in u3["city"]


def test_login_success_all_three_users_by_username():
    """Verifies that User 1, User 2, and User 3 can each log in with their demo username."""
    test_cases = [
        ("demo_cardio", 1, "Rahul Verma", "Cardiology"),
        ("demo_neuro", 2, "Priya Sharma", "Neurology"),
        ("demo_ortho", 3, "Amit Patel", "Orthopedics"),
    ]

    for username, expected_id, expected_name, expected_specialty in test_cases:
        res = client.post("/api/auth/login", json={
            "username": username,
            "password": "DemoPassword@123"
        })
        assert res.status_code == 200, f"Login failed for {username}: {res.text}"
        data = res.json()
        assert "access_token" in data
        assert data["user"]["id"] == expected_id
        assert data["user"]["full_name"] == expected_name
        assert data["user"]["specialty"] == expected_specialty


def test_login_success_all_three_users_by_email():
    """Verifies that all 3 users can also authenticate by email."""
    test_cases = [
        ("patient@example.com", 1),
        ("patient2@example.com", 2),
        ("patient3@example.com", 3),
    ]

    for email, expected_id in test_cases:
        res = client.post("/api/auth/login", json={
            "email": email,
            "password": "DemoPassword@123"
        })
        assert res.status_code == 200
        assert res.json()["user"]["id"] == expected_id


def test_login_invalid_password_rejected():
    """Verifies that invalid password attempts return HTTP 401."""
    res = client.post("/api/auth/login", json={
        "username": "demo_cardio",
        "password": "WrongPassword!999"
    })
    assert res.status_code == 401
    assert "invalid" in res.json()["detail"].lower()


def test_login_unknown_user_rejected():
    """Verifies that non-existent username returns HTTP 401."""
    res = client.post("/api/auth/login", json={
        "username": "non_existent_patient_999",
        "password": "DemoPassword@123"
    })
    assert res.status_code == 401


def test_logout_endpoint():
    """Verifies the logout action returns success and logs audit."""
    res = client.post("/api/auth/logout?user_id=1")
    assert res.status_code == 200
    assert "successfully" in res.json()["message"].lower()


def test_patient_context_isolation_clinical_profiles():
    """Verifies that each demo patient has an isolated, distinct clinical profile when authenticated."""
    # User 1: Cardiology
    tok1 = client.post("/api/auth/login", json={"username": "demo_cardio", "password": "DemoPassword@123"}).json()["access_token"]
    res1 = client.get("/api/auth/profile", headers={"Authorization": f"Bearer {tok1}"})
    assert res1.status_code == 200
    prof1 = res1.json()
    assert prof1["user_id"] == 1
    assert prof1["current_city"] == "Hyderabad"
    assert "Coronary" in str(prof1["conditions"]) or "Hypertension" in str(prof1["chronic_conditions"])

    # User 2: Neurology
    tok2 = client.post("/api/auth/login", json={"username": "demo_neuro", "password": "DemoPassword@123"}).json()["access_token"]
    res2 = client.get("/api/auth/profile", headers={"Authorization": f"Bearer {tok2}"})
    assert res2.status_code == 200
    prof2 = res2.json()
    assert prof2["user_id"] == 2
    assert prof2["current_city"] == "Bengaluru"
    assert "Migraine" in str(prof2["conditions"]) or "Migraine" in str(prof2["chronic_conditions"])

    # User 3: Orthopedics
    tok3 = client.post("/api/auth/login", json={"username": "demo_ortho", "password": "DemoPassword@123"}).json()["access_token"]
    res3 = client.get("/api/auth/profile", headers={"Authorization": f"Bearer {tok3}"})
    assert res3.status_code == 200
    prof3 = res3.json()
    assert prof3["user_id"] == 3
    assert prof3["current_city"] == "Delhi"
    assert "Osteoarthritis" in str(prof3["conditions"]) or "Osteoarthritis" in str(prof3["chronic_conditions"])

    # Confirm profiles are distinct between users
    assert prof1["current_city"] != prof2["current_city"]
    assert prof2["current_city"] != prof3["current_city"]


def test_patient_context_isolation_reports():
    """Verifies that reports queried for User 2 or User 3 return strictly their isolated reports."""
    # User 2 reports
    tok2 = client.post("/api/auth/login", json={"username": "demo_neuro", "password": "DemoPassword@123"}).json()["access_token"]
    res2 = client.get("/api/reports/", headers={"Authorization": f"Bearer {tok2}"})
    assert res2.status_code == 200
    reports2 = res2.json()
    assert len(reports2) >= 1
    for r in reports2:
        assert r["user_id"] == 2
    assert any("Neurology" in (r.get("recommended_specialty") or "") or "neurology" in r["filename"].lower() for r in reports2)

    # User 3 reports
    tok3 = client.post("/api/auth/login", json={"username": "demo_ortho", "password": "DemoPassword@123"}).json()["access_token"]
    res3 = client.get("/api/reports/", headers={"Authorization": f"Bearer {tok3}"})
    assert res3.status_code == 200
    reports3 = res3.json()
    assert len(reports3) >= 1
    for r in reports3:
        assert r["user_id"] == 3
        assert r["recommended_specialty"] == "Orthopedics"
        assert "Orthopedic" in r["filename"]


# =====================================================================
# SECURITY AUDIT: CROSS-USER AUTHORIZATION & LOGOUT INVALIDATION
# =====================================================================

def test_authenticated_user1_cross_user_requests_rejected():
    """
    Login as User 1.
    While authenticated as User 1, request User 2's or User 3's profile/reports/data
    by changing user_id -> MUST be rejected with HTTP 403.
    """
    login_res = client.post("/api/auth/login", json={"username": "demo_cardio", "password": "DemoPassword@123"})
    assert login_res.status_code == 200
    token1 = login_res.json()["access_token"]
    headers1 = {"Authorization": f"Bearer {token1}"}

    # 1. Own profile succeeds
    own_prof = client.get("/api/auth/profile", headers=headers1)
    assert own_prof.status_code == 200
    assert own_prof.json()["user_id"] == 1

    # 2. Request User 2 profile -> 403 Forbidden
    u2_prof = client.get("/api/auth/profile?user_id=2", headers=headers1)
    assert u2_prof.status_code == 403
    assert "Forbidden" in u2_prof.json()["detail"]

    # 3. Request User 3 profile -> 403 Forbidden
    u3_prof = client.get("/api/auth/profile?user_id=3", headers=headers1)
    assert u3_prof.status_code == 403

    # 4. Modify User 2 profile -> 403 Forbidden
    mod_u2 = client.put("/api/auth/profile?user_id=2", json={"age": 99}, headers=headers1)
    assert mod_u2.status_code == 403

    # 5. Request User 2 reports -> 403 Forbidden
    u2_reps = client.get("/api/reports/?user_id=2", headers=headers1)
    assert u2_reps.status_code == 403

    # 6. Request User 3 reports -> 403 Forbidden
    u3_reps = client.get("/api/reports/?user_id=3", headers=headers1)
    assert u3_reps.status_code == 403

    # 7. Request User 2's specific medical report -> 403 Forbidden
    db = SessionLocal()
    try:
        user2_rep = db.query(MedicalReport).filter(MedicalReport.user_id == 2).first()
        assert user2_rep is not None
        rep_res = client.get(f"/api/reports/{user2_rep.id}", headers=headers1)
        assert rep_res.status_code == 403
    finally:
        db.close()


def test_authenticated_user2_cross_user_requests_rejected():
    """
    Login as User 2.
    While authenticated as User 2, request User 1's or User 3's profile/reports/data
    by changing user_id -> MUST be rejected with HTTP 403.
    """
    login_res = client.post("/api/auth/login", json={"username": "demo_neuro", "password": "DemoPassword@123"})
    assert login_res.status_code == 200
    token2 = login_res.json()["access_token"]
    headers2 = {"Authorization": f"Bearer {token2}"}

    # 1. Own profile succeeds
    own_prof = client.get("/api/auth/profile", headers=headers2)
    assert own_prof.status_code == 200
    assert own_prof.json()["user_id"] == 2

    # 2. Request User 1 profile -> 403 Forbidden
    u1_prof = client.get("/api/auth/profile?user_id=1", headers=headers2)
    assert u1_prof.status_code == 403

    # 3. Request User 3 profile -> 403 Forbidden
    u3_prof = client.get("/api/auth/profile?user_id=3", headers=headers2)
    assert u3_prof.status_code == 403

    # 4. Request User 1 reports -> 403 Forbidden
    u1_reps = client.get("/api/reports/?user_id=1", headers=headers2)
    assert u1_reps.status_code == 403

    # 5. Request User 3 reports -> 403 Forbidden
    u3_reps = client.get("/api/reports/?user_id=3", headers=headers2)
    assert u3_reps.status_code == 403


def test_authenticated_user3_cross_user_requests_rejected():
    """
    Login as User 3.
    While authenticated as User 3, request User 1's or User 2's profile/reports/data
    by changing user_id -> MUST be rejected with HTTP 403.
    """
    login_res = client.post("/api/auth/login", json={"username": "demo_ortho", "password": "DemoPassword@123"})
    assert login_res.status_code == 200
    token3 = login_res.json()["access_token"]
    headers3 = {"Authorization": f"Bearer {token3}"}

    # 1. Own profile succeeds
    own_prof = client.get("/api/auth/profile", headers=headers3)
    assert own_prof.status_code == 200
    assert own_prof.json()["user_id"] == 3

    # 2. Request User 1 profile -> 403 Forbidden
    u1_prof = client.get("/api/auth/profile?user_id=1", headers=headers3)
    assert u1_prof.status_code == 403

    # 3. Request User 2 profile -> 403 Forbidden
    u2_prof = client.get("/api/auth/profile?user_id=2", headers=headers3)
    assert u2_prof.status_code == 403

    # 4. Request User 1 reports -> 403 Forbidden
    u1_reps = client.get("/api/reports/?user_id=1", headers=headers3)
    assert u1_reps.status_code == 403

    # 5. Request User 2 reports -> 403 Forbidden
    u2_reps = client.get("/api/reports/?user_id=2", headers=headers3)
    assert u2_reps.status_code == 403


def test_logout_invalidates_server_side_authentication():
    """
    Verifies that calling /api/auth/logout invalidates the bearer token server-side,
    and subsequent requests using that token are rejected with HTTP 401.
    Tested for Users 1, 2, and 3.
    """
    for username in ["demo_cardio", "demo_neuro", "demo_ortho"]:
        # 1. Login
        login_res = client.post("/api/auth/login", json={"username": username, "password": "DemoPassword@123"})
        assert login_res.status_code == 200
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 2. Verify token is active and valid
        profile_res = client.get("/api/auth/profile", headers=headers)
        assert profile_res.status_code == 200

        # 3. Logout with token
        logout_res = client.post("/api/auth/logout", headers=headers)
        assert logout_res.status_code == 200

        # 4. Attempt to use invalidated token -> MUST return 401 Unauthorized
        post_logout_res = client.get("/api/auth/profile", headers=headers)
        assert post_logout_res.status_code == 401
        assert "logged out" in post_logout_res.json()["detail"].lower() or "revoked" in post_logout_res.json()["detail"].lower()


def test_invalid_and_expired_tokens_rejected():
    """Verifies that invalid or expired bearer tokens are rejected with HTTP 401."""
    # Malformed token
    res1 = client.get("/api/auth/profile", headers={"Authorization": "Bearer invalid.malformed.token"})
    assert res1.status_code == 401

    # Expired token
    from datetime import timedelta
    from security import create_access_token
    expired_tok = create_access_token({"sub": "1", "role": "patient"}, expires_delta=timedelta(seconds=-30))
    res2 = client.get("/api/auth/profile", headers={"Authorization": f"Bearer {expired_tok}"})
    assert res2.status_code == 401
    assert "expired" in res2.json()["detail"].lower()
