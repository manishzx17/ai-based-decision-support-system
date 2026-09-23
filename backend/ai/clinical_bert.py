import re
from typing import List, Dict, Any, Optional

# Clinical / Biomedical NER Pipeline using Hugging Face Transformers
_transformer_nlp = None

def get_transformer_pipeline():
    """
    Lazily loads the biomedical token classification transformer model.
    Utilizes local cache (~/.cache/huggingface) to run offline and quickly.
    """
    global _transformer_nlp
    if _transformer_nlp is None:
        try:
            from transformers import AutoTokenizer, AutoModelForTokenClassification, pipeline
            model_id = "d4data/biomedical-ner-all"
            tokenizer = AutoTokenizer.from_pretrained(model_id)
            model = AutoModelForTokenClassification.from_pretrained(model_id)
            _transformer_nlp = pipeline(
                "ner",
                model=model,
                tokenizer=tokenizer,
                aggregation_strategy="simple",
                device=-1  # Strictly run on CPU to avoid Apple Silicon MPS shader segfaults
            )
        except Exception:
            _transformer_nlp = False
    return _transformer_nlp if _transformer_nlp is not False else None


class ClinicalBERTExtractor:
    """
    Biomedical Token Classification & Clinical Information Extraction Engine.
    Uses HuggingFace 'd4data/biomedical-ner-all' (DistilBERT-based 84-class biomedical token classifier)
    combined with contextual medical regex pattern matching and clinical tabular parsing.

    Extracts:
    1. Document Metadata (Patient Name, MRN/Patient ID, Report Date) - treated as identifiers, not clinical intelligence
    2. Patient Demographics (Age, Gender)
    3. Explicitly Reported Conditions (Conditions/diagnoses explicitly present in the report; no inferred diagnoses)
    4. Symptoms & Clinical Signs
    5. Diagnostic Tests performed
    6. Structured Test Results (Test name, value, unit, reference range, status)
    7. Medications (with dosage and frequency)
    8. Procedures (interventional, surgical)
    9. Medical History (past history, comorbidities, risk factors)
    """

    def __init__(self):
        # Comprehensive Clinical Lexicon & Patterns for multi-modal clinical intelligence
        self.disease_patterns = [
            r"\b(?:Double Vessel|Triple Vessel|Single Vessel)\s+(?:Coronary\s+)?Disease\b",
            r"\bCoronary Artery Disease\b|\bCAD\b",
            r"\bMeningioma\b|\bGlioma\b|\bAstrocytoma\b",
            r"\bOsteoarthritis\b|\bRheumatoid Arthritis\b|\bArthritis\b",
            r"\bHypertension\b|\bHTN\b",
            r"\bType\s*2\s*Diabetes(?:\s*Mellitus)?\b|\bT2DM\b|\bDiabetes Mellitus\b",
            r"\bAngina(?:\s*Pectoris)?\b",
            r"\bCerebral Edema\b|\bVasogenic Edema\b",
            r"\bStenosis\b|\bArteriosclerosis\b|\bAtherosclerosis\b",
            r"\bHyperlipidemia\b|\bDyslipidemia\b",
            r"\bMyocardial Infarction\b|\bSTEMI\b|\bNSTEMI\b",
            r"\bPneumonia\b|\bBronchitis\b|\bCOPD\b|\bAsthma\b",
            r"\bAppendicitis\b|\bCholecystitis\b|\bCholelithiasis\b",
            r"\bRenal Failure\b|\bChronic Kidney Disease\b|\bCKD\b",
            r"\bNeoplasm\b|\bCarcinoma\b|\bAdenoma\b|\bMalignancy\b",
            r"\bSpondylosis\b|\bDisc Herniation\b|\bRadiculopathy\b"
        ]

        self.symptom_patterns = [
            r"\bexertional angina\b|\bangina\b|\bchest pain\b",
            r"\bshortness of breath\b|\bdyspnea\b|\bbreathlessness\b",
            r"\bheadache\b|\bcephalea\b|\bmigraine\b",
            r"\bmotor weakness\b|\bfocal weakness\b|\bhemiparesis\b",
            r"\bdizziness\b|\bvertigo\b|\blightheadedness\b",
            r"\bknee pain\b|\bjoint pain\b|\barthralgia\b",
            r"\bjoint stiffness\b|\bstiffness\b",
            r"\bantalgic gait\b|\bgait disturbance\b",
            r"\bfatigue\b|\bmalaise\b|\blethargy\b",
            r"\bnausea\b|\bvomiting\b",
            r"\bpalpitations\b|\btachycardia\b",
            r"\bfever\b|\bpyrexia\b|\bchills\b",
            r"\bcough\b|\bhemoptysis\b"
        ]

        self.procedure_patterns = [
            r"\bPercutaneous Coronary Intervention\b|\bPCI\b",
            r"\bCoronary Angiography\b|\bAngiography\b|\bAngioplasty\b",
            r"\bCoronary Artery Bypass Grafting\b|\bCABG\b",
            r"\bCraniotomy\b|\bTumor Excision\b|\bBiopsy\b",
            r"\bTotal Knee Arthroplasty\b|\bTKA\b|\bKnee Replacement\b",
            r"\bTotal Hip Arthroplasty\b|\bTHA\b|\bHip Replacement\b",
            r"\bEchocardiogram\b|\bEcho\b|\bECG\b|\bEKG\b",
            r"\bMRI(?:\s+Brain|\s+Spine|\s+Knee)?\b",
            r"\bCT Scan\b|\bComputed Tomography\b",
            r"\bX-Ray(?:\s+Chest|\s+Knee|\s+Spine)?\b",
            r"\bEndoscopy\b|\bColonoscopy\b|\bLaparoscopy\b",
            r"\bCholecystectomy\b|\bAppendectomy\b"
        ]

        self.body_part_patterns = [
            r"\bLAD\b|\bLeft Anterior Descending(?:\s+Artery)?\b",
            r"\bRCA\b|\bRight Coronary Artery\b",
            r"\bLCx\b|\bLeft Circumflex(?:\s+Artery)?\b",
            r"\bLeft Main(?:\s+Coronary Artery)?\b",
            r"\bparasagittal\s+parietal\s+region\b|\bparietal\s+lobe\b",
            r"\bmedial compartment\b|\blateral compartment\b",
            r"\b(?:right|left)?\s*knee\b",
            r"\bbrain\b|\bcerebrum\b|\bcerebellum\b",
            r"\bheart\b|\bcoronary artery\b|\bmyocardium\b",
            r"\blung(?:s)?\b|\bthorax\b",
            r"\bliver\b|\bgallbladder\b|\bkidney(?:s)?\b",
            r"\blumbar spine\b|\bcervical spine\b"
        ]

    def _clean_token(self, token: str) -> str:
        """Strips subword markers and extraneous boundary punctuation."""
        t = re.sub(r"^##", "", token)
        t = t.strip(" \t\n\r,;:()[]{}'\"`.-_")
        return t

    def _is_negated_match(self, text: str, start_idx: int, end_idx: int) -> bool:
        """Determines if an entity mention is preceded or followed by clinical negation cues."""
        preceding = text[max(0, start_idx - 70):start_idx]
        preceding_clause = re.split(r"[\n\.;]", preceding)[-1].lower()
        neg_pre_pattern = r"\b(?:no\s+evidence\s+of|negative\s+for|rule\s+out|ruled\s+out|denies|absence\s+of|without\s+(?:any\s+)?evidence\s+of|without|no\s+signs?\s+of|free\s+of|unremarkable\s+for|normal\s+study|no|not)\b"
        if re.search(neg_pre_pattern, preceding_clause):
            return True

        following = text[end_idx:min(len(text), end_idx + 40)]
        following_clause = re.split(r"[\n\.;,]", following)[0].lower()
        neg_post_pattern = r"\b(?:negative|ruled\s+out|not\s+present|absent|normal|unremarkable)\b"
        if re.search(neg_post_pattern, following_clause):
            return True

        return False

    def _extract_context(self, term: str, lines: List[str]) -> str:
        """Finds the genuine matching line in the report text for context grounding."""
        term_lower = term.lower()
        for line in lines:
            if term_lower in line.lower():
                cleaned = line.strip()
                if len(cleaned) > 160:
                    cleaned = cleaned[:160] + "..."
                return cleaned
        return term

    def _extract_structured_test_results(self, text: str, lines: List[str]) -> List[Dict[str, Any]]:
        """Extracts structured diagnostic and laboratory measurements with units."""
        results = []

        # 1. Ejection Fraction (LVEF)
        for m in re.finditer(r"\b(?:LVEF|EF)\s*[:=]?\s*(\d{2}%|\d{2}\s*%)", text, re.IGNORECASE):
            full_match = m.group(0).strip()
            val = m.group(1).strip()
            results.append({
                "entity_type": "TestResult",
                "entity_name": f"LVEF: {val}",
                "confidence": 0.98,
                "context_snippet": self._extract_context(full_match, lines)
            })

        # 2. Vessel Stenosis percentages
        for m in re.finditer(r"\b(?:LAD|RCA|LCx|Left Main)?:?\s*(\d{2,3}%\s*(?:proximal|mid-vessel|distal)?\s*stenosis)", text, re.IGNORECASE):
            full_match = m.group(1).strip()
            results.append({
                "entity_type": "TestResult",
                "entity_name": f"Stenosis: {full_match}",
                "confidence": 0.97,
                "context_snippet": self._extract_context(full_match, lines)
            })

        # 3. Blood Pressure
        for m in re.finditer(r"\b(?:BP|Blood Pressure)\s*[:=]?\s*(\d{2,3}/\d{2,3}(?:\s*mmHg)?)", text, re.IGNORECASE):
            val = m.group(1).strip()
            results.append({
                "entity_type": "TestResult",
                "entity_name": f"BP: {val}",
                "confidence": 0.96,
                "context_snippet": self._extract_context(val, lines)
            })

        # 4. HbA1c
        for m in re.finditer(r"\bHbA1c\s*[:=]?\s*(\d+(?:\.\d+)?%?)", text, re.IGNORECASE):
            val = m.group(1).strip()
            results.append({
                "entity_type": "TestResult",
                "entity_name": f"HbA1c: {val}",
                "confidence": 0.97,
                "context_snippet": self._extract_context("HbA1c", lines)
            })

        # 5. Serum Creatinine
        for m in re.finditer(r"\b(?:Serum\s+)?Creatinine\s*[:=]?\s*(\d+(?:\.\d+)?\s*(?:mg/dL)?)", text, re.IGNORECASE):
            val = m.group(1).strip()
            results.append({
                "entity_type": "TestResult",
                "entity_name": f"Creatinine: {val}",
                "confidence": 0.96,
                "context_snippet": self._extract_context("Creatinine", lines)
            })

        # 6. Blood Sugar (FBS / PPBS / RBS)
        for m in re.finditer(r"\b(FBS|PPBS|RBS|Fasting Blood Sugar|Blood Glucose)\s*[:=]?\s*(\d{2,3}\s*(?:mg/dL)?)", text, re.IGNORECASE):
            label = m.group(1).strip()
            val = m.group(2).strip()
            results.append({
                "entity_type": "TestResult",
                "entity_name": f"{label}: {val}",
                "confidence": 0.96,
                "context_snippet": self._extract_context(label, lines)
            })

        return results

    def _extract_structured_medications(self, text: str, lines: List[str]) -> List[Dict[str, Any]]:
        """Extracts medication names with dosage and administration frequency."""
        meds = []
        med_pattern = (
            r"\b(Aspirin|Atorvastatin|Metoprolol|Levetiracetam|Clopidogrel|"
            r"Paracetamol|Insulin|Ticagrelor|Pantoprazole|Amlodipine|Metformin|"
            r"Cefixime|Amoxicillin|Ciprofloxacin|Azithromycin|Losartan|"
            r"Telmisartan|Rosuvastatin|Omeprazole|Tramadol|Diclofenac)\b"
            r"(?:\s*(\d+(?:\.\d+)?\s*(?:mg|mcg|g|IU|ml)\b))?"
            r"(?:\s*(OD|BD|TDS|QDS|HS|PRN|once daily|twice daily))?"
        )

        for m in re.finditer(med_pattern, text, re.IGNORECASE):
            drug = m.group(1).capitalize()
            dose = m.group(2).strip() if m.group(2) else ""
            freq = m.group(3).upper() if m.group(3) else ""

            parts = [drug]
            if dose:
                parts.append(dose)
            if freq:
                parts.append(freq)

            full_med = " ".join(parts)
            meds.append({
                "entity_type": "Medication",
                "entity_name": full_med,
                "confidence": 0.96,
                "context_snippet": self._extract_context(m.group(0).strip(), lines)
            })

        return meds

    def _extract_medical_history(self, text: str, lines: List[str]) -> List[Dict[str, Any]]:
        """Identifies past medical history, chronic conditions, and patient risk factors."""
        history = []
        hist_patterns = [
            r"\b(?:History of|H/O|Known case of|K/C/O)\s+([^,.;\n]+)",
            r"\b(?:Duration|Presenting since):\s*(\d+\s*(?:years?|months?|weeks?))",
            r"\b(?:Known diabetic|Known hypertensive|Past smoker)\b"
        ]

        for pat in hist_patterns:
            for m in re.finditer(pat, text, re.IGNORECASE):
                val = m.group(0).strip()
                if 4 < len(val) < 80:
                    history.append({
                        "entity_type": "MedicalHistory",
                        "entity_name": val.capitalize(),
                        "confidence": 0.91,
                        "context_snippet": self._extract_context(val, lines)
                    })

        return history

    def extract_metadata(self, text: str) -> Dict[str, Optional[str]]:
        """
        Extracts document metadata and identifiers: Patient Name, Patient ID / MRN, Report Date.
        Note: Metadata fields are strictly identifiers, not clinical intelligence.
        """
        metadata = {
            "patient_name": None,
            "patient_id": None,
            "report_date": None
        }

        # 1. Patient Name
        name_patterns = [
            r"(?:Patient\s*Name|Pt\.?\s*Name|Name\s*of\s*Patient|Name)\s*[:\-]\s*([A-Za-z\.\s]{2,35}?)(?=\s{2,}|\n|,|Age|Sex|Gender|MRN|UHID|DOB|Patient\s*ID|\bID\b|$)",
            r"(?:Mr\.|Mrs\.|Ms\.|Shri|Smt\.)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})"
        ]
        for pat in name_patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                val = m.group(1).strip()
                val = re.sub(r"\s+", " ", val)
                if len(val) >= 3 and val.lower() not in {"patient", "report", "test", "date", "hospital", "summary", "clinical", "evaluation", "sample"}:
                    metadata["patient_name"] = val
                    break

        # 2. Patient ID / MRN / UHID / Registration No
        id_patterns = [
            r"\b(?:MRN|UHID|Patient\s*ID|Reg(?:istration)?(?:\s*(?:No|Number|#))?|Record\s*ID|Case\s*ID)\s*[:\-#]\s*([A-Za-z0-9\-_]{3,20})\b",
            r"\b(?:IP|OP|IPD|OPD)\s*(?:No|#)\s*[:\-]?\s*([A-Za-z0-9\-_]{3,15})\b"
        ]
        for pat in id_patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                metadata["patient_id"] = m.group(1).strip()
                break

        # 3. Report Date
        date_patterns = [
            r"\b(?:Report\s*Date|Study\s*Date|Exam\s*Date|Date\s*of\s*Report|Collection\s*Date|Date)\s*[:\-]\s*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4}|\d{4}[\/\-\.]\d{1,2}[\/\-\.]\d{1,2}|[A-Za-z]{3,9}\s+\d{1,2},?\s+\d{4}|\d{1,2}\s+[A-Za-z]{3,9}\s+\d{4})\b",
            r"\b(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{4})\b"
        ]
        for pat in date_patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                metadata["report_date"] = m.group(1).strip()
                break

        return metadata

    def extract_demographics(self, text: str) -> Dict[str, Any]:
        """
        Extracts patient demographics: Age (int) and Gender (normalized string).
        """
        demographics = {
            "age": None,
            "gender": None
        }

        # Age
        age_patterns = [
            r"\b(?:Age|Aged)\s*[:\-\/]?\s*(\d{1,3})\s*(?:Y(?:ears?|rs?)?)?\b",
            r"\b(\d{1,3})\s*(?:Y|Yrs|Years)(?:-Old|\s+old)?\b",
            r"\b(\d{1,3})\s*(?:Y|Yrs|Years)?[\s\/]*(?:Male|Female|M|F)\b"
        ]
        for pat in age_patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                try:
                    val = int(m.group(1))
                    if 0 <= val <= 120:
                        demographics["age"] = val
                        break
                except ValueError:
                    pass

        # Gender
        gender_patterns = [
            r"\b(?:Gender|Sex)\s*[:\-]?\s*(Male|Female|M|F)\b",
            r"\b\d{1,3}\s*(?:Y|Yrs|Years)?[\s\/\-,]+(Male|Female|M|F)\b",
            r"\b(Male|Female)\b"
        ]
        for pat in gender_patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                raw_g = m.group(1).strip().upper()
                if raw_g in ["M", "MALE"]:
                    demographics["gender"] = "Male"
                elif raw_g in ["F", "FEMALE"]:
                    demographics["gender"] = "Female"
                else:
                    demographics["gender"] = raw_g.capitalize()
                break

        return demographics

    def extract_conditions(self, text: str, lines: List[str]) -> List[str]:
        """
        Extracts explicitly reported conditions and diagnoses from the document.
        STRICT REQUIREMENT: Does NOT infer or extrapolate diagnoses. Only extracts
        diagnoses/conditions explicitly stated in clinical impressions, diagnoses sections,
        or explicitly documented diagnostic statements.
        """
        conditions = []
        seen_cond = set()

        # Section-based extraction (Highest precision)
        diag_section_pat = r"(?:FINAL\s+DIAGNOSIS(?:\s*&?\s*CLINICAL\s+IMPRESSION)?|PRIMARY\s+DIAGNOSIS|DIAGNOSES|DIAGNOSIS|IMPRESSION|ASSESSMENT|CLINICAL\s+FINDINGS)\s*[:\-]([\s\S]*?)(?=\n\s*(?:RECOMMENDATIONS?|PLAN|TREATMENT|PROCEDURE|PAST\s+HISTORY|MEDICATIONS?|DISCHARGE|FOLLOW\s*UP|DOCTOR|SIGNATURE|SIGNED|$))"
        matches = re.finditer(diag_section_pat, text, re.IGNORECASE)
        for m in matches:
            section_text = m.group(1).strip()
            for ln in section_text.split("\n"):
                cleaned_ln = re.sub(r"^[\s*\-•\d\.\)]+", "", ln).strip()
                if not cleaned_ln or len(cleaned_ln) < 4 or len(cleaned_ln) > 100:
                    continue
                if any(neg in cleaned_ln.lower() for neg in ["rule out", "no evidence of", "normal study", "unremarkable", "negative for"]):
                    continue
                k = cleaned_ln.lower()
                if k not in seen_cond:
                    seen_cond.add(k)
                    conditions.append(cleaned_ln)

        # Explicit occurrences of recognized clinical disease entities
        for pat in self.disease_patterns:
            for m in re.finditer(pat, text, re.IGNORECASE):
                if self._is_negated_match(text, m.start(), m.end()):
                    continue
                match_val = m.group(0).strip()
                k = match_val.lower()
                if k not in seen_cond:
                    seen_cond.add(k)
                    conditions.append(match_val)

        return conditions

    def extract_symptoms(self, text: str, lines: List[str]) -> List[str]:
        """Extracts symptoms and clinical complaints explicitly documented in the report."""
        symptoms = []
        seen_sym = set()

        cc_section_pat = r"(?:CHIEF\s+COMPLAINTS?(?:\s*&?\s*SYMPTOMS)?|PRESENTING\s+SYMPTOMS?|COMPLAINTS\s+OF|SYMPTOMS)\s*[:\-]([\s\S]*?)(?=\n\s*(?:PAST\s+HISTORY|PHYSICAL\s+EXAM|INVESTIGATIONS|DIAGNOSIS|IMPRESSION|PLAN|$))"
        for m in re.finditer(cc_section_pat, text, re.IGNORECASE):
            sec_text = m.group(1).strip()
            # If paragraph format like "Patient presented with complaints of exertional angina, chest pain, shortness of breath."
            c_match = re.search(r"complaints\s+of\s+([^.]+)", sec_text, re.IGNORECASE)
            if c_match:
                phrase = c_match.group(1)
                for part in re.split(r",|\band\b", phrase):
                    c_item = part.strip().capitalize()
                    if 3 < len(c_item) < 80:
                        k = c_item.lower()
                        if k not in seen_sym:
                            seen_sym.add(k)
                            symptoms.append(c_item)
            else:
                for ln in sec_text.split("\n"):
                    cleaned = re.sub(r"^[\s*\-•\d\.\)]+", "", ln).strip()
                    if 3 < len(cleaned) < 80:
                        k = cleaned.lower()
                        if k not in seen_sym:
                            seen_sym.add(k)
                            symptoms.append(cleaned)

        for pat in self.symptom_patterns:
            for m in re.finditer(pat, text, re.IGNORECASE):
                if self._is_negated_match(text, m.start(), m.end()):
                    continue
                val = m.group(0).strip().capitalize()
                k = val.lower()
                if k not in seen_sym:
                    seen_sym.add(k)
                    symptoms.append(val)

        return symptoms

    def extract_tests(self, text: str, lines: List[str]) -> List[str]:
        """Extracts names of diagnostic investigations, imaging, or laboratory tests performed."""
        tests = []
        seen_tests = set()

        test_patterns = [
            r"\b(?:Coronary\s+Angiography|Coronary\s+Angiogram|CAG)\b",
            r"\b(?:2D\s+Echocardiogram|Echocardiogram|Transthoracic\s+Echocardiogram|Echo)\b",
            r"\b(?:Electrocardiogram|ECG|EKG)\b",
            r"\b(?:MRI(?:\s+Brain|\s+Spine|\s+Knee|\s+Pelvis)?|Magnetic\s+Resonance\s+Imaging)\b",
            r"\b(?:CT(?:\s+Scan|\s+Chest|\s+Abdomen|\s+Brain|\s+Angiography)?|Computed\s+Tomography)\b",
            r"\b(?:X-Ray(?:\s+Chest|\s+Knee|\s+Spine)?|Chest\s+Radiograph)\b",
            r"\b(?:Complete\s+Blood\s+Count|CBC|Hemogram)\b",
            r"\b(?:Renal\s+Function\s+Test|RFT|Kidney\s+Function\s+Test|KFT)\b",
            r"\b(?:Liver\s+Function\s+Test|LFT|Hepatic\s+Function\s+Panel)\b",
            r"\b(?:Lipid\s+Profile|Lipid\s+Panel)\b",
            r"\b(?:HbA1c(?:\s+Test)?|Glycated\s+Hemoglobin)\b",
            r"\b(?:Urine\s+Routine|Urinalysis)\b",
            r"\b(?:Ultrasound(?:\s+Abdomen|\s+Pelvis)?|USG)\b",
            r"\b(?:Upper\s+GI\s+Endoscopy|Colonoscopy|Endoscopy)\b",
            r"\b(?:Histopathology(?:\s+Report)?|Biopsy|Histopathological\s+Examination)\b"
        ]

        for pat in test_patterns:
            for m in re.finditer(pat, text, re.IGNORECASE):
                val = m.group(0).strip()
                k = val.lower()
                if k not in seen_tests:
                    seen_tests.add(k)
                    tests.append(val)

        return tests

    def extract_structured_test_results_detailed(self, text: str, lines: List[str]) -> List[Dict[str, Any]]:
        """Extracts structured diagnostic and lab results with values, units, reference ranges, and status."""
        results: List[Dict[str, Any]] = []
        seen_tests = set()

        # 1. LVEF
        m = re.search(r"\b(?:LVEF|EF)\s*[:=]?\s*(\d{1,2}%|\d{1,2}\s*%)", text, re.IGNORECASE)
        if m:
            val = m.group(1).strip()
            digits = re.sub(r"[^\d]", "", val)
            val_num = int(digits) if digits else 55
            status = "Low" if val_num < 50 else ("High" if val_num > 70 else "Normal")
            results.append({
                "test_name": "Left Ventricular Ejection Fraction (LVEF)",
                "value": val,
                "unit": "%",
                "reference_range": "50% - 70%",
                "status": status
            })
            seen_tests.add("lvef")

        # 2. Stenosis
        for sm in re.finditer(r"\b(LAD|RCA|LCx|Left Main)\s*[:\-]?\s*(\d{1,3}%\s*(?:proximal|mid|distal)?\s*stenosis|\d{1,3}%)", text, re.IGNORECASE):
            vessel = sm.group(1).upper()
            sten_val = sm.group(2).strip()
            pct_match = re.search(r"(\d{1,3})%", sten_val)
            pct = int(pct_match.group(1)) if pct_match else 0
            stat = "Critical" if pct >= 70 else ("High" if pct >= 50 else "Normal")
            key = f"{vessel.lower()} stenosis"
            if key not in seen_tests:
                results.append({
                    "test_name": f"{vessel} Stenosis",
                    "value": sten_val,
                    "unit": "%",
                    "reference_range": "< 50%",
                    "status": stat
                })
                seen_tests.add(key)

        # 3. Blood Pressure
        m = re.search(r"\b(?:BP|Blood Pressure)\s*[:=]?\s*(\d{2,3}\s*\/\s*\d{2,3}(?:\s*mmHg)?)", text, re.IGNORECASE)
        if m and "blood pressure" not in seen_tests:
            bp_val = m.group(1).strip()
            sys_m = re.search(r"(\d{2,3})\s*\/", bp_val)
            stat = "High" if (sys_m and int(sys_m.group(1)) >= 140) else "Normal"
            results.append({
                "test_name": "Blood Pressure",
                "value": bp_val.replace("mmHg", "").strip(),
                "unit": "mmHg",
                "reference_range": "90/60 - 120/80 mmHg",
                "status": stat
            })
            seen_tests.add("blood pressure")

        # 4. HbA1c
        m = re.search(r"\bHbA1c\s*[:=]?\s*(\d+(?:\.\d+)?)\s*%?", text, re.IGNORECASE)
        if m and "hba1c" not in seen_tests:
            hba1c_val = m.group(1).strip()
            stat = "High" if float(hba1c_val) >= 6.5 else ("Pre-diabetic" if float(hba1c_val) >= 5.7 else "Normal")
            results.append({
                "test_name": "HbA1c (Glycated Hemoglobin)",
                "value": hba1c_val,
                "unit": "%",
                "reference_range": "< 5.7%",
                "status": stat
            })
            seen_tests.add("hba1c")

        # 5. Serum Creatinine
        m = re.search(r"\b(?:Serum\s+)?Creatinine\s*[:=]?\s*(\d+(?:\.\d+)?)\s*(?:mg/dL)?", text, re.IGNORECASE)
        if m and "creatinine" not in seen_tests:
            creat_val = m.group(1).strip()
            stat = "High" if float(creat_val) > 1.3 else ("Low" if float(creat_val) < 0.6 else "Normal")
            results.append({
                "test_name": "Serum Creatinine",
                "value": creat_val,
                "unit": "mg/dL",
                "reference_range": "0.7 - 1.3 mg/dL",
                "status": stat
            })
            seen_tests.add("creatinine")

        # 6. Blood Sugar (FBS / PPBS)
        fbs_m = re.search(r"\b(?:FBS|Fasting Blood Sugar)\s*[:=]?\s*(\d{2,3})\s*(?:mg/dL)?", text, re.IGNORECASE)
        if fbs_m and "fbs" not in seen_tests:
            val = fbs_m.group(1).strip()
            stat = "High" if int(val) > 100 else ("Low" if int(val) < 70 else "Normal")
            results.append({
                "test_name": "Fasting Blood Sugar (FBS)",
                "value": val,
                "unit": "mg/dL",
                "reference_range": "70 - 99 mg/dL",
                "status": stat
            })
            seen_tests.add("fbs")

        # 7. Hemoglobin
        hb_m = re.search(r"\b(?:Hemoglobin|Hb)\s*[:=]?\s*(\d+(?:\.\d+)?)\s*(?:g/dL)?", text, re.IGNORECASE)
        if hb_m and "hemoglobin" not in seen_tests:
            val = hb_m.group(1).strip()
            stat = "Low" if float(val) < 13.0 else ("High" if float(val) > 17.5 else "Normal")
            results.append({
                "test_name": "Hemoglobin",
                "value": val,
                "unit": "g/dL",
                "reference_range": "13.0 - 17.5 g/dL",
                "status": stat
            })
            seen_tests.add("hemoglobin")

        # 8. Platelet Count
        plt_m = re.search(r"\b(?:Platelets?|Platelet Count)\s*[:=]?\s*([\d,]+)\s*(?:\/mcL|\/uL|\/cumm)?", text, re.IGNORECASE)
        if plt_m and "platelet" not in seen_tests:
            raw_val = plt_m.group(1).strip()
            num_val = int(raw_val.replace(",", "")) if raw_val.replace(",", "").isdigit() else 250000
            stat = "Low" if num_val < 150000 else ("High" if num_val > 450000 else "Normal")
            results.append({
                "test_name": "Platelet Count",
                "value": raw_val,
                "unit": "/mcL",
                "reference_range": "150,000 - 450,000 /mcL",
                "status": stat
            })
            seen_tests.add("platelet")

        # 9. Tabular lines: e.g. "Total Cholesterol    240    mg/dL    <200    High"
        table_pat = r"^\s*([A-Za-z\s\(\)\-\/]{3,30})\s+([0-9]+(?:\.[0-9]+)?)\s+(mg/dL|g/dL|mEq/L|%|mmol/L|U/L|IU/L|/mcL|ng/mL)\s+([0-9\.\<\>\-\s]+)\s+(Normal|High|Low|Critical|Abnormal)"
        for ln in lines:
            tm = re.search(table_pat, ln, re.IGNORECASE)
            if tm:
                tname = tm.group(1).strip()
                k = tname.lower()
                if k not in seen_tests and len(tname) > 2:
                    seen_tests.add(k)
                    results.append({
                        "test_name": tname,
                        "value": tm.group(2).strip(),
                        "unit": tm.group(3).strip(),
                        "reference_range": tm.group(4).strip(),
                        "status": tm.group(5).strip().capitalize()
                    })

        return results

    def extract_medications(self, text: str, lines: List[str]) -> List[str]:
        """Extracts medications along with dosage and administration frequency."""
        medications = []
        seen_meds = set()

        med_items = self._extract_structured_medications(text, lines)
        for item in med_items:
            m_name = item["entity_name"].strip()
            k = m_name.lower()
            if k not in seen_meds:
                seen_meds.add(k)
                medications.append(m_name)

        return medications

    def extract_procedures(self, text: str, lines: List[str]) -> List[str]:
        """Extracts surgical and interventional procedures documented in the report."""
        procedures = []
        seen_proc = set()

        for pat in self.procedure_patterns:
            for m in re.finditer(pat, text, re.IGNORECASE):
                val = m.group(0).strip()
                k = val.lower()
                if k not in seen_proc:
                    seen_proc.add(k)
                    procedures.append(val)

        return procedures

    def extract_medical_history_list(self, text: str, lines: List[str]) -> List[str]:
        """Extracts medical history, chronic conditions, and risk factors."""
        history = []
        seen_hist = set()

        hist_items = self._extract_medical_history(text, lines)
        for item in hist_items:
            h_name = item["entity_name"].strip()
            k = h_name.lower()
            if k not in seen_hist:
                seen_hist.add(k)
                history.append(h_name)

        return history

    def extract_structured_clinical_info(self, text: str) -> Dict[str, Any]:
        """
        Full Phase 2 Pipeline Structured Clinical Information Extractor.
        Ingests document text and extracts the 8 required clinical categories
        plus document metadata/identifiers.
        Does NOT contain recommended_specialty (belongs to Phase 5).
        Does NOT infer diagnoses (extracts only explicitly reported conditions).
        """
        if not text or not text.strip():
            return {
                "metadata": {"patient_name": None, "patient_id": None, "report_date": None},
                "demographics": {"age": None, "gender": None},
                "conditions": [],
                "symptoms": [],
                "tests": [],
                "test_results": [],
                "medications": [],
                "procedures": [],
                "medical_history": []
            }

        lines = [ln.strip() for ln in text.split("\n") if ln.strip()]

        metadata = self.extract_metadata(text)
        demographics = self.extract_demographics(text)
        conditions = self.extract_conditions(text, lines)
        symptoms = self.extract_symptoms(text, lines)
        tests = self.extract_tests(text, lines)
        test_results = self.extract_structured_test_results_detailed(text, lines)
        medications = self.extract_medications(text, lines)
        procedures = self.extract_procedures(text, lines)
        medical_history = self.extract_medical_history_list(text, lines)

        return {
            "metadata": metadata,
            "demographics": demographics,
            "conditions": conditions,
            "symptoms": symptoms,
            "tests": tests,
            "test_results": test_results,
            "medications": medications,
            "procedures": procedures,
            "medical_history": medical_history
        }

    def extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """
        Main extraction method. Ingests raw OCR document text, applies genuine
        Biomedical Transformer NER model, and extracts structured entities.
        """
        if not text or not text.strip():
            return []

        lines = [ln.strip() for ln in text.split("\n") if ln.strip()]
        entities: List[Dict[str, Any]] = []
        seen = set()

        STOP_TOKENS = {
            "patient", "doctor", "consultant", "name", "male", "female", "age", "years", "year",
            "date", "report", "hospital", "ticket", "regd", "opd", "mobile", "phone", "address",
            "time", "sure", "left", "right", "daily", "occupation", "wife", "house", "department"
        }
        ALLOWED_SHORT_ACRONYMS = {"ct", "mr", "bp", "ef", "hr", "rr", "hb", "dm", "oa"}

        def add_entity(etype: str, ename: str, conf: float, snippet: Optional[str] = None):
            cleaned_name = self._clean_token(ename)
            lower_name = cleaned_name.lower()
            
            # Filter noise, stop tokens, and incomplete fragments
            if len(cleaned_name) < 3 and lower_name not in ALLOWED_SHORT_ACRONYMS:
                return
            if lower_name in STOP_TOKENS:
                return
            if cleaned_name.isdigit():
                return

            key = (etype, lower_name)
            if key not in seen:
                seen.add(key)
                ctx = snippet or self._extract_context(cleaned_name, lines)
                entities.append({
                    "entity_type": etype,
                    "entity_name": cleaned_name,
                    "confidence": round(float(conf), 3),
                    "context_snippet": ctx
                })

        # 1. Structured Laboratory & Diagnostic Test Results (Highest clinical precision)
        for item in self._extract_structured_test_results(text, lines):
            add_entity(item["entity_type"], item["entity_name"], item["confidence"], item["context_snippet"])

        # 2. Structured Medications with Dosages & Frequencies
        for item in self._extract_structured_medications(text, lines):
            add_entity(item["entity_type"], item["entity_name"], item["confidence"], item["context_snippet"])

        # 3. Medical History and Risk Factors
        for item in self._extract_medical_history(text, lines):
            add_entity(item["entity_type"], item["entity_name"], item["confidence"], item["context_snippet"])

        # 4. Core Clinical Multi-Word Patterns (Ensures complete compound terms like 'Grade IV Osteoarthritis')
        for pat in self.disease_patterns:
            for m in re.finditer(pat, text, re.IGNORECASE):
                if self._is_negated_match(text, m.start(), m.end()):
                    continue
                add_entity("Disease", m.group(0).strip(), 0.96)

        for pat in self.symptom_patterns:
            for m in re.finditer(pat, text, re.IGNORECASE):
                if self._is_negated_match(text, m.start(), m.end()):
                    continue
                add_entity("Symptom", m.group(0).strip().capitalize(), 0.94)

        for pat in self.procedure_patterns:
            for m in re.finditer(pat, text, re.IGNORECASE):
                add_entity("Procedure", m.group(0).strip(), 0.96)

        for pat in self.body_part_patterns:
            for m in re.finditer(pat, text, re.IGNORECASE):
                add_entity("BodyPart", m.group(0).strip(), 0.94)

        # 5. Hugging Face Transformer Biomedical NER Model
        nlp = get_transformer_pipeline()
        if nlp is not None:
            try:
                # Segment text into manageable chunks for transformer context window (max 512 tokens)
                chunk_size = 800
                chunks = [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]
                for chunk in chunks:
                    hf_res = nlp(chunk)
                    for item in hf_res:
                        grp = item.get("entity_group", "")
                        raw_word = item.get("word", "")
                        score = float(item.get("score", 0.90))

                        cleaned_w = self._clean_token(raw_word)
                        if len(cleaned_w) < 3 and cleaned_w.lower() not in ALLOWED_SHORT_ACRONYMS:
                            continue

                        # Map transformer labels to standard entity types
                        if grp in ["Disease_disorder"]:
                            add_entity("Disease", cleaned_w.capitalize(), score)
                        elif grp in ["Sign_symptom"]:
                            add_entity("Symptom", cleaned_w.capitalize(), score)
                        elif grp in ["Medication"]:
                            add_entity("Medication", cleaned_w.capitalize(), score)
                        elif grp in ["Therapeutic_procedure", "Diagnostic_procedure"]:
                            add_entity("Procedure", cleaned_w.title(), score)
                        elif grp in ["Biological_structure"]:
                            add_entity("BodyPart", cleaned_w.title(), score)
                        elif grp in ["Lab_value"]:
                            add_entity("TestResult", cleaned_w, score)
                        elif grp in ["History"]:
                            add_entity("MedicalHistory", cleaned_w.capitalize(), score)
            except Exception:
                pass

        return entities

    def predict_recommended_specialty(self, text: str, entities: List[Dict[str, Any]]) -> str:
        """
        Dynamically infers the recommended medical specialty from the extracted clinical
        entities and overall report findings.
        """
        text_lower = text.lower()
        specialty_scores = {
            "Cardiology": 0,
            "Neurology": 0,
            "Orthopedics": 0,
            "Oncology": 0,
            "Gastroenterology": 0,
            "Pulmonology": 0,
            "Nephrology": 0,
            "Endocrinology": 0,
            "General Medicine": 1
        }

        # Scan extracted entities for targeted specialties
        for ent in entities:
            ename = ent["entity_name"].lower()
            etype = ent["entity_type"]

            # Cardiology cues
            if any(k in ename for k in ["coronary", "angina", "lad", "rca", "lcx", "pci", "cabg", "stenosis", "stent", "lvef", "infarction"]):
                specialty_scores["Cardiology"] += 4
            # Neurology cues
            if any(k in ename for k in ["brain", "meningioma", "craniotomy", "seizure", "levetiracetam", "parietal", "cerebral", "neurol"]):
                specialty_scores["Neurology"] += 4
            # Orthopedics cues
            if any(k in ename for k in ["knee", "osteoarthritis", "arthroplasty", "tka", "bone", "joint", "fracture", "spondyl"]):
                specialty_scores["Orthopedics"] += 4
            # Oncology cues
            if any(k in ename for k in ["tumor", "carcinoma", "malignan", "neoplasm", "biopsy", "chemo"]):
                specialty_scores["Oncology"] += 4
            # Gastroenterology cues
            if any(k in ename for k in ["cholelith", "gallbladder", "liver", "stomach", "endoscopy", "colon", "gastric"]):
                specialty_scores["Gastroenterology"] += 4
            # Pulmonology cues
            if any(k in ename for k in ["lung", "pneumonia", "bronch", "dyspnea", "asthma", "copd"]):
                specialty_scores["Pulmonology"] += 3
            # Nephrology cues
            if any(k in ename for k in ["renal", "creatinine", "kidney", "dialysis"]):
                specialty_scores["Nephrology"] += 4
            # Endocrinology cues
            if any(k in ename for k in ["diabetes", "hba1c", "fbs", "insulin", "thyroid"]):
                specialty_scores["Endocrinology"] += 4

        # Also inspect full text body for department headings
        if "cardio" in text_lower or "cath lab" in text_lower or "angiography" in text_lower:
            specialty_scores["Cardiology"] += 3
        if "neuro" in text_lower or "brain spine" in text_lower:
            specialty_scores["Neurology"] += 3
        if "ortho" in text_lower or "joint replacement" in text_lower:
            specialty_scores["Orthopedics"] += 3
        if "oncol" in text_lower or "cancer" in text_lower:
            specialty_scores["Oncology"] += 3
        if "gastro" in text_lower:
            specialty_scores["Gastroenterology"] += 3
        if "pulmon" in text_lower or "respiratory" in text_lower:
            specialty_scores["Pulmonology"] += 3
        if "nephro" in text_lower:
            specialty_scores["Nephrology"] += 3
        if "endocrin" in text_lower:
            specialty_scores["Endocrinology"] += 3

        # Return specialty with highest score
        best_specialty = max(specialty_scores.items(), key=lambda x: x[1])
        if best_specialty[1] > 1:
            return best_specialty[0]
        return "General Medicine"


clinical_bert_extractor = ClinicalBERTExtractor()
