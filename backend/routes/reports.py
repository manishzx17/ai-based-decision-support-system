import os
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Request, status
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from models import MedicalReport, ExtractedEntity, User, AuditLog
from schemas import MedicalReportResponse, AuditLogSchema
from ai.ocr_engine import ocr_engine
from ai.clinical_bert import clinical_bert_extractor
from ai.rag_engine import rag_engine
from security import (
    get_current_user, validate_uploaded_file, log_audit_event
)

router = APIRouter(prefix="/reports", tags=["Medical Reports & OCR Analysis"])

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/upload", response_model=MedicalReportResponse)
async def upload_report(
    request: Request,
    file: UploadFile = File(...),
    user_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if user_id is not None and user_id != current_user.id and getattr(current_user, "role", "") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You do not have authorization to upload reports for another patient."
        )
    target_user_id = current_user.id if current_user else (user_id or 1)

    contents = await file.read()

    # 1. Strict Security Validation: Extension, Magic Bytes, File Size, Traversal Sanitization
    is_valid, unique_filename, error_msg = validate_uploaded_file(contents, file.filename or "medical_report.pdf")
    if not is_valid:
        log_audit_event(
            db=db,
            action="REPORT_UPLOAD_REJECTED",
            resource_type="medical_report",
            user_id=target_user_id,
            status="REJECTED",
            details=f"File validation failure for '{file.filename}': {error_msg[:100]}",
            ip_address=request.client.host if request.client else None
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )

    # Secure storage using unique UUID-based filename
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    with open(file_path, "wb") as f:
        f.write(contents)

    # 2. OCR Extraction (Genuine PDF / image extraction with preprocessing)
    ocr_text = ocr_engine.extract_text(contents, file.filename or unique_filename)

    # 3. Validation & Quality Check
    is_ocr_valid, validation_msg = ocr_engine.validate_extracted_text(ocr_text)

    if not is_ocr_valid:
        report = MedicalReport(
            user_id=target_user_id,
            filename=file.filename or unique_filename,
            file_path=file_path,
            status="FAILED",
            ocr_text=ocr_text if ocr_text else "[Unusable or unreadable document: Extracted OCR text is too sparse or corrupted to reliably identify clinical entities.]",
            summary=f"Ingestion Warning: {validation_msg}",
            recommended_specialty="General Medicine",
            important_notes=f"Document validation failed: {validation_msg}. Please ensure the report is clearly legible and properly oriented."
        )
        db.add(report)
        db.commit()
        db.refresh(report)

        log_audit_event(
            db=db,
            action="REPORT_UPLOAD",
            resource_type="medical_report",
            user_id=target_user_id,
            resource_id=str(report.id),
            status="FAILED",
            details=f"OCR quality check failed: {validation_msg[:100]}",
            ip_address=request.client.host if request.client else None
        )
        return report

    # 4. Biomedical Transformer Entity Extraction (d4data/biomedical-ner-all)
    entities_data = clinical_bert_extractor.extract_entities(ocr_text)
    recommended_specialty = clinical_bert_extractor.predict_recommended_specialty(ocr_text, entities_data)
    structured_info_dict = clinical_bert_extractor.extract_structured_clinical_info(ocr_text)

    # 5. Genuine Semantic RAG Guideline Grounding (Contextualized with Patient Profile)
    from routes.auth import get_shared_clinical_context
    user_clinical_profile = get_shared_clinical_context(target_user_id, db)
    rag_grounding = rag_engine.ground_report_analysis(
        ocr_text,
        entities_data,
        recommended_specialty,
        clinical_profile=user_clinical_profile
    )

    # 6. Build Structured Dynamic Summary
    diseases = [e["entity_name"] for e in entities_data if e["entity_type"] == "Disease"]
    procedures = [e["entity_name"] for e in entities_data if e["entity_type"] == "Procedure"]
    tests = [e["entity_name"] for e in entities_data if e["entity_type"] == "TestResult"]
    meds = [e["entity_name"] for e in entities_data if e["entity_type"] == "Medication"]

    summary_parts = [f"Clinical report processed under {recommended_specialty}."]
    if diseases:
        summary_parts.append(f"Primary clinical findings indicate: {', '.join(diseases[:3])}.")
    if tests:
        summary_parts.append(f"Key test values: {', '.join(tests[:3])}.")
    if procedures:
        summary_parts.append(f"Recommended/performed procedures: {', '.join(procedures[:2])}.")
    if meds:
        summary_parts.append(f"Active medications: {', '.join(meds[:3])}.")

    summary_notes = " ".join(summary_parts)
    important_obs = f"Extracted {len(entities_data)} structured clinical entities from document content. Grounded with verified clinical guidelines."

    report = MedicalReport(
        user_id=target_user_id,
        filename=file.filename or unique_filename,
        file_path=file_path,
        status="COMPLETED",
        ocr_text=ocr_text,
        summary=summary_notes,
        recommended_specialty=recommended_specialty,
        important_notes=important_obs,
        grounding_notes=rag_grounding["grounding_notes"],
        grounding_sources=rag_grounding["grounding_sources"],
        structured_data=structured_info_dict
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    # Save entities
    for ent in entities_data:
        entity_obj = ExtractedEntity(
            report_id=report.id,
            entity_type=ent["entity_type"],
            entity_name=ent["entity_name"],
            confidence=ent["confidence"],
            context_snippet=ent["context_snippet"]
        )
        db.add(entity_obj)

    db.commit()
    db.refresh(report)

    # Phase 3: Synchronize Phase 2 StructuredClinicalInfo into persistent PatientProfile
    from models import PatientProfile
    from routes.auth import sync_clinical_profile_from_structured_info

    profile = db.query(PatientProfile).filter(PatientProfile.user_id == target_user_id).first()
    if not profile:
        profile = PatientProfile(user_id=target_user_id)
        db.add(profile)
    sync_clinical_profile_from_structured_info(profile, structured_info_dict, report_id=report.id)
    db.commit()

    log_audit_event(
        db=db,
        action="REPORT_UPLOAD",
        resource_type="medical_report",
        user_id=target_user_id,
        resource_id=str(report.id),
        status="SUCCESS",
        details=f"Report uploaded successfully ({len(contents)} bytes, {len(entities_data)} entities)",
        ip_address=request.client.host if request.client else None
    )

    return report


@router.get("/", response_model=List[MedicalReportResponse])
def get_user_reports(
    user_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns medical reports strictly belonging to the authenticated user.
    Enforces strict IDOR protection if a caller attempts to request another user's reports.
    """
    if user_id is not None and user_id != current_user.id and getattr(current_user, "role", "") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You do not have authorization to access another patient's reports."
        )
    target_user_id = current_user.id if current_user else (user_id or 1)
    return (
        db.query(MedicalReport)
        .filter(MedicalReport.user_id == target_user_id)
        .order_by(MedicalReport.id.desc())
        .all()
    )


@router.get("/audit-logs", response_model=List[AuditLogSchema])
def get_audit_logs(
    scope: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns audit log history.
    """
    if scope in ["all", "system"]:
        if getattr(current_user, "role", "") != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: Administrative privileges required to view system-wide audit logs."
            )
        return db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(100).all()

    return (
        db.query(AuditLog)
        .filter(AuditLog.user_id == current_user.id)
        .order_by(AuditLog.timestamp.desc())
        .limit(50)
        .all()
    )


@router.get("/{report_id}", response_model=MedicalReportResponse)
def get_report_detail(
    report_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieves detailed clinical analysis for a single medical report.
    """
    report = db.query(MedicalReport).filter(MedicalReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Medical report not found.")

    if report.user_id != current_user.id and getattr(current_user, "role", "") != "admin":
        log_audit_event(
            db=db,
            action="REPORT_ACCESS_DENIED",
            resource_type="medical_report",
            user_id=current_user.id,
            resource_id=str(report_id),
            status="DENIED",
            details=f"User {current_user.id} attempted to access user {report.user_id} report",
            ip_address=request.client.host if request.client else None
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You do not have authorization to access this patient's medical report."
        )

    log_audit_event(
        db=db,
        action="REPORT_VIEW",
        resource_type="medical_report",
        user_id=current_user.id,
        resource_id=str(report_id),
        status="SUCCESS",
        details=f"Report viewed by authorized owner",
        ip_address=request.client.host if request.client else None
    )

    return report
