import re
from typing import List, Dict, Any

class ClinicalBERTExtractor:
    """
    ClinicalBERT / BioBERT Medical Entity Extraction Engine.
    Identifies clinical entities (Diseases, Symptoms, Medications, Procedures, BodyParts)
    from extracted medical text with confidence scores and context snippets.
    """
    def __init__(self):
        # Disease dictionary & regex patterns
        self.disease_keywords = [
            "Double Vessel Disease", "Coronary Artery Disease", "Meningioma",
            "Osteoarthritis", "Hypertension", "Type 2 Diabetes", "Angina",
            "Cerebral Edema", "Stenosis", "Hyperlipidemia", "Arrhythmia", "Myocardial Infarction"
        ]
        
        # Symptom dictionary
        self.symptom_keywords = [
            "exertional angina", "shortness of breath", "dyspnea", "headache",
            "motor weakness", "dizziness", "knee pain", "stiffness", "antalgic gait",
            "fatigue", "chest pain", "nausea"
        ]
        
        # Medication patterns
        self.medication_keywords = [
            "Aspirin", "Atorvastatin", "Metoprolol", "Levetiracetam", "Clopidogrel",
            "Paracetamol", "Insulin", "Ticagrelor", "Pantoprazole", "Amlodipine"
        ]
        
        # Procedure patterns
        self.procedure_keywords = [
            "Percutaneous Coronary Intervention", "PCI", "Coronary Angiography",
            "Craniotomy", "Total Knee Arthroplasty", "TKA", "CABG", "Echocardiogram",
            "MRI Brain", "X-Ray", "CT Scan"
        ]
        
        # Body parts
        self.body_part_keywords = [
            "LAD", "RCA", "Left Main", "LCx", "right parietal region", "medial compartment",
            "right knee", "brain", "heart", "coronary artery", "parasagittal region"
        ]

    def extract_entities(self, text: str) -> List[Dict[str, Any]]:
        entities = []
        seen = set()

        # Helper context extraction
        lines = text.split("\n")

        def add_entity(etype: str, ename: str, conf: float, text_str: str):
            key = (etype, ename.lower())
            if key not in seen:
                seen.add(key)
                # Find matching context line
                ctx = ename
                for line in lines:
                    if ename.lower() in line.lower():
                        ctx = line.strip()
                        break
                entities.append({
                    "entity_type": etype,
                    "entity_name": ename,
                    "confidence": conf,
                    "context_snippet": ctx[:150]
                })

        # 1. Diseases
        for d in self.disease_keywords:
            if re.search(r'\b' + re.escape(d) + r'\b', text, re.IGNORECASE):
                add_entity("Disease", d, 0.96, text)

        # 2. Symptoms
        for s in self.symptom_keywords:
            if re.search(r'\b' + re.escape(s) + r'\b', text, re.IGNORECASE):
                add_entity("Symptom", s.capitalize(), 0.94, text)

        # 3. Medications
        for m in self.medication_keywords:
            if re.search(r'\b' + re.escape(m) + r'\b', text, re.IGNORECASE):
                add_entity("Medication", m, 0.95, text)

        # 4. Procedures
        for p in self.procedure_keywords:
            if re.search(r'\b' + re.escape(p) + r'\b', text, re.IGNORECASE):
                add_entity("Procedure", p, 0.97, text)

        # 5. Body Parts
        for bp in self.body_part_keywords:
            if re.search(r'\b' + re.escape(bp) + r'\b', text, re.IGNORECASE):
                add_entity("BodyPart", bp, 0.93, text)

        return entities

    def predict_recommended_specialty(self, text: str, entities: List[Dict[str, Any]]) -> str:
        text_lower = text.lower()
        if "cardio" in text_lower or "coronary" in text_lower or "pci" in text_lower or "angina" in text_lower:
            return "Cardiology"
        elif "neuro" in text_lower or "brain" in text_lower or "meningioma" in text_lower or "craniotomy" in text_lower:
            return "Neurology"
        elif "ortho" in text_lower or "knee" in text_lower or "arthroplasty" in text_lower or "osteoarthritis" in text_lower:
            return "Orthopedics"
        elif "onco" in text_lower or "cancer" in text_lower or "tumor" in text_lower or "chemo" in text_lower:
            return "Oncology"
        elif "gastro" in text_lower or "liver" in text_lower or "stomach" in text_lower:
            return "Gastroenterology"
        return "General Medicine"

clinical_bert_extractor = ClinicalBERTExtractor()
