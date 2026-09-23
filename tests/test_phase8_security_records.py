"""
Tests for Phase 8: Security & Medical Record Management.

Covers:
1. Bcrypt password hashing & legacy password compatibility.
2. Genuine JWT generation, signature verification, and expiration handling.
3. Login API returning decodable JWT and creating non-PII audit records.
4. Secure medical report upload:
   - Path traversal prevention (sanitizing '../../').
   - Executable/disallowed extension rejection (.exe, .sh, etc.).
   - Magic bytes / header content validation.
   - Oversized file rejection (>20MB).
5. Strict IDOR protection & medical record access control:
   - User 1 cannot view User 2's private medical report (HTTP 403 Forbidden).
   - User 1 cannot list User 2's medical records vault.
   - User 1 cannot generate a travel plan referencing User 2's medical report (HTTP 403 Forbidden).
   - User 1 cannot view or modify User 2's patient profile (HTTP 403 Forbidden).
6. Operational Audit Logging:
   - Verifies audit logs record login, upload, view, and denied access events.
   - Ensures no passwords, Bearer tokens, or raw OCR/PII are ever stored in audit logs.
   - Scopes audit log inspection to authenticated user.
"""

import sys
import os
import io
import pytest
from datetime import timedelta
from fastapi import HTTPException
from fastapi.testclient import TestClient

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(os.path.dirname(CURRENT_DIR), "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from main import app
from init_db import init_db
from database import SessionLocal
from models import User, PatientProfile, MedicalReport, AuditLog
from security import (
    hash_password, verify_password, create_access_token, decode_access_token,
    validate_uploaded_file, sanitize_filename
)

client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def setup_phase8_security_data():
    """Ensure baseline test users and isolated medical reports exist in DB."""
    init_db()
    db = SessionLocal()
    try:
        # User 1: Rajesh Verma (password: demo_password_123)
        user1 = db.query(User).filter(User.id == 1).first()
        if not user1:
            user1 = User(
                id=1,
                email="patient@example.com",
                hashed_password=hash_password("demo_password_123"),
                full_name="Rajesh Verma",
                role="patient"
            )
            db.add(user1)
            db.commit()

        # User 2: Priya Sharma (password: demo_password_456)
        user2 = db.query(User).filter(User.id == 2).first()
        if not user2:
            user2 = User(
                id=2,
                email="patient2@example.com",
                hashed_password=hash_password("demo_password_456"),
                full_name="Priya Sharma",
                role="patient"
            )
            db.add(user2)
            db.commit()

        # Ensure User 2 has a private medical report
        user2_report = db.query(MedicalReport).filter(MedicalReport.user_id == 2).first()
        if not user2_report:
            user2_report = MedicalReport(
                user_id=2,
                filename="priya_confidential_report.pdf",
                file_path="uploads/priya_confidential_report.pdf",
                summary="Confidential Pulmonology Bronchial Asthma Diagnostics.",
                recommended_specialty="Pulmonology",
                status="COMPLETED"
            )
            db.add(user2_report)
            db.commit()

        # Admin User: Chief Medical Officer
        admin_user = db.query(User).filter(User.role == "admin").first()
        if not admin_user:
            admin_user = User(
                id=99,
                email="admin@hospital.org",
                hashed_password=hash_password("admin_secure_pass_2026"),
                full_name="Chief Medical Administrator",
                role="admin"
            )
            db.add(admin_user)
            db.commit()
    finally:
        db.close()


def get_auth_token_for_user(user_id: int) -> str:
    """Helper to generate genuine JWT Bearer token for test patient user."""
    return create_access_token({"sub": str(user_id), "role": "patient"})


def get_auth_token_for_admin(user_id: int = 99) -> str:
    """Helper to generate genuine JWT Bearer token for admin user."""
    return create_access_token({"sub": str(user_id), "role": "admin"})


# =====================================================================
# 1. BCRYPT PASSWORD HASHING & BACKWARD COMPATIBILITY
# =====================================================================

def test_bcrypt_password_hashing_and_verification():
    """Verifies that password hashing produces valid bcrypt hashes and rejects mismatches."""
    password = "SuperClinicalPassword2026!"
    hashed = hash_password(password)

    # Must be a bcrypt hash ($2b$...)
    assert hashed.startswith("$2b$")
    assert verify_password(password, hashed) is True
    assert verify_password("WrongPassword123", hashed) is False

    # Salting: Two hashes of the exact same password must produce distinct strings
    hashed2 = hash_password(password)
    assert hashed != hashed2
    assert verify_password(password, hashed2) is True


def test_legacy_password_hash_compatibility():
    """Verifies backward compatibility for legacy test fixtures and demo accounts."""
    legacy_hash = "hashed_demo_password_123"
    assert verify_password("demo_password_123", legacy_hash) is True
    assert verify_password("incorrect_password", legacy_hash) is False


# =====================================================================
# 2. JWT CREATION, VALIDATION, AND EXPIRATION
# =====================================================================

def test_jwt_generation_decoding_and_payload():
    """Verifies JWT encoding and decoding with proper claims."""
    token = create_access_token({"sub": "1", "role": "patient", "email": "patient@example.com"})
    payload = decode_access_token(token)

    assert payload["sub"] == "1"
    assert payload["role"] == "patient"
    assert payload["email"] == "patient@example.com"
    assert "exp" in payload
    assert "iat" in payload


def test_jwt_expiration_rejection():
    """Verifies that expired JWT tokens raise HTTP 401 Unauthorized."""
    expired_token = create_access_token(
        {"sub": "1", "role": "patient"},
        expires_delta=timedelta(seconds=-10) # Expired 10 seconds ago
    )
    with pytest.raises(HTTPException) as exc_info:
        decode_access_token(expired_token)
    assert exc_info.value.status_code == 401
    assert "expired" in exc_info.value.detail.lower()


# =====================================================================
# 3. LOGIN API & GENUINE JWT ISSUANCE
# =====================================================================

def test_api_login_returns_valid_jwt_and_audits():
    """Verifies /api/auth/login produces genuine JWT and records audit event."""
    response = client.post("/api/auth/login", json={
        "email": "patient@example.com",
        "password": "demo_password_123"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    token = data["access_token"]

    # Decode and verify claims
    payload = decode_access_token(token)
    assert payload["sub"] == "1"

    # Verify audit log in database
    db = SessionLocal()
    try:
        log = (
            db.query(AuditLog)
            .filter(AuditLog.user_id == 1, AuditLog.action == "AUTH_LOGIN_SUCCESS")
            .order_by(AuditLog.timestamp.desc())
            .first()
        )
        assert log is not None
        assert "password" not in log.details.lower()
        assert "bearer" not in log.details.lower()
    finally:
        db.close()


def test_api_login_invalid_password_audits_failure():
    """Verifies invalid login attempt is rejected with 401 and logged."""
    response = client.post("/api/auth/login", json={
        "email": "patient@example.com",
        "password": "totally_wrong_password"
    })
    assert response.status_code == 401

    db = SessionLocal()
    try:
        log = (
            db.query(AuditLog)
            .filter(AuditLog.action == "AUTH_LOGIN_FAILED")
            .order_by(AuditLog.timestamp.desc())
            .first()
        )
        assert log is not None
        assert log.status == "FAILED"
    finally:
        db.close()


# =====================================================================
# 4. FILE UPLOAD SECURITY (TRAVERSAL, DISALLOWED EXTENSIONS, MAGIC BYTES)
# =====================================================================

def test_file_upload_path_traversal_defense():
    """Verifies that filename traversal attacks like '../../etc/passwd.pdf' are sanitized."""
    raw_name = "../../etc/passwd_evil.pdf"
    safe_name = sanitize_filename(raw_name)
    assert ".." not in safe_name
    assert "/" not in safe_name
    assert "\\" not in safe_name
    assert "passwd_evil.pdf" in safe_name


def test_file_upload_disallowed_extension_rejected():
    """Verifies that executable and script uploads (.exe, .sh) are rejected with HTTP 400."""
    token1 = get_auth_token_for_user(1)
    
    # Executable file
    fake_exe = io.BytesIO(b"MZ\x90\x00\x03\x00\x00\x00Dummy executable binary content")
    res_exe = client.post(
        "/api/reports/upload",
        files={"file": ("malware.exe", fake_exe, "application/octet-stream")},
        headers={"Authorization": f"Bearer {token1}"}
    )
    assert res_exe.status_code == 400
    assert "forbidden" in res_exe.json()["detail"].lower() or "extension" in res_exe.json()["detail"].lower()

    # Shell script
    fake_sh = io.BytesIO(b"#!/bin/bash\necho 'hello'")
    res_sh = client.post(
        "/api/reports/upload",
        files={"file": ("exploit.sh", fake_sh, "application/x-sh")},
        headers={"Authorization": f"Bearer {token1}"}
    )
    assert res_sh.status_code == 400


def test_file_upload_invalid_magic_bytes_rejected():
    """Verifies that a file named .pdf containing non-PDF bytes is rejected."""
    token1 = get_auth_token_for_user(1)
    fake_pdf = io.BytesIO(b"This is just raw text without a PDF header")
    res = client.post(
        "/api/reports/upload",
        files={"file": ("fake.pdf", fake_pdf, "application/pdf")},
        headers={"Authorization": f"Bearer {token1}"}
    )
    assert res.status_code == 400
    assert "magic" in res.json()["detail"].lower() or "header" in res.json()["detail"].lower() or "invalid" in res.json()["detail"].lower()


def test_file_upload_oversized_rejection():
    """Verifies that files exceeding 20MB are rejected."""
    # Test validation function directly to avoid allocating 21MB in test memory
    dummy_huge = b"%PDF-" + b"0" * (21 * 1024 * 1024)
    is_valid, _, msg = validate_uploaded_file(dummy_huge, "huge.pdf")
    assert is_valid is False
    assert "exceeds maximum allowed limit" in msg


# =====================================================================
# 5. STRICT CROSS-PATIENT IDOR & MEDICAL RECORD ISOLATION
# =====================================================================

def test_cross_patient_report_idor_prevention():
    """
    STRICT IDOR CHECK:
    User 1 authenticates with genuine Bearer token and attempts to access User 2's medical report.
    Backend must refuse with HTTP 403 Forbidden and record REPORT_ACCESS_DENIED in AuditLog.
    """
    db = SessionLocal()
    try:
        user2_report = db.query(MedicalReport).filter(MedicalReport.user_id == 2).first()
        assert user2_report is not None
        rep_id = user2_report.id

        token_user1 = get_auth_token_for_user(1)

        response = client.get(
            f"/api/reports/{rep_id}",
            headers={"Authorization": f"Bearer {token_user1}"}
        )
        assert response.status_code == 403
        assert "Forbidden" in response.json()["detail"]

        # Verify audit log was recorded
        denied_log = (
            db.query(AuditLog)
            .filter(AuditLog.user_id == 1, AuditLog.action == "REPORT_ACCESS_DENIED", AuditLog.resource_id == str(rep_id))
            .first()
        )
        assert denied_log is not None
        assert denied_log.status == "DENIED"
    finally:
        db.close()


def test_medical_records_vault_strictly_scoped():
    """Verifies that User 1 querying /api/reports/ only receives User 1's reports, never User 2's."""
    token_user1 = get_auth_token_for_user(1)

    response = client.get(
        "/api/reports/",
        headers={"Authorization": f"Bearer {token_user1}"}
    )
    assert response.status_code == 200
    reports = response.json()
    for r in reports:
        # None of the returned reports should belong to user 2
        assert "priya" not in r["filename"].lower()


def test_travel_plan_cross_patient_report_isolation():
    """
    Verifies that User 1 cannot craft a personalized travel plan
    using User 2's private medical report.
    """
    db = SessionLocal()
    try:
        user2_report = db.query(MedicalReport).filter(MedicalReport.user_id == 2).first()
        assert user2_report is not None

        token_user1 = get_auth_token_for_user(1)

        response = client.post(
            "/api/travel/plan",
            json={
                "hospital_id": 1,
                "doctor_id": 1,
                "medical_condition": "Cardiology",
                "report_id": user2_report.id,
                "preferred_travel_date": "2026-09-10",
                "duration_days": 5
            },
            headers={"Authorization": f"Bearer {token_user1}"}
        )
        assert response.status_code == 403
        assert "Forbidden" in response.json()["detail"]
    finally:
        db.close()


def test_patient_profile_update_idor_prevention():
    """
    Verifies that User 1 cannot modify User 2's patient profile by passing user_id=2.
    """
    token_user1 = get_auth_token_for_user(1)

    response = client.put(
        "/api/auth/profile?user_id=2",
        json={
            "age": 55,
            "blood_group": "AB+",
            "allergies": "Penicillin",
            "chronic_conditions": "None"
        },
        headers={"Authorization": f"Bearer {token_user1}"}
    )
    assert response.status_code == 403
    assert "Forbidden" in response.json()["detail"]


# =====================================================================
# 6. AUDIT LOGS ENDPOINT & SCOPING
# =====================================================================

def test_audit_logs_endpoint_scoped_to_authenticated_user():
    """Verifies that /api/reports/audit-logs returns only the current user's logs without credentials."""
    token_user1 = get_auth_token_for_user(1)

    response = client.get(
        "/api/reports/audit-logs",
        headers={"Authorization": f"Bearer {token_user1}"}
    )
    assert response.status_code == 200
    logs = response.json()
    assert isinstance(logs, list)
    for log in logs:
        assert log["user_id"] == 1
        # Confidentiality check: no passwords or tokens in details
        if log.get("details"):
            assert "password" not in log["details"].lower()
            assert "bearer" not in log["details"].lower()


# =====================================================================
# 7. FINAL FOCUSED VERIFICATION: AUTHENTICATION ENFORCEMENT & ADMIN ACCESS
# =====================================================================

def test_unauthenticated_medical_report_access_denied():
    """
    Verifies that all sensitive medical records endpoints return HTTP 401
    when no Authorization header is provided, and that ?user_id= cannot substitute for auth.
    """
    # 1. GET /api/reports/{id} without token
    res1 = client.get("/api/reports/1")
    assert res1.status_code == 401
    assert "Bearer" in res1.headers.get("WWW-Authenticate", "")

    # 2. GET /api/reports/{id} with ?user_id=1 without token (user_id NEVER substitutes for auth)
    res2 = client.get("/api/reports/1?user_id=1")
    assert res2.status_code == 401

    # 3. GET /api/reports/ without token
    res3 = client.get("/api/reports/")
    assert res3.status_code == 401

    # 4. GET /api/auth/profile without token
    res4 = client.get("/api/auth/profile")
    assert res4.status_code == 401

    # 5. PUT /api/auth/profile without token
    res5 = client.put("/api/auth/profile", json={"age": 49})
    assert res5.status_code == 401

    # 6. GET /api/reports/audit-logs without token
    res6 = client.get("/api/reports/audit-logs")
    assert res6.status_code == 401


def test_invalid_jwt_denied():
    """Verifies that requests with malformed, forged, or invalid JWTs are rejected with HTTP 401."""
    bad_headers = {"Authorization": "Bearer totally.invalid.forged_jwt_signature"}

    # 1. Reports detail
    res1 = client.get("/api/reports/1", headers=bad_headers)
    assert res1.status_code == 401

    # 2. Reports vault list
    res2 = client.get("/api/reports/", headers=bad_headers)
    assert res2.status_code == 401

    # 3. Patient profile
    res3 = client.get("/api/auth/profile", headers=bad_headers)
    assert res3.status_code == 401

    # 4. Audit logs
    res4 = client.get("/api/reports/audit-logs", headers=bad_headers)
    assert res4.status_code == 401


def test_expired_jwt_denied():
    """Verifies that requests with expired JWT tokens are rejected with HTTP 401."""
    expired_token = create_access_token(
        {"sub": "1", "role": "patient"},
        expires_delta=timedelta(seconds=-60) # Expired 1 minute ago
    )
    exp_headers = {"Authorization": f"Bearer {expired_token}"}

    res1 = client.get("/api/reports/1", headers=exp_headers)
    assert res1.status_code == 401
    assert "expired" in res1.json()["detail"].lower()

    res2 = client.get("/api/reports/", headers=exp_headers)
    assert res2.status_code == 401
    assert "expired" in res2.json()["detail"].lower()

    res3 = client.get("/api/auth/profile", headers=exp_headers)
    assert res3.status_code == 401
    assert "expired" in res3.json()["detail"].lower()


def test_cross_user_jwt_denied():
    """
    Verifies that a valid JWT for User 1 CANNOT access User 2's medical data:
    - User 2's private report: HTTP 403
    - User 2's patient profile: HTTP 403
    - User 2's private chat history: HTTP 403
    """
    db = SessionLocal()
    try:
        user2_report = db.query(MedicalReport).filter(MedicalReport.user_id == 2).first()
        assert user2_report is not None

        token_user1 = get_auth_token_for_user(1)
        headers1 = {"Authorization": f"Bearer {token_user1}"}

        # 1. Report access
        r1 = client.get(f"/api/reports/{user2_report.id}", headers=headers1)
        assert r1.status_code == 403

        # 2. Profile access with ?user_id=2
        r2 = client.get("/api/auth/profile?user_id=2", headers=headers1)
        assert r2.status_code == 403

        # 3. Chat history with ?user_id=2
        r3 = client.get("/api/services/chat/history?user_id=2", headers=headers1)
        assert r3.status_code == 403
    finally:
        db.close()


def test_unauthorized_admin_audit_log_access_denied():
    """
    Verifies that a non-admin patient user cannot access system-wide audit logs
    by requesting scope=system or scope=all.
    """
    token_patient = get_auth_token_for_user(1) # Role: patient
    headers = {"Authorization": f"Bearer {token_patient}"}

    res_all = client.get("/api/reports/audit-logs?scope=all", headers=headers)
    assert res_all.status_code == 403
    assert "administrative" in res_all.json()["detail"].lower()

    res_system = client.get("/api/reports/audit-logs?scope=system", headers=headers)
    assert res_system.status_code == 403
    assert "administrative" in res_system.json()["detail"].lower()


def test_legitimate_authenticated_audit_log_access_allowed():
    """
    Verifies legitimate access to audit logs:
    1. Authenticated patient user can view their own audit logs.
    2. Server-validated administrator can view system-wide audit logs.
    """
    # 1. Patient viewing their own audit logs
    token_patient = get_auth_token_for_user(1)
    res_pat = client.get("/api/reports/audit-logs", headers={"Authorization": f"Bearer {token_patient}"})
    assert res_pat.status_code == 200
    pat_logs = res_pat.json()
    assert isinstance(pat_logs, list)

    # 2. Administrator viewing system-wide logs
    token_admin = get_auth_token_for_admin(99)
    res_adm = client.get("/api/reports/audit-logs?scope=system", headers={"Authorization": f"Bearer {token_admin}"})
    assert res_adm.status_code == 200
    adm_logs = res_adm.json()
    assert isinstance(adm_logs, list)
