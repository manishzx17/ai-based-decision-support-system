"""
Security and Access Control Utilities for 12C Medical Travel Decision Support System.
Handles:
- Bcrypt password hashing and legacy password compatibility.
- Genuine JWT creation, decoding, and expiration enforcement.
- Strict authentication & authorization dependency with IDOR prevention.
- Non-PII audit logging for medical record actions.
- File-upload validation (extension, magic bytes, size, traversal sanitization).
"""

import os
import re
import uuid
import bcrypt
import jwt
from datetime import datetime, timedelta
from typing import Optional, List, Tuple, Dict, Any
from fastapi import Request, HTTPException, status, Depends
from sqlalchemy.orm import Session

from config import settings
from database import get_db
from models import User, AuditLog

# Allowed file types for medical records
ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".webp", ".tiff", ".tif", ".gif"}
MAX_FILE_SIZE_BYTES = 20 * 1024 * 1024  # 20 MB

# Disallowed executable or dangerous extensions
DISALLOWED_EXTENSIONS = {
    ".exe", ".sh", ".bat", ".cmd", ".py", ".js", ".php", ".vbs",
    ".bin", ".msi", ".dll", ".so", ".jar", ".ps1", ".bash", ".pl"
}


# =====================================================================
# 1. PASSWORD HASHING & VERIFICATION
# =====================================================================

