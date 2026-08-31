from sqlalchemy import Column, Integer, String, Float, Text, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    role = Column(String, default="patient") # patient, admin, doctor
    created_at = Column(DateTime, default=datetime.utcnow)

    profile = relationship("PatientProfile", back_populates="user", uselist=False)
    reports = relationship("MedicalReport", back_populates="user")
    appointments = relationship("Appointment", back_populates="user")
    travel_plans = relationship("TravelPlan", back_populates="user")
    conversations = relationship("Conversation", back_populates="user")


class PatientProfile(Base):
    __tablename__ = "patient_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    age = Column(Integer, default=30)
    gender = Column(String, default="Other")
    blood_group = Column(String, default="O+")
    allergies = Column(Text, default="None")
    chronic_conditions = Column(Text, default="None")
    current_city = Column(String, default="Hyderabad")
    preferred_currency = Column(String, default="INR")
    emergency_contact_name = Column(String, default="Family Member")
    emergency_contact_phone = Column(String, default="+91 98765 43210")

    user = relationship("User", back_populates="profile")


class MedicalReport(Base):
    __tablename__ = "medical_reports"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    status = Column(String, default="COMPLETED") # PROCESSING, COMPLETED, FAILED
    ocr_text = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    recommended_specialty = Column(String, default="General Medicine")
    important_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="reports")
    entities = relationship("ExtractedEntity", back_populates="report", cascade="all, delete-orphan")


class ExtractedEntity(Base):
    __tablename__ = "extracted_entities"

    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(Integer, ForeignKey("medical_reports.id"), nullable=False)
    entity_type = Column(String, nullable=False) # Disease, Symptom, Medication, LabTest, Procedure, BodyPart
    entity_name = Column(String, nullable=False)
    confidence = Column(Float, default=0.95)
    context_snippet = Column(Text, nullable=True)

    report = relationship("MedicalReport", back_populates="entities")


class Hospital(Base):
    __tablename__ = "hospitals"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    city = Column(String, nullable=False, index=True)
    state = Column(String, default="Telangana")
    address = Column(Text, nullable=False)
    lat = Column(Float, default=17.3850)
    lng = Column(Float, default=78.4867)
    specialties = Column(JSON, default=list) # List of specialty strings
    rating = Column(Float, default=4.5)
    distance_km = Column(Float, default=5.2)
    insurance_accepted = Column(JSON, default=list) # List of insurance provider names
    facilities = Column(JSON, default=list) # ICU, Helicopter Pad, Interpreter, International Lounge
    contact_phone = Column(String, default="+91 40 2345 6789")
    availability_status = Column(String, default="High")

    doctors = relationship("Doctor", back_populates="hospital")
    treatment_costs = relationship("TreatmentCost", back_populates="hospital")
    accommodations = relationship("Accommodation", back_populates="hospital")


class Doctor(Base):
    __tablename__ = "doctors"

    id = Column(Integer, primary_key=True, index=True)
    hospital_id = Column(Integer, ForeignKey("hospitals.id"), nullable=False)
    name = Column(String, nullable=False)
    specialty = Column(String, nullable=False)
    experience_years = Column(Integer, default=12)
    qualification = Column(String, default="MBBS, MD, DM")
    rating = Column(Float, default=4.8)
    consultation_fee = Column(Float, default=1000.0)
    availability_days = Column(String, default="Mon - Sat")

    hospital = relationship("Hospital", back_populates="doctors")


class Pharmacy(Base):
    __tablename__ = "pharmacies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    city = Column(String, nullable=False)
    address = Column(Text, nullable=False)
    lat = Column(Float, default=17.3850)
    lng = Column(Float, default=78.4867)
    distance_km = Column(Float, default=1.5)
    is_24_7 = Column(Boolean, default=True)
    contact_phone = Column(String, default="+91 40 1122 3344")
    medication_stock_summary = Column(Text, default="All major cardiac, oncology, and antibiotic medications available.")


class TreatmentCost(Base):
    __tablename__ = "treatment_costs"

    id = Column(Integer, primary_key=True, index=True)
    hospital_id = Column(Integer, ForeignKey("hospitals.id"), nullable=False)
    treatment_name = Column(String, nullable=False)
    min_cost = Column(Float, nullable=False)
    max_cost = Column(Float, nullable=False)
    avg_cost = Column(Float, nullable=False)
    room_type = Column(String, default="Private AC Deluxe")

    hospital = relationship("Hospital", back_populates="treatment_costs")


class InsuranceProvider(Base):
    __tablename__ = "insurance_providers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    policy_type = Column(String, default="Comprehensive Health Travel Cover")
    coverage_details = Column(Text, nullable=False)
    network_hospitals_count = Column(Integer, default=450)
    claim_contact = Column(String, default="claims@medinsurance.com")


class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    hospital_id = Column(Integer, ForeignKey("hospitals.id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False)
    patient_name = Column(String, nullable=False)
    appointment_date = Column(String, nullable=False)
    appointment_time = Column(String, nullable=False)
    status = Column(String, default="CONFIRMED") # CONFIRMED, PENDING, CANCELLED
    reason = Column(Text, default="Medical consultation")

    user = relationship("User", back_populates="appointments")


class Accommodation(Base):
    __tablename__ = "accommodations"

    id = Column(Integer, primary_key=True, index=True)
    hospital_id = Column(Integer, ForeignKey("hospitals.id"), nullable=False)
    name = Column(String, nullable=False)
    address = Column(Text, nullable=False)
    price_per_night = Column(Float, default=2500.0)
    rating = Column(Float, default=4.5)
    distance_km = Column(Float, default=0.8)
    facilities = Column(JSON, default=list) # Wheelchair accessible, Kitchen, Free Wifi, Airport Shuttle

    hospital = relationship("Hospital", back_populates="accommodations")


class EmergencyContact(Base):
    __tablename__ = "emergency_contacts"

    id = Column(Integer, primary_key=True, index=True)
    city = Column(String, nullable=False)
    service_type = Column(String, nullable=False) # Ambulance, Police, Trauma Center, Blood Bank
    service_name = Column(String, nullable=False)
    phone_number = Column(String, nullable=False)
    address = Column(Text, nullable=True)


class TravelPlan(Base):
    __tablename__ = "travel_plans"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    destination_city = Column(String, nullable=False)
    hospital_id = Column(Integer, ForeignKey("hospitals.id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False)
    start_date = Column(String, nullable=False)
    duration_days = Column(Integer, default=5)
    itinerary_json = Column(JSON, nullable=False)
    total_estimated_cost = Column(Float, default=125000.0)

    user = relationship("User", back_populates="travel_plans")


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String, default="Medical Assistance Consultation")
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="conversations")
    messages = relationship("ChatMessage", back_populates="conversation", cascade="all, delete-orphan")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    sender = Column(String, nullable=False) # user or assistant
    text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    conversation = relationship("Conversation", back_populates="messages")


class MedicalKnowledge(Base):
    __tablename__ = "medical_knowledge"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    category = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    keywords = Column(Text, nullable=False)
    source_reference = Column(String, default="Verified Clinical Practice Guidelines")
