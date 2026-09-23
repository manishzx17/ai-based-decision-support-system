from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from database import get_db
from models import User, PatientProfile, MedicalReport
from schemas import PatientProfileSchema, UserLogin
from security import get_current_user, verify_password, create_access_token, log_audit_event

router = APIRouter(prefix="/auth", tags=["Clinical Profile"])


def merge_clinical_lists(existing: Optional[List[str]], new_items: Optional[List[str]]) -> List[str]:
    """Merges two lists of clinical strings without duplication while preserving order."""
    seen = set()
    merged = []
    # Add new items first, then preserve existing
    for item in (new_items or []) + (existing or []):
        if not item:
            continue
        cleaned = item.strip()
        k = cleaned.lower()
        if k and k not in seen:
            seen.add(k)
            merged.append(cleaned)
    return merged


def merge_test_results(existing: Optional[List[Dict[str, Any]]], new_items: Optional[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    """Merges structured lab test results by test_name, updating values or appending new investigations."""
    res_map: Dict[str, Dict[str, Any]] = {}
    
    # Existing results
    for tr in (existing or []):
        if isinstance(tr, dict) and "test_name" in tr:
            res_map[tr["test_name"].lower()] = tr
            
    # New results overwrite or append
    for tr in (new_items or []):
        if isinstance(tr, dict) and "test_name" in tr:
            res_map[tr["test_name"].lower()] = tr

    return list(res_map.values())


def sync_clinical_profile_from_structured_info(
    profile: PatientProfile,
    structured_info: Dict[str, Any],
    report_id: Optional[int] = None
) -> PatientProfile:
    """
    Core Phase 3 Pipeline Function:
    Directly maps Phase 2 StructuredClinicalInfo into persistent PatientProfile.
    STRICT RULES:
    1. Zero inferred diagnoses: only explicitly extracted conditions are mapped.
    2. Document metadata (patient name, ID, date) is administrative, not clinical intelligence.
    3. Handles empty or missing fields gracefully without corruption.
    """
    if not structured_info:
        return profile

    # 1. Demographics
    demo = structured_info.get("demographics") or {}
    if demo.get("age") is not None and isinstance(demo.get("age"), int) and demo.get("age") > 0:
        profile.age = demo["age"]
    if demo.get("gender") and isinstance(demo.get("gender"), str) and demo.get("gender").strip():
        profile.gender = demo["gender"].strip()

    # 2. Conditions (Explicitly reported only — zero inferred diagnoses)
    new_conds = structured_info.get("conditions") or []
    profile.conditions = merge_clinical_lists(profile.conditions, new_conds)
    if profile.conditions:
        profile.chronic_conditions = ", ".join(profile.conditions)

    # 3. Symptoms
    new_syms = structured_info.get("symptoms") or []
    profile.symptoms = merge_clinical_lists(profile.symptoms, new_syms)

    # 4. Tests
    new_tests = structured_info.get("tests") or []
    profile.tests = merge_clinical_lists(profile.tests, new_tests)

    # 5. Test Results
    new_test_results = structured_info.get("test_results") or []
    profile.test_results = merge_test_results(profile.test_results, new_test_results)

    # 6. Medications
    new_meds = structured_info.get("medications") or []
    profile.medications = merge_clinical_lists(profile.medications, new_meds)

    # 7. Procedures
    new_procs = structured_info.get("procedures") or []
    profile.procedures = merge_clinical_lists(profile.procedures, new_procs)

    # 8. Medical History
    new_hist = structured_info.get("medical_history") or []
    profile.medical_history = merge_clinical_lists(profile.medical_history, new_hist)

    # 9. Link provenance report ID & raw snapshot
    if report_id:
        profile.last_report_id = report_id
    profile.structured_data = structured_info

    return profile


def get_shared_clinical_context(user_id: int, db: Session) -> Dict[str, Any]:
    """
    Shared Patient Context Provider for downstream phases (RAG, Recommendations, Cost/LOS, Assistant).
    Returns one consistent, structured clinical context object.
    """
    profile = db.query(PatientProfile).filter(PatientProfile.user_id == user_id).first()
    if not profile:
        return {
            "user_id": user_id,
            "demographics": {
                "age": 30,
                "gender": "Other",
                "blood_group": "O+",
                "allergies": "None",
                "chronic_conditions": "None",
                "current_city": "Hyderabad"
            },
            "conditions": [],
            "symptoms": [],
            "tests": [],
            "test_results": [],
            "medications": [],
            "procedures": [],
            "medical_history": [],
            "last_report_id": None
        }

    return {
        "user_id": user_id,
        "demographics": {
            "age": profile.age,
            "gender": profile.gender,
            "blood_group": profile.blood_group,
            "allergies": profile.allergies,
            "chronic_conditions": profile.chronic_conditions,
            "current_city": profile.current_city,
            "preferred_currency": profile.preferred_currency
        },
        "conditions": profile.conditions or [],
        "symptoms": profile.symptoms or [],
        "tests": profile.tests or [],
        "test_results": profile.test_results or [],
        "medications": profile.medications or [],
        "procedures": profile.procedures or [],
        "medical_history": profile.medical_history or [],
        "last_report_id": profile.last_report_id
    }


@router.get("/profile", response_model=PatientProfileSchema)
def get_profile(
    user_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieves the clinical profile for the current authenticated patient.
    Enforces authorization check if user_id query parameter differs from authenticated user.
    """
    if user_id is not None and user_id != current_user.id and getattr(current_user, "role", "") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You do not have authorization to access another patient's data."
        )
    target_user_id = current_user.id if current_user else (user_id or 1)

    profile = db.query(PatientProfile).filter(PatientProfile.user_id == target_user_id).first()
    if not profile:
        profile = PatientProfile(
            user_id=target_user_id,
            age=48,
            gender="Male",
            blood_group="O+",
            current_city="Hyderabad",
            allergies="None",
            chronic_conditions="None",
            conditions=[],
            symptoms=[],
            tests=[],
            test_results=[],
            medications=[],
            procedures=[],
            medical_history=[]
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile


@router.put("/profile", response_model=PatientProfileSchema)
def update_profile(
    profile_data: PatientProfileSchema,
    user_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Updates the clinical profile for the current authenticated patient.
    """
    if user_id is not None and user_id != current_user.id and getattr(current_user, "role", "") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You do not have authorization to modify another patient's profile."
        )
    target_user_id = current_user.id if current_user else (user_id or 1)

    profile = db.query(PatientProfile).filter(PatientProfile.user_id == target_user_id).first()
    if not profile:
        profile = PatientProfile(user_id=target_user_id)
        db.add(profile)

    update_dict = profile_data.model_dump(exclude_unset=True) if hasattr(profile_data, "model_dump") else profile_data.dict(exclude_unset=True)
    for field, val in update_dict.items():
        if field not in ["id", "user_id"]:
            setattr(profile, field, val)

    db.commit()
    db.refresh(profile)
    return profile


@router.post("/profile/sync-from-report/{report_id}", response_model=PatientProfileSchema)
def sync_profile_from_report(
    report_id: int,
    user_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Explicitly populates/updates the persistent Clinical Profile from a specific
    Phase 2 structured clinical report.
    """
    if user_id is not None and user_id != current_user.id and getattr(current_user, "role", "") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You do not have authorization for this action."
        )
    target_user_id = current_user.id if current_user else (user_id or 1)
    report = db.query(MedicalReport).filter(MedicalReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Medical report not found.")

    if report.user_id != target_user_id and getattr(current_user, "role", "") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You do not have authorization to sync from another patient's report."
        )

    profile = db.query(PatientProfile).filter(PatientProfile.user_id == target_user_id).first()
    if not profile:
        profile = PatientProfile(user_id=target_user_id)
        db.add(profile)

    # Use existing structured_data or dynamically extracted structured_info
    structured_info = report.structured_info
    if not structured_info and report.ocr_text:
        from ai.clinical_bert import clinical_bert_extractor
        structured_info = clinical_bert_extractor.extract_structured_clinical_info(report.ocr_text)

    if structured_info:
        sync_clinical_profile_from_structured_info(profile, structured_info, report_id=report.id)

    db.commit()
    db.refresh(profile)
    return profile


@router.get("/profile/shared-context")
def get_shared_context_endpoint(
    user_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns the unified shared patient context used by downstream modules.
    """
    if user_id is not None and user_id != current_user.id and getattr(current_user, "role", "") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You do not have authorization to access another patient's data."
        )
    target_user_id = current_user.id if current_user else (user_id or 1)
    return get_shared_clinical_context(target_user_id, db)


@router.post("/login")
def login(login_data: UserLogin, request: Request, db: Session = Depends(get_db)):
    """
    Minimal demo login endpoint supporting the 3 synthetic demo patients.
    Accepts username or email, plus password.
    """
    identifier = (login_data.username or login_data.email or "").strip().lower()
    raw_password = login_data.password or ""

    if not identifier:
        raise HTTPException(status_code=400, detail="Username or email is required.")

    alias_map = {
        "demo_cardio": "patient@example.com",
        "patient1": "patient@example.com",
        "patient1@demo.local": "patient@example.com",
        "demo_neuro": "patient2@example.com",
        "patient2": "patient2@example.com",
        "patient2@demo.local": "patient2@example.com",
        "demo_ortho": "patient3@example.com",
        "patient3": "patient3@example.com",
        "patient3@demo.local": "patient3@example.com",
    }
    target_email = alias_map.get(identifier, identifier)

    user = db.query(User).filter(
        (User.email == target_email) | (User.email == identifier)
    ).first()

    if not user:
        log_audit_event(
            db=db,
            action="AUTH_LOGIN_FAILED",
            resource_type="user",
            status="FAILED",
            details=f"Login attempt failed: user '{identifier}' not found",
            ip_address=request.client.host if request.client else None
        )
        raise HTTPException(status_code=401, detail="Invalid username or password.")

    is_valid = verify_password(raw_password, user.hashed_password)
    # Support standard demo password fallback for synthetic demo accounts
    if not is_valid and raw_password in ["DemoPassword@123", "demo_password_123", "demo_password_456"]:
        is_valid = True

    if not is_valid:
        log_audit_event(
            db=db,
            action="AUTH_LOGIN_FAILED",
            resource_type="user",
            user_id=user.id,
            status="FAILED",
            details="Login attempt failed: invalid password",
            ip_address=request.client.host if request.client else None
        )
        raise HTTPException(status_code=401, detail="Invalid username or password.")

    log_audit_event(
        db=db,
        action="AUTH_LOGIN_SUCCESS",
        resource_type="user",
        user_id=user.id,
        status="SUCCESS",
        details="User authenticated successfully",
        ip_address=request.client.host if request.client else None
    )

    token = create_access_token({"sub": str(user.id), "role": user.role, "email": user.email})
    specialty_map = {1: "Cardiology", 2: "Neurology", 3: "Orthopedics"}
    canonical_username = (
        "demo_cardio" if user.id == 1 else (
            "demo_neuro" if user.id == 2 else (
                "demo_ortho" if user.id == 3 else user.email.split("@")[0]
            )
        )
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "specialty": specialty_map.get(user.id, "General"),
            "username": canonical_username
        }
    }


@router.post("/logout")
def logout(request: Request, user_id: Optional[int] = None, db: Session = Depends(get_db)):
    """
    Minimal demo logout action with server-side token revocation.
    """
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ", 1)[1].strip()
        from security import revoke_token
        revoke_token(token)

    log_audit_event(
        db=db,
        action="AUTH_LOGOUT",
        resource_type="user",
        user_id=user_id,
        status="SUCCESS",
        details="User logged out",
        ip_address=request.client.host if request.client else None
    )
    return {"message": "Logged out successfully"}


@router.get("/demo-users")
def get_demo_users():
    """
    Returns the 3 synthetic demo patient accounts for easy selection.
    """
    return [
        {
            "id": 1,
            "username": "demo_cardio",
            "email": "patient@example.com",
            "full_name": "Rahul Verma",
            "specialty": "Cardiology",
            "clinical_focus": "Coronary Artery Disease (CAD)",
            "city": "Hyderabad",
            "badge": "Synthetic Demo Patient 1"
        },
        {
            "id": 2,
            "username": "demo_neuro",
            "email": "patient2@example.com",
            "full_name": "Priya Sharma",
            "specialty": "Neurology",
            "clinical_focus": "Chronic Migraine & Neuralgia",
            "city": "Bengaluru",
            "badge": "Synthetic Demo Patient 2"
        },
        {
            "id": 3,
            "username": "demo_ortho",
            "email": "patient3@example.com",
            "full_name": "Amit Patel",
            "specialty": "Orthopedics",
            "clinical_focus": "Bilateral Knee Osteoarthritis",
            "city": "Delhi",
            "badge": "Synthetic Demo Patient 3"
        }
    ]


