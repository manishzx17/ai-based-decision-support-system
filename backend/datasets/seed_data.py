"""
Demo Dataset for 12C - AI-Based Medical Travel Decision Support System
Contains realistic healthcare provider data, medical knowledge base for RAG, treatment cost matrix, emergency contacts, accommodations, and pharmacies across major medical hubs (Hyderabad, Chennai, Mumbai, Delhi, Bengaluru).
"""

SEED_HOSPITALS = [
    {
        "id": 1,
        "name": "Apollo Hospitals Jubilee Hills",
        "city": "Hyderabad",
        "state": "Telangana",
        "address": "Road No 72, Opposite Bharatiya Vidya Bhavan, Jubilee Hills, Hyderabad",
        "lat": 17.4325,
        "lng": 78.4071,
        "specialties": ["Cardiology", "Oncology", "Neurology", "Orthopedics", "Gastroenterology"],
        "rating": 4.9,
        "distance_km": 4.2,
        "insurance_accepted": ["Star Health", "HDFC ERGO", "ICICI Lombard", "Care Health", "Max Bupa"],
        "facilities": ["24x7 ICU", "Helipad", "International Patient Lounge", "Medical Translators", "Robotic Surgery"],
        "contact_phone": "+91 40 2360 7777",
        "availability_status": "High"
    },
    {
        "id": 2,
        "name": "Yashoda Hospitals Somajiguda",
        "city": "Hyderabad",
        "state": "Telangana",
        "address": "Raj Bhavan Road, Somajiguda, Hyderabad",
        "lat": 17.4238,
        "lng": 78.4583,
        "specialties": ["Neurology", "Cardiology", "Nephrology", "Pulmonology", "Organ Transplant"],
        "rating": 4.8,
        "distance_km": 6.1,
        "insurance_accepted": ["Star Health", "HDFC ERGO", "Care Health", "Niva Bupa"],
        "facilities": ["24x7 Emergency", "Dedicated Organ Transplant Unit", "PET-CT Scan", "Ambulance Fleet"],
        "contact_phone": "+91 40 4567 4567",
        "availability_status": "High"
    },
    {
        "id": 3,
        "name": "Fortis Hospital Bannerghatta",
        "city": "Bengaluru",
        "state": "Karnataka",
        "address": "154/9, Bannerghatta Road, Opposite IIMB, Bengaluru",
        "lat": 12.8954,
        "lng": 77.5988,
        "specialties": ["Cardiology", "Orthopedics", "Neurology", "Oncology"],
        "rating": 4.7,
        "distance_km": 8.5,
        "insurance_accepted": ["Star Health", "HDFC ERGO", "ICICI Lombard", "Reliance General"],
        "facilities": ["24x7 Cath Lab", "Joint Replacement Suite", "International Travel Desk"],
        "contact_phone": "+91 80 6621 4444",
        "availability_status": "Medium"
    },
    {
        "id": 4,
        "name": "Max Super Speciality Hospital Saket",
        "city": "Delhi",
        "state": "Delhi NCR",
        "address": "1, 2 Press Enclave Marg, Saket, New Delhi",
        "lat": 28.5284,
        "lng": 77.2110,
        "specialties": ["Oncology", "Cardiology", "Neurosurgery", "Gastroenterology", "Urology"],
        "rating": 4.9,
        "distance_km": 12.0,
        "insurance_accepted": ["Star Health", "HDFC ERGO", "ICICI Lombard", "Care Health", "Bupa Global"],
        "facilities": ["Comprehensive Cancer Center", "CyberKnife", "Bone Marrow Transplant Unit", "Interpreter Support"],
        "contact_phone": "+91 11 2651 5050",
        "availability_status": "High"
    },
    {
        "id": 5,
        "name": "Manipal Hospital HAL Road",
        "city": "Bengaluru",
        "state": "Karnataka",
        "address": "98, Rustam Bagh, Old Airport Road, Bengaluru",
        "lat": 12.9582,
        "lng": 77.6493,
        "specialties": ["Neurology", "Cardiology", "Pediatrics", "Orthopedics"],
        "rating": 4.6,
        "distance_km": 5.8,
        "insurance_accepted": ["Star Health", "ICICI Lombard", "Care Health"],
        "facilities": ["Trauma Center", "Comprehensive Rehab", "Foreign Currency Exchange"],
        "contact_phone": "+91 80 2502 4444",
        "availability_status": "High"
    }
]

