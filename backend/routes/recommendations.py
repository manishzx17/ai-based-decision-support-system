from fastapi import APIRouter, Depends, Query, HTTPException, Body
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any, Union
from database import get_db
from models import User, Hospital, Doctor, PatientProfile, MedicalReport, ExtractedEntity
from schemas import (
    HospitalSchema, DoctorSchema, TreatmentRecommendationResponse, TreatmentPathwaySchema,
    PersonalizedRecommendationRequest, PersonalizedRecommendationResponse, PatientPreferencesSchema
)
from ai.recommendation_engine import recommendation_engine
from security import get_current_user

router = APIRouter(prefix="/recommend", tags=["Hospital, Doctor & Treatment Recommendations"])

def _hospital_to_dict(h: Hospital) -> Dict[str, Any]:
    return {
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
        "availability_status": h.availability_status,
        "cost_tier": h.cost_tier or "Moderate",
        "quality_rating": h.quality_rating or h.rating or 4.5,
        "accreditation": h.accreditation or "NABH Accredited",
        "treatment_capabilities": h.treatment_capabilities or [],
        "icu_beds": h.icu_beds or 50,
        "emergency_24x7": h.emergency_24x7 if h.emergency_24x7 is not None else True,
        "estimated_cost_tier": h.estimated_cost_tier or 320000.0,
        "provenance": h.provenance
    }

