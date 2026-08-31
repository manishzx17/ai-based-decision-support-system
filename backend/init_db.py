import sys
import os

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from database import engine, SessionLocal, Base
from models import (
    User, PatientProfile, MedicalReport, ExtractedEntity,
    Hospital, Doctor, Pharmacy, TreatmentCost, InsuranceProvider,
    Accommodation, EmergencyContact, MedicalKnowledge, Appointment, TravelPlan
)
from datasets.seed_data import (
    SEED_HOSPITALS, SEED_DOCTORS, SEED_PHARMACIES,
    SEED_TREATMENT_COSTS, SEED_INSURANCE, SEED_ACCOMMODATIONS,
    SEED_EMERGENCY, SEED_KNOWLEDGE_BASE
)

def init_db():
    print("Initializing Database Schemas...")
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # Check if already seeded
        if db.query(Hospital).first():
            print("Database already contains data. Skipping initial seeding.")
            return

        print("Seeding initial medical travel data...")

        # 1. Create Default Demo User & Profile
        demo_user = User(
            email="patient@example.com",
            hashed_password="hashed_demo_password_123",
            full_name="Rajesh Verma",
            role="patient"
        )
        db.add(demo_user)
        db.commit()
        db.refresh(demo_user)

        demo_profile = PatientProfile(
            user_id=demo_user.id,
            age=48,
            gender="Male",
            blood_group="B+",
            allergies="Penicillin",
            chronic_conditions="Hypertension, Type 2 Diabetes",
            current_city="Hyderabad",
            preferred_currency="INR",
            emergency_contact_name="Sunita Verma (Spouse)",
            emergency_contact_phone="+91 98765 12345"
        )
        db.add(demo_profile)

        # 2. Seed Hospitals
        for h in SEED_HOSPITALS:
            h_obj = Hospital(**h)
            db.add(h_obj)

        # 3. Seed Doctors
        for d in SEED_DOCTORS:
            d_obj = Doctor(**d)
            db.add(d_obj)

        # 4. Seed Pharmacies
        for p in SEED_PHARMACIES:
            p_obj = Pharmacy(**p)
            db.add(p_obj)

        # 5. Seed Treatment Costs
        for tc in SEED_TREATMENT_COSTS:
            tc_obj = TreatmentCost(**tc)
            db.add(tc_obj)

        # 6. Seed Insurance
        for ins in SEED_INSURANCE:
            ins_obj = InsuranceProvider(**ins)
            db.add(ins_obj)

        # 7. Seed Accommodations
        for acc in SEED_ACCOMMODATIONS:
            acc_obj = Accommodation(**acc)
            db.add(acc_obj)

        # 8. Seed Emergency Contacts
        for em in SEED_EMERGENCY:
            em_obj = EmergencyContact(**em)
            db.add(em_obj)

        # 9. Seed Medical Knowledge Base
        for kb in SEED_KNOWLEDGE_BASE:
            kb_obj = MedicalKnowledge(**kb)
            db.add(kb_obj)

        # 10. Seed Sample Report & Extracted Entities
        sample_report = MedicalReport(
            user_id=demo_user.id,
            filename="Cardiology_Angiography_Report_RajeshVerma.pdf",
            file_path="uploads/sample_cardio_report.pdf",
            status="COMPLETED",
            ocr_text="""PATIENT DIAGNOSTIC REPORT
Name: Rajesh Verma | Age: 48 | Gender: Male
Department: Cardiology & Interventional Medicine
Clinical Findings: Patient presents with exertional angina (CCS Class II) and shortness of breath.
Coronary Angiography Summary:
1. Left Main (LM): Normal
2. Left Anterior Descending (LAD): 85% proximal stenosis with discrete calcified plaque.
3. Left Circumflex (LCx): Minor 30% irregular luminal disease.
4. Right Coronary Artery (RCA): 70% mid-vessel stenosis.
Impression: Severe Double Vessel Disease (DVD).
Recommended Management: Elective Percutaneous Coronary Intervention (PCI) with Drug-Eluting Stents (DES) in LAD and RCA, or Coronary Artery Bypass Grafting (CABG).
Current Medications: Aspirin 75mg OD, Atorvastatin 40mg HS, Metoprolol 50mg BD.""",
            summary="Patient has Severe Double Vessel Disease (LAD 85% stenosis, RCA 70% stenosis) causing exertional angina. Elective Angioplasty (PCI) with drug-eluting stents or CABG surgery is advised under Cardiology.",
            recommended_specialty="Cardiology",
            important_notes="High priority for elective interventional cardiology. High LVEF (55%). Safe for regional travel under medical supervision."
        )
        db.add(sample_report)
        db.commit()
        db.refresh(sample_report)

        entities_data = [
            ("Disease", "Severe Double Vessel Disease", 0.98, "Impression: Severe Double Vessel Disease (DVD)."),
            ("Symptom", "Exertional Angina", 0.95, "Patient presents with exertional angina"),
            ("Symptom", "Shortness of Breath", 0.92, "shortness of breath"),
            ("Procedure", "Percutaneous Coronary Intervention (PCI)", 0.96, "Elective Percutaneous Coronary Intervention"),
            ("Procedure", "Coronary Angiography", 0.99, "Coronary Angiography Summary"),
            ("Medication", "Aspirin 75mg", 0.94, "Aspirin 75mg OD"),
            ("Medication", "Atorvastatin 40mg", 0.93, "Atorvastatin 40mg HS"),
            ("BodyPart", "Left Anterior Descending Artery (LAD)", 0.97, "LAD: 85% proximal stenosis")
        ]

        for etype, ename, conf, context in entities_data:
            ent = ExtractedEntity(
                report_id=sample_report.id,
                entity_type=etype,
                entity_name=ename,
                confidence=conf,
                context_snippet=context
            )
            db.add(ent)

        db.commit()
        print("Database initialized and successfully seeded with complete demo dataset!")
    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    init_db()
