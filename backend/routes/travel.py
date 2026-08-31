from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Hospital, Doctor, Accommodation, TravelPlan
from schemas import TravelPlanRequest, TravelPlanResponse
from ai.astar_navigation import astar_navigator

router = APIRouter(prefix="/travel", tags=["Medical Travel Planner & Navigation"])

@router.post("/plan", response_model=TravelPlanResponse)
def create_travel_plan(req: TravelPlanRequest, user_id: int = 1, db: Session = Depends(get_db)):
    h = db.query(Hospital).filter(Hospital.id == req.hospital_id).first()
    d = db.query(Doctor).filter(Doctor.id == req.doctor_id).first()

    h_name = h.name if h else "Apollo Hospitals"
    d_name = d.name if d else "Dr. K. Srinivas Rao"
    city = h.city if h else "Hyderabad"

    # Multi-day medical travel itinerary generator
    itinerary = [
        {
            "day": 1,
            "title": f"Arrival in {city} & Hotel Check-in",
            "details": f"Fly/Travel from {req.current_location} to {city}. Check into Taj Executive Stays. Rest and hydration ahead of consultation.",
            "location": "Destination City & Hotel"
        },
        {
            "day": 2,
            "title": f"Primary Specialist Consultation at {h_name}",
            "details": f"09:30 AM Appointment with {d_name}. Diagnostic review, ECG, pre-procedural lab tests, and TPA insurance approval verification.",
            "location": h_name
        },
        {
            "day": 3,
            "title": f"Medical Procedure / Treatment Execution",
            "details": f"Admit for {req.medical_condition} treatment procedure under supervision of {d_name}. Post-op monitoring in ICU/Deluxe Suite.",
            "location": f"{h_name} IPD Unit"
        },
        {
            "day": 4,
            "title": "Hospital Discharge & Prescription Dispensing",
            "details": f"Discharge summary issued. Medication collection at 24/7 Pharmacy. Return to hotel for post-procedure recovery.",
            "location": "Hospital & Hotel"
        },
        {
            "day": 5,
            "title": "Post-Op Clearance & Return Journey",
            "details": f"Final fit-to-travel evaluation. Transfer from hotel to airport/station for return travel home.",
            "location": "Airport / Railway Hub"
        }
    ]

    total_est = 125000.0 if "cardio" in req.medical_condition.lower() else 95000.0

    plan_db = TravelPlan(
        user_id=user_id,
        destination_city=city,
        hospital_id=req.hospital_id,
        doctor_id=req.doctor_id,
        start_date=req.preferred_travel_date,
        duration_days=req.duration_days,
        itinerary_json=itinerary,
        total_estimated_cost=total_est
    )
    db.add(plan_db)
    db.commit()
    db.refresh(plan_db)

    return {
        "id": plan_db.id,
        "destination_city": city,
        "hospital_name": h_name,
        "doctor_name": d_name,
        "start_date": req.preferred_travel_date,
        "duration_days": req.duration_days,
        "itinerary": itinerary,
        "total_estimated_cost": total_est
    }

@router.get("/navigate")
def get_astar_navigation_route(origin: str = "Airport", destination: str = "Hospital"):
    return astar_navigator.plan_route(origin, destination)

@router.get("/accommodations")
def get_accommodations_near_hospital(hospital_id: int = 1, db: Session = Depends(get_db)):
    accs = db.query(Accommodation).filter(Accommodation.hospital_id == hospital_id).all()
    if not accs:
        accs = db.query(Accommodation).all()
    return accs