SEED_DOCTORS = [
    {
        "id": 1,
        "hospital_id": 1,
        "name": "Dr. K. Srinivas Rao",
        "specialty": "Cardiology",
        "experience_years": 22,
        "qualification": "MBBS, MD, DM (Cardiology), FACC",
        "rating": 4.9,
        "consultation_fee": 1200.0,
        "availability_days": "Mon - Sat (10:00 AM - 4:00 PM)"
    },
    {
        "id": 2,
        "hospital_id": 1,
        "name": "Dr. Ananya Sharma",
        "specialty": "Oncology",
        "experience_years": 18,
        "qualification": "MBBS, MS, MCh (Surgical Oncology)",
        "rating": 4.9,
        "consultation_fee": 1500.0,
        "availability_days": "Mon, Wed, Fri (11:00 AM - 5:00 PM)"
    },
    {
        "id": 3,
        "hospital_id": 2,
        "name": "Dr. V. Ramesh Kumar",
        "specialty": "Neurology",
        "experience_years": 20,
        "qualification": "MBBS, MD, DM (Neurology)",
        "rating": 4.8,
        "consultation_fee": 1100.0,
        "availability_days": "Mon - Fri (9:00 AM - 3:00 PM)"
    },
    {
        "id": 4,
        "hospital_id": 3,
        "name": "Dr. Rajeshwar Reddy",
        "specialty": "Orthopedics",
        "experience_years": 16,
        "qualification": "MBBS, MS (Ortho), FRCS (Edin)",
        "rating": 4.7,
        "consultation_fee": 1000.0,
        "availability_days": "Tue, Thu, Sat (10:00 AM - 2:00 PM)"
    },
    {
        "id": 5,
        "hospital_id": 4,
        "name": "Dr. Meera Deshmukh",
        "specialty": "Gastroenterology",
        "experience_years": 19,
        "qualification": "MBBS, MD, DM (Gastroenterology)",
        "rating": 4.8,
        "consultation_fee": 1400.0,
        "availability_days": "Mon - Sat (10:30 AM - 4:30 PM)"
    }
]

SEED_PHARMACIES = [
    {
        "id": 1,
        "name": "Apollo Pharmacy 24x7 Jubilee Hills",
        "city": "Hyderabad",
        "address": "Opposite Apollo Hospitals Main Gate, Road No 72, Jubilee Hills",
        "lat": 17.4328,
        "lng": 78.4075,
        "distance_km": 0.1,
        "is_24_7": True,
        "contact_phone": "+91 40 2360 8888",
        "medication_stock_summary": "In-stock: Cardiac stents, Chemotherapy meds, Insulin, Antibiotics, Post-op dressing supplies."
    },
    {
        "id": 2,
        "name": "MedPlus Pharmacy Somajiguda",
        "city": "Hyderabad",
        "address": "Near Yashoda Hospital, Raj Bhavan Road, Somajiguda",
        "lat": 17.4240,
        "lng": 78.4586,
        "distance_km": 0.2,
        "is_24_7": True,
        "contact_phone": "+91 40 4000 5000",
        "medication_stock_summary": "In-stock: Neurological anti-epileptic drugs, Dialysis fluids, General prescriptions."
    },
    {
        "id": 3,
        "name": "Wellness Forever Bannerghatta",
        "city": "Bengaluru",
        "address": "Next to Fortis Hospital, Bannerghatta Road, Bengaluru",
        "lat": 12.8956,
        "lng": 77.5990,
        "distance_km": 0.15,
        "is_24_7": True,
        "contact_phone": "+91 80 4433 2211",
        "medication_stock_summary": "In-stock: Orthopedic pain relief, Post-knee replacement meds, Surgical equipment."
    }
]

