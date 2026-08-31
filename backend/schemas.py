from pydantic import BaseModel, EmailStr
from typing import List, Optional, Any, Dict
from datetime import datetime

# --- AUTH & USER ---
class UserCreate(BaseModel):
    email: str
    password: str
    full_name: str

class UserLogin(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    role: str
    created_at: datetime

    class Config:
        from_attributes = True

class PatientProfileSchema(BaseModel):
    id: Optional[int] = None
    user_id: Optional[int] = None
    age: int = 30
    gender: str = "Male"
    blood_group: str = "O+"
    allergies: str = "None"
    chronic_conditions: str = "None"
    current_city: str = "Hyderabad"
    preferred_currency: str = "INR"
    emergency_contact_name: str = "Emergency Contact"
    emergency_contact_phone: str = "+91 98765 43210"

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

class MedicalReportResponse(BaseModel):
    id: int
    filename: str
    file_path: str
    status: str
    ocr_text: Optional[str] = None
    summary: Optional[str] = None
    recommended_specialty: str
    important_notes: Optional[str] = None
    created_at: datetime
    entities: List[ExtractedEntitySchema] = []

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
    recommendation_score: Optional[float] = None
    shap_reasons: Optional[List[str]] = None

    class Config:
        from_attributes = True

# --- COST PREDICTION ---
class CostPredictionRequest(BaseModel):
    treatment_name: str
    hospital_id: Optional[int] = None
    city: str = "Hyderabad"
    room_type: str = "Private AC Deluxe"
    duration_days: int = 4

class CostPredictionResponse(BaseModel):
    treatment_name: str
    city: str
    room_type: str
    estimated_min_cost: float
    estimated_max_cost: float
    estimated_avg_cost: float
    currency: str = "INR"
    shap_feature_impacts: Dict[str, float]
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

class TravelPlanResponse(BaseModel):
    id: Optional[int] = None
    destination_city: str
    hospital_name: str
    doctor_name: str
    start_date: str
    duration_days: int
    itinerary: List[Dict[str, Any]]
    total_estimated_cost: float

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

class ChatResponse(BaseModel):
    reply: str
    conversation_id: int
    citations: List[str] = []
    disclaimer: str
