"""
Synthetic Medical Report Benchmark Generator (Phase 2 Evaluation Dataset)
Generates 30 realistic synthetic medical reports (Digital PDFs, Scanned PDFs, Image reports, and Tables)
across 8 specialties with independently verified ground_truth.json.

NOTICE: This dataset contains 100% synthetic benchmark evaluation data for pipeline validation.
It does NOT contain real clinical or protected health information (PHI).
"""

import os
import json
import re
from typing import List, Dict, Any
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from PIL import Image, ImageDraw, ImageFont

REPORTS_DIR = os.path.join(os.path.dirname(__file__), "reports")
GROUND_TRUTH_FILE = os.path.join(os.path.dirname(__file__), "ground_truth.json")

# Define 30 Synthetic Benchmark Report Specifications
DATASET_SPECS: List[Dict[str, Any]] = [
    # --- CARDIOLOGY (5 reports) ---
    {
        "id": 1,
        "filename": "report_01_cardio_angiogram.pdf",
        "format": "digital_pdf",
        "specialty": "Cardiology",
        "hospital": "Apex Heart Institute & Research Center",
        "metadata": {"patient_name": "Ramesh Gupta", "patient_id": "MRN-CRD-8821", "report_date": "14/08/2025"},
        "demographics": {"age": 58, "gender": "Male"},
        "conditions": ["Double Vessel Coronary Artery Disease", "Angina Pectoris"],
        "symptoms": ["exertional angina", "chest pain", "shortness of breath"],
        "tests": ["Coronary Angiography", "2D Echocardiogram", "Electrocardiogram"],
        "test_results": [
            {"test_name": "LAD Stenosis", "value": "85%", "unit": "%", "reference_range": "< 50%", "status": "Critical"},
            {"test_name": "RCA Stenosis", "value": "75%", "unit": "%", "reference_range": "< 50%", "status": "Critical"},
            {"test_name": "LVEF", "value": "52%", "unit": "%", "reference_range": "50% - 70%", "status": "Normal"},
            {"test_name": "Blood Pressure", "value": "142/88", "unit": "mmHg", "reference_range": "90/60 - 120/80 mmHg", "status": "High"},
        ],
        "medications": ["Aspirin 75mg OD", "Atorvastatin 40mg HS", "Metoprolol 25mg BD"],
        "procedures": ["Coronary Angiography", "Percutaneous Coronary Intervention"],
        "medical_history": ["Known case of hypertension for 6 years", "Past smoker"],
        "has_table": True
    },
    {
        "id": 2,
        "filename": "report_02_cardio_cad_echo.pdf",
        "format": "digital_pdf",
        "specialty": "Cardiology",
        "hospital": "Metro Cardiac Sciences Care",
        "metadata": {"patient_name": "Sunita Verma", "patient_id": "MRN-CRD-3190", "report_date": "22/07/2025"},
        "demographics": {"age": 62, "gender": "Female"},
        "conditions": ["Coronary Artery Disease", "Dyslipidemia"],
        "symptoms": ["chest pain", "palpitations", "fatigue"],
        "tests": ["2D Echocardiogram", "Lipid Profile"],
        "test_results": [
            {"test_name": "LVEF", "value": "48%", "unit": "%", "reference_range": "50% - 70%", "status": "Low"},
            {"test_name": "Total Cholesterol", "value": "245", "unit": "mg/dL", "reference_range": "<200", "status": "High"},
            {"test_name": "Serum Creatinine", "value": "0.9", "unit": "mg/dL", "reference_range": "0.7 - 1.3 mg/dL", "status": "Normal"}
        ],
        "medications": ["Rosuvastatin 20mg HS", "Amlodipine 5mg OD"],
        "procedures": ["Echocardiogram"],
        "medical_history": ["Known case of Type 2 Diabetes Mellitus x 4 years"],
        "has_table": True
    },
    {
        "id": 3,
        "filename": "report_03_cardio_stemi_scanned.pdf",
        "format": "scanned_pdf",
        "specialty": "Cardiology",
        "hospital": "City Emergency Cardiology Hospital",
        "metadata": {"patient_name": "Vikram Patel", "patient_id": "MRN-CRD-7704", "report_date": "05/09/2025"},
        "demographics": {"age": 51, "gender": "Male"},
        "conditions": ["Myocardial Infarction", "Hypertension"],
        "symptoms": ["chest pain", "dyspnea", "vomiting"],
        "tests": ["ECG", "Coronary Angiography"],
        "test_results": [
            {"test_name": "Blood Pressure", "value": "158/96", "unit": "mmHg", "reference_range": "90/60 - 120/80 mmHg", "status": "High"},
            {"test_name": "LVEF", "value": "42%", "unit": "%", "reference_range": "50% - 70%", "status": "Low"}
        ],
        "medications": ["Ticagrelor 90mg BD", "Aspirin 75mg OD", "Pantoprazole 40mg OD"],
        "procedures": ["Percutaneous Coronary Intervention", "Angioplasty"],
        "medical_history": ["History of hypertension", "Past smoker"],
        "has_table": False
    },
    {
        "id": 4,
        "filename": "report_04_cardio_angina_table.png",
        "format": "image_png",
        "specialty": "Cardiology",
        "hospital": "Trinity Heart & Vascular Care",
        "metadata": {"patient_name": "Rajesh Nair", "patient_id": "MRN-CRD-5021", "report_date": "18/06/2025"},
        "demographics": {"age": 65, "gender": "Male"},
        "conditions": ["Coronary Artery Disease", "Hyperlipidemia"],
        "symptoms": ["exertional angina", "breathlessness"],
        "tests": ["Complete Blood Count", "Lipid Profile", "ECG"],
        "test_results": [
            {"test_name": "Total Cholesterol", "value": "260", "unit": "mg/dL", "reference_range": "<200", "status": "High"},
            {"test_name": "Blood Pressure", "value": "138/86", "unit": "mmHg", "reference_range": "90/60 - 120/80 mmHg", "status": "Normal"},
            {"test_name": "Hemoglobin", "value": "14.2", "unit": "g/dL", "reference_range": "13.0 - 17.5 g/dL", "status": "Normal"}
        ],
        "medications": ["Atorvastatin 20mg HS", "Metoprolol 50mg OD"],
        "procedures": ["Electrocardiogram"],
        "medical_history": ["K/C/O Hypertension x 8 years"],
        "has_table": True
    },
    {
        "id": 5,
        "filename": "report_05_cardio_triple_vessel.pdf",
        "format": "digital_pdf",
        "specialty": "Cardiology",
        "hospital": "National Cardiovascular Center",
        "metadata": {"patient_name": "Kishore Kumar", "patient_id": "MRN-CRD-1192", "report_date": "02/08/2025"},
        "demographics": {"age": 69, "gender": "Male"},
        "conditions": ["Triple Vessel Disease", "Coronary Artery Disease"],
        "symptoms": ["chest pain", "shortness of breath", "fatigue"],
        "tests": ["Coronary Angiography", "2D Echocardiogram"],
        "test_results": [
            {"test_name": "LAD Stenosis", "value": "90%", "unit": "%", "reference_range": "< 50%", "status": "Critical"},
            {"test_name": "RCA Stenosis", "value": "80%", "unit": "%", "reference_range": "< 50%", "status": "Critical"},
            {"test_name": "LCx Stenosis", "value": "70%", "unit": "%", "reference_range": "< 50%", "status": "Critical"},
            {"test_name": "LVEF", "value": "44%", "unit": "%", "reference_range": "50% - 70%", "status": "Low"}
        ],
        "medications": ["Clopidogrel 75mg OD", "Atorvastatin 40mg HS", "Aspirin 75mg OD"],
        "procedures": ["Coronary Artery Bypass Grafting", "CABG"],
        "medical_history": ["Known diabetic x 12 years", "Known hypertensive"],
        "has_table": True
    },

    # --- NEUROLOGY (4 reports) ---
    {
        "id": 6,
        "filename": "report_06_neuro_meningioma_mri.pdf",
        "format": "digital_pdf",
        "specialty": "Neurology",
        "hospital": "Apollo Institute of Neurosciences",
        "metadata": {"patient_name": "Pooja Sharma", "patient_id": "MRN-NEU-4412", "report_date": "19/07/2025"},
        "demographics": {"age": 46, "gender": "Female"},
        "conditions": ["Meningioma", "Cerebral Edema"],
        "symptoms": ["headache", "motor weakness", "dizziness"],
        "tests": ["MRI Brain", "CT Scan"],
        "test_results": [
            {"test_name": "Blood Pressure", "value": "124/80", "unit": "mmHg", "reference_range": "90/60 - 120/80 mmHg", "status": "Normal"},
            {"test_name": "Serum Creatinine", "value": "0.8", "unit": "mg/dL", "reference_range": "0.7 - 1.3 mg/dL", "status": "Normal"}
        ],
        "medications": ["Levetiracetam 500mg BD", "Pantoprazole 40mg OD"],
        "procedures": ["Craniotomy", "Tumor Excision"],
        "medical_history": ["Presenting since 6 months", "No known chronic illnesses"],
        "has_table": False
    },
    {
        "id": 7,
        "filename": "report_07_neuro_ischemic_stroke_scanned.pdf",
        "format": "scanned_pdf",
        "specialty": "Neurology",
        "hospital": "Max Neuro Sciences Care",
        "metadata": {"patient_name": "Anil Deshmukh", "patient_id": "MRN-NEU-9021", "report_date": "11/08/2025"},
        "demographics": {"age": 64, "gender": "Male"},
        "conditions": ["Hypertension", "Atherosclerosis"],
        "symptoms": ["motor weakness", "headache", "dizziness"],
        "tests": ["CT Scan", "MRI Brain"],
        "test_results": [
            {"test_name": "Blood Pressure", "value": "164/98", "unit": "mmHg", "reference_range": "90/60 - 120/80 mmHg", "status": "High"},
            {"test_name": "Fasting Blood Sugar", "value": "136", "unit": "mg/dL", "reference_range": "70 - 99 mg/dL", "status": "High"}
        ],
        "medications": ["Aspirin 75mg OD", "Atorvastatin 40mg HS", "Telmisartan 40mg OD"],
        "procedures": ["Computed Tomography"],
        "medical_history": ["Known hypertensive for 10 years", "Known diabetic"],
        "has_table": False
    },
    {
        "id": 8,
        "filename": "report_08_neuro_glioma_histopath.pdf",
        "format": "digital_pdf",
        "specialty": "Neurology",
        "hospital": "NIMHANS Allied Neuro Center",
        "metadata": {"patient_name": "Deepak Mehta", "patient_id": "MRN-NEU-6124", "report_date": "29/06/2025"},
        "demographics": {"age": 52, "gender": "Male"},
        "conditions": ["Glioma", "Astrocytoma"],
        "symptoms": ["headache", "seizures", "vomiting"],
        "tests": ["MRI Brain", "Histopathology Report", "Biopsy"],
        "test_results": [
            {"test_name": "Hemoglobin", "value": "13.6", "unit": "g/dL", "reference_range": "13.0 - 17.5 g/dL", "status": "Normal"},
            {"test_name": "Platelet Count", "value": "240,000", "unit": "/mcL", "reference_range": "150,000 - 450,000 /mcL", "status": "Normal"}
        ],
        "medications": ["Levetiracetam 500mg BD", "Tramadol 50mg PRN"],
        "procedures": ["Craniotomy", "Biopsy"],
        "medical_history": ["History of headache since 4 months"],
        "has_table": True
    },
    {
        "id": 9,
        "filename": "report_09_neuro_seizure_eeg.png",
        "format": "image_png",
        "specialty": "Neurology",
        "hospital": "Fortis Brain & Spine Clinic",
        "metadata": {"patient_name": "Kavita Rao", "patient_id": "MRN-NEU-2287", "report_date": "15/07/2025"},
        "demographics": {"age": 34, "gender": "Female"},
        "conditions": ["Vasogenic Edema"],
        "symptoms": ["headache", "dizziness", "lethargy"],
        "tests": ["MRI Brain", "Electrocardiogram"],
        "test_results": [
            {"test_name": "Blood Pressure", "value": "118/76", "unit": "mmHg", "reference_range": "90/60 - 120/80 mmHg", "status": "Normal"},
            {"test_name": "Serum Creatinine", "value": "0.7", "unit": "mg/dL", "reference_range": "0.7 - 1.3 mg/dL", "status": "Normal"}
        ],
        "medications": ["Levetiracetam 500mg BD", "Pantoprazole 40mg OD"],
        "procedures": ["MRI Brain"],
        "medical_history": ["Known case of migraine for 3 years"],
        "has_table": False
    },

    # --- ORTHOPEDICS (4 reports) ---
    {
        "id": 10,
        "filename": "report_10_ortho_knee_osteoarthritis.pdf",
        "format": "digital_pdf",
        "specialty": "Orthopedics",
        "hospital": "Manipal Institute of Orthopedics",
        "metadata": {"patient_name": "Shashi Kapoor", "patient_id": "MRN-ORT-1982", "report_date": "08/08/2025"},
        "demographics": {"age": 66, "gender": "Female"},
        "conditions": ["Osteoarthritis", "Arthritis"],
        "symptoms": ["knee pain", "joint stiffness", "antalgic gait"],
        "tests": ["X-Ray Knee", "Complete Blood Count"],
        "test_results": [
            {"test_name": "ESR", "value": "24", "unit": "mm/hr", "reference_range": "0 - 20 mm/hr", "status": "High"},
            {"test_name": "Uric Acid", "value": "5.4", "unit": "mg/dL", "reference_range": "2.4 - 6.0 mg/dL", "status": "Normal"},
            {"test_name": "Blood Pressure", "value": "130/84", "unit": "mmHg", "reference_range": "90/60 - 120/80 mmHg", "status": "Normal"}
        ],
        "medications": ["Paracetamol 650mg TDS", "Diclofenac 50mg BD", "Pantoprazole 40mg OD"],
        "procedures": ["Total Knee Arthroplasty", "TKA"],
        "medical_history": ["Duration: 5 years", "Known diabetic x 6 years"],
        "has_table": True
    },
    {
        "id": 11,
        "filename": "report_11_ortho_lumbar_spondylosis_scanned.pdf",
        "format": "scanned_pdf",
        "specialty": "Orthopedics",
        "hospital": "Medanta Bone & Joint Care",
        "metadata": {"patient_name": "Gopal Sharma", "patient_id": "MRN-ORT-4890", "report_date": "25/08/2025"},
        "demographics": {"age": 57, "gender": "Male"},
        "conditions": ["Spondylosis", "Radiculopathy"],
        "symptoms": ["joint stiffness", "fatigue", "motor weakness"],
        "tests": ["MRI Spine", "X-Ray Spine"],
        "test_results": [
            {"test_name": "Blood Pressure", "value": "134/86", "unit": "mmHg", "reference_range": "90/60 - 120/80 mmHg", "status": "Normal"},
            {"test_name": "Hemoglobin", "value": "14.0", "unit": "g/dL", "reference_range": "13.0 - 17.5 g/dL", "status": "Normal"}
        ],
        "medications": ["Tramadol 50mg BD", "Paracetamol 500mg TDS"],
        "procedures": ["MRI Spine"],
        "medical_history": ["K/C/O Hypertension x 3 years"],
        "has_table": False
    },
    {
        "id": 12,
        "filename": "report_12_ortho_hip_fracture.pdf",
        "format": "digital_pdf",
        "specialty": "Orthopedics",
        "hospital": "Fortis Orthopedic Specialties",
        "metadata": {"patient_name": "Kamla Devi", "patient_id": "MRN-ORT-7119", "report_date": "04/09/2025"},
        "demographics": {"age": 73, "gender": "Female"},
        "conditions": ["Osteoarthritis", "Hypertension"],
        "symptoms": ["joint pain", "antalgic gait"],
        "tests": ["X-Ray Pelvis", "Complete Blood Count"],
        "test_results": [
            {"test_name": "Hemoglobin", "value": "11.8", "unit": "g/dL", "reference_range": "12.0 - 15.5 g/dL", "status": "Low"},
            {"test_name": "Platelet Count", "value": "210,000", "unit": "/mcL", "reference_range": "150,000 - 450,000 /mcL", "status": "Normal"}
        ],
        "medications": ["Tramadol 50mg BD", "Paracetamol 650mg TDS"],
        "procedures": ["Total Hip Arthroplasty", "THA"],
        "medical_history": ["Known hypertensive for 12 years", "Known diabetic"],
        "has_table": True
    },
    {
        "id": 13,
        "filename": "report_13_ortho_knee_replacement_table.png",
        "format": "image_png",
        "specialty": "Orthopedics",
        "hospital": "Sparsh Joint Surgery Hospital",
        "metadata": {"patient_name": "Brijesh Prasad", "patient_id": "MRN-ORT-9302", "report_date": "17/07/2025"},
        "demographics": {"age": 61, "gender": "Male"},
        "conditions": ["Osteoarthritis"],
        "symptoms": ["knee pain", "joint stiffness", "gait disturbance"],
        "tests": ["X-Ray Knee", "Lipid Profile"],
        "test_results": [
            {"test_name": "Blood Pressure", "value": "136/82", "unit": "mmHg", "reference_range": "90/60 - 120/80 mmHg", "status": "Normal"},
            {"test_name": "Fasting Blood Sugar", "value": "112", "unit": "mg/dL", "reference_range": "70 - 99 mg/dL", "status": "High"},
            {"test_name": "Serum Creatinine", "value": "1.0", "unit": "mg/dL", "reference_range": "0.7 - 1.3 mg/dL", "status": "Normal"}
        ],
        "medications": ["Diclofenac 50mg BD", "Pantoprazole 40mg OD"],
        "procedures": ["Total Knee Arthroplasty", "Knee Replacement"],
        "medical_history": ["Known case of hypertension for 4 years"],
        "has_table": True
    },

    # --- ONCOLOGY (4 reports) ---
    {
        "id": 14,
        "filename": "report_14_oncol_colon_carcinoma.pdf",
        "format": "digital_pdf",
        "specialty": "Oncology",
        "hospital": "Tata Memorial Allied Oncology Center",
        "metadata": {"patient_name": "Manohar Joshi", "patient_id": "MRN-ONC-8810", "report_date": "27/07/2025"},
        "demographics": {"age": 60, "gender": "Male"},
        "conditions": ["Carcinoma", "Malignancy"],
        "symptoms": ["fatigue", "nausea", "malaise"],
        "tests": ["Colonoscopy", "Biopsy", "CT Abdomen"],
        "test_results": [
            {"test_name": "Hemoglobin", "value": "10.2", "unit": "g/dL", "reference_range": "13.0 - 17.5 g/dL", "status": "Low"},
            {"test_name": "CEA Marker", "value": "18.4", "unit": "ng/mL", "reference_range": "< 3.0 ng/mL", "status": "High"},
            {"test_name": "Serum Creatinine", "value": "1.1", "unit": "mg/dL", "reference_range": "0.7 - 1.3 mg/dL", "status": "Normal"}
        ],
        "medications": ["Pantoprazole 40mg OD", "Tramadol 50mg PRN"],
        "procedures": ["Colonoscopy", "Biopsy"],
        "medical_history": ["Known hypertensive for 5 years", "Past smoker"],
        "has_table": True
    },
    {
        "id": 15,
        "filename": "report_15_oncol_breast_carcinoma_table.pdf",
        "format": "digital_pdf",
        "specialty": "Oncology",
        "hospital": "HCG Cancer Care Hospital",
        "metadata": {"patient_name": "Meena Saxena", "patient_id": "MRN-ONC-3912", "report_date": "14/08/2025"},
        "demographics": {"age": 54, "gender": "Female"},
        "conditions": ["Carcinoma", "Neoplasm"],
        "symptoms": ["fatigue", "malaise"],
        "tests": ["Histopathology Report", "Biopsy", "Complete Blood Count"],
        "test_results": [
            {"test_name": "Hemoglobin", "value": "12.4", "unit": "g/dL", "reference_range": "12.0 - 15.5 g/dL", "status": "Normal"},
            {"test_name": "Platelet Count", "value": "260,000", "unit": "/mcL", "reference_range": "150,000 - 450,000 /mcL", "status": "Normal"},
            {"test_name": "Blood Pressure", "value": "122/78", "unit": "mmHg", "reference_range": "90/60 - 120/80 mmHg", "status": "Normal"}
        ],
        "medications": ["Pantoprazole 40mg OD", "Paracetamol 500mg PRN"],
        "procedures": ["Biopsy"],
        "medical_history": ["Presenting since 3 months", "No prior surgical history"],
        "has_table": True
    },
    {
        "id": 16,
        "filename": "report_16_oncol_lung_neoplasm_scanned.pdf",
        "format": "scanned_pdf",
        "specialty": "Oncology",
        "hospital": "Rajiv Gandhi Cancer Institute",
        "metadata": {"patient_name": "Suresh Trivedi", "patient_id": "MRN-ONC-5520", "report_date": "03/09/2025"},
        "demographics": {"age": 68, "gender": "Male"},
        "conditions": ["Neoplasm", "COPD"],
        "symptoms": ["cough", "shortness of breath", "fatigue", "hemoptysis"],
        "tests": ["CT Chest", "Biopsy"],
        "test_results": [
            {"test_name": "Hemoglobin", "value": "12.1", "unit": "g/dL", "reference_range": "13.0 - 17.5 g/dL", "status": "Low"},
            {"test_name": "Blood Pressure", "value": "144/88", "unit": "mmHg", "reference_range": "90/60 - 120/80 mmHg", "status": "High"}
        ],
        "medications": ["Azithromycin 500mg OD", "Pantoprazole 40mg OD"],
        "procedures": ["Biopsy", "Computed Tomography"],
        "medical_history": ["Past smoker x 30 years", "Known hypertensive"],
        "has_table": False
    },
    {
        "id": 17,
        "filename": "report_17_oncol_adenoma_biopsy.png",
        "format": "image_png",
        "specialty": "Oncology",
        "hospital": "Continental Oncology & Surgical Center",
        "metadata": {"patient_name": "Nandita Iyer", "patient_id": "MRN-ONC-7741", "report_date": "12/06/2025"},
        "demographics": {"age": 49, "gender": "Female"},
        "conditions": ["Adenoma"],
        "symptoms": ["nausea", "fatigue"],
        "tests": ["Histopathology Examination", "Biopsy"],
        "test_results": [
            {"test_name": "Blood Pressure", "value": "126/80", "unit": "mmHg", "reference_range": "90/60 - 120/80 mmHg", "status": "Normal"},
            {"test_name": "Serum Creatinine", "value": "0.8", "unit": "mg/dL", "reference_range": "0.7 - 1.3 mg/dL", "status": "Normal"}
        ],
        "medications": ["Omeprazole 20mg OD", "Paracetamol 500mg PRN"],
        "procedures": ["Biopsy"],
        "medical_history": ["Known case of hypothyroidism"],
        "has_table": False
    },

    # --- GASTROENTEROLOGY (4 reports) ---
    {
        "id": 18,
        "filename": "report_18_gastro_cholelithiasis.pdf",
        "format": "digital_pdf",
        "specialty": "Gastroenterology",
        "hospital": "Asian Institute of Gastroenterology (AIG)",
        "metadata": {"patient_name": "Vandana Kulkarni", "patient_id": "MRN-GAS-2109", "report_date": "20/08/2025"},
        "demographics": {"age": 43, "gender": "Female"},
        "conditions": ["Cholelithiasis", "Cholecystitis"],
        "symptoms": ["nausea", "vomiting", "fever"],
        "tests": ["Ultrasound Abdomen", "Liver Function Test"],
        "test_results": [
            {"test_name": "Total Bilirubin", "value": "1.8", "unit": "mg/dL", "reference_range": "0.2 - 1.2 mg/dL", "status": "High"},
            {"test_name": "SGPT / ALT", "value": "64", "unit": "U/L", "reference_range": "7 - 56 U/L", "status": "High"},
            {"test_name": "WBC Count", "value": "12,400", "unit": "/mcL", "reference_range": "4,500 - 11,000 /mcL", "status": "High"},
            {"test_name": "Blood Pressure", "value": "120/78", "unit": "mmHg", "reference_range": "90/60 - 120/80 mmHg", "status": "Normal"}
        ],
        "medications": ["Pantoprazole 40mg OD", "Cefixime 200mg BD", "Tramadol 50mg PRN"],
        "procedures": ["Cholecystectomy", "Laparoscopy"],
        "medical_history": ["History of biliary colic since 3 months"],
        "has_table": True
    },
    {
        "id": 19,
        "filename": "report_19_gastro_peptic_ulcer_scanned.pdf",
        "format": "scanned_pdf",
        "specialty": "Gastroenterology",
        "hospital": "Max Digestive Health Institute",
        "metadata": {"patient_name": "Harish Rawat", "patient_id": "MRN-GAS-6612", "report_date": "06/09/2025"},
        "demographics": {"age": 55, "gender": "Male"},
        "conditions": ["Hypertension"],
        "symptoms": ["nausea", "vomiting", "fatigue"],
        "tests": ["Upper GI Endoscopy", "Complete Blood Count"],
        "test_results": [
            {"test_name": "Hemoglobin", "value": "11.4", "unit": "g/dL", "reference_range": "13.0 - 17.5 g/dL", "status": "Low"},
            {"test_name": "Blood Pressure", "value": "138/86", "unit": "mmHg", "reference_range": "90/60 - 120/80 mmHg", "status": "Normal"}
        ],
        "medications": ["Pantoprazole 40mg OD", "Amoxicillin 500mg TDS"],
        "procedures": ["Endoscopy", "Biopsy"],
        "medical_history": ["Known hypertensive for 4 years", "Past smoker"],
        "has_table": False
    },
    {
        "id": 20,
        "filename": "report_20_gastro_cholecystitis_table.pdf",
        "format": "digital_pdf",
        "specialty": "Gastroenterology",
        "hospital": "GEM Hospital & Digestive Center",
        "metadata": {"patient_name": "Rekha Agarwal", "patient_id": "MRN-GAS-4491", "report_date": "16/07/2025"},
        "demographics": {"age": 48, "gender": "Female"},
        "conditions": ["Cholecystitis", "Cholelithiasis"],
        "symptoms": ["nausea", "vomiting", "fever"],
        "tests": ["Ultrasound Abdomen", "Complete Blood Count", "LFT"],
        "test_results": [
            {"test_name": "WBC Count", "value": "13,200", "unit": "/mcL", "reference_range": "4,500 - 11,000 /mcL", "status": "High"},
            {"test_name": "Total Bilirubin", "value": "1.4", "unit": "mg/dL", "reference_range": "0.2 - 1.2 mg/dL", "status": "High"},
            {"test_name": "Serum Creatinine", "value": "0.9", "unit": "mg/dL", "reference_range": "0.7 - 1.3 mg/dL", "status": "Normal"}
        ],
        "medications": ["Ciprofloxacin 500mg BD", "Pantoprazole 40mg OD", "Paracetamol 650mg TDS"],
        "procedures": ["Cholecystectomy"],
        "medical_history": ["Known diabetic x 5 years"],
        "has_table": True
    },
    {
        "id": 21,
        "filename": "report_21_gastro_colonoscopy.png",
        "format": "image_png",
        "specialty": "Gastroenterology",
        "hospital": "Narayana Digestive Care",
        "metadata": {"patient_name": "Prakash Sen", "patient_id": "MRN-GAS-9018", "report_date": "28/06/2025"},
        "demographics": {"age": 59, "gender": "Male"},
        "conditions": ["Hypertension"],
        "symptoms": ["fatigue", "malaise"],
        "tests": ["Colonoscopy", "Biopsy"],
        "test_results": [
            {"test_name": "Hemoglobin", "value": "13.8", "unit": "g/dL", "reference_range": "13.0 - 17.5 g/dL", "status": "Normal"},
            {"test_name": "Blood Pressure", "value": "142/90", "unit": "mmHg", "reference_range": "90/60 - 120/80 mmHg", "status": "High"}
        ],
        "medications": ["Amlodipine 5mg OD", "Pantoprazole 40mg OD"],
        "procedures": ["Colonoscopy", "Biopsy"],
        "medical_history": ["K/C/O Hypertension x 7 years"],
        "has_table": False
    },

    # --- PULMONOLOGY (3 reports) ---
    {
        "id": 22,
        "filename": "report_22_pulmon_pneumonia.pdf",
        "format": "digital_pdf",
        "specialty": "Pulmonology",
        "hospital": "Metro Chest & Pulmonary Center",
        "metadata": {"patient_name": "Dharmendra Singh", "patient_id": "MRN-PUL-1845", "report_date": "10/08/2025"},
        "demographics": {"age": 63, "gender": "Male"},
        "conditions": ["Pneumonia", "Hypertension"],
        "symptoms": ["cough", "shortness of breath", "fever", "chills"],
        "tests": ["X-Ray Chest", "Complete Blood Count"],
        "test_results": [
            {"test_name": "WBC Count", "value": "14,800", "unit": "/mcL", "reference_range": "4,500 - 11,000 /mcL", "status": "High"},
            {"test_name": "Blood Pressure", "value": "132/84", "unit": "mmHg", "reference_range": "90/60 - 120/80 mmHg", "status": "Normal"},
            {"test_name": "Hemoglobin", "value": "13.4", "unit": "g/dL", "reference_range": "13.0 - 17.5 g/dL", "status": "Normal"}
        ],
        "medications": ["Azithromycin 500mg OD", "Amoxicillin 500mg TDS", "Paracetamol 650mg TDS"],
        "procedures": ["X-Ray Chest"],
        "medical_history": ["Known hypertensive for 6 years", "Past smoker"],
        "has_table": True
    },
    {
        "id": 23,
        "filename": "report_23_pulmon_copd_bronchitis_scanned.pdf",
        "format": "scanned_pdf",
        "specialty": "Pulmonology",
        "hospital": "National Institute of Respiratory Sciences",
        "metadata": {"patient_name": "Jagdish Chandra", "patient_id": "MRN-PUL-7230", "report_date": "24/08/2025"},
        "demographics": {"age": 70, "gender": "Male"},
        "conditions": ["COPD", "Bronchitis"],
        "symptoms": ["cough", "dyspnea", "breathlessness", "fatigue"],
        "tests": ["Chest Radiograph", "ECG"],
        "test_results": [
            {"test_name": "Blood Pressure", "value": "140/88", "unit": "mmHg", "reference_range": "90/60 - 120/80 mmHg", "status": "High"},
            {"test_name": "Serum Creatinine", "value": "1.2", "unit": "mg/dL", "reference_range": "0.7 - 1.3 mg/dL", "status": "Normal"}
        ],
        "medications": ["Azithromycin 500mg OD", "Pantoprazole 40mg OD"],
        "procedures": ["Electrocardiogram"],
        "medical_history": ["Past smoker x 35 years", "Known case of COPD"],
        "has_table": False
    },
    {
        "id": 24,
        "filename": "report_24_pulmon_pleural_effusion.png",
        "format": "image_png",
        "specialty": "Pulmonology",
        "hospital": "PulmoCare Specialty Clinic",
        "metadata": {"patient_name": "Sarita Mukhopadhyay", "patient_id": "MRN-PUL-3918", "report_date": "19/07/2025"},
        "demographics": {"age": 56, "gender": "Female"},
        "conditions": ["Pneumonia"],
        "symptoms": ["shortness of breath", "cough", "fever"],
        "tests": ["CT Chest", "Complete Blood Count"],
        "test_results": [
            {"test_name": "WBC Count", "value": "12,100", "unit": "/mcL", "reference_range": "4,500 - 11,000 /mcL", "status": "High"},
            {"test_name": "Hemoglobin", "value": "12.8", "unit": "g/dL", "reference_range": "12.0 - 15.5 g/dL", "status": "Normal"}
        ],
        "medications": ["Cefixime 200mg BD", "Paracetamol 500mg TDS"],
        "procedures": ["Computed Tomography"],
        "medical_history": ["Known diabetic x 4 years"],
        "has_table": False
    },

    # --- NEPHROLOGY (3 reports) ---
    {
        "id": 25,
        "filename": "report_25_nephro_ckd_renal_failure.pdf",
        "format": "digital_pdf",
        "specialty": "Nephrology",
        "hospital": "Apex Kidney Institute & Dialysis Center",
        "metadata": {"patient_name": "Mahesh Bhatia", "patient_id": "MRN-NEP-8102", "report_date": "13/08/2025"},
        "demographics": {"age": 67, "gender": "Male"},
        "conditions": ["Chronic Kidney Disease", "Renal Failure", "Hypertension"],
        "symptoms": ["fatigue", "nausea", "malaise"],
        "tests": ["Renal Function Test", "Complete Blood Count", "Ultrasound Abdomen"],
        "test_results": [
            {"test_name": "Serum Creatinine", "value": "2.8", "unit": "mg/dL", "reference_range": "0.7 - 1.3 mg/dL", "status": "Critical"},
            {"test_name": "Blood Urea", "value": "68", "unit": "mg/dL", "reference_range": "15 - 45 mg/dL", "status": "High"},
            {"test_name": "Serum Potassium", "value": "5.1", "unit": "mEq/L", "reference_range": "3.5 - 5.0 mEq/L", "status": "High"},
            {"test_name": "Hemoglobin", "value": "10.4", "unit": "g/dL", "reference_range": "13.0 - 17.5 g/dL", "status": "Low"},
            {"test_name": "Blood Pressure", "value": "152/94", "unit": "mmHg", "reference_range": "90/60 - 120/80 mmHg", "status": "High"}
        ],
        "medications": ["Amlodipine 10mg OD", "Telmisartan 40mg OD", "Torsemide 10mg OD"],
        "procedures": ["Ultrasound Abdomen"],
        "medical_history": ["Known hypertensive for 14 years", "Known diabetic x 10 years"],
        "has_table": True
    },
    {
        "id": 26,
        "filename": "report_26_nephro_diabetic_nephropathy_scanned.pdf",
        "format": "scanned_pdf",
        "specialty": "Nephrology",
        "hospital": "City Nephro-Care Hospital",
        "metadata": {"patient_name": "Sultana Begum", "patient_id": "MRN-NEP-4390", "report_date": "30/08/2025"},
        "demographics": {"age": 60, "gender": "Female"},
        "conditions": ["Chronic Kidney Disease", "Type 2 Diabetes Mellitus"],
        "symptoms": ["fatigue", "malaise"],
        "tests": ["Renal Function Test", "HbA1c Test"],
        "test_results": [
            {"test_name": "Serum Creatinine", "value": "1.9", "unit": "mg/dL", "reference_range": "0.7 - 1.3 mg/dL", "status": "High"},
            {"test_name": "HbA1c", "value": "8.8", "unit": "%", "reference_range": "< 5.7%", "status": "High"},
            {"test_name": "Blood Pressure", "value": "148/90", "unit": "mmHg", "reference_range": "90/60 - 120/80 mmHg", "status": "High"}
        ],
        "medications": ["Insulin 20IU BD", "Telmisartan 40mg OD", "Pantoprazole 40mg OD"],
        "procedures": ["Renal Function Test"],
        "medical_history": ["Known case of Type 2 Diabetes Mellitus x 15 years", "Known hypertensive"],
        "has_table": False
    },
    {
        "id": 27,
        "filename": "report_27_nephro_hypertensive_nephrosclerosis.png",
        "format": "image_png",
        "specialty": "Nephrology",
        "hospital": "Narayana Kidney Sciences",
        "metadata": {"patient_name": "Devendra Pandey", "patient_id": "MRN-NEP-6014", "report_date": "18/06/2025"},
        "demographics": {"age": 58, "gender": "Male"},
        "conditions": ["Hypertension", "Renal Failure"],
        "symptoms": ["fatigue", "headache", "dizziness"],
        "tests": ["RFT", "Lipid Profile"],
        "test_results": [
            {"test_name": "Serum Creatinine", "value": "1.7", "unit": "mg/dL", "reference_range": "0.7 - 1.3 mg/dL", "status": "High"},
            {"test_name": "Blood Pressure", "value": "160/100", "unit": "mmHg", "reference_range": "90/60 - 120/80 mmHg", "status": "High"},
            {"test_name": "Serum Potassium", "value": "4.6", "unit": "mEq/L", "reference_range": "3.5 - 5.0 mEq/L", "status": "Normal"}
        ],
        "medications": ["Amlodipine 5mg OD", "Losartan 50mg OD"],
        "procedures": ["Renal Function Test"],
        "medical_history": ["Known hypertensive for 8 years"],
        "has_table": True
    },

    # --- GENERAL MEDICINE / ENDOCRINOLOGY (3 reports) ---
    {
        "id": 28,
        "filename": "report_28_genmed_t2dm_hba1c_table.pdf",
        "format": "digital_pdf",
        "specialty": "General Medicine",
        "hospital": "Comprehensive Diabetes & Endocrine Center",
        "metadata": {"patient_name": "Ashok Aggarwal", "patient_id": "MRN-GEN-1029", "report_date": "15/08/2025"},
        "demographics": {"age": 53, "gender": "Male"},
        "conditions": ["Type 2 Diabetes Mellitus", "Dyslipidemia", "Hypertension"],
        "symptoms": ["fatigue", "malaise"],
        "tests": ["HbA1c Test", "Lipid Profile", "Complete Blood Count"],
        "test_results": [
            {"test_name": "HbA1c", "value": "9.2", "unit": "%", "reference_range": "< 5.7%", "status": "High"},
            {"test_name": "Fasting Blood Sugar", "value": "168", "unit": "mg/dL", "reference_range": "70 - 99 mg/dL", "status": "High"},
            {"test_name": "Total Cholesterol", "value": "230", "unit": "mg/dL", "reference_range": "<200", "status": "High"},
            {"test_name": "Serum Creatinine", "value": "0.9", "unit": "mg/dL", "reference_range": "0.7 - 1.3 mg/dL", "status": "Normal"},
            {"test_name": "Blood Pressure", "value": "138/88", "unit": "mmHg", "reference_range": "90/60 - 120/80 mmHg", "status": "Normal"}
        ],
        "medications": ["Metformin 500mg BD", "Atorvastatin 20mg HS", "Telmisartan 40mg OD"],
        "procedures": ["Electrocardiogram"],
        "medical_history": ["Known case of Type 2 Diabetes Mellitus x 8 years", "Known hypertensive"],
        "has_table": True
    },
    {
        "id": 29,
        "filename": "report_29_genmed_hypertension_metabolic.pdf",
        "format": "digital_pdf",
        "specialty": "General Medicine",
        "hospital": "Apollo Clinic Family Health",
        "metadata": {"patient_name": "Preeti Sen", "patient_id": "MRN-GEN-5541", "report_date": "21/07/2025"},
        "demographics": {"age": 47, "gender": "Female"},
        "conditions": ["Hypertension", "Hyperlipidemia"],
        "symptoms": ["headache", "dizziness", "fatigue"],
        "tests": ["ECG", "Lipid Panel", "RFT"],
        "test_results": [
            {"test_name": "Blood Pressure", "value": "146/92", "unit": "mmHg", "reference_range": "90/60 - 120/80 mmHg", "status": "High"},
            {"test_name": "Total Cholesterol", "value": "225", "unit": "mg/dL", "reference_range": "<200", "status": "High"},
            {"test_name": "Serum Creatinine", "value": "0.8", "unit": "mg/dL", "reference_range": "0.7 - 1.3 mg/dL", "status": "Normal"}
        ],
        "medications": ["Telmisartan 40mg OD", "Rosuvastatin 10mg HS"],
        "procedures": ["Electrocardiogram"],
        "medical_history": ["Duration: 2 years", "No prior surgeries"],
        "has_table": True
    },
    {
        "id": 30,
        "filename": "report_30_genmed_fever_infection_scanned.pdf",
        "format": "scanned_pdf",
        "specialty": "General Medicine",
        "hospital": "City Multispecialty Medical Center",
        "metadata": {"patient_name": "Naveen Yadav", "patient_id": "MRN-GEN-9904", "report_date": "01/09/2025"},
        "demographics": {"age": 38, "gender": "Male"},
        "conditions": ["Pneumonia"],
        "symptoms": ["fever", "chills", "fatigue", "cough"],
        "tests": ["Complete Blood Count", "Chest Radiograph"],
        "test_results": [
            {"test_name": "WBC Count", "value": "13,600", "unit": "/mcL", "reference_range": "4,500 - 11,000 /mcL", "status": "High"},
            {"test_name": "Platelet Count", "value": "190,000", "unit": "/mcL", "reference_range": "150,000 - 450,000 /mcL", "status": "Normal"},
            {"test_name": "Blood Pressure", "value": "120/78", "unit": "mmHg", "reference_range": "90/60 - 120/80 mmHg", "status": "Normal"}
        ],
        "medications": ["Paracetamol 650mg TDS", "Amoxicillin 500mg TDS"],
        "procedures": ["X-Ray Chest"],
        "medical_history": ["Presenting since 1 week", "No chronic comorbidities"],
        "has_table": False
    }
]