SEED_TREATMENT_COSTS = [
    {
        "id": 1,
        "hospital_id": 1,
        "treatment_name": "Coronary Angioplasty (Single Stent)",
        "min_cost": 180000.0,
        "max_cost": 260000.0,
        "avg_cost": 220000.0,
        "room_type": "Private AC Suite"
    },
    {
        "id": 2,
        "hospital_id": 1,
        "treatment_name": "Coronary Artery Bypass Grafting (CABG)",
        "min_cost": 320000.0,
        "max_cost": 480000.0,
        "avg_cost": 400000.0,
        "room_type": "Private AC Deluxe"
    },
    {
        "id": 3,
        "hospital_id": 3,
        "treatment_name": "Total Knee Replacement (Single)",
        "min_cost": 210000.0,
        "max_cost": 310000.0,
        "avg_cost": 250000.0,
        "room_type": "Private AC Deluxe"
    },
    {
        "id": 4,
        "hospital_id": 4,
        "treatment_name": "Chemotherapy Cycle (Targeted Therapy)",
        "min_cost": 75000.0,
        "max_cost": 150000.0,
        "avg_cost": 110000.0,
        "room_type": "Daycare Suite"
    },
    {
        "id": 5,
        "hospital_id": 2,
        "treatment_name": "Craniotomy / Brain Tumor Resection",
        "min_cost": 350000.0,
        "max_cost": 550000.0,
        "avg_cost": 450000.0,
        "room_type": "Neuro ICU + Deluxe Room"
    }
]

SEED_INSURANCE = [
    {
        "id": 1,
        "name": "Star Health Insurance",
        "policy_type": "Comprehensive Medical Travel & Cashless Care",
        "coverage_details": "Covers pre-existing conditions after waiting period, inpatient hospitalization up to 100%, pre & post hospitalization 60 days.",
        "network_hospitals_count": 14000,
        "claim_contact": "1800 425 2255 / travelclaims@starhealth.in"
    },
    {
        "id": 2,
        "name": "HDFC ERGO Optima Secure",
        "policy_type": "2X Coverage Health Plan",
        "coverage_details": "Instant 2X coverage boost, cashless claim approval in 20 minutes, international emergency coverage add-on.",
        "network_hospitals_count": 12000,
        "claim_contact": "1800 266 6000 / care@hdfcergo.com"
    },
    {
        "id": 3,
        "name": "ICICI Lombard Health Care",
        "policy_type": "Complete Health Insurance",
        "coverage_details": "No sub-limits on room rent for superspecialty hospitals, ambulance cover up to INR 10,000, organ donor expenses covered.",
        "network_hospitals_count": 10500,
        "claim_contact": "1800 2666 / ihealth@icicilombard.com"
    }
]

SEED_ACCOMMODATIONS = [
    {
        "id": 1,
        "hospital_id": 1,
        "name": "Taj Jubilee Stays & Executive Apartments",
        "address": "Road No 36, Jubilee Hills, Hyderabad (800m from Apollo)",
        "price_per_night": 3800.0,
        "rating": 4.8,
        "distance_km": 0.8,
        "facilities": ["Wheelchair Accessible", "Patient Kitchenette", "Free Hospital Shuttle", "24/7 Nurse on Call"]
    },
    {
        "id": 2,
        "hospital_id": 1,
        "name": "Treebo Trend MedStay Jubilee",
        "address": "Near Peddamma Temple Metro, Jubilee Hills, Hyderabad",
        "price_per_night": 2200.0,
        "rating": 4.5,
        "distance_km": 1.2,
        "facilities": ["Elevator", "Free Breakfast", "Doctor Consultation Room", "High-speed Wi-Fi"]
    },
    {
        "id": 3,
        "hospital_id": 2,
        "name": "Fortune Park Raj Bhavan Stay",
        "address": "Somajiguda, Raj Bhavan Road, Hyderabad (400m from Yashoda)",
        "price_per_night": 3100.0,
        "rating": 4.7,
        "distance_km": 0.4,
        "facilities": ["Wheelchair Ramp", "Elevator", "Sterilized Linen", "Airport Pickup Service"]
    }
]

