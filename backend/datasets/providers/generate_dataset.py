"""
Dataset 3 Generator: Synthetic Research Benchmark Dataset of Healthcare Providers & Specialists.
Generates 60 hospitals and 210 doctors across 6 Indian medical travel hubs with explicit provenance metadata.
"""

import os
import json

BASE_CITIES = [
    {
        "city": "Hyderabad",
        "state": "Telangana",
        "center_lat": 17.3850,
        "center_lng": 78.4867,
        "hospitals": [
            {"name": "Apollo Hospitals Jubilee Hills", "area": "Jubilee Hills", "lat": 17.4325, "lng": 78.4071, "cost_tier": "Premium", "cost_tier_num": 420000.0, "accreditation": "NABH & JCI", "rating": 4.9, "quality_rating": 4.9, "icu_beds": 95},
            {"name": "Yashoda Hospitals Somajiguda", "area": "Somajiguda", "lat": 17.4238, "lng": 78.4583, "cost_tier": "Moderate", "cost_tier_num": 330000.0, "accreditation": "NABH", "rating": 4.8, "quality_rating": 4.7, "icu_beds": 80},
            {"name": "Care Hospitals Banjara Hills", "area": "Banjara Hills", "lat": 17.4156, "lng": 78.4485, "cost_tier": "Moderate", "cost_tier_num": 310000.0, "accreditation": "NABH", "rating": 4.7, "quality_rating": 4.6, "icu_beds": 65},
            {"name": "AIG Hospitals Gachibowli", "area": "Gachibowli", "lat": 17.4421, "lng": 78.3582, "cost_tier": "Premium", "cost_tier_num": 390000.0, "accreditation": "NABH & JCI", "rating": 4.9, "quality_rating": 4.9, "icu_beds": 90},
            {"name": "KIMS Hospitals Secunderabad", "area": "Secunderabad", "lat": 17.4375, "lng": 78.4983, "cost_tier": "Moderate", "cost_tier_num": 290000.0, "accreditation": "NABH", "rating": 4.6, "quality_rating": 4.6, "icu_beds": 75},
            {"name": "Basavatarakam Indo-American Cancer Hospital", "area": "Banjara Hills", "lat": 17.4201, "lng": 78.4350, "cost_tier": "Budget", "cost_tier_num": 220000.0, "accreditation": "NABH", "rating": 4.7, "quality_rating": 4.7, "icu_beds": 50},
            {"name": "Sunshine Hospitals Gachibowli", "area": "Gachibowli", "lat": 17.4489, "lng": 78.3695, "cost_tier": "Budget", "cost_tier_num": 240000.0, "accreditation": "NABH", "rating": 4.6, "quality_rating": 4.5, "icu_beds": 45},
            {"name": "Continental Hospitals Nanakramguda", "area": "Nanakramguda", "lat": 17.4190, "lng": 78.3428, "cost_tier": "Premium", "cost_tier_num": 380000.0, "accreditation": "NABH & JCI", "rating": 4.8, "quality_rating": 4.8, "icu_beds": 70},
            {"name": "Star Hospitals Banjara Hills", "area": "Banjara Hills", "lat": 17.4168, "lng": 78.4410, "cost_tier": "Moderate", "cost_tier_num": 320000.0, "accreditation": "NABH", "rating": 4.7, "quality_rating": 4.6, "icu_beds": 60},
            {"name": "MaxCure Medicover Hospitals Hitec City", "area": "Madhapur", "lat": 17.4475, "lng": 78.3762, "cost_tier": "Budget", "cost_tier_num": 230000.0, "accreditation": "NABH", "rating": 4.5, "quality_rating": 4.5, "icu_beds": 55}
        ]
    },
    {
        "city": "Bengaluru",
        "state": "Karnataka",
        "center_lat": 12.9716,
        "center_lng": 77.5946,
        "hospitals": [
            {"name": "Manipal Hospital Old Airport Road", "area": "Old Airport Road", "lat": 12.9592, "lng": 77.6534, "cost_tier": "Premium", "cost_tier_num": 430000.0, "accreditation": "NABH & JCI", "rating": 4.9, "quality_rating": 4.9, "icu_beds": 100},
            {"name": "Narayana Health City Bommasandra", "area": "Anekal Taluk", "lat": 12.8090, "lng": 77.6974, "cost_tier": "Budget", "cost_tier_num": 210000.0, "accreditation": "NABH & JCI", "rating": 4.8, "quality_rating": 4.8, "icu_beds": 140},
            {"name": "Fortis Hospital Bannerghatta Road", "area": "Bannerghatta Road", "lat": 12.8949, "lng": 77.5986, "cost_tier": "Premium", "cost_tier_num": 400000.0, "accreditation": "NABH & JCI", "rating": 4.8, "quality_rating": 4.8, "icu_beds": 80},
            {"name": "Aster CMI Hospital Hebbal", "area": "Hebbal", "lat": 13.0573, "lng": 77.5910, "cost_tier": "Moderate", "cost_tier_num": 340000.0, "accreditation": "NABH", "rating": 4.7, "quality_rating": 4.7, "icu_beds": 75},
            {"name": "Apollo Hospitals Bannerghatta Road", "area": "Bannerghatta Road", "lat": 12.8920, "lng": 77.6010, "cost_tier": "Premium", "cost_tier_num": 410000.0, "accreditation": "NABH & JCI", "rating": 4.8, "quality_rating": 4.8, "icu_beds": 85},
            {"name": "Sparsh Hospital Yeshwanthpur", "area": "Yeshwanthpur", "lat": 13.0232, "lng": 77.5510, "cost_tier": "Moderate", "cost_tier_num": 300000.0, "accreditation": "NABH", "rating": 4.6, "quality_rating": 4.6, "icu_beds": 60},
            {"name": "Sakra World Hospital Marathahalli", "area": "Bellandur", "lat": 12.9288, "lng": 77.6843, "cost_tier": "Premium", "cost_tier_num": 390000.0, "accreditation": "NABH", "rating": 4.7, "quality_rating": 4.7, "icu_beds": 70},
            {"name": "HCG Cancer Centre Kalinga Rao Road", "area": "Sampangi Rama Nagar", "lat": 12.9610, "lng": 77.5930, "cost_tier": "Moderate", "cost_tier_num": 320000.0, "accreditation": "NABH", "rating": 4.7, "quality_rating": 4.7, "icu_beds": 50},
            {"name": "St Johns Medical College Hospital", "area": "Koramangala", "lat": 12.9312, "lng": 77.6210, "cost_tier": "Budget", "cost_tier_num": 190000.0, "accreditation": "NABH", "rating": 4.5, "quality_rating": 4.5, "icu_beds": 90},
            {"name": "BGS Gleneagles Global Hospital Kengeri", "area": "Kengeri", "lat": 12.9056, "lng": 77.4988, "cost_tier": "Moderate", "cost_tier_num": 280000.0, "accreditation": "NABH", "rating": 4.6, "quality_rating": 4.6, "icu_beds": 65}
        ]
    },
    {
        "city": "Chennai",
        "state": "Tamil Nadu",
        "center_lat": 13.0827,
        "center_lng": 80.2707,
        "hospitals": [
            {"name": "Apollo Hospitals Greams Road", "area": "Thousand Lights", "lat": 13.0601, "lng": 80.2515, "cost_tier": "Premium", "cost_tier_num": 440000.0, "accreditation": "NABH & JCI", "rating": 4.9, "quality_rating": 4.9, "icu_beds": 120},
            {"name": "Fortis Malar Hospital Adyar", "area": "Adyar", "lat": 13.0067, "lng": 80.2571, "cost_tier": "Moderate", "cost_tier_num": 330000.0, "accreditation": "NABH", "rating": 4.7, "quality_rating": 4.6, "icu_beds": 60},
            {"name": "Gleneagles Global Health City Perumbakkam", "area": "Perumbakkam", "lat": 12.9022, "lng": 80.1989, "cost_tier": "Moderate", "cost_tier_num": 310000.0, "accreditation": "NABH", "rating": 4.8, "quality_rating": 4.8, "icu_beds": 85},
            {"name": "MIOT International Manapakkam", "area": "Manapakkam", "lat": 13.0238, "lng": 80.1802, "cost_tier": "Premium", "cost_tier_num": 380000.0, "accreditation": "NABH", "rating": 4.8, "quality_rating": 4.7, "icu_beds": 90},
            {"name": "MGM Healthcare Nelson Manickam Road", "area": "Aminjikarai", "lat": 13.0720, "lng": 80.2220, "cost_tier": "Premium", "cost_tier_num": 420000.0, "accreditation": "NABH & JCI", "rating": 4.9, "quality_rating": 4.9, "icu_beds": 95},
            {"name": "Kauvery Hospital Alwarpet", "area": "Alwarpet", "lat": 13.0370, "lng": 80.2540, "cost_tier": "Moderate", "cost_tier_num": 320000.0, "accreditation": "NABH", "rating": 4.7, "quality_rating": 4.7, "icu_beds": 55},
            {"name": "Dr. Rela Institute & Medical Centre", "area": "Chromepet", "lat": 12.9550, "lng": 80.1420, "cost_tier": "Premium", "cost_tier_num": 410000.0, "accreditation": "NABH & JCI", "rating": 4.9, "quality_rating": 4.9, "icu_beds": 85},
            {"name": "SIMS Hospital Vadapalani", "area": "Vadapalani", "lat": 13.0515, "lng": 80.2095, "cost_tier": "Moderate", "cost_tier_num": 300000.0, "accreditation": "NABH", "rating": 4.6, "quality_rating": 4.6, "icu_beds": 70},
            {"name": "Cancer Institute (WIA) Adyar", "area": "Adyar", "lat": 13.0080, "lng": 80.2470, "cost_tier": "Budget", "cost_tier_num": 180000.0, "accreditation": "NABH", "rating": 4.7, "quality_rating": 4.8, "icu_beds": 40},
            {"name": "Prashanth Super Speciality Hospital", "area": "Velachery", "lat": 12.9810, "lng": 80.2180, "cost_tier": "Budget", "cost_tier_num": 250000.0, "accreditation": "NABH", "rating": 4.5, "quality_rating": 4.5, "icu_beds": 45}
        ]
    },
    {
        "city": "Mumbai",
        "state": "Maharashtra",
        "center_lat": 19.0760,
        "center_lng": 72.8777,
        "hospitals": [
            {"name": "Hinduja Hospital Mahim", "area": "Mahim", "lat": 19.0330, "lng": 72.8398, "cost_tier": "Premium", "cost_tier_num": 450000.0, "accreditation": "NABH", "rating": 4.8, "quality_rating": 4.8, "icu_beds": 90},
            {"name": "Kokilaben Dhirubhai Ambani Hospital", "area": "Andheri West", "lat": 19.1311, "lng": 72.8252, "cost_tier": "Premium", "cost_tier_num": 470000.0, "accreditation": "NABH & JCI", "rating": 4.9, "quality_rating": 4.9, "icu_beds": 110},
            {"name": "Lilavati Hospital Bandra", "area": "Bandra West", "lat": 19.0514, "lng": 72.8285, "cost_tier": "Premium", "cost_tier_num": 440000.0, "accreditation": "NABH", "rating": 4.8, "quality_rating": 4.8, "icu_beds": 80},
            {"name": "Fortis Hospital Mulund", "area": "Mulund Goregaon Link Rd", "lat": 19.1601, "lng": 72.9395, "cost_tier": "Moderate", "cost_tier_num": 350000.0, "accreditation": "NABH & JCI", "rating": 4.7, "quality_rating": 4.7, "icu_beds": 75},
            {"name": "Tata Memorial Hospital Parel", "area": "Parel", "lat": 19.0048, "lng": 72.8427, "cost_tier": "Budget", "cost_tier_num": 180000.0, "accreditation": "NABH", "rating": 4.8, "quality_rating": 4.9, "icu_beds": 60},
            {"name": "Nanavati Max Super Speciality Hospital", "area": "Vile Parle", "lat": 19.0970, "lng": 72.8420, "cost_tier": "Premium", "cost_tier_num": 420000.0, "accreditation": "NABH", "rating": 4.7, "quality_rating": 4.7, "icu_beds": 85},
            {"name": "Sir H. N. Reliance Foundation Hospital", "area": "Girgaon", "lat": 18.9590, "lng": 72.8180, "cost_tier": "Premium", "cost_tier_num": 480000.0, "accreditation": "NABH & JCI", "rating": 4.9, "quality_rating": 4.9, "icu_beds": 100},
            {"name": "Global Hospital Parel", "area": "Parel", "lat": 19.0060, "lng": 72.8390, "cost_tier": "Moderate", "cost_tier_num": 340000.0, "accreditation": "NABH", "rating": 4.6, "quality_rating": 4.6, "icu_beds": 65},
            {"name": "Wockhardt Hospitals Mumbai Central", "area": "Mumbai Central", "lat": 18.9720, "lng": 72.8220, "cost_tier": "Moderate", "cost_tier_num": 320000.0, "accreditation": "NABH", "rating": 4.6, "quality_rating": 4.6, "icu_beds": 55},
            {"name": "Jupiter Hospital Thane", "area": "Thane West", "lat": 19.2080, "lng": 72.9720, "cost_tier": "Budget", "cost_tier_num": 270000.0, "accreditation": "NABH", "rating": 4.6, "quality_rating": 4.5, "icu_beds": 50}
        ]
    },
    {
        "city": "Delhi-NCR",
        "state": "Delhi",
        "center_lat": 28.6139,
        "center_lng": 77.2090,
        "hospitals": [
            {"name": "Indraprastha Apollo Hospitals Sarita Vihar", "area": "Sarita Vihar", "lat": 28.5392, "lng": 77.2917, "cost_tier": "Premium", "cost_tier_num": 450000.0, "accreditation": "NABH & JCI", "rating": 4.9, "quality_rating": 4.9, "icu_beds": 120},
            {"name": "Medanta The Medicity Gurugram", "area": "Sector 38, Gurugram", "lat": 28.4394, "lng": 77.0427, "cost_tier": "Premium", "cost_tier_num": 460000.0, "accreditation": "NABH & JCI", "rating": 4.9, "quality_rating": 4.9, "icu_beds": 150},
            {"name": "Max Super Speciality Hospital Saket", "area": "Saket", "lat": 28.5284, "lng": 77.2132, "cost_tier": "Premium", "cost_tier_num": 440000.0, "accreditation": "NABH & JCI", "rating": 4.8, "quality_rating": 4.8, "icu_beds": 90},
            {"name": "Fortis Memorial Research Institute Gurugram", "area": "Sector 44, Gurugram", "lat": 28.4595, "lng": 77.0724, "cost_tier": "Premium", "cost_tier_num": 430000.0, "accreditation": "NABH & JCI", "rating": 4.8, "quality_rating": 4.8, "icu_beds": 85},
            {"name": "All India Institute of Medical Sciences (AIIMS)", "area": "Ansari Nagar", "lat": 28.5672, "lng": 77.2100, "cost_tier": "Budget", "cost_tier_num": 150000.0, "accreditation": "NABH", "rating": 4.9, "quality_rating": 5.0, "icu_beds": 200},
            {"name": "Sir Ganga Ram Hospital Rajinder Nagar", "area": "Rajinder Nagar", "lat": 28.6380, "lng": 77.1890, "cost_tier": "Moderate", "cost_tier_num": 310000.0, "accreditation": "NABH", "rating": 4.7, "quality_rating": 4.8, "icu_beds": 80},
            {"name": "Artemis Hospitals Gurugram", "area": "Sector 51, Gurugram", "lat": 28.4320, "lng": 77.0850, "cost_tier": "Moderate", "cost_tier_num": 350000.0, "accreditation": "NABH & JCI", "rating": 4.7, "quality_rating": 4.7, "icu_beds": 70},
            {"name": "BLK-Max Super Speciality Hospital", "area": "Pusa Road", "lat": 28.6430, "lng": 77.1790, "cost_tier": "Moderate", "cost_tier_num": 340000.0, "accreditation": "NABH", "rating": 4.7, "quality_rating": 4.7, "icu_beds": 75},
            {"name": "Jaypee Hospital Noida", "area": "Sector 128, Noida", "lat": 28.5150, "lng": 77.3750, "cost_tier": "Budget", "cost_tier_num": 260000.0, "accreditation": "NABH", "rating": 4.6, "quality_rating": 4.6, "icu_beds": 60},
            {"name": "Manipal Hospital Dwarka", "area": "Dwarka Sector 6", "lat": 28.5870, "lng": 77.0650, "cost_tier": "Moderate", "cost_tier_num": 320000.0, "accreditation": "NABH", "rating": 4.7, "quality_rating": 4.7, "icu_beds": 65}
        ]
    },
    {
        "city": "Kolkata",
        "state": "West Bengal",
        "center_lat": 22.5726,
        "center_lng": 88.3639,
        "hospitals": [
            {"name": "Apollo Gleneagles Hospitals Salt Lake", "area": "Salt Lake", "lat": 22.5744, "lng": 88.4067, "cost_tier": "Premium", "cost_tier_num": 390000.0, "accreditation": "NABH & JCI", "rating": 4.8, "quality_rating": 4.8, "icu_beds": 80},
            {"name": "Fortis Hospital Anandapur", "area": "Anandapur", "lat": 22.5173, "lng": 88.4042, "cost_tier": "Moderate", "cost_tier_num": 310000.0, "accreditation": "NABH", "rating": 4.7, "quality_rating": 4.7, "icu_beds": 70},
            {"name": "Medica Superspecialty Hospital Mukundapur", "area": "Mukundapur", "lat": 22.4930, "lng": 88.3970, "cost_tier": "Moderate", "cost_tier_num": 290000.0, "accreditation": "NABH", "rating": 4.6, "quality_rating": 4.6, "icu_beds": 65},
            {"name": "AMRI Hospitals Dhakuria", "area": "Dhakuria", "lat": 22.5110, "lng": 88.3650, "cost_tier": "Moderate", "cost_tier_num": 300000.0, "accreditation": "NABH", "rating": 4.6, "quality_rating": 4.5, "icu_beds": 60},
            {"name": "Tata Medical Center Rajarhat", "area": "Rajarhat", "lat": 22.5850, "lng": 88.4720, "cost_tier": "Budget", "cost_tier_num": 200000.0, "accreditation": "NABH", "rating": 4.8, "quality_rating": 4.9, "icu_beds": 50},
            {"name": "Rabindranath Tagore International Institute (RTIICS)", "area": "Mukundapur", "lat": 22.4850, "lng": 88.3980, "cost_tier": "Budget", "cost_tier_num": 210000.0, "accreditation": "NABH", "rating": 4.7, "quality_rating": 4.7, "icu_beds": 80},
            {"name": "Peerless Hospital Panchasayar", "area": "Panchasayar", "lat": 22.4860, "lng": 88.3920, "cost_tier": "Budget", "cost_tier_num": 230000.0, "accreditation": "NABH", "rating": 4.5, "quality_rating": 4.5, "icu_beds": 55},
            {"name": "Belle Vue Clinic Loudon Street", "area": "Loudon Street", "lat": 22.5440, "lng": 88.3540, "cost_tier": "Moderate", "cost_tier_num": 320000.0, "accreditation": "NABH", "rating": 4.6, "quality_rating": 4.6, "icu_beds": 50},
            {"name": "Ruby General Hospital Kasba", "area": "Kasba", "lat": 22.5140, "lng": 88.4020, "cost_tier": "Budget", "cost_tier_num": 240000.0, "accreditation": "NABH", "rating": 4.5, "quality_rating": 4.4, "icu_beds": 45},
            {"name": "Desun Hospital EM Bypass", "area": "Kasba Golpark", "lat": 22.5170, "lng": 88.4030, "cost_tier": "Moderate", "cost_tier_num": 280000.0, "accreditation": "NABH", "rating": 4.6, "quality_rating": 4.5, "icu_beds": 65}
        ]
    }
]

