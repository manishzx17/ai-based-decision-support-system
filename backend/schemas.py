from pydantic import BaseModel, EmailStr
from typing import List, Optional, Any, Dict
from datetime import datetime

# --- AUTH & USER ---
class UserCreate(BaseModel):
    email: str
    password: str
    full_name: str

class UserLogin(BaseModel):
    email: Optional[str] = None
    username: Optional[str] = None
    password: str

class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    role: str
    created_at: datetime

    class Config:
        from_attributes = True

class DocumentMetadata(BaseModel):
    patient_name: Optional[str] = None
    patient_id: Optional[str] = None
    report_date: Optional[str] = None


class PatientDemographics(BaseModel):
    age: Optional[int] = None
    gender: Optional[str] = None


class TestResultItem(BaseModel):
    test_name: str
    value: str
    unit: Optional[str] = None
    reference_range: Optional[str] = None
    status: Optional[str] = None  # Normal, High, Low, Critical


class PatientProfileSchema(BaseModel):
    id: Optional[int] = None
    user_id: Optional[int] = None
    age: Optional[int] = 30
    gender: Optional[str] = "Male"
    blood_group: Optional[str] = "O+"
    allergies: Optional[str] = "None"
    chronic_conditions: Optional[str] = "None"
    current_city: Optional[str] = "Hyderabad"
    preferred_currency: Optional[str] = "INR"
    emergency_contact_name: Optional[str] = "Emergency Contact"
    emergency_contact_phone: Optional[str] = "+91 98765 43210"

    # Phase 3 Persistent Clinical Profile Fields
    conditions: Optional[List[str]] = []
    symptoms: Optional[List[str]] = []
    tests: Optional[List[str]] = []
    test_results: Optional[List[TestResultItem]] = []
    medications: Optional[List[str]] = []
    procedures: Optional[List[str]] = []
    medical_history: Optional[List[str]] = []
    last_report_id: Optional[int] = None
    structured_data: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


# --- MEDICAL REPORTS & ENTITIES ---
class ExtractedEntitySchema(BaseModel):
    id: Optional[int] = None
    entity_type: str
    entity_name: str
    confidence: float
    context_snippet: Optional[str] = None

    class Config:
        from_attributes = True


class StructuredClinicalInfo(BaseModel):
    metadata: DocumentMetadata = DocumentMetadata()
    demographics: PatientDemographics = PatientDemographics()
    conditions: List[str] = []  # Explicitly reported conditions only (no inferred diagnoses)
    symptoms: List[str] = []
    tests: List[str] = []
    test_results: List[TestResultItem] = []
    medications: List[str] = []
    procedures: List[str] = []
    medical_history: List[str] = []


class MedicalReportResponse(BaseModel):
    id: int
    user_id: Optional[int] = None
    filename: str
    file_path: str
    status: str
    ocr_text: Optional[str] = None
    summary: Optional[str] = None
    recommended_specialty: str
    important_notes: Optional[str] = None
    grounding_notes: Optional[str] = None
    grounding_sources: Optional[List[Dict[str, Any]]] = None
    created_at: datetime
    entities: List[ExtractedEntitySchema] = []
    structured_info: Optional[StructuredClinicalInfo] = None

    class Config:
        from_attributes = True


# --- HOSPITALS & DOCTORS ---
class DoctorSchema(BaseModel):
    id: int
    hospital_id: int
    name: str
    specialty: str
    experience_years: int
    qualification: str
    rating: float
    consultation_fee: float
    availability_days: str
    expertise: Optional[List[str]] = []
    match_score: Optional[float] = None
    reasons: Optional[List[str]] = None
    hospital_name: Optional[str] = None
    hospital_city: Optional[str] = None
    provenance: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True

class HospitalSchema(BaseModel):
    id: int
    name: str
    city: str
    state: str
    address: str
    lat: float
    lng: float
    specialties: List[str]
    rating: float
    distance_km: float
    insurance_accepted: List[str]
    facilities: List[str]
    contact_phone: str
    availability_status: str
    cost_tier: Optional[str] = None
    quality_rating: Optional[float] = None
    accreditation: Optional[str] = None
    treatment_capabilities: Optional[List[str]] = []
    icu_beds: Optional[int] = None
    emergency_24x7: Optional[bool] = None
    estimated_cost_tier: Optional[float] = None
    recommendation_score: Optional[float] = None
    shap_reasons: Optional[List[str]] = None
    reasons: Optional[List[str]] = None
    score_breakdown: Optional[Dict[str, float]] = None
    provenance: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True

# --- PHASE 5 PERSONALIZED RECOMMENDATIONS ---
class PatientPreferencesSchema(BaseModel):
    preferred_city: Optional[str] = None
    user_location: Optional[Dict[str, float]] = None
    max_distance_km: Optional[float] = None
    insurance_provider: Optional[str] = None
    max_budget_inr: Optional[float] = None
    max_cost_tier: Optional[str] = None
    preferred_languages: Optional[List[str]] = None
    priority_mode: Optional[str] = "balanced"
    min_hospital_rating: Optional[float] = None
    require_nabh_jci: Optional[bool] = False
    treatment_type_interest: Optional[str] = None

