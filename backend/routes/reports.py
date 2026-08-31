import os
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models import MedicalReport, ExtractedEntity
from schemas import MedicalReportResponse
from ai.ocr_engine import ocr_engine
from ai.clinical_bert import clinical_bert_extractor

router = APIRouter(prefix="/reports", tags=["Medical Reports & OCR Analysis"])

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload", response_model=MedicalReportResponse)
async def upload_report(
    file: UploadFile = File(...),
    user_id: int = 1,
    db: Session = Depends(get_db)
):
    contents = await file.read()
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as f:
        f.write(contents)

    # 1. OCR Extraction
    ocr_text = ocr_engine.extract_text(contents, file.filename)

    # 2. ClinicalBERT Entity Extraction
    entities_data = clinical_bert_extractor.extract_entities(ocr_text)
    recommended_specialty = clinical_bert_extractor.predict_recommended_specialty(ocr_text, entities_data)

    # 3. Build Summary & Notes
    summary_notes = f"Extracted {len(entities_data)} medical entities. Recommended clinical specialty: {recommended_specialty}."
    important_obs = f"Patient file successfully ingested. Primary area of concern indicates {recommended_specialty} consultation."

    report = MedicalReport(
        user_id=user_id,
        filename=file.filename,
        file_path=file_path,
        status="COMPLETED",
        ocr_text=ocr_text,
        summary=summary_notes,
        recommended_specialty=recommended_specialty,
        important_notes=important_obs
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

    return report

@router.get("/", response_model=List[MedicalReportResponse])
def get_user_reports(user_id: int = 1, db: Session = Depends(get_db)):
    return db.query(MedicalReport).filter(MedicalReport.user_id == user_id).order_by(MedicalReport.id.desc()).all()

@router.get("/{report_id}", response_model=MedicalReportResponse)
def get_report_detail(report_id: int, db: Session = Depends(get_db)):
    report = db.query(MedicalReport).filter(MedicalReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Medical report not found.")
    return report