ALL_SPECIALTIES = [
    "Cardiology", "Oncology", "Orthopedics", "Neurology",
    "Gastroenterology", "Nephrology", "Pulmonology", "General Medicine"
]

FACILITIES_MAP = {
    "Cardiology": ["24x7 Cath Lab", "Cardiac ICU (CCU)", "Robotic Surgery", "3D Echocardiography"],
    "Oncology": ["PET-CT Scan", "Linear Accelerator (TrueBeam)", "Bone Marrow Transplant Unit", "Chemotherapy Infusion Lounge"],
    "Orthopedics": ["Robotic Joint Arthroplasty Suite", "Orthopedic Trauma ICU", "Computer-Assisted Navigation", "Hydrotherapy Rehab"],
    "Neurology": ["Intraoperative MRI / CT", "Neuro ICU", "Biplane Neuro-Angiography", "Stereotactic Radiosurgery"],
    "Gastroenterology": ["Advanced Endoscopy Suite", "Endoscopic Ultrasound (EUS)", "Liver ICU", "ERCP / SpyGlass"],
    "Nephrology": ["24x7 Dialysis Unit", "Isolated Hep-B/C Dialysis", "Kidney Transplant ICU", "CRRT / Plasmapheresis"],
    "Pulmonology": ["Sleep Lab", "EBUS Bronchoscopy", "Respiratory ICU", "Pulmonary Rehabilitation Unit"],
    "General Medicine": ["24x7 Emergency Room", "Medical ICU", "Advanced Diagnostic Pathology", "Executive Health Lounge"]
}

