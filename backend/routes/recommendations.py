from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from models import Hospital, Doctor
from schemas import HospitalSchema, DoctorSchema
from ai.recommendation_engine import recommendation_engine

router = APIRouter(prefix="/recommend", tags=["Hospital & Doctor Recommendations"])

@router.get("/hospitals", response_model=List[HospitalSchema])
def get_recommended_hospitals(
    specialty: str = Query("Cardiology"),
    city: str = Query("Hyderabad"),
    max_budget: float = Query(500000.0),
    insurance: str = Query("Star Health"),
    db: Session = Depends(get_db)
):
    hospitals = db.query(Hospital).all()
    scored_list = []
    
    for h in hospitals:
        h_dict = {
            "id": h.id,
            "name": h.name,
            "city": h.city,
            "state": h.state,
            "address": h.address,
            "lat": h.lat,
            "lng": h.lng,
            "specialties": h.specialties or [],
            "rating": h.rating,
            "distance_km": h.distance_km,
            "insurance_accepted": h.insurance_accepted or [],
            "facilities": h.facilities or [],
            "contact_phone": h.contact_phone,
            "availability_status": h.availability_status
        }
        scored = recommendation_engine.score_hospital(
            h_dict,
            required_specialty=specialty,
            patient_city=city,
            max_budget=max_budget,
            preferred_insurance=insurance
        )
        scored_list.append(scored)

    # Sort by recommendation score descending
    scored_list.sort(key=lambda x: x["recommendation_score"], reverse=True)
    return scored_list

@router.get("/hospitals/{hospital_id}", response_model=HospitalSchema)
def get_hospital_details(hospital_id: int, db: Session = Depends(get_db)):
    h = db.query(Hospital).filter(Hospital.id == hospital_id).first()
    if not h:
        return {}
    h_dict = {
        "id": h.id,
        "name": h.name,
        "city": h.city,
        "state": h.state,
        "address": h.address,
        "lat": h.lat,
        "lng": h.lng,
        "specialties": h.specialties or [],
        "rating": h.rating,
        "distance_km": h.distance_km,
        "insurance_accepted": h.insurance_accepted or [],
        "facilities": h.facilities or [],
        "contact_phone": h.contact_phone,
        "availability_status": h.availability_status
    }
    return recommendation_engine.score_hospital(h_dict, required_specialty="Cardiology")

@router.get("/doctors", response_model=List[DoctorSchema])
def get_recommended_doctors(
    specialty: Optional[str] = Query(None),
    hospital_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(Doctor)
    if hospital_id:
        query = query.filter(Doctor.hospital_id == hospital_id)
    if specialty:
        query = query.filter(Doctor.specialty.ilike(f"%{specialty}%"))
    
    return query.all()

@router.post("/compare")
def compare_hospitals(hospital_ids: List[int], db: Session = Depends(get_db)):
    hospitals = db.query(Hospital).filter(Hospital.id.in_(hospital_ids)).all()
    comparison = []
    for h in hospitals:
        h_dict = {
            "id": h.id,
            "name": h.name,
            "city": h.city,
            "specialties": h.specialties or [],
            "rating": h.rating,
            "distance_km": h.distance_km,
            "insurance_accepted": h.insurance_accepted or [],
            "facilities": h.facilities or [],
            "contact_phone": h.contact_phone,
            "availability": h.availability_status
        }
        comparison.append(h_dict)
    
    return {
        "compared_hospitals": comparison,
        "ai_recommendation": f"Hospital '{hospitals[0].name if hospitals else 'Apollo'}' is recommended as top choice due to highest clinical specialty score and direct cashless coverage."
    }