def render_digital_pdf(spec: Dict[str, Any], output_path: str):
    """Renders clean digital PDF using ReportLab with tables and structured headings."""
    doc = SimpleDocTemplate(output_path, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=14,
        leading=18,
        textColor=colors.HexColor("#0f2444"),
        spaceAfter=4
    )
    banner_style = ParagraphStyle(
        'Banner',
        parent=styles['Normal'],
        fontSize=7,
        leading=9,
        textColor=colors.HexColor("#777777"),
        spaceAfter=10
    )
    section_style = ParagraphStyle(
        'SecTitle',
        parent=styles['Heading3'],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#1b4b72"),
        spaceBefore=6,
        spaceAfter=3
    )
    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#222222")
    )
    
    elements = []
    
    # Synthetic dataset disclaimer banner
    elements.append(Paragraph("[SYNTHETIC BENCHMARK EVALUATION DATASET — NOT REAL CLINICAL DATA]", banner_style))
    elements.append(Paragraph(f"{spec['hospital']} — Department of {spec['specialty']}", title_style))
    elements.append(Paragraph("<b>CLINICAL DIAGNOSTIC & INVESTIGATION REPORT</b>", section_style))
    elements.append(Spacer(1, 4))
    
    # Metadata Block
    meta = spec['metadata']
    demo = spec['demographics']
    meta_table_data = [
        [f"Patient Name: {meta['patient_name']}", f"Patient ID: {meta['patient_id']}"],
        [f"Age: {demo['age']} Years  |  Gender: {demo['gender']}", f"Report Date: {meta['report_date']}"]
    ]
    meta_table = Table(meta_table_data, colWidths=[270, 270])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f4f7fa")),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('TEXTCOLOR', (0,0), (-1,-1), colors.HexColor("#1a2b3c")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#d0d7de")),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#d0d7de")),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    elements.append(meta_table)
    elements.append(Spacer(1, 8))
    
    # Chief Complaints / Symptoms
    elements.append(Paragraph("CHIEF COMPLAINTS & SYMPTOMS:", section_style))
    sym_text = ", ".join(spec['symptoms'])
    elements.append(Paragraph(f"Patient presented with complaints of {sym_text}.", body_style))
    elements.append(Spacer(1, 4))
    
    # Medical History
    elements.append(Paragraph("PAST MEDICAL HISTORY:", section_style))
    elements.append(Paragraph(f"{spec['medical_history']}.", body_style))
    elements.append(Spacer(1, 4))
    
    # Tests & Investigations
    elements.append(Paragraph("DIAGNOSTIC INVESTIGATIONS PERFORMED:", section_style))
    test_text = ", ".join(spec['tests'])
    elements.append(Paragraph(f"Investigations: {test_text}.", body_style))
    elements.append(Spacer(1, 4))
    
    # Structured Test Results Table
    if spec['test_results']:
        elements.append(Paragraph("LABORATORY & DIAGNOSTIC MEASUREMENTS:", section_style))
        t_data = [["Test Name", "Measured Value", "Unit", "Reference Range", "Status"]]
        for tr in spec['test_results']:
            t_data.append([tr['test_name'], tr['value'], tr['unit'], tr['reference_range'], tr['status']])
        res_table = Table(t_data, colWidths=[180, 80, 70, 110, 100])
        res_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#e5effa")),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 8),
            ('TEXTCOLOR', (0,0), (-1,-1), colors.HexColor("#112233")),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
            ('TOPPADDING', (0,0), (-1,-1), 3),
            ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ]))
        elements.append(res_table)
        elements.append(Spacer(1, 6))
    
    # Explicit Diagnoses / Conditions
    elements.append(Paragraph("FINAL DIAGNOSIS & CLINICAL IMPRESSION:", section_style))
    for c in spec['conditions']:
        elements.append(Paragraph(f"• {c}", body_style))
    elements.append(Spacer(1, 4))
    
    # Procedures
    if spec['procedures']:
        elements.append(Paragraph("PROCEDURES PERFORMED / RECOMMENDED:", section_style))
        proc_text = ", ".join(spec['procedures'])
        elements.append(Paragraph(f"{proc_text}.", body_style))
        elements.append(Spacer(1, 4))
        
    # Medications
    if spec['medications']:
        elements.append(Paragraph("ACTIVE MEDICATIONS:", section_style))
        med_text = ", ".join(spec['medications'])
        elements.append(Paragraph(f"Rx: {med_text}.", body_style))
        elements.append(Spacer(1, 8))
        
    elements.append(Paragraph("Signed: Medical Officer / Attending Consultant", banner_style))
    doc.build(elements)