TREATMENT_CAPABILITIES_MAP = {
    "Cardiology": ["Complex Multivessel PCI", "TAVR / Valve Replacement", "Coronary Bypass (CABG)", "Electrophysiology Ablation"],
    "Oncology": ["SBRT / IMRT Radiation", "Targeted Immunotherapy", "Surgical Oncologic Resection", "CAR-T & Autologous BMT"],
    "Orthopedics": ["Minimally Invasive TKA / THA", "Complex Revision Arthroplasty", "Arthroscopic Ligament Reconstruction", "Spinal Fusion"],
    "Neurology": ["Micro-Neurosurgical Craniotomy", "Mechanical Thrombectomy for Stroke", "Deep Brain Stimulation (DBS)", "Epilepsy Surgery"],
    "Gastroenterology": ["Therapeutic Endoscopic Hemostasis", "Laparoscopic GI Resection", "Living Donor Liver Transplant", "Bariatric Surgery"],
    "Nephrology": ["Living Donor Kidney Transplant", "Maintenance Hemodialysis", "Peritoneal Dialysis Catheter Placement", "AV Fistula Creation"],
    "Pulmonology": ["Advanced COPD Management", "Bronchial Thermoplasty", "High Altitude Fitness Evaluation", "Severe Asthma Biologics"],
    "General Medicine": ["Multi-organ Sepsis Management", "Diabetic Ketoacidosis Protocol", "Cardiovascular Risk Stratification", "Pre-operative Clearance"]
}

