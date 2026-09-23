import sys
import os

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from sqlalchemy import text
from database import engine, SessionLocal, Base
from models import (
    User, PatientProfile, MedicalReport, ExtractedEntity,
    Hospital, Doctor, Pharmacy, TreatmentCost, InsuranceProvider,
    Accommodation, EmergencyContact, MedicalKnowledge, Appointment, TravelPlan,
    AuditLog
)
from datasets.seed_data import (
    SEED_HOSPITALS, SEED_DOCTORS, SEED_PHARMACIES,
    SEED_TREATMENT_COSTS, SEED_INSURANCE, SEED_ACCOMMODATIONS,
    SEED_EMERGENCY, SEED_KNOWLEDGE_BASE
)

def init_db():
    print("Initializing Database Schemas...")
    Base.metadata.create_all(bind=engine)

    # Automated schema migrations for newly added columns in SQLite
    with engine.connect() as conn:
        for col_name, col_type in [("grounding_notes", "TEXT"), ("grounding_sources", "JSON"), ("structured_data", "JSON")]:
            try:
                conn.execute(text(f"ALTER TABLE medical_reports ADD COLUMN {col_name} {col_type}"))
                conn.commit()
            except Exception:
                pass
        for col_name, col_type in [("organization", "VARCHAR"), ("reference_url", "VARCHAR")]:
            try:
                conn.execute(text(f"ALTER TABLE medical_knowledge ADD COLUMN {col_name} {col_type}"))
                conn.commit()
            except Exception:
                pass
        for col_name, col_type in [
            ("estimated_cost_tier", "FLOAT"),
            ("cost_tier", "VARCHAR"),
            ("quality_rating", "FLOAT"),
            ("accreditation", "VARCHAR"),
            ("treatment_capabilities", "JSON"),
            ("icu_beds", "INTEGER"),
            ("emergency_24x7", "BOOLEAN"),
            ("provenance", "JSON")
        ]:
            try:
                conn.execute(text(f"ALTER TABLE hospitals ADD COLUMN {col_name} {col_type}"))
                conn.commit()
            except Exception:
                pass
        for col_name, col_type in [("provenance", "JSON"), ("expertise", "VARCHAR")]:
            try:
                conn.execute(text(f"ALTER TABLE doctors ADD COLUMN {col_name} {col_type}"))
                conn.commit()
            except Exception:
                pass

        # Phase 3: Patient profile structured clinical columns migration
        for col_name, col_type in [
            ("conditions", "JSON"),
            ("symptoms", "JSON"),
            ("tests", "JSON"),
            ("test_results", "JSON"),
            ("medications", "JSON"),
            ("procedures", "JSON"),
            ("medical_history", "JSON"),
            ("last_report_id", "INTEGER"),
            ("structured_data", "JSON")
        ]:
            try:
                conn.execute(text(f"ALTER TABLE patient_profiles ADD COLUMN {col_name} {col_type}"))
                conn.commit()
            except Exception:
                pass

        # Phase 5: Hospital and Doctor structured benchmark columns migration
        for col_name, col_type in [
            ("cost_tier", "VARCHAR DEFAULT 'Moderate'"),
            ("quality_rating", "FLOAT DEFAULT 4.5"),
            ("accreditation", "VARCHAR DEFAULT 'NABH Accredited'"),
            ("treatment_capabilities", "JSON DEFAULT '[]'"),
            ("icu_beds", "INTEGER DEFAULT 50"),
            ("emergency_24x7", "BOOLEAN DEFAULT 1"),
        ]:
            try:
                conn.execute(text(f"ALTER TABLE hospitals ADD COLUMN {col_name} {col_type}"))
                conn.commit()
            except Exception:
                pass

        try:
            conn.execute(text("ALTER TABLE doctors ADD COLUMN expertise JSON DEFAULT '[]'"))
            conn.commit()
        except Exception:
            pass

    db = SessionLocal()
    try:
        # Check if already seeded
        if db.query(Hospital).first():
            # Ensure medical knowledge base is fully populated with all verified guidelines
            if db.query(MedicalKnowledge).count() < len(SEED_KNOWLEDGE_BASE):
                existing_ids = {k[0] for k in db.query(MedicalKnowledge.id).all()}
                for kb in SEED_KNOWLEDGE_BASE:
                    if kb["id"] not in existing_ids:
                        db.add(MedicalKnowledge(**kb))
                    else:
                        db_obj = db.query(MedicalKnowledge).filter(MedicalKnowledge.id == kb["id"]).first()
                        if db_obj:
                            for key, val in kb.items():
                                setattr(db_obj, key, val)
                db.commit()

            # Ensure hospitals are fully synchronized with Dataset 3
            existing_h_ids = {h[0] for h in db.query(Hospital.id).all()}
            for h in SEED_HOSPITALS:
                if h["id"] not in existing_h_ids:
                    db.add(Hospital(**h))
                else:
                    db_obj = db.query(Hospital).filter(Hospital.id == h["id"]).first()
                    if db_obj:
                        for key, val in h.items():
                            setattr(db_obj, key, val)
            if len(existing_h_ids) > len(SEED_HOSPITALS):
                valid_ids = {h["id"] for h in SEED_HOSPITALS}
                for hid in existing_h_ids:
                    if hid not in valid_ids:
                        db.query(Hospital).filter(Hospital.id == hid).delete()
            db.commit()

            # Ensure doctors are fully synchronized with Dataset 3
            existing_d_ids = {d[0] for d in db.query(Doctor.id).all()}
            doc_cols = {col.name for col in Doctor.__table__.columns}
            for d in SEED_DOCTORS:
                clean_d = {k: v for k, v in d.items() if k in doc_cols}
                if clean_d["id"] not in existing_d_ids:
                    db.add(Doctor(**clean_d))
                else:
                    db_obj = db.query(Doctor).filter(Doctor.id == clean_d["id"]).first()
                    if db_obj:
                        for key, val in clean_d.items():
                            setattr(db_obj, key, val)
            if len(existing_d_ids) > len(SEED_DOCTORS):
                valid_d_ids = {d["id"] for d in SEED_DOCTORS}
                for did in existing_d_ids:
                    if did not in valid_d_ids:
                        db.query(Doctor).filter(Doctor.id == did).delete()
            db.commit()

            # Ensure accommodations are fully synchronized
            if db.query(Accommodation).count() < len(SEED_ACCOMMODATIONS):
                existing_acc_ids = {a[0] for a in db.query(Accommodation.id).all()}
                for acc in SEED_ACCOMMODATIONS:
                    if acc["id"] not in existing_acc_ids:
                        db.add(Accommodation(**acc))
                    else:
                        db_obj = db.query(Accommodation).filter(Accommodation.id == acc["id"]).first()
                        if db_obj:
                            for key, val in acc.items():
                                setattr(db_obj, key, val)
                db.commit()

            # Ensure pharmacies are fully synchronized
            if db.query(Pharmacy).count() < len(SEED_PHARMACIES):
                existing_pharm_ids = {p[0] for p in db.query(Pharmacy.id).all()}
                for p in SEED_PHARMACIES:
                    if p["id"] not in existing_pharm_ids:
                        db.add(Pharmacy(**p))
                    else:
                        db_obj = db.query(Pharmacy).filter(Pharmacy.id == p["id"]).first()
                        if db_obj:
                            for key, val in p.items():
                                setattr(db_obj, key, val)
                db.commit()

            # Ensure 3 synthetic demo patients are seeded and up-to-date
            seed_demo_patients(db)

            print("Database already contains data. Knowledge base, hospitals, doctors, accommodations, and pharmacies synchronized.")
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

        # Ensure 3 synthetic demo patients are seeded and up-to-date
        seed_demo_patients(db)

        db.commit()
        print("Database initialized and successfully seeded with complete demo dataset!")
    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
    finally:
        db.close()


