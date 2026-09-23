"""
Demo Dataset for 12C - AI-Based Medical Travel Decision Support System
Contains realistic healthcare provider data, medical knowledge base for RAG, treatment cost matrix, emergency contacts, accommodations, and pharmacies across major medical hubs (Hyderabad, Chennai, Mumbai, Delhi, Bengaluru).
"""

from .providers_data import HOSPITALS_DATA, DOCTORS_DATA

SEED_HOSPITALS = HOSPITALS_DATA
SEED_DOCTORS = DOCTORS_DATA


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
    },
    {
        "id": 4,
        "name": "Apollo Pharmacy 24x7 Saket",
        "city": "Delhi",
        "address": "Adjacent to Max Super Speciality Hospital, Press Enclave Road, Saket",
        "lat": 28.5273,
        "lng": 77.2159,
        "distance_km": 0.1,
        "is_24_7": True,
        "contact_phone": "+91 11 2651 5050",
        "medication_stock_summary": "In-stock: Chemotherapy meds, Oncology supportive care, Cardiac stents, Post-op ICU dressings."
    },
    {
        "id": 5,
        "name": "Wellness Forever 24x7 Parel",
        "city": "Mumbai",
        "address": "Near Tata Memorial Hospital, Dr. E Borges Road, Parel",
        "lat": 19.0034,
        "lng": 72.8427,
        "distance_km": 0.2,
        "is_24_7": True,
        "contact_phone": "+91 22 2417 7000",
        "medication_stock_summary": "In-stock: Targeted cancer drugs, Immunotherapy biologics, Pain management, Antiemetic infusions."
    },
    {
        "id": 6,
        "name": "Apollo Pharmacy 24x7 Greams Road",
        "city": "Chennai",
        "address": "Near Apollo Main Hospital, Greams Lane, Thousand Lights",
        "lat": 13.0604,
        "lng": 80.2496,
        "distance_km": 0.1,
        "is_24_7": True,
        "contact_phone": "+91 44 2829 0200",
        "medication_stock_summary": "In-stock: Cardiac medication, Heparin, Insulin analogs, Broad-spectrum antibiotics, Post-CABG recovery kits."
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
    # Apollo Hospitals Jubilee Hills (Hospital ID 1)
    {
        "id": 1,
        "hospital_id": 1,
        "name": "Taj Jubilee Stays & Executive Apartments",
        "address": "Road No 36, Jubilee Hills, Hyderabad (800m from Apollo)",
        "price_per_night": 3800.0,
        "rating": 4.8,
        "distance_km": 0.8,
        "facilities": ["Wheelchair Accessible", "Patient Kitchenette", "Free Hospital Shuttle", "24/7 Nurse on Call", "Elevator"]
    },
    {
        "id": 2,
        "hospital_id": 1,
        "name": "Treebo Trend MedStay Jubilee",
        "address": "Near Peddamma Temple Metro, Jubilee Hills, Hyderabad",
        "price_per_night": 1950.0,
        "rating": 4.5,
        "distance_km": 1.2,
        "facilities": ["Elevator", "Free Breakfast", "Doctor Consultation Room", "High-speed Wi-Fi"]
    },
    {
        "id": 3,
        "hospital_id": 1,
        "name": "ITC Kohenur Medical Recovery Suites",
        "address": "HITEC City - Jubilee Enclave, Hyderabad (2.5km from Apollo)",
        "price_per_night": 6500.0,
        "rating": 4.9,
        "distance_km": 2.5,
        "facilities": ["Wheelchair Accessible", "Elevator", "24/7 Nurse on Call", "Dietitian Meal Service", "Dedicated Medical Attendant"]
    },
    {
        "id": 4,
        "hospital_id": 1,
        "name": "Jubilee Care Guest House",
        "address": "Road No 72, Jubilee Hills, Hyderabad (350m from Apollo Gate 2)",
        "price_per_night": 1400.0,
        "rating": 4.3,
        "distance_km": 0.35,
        "facilities": ["Wheelchair Ramp", "Patient Kitchenette", "Ground Floor Access"]
    },

    # Yashoda Hospitals Somajiguda (Hospital ID 2)
    {
        "id": 5,
        "hospital_id": 2,
        "name": "Fortune Park Raj Bhavan Stay",
        "address": "Somajiguda, Raj Bhavan Road, Hyderabad (400m from Yashoda)",
        "price_per_night": 3100.0,
        "rating": 4.7,
        "distance_km": 0.4,
        "facilities": ["Wheelchair Accessible", "Elevator", "Sterilized Linen", "Airport Pickup Service", "Patient Kitchenette"]
    },
    {
        "id": 6,
        "hospital_id": 2,
        "name": "Somajiguda MedResidency Budget Inn",
        "address": "Near Raj Bhavan Post Office, Somajiguda, Hyderabad",
        "price_per_night": 1600.0,
        "rating": 4.4,
        "distance_km": 0.6,
        "facilities": ["Elevator", "Doctor on Call", "Wheelchair Ramp", "Low-Sodium Meal Plan"]
    },
    {
        "id": 7,
        "hospital_id": 2,
        "name": "The Park Hyderabad Medical Suite",
        "address": "Somajiguda Lakefront, Raj Bhavan Road, Hyderabad",
        "price_per_night": 5400.0,
        "rating": 4.8,
        "distance_km": 1.2,
        "facilities": ["Wheelchair Accessible", "Elevator", "24/7 Nurse on Call", "Oxygen Support Enabled", "Dietary Customization"]
    },

    # Care Hospital Banjara Hills (Hospital ID 3)
    {
        "id": 8,
        "hospital_id": 3,
        "name": "Banjara Comforts Care Stay",
        "address": "Road No 1, Banjara Hills, Hyderabad (500m from Care Hospital)",
        "price_per_night": 1900.0,
        "rating": 4.5,
        "distance_km": 0.5,
        "facilities": ["Elevator", "Wheelchair Ramp", "Emergency Call Button", "Free Wi-Fi"]
    },
    {
        "id": 9,
        "hospital_id": 3,
        "name": "Radisson Blu Plaza Medical Wing",
        "address": "Banjara Hills Main Road, Hyderabad (1.1km from Care)",
        "price_per_night": 4500.0,
        "rating": 4.8,
        "distance_km": 1.1,
        "facilities": ["Wheelchair Accessible", "Elevator", "24/7 Nurse on Call", "Patient Kitchenette", "Hospital Shuttle"]
    },

    # Fortis Hospital Bannerghatta (Hospital ID 11)
    {
        "id": 10,
        "hospital_id": 11,
        "name": "Bannerghatta MedStay Executive Suites",
        "address": "Opposite Fortis Main Gate, Bannerghatta Road, Bengaluru",
        "price_per_night": 2800.0,
        "rating": 4.7,
        "distance_km": 0.3,
        "facilities": ["Wheelchair Accessible", "Elevator", "Patient Kitchenette", "Free Hospital Shuttle", "24/7 Nurse on Call"]
    },
    {
        "id": 11,
        "hospital_id": 11,
        "name": "Ibis Bengaluru South Care Stay",
        "address": "Bannerghatta Link Road, Bengaluru",
        "price_per_night": 1950.0,
        "rating": 4.4,
        "distance_km": 1.2,
        "facilities": ["Elevator", "Wheelchair Accessible", "High-speed Wi-Fi"]
    },

    # Manipal Hospital Old Airport Road (Hospital ID 12)
    {
        "id": 12,
        "hospital_id": 12,
        "name": "The Leela Health Residency",
        "address": "Old Airport Road, Kodihalli, Bengaluru (800m from Manipal)",
        "price_per_night": 6800.0,
        "rating": 4.9,
        "distance_km": 0.8,
        "facilities": ["Wheelchair Accessible", "Elevator", "24/7 Nurse on Call", "Private Medical Escort", "Custom Therapeutic Meals"]
    },
    {
        "id": 13,
        "hospital_id": 12,
        "name": "Indiranagar Recovery Home Stay",
        "address": "100 Feet Road, Indiranagar, Bengaluru (1.5km from Manipal)",
        "price_per_night": 1850.0,
        "rating": 4.5,
        "distance_km": 1.5,
        "facilities": ["Wheelchair Ramp", "Elevator", "Patient Kitchenette", "Doctor on Call"]
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
        "title": "Clinical Guidance on Coronary Angioplasty, Stents & Commercial Air Travel",
        "category": "Cardiology",
        "organization": "European Society of Cardiology (ESC)",
        "content": "Patients undergoing uncomplicated Percutaneous Coronary Intervention (PCI) with drug-eluting stent placement may safely undertake commercial air travel 3 to 5 days post-procedure provided left ventricular ejection fraction (LVEF) is greater than 40% and no residual ischemia or arrhythmias are present. Strict adherence to Dual Antiplatelet Therapy (DAPT) with Aspirin and P2Y12 inhibitors (Clopidogrel, Ticagrelor) is required. Heavy exertion and lifting luggage exceeding 5 kg should be avoided for 14 days.",
        "keywords": "angioplasty stent cardiology DAPT flight air travel LVEF LAD RCA PCI coronary artery disease",
        "source_reference": "Knuuti J, et al. 2019/2024 ESC Guidelines for Chronic Coronary Syndromes. Eur Heart J.",
        "reference_url": "https://www.escardio.org/Guidelines/Clinical-Practice-Guidelines/Chronic-Coronary-Syndromes"
    },
    {
        "id": 2,
        "title": "Dual Antiplatelet Therapy (DAPT) & Post-PCI Revascularization Travel Precautions",
        "category": "Cardiology",
        "organization": "American College of Cardiology / American Heart Association (ACC/AHA)",
        "content": "Following coronary revascularization via PCI, patients must maintain uninterrupted DAPT for a minimum of 6 to 12 months unless prohibitive bleeding risk occurs. During medical travel, patients must carry sufficient medication in original prescription bottles in carry-on luggage. In case of flight delays, medication schedules must be maintained using home-time alarms. Patients with active angina CCS Class III or IV should defer non-emergency travel until stabilized.",
        "keywords": "revascularization DAPT aspirin clopidogrel ticagrelor travel carry-on angina cardiology",
        "source_reference": "Lawton JS, et al. 2021 ACC/AHA/SCAI Guideline for Coronary Artery Revascularization. J Am Coll Cardiol. 2022;79(2):e21-e129.",
        "reference_url": "https://www.jacc.org/doi/10.1016/j.jacc.2021.09.006"
    },
    {
        "id": 3,
        "title": "Commercial Aviation Fitness to Fly Following Cardiovascular Incidents",
        "category": "Cardiology",
        "organization": "International Air Transport Association (IATA)",
        "content": "The IATA Medical Manual classifies cardiovascular fitness for passenger flights: Uncomplicated PCI allows air travel after 3 days. Uncomplicated STEMI/NSTEMI treated with successful reperfusion requires 7 to 10 days wait with exercise tolerance equivalent to climbing one flight of stairs without dyspnea. Coronary Artery Bypass Graft (CABG) surgery requires at least 10 to 14 days and radiographic clearance of pneumothorax before air transit.",
        "keywords": "IATA fitness to fly myocardial infarction PCI CABG heart bypass airline medical clearance",
        "source_reference": "IATA Medical Advisory Group. Medical Manual (14th Edition). Section 2.2: Cardiovascular Disorders.",
        "reference_url": "https://www.iata.org/en/programs/safety/health/medical-manual/"
    },
    {
        "id": 4,
        "title": "Fitness to Fly with Valvular Heart Disease and Anticoagulation",
        "category": "Cardiology",
        "organization": "American Heart Association / American College of Cardiology (AHA/ACC)",
        "content": "Patients with mechanical prosthetic heart valves traveling across international regions must verify International Normalized Ratio (INR) stability within therapeutic target (2.5 - 3.5 depending on valve position) within 48 to 72 hours prior to departure. Patients on oral anticoagulants (Warfarin, DOACs) must maintain adequate hydration and avoid prolonged immobility to prevent thromboembolism.",
        "keywords": "valvular heart disease prosthetic valve anticoagulation INR warfarin DOAC flight safety cardiology",
        "source_reference": "Otto CM, et al. 2020 ACC/AHA Guideline for the Management of Patients With Valvular Heart Disease. Circulation. 2021;143(5):e72-e227.",
        "reference_url": "https://www.ahajournals.org/doi/10.1161/CIR.0000000000000923"
    },
    {
        "id": 5,
        "title": "Total Knee Arthroplasty (TKA) Rehabilitation & Early Travel Safety",
        "category": "Orthopedics",
        "organization": "American Academy of Orthopaedic Surgeons (AAOS)",
        "content": "Elective Total Knee Arthroplasty (TKA) patients planning medical travel should achieve stable independent mobilization with assistive devices before departure. Long-distance car or rail travel is discouraged within the first 7 to 14 days without frequent mobility breaks every 60 minutes. Deep venous thrombosis (DVT) prophylaxis with pharmacologic agents (low molecular weight heparin, DOACs, or aspirin) and mechanical calf compression is mandatory for at least 35 days post-surgery.",
        "keywords": "total knee arthroplasty TKA knee replacement osteoarthritis DVT prophylaxis mobilization orthopedics",
        "source_reference": "Mont MA, et al. Surgical Management of Osteoarthritis of the Knee: Evidence-Based Clinical Practice Guideline. J Am Acad Orthop Surg. 2020.",
        "reference_url": "https://www.aaos.org/quality/quality-programs/lower-extremity-programs/osteoarthritis-of-the-knee/"
    },
    {
        "id": 6,
        "title": "Venous Thromboembolic Disease Prevention for Traveling Joint Replacement Patients",
        "category": "Orthopedics",
        "organization": "American Academy of Orthopaedic Surgeons (AAOS)",
        "content": "Patients undergoing total joint arthroplasty face heightened risk of pulmonary embolism and deep vein thrombosis during prolonged travel (>4 hours). AAOS guidelines recommend: 1) Graduated knee-high compression stockings (15-20 mmHg), 2) Continuous hydration avoiding caffeine and alcohol, 3) Frequent seated ankle-pumps (10 repetitions every 30 minutes), and 4) Scheduled anticoagulant intake as prescribed by the operating orthopedic surgeon.",
        "keywords": "DVT prevention pulmonary embolism joint replacement compression stockings flight travel orthopedics",
        "source_reference": "AAOS Clinical Practice Guideline: Preventing Venous Thromboembolic Disease in Patients Undergoing Elective Hip and Knee Arthroplasty.",
        "reference_url": "https://www.aaos.org/quality/quality-programs/lower-extremity-programs/venous-thromboembolic-disease/"
    },
    {
        "id": 7,
        "title": "Flight Timing and Cast Precautions Following Orthopaedic Procedures",
        "category": "Orthopedics",
        "organization": "British Orthopaedic Association (BOA)",
        "content": "For patients with rigid plaster casts following fracture reduction or surgery, airlines require rigid casts to be bivalved (split along their full length) if flying within 48 hours of application to prevent acute compartment syndrome caused by low cabin pressure swelling. Commercial air travel after major hip or knee reconstruction should ideally be delayed until 6 weeks post-op unless direct clearance and medical escort are arranged.",
        "keywords": "orthopaedic surgery plaster cast compartment syndrome bivalved cast airline travel BOA",
        "source_reference": "BOA Advisory Guidelines on Patient Travel Following Orthopaedic Surgery and Lower Limb Immobilisation.",
        "reference_url": "https://www.boa.ac.uk/resources/knowledge-hub/flying-after-orthopaedic-surgery.html"
    },
    {
        "id": 8,
        "title": "Airport Security and Metal Detection with Orthopedic Implants",
        "category": "Orthopedics",
        "organization": "American Academy of Orthopaedic Surgeons (AAOS)",
        "content": "Modern orthopedic implants (cobalt-chromium, titanium, ceramic, and ultra-high-molecular-weight polyethylene) in total knee or hip replacements frequently trigger airport millimeter-wave body scanners and metal detectors. Patients should carry an implant verification card or surgeon discharge summary indicating operative date, hospital, and implant manufacturer to facilitate security screening.",
        "keywords": "implant card airport security metal detector joint replacement knee hip titanium scanner",
        "source_reference": "AAOS Patient Safety Committee Guidance: Traveling with Total Joint Replacements and Security Screening.",
        "reference_url": "https://orthoinfo.aaos.org/en/treatment/traveling-with-a-joint-replacement/"
    },
    {
        "id": 9,
        "title": "Post-Craniotomy Aviation Safety and Pneumocephalus Risk",
        "category": "Neurology",
        "organization": "Congress of Neurological Surgeons (CNS)",
        "content": "Following craniotomy for brain tumor resection (meningioma, glioma), intracranial surgery introduces intracranial air (pneumocephalus). According to Boyle's Law, trapped gas expands by approximately 30% at commercial cruising altitudes (6,000-8,000 ft cabin equivalent), risking tension pneumocephalus, elevated intracranial pressure, and brain herniation. Air travel is contraindicated until complete radiographic resorption of intracranial air is confirmed on CT, typically 14 to 21 days post-procedure.",
        "keywords": "craniotomy meningioma brain tumor pneumocephalus intracranial pressure air travel neurosurgery",
        "source_reference": "CNS Systematic Review and Evidence-Based Guideline on the Timing of Air Travel Following Craniotomy. Neurosurgery.",
        "reference_url": "https://www.cns.org/guidelines/guidelines-detail/post-craniotomy-air-travel"
    },
    {
        "id": 10,
        "title": "Seizure Management and Anti-Seizure Drug Adherence Across Time Zones",
        "category": "Neurology",
        "organization": "American Academy of Neurology (AAN)",
        "content": "Patients with neurological disorders or post-operative seizure risk on anti-seizure medications (such as Levetiracetam, Carbamazepine, Valproate) must maintain uniform dosing intervals during cross-border travel. Crossing time zones should not cause dose gaps: when traveling eastward, dosing intervals shorten slightly; traveling westward, an additional intermediate half-dose may be guided by the neurologist. Sleep deprivation and jet lag are known seizure triggers; adequate in-flight sleep is essential.",
        "keywords": "seizure epilepsy levetiracetam anti-seizure medication time zone jet lag sleep deprivation neurology",
        "source_reference": "Harden CL, et al. Practice parameter update: Management issues for epilepsy traveling across time zones. Neurology.",
        "reference_url": "https://www.aan.com/Guidelines/home/GetGuidelineContent/244"
    },
    {
        "id": 11,
        "title": "Commercial Airline Clearance for Central Nervous System Lesions and Edema",
        "category": "Neurology",
        "organization": "Aerospace Medical Association (AsMA)",
        "content": "Patients with intracranial space-occupying lesions (meningiomas, metastases) with significant surrounding vasogenic edema must be stabilized on corticosteroid therapy (such as Dexamethasone) before commercial flight consideration. Relative hypoxia at aircraft cabin altitudes may exacerbate neurological deficits. Travel should only proceed when neurological exam has been stable for at least 7 days without focal progression.",
        "keywords": "brain lesion vasogenic edema dexamethasone corticosteroids airline clearance AsMA neurology",
        "source_reference": "AsMA Medical Guidelines for Airline Travel: Central Nervous System Conditions. Aviat Space Environ Med.",
        "reference_url": "https://www.asma.org/publications/medical-publications-for-airline-travel"
    },
    {
        "id": 12,
        "title": "Cancer Patient Travel & Air Transit Thromboprophylaxis",
        "category": "Oncology",
        "organization": "National Comprehensive Cancer Network (NCCN)",
        "content": "Malignancy is an independent risk factor for venous thromboembolism (VTE), which is magnified by long-haul air travel. NCCN Guidelines recommend that active cancer patients undergoing medical travel receive risk-stratified thromboprophylaxis: high-risk ambulatory patients on systemic chemotherapy should be evaluated for Low Molecular Weight Heparin (LMWH) or direct oral anticoagulants before flights exceeding 4 hours. Adequate hydration and aisle seating for mobility are strongly advised.",
        "keywords": "oncology cancer VTE DVT thromboprophylaxis chemotherapy LMWH air travel NCCN",
        "source_reference": "NCCN Clinical Practice Guidelines in Oncology: Cancer-Associated Venous Thromboembolic Disease. Version 1.2024.",
        "reference_url": "https://www.nccn.org/guidelines/guidelines-detail?category=3&id=1426"
    },
    {
        "id": 13,
        "title": "Infection Precautions and Chemotherapy Nadir Travel Timing",
        "category": "Oncology",
        "organization": "American Society of Clinical Oncology (ASCO)",
        "content": "Patients receiving myelosuppressive chemotherapy should avoid commercial travel during the anticipated neutropenic nadir (typically days 7 to 14 post-infusion) when Absolute Neutrophil Count (ANC) falls below 1,000 cells/mcL. Public air transport during the nadir carries severe risk of opportunistic bacterial and viral infections. Patients must have immediate access to emergency centers capable of administering broad-spectrum intravenous empiric antibiotics within 60 minutes of febrile neutropenia onset.",
        "keywords": "chemotherapy nadir neutropenia ANC infection risk oncology fever hospital ASCO",
        "source_reference": "Taplitz RA, et al. Outpatient Management of Fever and Neutropenia in Adults Treated for Malignancy: ASCO Guideline Update. J Clin Oncol. 2018;36(14):1443-1453.",
        "reference_url": "https://ascopubs.org/doi/10.1200/JCO.2017.77.6211"
    },
    {
        "id": 14,
        "title": "International Medical Travel Protocol for Patients Receiving Radiotherapy",
        "category": "Oncology",
        "organization": "European Society for Medical Oncology (ESMO)",
        "content": "Patients traveling to international oncology centers for Stereotactic Body Radiotherapy (SBRT) or Intensity-Modulated Radiotherapy (IMRT) should plan continuous residency at the treatment destination for the entire planned treatment course. Interruptions in radiation therapy schedules are correlated with inferior locoregional control. Pre-travel simulation CT and contouring datasets must be transferred via DICOM standards at least 5 business days before travel.",
        "keywords": "radiotherapy SBRT IMRT oncology radiation oncology DICOM treatment continuity ESMO",
        "source_reference": "Jordan K, et al. ESMO Guidelines Committee: Management of acute and chronic toxicities during cancer transit. Ann Oncol. 2021.",
        "reference_url": "https://www.esmo.org/guidelines/supportive-and-palliative-care"
    },
    {
        "id": 15,
        "title": "Post-Endoscopic Hemostasis Recovery & Travel Clearance",
        "category": "Gastroenterology",
        "organization": "American College of Gastroenterology (ACG)",
        "content": "Following diagnostic upper endoscopy with therapeutic intervention (e.g., band ligation, heater probe, or hemoclip placement for peptic ulcer bleeding), the peak recurrence window for hemorrhage is the first 72 hours. Travel should be deferred until the patient has tolerated a soft oral diet for 48 hours without evidence of melena, hematemesis, or hemoglobin drop. High-dose oral proton pump inhibitor (PPI) therapy (Pantoprazole 40mg twice daily) should continue throughout the travel period.",
        "keywords": "endoscopy peptic ulcer gastrointestinal bleeding hemoclip PPI pantoprazole travel ACG",
        "source_reference": "Laine L, et al. ACG Clinical Guideline: Upper Gastrointestinal and Ulcer Bleeding. Am J Gastroenterol. 2021;116(5):899-917.",
        "reference_url": "https://journals.lww.com/ajg/fulltext/2021/05000/acg_clinical_guideline__upper_gastrointestinal_and.14.aspx"
    },
    {
        "id": 16,
        "title": "Post-Laparoscopic Cholecystectomy and Abdominal Surgery Travel Clearance",
        "category": "Gastroenterology",
        "organization": "Society of American Gastrointestinal and Endoscopic Surgeons (SAGES)",
        "content": "Laparoscopic abdominal procedures introduce carbon dioxide (CO2) pneumoperitoneum. Most residual CO2 is absorbed within 24 to 48 hours. Patients undergoing uncomplicated laparoscopic cholecystectomy or appendectomy may travel by air after 4 to 7 days, provided bowel sounds are present, flatus has passed, and surgical incisions show no wound breakdown or signs of peritonitis. Heavy lifting (>5kg) is restricted for 3 to 4 weeks.",
        "keywords": "laparoscopy cholecystectomy gallbladder appendectomy abdominal surgery pneumoperitoneum SAGES",
        "source_reference": "SAGES Guidelines for Clinical Application of Laparoscopic Biliary and Abdominal Procedures. Surg Endosc.",
        "reference_url": "https://www.sages.org/publications/guidelines/"
    },
    {
        "id": 17,
        "title": "Travel Guidelines for Chronic Kidney Disease (CKD) Stages 3 to 5",
        "category": "Nephrology",
        "organization": "Kidney Disease: Improving Global Outcomes (KDIGO)",
        "content": "Patients with advanced chronic kidney disease (CKD Stages 3b-5, eGFR < 45 mL/min/1.73m2) traveling for medical care must strictly regulate dietary sodium (<2 g/day) and potassium intake, especially when dining during transit. Serum creatinine and electrolytes must be checked within 1 week of travel. Travelers must avoid non-steroidal anti-inflammatory drugs (NSAIDs like Ibuprofen, Diclofenac) which precipitate acute kidney injury. Proper hydration is critical to prevent pre-renal azotemia.",
        "keywords": "chronic kidney disease CKD nephrology creatinine eGFR dialysis potassium NSAID KDIGO",
        "source_reference": "KDIGO 2024 Clinical Practice Guideline for the Evaluation and Management of Chronic Kidney Disease. Kidney Int. 2024;105(4S):S117-S314.",
        "reference_url": "https://kdigo.org/guidelines/ckd-evaluation-and-management/"
    },
    {
        "id": 18,
        "title": "Cross-Border Hemodialysis Coordination Protocol for ESRD Patients",
        "category": "Nephrology",
        "organization": "International Society of Nephrology (ISN)",
        "content": "End-stage renal disease (ESRD) patients requiring maintenance hemodialysis must reserve guest dialysis slots at an accredited receiving center in the destination city at least 4 to 6 weeks before departure. Mandatory medical packet includes: 1) Recent serologies (HBsAg, Anti-HCV, HIV within 30 days), 2) Current dialysis prescription (dialyzer type, blood flow rate, heparin dosage, dry weight), 3) Vascular access history (AV fistula or tunneled catheter). Dialysis should be scheduled on the day before travel and immediately upon arrival.",
        "keywords": "hemodialysis dialysis ESRD nephrology AV fistula guest dialysis ISN medical travel",
        "source_reference": "ISN Dialysis Committee Practical Framework: Transient and Cross-Border Hemodialysis Management for Traveling ESRD Patients.",
        "reference_url": "https://www.theisn.org/initiatives/dialysis-travel/"
    },
    {
        "id": 19,
        "title": "Carrying Insulin, Supplies & Crossing Time Zones with Diabetes",
        "category": "Endocrinology",
        "organization": "American Diabetes Association (ADA)",
        "content": "Patients with Type 1 or insulin-requiring Type 2 Diabetes must carry all insulin vials/pens and continuous glucose monitoring (CGM) sensors in carry-on luggage; insulin must never be placed in checked baggage due to cargo freezing risks. Carry an official physician letter and original pharmacy prescription. When traveling across more than 5 time zones: eastward travel shortens the day (requires less basal insulin), whereas westward travel lengthens the day (requires supplemental short-acting bolus or split basal dose).",
        "keywords": "diabetes insulin ADA endocrinology CGM time zones glucose travel blood sugar",
        "source_reference": "American Diabetes Association. Standards of Care in Diabetes—2024. Chapter 6: Glycemic Targets. Diabetes Care. 2024;47(Suppl 1):S111-S125.",
        "reference_url": "https://diabetesjournals.org/care/issue/47/Supplement_1"
    },
    {
        "id": 20,
        "title": "Air Travel Hypoxemia and Supplemental In-Flight Oxygen Guidelines",
        "category": "Pulmonology",
        "organization": "British Thoracic Society (BTS)",
        "content": "Commercial airliner cabins are pressurized to an equivalent of 1,500 to 2,400 meters (5,000 to 8,000 feet) altitude, resulting in an in-cabin inspired oxygen fraction equivalent to ~15% at sea level. Patients with baseline resting sea-level SpO2 < 92% or severe COPD/pulmonary fibrosis require pre-flight High Altitude Simulation Testing (HAST) or must arrange in-flight supplemental oxygen (typically 2 to 4 L/min via airline-approved Portable Oxygen Concentrators - POC). Airlines require oxygen requests 48 to 72 hours in advance.",
        "keywords": "hypoxemia oxygen COPD pulmonology flight altitude BTS respiratory POC",
        "source_reference": "Coker RK, et al. Managing passengers with stable respiratory disease planning air travel: British Thoracic Society recommendations. Thorax. 2011;66(Suppl 1):i1-i30.",
        "reference_url": "https://thorax.bmj.com/content/66/Suppl_1/i1"
    },
    {
        "id": 21,
        "title": "General Pre-Travel Health Evaluation and Medical Contraindications to Flight",
        "category": "General Medicine",
        "organization": "World Health Organization (WHO)",
        "content": "The WHO International Travel and Health guidance outlines absolute and relative contraindications to passenger air travel: 1) Active communicable infectious diseases, 2) Recent stroke within 14 days without stable neurologic baseline, 3) Severe decompensated congestive heart failure, 4) Recent surgery with risk of intra-abdominal or intra-cranial gas expansion, 5) Uncontrolled hypertension (systolic BP > 200 mmHg or diastolic > 110 mmHg). Patients must receive medical clearance letters from their attending physician.",
        "keywords": "WHO travel health flight contraindications medical clearance general medicine",
        "source_reference": "World Health Organization. International Travel and Health: General Considerations on Air Travel and Pre-existing Medical Conditions.",
        "reference_url": "https://www.who.int/publications/m/item/international-travel-and-health-general-considerations"
    },
    {
        "id": 22,
        "title": "Travel with Chronic Medical Illness and Immunosuppression",
        "category": "General Medicine",
        "organization": "Centers for Disease Control and Prevention (CDC)",
        "content": "According to the CDC Yellow Book, travelers with chronic medical illness should establish medical travel portfolios containing: full problem list, surgical history, current medication regimen with generic names, baseline 12-lead ECG, and emergency contact information. Immunosuppressed patients (organ transplant, biologic therapy, high-dose steroids) should avoid live vaccines and carry prophylactic broad-spectrum antibiotics and water purification tablets when visiting areas with endemic enteric pathogens.",
        "keywords": "CDC Yellow Book chronic illness travel medicine immunosuppression medical portfolio",
        "source_reference": "CDC Yellow Book 2024: Health Information for International Travel. Chapter 8: Travel with Chronic Medical Conditions. Oxford University Press.",
        "reference_url": "https://wwwnc.cdc.gov/travel/yellowbook/2024/air-travel/air-travel-with-chronic-illness"
    },
    {
        "id": 23,
        "title": "Cashless Hospitalization Pre-Authorization Timeline and Standards",
        "category": "Insurance",
        "organization": "Insurance Regulatory and Development Authority of India (IRDAI)",
        "content": "Under the IRDAI Master Circular on Health Insurance, network hospitals and Third Party Administrators (TPAs) must operate under strict turnaround times: 1) Initial pre-authorization requests for planned admissions must be decided within 1 hour of receiving complete medical documentation from the hospital TPA desk. 2) Final discharge authorization must be processed within 3 hours of final bill upload. Mandatory pre-auth documents include doctor's consultation note, preliminary diagnostic report, estimated cost breakdown, and government identity card.",
        "keywords": "cashless insurance IRDAI pre-authorization TPA hospital admission claims health insurance",
        "source_reference": "IRDAI Master Circular on Health Insurance Products and Claims Processing (Ref: IRDAI/HLT/REG/CIR/2024).",
        "reference_url": "https://irdai.gov.in/master-circulars"
    },
    {
        "id": 24,
        "title": "NABH Hospital Accreditation Standards for Inpatient Financial Clearances",
        "category": "Insurance",
        "organization": "National Accreditation Board for Hospitals & Healthcare Providers (NABH)",
        "content": "NABH Hospital Accreditation Standards (5th Edition, Access Assessment and Continuity of Care) mandate that medical travelers receive a transparent, itemized preliminary estimate of total hospitalization charges, anticipated room category tariffs, procedure package fees, and implant costs prior to admission. The hospital must maintain a dedicated international and outstation patient coordination desk to assist with insurance verification, language translation, and discharge summary generation.",
        "keywords": "NABH hospital accreditation TPA estimate medical travel transparent billing patient rights",
        "source_reference": "NABH Hospital Accreditation Standards (5th Edition). Chapter on Access, Assessment and Continuity of Care (AAC).",
        "reference_url": "https://www.nabh.co/Standards.aspx"
    },
    {
        "id": 25,
        "title": "Gastrointestinal Gas Expansion at Cabin Altitudes Following Abdominal Surgery",
        "category": "Gastroenterology",
        "organization": "International Air Transport Association (IATA)",
        "content": "Due to reduced barometric cabin pressure at cruise altitude, trapped gases in body cavities expand by 25% to 30%. Following open abdominal surgery (laparotomy, bowel resection), air travel is strictly contraindicated for at least 10 to 14 days due to the risk of suture line dehiscence, anastomotic leak, and bowel perforation. Patients must have verified passage of stool and flatus, minimal abdominal distension, and absence of fever before flight clearance is issued.",
        "keywords": "abdominal surgery laparotomy gas expansion cabin altitude bowel resection IATA fitness to fly",
        "source_reference": "IATA Medical Advisory Group. Medical Manual (14th Edition). Section 2.5: Gastrointestinal and Abdominal Conditions.",
        "reference_url": "https://www.iata.org/en/programs/safety/health/medical-manual/"
    }
]