INSURANCE_PROVIDERS = [
    "Star Health", "HDFC ERGO", "ICICI Lombard", "Care Health", "Niva Bupa", "Bajaj Allianz"
]

DOCTOR_NAMES = [
    ("Dr. Rajeshwar Rao", "Male", "MBBS, MD, DM (Cardiology), FACC", 24, 1500),
    ("Dr. Ananya Sen", "Female", "MBBS, MD, DNB (Medical Oncology), ECMO", 18, 1400),
    ("Dr. Vikramaditya Reddy", "Male", "MBBS, MS (Orthopaedics), MCh, FRCS", 22, 1600),
    ("Dr. Sunita Deshmukh", "Female", "MBBS, MCh (Neurosurgery), FAANS", 20, 1800),
    ("Dr. Suresh Nambiar", "Male", "MBBS, MD, DM (Gastroenterology)", 19, 1300),
    ("Dr. Priya Balasubramanian", "Female", "MBBS, MD, DM (Nephrology), FISN", 17, 1200),
    ("Dr. Arvind Swaminathan", "Male", "MBBS, MD (Pulmonary Medicine), FCCP", 16, 1100),
    ("Dr. Kavita Mukherjee", "Female", "MBBS, MD (General Medicine), FACP", 15, 1000)
]

def generate_dataset():
    hospitals = []
    doctors = []
    h_id = 1
    d_id = 1

    for hub in BASE_CITIES:
        city = hub["city"]
        state = hub["state"]
        
        for h_info in hub["hospitals"]:
            # Assign specialties
            if "Cancer" in h_info["name"]:
                specs = ["Oncology", "General Medicine", "Pulmonology", "Gastroenterology"]
            elif "Heart" in h_info["name"] or "Cardio" in h_info["name"]:
                specs = ["Cardiology", "Neurology", "Nephrology", "General Medicine"]
            elif "Orthop" in h_info["name"] or "Bone" in h_info["name"] or "Joint" in h_info["name"] or "Sparsh" in h_info["name"]:
                specs = ["Orthopedics", "Neurology", "Cardiology", "General Medicine"]
            else:
                specs = list(ALL_SPECIALTIES)

            # Assign facilities & treatment capabilities
            facs = ["24x7 Emergency", "24x7 ICU", "Blood Bank", "Radiology (MRI/CT)"]
            caps = []
            for s in specs[:5]:
                facs.extend(FACILITIES_MAP[s][:2])
                caps.extend(TREATMENT_CAPABILITIES_MAP[s][:2])
            
            facs = list(dict.fromkeys(facs))
            caps = list(dict.fromkeys(caps))

            # Insurance
            if h_info["cost_tier"] == "Premium":
                ins = INSURANCE_PROVIDERS[:]
            elif h_info["cost_tier"] == "Moderate":
                ins = INSURANCE_PROVIDERS[:4]
            else:
                ins = ["Star Health", "Care Health", "Bajaj Allianz", "Government Ayushman"]

            hospital_record = {
                "id": h_id,
                "name": h_info["name"],
                "city": city,
                "state": state,
                "address": f"{h_info['area']}, {city}, {state}",
                "lat": h_info["lat"],
                "lng": h_info["lng"],
                "specialties": specs,
                "facilities": facs,
                "treatment_capabilities": caps,
                "cost_tier": h_info["cost_tier"],
                "estimated_cost_tier": h_info["cost_tier_num"],
                "quality_rating": h_info["quality_rating"],
                "rating": h_info["rating"],
                "accreditation": h_info["accreditation"],
                "insurance_accepted": ins,
                "icu_beds": h_info["icu_beds"],
                "emergency_24x7": True,
                "contact_phone": f"+91 {city[:3].upper()} {h_id * 1111:04d}",
                "availability_status": "Operational",
                "provenance": {
                    "is_synthetic_benchmark": True,
                    "dataset_label": "Synthetic Research Benchmark Dataset for Decision Support Algorithm Evaluation",
                    "benchmark_purpose": "Algorithmic decision support evaluation",
                    "directory_curated_fields": ["name", "city", "state", "address", "lat", "lng", "contact_phone"],
                    "synthetic_benchmark_fields": ["quality_rating", "rating", "cost_tier", "estimated_cost_tier", "icu_beds", "treatment_capabilities"],
                    "source": "Curated Indian Hospital Registry & Synthetic Benchmark Simulator"
                }
            }
            hospitals.append(hospital_record)

            # Generate 3 to 4 specialized doctors per hospital
            # Assign doctors matching hospital specialties
            num_docs = 4 if h_id % 2 == 0 else 3
            for doc_idx in range(num_docs):
                spec = specs[doc_idx % len(specs)]
                doc_template = DOCTOR_NAMES[doc_idx % len(DOCTOR_NAMES)]
                
                # Variation in experience, qualification, fee based on cost tier
                fee_multiplier = 1.2 if h_info["cost_tier"] == "Premium" else (0.8 if h_info["cost_tier"] == "Budget" else 1.0)
                fee = int(doc_template[4] * fee_multiplier)
                exp = doc_template[3] + (h_id % 5) - 2

                expertise_candidates = TREATMENT_CAPABILITIES_MAP.get(spec, ["General Clinical Care"])
                expertise = [expertise_candidates[doc_idx % len(expertise_candidates)]]

                doctor_record = {
                    "id": d_id,
                    "hospital_id": h_id,
                    "hospital_name": h_info["name"],
                    "name": f"{doc_template[0]} ({city[:3]})",
                    "specialty": spec,
                    "expertise": expertise,
                    "experience_years": max(exp, 8),
                    "qualification": doc_template[2],
                    "rating": round(min(4.5 + (d_id % 5) * 0.1, 5.0), 1),
                    "consultation_fee": fee,
                    "availability_days": "Mon, Wed, Fri" if d_id % 2 == 0 else "Tue, Thu, Sat",
                    "provenance": {
                        "is_synthetic_benchmark": True,
                        "dataset_label": "Synthetic Research Benchmark Dataset for Decision Support Algorithm Evaluation",
                        "benchmark_purpose": "Algorithmic decision support evaluation",
                        "directory_curated_fields": ["hospital_name", "specialty"],
                        "synthetic_benchmark_fields": ["name", "experience_years", "qualification", "rating", "consultation_fee"],
                        "source": "Synthetic Doctor Profile Generator for Algorithmic Ranking Evaluation"
                    }
                }
                doctors.append(doctor_record)
                d_id += 1

            h_id += 1

    return hospitals, doctors


def save_dataset():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    hospitals, doctors = generate_dataset()

    hospitals_file = os.path.join(current_dir, "hospitals.json")
    doctors_file = os.path.join(current_dir, "doctors.json")

    with open(hospitals_file, "w", encoding="utf-8") as f:
        json.dump(hospitals, f, indent=2, ensure_ascii=False)

    with open(doctors_file, "w", encoding="utf-8") as f:
        json.dump(doctors, f, indent=2, ensure_ascii=False)

    print(f"Generated {len(hospitals)} hospitals -> {hospitals_file}")
    print(f"Generated {len(doctors)} doctors -> {doctors_file}")


if __name__ == "__main__":
    save_dataset()