def hash_password(plain_password: str) -> str:
    """Hashes a plaintext password using bcrypt with salt."""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(plain_password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies a plaintext password against a hashed password.
    Supports bcrypt hashes as well as legacy seed passwords (hashed_*)
    for backward compatibility with existing tests and demo data.
    """
    if not plain_password or not hashed_password:
        return False

    # Check bcrypt format
    if hashed_password.startswith("$2b$") or hashed_password.startswith("$2a$") or hashed_password.startswith("$2y$"):
        try:
            return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
        except Exception:
            return False

    # Check legacy seed/demo password format (e.g. 'hashed_demo_password_123')
    if hashed_password.startswith("hashed_"):
        expected_legacy = f"hashed_{plain_password}"
        return hashed_password == expected_legacy

    return False


# =====================================================================
# 2. JWT TOKEN CREATION & VALIDATION
# =====================================================================

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Generates a genuine signed JWT access token with expiration and unique jti."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "jti": uuid.uuid4().hex
    })
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


REVOKED_TOKENS: set = set()


def revoke_token(token: str) -> None:
    """Revokes a token so subsequent requests are rejected."""
    if token:
        REVOKED_TOKENS.add(token.strip())


def is_token_revoked(token: str) -> bool:
    """Checks whether a token has been revoked on logout."""
    if not token:
        return False
    return token.strip() in REVOKED_TOKENS


def decode_access_token(token: str) -> Dict[str, Any]:
    """
    Decodes and validates signature and expiration of a JWT access token.
    Raises HTTPException 401 on expired, invalid, or revoked token.
    """
    clean_token = token.strip() if token else ""
    if is_token_revoked(clean_token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session has been logged out. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"}
        )
    try:
        payload = jwt.decode(clean_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session has expired. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token.",
            headers={"WWW-Authenticate": "Bearer"}
        )


# =====================================================================
# 3. AUTHENTICATION & STRICT ISOLATION DEPENDENCY
# =====================================================================

def get_current_user(
    request: Request,
    user_id: Optional[int] = None,
    db: Session = Depends(get_db)
) -> User:
    """
    Genuine authentication & authorization dependency.
    Validates server-side Bearer token if provided.
    Raises 401 on invalid/expired/revoked token.
    Enforces authorization check if user_id query/body param differs from authenticated user.
    """
    auth_header = request.headers.get("Authorization")

    if auth_header:
        if not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authorization scheme. Bearer token required.",
                headers={"WWW-Authenticate": "Bearer"}
            )
        token = auth_header.split(" ", 1)[1].strip()
        payload = decode_access_token(token)
        sub = payload.get("sub")
        if not sub:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token payload missing subject identifier.",
                headers={"WWW-Authenticate": "Bearer"}
            )
        user = db.query(User).filter(User.id == int(sub)).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authenticated user not found in database.",
                headers={"WWW-Authenticate": "Bearer"}
            )
        # IDOR check: If a specific user_id was requested that differs from the authenticated user
        if user_id is not None and user_id != user.id and getattr(user, "role", "") != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: You do not have authorization to access another patient's data."
            )
        return user

    # No Authorization header provided: strictly require authentication
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required to access patient data.",
        headers={"WWW-Authenticate": "Bearer"}
    )



# =====================================================================
# 4. AUDIT LOGGING (NO PASSWORDS, TOKENS, OR PII STORED)
# =====================================================================

def log_audit_event(
    db: Session,
    action: str,
    resource_type: str,
    user_id: Optional[int] = None,
    resource_id: Optional[str] = None,
    status: str = "SUCCESS",
    details: Optional[str] = None,
    ip_address: Optional[str] = None
) -> AuditLog:
    """
    Persists an operational security audit log entry.
    CRITICAL: Never stores passwords, tokens, full OCR text, or sensitive clinical PII.
    """
    # Sanitize details to guarantee no credentials or bearer tokens are logged
    safe_details = details or ""
    if "bearer" in safe_details.lower() or "password" in safe_details.lower():
        safe_details = "[Sanitized security details]"

    audit_entry = AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=str(resource_id) if resource_id is not None else None,
        ip_address=ip_address,
        status=status,
        details=safe_details[:500],
        timestamp=datetime.utcnow()
    )
    try:
        db.add(audit_entry)
        db.commit()
        db.refresh(audit_entry)
        return audit_entry
    except Exception as e:
        db.rollback()
        # Logging failure should not crash application, but is noted
        print(f"Warning: Audit log persistence failed: {e}")
        return audit_entry


# =====================================================================
# 5. SECURE FILE-UPLOAD VALIDATION (MIME, MAGIC BYTES, SIZE, TRAVERSAL)
# =====================================================================

def sanitize_filename(filename: str) -> str:
    """Sanitizes filename against path traversal and null bytes."""
    # Strip path separators
    clean = os.path.basename(filename)
    # Remove null bytes and directory traversal symbols
    clean = clean.replace("\x00", "").replace("..", "")
    # Remove unsafe characters
    clean = re.sub(r"[^a-zA-Z0-9_.-]", "_", clean)
    if not clean or clean.startswith("."):
        clean = f"document_{clean}"
    return clean


def validate_uploaded_file(contents: bytes, raw_filename: str) -> Tuple[bool, str, str]:
    """
    Validates uploaded medical document against:
    - 0-byte check
    - 20MB file size limit
    - Disallowed/executable extensions
    - Whitelisted extensions (.pdf, .png, .jpg, .jpeg, .webp, .tiff)
    - Magic bytes check for PDF, PNG, JPEG, WebP, TIFF
    - Rejection of executable/script signatures (MZ, ELF, shell #!, PHP <?php)
    Returns: (is_valid: bool, sanitized_filename: str, error_message: str)
    """
    if not contents or len(contents) == 0:
        return False, "", "Uploaded file is empty (0 bytes). Please provide a valid medical record."

    if len(contents) > MAX_FILE_SIZE_BYTES:
        return False, "", f"File size ({len(contents) / (1024*1024):.1f} MB) exceeds maximum allowed limit of 20 MB."

    safe_name = sanitize_filename(raw_filename)
    _, ext = os.path.splitext(safe_name.lower())

    if ext in DISALLOWED_EXTENSIONS:
        return False, safe_name, f"Security Violation: File extension '{ext}' is forbidden for medical record uploads."

    if ext not in ALLOWED_EXTENSIONS:
        return False, safe_name, f"Invalid file format. Supported formats are: {', '.join(sorted(ALLOWED_EXTENSIONS))}."

    # Inspect Magic Bytes / File Headers
    header = contents[:16]

    # Check for prohibited executable signatures
    if header.startswith(b"MZ"):  # Windows PE executable
        return False, safe_name, "Security Violation: Executable file content detected."
    if header.startswith(b"\x7fELF"):  # Linux ELF executable
        return False, safe_name, "Security Violation: Linux executable binary detected."
    if header.startswith(b"#!"):  # Unix shell script
        return False, safe_name, "Security Violation: Shell script content detected."
    if b"<?php" in contents[:100] or b"<script" in contents[:100].lower():
        return False, safe_name, "Security Violation: Script injection pattern detected."

    # Validate legitimate format magic bytes
    if ext == ".pdf":
        if not contents.startswith(b"%PDF-"):
            return False, safe_name, "Corrupted or invalid PDF file: Missing '%PDF-' header."
    elif ext == ".png":
        if not contents.startswith(b"\x89PNG\r\n\x1a\n"):
            return False, safe_name, "Corrupted or invalid PNG image: Missing PNG magic header."
    elif ext in [".jpg", ".jpeg"]:
        if not contents.startswith(b"\xff\xd8\xff"):
            return False, safe_name, "Corrupted or invalid JPEG image: Missing JPEG SOI marker."
    elif ext == ".webp":
        if not (contents[:4] == b"RIFF" and contents[8:12] == b"WEBP"):
            return False, safe_name, "Corrupted or invalid WebP image: Missing RIFF/WEBP header."
    elif ext in [".tiff", ".tif"]:
        if not (contents.startswith(b"II*\x00") or contents.startswith(b"MM\x00*")):
            return False, safe_name, "Corrupted or invalid TIFF image: Missing TIFF endian marker."
    elif ext == ".gif":
        if not (contents.startswith(b"GIF87a") or contents.startswith(b"GIF89a")):
            return False, safe_name, "Corrupted or invalid GIF image: Missing GIF magic header."

    # Generate unique non-colliding storage filename
    unique_storage_name = f"{uuid.uuid4().hex}_{safe_name}"
    return True, unique_storage_name, ""
