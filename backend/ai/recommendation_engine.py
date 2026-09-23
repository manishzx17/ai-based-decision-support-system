"""
Context-Aware Personalized Medical Decision Support Engine (Phase 5).

Implements:
1. Stage 1: Transparent Eligibility Filtering (Hard Constraints) with explicit exclusion reasons.
2. Stage 2: Explainable Deterministic Weighted Multi-Criteria Ranking:
   - Clinical Match: 35%
   - Cost & Insurance: 25%
   - Geographic Proximity: 20%
   - Quality & Accreditation: 20%
   (Operational availability removed as per clinical specification).
   Dynamic weight shifting across Priority Modes (Balanced, Cost-Sensitive, Quality-Focused, Proximity-Focused).
3. Evidence-Grounded Treatment Pathways derived strictly from the Phase 4 RAG knowledge layer.
4. Full integration with Phase 3 Shared Clinical Profile and explicit patient preferences.
"""

import math
import re
from typing import List, Dict, Any, Optional, Tuple
from ai.rag_engine import rag_engine

CITY_COORDINATES: Dict[str, tuple[float, float]] = {
    "hyderabad": (17.3850, 78.4867),
    "bengaluru": (12.9716, 77.5946),
    "bangalore": (12.9716, 77.5946),
    "chennai": (13.0827, 80.2707),
    "delhi": (28.6139, 77.2090),
    "delhi ncr": (28.6139, 77.2090),
    "delhi-ncr": (28.6139, 77.2090),
    "mumbai": (19.0760, 72.8777),
    "kolkata": (22.5726, 88.3639)
}