SEED_EMERGENCY = [
    {
        "id": 1,
        "city": "Hyderabad",
        "service_type": "Ambulance",
        "service_name": "GVK EMRI 108 Emergency Ambulance",
        "phone_number": "108",
        "address": "Statewide Emergency Response Center, Hyderabad"
    },
    {
        "id": 2,
        "city": "Hyderabad",
        "service_type": "Trauma Center",
        "service_name": "Apollo Emergency Trauma & Critical Care",
        "phone_number": "+91 40 1066",
        "address": "Road No 72, Jubilee Hills, Hyderabad"
    },
    {
        "id": 3,
        "city": "Hyderabad",
        "service_type": "Blood Bank",
        "service_name": "Chiranjeevi Charitable Blood Bank Central",
        "phone_number": "+91 40 2355 4545",
        "address": "Jubilee Hills Check Post, Hyderabad"
    },
    {
        "id": 4,
        "city": "Bengaluru",
        "service_type": "Ambulance",
        "service_name": "Karnataka 108 Cardiac Express Ambulance",
        "phone_number": "108",
        "address": "Central Command Desk, Bengaluru"
    }
]

SEED_KNOWLEDGE_BASE = [
    {
        "id": 1,
        "title": "Clinical Guidance on Coronary Angioplasty & Post-Stent Travel",
        "category": "Cardiology",
        "content": "Patients undergoing Percutaneous Coronary Intervention (PCI) with stent placement require dual antiplatelet therapy (DAPT) including Aspirin and Clopidogrel/Ticagrelor. Commercial air travel is generally safe 3-5 days post-uncomplicated PCI if left ventricular ejection fraction (LVEF) > 40%. Avoid heavy lifting (>5kg) for 14 days post-femoral or radial access.",
        "keywords": "angioplasty stent cardiology DAPT flight travel safety ejection fraction heart attack",
        "source_reference": "European Society of Cardiology (ESC) Travel Guidelines 2024"
    },
    {
        "id": 2,
        "title": "Oncology Travel Protocol & Chemotherapy Management",
        "category": "Oncology",
        "content": "Cancer patients traveling for chemotherapy or surgical resection should maintain complete records of absolute neutrophil count (ANC) and hemoglobin levels. Air travel should be timed 7-10 days after chemo infusion to avoid flying during nadir phase of neutropenia. Hydration and compression stockings are critical during long flights to mitigate deep vein thrombosis (DVT) risk.",
        "keywords": "chemotherapy cancer nadir neutropenia oncology DVT flight safety infection risk",
        "source_reference": "NCCN Clinical Practice Guidelines in Oncology"
    },
    {
        "id": 3,
        "title": "Cashless Insurance Claim Protocol for Medical Travelers",
        "category": "Insurance",
        "content": "To avail cashless hospitalization, pre-authorization request forms must be submitted to the hospital Third Party Administrator (TPA) desk at least 48 hours prior to planned admission. Key mandatory documents include: 1) Doctor Consultation Note, 2) Diagnostic Reports, 3) Estimated Cost Breakdown on Hospital Letterhead, 4) Government ID Card & Policy Card.",
        "keywords": "cashless insurance TPA claim pre-authorization document checklist hospitalization",
        "source_reference": "Insurance Regulatory and Development Authority of India (IRDAI) Guidelines"
    }
]
