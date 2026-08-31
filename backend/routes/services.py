from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from models import (
    Pharmacy, InsuranceProvider, EmergencyContact,
    Appointment, Conversation, ChatMessage, MedicalKnowledge, MedicalReport
)
from schemas import (
    AppointmentCreate, AppointmentSchema, SymptomGuidanceRequest,
    SymptomGuidanceResponse, TranslationRequest, TranslationResponse,
    ChatRequest, ChatResponse
)
from ai.rag_engine import rag_engine
from ai.translator import medical_translator

router = APIRouter(prefix="/services", tags=["Healthcare Services & AI Support"])

# 1. Pharmacies
@router.get("/pharmacies")
def get_pharmacies(city: str = "Hyderabad", db: Session = Depends(get_db)):
    return db.query(Pharmacy).filter(Pharmacy.city.ilike(f"%{city}%")).all() or db.query(Pharmacy).all()

# 2. Insurance Help
@router.get("/insurance")
def get_insurance_providers(db: Session = Depends(get_db)):
    return db.query(InsuranceProvider).all()

# 3. Emergency Assistance & Contacts
@router.get("/emergency")
def get_emergency_services(city: str = "Hyderabad", db: Session = Depends(get_db)):
    contacts = db.query(EmergencyContact).filter(EmergencyContact.city.ilike(f"%{city}%")).all() or db.query(EmergencyContact).all()
    return {
        "emergency_number": "108",
        "ambulance": "+91 40 1066",
        "trauma_centers": contacts,
        "location_status": f"Active GPS Location in {city}",
        "disclaimer": "FOR IMMEDIATE LIFE-THREATENING EMERGENCY, CALL 108 OR PROCEED TO NEAREST TRAUMA CENTER."
    }

# 4. Appointments
@router.post("/appointments", response_model=AppointmentSchema)
def book_appointment(apt: AppointmentCreate, user_id: int = 1, db: Session = Depends(get_db)):
    new_apt = Appointment(
        user_id=user_id,
        hospital_id=apt.hospital_id,
        doctor_id=apt.doctor_id,
        patient_name=apt.patient_name,
        appointment_date=apt.appointment_date,
        appointment_time=apt.appointment_time,
        status="CONFIRMED",
        reason=apt.reason
    )
    db.add(new_apt)
    db.commit()
    db.refresh(new_apt)
    return new_apt

@router.get("/appointments", response_model=List[AppointmentSchema])
def get_my_appointments(user_id: int = 1, db: Session = Depends(get_db)):
    return db.query(Appointment).filter(Appointment.user_id == user_id).order_by(Appointment.id.desc()).all()

# 5. Symptom Guidance
@router.post("/symptoms", response_model=SymptomGuidanceResponse)
def check_symptoms(req: SymptomGuidanceRequest):
    stext = req.symptoms_text.lower()
    
    if "chest pain" in stext or "severe pressure" in stext or "fainting" in stext:
        urgency = "EMERGENCY"
        spec = "Emergency Cardiology"
        actions = ["CALL 108 IMMEDIATELY", "Do not drive yourself to hospital", "Chew Aspirin 300mg if advised by paramedic"]
    elif "breath" in stext or "headache" in stext or "dizziness" in stext:
        urgency = "URGENT"
        spec = "Cardiology / Neurology"
        actions = ["Schedule specialist consultation within 24-48 hours", "Avoid strenuous physical activity", "Keep blood pressure log"]
    else:
        urgency = "MODERATE"
        spec = "General Medicine / Orthopedics"
        actions = ["Book routine outpatient consultation", "Monitor symptom progression"]

    return {
        "summary": f"Symptoms evaluated: '{req.symptoms_text}' over {req.duration}.",
        "urgency_level": urgency,
        "recommended_specialty": spec,
        "guidance_notes": [
            f"Evaluated urgency level: {urgency}",
            f"Primary specialty alignment: {spec}",
            "Patient should present recent diagnostic reports during consultation"
        ],
        "suggested_actions": actions,
        "disclaimer": "AI Symptom guidance is for triage decision support only. Consult a doctor for diagnosis."
    }

# 6. Medical Translation
@router.post("/translate", response_model=TranslationResponse)
def translate_text(req: TranslationRequest):
    return medical_translator.translate(req.text, req.source_lang, req.target_lang)

# 7. AI Healthcare Assistant (Conversational RAG)
@router.post("/chat", response_model=ChatResponse)
def ai_assistant_chat(req: ChatRequest, user_id: int = 1, db: Session = Depends(get_db)):
    # Fetch user conversation or create new
    if not req.conversation_id:
        conv = Conversation(user_id=user_id, title=req.message[:30])
        db.add(conv)
        db.commit()
        db.refresh(conv)
        conv_id = conv.id
    else:
        conv_id = req.conversation_id

    # Save user message
    u_msg = ChatMessage(conversation_id=conv_id, sender="user", text=req.message)
    db.add(u_msg)
    db.commit()

    # Load report context if available
    report_ctx = ""
    if req.report_id:
        rep = db.query(MedicalReport).filter(MedicalReport.id == req.report_id).first()
        if rep:
            report_ctx = f"Report: {rep.filename} | Specialty: {rep.recommended_specialty} | Summary: {rep.summary}"
    else:
        latest_rep = db.query(MedicalReport).filter(MedicalReport.user_id == user_id).order_by(MedicalReport.id.desc()).first()
        if latest_rep:
            report_ctx = f"Report: {latest_rep.filename} | Specialty: {latest_rep.recommended_specialty} | Summary: {latest_rep.summary}"

    # Fetch knowledge base for RAG
    kb_docs = db.query(MedicalKnowledge).all()
    kb_dicts = [
        {"id": k.id, "title": k.title, "category": k.category, "content": k.content, "keywords": k.keywords, "source_reference": k.source_reference}
        for k in kb_docs
    ]

    retrieved = rag_engine.retrieve_documents(req.message, kb_dicts, top_k=2)
    rag_res = rag_engine.generate_response(req.message, retrieved, report_ctx)

    # Save assistant message
    a_msg = ChatMessage(conversation_id=conv_id, sender="assistant", text=rag_res["reply"])
    db.add(a_msg)
    db.commit()

    return {
        "reply": rag_res["reply"],
        "conversation_id": conv_id,
        "citations": rag_res["citations"],
        "disclaimer": "AI-generated medical response. Verify with a registered healthcare professional."
    }

# 8. Local Health Information
@router.get("/local-health")
def get_local_health_info(city: str = "Hyderabad", db: Session = Depends(get_db)):
    return {
        "city": city,
        "advisories": [
            "Seasonal Dengue & Viral Fever Precaution: Stay hydrated and use mosquito repellent.",
            "International Traveler Vaccination Center available at Airport Health Office.",
            "Clean Water & Sanitize Standards compliant across all accredited medical centers."
        ],
        "blood_banks": [
            {"name": "Central Red Cross Blood Bank", "phone": "+91 40 2320 2345", "address": "Lakdikapul, Hyderabad"},
            {"name": "Chiranjeevi Blood Bank", "phone": "+91 40 2355 4545", "address": "Jubilee Hills, Hyderabad"}
        ],
        "diagnostic_centers": [
            {"name": "Vijaya Diagnostic Centre", "rating": 4.8, "address": "Somajiguda, Hyderabad"},
            {"name": "Lucid Medical Diagnostics", "rating": 4.7, "address": "Banjara Hills, Hyderabad"}
        ]
    }