def calculate_haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates great-circle geodesic distance in kilometers between two lat/lng coordinates."""
    R = 6371.0  # Earth radius in kilometers
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2.0) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2.0) ** 2)
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return round(R * c, 2)


class RecommendationEngine:
    """
    Explainable Multi-Criteria Recommendation Engine (Phase 5).
    Strictly deterministic and explainable without black-box ML models.
    """

    DEFAULT_WEIGHTS = {
        "clinical_match": 0.35,
        "cost_insurance": 0.25,
        "distance": 0.20,
        "quality_accreditation": 0.20
    }

    PRIORITY_WEIGHTS = {
        "balanced": {
            "clinical_match": 0.35,
            "cost_insurance": 0.25,
            "distance": 0.20,
            "quality_accreditation": 0.20
        },
        "cost_sensitive": {
            "clinical_match": 0.30,
            "cost_insurance": 0.40,
            "distance": 0.15,
            "quality_accreditation": 0.15
        },
        "quality_focused": {
            "clinical_match": 0.35,
            "cost_insurance": 0.15,
            "distance": 0.15,
            "quality_accreditation": 0.35
        },
        "proximity_focused": {
            "clinical_match": 0.30,
            "cost_insurance": 0.15,
            "distance": 0.40,
            "quality_accreditation": 0.15
        }
    }

    def __init__(self):
        self.weights = dict(self.DEFAULT_WEIGHTS)

    # -------------------------------------------------------------------------
    # STAGE 1: TRANSPARENT ELIGIBILITY FILTERING (HARD CONSTRAINTS)
    # -------------------------------------------------------------------------

    def filter_eligible_hospitals(
        self,
        hospitals: List[Dict[str, Any]],
        clinical_profile: Optional[Dict[str, Any]] = None,
        preferences: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Applies hard eligibility constraints:
        1. Specialty / Clinical Department presence.
        2. Critical facility requirements (Cath Lab for acute cardiac, ICU for severe cases).
        3. Hard budget ceiling filter (if strict_budget specified).
        Returns (eligible_hospitals, excluded_hospitals_with_reasons).
        """
        preferences = preferences or {}
        clinical_profile = clinical_profile or {}

        target_specialty = preferences.get("specialty")
        if not target_specialty and clinical_profile.get("conditions"):
            # Infer specialty from conditions if not specified
            c_str = " ".join(clinical_profile["conditions"]).lower()
            if any(k in c_str for k in ["coronary", "cad", "angina", "stent", "infarction", "cardio"]):
                target_specialty = "Cardiology"
            elif any(k in c_str for k in ["knee", "hip", "arthroplasty", "osteoarthritis", "joint"]):
                target_specialty = "Orthopedics"
            elif any(k in c_str for k in ["brain", "craniotomy", "tumor", "glioma", "neuro", "seizure", "stroke"]):
                target_specialty = "Neurology"
            elif any(k in c_str for k in ["cancer", "carcinoma", "chemo", "onco", "tumor", "metastasis"]):
                target_specialty = "Oncology"
            elif any(k in c_str for k in ["endoscopy", "ulcer", "cholecystectomy", "gastro"]):
                target_specialty = "Gastroenterology"
            elif any(k in c_str for k in ["kidney", "ckd", "dialysis", "nephro", "creatinine"]):
                target_specialty = "Nephrology"
            elif any(k in c_str for k in ["copd", "asthma", "hypoxemia", "pulmo", "respiratory"]):
                target_specialty = "Pulmonology"
            else:
                target_specialty = "General Medicine"

        target_specialty = (target_specialty or "Cardiology").strip().lower()

        # Check for critical clinical constraints
        needs_cath_lab = False
        needs_critical_icu = False
        all_conditions_text = " ".join(clinical_profile.get("conditions", []) + clinical_profile.get("procedures", [])).lower()
        test_results = clinical_profile.get("test_results", [])
        has_critical_test = any(str(t.get("status", "")).lower() == "critical" for t in test_results)

        if "cardio" in target_specialty or "stent" in all_conditions_text or "angioplasty" in all_conditions_text:
            needs_cath_lab = True
        if has_critical_test or "stroke" in all_conditions_text or "craniotomy" in all_conditions_text:
            needs_critical_icu = True

        max_budget = preferences.get("max_budget")
        strict_budget = preferences.get("strict_budget", False)
        required_facilities = [f.lower() for f in preferences.get("required_facilities", [])]

        eligible = []
        excluded = []

        for h in hospitals:
            h_name = h.get("name", "Hospital")
            h_specialties = [s.lower() for s in h.get("specialties", [])]
            h_facilities = [f.lower() for f in h.get("facilities", [])]
            cost_tier_num = float(h.get("estimated_cost_tier", 320000.0))

            exclusion_reasons = []

            # 1. Specialty Capability Check
            has_specialty = any(target_specialty in s or s in target_specialty for s in h_specialties)
            if not has_specialty and target_specialty != "general medicine":
                exclusion_reasons.append(f"Lacks accredited {target_specialty.capitalize()} department")

            # 2. Critical Care Capability Check
            if needs_cath_lab and not any("cath lab" in f for f in h_facilities):
                exclusion_reasons.append("Lacks 24x7 Cath Lab required for acute cardiac intervention")

            if needs_critical_icu and not any("icu" in f for f in h_facilities):
                exclusion_reasons.append("Lacks critical Intensive Care Unit (ICU)")

            # 3. Explicit Required Facilities Filter
            for rf in required_facilities:
                if not any(rf in f for f in h_facilities):
                    exclusion_reasons.append(f"Lacks user-requested facility: {rf.title()}")

            # 4. Hard Budget Constraint Check
            if max_budget is not None and cost_tier_num > max_budget:
                exclusion_reasons.append(f"Baseline cost (₹{cost_tier_num:,.0f}) exceeds selected budget ceiling (₹{max_budget:,.0f})")

            if exclusion_reasons:
                excluded.append({
                    "provider_type": "hospital",
                    "id": h.get("id", 0),
                    "name": h_name,
                    "status": "EXCLUDED",
                    "exclusion_reasons": exclusion_reasons,
                    "city": h.get("city", "")
                })
            else:
                eligible.append(h)

        return eligible, excluded

    def filter_eligible_doctors(
        self,
        doctors: List[Dict[str, Any]],
        clinical_profile: Optional[Dict[str, Any]] = None,
        preferences: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Filters doctors based on specialty match, subspecialty/expertise alignment,
        and minimum experience requirements.
        """
        preferences = preferences or {}
        target_specialty = (preferences.get("specialty") or "Cardiology").strip().lower()
        min_experience = preferences.get("min_doctor_experience")

        eligible = []
        excluded = []

        for d in doctors:
            doc_spec = d.get("specialty", "").lower()
            exp = d.get("experience_years", 10)
            doc_name = d.get("name", "Doctor")

            reasons = []
            if target_specialty not in doc_spec and not any(tok in doc_spec for tok in target_specialty.split()):
                reasons.append(f"Specialty ({d.get('specialty')}) does not match target ({target_specialty.title()})")

            if min_experience and exp < min_experience:
                reasons.append(f"Clinical experience ({exp} yrs) below requested threshold ({min_experience} yrs)")

            if reasons:
                excluded.append({
                    "provider_type": "doctor",
                    "id": d.get("id", 0),
                    "name": doc_name,
                    "status": "EXCLUDED",
                    "exclusion_reasons": reasons,
                    "specialty": d.get("specialty")
                })
            else:
                eligible.append(d)

        return eligible, excluded

    # -------------------------------------------------------------------------
    # STAGE 2: WEIGHTED MULTI-CRITERIA SCORING & PERSONALIZED RANKING
    # -------------------------------------------------------------------------

    def score_hospital(
        self,
        hospital: Dict[str, Any],
        required_specialty: str = "Cardiology",
        patient_city: str = "Hyderabad",
        patient_lat: Optional[float] = None,
        patient_lng: Optional[float] = None,
        max_budget: float = 500000.0,
        preferred_insurance: str = "Star Health",
        condition_entities: Optional[List[str]] = None,
        priority_mode: str = "balanced",
        treatment_capabilities_needed: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Scores a hospital across 4 transparent dimensions:
        1. Clinical Match (35% baseline)
        2. Cost & Insurance (25% baseline)
        3. Geographic Proximity (20% baseline)
        4. Quality & Accreditation (20% baseline)
        (Availability is removed as per clinical specification).
        """
        active_weights = self.PRIORITY_WEIGHTS.get(priority_mode.lower(), self.DEFAULT_WEIGHTS)

        # Coordinate resolution
        if patient_lat is None or patient_lng is None:
            resolved_coords = CITY_COORDINATES.get(patient_city.lower().strip(), (17.3850, 78.4867))
            p_lat, p_lng = resolved_coords
        else:
            p_lat, p_lng = patient_lat, patient_lng

        h_lat = hospital.get("lat", 17.3850)
        h_lng = hospital.get("lng", 78.4867)

        # 1. Clinical Specialty & Treatment Match (0 - 100)
        h_specialties = [s.lower() for s in hospital.get("specialties", [])]
        req_spec_lower = required_specialty.lower().strip()
        facilities = [f.lower() for f in hospital.get("facilities", [])]
        capabilities = [c.lower() for c in hospital.get("treatment_capabilities", [])]

        if req_spec_lower in h_specialties:
            specialty_score = 100.0
        elif any(req_spec_lower in s or s in req_spec_lower for s in h_specialties):
            specialty_score = 85.0
        else:
            specialty_score = 40.0

        # Clinical infrastructure enhancements
        clinical_infra_score = 70.0
        if "cardio" in req_spec_lower:
            if any("cath lab" in f for f in facilities): clinical_infra_score += 15.0
            if any("icu" in f for f in facilities): clinical_infra_score += 10.0
            if any("pci" in c for c in capabilities): clinical_infra_score += 5.0
        elif "oncol" in req_spec_lower:
            if any("pet-ct" in f or "bmt" in f for f in facilities): clinical_infra_score += 15.0
            if any("radiation" in c or "sbrt" in c or "chemo" in c for c in capabilities): clinical_infra_score += 15.0
        elif "ortho" in req_spec_lower:
            if any("arthroplasty" in f or "joint" in f for f in facilities): clinical_infra_score += 15.0
            if any("tka" in c or "replacement" in c for c in capabilities): clinical_infra_score += 15.0
        elif "neuro" in req_spec_lower:
            if any("neuro" in f for f in facilities): clinical_infra_score += 15.0
            if any("craniotomy" in c or "stroke" in c for c in capabilities): clinical_infra_score += 15.0
        else:
            if any("icu" in f for f in facilities): clinical_infra_score += 15.0
            if any("emergency" in f for f in facilities): clinical_infra_score += 15.0

        # Clinical entity matching from report/profile
        if condition_entities:
            ent_text = " ".join(condition_entities).lower()
            if any(k in ent_text for k in ["pci", "stent", "angioplasty"]) and any("cath lab" in f for f in facilities):
                clinical_infra_score += 5.0
            if any(k in ent_text for k in ["dialysis", "ckd"]) and any("dialysis" in f for f in facilities):
                clinical_infra_score += 5.0

        clinical_infra_score = min(clinical_infra_score, 100.0)
        clinical_score = (0.50 * specialty_score) + (0.50 * clinical_infra_score)

        # 2. Cost & Insurance Compatibility (0 - 100)
        ins_accepted = [i.lower() for i in hospital.get("insurance_accepted", [])]
        pref_ins_lower = preferred_insurance.lower().strip() if preferred_insurance else ""

        if pref_ins_lower and (pref_ins_lower in ins_accepted or any(pref_ins_lower in i for i in ins_accepted)):
            insurance_score = 100.0
            cashless_supported = True
        else:
            insurance_score = 50.0  # Out-of-network reimbursement
            cashless_supported = False

        cost_tier_num = float(hospital.get("estimated_cost_tier", 320000.0))
        if cost_tier_num <= max_budget:
            budget_score = 100.0
        else:
            overrun = cost_tier_num - max_budget
            budget_score = max(100.0 - ((overrun / 10000.0) * 3.5), 25.0)

        cost_score = (0.55 * insurance_score) + (0.45 * budget_score)

        # 3. Geographic Proximity via Haversine (0 - 100)
        calc_dist_km = calculate_haversine_distance(p_lat, p_lng, h_lat, h_lng)
        if calc_dist_km <= 15.0:
            dist_score = max(100.0 - (calc_dist_km * 0.8), 88.0)
        elif calc_dist_km <= 60.0:
            dist_score = max(88.0 - ((calc_dist_km - 15.0) * 0.3), 75.0)
        elif calc_dist_km <= 500.0:
            dist_score = max(75.0 - ((calc_dist_km - 60.0) * 0.06), 45.0)
        else:
            dist_score = max(45.0 - ((calc_dist_km - 500.0) * 0.02), 20.0)

        # 4. Quality & Accreditation Rating (0 - 100)
        base_rating = float(hospital.get("quality_rating", hospital.get("rating", 4.5)))
        quality_score = (base_rating / 5.0) * 90.0

        accred = str(hospital.get("accreditation", "")).upper()
        if "JCI" in accred:
            quality_score += 10.0
        elif "NABH" in accred:
            quality_score += 6.0

        icu_beds = int(hospital.get("icu_beds", 50))
        if icu_beds >= 80:
            quality_score += 4.0

        quality_score = min(quality_score, 100.0)

        # Final Weighted Multi-Criteria Total Score
        total_score = (
            active_weights["clinical_match"] * clinical_score +
            active_weights["cost_insurance"] * cost_score +
            active_weights["distance"] * dist_score +
            active_weights["quality_accreditation"] * quality_score
        )

        score_breakdown = {
            "clinical_match": round(active_weights["clinical_match"] * clinical_score, 2),
            "cost_insurance": round(active_weights["cost_insurance"] * cost_score, 2),
            "distance_proximity": round(active_weights["distance"] * dist_score, 2),
            "quality_accreditation": round(active_weights["quality_accreditation"] * quality_score, 2)
        }

        # Explainability reasons
        reasons = []
        if specialty_score >= 85.0:
            reasons.append(f"✓ Accredited department for {required_specialty} (Clinical Match: {clinical_score:.0f}/100)")

        if cashless_supported:
            reasons.append(f"✓ Direct cashless hospitalization with {preferred_insurance}")
        else:
            reasons.append(f"⚠ Non-empanelled for {preferred_insurance} (Reimbursement basis)")

        if calc_dist_km <= 25.0:
            reasons.append(f"✓ Intra-city proximity advantage: {calc_dist_km:.1f} km from {patient_city}")
        else:
            reasons.append(f"✈ Inter-city medical transit: {calc_dist_km:.1f} km from {patient_city}")

        if "JCI" in accred:
            reasons.append(f"✓ Gold-standard JCI & NABH International Accreditation (Rating: {base_rating:.1f}/5.0)")
        elif "NABH" in accred:
            reasons.append(f"✓ National NABH Healthcare Accreditation (Rating: {base_rating:.1f}/5.0)")

        if cost_tier_num <= max_budget:
            reasons.append(f"✓ Cost tier ({cost_tier_num:,.0f} INR) within your {max_budget:,.0f} INR budget")

        result = dict(hospital)
        result["distance_km"] = calc_dist_km
        result["recommendation_score"] = round(total_score, 1)
        result["score_breakdown"] = score_breakdown
        result["reasons"] = reasons
        result["shap_reasons"] = reasons
        return result

    def score_doctor(
        self,
        doctor: Dict[str, Any],
        required_specialty: str = "Cardiology",
        patient_city: Optional[str] = None,
        hospital_dict: Optional[Dict[str, Any]] = None,
        comorbidity_conditions: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Calculates personalized matching score for a doctor based on clinical specialty,
        sub-specialty expertise, clinical experience, and patient feedback rating.
        Restores original scoring weights:
          - Specialty/Clinical Match: 50% (0.50)
          - Clinical Experience: 25% (0.25)
          - Patient Feedback Rating: 25% (0.25)
        Integrates comorbidity relevance strictly within the 50% clinical-match mechanism.
        """
        doc_spec = doctor.get("specialty", "").lower()
        req_spec = required_specialty.lower().strip()
        doc_exp = doctor.get("experience_years", 10)
        doc_rating = doctor.get("rating", 4.5)
        raw_exp = doctor.get("expertise") or ""
        if isinstance(raw_exp, list):
            doc_expertise = " ".join(str(x) for x in raw_exp).lower()
            exp_display = ", ".join(str(x) for x in raw_exp)
        else:
            doc_expertise = str(raw_exp).lower()
            exp_display = str(raw_exp) if raw_exp else "Clinical Specialist"

        # Check sub-specialty alignment with patient comorbidities
        matched_comorbidities = []
        if comorbidity_conditions:
            for comorb in comorbidity_conditions:
                c_clean = comorb.strip().lower()
                if c_clean and c_clean != "none" and len(c_clean) >= 3:
                    if c_clean in doc_expertise or c_clean in doc_spec or any(tok in doc_expertise for tok in c_clean.split() if len(tok) > 3):
                        matched_comorbidities.append(comorb.strip())

        # 1. Clinical / Specialty Match (0 - 100) -> Strictly 50% weight
        # Primary specialty remains the mandatory driver
        if doc_spec == req_spec or req_spec in doc_spec or doc_spec in req_spec:
            if comorbidity_conditions is None:
                spec_match = 100.0
            else:
                # Comorbidity relevance boosts matching within the clinical match component
                spec_match = 100.0 if matched_comorbidities else 95.0
        elif any(tok in doc_spec for tok in req_spec.split()):
            # Broad / related specialty match
            spec_match = 85.0 if matched_comorbidities else 75.0
        else:
            spec_match = 50.0  # Original non-match score

        # 2. Experience Score (0 - 100) -> Strictly 25% weight (Original formula: min(doc_exp * 4.0, 100.0))
        exp_score = min(doc_exp * 4.0, 100.0)

        # 3. Satisfaction Rating (0 - 100) -> Strictly 25% weight (Original formula: (doc_rating / 5.0) * 100.0)
        rating_score = (doc_rating / 5.0) * 100.0

        # Final Score: Strictly (0.50 * spec_match) + (0.25 * exp_score) + (0.25 * rating_score)
        final_score = (0.50 * spec_match) + (0.25 * exp_score) + (0.25 * rating_score)

        doc_result = dict(doctor)
        doc_result["match_score"] = round(final_score, 1)
        doc_result["comorbidity_matches"] = len(matched_comorbidities)
        doc_result["scoring_weights"] = {
            "specialty_match": 0.50,
            "experience": 0.25,
            "rating": 0.25
        }
        doc_result["score_breakdown"] = {
            "specialty_match": round(0.50 * spec_match, 2),
            "experience": round(0.25 * exp_score, 2),
            "rating": round(0.25 * rating_score, 2)
        }

        reasons = [
            f"✓ {doc_exp} years clinical experience in {doctor.get('specialty')}",
            f"✓ Patient satisfaction rating: {doc_rating:.1f}/5.0",
            f"✓ Sub-specialty expertise: {exp_display}"
        ]
        for mc in matched_comorbidities:
            reasons.append(f"✓ Sub-specialty relevance to patient comorbidity: {mc}")

        if hospital_dict:
            doc_result["hospital_name"] = hospital_dict.get("name")
            doc_result["hospital_city"] = hospital_dict.get("city")
            reasons.append(f"✓ Practicing at {hospital_dict.get('name')}")

        doc_result["reasons"] = reasons
        return doc_result

    # -------------------------------------------------------------------------
    # EVIDENCE-GROUNDED TREATMENT PATHWAYS (PHASE 4 RAG INTEGRATION)
    # -------------------------------------------------------------------------

    def match_treatment_pathways(
        self,
        condition: str,
        specialty: str,
        report_entities: Optional[List[str]] = None,
        patient_allergies: Optional[List[str]] = None,
        patient_conditions: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Derives evidence-grounded clinical treatment pathways EXCLUSIVELY from the
        Phase 4 verified medical knowledge RAG layer.
        Incorporate patient profile comorbidities into evidence retrieval and
        cross-checks documented drug allergies to flag potential contraindications.
        NEVER prescribes, alters dosages, or independently changes medications.
        """
        query_terms = [condition, specialty, "treatment clinical pathway guidelines flight clearance"]
        if report_entities:
            query_terms.extend(report_entities[:2])
        if patient_conditions:
            for pc in patient_conditions[:2]:
                if pc.lower() not in condition.lower():
                    query_terms.append(pc)

        rag_query = " ".join(query_terms)
        retrieved_docs = rag_engine.retrieve_documents(rag_query, top_k=3, threshold=0.30)

        if not retrieved_docs:
            retrieved_docs = rag_engine.retrieve_documents(f"{specialty} clinical guidelines travel", top_k=2, threshold=0.25)

        pathways = []
        for i, doc in enumerate(retrieved_docs, 1):
            pathway_name = f"Evidence-Grounded Pathway: {doc['title']}"
            guideline_excerpt = doc.get("content", "")

            # Identify travel clearance statements from guideline content
            flight_guidance = "Refer to treating specialist for pre-flight clinical clearance."
            if "travel" in guideline_excerpt.lower() or "flight" in guideline_excerpt.lower() or "air" in guideline_excerpt.lower():
                flight_guidance = guideline_excerpt

            # Allergy Safety Check: Scan guideline text against documented patient allergies
            allergy_conflict = False
            allergy_warning = None
            if patient_allergies:
                check_corpus = f"{doc.get('title', '')} {guideline_excerpt}".lower()
                for allergy in patient_allergies:
                    a_clean = allergy.strip().lower()
                    if not a_clean or a_clean == "none":
                        continue
                    # Regex word boundary check for exact allergy agent match
                    pattern = r"\b" + re.escape(a_clean) + r"\b"
                    if re.search(pattern, check_corpus):
                        allergy_conflict = True
                        allergy_warning = (
                            f"⚠️ Potential Allergy Warning: Patient profile documents allergy to '{allergy.strip()}'. "
                            f"This clinical pathway guideline references '{allergy.strip()}'. Verify alternative "
                            f"treatment protocols with your attending physician prior to therapy."
                        )
                        break

            pathways.append({
                "pathway_name": pathway_name,
                "specialty": doc.get("specialty", doc.get("category", specialty)),
                "condition": doc.get("condition_covered", condition),
                "description": guideline_excerpt,
                "suitability": f"Verified guideline from {doc.get('organization', 'Clinical Society')} (Evidence: {doc.get('clinical_evidence_level', 'Consensus')}).",
                "estimated_duration_days": 3 if "pci" in guideline_excerpt.lower() else (5 if "knee" in guideline_excerpt.lower() else 4),
                "flight_clearance_guideline": flight_guidance,
                "grounding_sources": [
                    {
                        "organization": doc.get("organization", "Clinical Organization"),
                        "title": doc.get("title", ""),
                        "source_reference": doc.get("source_reference", ""),
                        "reference_url": doc.get("reference_url", "")
                    }
                ],
                "clinical_disclaimer": "Clinical decision support derived directly from published peer-reviewed medical guidelines. Must be verified with treating specialist.",
                "allergy_conflict_detected": allergy_conflict,
                "allergy_warning": allergy_warning
            })

        return pathways

    # -------------------------------------------------------------------------
    # UNIFIED PERSONALIZED DECISION SUPPORT API
    # -------------------------------------------------------------------------

    def get_personalized_recommendations(
        self,
        clinical_profile: Dict[str, Any],
        preferences: Optional[Dict[str, Any]] = None,
        all_hospitals: Optional[List[Dict[str, Any]]] = None,
        all_doctors: Optional[List[Dict[str, Any]]] = None,
        top_k_hospitals: int = 5,
        top_k_doctors: int = 5,
        top_k_pathways: int = 3,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Fuses Phase 3 Clinical Profile and explicit patient preferences through:
        1. Stage 1: Transparent Eligibility Filtering (hard constraints + audit reasons)
        2. Stage 2: Weighted Multi-Criteria Scoring & Personalized Ranking
        3. Phase 4 RAG Evidence-Grounded Treatment Pathways
        """
        from datasets.providers_data import HOSPITALS_DATA, DOCTORS_DATA

        hospitals_pool = all_hospitals if all_hospitals is not None else kwargs.get("hospitals", HOSPITALS_DATA)
        doctors_pool = all_doctors if all_doctors is not None else kwargs.get("doctors", DOCTORS_DATA)
        top_k_h = kwargs.get("top_hospitals", top_k_hospitals)
        top_k_d = kwargs.get("top_doctors", top_k_doctors)
        top_k_p = kwargs.get("top_pathways", top_k_pathways)
        preferences = preferences or {}

        # 1. Determine clinical target from profile
        conditions = clinical_profile.get("conditions", [])
        primary_condition = conditions[0] if conditions else "General Medical Evaluation"
        
        target_specialty = preferences.get("specialty")
        if not target_specialty:
            c_text = " ".join(conditions).lower()
            if any(k in c_text for k in ["coronary", "cad", "angina", "stent", "infarction", "cardio"]):
                target_specialty = "Cardiology"
            elif any(k in c_text for k in ["knee", "hip", "arthroplasty", "osteoarthritis", "joint"]):
                target_specialty = "Orthopedics"
            elif any(k in c_text for k in ["brain", "craniotomy", "tumor", "glioma", "neuro", "seizure", "stroke"]):
                target_specialty = "Neurology"
            elif any(k in c_text for k in ["cancer", "carcinoma", "chemo", "onco"]):
                target_specialty = "Oncology"
            elif any(k in c_text for k in ["endoscopy", "ulcer", "cholecystectomy", "gastro"]):
                target_specialty = "Gastroenterology"
            elif any(k in c_text for k in ["kidney", "ckd", "dialysis", "nephro"]):
                target_specialty = "Nephrology"
            elif any(k in c_text for k in ["copd", "asthma", "hypoxemia", "pulmo"]):
                target_specialty = "Pulmonology"
            else:
                target_specialty = "General Medicine"

        patient_city = preferences.get("preferred_city") or clinical_profile.get("demographics", {}).get("current_city") or "Hyderabad"
        max_budget = float(preferences.get("max_budget") or 500000.0)
        preferred_insurance = preferences.get("preferred_insurance") or "Star Health"
        priority_mode = preferences.get("priority_factor", "balanced").lower()

        # 2. Stage 1: Transparent Eligibility Filtering
        pref_dict = dict(preferences)
        pref_dict["specialty"] = target_specialty
        eligible_hospitals, excluded_hospitals = self.filter_eligible_hospitals(
            hospitals_pool,
            clinical_profile=clinical_profile,
            preferences=pref_dict
        )

        eligible_doctors, excluded_doctors = self.filter_eligible_doctors(
            doctors_pool,
            clinical_profile=clinical_profile,
            preferences=pref_dict
        )

        # 3. Stage 2: Weighted Multi-Criteria Scoring on Eligible Providers
        scored_hospitals = []
        for h in eligible_hospitals:
            scored = self.score_hospital(
                h,
                required_specialty=target_specialty,
                patient_city=patient_city,
                max_budget=max_budget,
                preferred_insurance=preferred_insurance,
                condition_entities=conditions,
                priority_mode=priority_mode
            )
            scored_hospitals.append(scored)

        scored_hospitals.sort(key=lambda x: x["recommendation_score"], reverse=True)

        # Hospital map for doctor affiliation context
        hosp_map = {h["id"]: h for h in hospitals_pool}
        scored_doctors = []
        for d in eligible_doctors:
            h_info = hosp_map.get(d.get("hospital_id"))
            scored_doc = self.score_doctor(
                d,
                required_specialty=target_specialty,
                patient_city=patient_city,
                hospital_dict=h_info
            )
            scored_doctors.append(scored_doc)

        scored_doctors.sort(key=lambda x: x["match_score"], reverse=True)

        # 4. Evidence-Grounded Treatment Pathways via Phase 4 RAG
        pathways = self.match_treatment_pathways(
            condition=primary_condition,
            specialty=target_specialty,
            report_entities=conditions
        )

        # 5. Combined Eligibility Audit
        eligibility_audit = []
        for eh in scored_hospitals[:top_k_hospitals]:
            eligibility_audit.append({
                "provider_type": "hospital",
                "id": eh.get("id", 0),
                "name": eh.get("name", ""),
                "status": "ELIGIBLE",
                "exclusion_reason": None
            })
        for xh in excluded_hospitals[:5]:
            eligibility_audit.append({
                "provider_type": "hospital",
                "id": xh.get("id", 0),
                "name": xh.get("name", ""),
                "status": "EXCLUDED",
                "exclusion_reason": "; ".join(xh.get("exclusion_reasons", []))
            })

        active_weights = self.PRIORITY_WEIGHTS.get(priority_mode, self.DEFAULT_WEIGHTS)

        return {
            "recommended_hospitals": scored_hospitals[:top_k_hospitals],
            "recommended_doctors": scored_doctors[:top_k_doctors],
            "treatment_pathways": pathways,
            "clinical_profile_applied": {
                "conditions": conditions,
                "target_specialty": target_specialty,
                "primary_condition": primary_condition,
                "demographics": clinical_profile.get("demographics", {})
            },
            "preferences_applied": {
                "preferred_city": patient_city,
                "max_budget": max_budget,
                "preferred_insurance": preferred_insurance,
                "priority_mode": priority_mode
            },
            "active_weights": active_weights,
            "priority_mode": priority_mode,
            "eligibility_audit": eligibility_audit,
            "disclaimer": (
                "Algorithmic decision support recommendations are strictly informational and intended "
                "for clinical decision support. Final provider selection and medical procedures must be "
                "determined in direct consultation with a qualified medical specialist."
            )
        }


recommendation_engine = RecommendationEngine()