def render_scanned_pdf(spec: Dict[str, Any], output_path: str):
    """Renders text report into image with synthetic scanning noise, then packages into PDF."""
    temp_img_path = output_path.replace(".pdf", "_temp.png")
    render_image_report(spec, temp_img_path)
    
    # Convert image to single-page PDF with slight simulated scan quality
    img = Image.open(temp_img_path).convert("L")  # Grayscale simulated scan
    img.save(output_path, "PDF", resolution=150.0)
    if os.path.exists(temp_img_path):
        os.remove(temp_img_path)


def render_image_report(spec: Dict[str, Any], output_path: str):
    """Renders synthetic medical report into high-resolution PNG image."""
    img_width, img_height = 800, 1100
    img = Image.new("RGB", (img_width, img_height), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    
    try:
        font_large = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 18)
        font_med = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 13)
        font_small = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 11)
        font_tiny = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 9)
    except Exception:
        font_large = font_med = font_small = font_tiny = ImageFont.load_default()
        
    y = 20
    draw.text((30, y), "[SYNTHETIC BENCHMARK EVALUATION DATASET — NOT REAL CLINICAL DATA]", fill=(120, 120, 120), font=font_tiny)
    y += 18
    draw.text((30, y), f"{spec['hospital']} — {spec['specialty']}", fill=(15, 36, 68), font=font_large)
    y += 24
    draw.text((30, y), "CLINICAL DIAGNOSTIC & INVESTIGATION REPORT", fill=(27, 75, 114), font=font_med)
    y += 20
    draw.line([(30, y), (770, y)], fill=(200, 200, 200), width=1)
    y += 10
    
    # Demographics Box
    meta = spec['metadata']
    demo = spec['demographics']
    draw.rectangle([(30, y), (770, y + 42)], fill=(245, 247, 250), outline=(210, 215, 222))
    draw.text((40, y + 6), f"Patient Name: {meta['patient_name']}     Patient ID: {meta['patient_id']}", fill=(20, 30, 40), font=font_small)
    draw.text((40, y + 22), f"Age: {demo['age']} Years     Gender: {demo['gender']}     Report Date: {meta['report_date']}", fill=(20, 30, 40), font=font_small)
    y += 54
    
    # Chief Complaints
    draw.text((30, y), "CHIEF COMPLAINTS & SYMPTOMS:", fill=(27, 75, 114), font=font_med)
    y += 18
    sym_str = ", ".join(spec['symptoms'])
    draw.text((35, y), f"Patient presented with complaints of {sym_str}.", fill=(30, 30, 30), font=font_small)
    y += 22
    
    # Medical History
    draw.text((30, y), "PAST MEDICAL HISTORY:", fill=(27, 75, 114), font=font_med)
    y += 18
    draw.text((35, y), f"{spec['medical_history']}.", fill=(30, 30, 30), font=font_small)
    y += 22
    
    # Tests
    draw.text((30, y), "DIAGNOSTIC INVESTIGATIONS PERFORMED:", fill=(27, 75, 114), font=font_med)
    y += 18
    tests_str = ", ".join(spec['tests'])
    draw.text((35, y), f"Investigations: {tests_str}.", fill=(30, 30, 30), font=font_small)
    y += 24
    
    # Table of Test Results
    if spec['test_results']:
        draw.text((30, y), "LABORATORY & DIAGNOSTIC MEASUREMENTS:", fill=(27, 75, 114), font=font_med)
        y += 18
        # Header
        draw.rectangle([(30, y), (770, y + 20)], fill=(225, 235, 245), outline=(200, 210, 220))
        draw.text((35, y + 4), "Test Name", fill=(10, 20, 30), font=font_small)
        draw.text((260, y + 4), "Value", fill=(10, 20, 30), font=font_small)
        draw.text((360, y + 4), "Unit", fill=(10, 20, 30), font=font_small)
        draw.text((460, y + 4), "Reference Range", fill=(10, 20, 30), font=font_small)
        draw.text((640, y + 4), "Status", fill=(10, 20, 30), font=font_small)
        y += 20
        
        for tr in spec['test_results']:
            draw.rectangle([(30, y), (770, y + 20)], fill=(255, 255, 255), outline=(230, 235, 240))
            draw.text((35, y + 4), tr['test_name'], fill=(20, 30, 40), font=font_small)
            draw.text((260, y + 4), tr['value'], fill=(20, 30, 40), font=font_small)
            draw.text((360, y + 4), tr['unit'], fill=(60, 60, 60), font=font_small)
            draw.text((460, y + 4), tr['reference_range'], fill=(60, 60, 60), font=font_small)
            draw.text((640, y + 4), tr['status'], fill=(180, 20, 20) if tr['status'] in ['High', 'Critical', 'Low'] else (20, 120, 40), font=font_small)
            y += 20
        y += 10
        
    # Final Diagnosis
    draw.text((30, y), "FINAL DIAGNOSIS & CLINICAL IMPRESSION:", fill=(27, 75, 114), font=font_med)
    y += 18
    for c in spec['conditions']:
        draw.text((35, y), f"• {c}", fill=(20, 20, 20), font=font_small)
        y += 16
    y += 6
    
    # Procedures
    if spec['procedures']:
        draw.text((30, y), "PROCEDURES PERFORMED / RECOMMENDED:", fill=(27, 75, 114), font=font_med)
        y += 18
        draw.text((35, y), f"{', '.join(spec['procedures'])}.", fill=(30, 30, 30), font=font_small)
        y += 20
        
    # Medications
    if spec['medications']:
        draw.text((30, y), "ACTIVE MEDICATIONS:", fill=(27, 75, 114), font=font_med)
        y += 18
        draw.text((35, y), f"Rx: {', '.join(spec['medications'])}.", fill=(30, 30, 30), font=font_small)
        y += 24
        
    draw.line([(30, y), (770, y)], fill=(220, 220, 220), width=1)
    y += 8
    draw.text((30, y), "Signed: Medical Officer / Attending Consultant", fill=(130, 130, 130), font=font_tiny)
    
    img.save(output_path)