def _doctor_to_dict(d: Doctor, hosp_dict: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    return {
        "id": d.id,
        "hospital_id": d.hospital_id,
        "name": d.name,
        "specialty": d.specialty,
        "experience_years": d.experience_years,
        "qualification": d.qualification,
        "rating": d.rating,
        "consultation_fee": d.consultation_fee,
        "availability_days": d.availability_days,
        "expertise": d.expertise or [],
        "hospital_name": hosp_dict.get("name") if hosp_dict else None,
        "hospital_city": hosp_dict.get("city") if hosp_dict else None,
        "provenance": d.provenance
    }

@router.post("/personalized", response_model=PersonalizedRecommendationResponse)
def get_personalized_recommendations_endpoint(
    req: PersonalizedRecommendationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Phase 5 Unified Personalized Decision Support Endpoint.
    Integrates Phase 3 Clinical Profile + Explicit Preferences to generate:
    - Ranked accredited hospitals with transparent 35/25/20/20 scoring & weight breakdowns.
    - Matched clinical specialists with subspecialty expertise scoring.
    - Evidence-grounded treatment pathways from Phase 4 RAG guidelines (ESC, ACC, AAOS, NCCN, etc.).
    - Stage 1 eligibility filtering audit.
    """
    if req.user_id is not None and req.user_id != current_user.id and getattr(current_user, "role", "") != "admin":
        raise HTTPException(
            status_code=403,
            detail="Forbidden: You do not have authorization to access another patient's recommendations."
        )
    target_user_id = current_user.id

    # 1. Resolve clinical profile
    clinical_profile = req.clinical_profile or {}
    if not clinical_profile:
        profile = db.query(PatientProfile).filter(PatientProfile.user_id == target_user_id).first()
        if profile:
            clinical_profile = {
                "conditions": profile.conditions or ([c.strip() for c in profile.chronic_conditions.split(",")] if profile.chronic_conditions and profile.chronic_conditions.lower() != "none" else []),
                "symptoms": profile.symptoms or [],
                "procedures": profile.procedures or [],
                "current_city": profile.current_city or "Hyderabad",
                "recommended_specialty": "Cardiology"
            }
            # Also check latest report belonging to authenticated user
            latest_report = db.query(MedicalReport).filter(MedicalReport.user_id == target_user_id).order_by(MedicalReport.id.desc()).first()
            if latest_report:
                if latest_report.recommended_specialty:
                    clinical_profile["recommended_specialty"] = latest_report.recommended_specialty
                if latest_report.entities:
                    ents = [e.entity_name for e in latest_report.entities if e.entity_type in ["Disease", "Symptom"]]
                    clinical_profile["conditions"] = list(set(clinical_profile.get("conditions", []) + ents))

    # 2. Fetch all hospitals and doctors from DB
    hospitals = db.query(Hospital).all()
    hospital_dicts = [_hospital_to_dict(h) for h in hospitals]

    doctors = db.query(Doctor).all()
    hosp_map = {h["id"]: h for h in hospital_dicts}
    doctor_dicts = [_doctor_to_dict(d, hosp_map.get(d.hospital_id)) for d in doctors]

    preferences_dict = req.preferences.dict() if req.preferences else {}

    # 3. Call recommendation engine
    engine_result = recommendation_engine.get_personalized_recommendations(
        clinical_profile=clinical_profile,
        preferences=preferences_dict,
        all_hospitals=hospital_dicts,
        all_doctors=doctor_dicts,
        top_k_hospitals=req.top_hospitals or 5,
        top_k_doctors=req.top_doctors or 5,
        top_k_pathways=req.top_pathways or 3
    )

    audit_items = []
    for item in engine_result.get("eligibility_audit", []):
        audit_items.append({
            "provider_id": item.get("id", 0),
            "name": item.get("name", ""),
            "entity_type": item.get("provider_type", "hospital"),
            "eligible": item.get("status") == "ELIGIBLE",
            "exclusion_reasons": [item["exclusion_reason"]] if item.get("exclusion_reason") else []
        })

    return {
        "clinical_profile_summary": engine_result.get("clinical_profile_applied", {}),
        "active_weights": engine_result.get("active_weights", {}),
        "priority_mode": engine_result.get("priority_mode", "balanced"),
        "hospitals": engine_result.get("recommended_hospitals", []),
        "doctors": engine_result.get("recommended_doctors", []),
        "treatment_pathways": engine_result.get("treatment_pathways", []),
        "eligibility_audit": audit_items,
        "synthetic_benchmark_notice": (
            "NOTICE: Operational and performance metrics for hospitals and doctors are derived from a synthetic "
            "research benchmark dataset calibrated for decision-support algorithm testing. Evidence-grounded "
            "clinical treatment pathways are retrieved directly from published clinical practice guidelines."
        )
    }


@router.get("/hospitals", response_model=List[HospitalSchema])
def get_recommended_hospitals(
    specialty: Optional[str] = Query(None),
    city: Optional[str] = Query(None),
    max_budget: Optional[float] = Query(None),
    insurance: Optional[str] = Query(None),
    priority_mode: Optional[str] = Query("balanced"),
    user_id: Optional[int] = Query(None),
    report_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Personalized Hospital Recommendation API with Stage 1 Hard Filtering
    and Stage 2 Weighted Scoring (35% Clinical, 25% Cost, 20% Proximity, 20% Quality).
    Strictly isolated to authenticated user and verified medical report ownership.
    """
    if user_id is not None and user_id != current_user.id and getattr(current_user, "role", "") != "admin":
        raise HTTPException(
            status_code=403,
            detail="Forbidden: You do not have authorization to access another patient's recommendations."
        )
    target_user_id = current_user.id

    condition_entities = []
    patient_city = city if isinstance(city, str) else None
    target_specialty = specialty if isinstance(specialty, str) else None
    patient_budget = max_budget if isinstance(max_budget, (int, float)) else 500000.0
    patient_insurance = insurance if isinstance(insurance, str) else "Star Health"
    active_priority = priority_mode if isinstance(priority_mode, str) else "balanced"

    profile = db.query(PatientProfile).filter(PatientProfile.user_id == target_user_id).first()
    if profile:
        if not patient_city and profile.current_city:
            patient_city = profile.current_city
        if profile.chronic_conditions and profile.chronic_conditions.lower() != "none":
            condition_entities.extend([c.strip() for c in profile.chronic_conditions.split(",") if c.strip()])

    if isinstance(report_id, int):
        report = db.query(MedicalReport).filter(MedicalReport.id == report_id).first()
        if not report:
            raise HTTPException(status_code=404, detail="Medical report not found")
        if report.user_id != target_user_id and getattr(current_user, "role", "") != "admin":
            raise HTTPException(
                status_code=403,
                detail="Forbidden: Medical report does not belong to authenticated patient."
            )
        if not target_specialty and report.recommended_specialty:
            target_specialty = report.recommended_specialty
        if report.entities:
            for ent in report.entities:
                condition_entities.append(ent.entity_name)

    target_specialty = target_specialty or "Cardiology"
    patient_city = patient_city or "Hyderabad"

    hospitals = db.query(Hospital).all()
    hospital_dicts = [_hospital_to_dict(h) for h in hospitals]

    # Stage 1 Eligibility Filtering
    eligible_hospitals, ineligible = recommendation_engine.filter_eligible_hospitals(
        hospital_dicts,
        clinical_profile={"conditions": condition_entities},
        preferences={"specialty": target_specialty, "max_budget": patient_budget if isinstance(max_budget, (int, float)) else None}
    )

    # REMOVE UNSUPPORTED SPECIALTY FALLBACK:
    # If 0 hospitals match the requested specialty, return empty result.
    if not eligible_hospitals:
        return []

    scored_list = []
    for h_dict in eligible_hospitals:
        scored = recommendation_engine.score_hospital(
            h_dict,
            required_specialty=target_specialty,
            patient_city=patient_city,
            max_budget=patient_budget,
            preferred_insurance=patient_insurance,
            condition_entities=condition_entities,
            priority_mode=active_priority
        )
        scored_list.append(scored)

    scored_list.sort(key=lambda x: x["recommendation_score"], reverse=True)
    return scored_list


@router.get("/hospitals/{hospital_id}", response_model=HospitalSchema)
def get_hospital_details(
    hospital_id: int,
    specialty: Optional[str] = Query("Cardiology"),
    city: Optional[str] = Query("Hyderabad"),
    insurance: Optional[str] = Query("Star Health"),
    priority_mode: Optional[str] = Query("balanced"),
    user_id: Optional[int] = Query(None),
    report_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    h = db.query(Hospital).filter(Hospital.id == hospital_id).first()
    if not h:
        raise HTTPException(status_code=404, detail="Hospital not found")

    if user_id is not None and user_id != current_user.id and getattr(current_user, "role", "") != "admin":
        raise HTTPException(
            status_code=403,
            detail="Forbidden: You do not have authorization to access another patient's data."
        )
    target_user_id = current_user.id

    target_specialty = specialty if isinstance(specialty, str) else "Cardiology"
    patient_city = city if isinstance(city, str) else "Hyderabad"
    target_insurance = insurance if isinstance(insurance, str) else "Star Health"
    active_priority = priority_mode if isinstance(priority_mode, str) else "balanced"

    profile = db.query(PatientProfile).filter(PatientProfile.user_id == target_user_id).first()
    if profile and profile.current_city and not city:
        patient_city = profile.current_city

    condition_entities = []
    if isinstance(report_id, int):
        report = db.query(MedicalReport).filter(MedicalReport.id == report_id).first()
        if not report:
            raise HTTPException(status_code=404, detail="Medical report not found")
        if report.user_id != target_user_id and getattr(current_user, "role", "") != "admin":
            raise HTTPException(
                status_code=403,
                detail="Forbidden: Medical report does not belong to authenticated patient."
            )
        if report.recommended_specialty and not specialty:
            target_specialty = report.recommended_specialty
        if report.entities:
            for ent in report.entities:
                condition_entities.append(ent.entity_name)

    h_dict = _hospital_to_dict(h)
    return recommendation_engine.score_hospital(
        h_dict,
        required_specialty=target_specialty,
        patient_city=patient_city,
        preferred_insurance=target_insurance,
        condition_entities=condition_entities,
        priority_mode=active_priority
    )


@router.get("/doctors", response_model=List[DoctorSchema])
def get_recommended_doctors(
    specialty: Optional[str] = Query(None),
    hospital_id: Optional[int] = Query(None),
    city: Optional[str] = Query(None),
    user_id: Optional[int] = Query(None),
    report_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Context-Aware Doctor Recommendation API.
    Scores doctors based on medical report specialty, experience years, patient rating,
    and hospital affiliation. Strictly isolated to authenticated user session.
    """
    if user_id is not None and user_id != current_user.id and getattr(current_user, "role", "") != "admin":
        raise HTTPException(
            status_code=403,
            detail="Forbidden: You do not have authorization to access another patient's recommendations."
        )
    target_user_id = current_user.id

    target_specialty = specialty if isinstance(specialty, str) else None
    patient_city = city if isinstance(city, str) else None

    patient_comorbidities = []
    profile = db.query(PatientProfile).filter(PatientProfile.user_id == target_user_id).first()
    if profile:
        if profile.current_city and not patient_city:
            patient_city = profile.current_city
        if profile.chronic_conditions and profile.chronic_conditions.lower() != "none":
            patient_comorbidities.extend([c.strip() for c in profile.chronic_conditions.split(",") if c.strip()])
        if profile.conditions:
            for c in profile.conditions:
                if c not in patient_comorbidities:
                    patient_comorbidities.append(c)

    if isinstance(report_id, int):
        report = db.query(MedicalReport).filter(MedicalReport.id == report_id).first()
        if not report:
            raise HTTPException(status_code=404, detail="Medical report not found")
        if report.user_id != target_user_id and getattr(current_user, "role", "") != "admin":
            raise HTTPException(
                status_code=403,
                detail="Forbidden: Medical report does not belong to authenticated patient."
            )
        if report and report.recommended_specialty and not target_specialty:
            target_specialty = report.recommended_specialty

    target_specialty = target_specialty or "Cardiology"

    query = db.query(Doctor)
    if isinstance(hospital_id, int):
        query = query.filter(Doctor.hospital_id == hospital_id)
    active_specialty = specialty or target_specialty
    if active_specialty:
        query = query.filter(Doctor.specialty.ilike(f"%{active_specialty}%"))

    doctors = query.all()
    if not doctors:
        # Fallback query by target specialty if specific filter yielded empty
        doctors = db.query(Doctor).filter(Doctor.specialty.ilike(f"%{target_specialty}%")).all()

    # REMOVE UNSUPPORTED SPECIALTY FALLBACK:
    # If no doctors match the requested specialty, do NOT return unrelated doctors! Return empty list.
    if not doctors:
        return []

    # Preload hospital map for quick affiliation lookup
    hospital_ids = {d.hospital_id for d in doctors}
    hospitals = {h.id: h for h in db.query(Hospital).filter(Hospital.id.in_(hospital_ids)).all()}

    scored_doctors = []
    for d in doctors:
        hosp = hospitals.get(d.hospital_id)
        hosp_dict = {
            "name": hosp.name if hosp else "Tertiary Medical Center",
            "city": hosp.city if hosp else "Hyderabad"
        } if hosp else None

        d_dict = _doctor_to_dict(d, hosp_dict)
        scored = recommendation_engine.score_doctor(
            d_dict,
            required_specialty=target_specialty,
            patient_city=patient_city,
            hospital_dict=hosp_dict,
            comorbidity_conditions=patient_comorbidities
        )
        scored_doctors.append(scored)

    # Sort descending by match score and comorbidity relevance
    scored_doctors.sort(key=lambda x: (x["match_score"], x.get("comorbidity_matches", 0)), reverse=True)
    return scored_doctors


@router.get("/treatments", response_model=TreatmentRecommendationResponse)
def get_treatment_recommendations(
    condition: Optional[str] = Query(None),
    specialty: Optional[str] = Query(None),
    report_id: Optional[int] = Query(None),
    user_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    RAG-Grounded Treatment Option & Clinical Pathway Recommendation API.
    Retrieves evidence-based clinical pathways from the Phase 3/4 verified knowledge base,
    fusing authenticated patient profile comorbidities and allergies to flag potential
    contraindications without independently prescribing or altering medications.
    """
    if user_id is not None and user_id != current_user.id and getattr(current_user, "role", "") != "admin":
        raise HTTPException(
            status_code=403,
            detail="Forbidden: You do not have authorization to access another patient's treatments."
        )
    target_user_id = current_user.id

    target_condition = condition
    target_specialty = specialty
    report_entities = []

    # Pull clinical context from medical report if report_id provided
    if report_id:
        report = db.query(MedicalReport).filter(MedicalReport.id == report_id).first()
        if not report:
            raise HTTPException(status_code=404, detail="Medical report not found")
        if report.user_id != target_user_id and getattr(current_user, "role", "") != "admin":
            raise HTTPException(
                status_code=403,
                detail="Forbidden: Medical report does not belong to authenticated patient."
            )
        if not target_specialty:
            target_specialty = report.recommended_specialty
        if not target_condition:
            disease_ents = [e.entity_name for e in report.entities if e.entity_type in ["Disease", "Symptom"]]
            if disease_ents:
                target_condition = ", ".join(disease_ents[:2])
            elif report.summary:
                target_condition = report.summary[:100]
        for ent in report.entities:
            report_entities.append(ent.entity_name)

    # Resolve authenticated patient profile (allergies & chronic conditions)
    patient_allergies = []
    patient_conditions = []
    profile = db.query(PatientProfile).filter(PatientProfile.user_id == target_user_id).first()
    if profile:
        if profile.allergies and profile.allergies.lower() != "none":
            patient_allergies = [a.strip() for a in profile.allergies.split(",") if a.strip() and a.strip().lower() != "none"]
        if profile.chronic_conditions and profile.chronic_conditions.lower() != "none":
            patient_conditions.extend([c.strip() for c in profile.chronic_conditions.split(",") if c.strip() and c.strip().lower() != "none"])
        if profile.conditions:
            for c in profile.conditions:
                if c not in patient_conditions:
                    patient_conditions.append(c)

    # Pull patient chronic conditions if condition not derived from report
    if not target_condition and patient_conditions:
        target_condition = ", ".join(patient_conditions[:2])

    # Final fallbacks
    target_condition = target_condition or "Coronary Artery Disease / Angina"
    target_specialty = target_specialty or "Cardiology"

    pathways = recommendation_engine.match_treatment_pathways(
        condition=target_condition,
        specialty=target_specialty,
        report_entities=report_entities,
        patient_allergies=patient_allergies,
        patient_conditions=patient_conditions
    )
    all_sources = []
    for p in pathways:
        for s in p.get("grounding_sources", []):
            if s not in all_sources:
                all_sources.append(s)

    patient_context_dict = {
        "user_id": target_user_id,
        "allergies_evaluated": patient_allergies,
        "conditions_evaluated": patient_conditions
    } if (patient_allergies or patient_conditions) else None

    return {
        "patient_condition": target_condition,
        "specialty": target_specialty,
        "recommended_pathways": pathways,
        "clinical_notes": f"Evidence-based clinical pathways matched from verified {target_specialty} medical guidelines.",
        "sources_consulted": all_sources,
        "patient_context_applied": patient_context_dict
    }


@router.post("/compare")
def compare_hospitals(
    body: Union[List[int], Dict[str, Any]] = Body(default=[]),
    user_id: Optional[int] = None,
    city: Optional[str] = None,
    specialty: Optional[str] = None,
    priority_mode: Optional[str] = None,
    max_budget: Optional[float] = None,
    insurance: Optional[str] = None,
    report_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Side-by-side hospital comparison with patient context awareness.
    Compares existing dataset fields with exact user priority mode, insurance, budget,
    and report entity context to preserve consistent scores.
    """
    if user_id is not None and user_id != current_user.id and getattr(current_user, "role", "") != "admin":
        raise HTTPException(
            status_code=403,
            detail="Forbidden: You do not have authorization to access another patient's comparison."
        )
    target_user_id = current_user.id

    if isinstance(body, dict):
        hospital_ids = body.get("hospital_ids", [])
    elif isinstance(body, list):
        hospital_ids = body
    else:
        hospital_ids = []

    patient_city = city or "Hyderabad"
    profile = db.query(PatientProfile).filter(PatientProfile.user_id == target_user_id).first()
    if profile and profile.current_city and not city:
        patient_city = profile.current_city

    condition_entities = []
    if profile and profile.chronic_conditions and profile.chronic_conditions.lower() != "none":
        condition_entities.extend([c.strip() for c in profile.chronic_conditions.split(",") if c.strip()])

    target_specialty = specialty
    if isinstance(report_id, int):
        report = db.query(MedicalReport).filter(MedicalReport.id == report_id).first()
        if not report:
            raise HTTPException(status_code=404, detail="Medical report not found")
        if report.user_id != target_user_id and getattr(current_user, "role", "") != "admin":
            raise HTTPException(
                status_code=403,
                detail="Forbidden: Medical report does not belong to authenticated patient."
            )
        if not target_specialty and report.recommended_specialty:
            target_specialty = report.recommended_specialty
        if report.entities:
            for ent in report.entities:
                condition_entities.append(ent.entity_name)

    target_specialty = target_specialty or "Cardiology"
    active_priority = priority_mode or "balanced"
    patient_budget = max_budget if isinstance(max_budget, (int, float)) else 500000.0
    patient_insurance = insurance or "Star Health"

    if not hospital_ids:
        # Default to top 3 hospitals in city or accredited hubs if none provided
        hospitals = db.query(Hospital).filter(Hospital.city.ilike(f"%{patient_city}%")).limit(3).all()
        if len(hospitals) < 2:
            hospitals = db.query(Hospital).limit(3).all()
    else:
        hospitals = db.query(Hospital).filter(Hospital.id.in_(hospital_ids)).all()

    comparison = []
    for h in hospitals:
        calc_dist = recommendation_engine.score_hospital(
            _hospital_to_dict(h),
            required_specialty=target_specialty,
            patient_city=patient_city,
            max_budget=patient_budget,
            preferred_insurance=patient_insurance,
            condition_entities=condition_entities,
            priority_mode=active_priority
        )
        h_dict = {
            "id": h.id,
            "name": h.name,
            "city": h.city,
            "state": h.state,
            "address": h.address,
            "specialties": h.specialties or [],
            "rating": h.rating,
            "quality_rating": h.quality_rating or h.rating or 4.5,
            "cost_tier": h.cost_tier or "Moderate",
            "estimated_cost_tier": h.estimated_cost_tier or 320000.0,
            "accreditation": h.accreditation or "NABH Accredited",
            "treatment_capabilities": h.treatment_capabilities or [],
            "icu_beds": h.icu_beds or 50,
            "emergency_24x7": h.emergency_24x7 if h.emergency_24x7 is not None else True,
            "distance_km": calc_dist["distance_km"],
            "insurance_accepted": h.insurance_accepted or [],
            "facilities": h.facilities or [],
            "contact_phone": h.contact_phone,
            "availability": h.availability_status,
            "availability_status": h.availability_status,
            "recommendation_score": calc_dist["recommendation_score"],
            "score_breakdown": calc_dist["score_breakdown"],
            "reasons": calc_dist["reasons"]
        }
        comparison.append(h_dict)

    comparison.sort(key=lambda x: x["recommendation_score"], reverse=True)
    top_hospital_name = comparison[0]["name"] if comparison else "Top Hospital"

    return {
        "compared_hospitals": comparison,
        "ai_recommendation": f"Based on multi-criteria analysis for {patient_city}, '{top_hospital_name}' leads the comparison with top specialty infrastructure and cashless insurance compatibility." if comparison else "Please select 2 to 3 hospitals to compare."
    }


@router.post("/compare-doctors")
def compare_doctors(
    body: Union[List[int], Dict[str, Any]] = Body(default=[]),
    user_id: Optional[int] = None,
    specialty: Optional[str] = None,
    report_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Side-by-side doctor comparison with patient context awareness.
    Compares existing dataset fields: name, specialty, expertise,
    experience_years, rating, consultation_fee, hospital, match_score.
    """
    if user_id is not None and user_id != current_user.id and getattr(current_user, "role", "") != "admin":
        raise HTTPException(
            status_code=403,
            detail="Forbidden: You do not have authorization to access another patient's comparison."
        )
    target_user_id = current_user.id

    if isinstance(body, dict):
        doctor_ids = body.get("doctor_ids", [])
    elif isinstance(body, list):
        doctor_ids = body
    else:
        doctor_ids = []

    patient_comorbidities = []
    profile = db.query(PatientProfile).filter(PatientProfile.user_id == target_user_id).first()
    if profile:
        raw_conds = profile.chronic_conditions or profile.conditions
        if isinstance(raw_conds, list):
            patient_comorbidities = [c for c in raw_conds if c and c != "None"]
        elif isinstance(raw_conds, str):
            patient_comorbidities = [c.strip() for c in raw_conds.split(",") if c.strip() and c.lower() != "none"]

    target_specialty = specialty
    if isinstance(report_id, int):
        report = db.query(MedicalReport).filter(MedicalReport.id == report_id).first()
        if not report:
            raise HTTPException(status_code=404, detail="Medical report not found")
        if report.user_id != target_user_id and getattr(current_user, "role", "") != "admin":
            raise HTTPException(
                status_code=403,
                detail="Forbidden: Medical report does not belong to authenticated patient."
            )
        if not target_specialty and report.recommended_specialty:
            target_specialty = report.recommended_specialty

    target_specialty = target_specialty or "Cardiology"

    if not doctor_ids:
        doctors = db.query(Doctor).filter(Doctor.specialty.ilike(f"%{target_specialty}%")).limit(3).all()
        if not doctors:
            doctors = db.query(Doctor).limit(3).all()
    else:
        doctors = db.query(Doctor).filter(Doctor.id.in_(doctor_ids)).all()

    hosp_map = {h.id: h for h in db.query(Hospital).filter(Hospital.id.in_([d.hospital_id for d in doctors])).all()}

    comparison = []
    for d in doctors:
        h_info = hosp_map.get(d.hospital_id)
        d_dict = _doctor_to_dict(d, _hospital_to_dict(h_info) if h_info else None)
        scored = recommendation_engine.score_doctor(
            d_dict,
            required_specialty=target_specialty or d.specialty,
            comorbidity_conditions=patient_comorbidities
        )
        d_dict["match_score"] = scored.get("match_score")
        d_dict["score_breakdown"] = scored.get("score_breakdown")
        d_dict["reasons"] = scored.get("reasons", [])
        comparison.append(d_dict)

    comparison.sort(key=lambda x: x.get("match_score", 0), reverse=True)
    top_doc_name = comparison[0]["name"] if comparison else "Top Specialist"

    return {
        "compared_doctors": comparison,
        "ai_recommendation": f"Doctor '{top_doc_name}' leads the comparison with top clinical specialty alignment, clinical experience ({comparison[0]['experience_years']} yrs), and high patient rating." if comparison else "Please select 2 to 3 doctors to compare."
    }