class EligibilityAuditItem(BaseModel):
    provider_id: int
    name: str
    entity_type: str
    eligible: bool
    exclusion_reasons: List[str] = []

class PersonalizedRecommendationRequest(BaseModel):
    user_id: Optional[int] = None
    clinical_profile: Optional[Dict[str, Any]] = None
    preferences: Optional[PatientPreferencesSchema] = None
    top_hospitals: Optional[int] = 5
    top_doctors: Optional[int] = 5
    top_pathways: Optional[int] = 3

class PersonalizedRecommendationResponse(BaseModel):
    clinical_profile_summary: Dict[str, Any]
    active_weights: Dict[str, float]
    priority_mode: str
    hospitals: List[HospitalSchema]
    doctors: List[DoctorSchema]
    treatment_pathways: List[Dict[str, Any]]
    eligibility_audit: List[EligibilityAuditItem] = []
    synthetic_benchmark_notice: str


# --- TREATMENT RECOMMENDATIONS ---
class TreatmentPathwaySchema(BaseModel):
    pathway_name: str
    specialty: str
    condition: str
    description: str
    suitability: str
    estimated_duration_days: int
    flight_clearance_guideline: str
    grounding_sources: List[Dict[str, Any]]
    clinical_disclaimer: str
    allergy_conflict_detected: Optional[bool] = False
    allergy_warning: Optional[str] = None

class TreatmentRecommendationResponse(BaseModel):
    patient_condition: str
    specialty: str
    recommended_pathways: List[TreatmentPathwaySchema]
    clinical_notes: str
    sources_consulted: List[Dict[str, Any]]
    patient_context_applied: Optional[Dict[str, Any]] = None

# --- COST PREDICTION ---
class CostPredictionRequest(BaseModel):
    treatment_name: str
    hospital_id: Optional[int] = None
    city: str = "Hyderabad"
    room_type: str = "Private AC Deluxe"
    duration_days: Optional[int] = None
    user_id: Optional[int] = None
    report_id: Optional[int] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    specialty: Optional[str] = None
    comorbidity_count: Optional[int] = None
    has_diabetes: Optional[bool] = None
    has_hypertension: Optional[bool] = None
    has_cardiac_history: Optional[bool] = None
    hospital_tier: Optional[str] = None
    insurance_type: Optional[str] = "Cashless Empanelled"

class CostPredictionResponse(BaseModel):
    treatment_name: str
    canonical_treatment: Optional[str] = None
    city: str
    room_type: str
    duration_days: int
    predicted_los_days: Optional[float] = None
    los_source: Optional[str] = None
    estimated_min_cost: float
    estimated_max_cost: float
    estimated_avg_cost: float
    currency: str = "INR"
    empirical_model_error_range: Optional[Dict[str, Any]] = None
    shap_feature_impacts: Dict[str, float]
    base_value: Optional[float] = None
    additive_difference: Optional[float] = None
    relative_additive_difference: Optional[float] = None
    disclaimer: str = "Estimated cost – actual hospital charges may vary."

# --- TRAVEL PLANNER ---
class TravelPlanRequest(BaseModel):
    medical_condition: str
    hospital_id: int
    doctor_id: int
    preferred_travel_date: str
    current_location: str = "Bengaluru"
    budget_range: str = "Standard"
    duration_days: int = 5
    report_id: Optional[int] = None
    accessibility_needed: Optional[List[str]] = None

class TravelPlanResponse(BaseModel):
    id: Optional[int] = None
    destination_city: str
    hospital_name: str
    doctor_name: str
    start_date: str
    duration_days: int
    itinerary: List[Dict[str, Any]]
    total_estimated_cost: float
    cost_breakdown: Optional[Dict[str, float]] = None
    patient_context: Optional[Dict[str, Any]] = None
    recommended_accommodation: Optional[Dict[str, Any]] = None
    navigation_summary: Optional[Dict[str, Any]] = None
    pre_treatment_considerations: Optional[List[Dict[str, Any]]] = None
    post_treatment_considerations: Optional[List[Dict[str, Any]]] = None
    clinical_disclaimer: Optional[str] = None

# --- APPOINTMENT ---
class AppointmentCreate(BaseModel):
    hospital_id: int
    doctor_id: int
    patient_name: str
    appointment_date: str
    appointment_time: str
    reason: str

class AppointmentSchema(BaseModel):
    id: int
    user_id: int
    hospital_id: int
    doctor_id: int
    patient_name: str
    appointment_date: str
    appointment_time: str
    status: str
    reason: str

    class Config:
        from_attributes = True

# --- SYMPTOM GUIDANCE ---
class SymptomGuidanceRequest(BaseModel):
    symptoms_text: str
    duration: Optional[str] = "2 days"
    severity: Optional[str] = "Moderate"