def generate_all_reports():
    """Generates all 30 reports and executes independent ground-truth verification."""
    os.makedirs(REPORTS_DIR, exist_ok=True)
    ground_truth = []
    
    print(f"Generating 30 synthetic medical benchmark reports in '{REPORTS_DIR}'...")
    
    for spec in DATASET_SPECS:
        file_path = os.path.join(REPORTS_DIR, spec['filename'])
        fmt = spec['format']
        
        if fmt == "digital_pdf":
            render_digital_pdf(spec, file_path)
        elif fmt == "scanned_pdf":
            render_scanned_pdf(spec, file_path)
        elif fmt == "image_png":
            render_image_report(spec, file_path)
            
        # Structure ground truth entry (WITHOUT recommended_specialty; explicitly reported diagnoses only)
        gt_entry = {
            "id": spec["id"],
            "filename": spec["filename"],
            "format": spec["format"],
            "specialty_domain": spec["specialty"],
            "metadata": spec["metadata"],
            "demographics": spec["demographics"],
            "conditions": spec["conditions"],
            "symptoms": spec["symptoms"],
            "tests": spec["tests"],
            "test_results": spec["test_results"],
            "medications": spec["medications"],
            "procedures": spec["procedures"],
            "medical_history": spec["medical_history"],
            "has_table": spec["has_table"]
        }
        ground_truth.append(gt_entry)
        print(f"[{spec['id']:02d}/30] Generated ({fmt}): {spec['filename']}")
        
    with open(GROUND_TRUTH_FILE, "w") as f:
        json.dump(ground_truth, f, indent=2)
        
    print(f"\nSaved ground truth to {GROUND_TRUTH_FILE}")
    
    # Execute Independent Validation
    print("\nExecuting independent verification of ground truth against generated files...")
    from pypdf import PdfReader
    verification_errors = []
    
    for item in ground_truth:
        fpath = os.path.join(REPORTS_DIR, item['filename'])
        if not os.path.exists(fpath):
            verification_errors.append(f"Missing file: {item['filename']}")
            continue
            
        # For digital PDFs, verify text tokens are physically present in PDF stream
        if item['format'] == "digital_pdf":
            reader = PdfReader(fpath)
            extracted_text = " ".join([page.extract_text() for page in reader.pages])
            
            # Verify patient name
            pname = item['metadata']['patient_name']
            if pname not in extracted_text:
                verification_errors.append(f"Report {item['id']}: Patient name '{pname}' missing from PDF stream")
                
            # Verify MRN
            pid = item['metadata']['patient_id']
            if pid not in extracted_text:
                verification_errors.append(f"Report {item['id']}: Patient ID '{pid}' missing from PDF stream")
                
            # Verify conditions
            for c in item['conditions']:
                if c not in extracted_text:
                    verification_errors.append(f"Report {item['id']}: Condition '{c}' missing from PDF stream")
                    
    if verification_errors:
        print(f"FAILED: {len(verification_errors)} verification errors found:")
        for err in verification_errors:
            print(" -", err)
    else:
        print("SUCCESS: 100% of digital benchmark reports independently verified against document byte stream.")


if __name__ == "__main__":
    generate_all_reports()