def seed_demo_patients(db):
    """
    Ensures exactly 3 synthetic demo patients exist with distinct clinical profiles,
    reports, and credentials for verified patient-context isolation.
    """
    from security import hash_password

    demo_specs = [
        {
            "id": 1,
            "email": "patient@example.com",
            "full_name": "Rahul Verma",
            "password": "DemoPassword@123",
            "profile": {
                "age": 48,
                "gender": "Male",
                "blood_group": "B+",
                "current_city": "Hyderabad",
                "allergies": "Penicillin",
                "chronic_conditions": "Hypertension, Coronary Artery Disease",
                "conditions": ["Coronary Artery Disease", "CAD", "Angina"],
                "symptoms": ["Chest tightness", "Exertional dyspnea"],
                "tests": ["Coronary Angiography", "ECG", "Lipid Profile"],
                "test_results": [
                    {"test_name": "LAD Stenosis", "value": "85%", "unit": "%", "reference_range": "<50%", "status": "Critical"},
                    {"test_name": "Total Cholesterol", "value": "240", "unit": "mg/dL", "reference_range": "<200", "status": "High"}
                ],
                "medications": ["Aspirin 75mg", "Atorvastatin 40mg", "Metoprolol 25mg"],
                "procedures": ["Coronary Angioplasty (PTCA)"],
                "medical_history": ["Primary Hypertension 5 years", "Dyslipidemia"]
            },
            "report": {
                "filename": "Cardiology_Angiography_Report_RajeshVerma.pdf",
                "file_path": "uploads/sample_cardio_report.pdf",
                "summary": "Patient has Severe Double Vessel Disease (LAD 85% stenosis, RCA 70% stenosis) causing exertional angina. Elective Angioplasty (PCI) with drug-eluting stents is advised under Cardiology.",
                "recommended_specialty": "Cardiology",
                "important_notes": "High priority for elective interventional cardiology. High LVEF (55%). Safe for regional travel.",
                "ocr_text": "PATIENT DIAGNOSTIC REPORT\nName: Rahul Verma | Age: 48 | Gender: Male\nDepartment: Cardiology & Interventional Medicine\nClinical Findings: Patient presents with exertional angina (CCS Class II) and shortness of breath.\nCoronary Angiography Summary: LAD 85% proximal stenosis with discrete calcified plaque. RCA 70% stenosis.\nImpression: Severe Double Vessel Disease (DVD).\nRecommended Management: Elective Percutaneous Coronary Intervention (PCI) with Drug-Eluting Stents (DES).\nCurrent Medications: Aspirin 75mg OD, Atorvastatin 40mg HS, Metoprolol 25mg BD.",
                "entities": [
                    ("Disease", "Severe Double Vessel Disease", 0.98, "Impression: Severe Double Vessel Disease (DVD)."),
                    ("Symptom", "Exertional Angina", 0.95, "Patient presents with exertional angina"),
                    ("Procedure", "Percutaneous Coronary Intervention (PCI)", 0.96, "Elective Percutaneous Coronary Intervention"),
                    ("Medication", "Aspirin 75mg", 0.94, "Aspirin 75mg OD"),
                    ("BodyPart", "Left Anterior Descending Artery (LAD)", 0.97, "LAD: 85% proximal stenosis")
                ]
            }
        },
        {
            "id": 2,
            "email": "patient2@example.com",
            "full_name": "Priya Sharma",
            "password": "DemoPassword@123",
            "profile": {
                "age": 34,
                "gender": "Female",
                "blood_group": "A+",
                "current_city": "Bengaluru",
                "allergies": "Sulfa drugs",
                "chronic_conditions": "Chronic Migraine, Occipital Neuralgia",
                "conditions": ["Chronic Migraine", "Neurological Headache", "Cervicogenic Neuralgia"],
                "symptoms": ["Unilateral throbbing headache", "Photophobia", "Visual aura", "Nausea"],
                "tests": ["Brain MRI with Contrast", "Electroencephalogram (EEG)", "Neurological Reflex Exam"],
                "test_results": [
                    {"test_name": "Brain MRI", "value": "Non-lesional / Normal Vasculature", "unit": "Text", "reference_range": "Normal", "status": "Normal"},
                    {"test_name": "EEG Baseline", "value": "Normal Alpha Rhythm 10Hz", "unit": "Hz", "reference_range": "8-13 Hz", "status": "Normal"}
                ],
                "medications": ["Sumatriptan 50mg", "Topiramate 25mg", "Magnesium Glycinate 400mg"],
                "procedures": ["Occipital Nerve Block Evaluation", "MRI Brain Scan"],
                "medical_history": ["Episodic Migraine progressing to Chronic 2 years"]
            },
            "report": {
                "filename": "Neurology_Diagnostic_Report_PriyaSharma.pdf",
                "file_path": "uploads/neurology_diagnostic_report_priya.pdf",
                "summary": "Neuro-diagnostic Evaluation: Patient diagnosed with Chronic Refractory Migraine with visual aura. Non-lesional 3T Brain MRI rules out intracranial mass or vascular malformation. Neurology follow-up indicated.",
                "recommended_specialty": "Neurology",
                "important_notes": "Advised prophylactic neuromodulation and triptan therapy. Low neurological deficit score.",
                "ocr_text": "PATIENT NEURO-DIAGNOSTIC REPORT\nName: Priya Sharma | Age: 34 | Gender: Female\nDepartment: Neurology & Comprehensive Headache Center\nClinical Findings: Patient presents with refractory hemicranial throbbing headaches, episodic visual aura, and photophobia.\nMRI Brain (3.0 Tesla): Normal cerebral parenchyma without focal signal abnormality. No acute ischemia or intracranial hemorrhage.\nImpression: Intractable Chronic Migraine with Visual Aura.\nRecommended Management: Prophylactic neuromodulator therapy, abortive Sumatriptan, and lifestyle triggers minimization.\nMedications: Sumatriptan 50mg PRN, Topiramate 25mg HS.",
                "entities": [
                    ("Disease", "Chronic Migraine", 0.98, "Impression: Intractable Chronic Migraine"),
                    ("Symptom", "Photophobia", 0.94, "photophobia and episodic visual aura"),
                    ("Procedure", "Brain MRI with Contrast", 0.97, "MRI Brain (3.0 Tesla)"),
                    ("Medication", "Sumatriptan 50mg", 0.96, "abortive Sumatriptan 50mg"),
                    ("BodyPart", "Cerebral Cortex", 0.91, "cerebral parenchyma normal")
                ]
            }
        },
        {
            "id": 3,
            "email": "patient3@example.com",
            "full_name": "Amit Patel",
            "password": "DemoPassword@123",
            "profile": {
                "age": 62,
                "gender": "Male",
                "blood_group": "O+",
                "current_city": "Delhi",
                "allergies": "NSAIDs (Ibuprofen / Diclofenac)",
                "chronic_conditions": "Severe Bilateral Knee Osteoarthritis, Degenerative Joint Disease",
                "conditions": ["Bilateral Knee Osteoarthritis", "Degenerative Joint Disease", "Cartilage Loss"],
                "symptoms": ["Severe knee joint pain", "Morning joint stiffness", "Crepitus", "Limited mobility"],
                "tests": ["Weight-bearing Knee Radiography (X-Ray)", "Serum Uric Acid", "Knee Range of Motion Assessment"],
                "test_results": [
                    {"test_name": "Joint Space Width (Medial)", "value": "1.2", "unit": "mm", "reference_range": ">3.5 mm", "status": "Critical"},
                    {"test_name": "Serum Uric Acid", "value": "5.6", "unit": "mg/dL", "reference_range": "3.5-7.2", "status": "Normal"}
                ],
                "medications": ["Paracetamol 650mg", "Glucosamine Sulfate 1500mg", "Hyaluronic Acid Joint Supplements"],
                "procedures": ["Total Knee Arthroplasty (TKA)", "Bilateral Knee Diagnostic Fluoroscopy"],
                "medical_history": ["Osteoarthritis Grade IV Kellgren-Lawrence 4 years"]
            },
            "report": {
                "filename": "Orthopedic_Evaluation_Report_AmitPatel.pdf",
                "file_path": "uploads/orthopedic_evaluation_report_amit.pdf",
                "summary": "Orthopedic Knee Examination: Severe bilateral medial compartment osteoarthritis (Kellgren-Lawrence Grade IV) with bone-on-bone contact and varus deformity. Candidate for Total Knee Arthroplasty under Orthopedics.",
                "recommended_specialty": "Orthopedics",
                "important_notes": "Significant mechanical pain upon weight-bearing. Total Knee Replacement (TKA) advised.",
                "ocr_text": "PATIENT ORTHOPEDIC CLINICAL EVALUATION\nName: Amit Patel | Age: 62 | Gender: Male\nDepartment: Orthopedics & Joint Reconstruction Surgery\nClinical Presentation: Patient presents with chronic progressive bilateral knee pain for 4 years, exacerbating on ambulation.\nWeight-Bearing Radiography: Severe narrowing of medial joint space (<1.5mm), marginal osteophytes, subchondral sclerosis.\nImpression: Severe Bilateral Knee Osteoarthritis (Kellgren-Lawrence Grade IV).\nPlan: Elective Bilateral Total Knee Arthroplasty (TKA). Pre-operative cardiac and anesthetic clearance requested.\nMedications: Paracetamol 650mg TDS, Glucosamine 1500mg OD. NSAIDs strictly contraindicated.",
                "entities": [
                    ("Disease", "Bilateral Knee Osteoarthritis", 0.99, "Severe Bilateral Knee Osteoarthritis"),
                    ("Symptom", "Knee Joint Pain", 0.93, "chronic progressive bilateral knee pain"),
                    ("Procedure", "Total Knee Arthroplasty (TKA)", 0.97, "Elective Bilateral Total Knee Arthroplasty"),
                    ("Medication", "Paracetamol 650mg", 0.95, "Paracetamol 650mg TDS"),
                    ("BodyPart", "Bilateral Knee Joints", 0.98, "bilateral knee joints medial space")
                ]
            }
        }
    ]

    for spec in demo_specs:
        uid = spec["id"]
        user = db.query(User).filter(User.id == uid).first()
        hashed = hash_password(spec["password"])
        if not user:
            user = db.query(User).filter(User.email == spec["email"]).first()
        if not user:
            user = User(
                id=uid,
                email=spec["email"],
                full_name=spec["full_name"],
                hashed_password=hashed,
                role="patient"
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        else:
            user.full_name = spec["full_name"]
            user.email = spec["email"]
            user.hashed_password = hashed
            db.commit()

        # Ensure report exists
        rep_data = spec["report"]
        report = db.query(MedicalReport).filter(MedicalReport.user_id == user.id).first()
        if not report:
            report = MedicalReport(
                user_id=user.id,
                filename=rep_data["filename"],
                file_path=rep_data["file_path"],
                status="COMPLETED",
                ocr_text=rep_data["ocr_text"],
                summary=rep_data["summary"],
                recommended_specialty=rep_data["recommended_specialty"],
                important_notes=rep_data["important_notes"]
            )
            db.add(report)
            db.commit()
            db.refresh(report)
            for etype, ename, conf, context in rep_data["entities"]:
                ent = ExtractedEntity(
                    report_id=report.id,
                    entity_type=etype,
                    entity_name=ename,
                    confidence=conf,
                    context_snippet=context
                )
                db.add(ent)
            db.commit()
        else:
            report.recommended_specialty = rep_data["recommended_specialty"]
            db.commit()

        # Ensure profile exists
        prof_data = spec["profile"]
        profile = db.query(PatientProfile).filter(PatientProfile.user_id == user.id).first()
        if not profile:
            profile = PatientProfile(
                user_id=user.id,
                last_report_id=report.id if report else None,
                **prof_data
            )
            db.add(profile)
            db.commit()
        else:
            for k, v in prof_data.items():
                setattr(profile, k, v)
            if report:
                profile.last_report_id = report.id
            db.commit()


if __name__ == "__main__":
    init_db()