class SymptomGuidanceResponse(BaseModel):
    summary: str
    urgency_level: str # LOW, MODERATE, URGENT, EMERGENCY
    recommended_specialty: str
    guidance_notes: List[str]
    suggested_actions: List[str]
    disclaimer: str

# --- TRANSLATION ---
class TranslationRequest(BaseModel):
    text: str
    source_lang: str = "English"
    target_lang: str = "Telugu"

class TranslationResponse(BaseModel):
    original_text: str
    translated_text: str
    source_lang: str
    target_lang: str

# --- CHAT ASSISTANT ---
class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[int] = None
    report_id: Optional[int] = None
    hospital_id: Optional[int] = None

class ChatResponse(BaseModel):
    reply: str
    conversation_id: int
    citations: List[str] = []
    grounding_status: Optional[str] = "GROUNDED" # GROUNDED, INSUFFICIENT_EVIDENCE
    retrieved_evidence: Optional[List[Dict[str, Any]]] = []
    disclaimer: str
    is_emergency: Optional[bool] = False
    emergency_alert: Optional[str] = None
    patient_context_applied: Optional[Dict[str, Any]] = None
    suggested_followups: Optional[List[str]] = []
    safety_guardrails_triggered: Optional[List[str]] = []
    llm_provider: Optional[str] = "ollama"
    model_used: Optional[str] = "llama3.2:1b"


# --- RAG SCHEMAS (PHASE 4) ---
class RAGQueryRequest(BaseModel):
    query: str
    top_k: Optional[int] = 3
    threshold: Optional[float] = None
    use_clinical_profile: Optional[bool] = True

class RAGQueryResponse(BaseModel):
    reply: str
    citations: List[str] = []
    grounding_status: str  # GROUNDED or INSUFFICIENT_EVIDENCE
    retrieved_evidence: List[Dict[str, Any]] = []
    llm_provider: str
    model_used: str
    clinical_profile_used: Optional[Dict[str, Any]] = None

class RAGProfileGroundingRequest(BaseModel):
    user_id: Optional[int] = None
    top_k: Optional[int] = 2

class RAGProfileGroundingResponse(BaseModel):
    grounding_status: str
    matched_guidelines: List[Dict[str, Any]] = []
    citations: List[str] = []
    patient_conditions_evaluated: List[str] = []
    patient_procedures_evaluated: List[str] = []



# --- AUDIT LOGS ---
class AuditLogSchema(BaseModel):
    id: int
    user_id: Optional[int] = None
    action: str
    resource_type: str
    resource_id: Optional[str] = None
    status: str
    details: Optional[str] = None
    timestamp: datetime

    class Config:
        from_attributes = True


# --- CLINICAL RECOVERY & TRAVEL TIMELINE ---
class RecoveryMilestone(BaseModel):
    phase: str
    title: str
    timeline_days: str
    clinical_focus: str
    guideline_statement: str
    clearance_status: str

class ClinicalRecoveryTimelineResponse(BaseModel):
    treatment_name: str
    specialty: str
    predicted_los_days: float
    total_recovery_window_days: int
    milestones: List[RecoveryMilestone]
    clinical_guideline_sources: List[str]
    safety_disclaimer: str


# --- MEDICAL TRAVEL (OPEN ROUTING & NOMINATIM) ---
class OpenRouteRequest(BaseModel):
    origin: str
    destination: str
    travel_mode: str = "car"  # car, two_wheeler, walking, bicycle, transit

class OpenRouteWaypoint(BaseModel):
    name: str
    lat: float
    lon: float

class OpenRouteResponse(BaseModel):
    origin: OpenRouteWaypoint
    destination: OpenRouteWaypoint
    travel_mode: str
    distance_km: float
    duration_minutes: float
    duration_text: str
    route_geometry: List[List[float]]  # List of [lat, lon] coordinates for Leaflet
    osm_attribution: str
    open_map_url: str
    routing_service: str

class NearbyPOI(BaseModel):
    name: str
    category: str  # hotel, pharmacy
    address: str
    lat: float
    lon: float
    distance_km: Optional[float] = None
    open_map_url: str

class NearbyPOIResponse(BaseModel):
    query_location: str
    category: str
    total_found: int
    items: List[NearbyPOI]
    osm_attribution: str

class EmergencyContact(BaseModel):
    service_name: str
    number: str
    description: str

class HospitalEmergencyDept(BaseModel):
    hospital_name: str
    emergency_phone: str
    address: str
    city: str
    state: str
    emergency_24x7: bool
    icu_beds: int
    lat: Optional[float] = None
    lon: Optional[float] = None

class EmergencyServicesResponse(BaseModel):
    city: str
    state: str
    national_emergency_number: str
    ambulance_number: str
    police_number: str
    fire_number: str
    women_helpline: str
    contacts: List[EmergencyContact]
    hospital_emergency_dept: Optional[HospitalEmergencyDept] = None
    disclaimer: str


