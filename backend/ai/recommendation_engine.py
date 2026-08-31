from typing import List, Dict, Any

class RecommendationEngine:
    """
    Weighted Multi-Criteria Decision Recommendation Engine for Hospitals & Doctors.
    Implements:
    Score = 0.30 * SpecialtyMatch + 0.20 * TreatmentMatch + 0.15 * DistanceScore + 0.15 * CostScore + 0.10 * RatingScore + 0.10 * AvailabilityScore
    """
    def __init__(self):
        self.weights = {
            "specialty_match": 0.30,
            "treatment_match": 0.20,
            "distance": 0.15,
            "cost": 0.15,
            "rating": 0.10,
            "availability": 0.10
        }

    def score_hospital(
        self,
        hospital: Dict[str, Any],
        required_specialty: str,
        patient_city: str = "Hyderabad",
        max_budget: float = 500000.0,
        preferred_insurance: str = "Star Health"
    ) -> Dict[str, Any]:
        
        # 1. Specialty Match Score (0 - 100)
        h_specialties = [s.lower() for s in hospital.get("specialties", [])]
        if required_specialty.lower() in h_specialties:
            specialty_score = 100.0
        elif any(required_specialty.lower() in s for s in h_specialties):
            specialty_score = 80.0
        else:
            specialty_score = 40.0

        # 2. Treatment Match / Facilities Score (0 - 100)
        facilities = [f.lower() for f in hospital.get("facilities", [])]
        treatment_score = 70.0
        if "24x7 icu" in facilities or "cath lab" in facilities or "robotic surgery" in facilities:
            treatment_score += 20.0
        if preferred_insurance and preferred_insurance in hospital.get("insurance_accepted", []):
            treatment_score += 10.0

        # 3. Distance Score (0 - 100)
        # Same city = higher score
        dist_km = hospital.get("distance_km", 10.0)
        if hospital.get("city", "").lower() == patient_city.lower():
            dist_score = max(100.0 - (dist_km * 4.0), 50.0)
        else:
            dist_score = max(80.0 - (dist_km * 2.0), 30.0)

        # 4. Cost Score (0 - 100)
        cost_tier = hospital.get("estimated_cost_tier", 250000.0)
        if cost_tier <= max_budget:
            cost_score = 95.0
        else:
            cost_score = max(90.0 - ((cost_tier - max_budget) / 10000.0), 40.0)

        # 5. Rating Score (0 - 100)
        rating = hospital.get("rating", 4.5)
        rating_score = (rating / 5.0) * 100.0

        # 6. Availability Score (0 - 100)
        avail = hospital.get("availability_status", "High").lower()
        avail_score = 95.0 if avail == "high" else (75.0 if avail == "medium" else 50.0)

        # Final Weighted Formula Calculation
        total_score = (
            self.weights["specialty_match"] * specialty_score +
            self.weights["treatment_match"] * treatment_score +
            self.weights["distance"] * dist_score +
            self.weights["cost"] * cost_score +
            self.weights["rating"] * rating_score +
            self.weights["availability"] * avail_score
        )

        # Key Drivers for SHAP / Human Explanation
        reasons = []
        if specialty_score >= 80:
            reasons.append(f"✓ Direct specialty match for {required_specialty}")
        if preferred_insurance in hospital.get("insurance_accepted", []):
            reasons.append(f"✓ Direct cashless support for {preferred_insurance}")
        if rating >= 4.7:
            reasons.append(f"✓ Top patient satisfaction rating ({rating}/5.0)")
        if hospital.get("city", "").lower() == patient_city.lower():
            reasons.append(f"✓ Proximity advantage ({dist_km:.1f} km in {patient_city})")
        if avail == "high":
            reasons.append("✓ High doctor & bed availability")

        result = dict(hospital)
        result["recommendation_score"] = round(total_score, 1)
        result["shap_reasons"] = reasons
        return result

    def score_doctor(self, doctor: Dict[str, Any], required_specialty: str) -> Dict[str, Any]:
        spec_match = 100.0 if doctor["specialty"].lower() == required_specialty.lower() else 50.0
        exp_score = min(doctor["experience_years"] * 4.0, 100.0)
        rating_score = (doctor["rating"] / 5.0) * 100.0
        
        final_score = (0.50 * spec_match) + (0.25 * exp_score) + (0.25 * rating_score)
        
        doc_result = dict(doctor)
        doc_result["match_score"] = round(final_score, 1)
        doc_result["reasons"] = [
            f"✓ {doctor['experience_years']} years expert clinical experience",
            f"✓ High patient rating of {doctor['rating']}/5.0",
            f"✓ Specializes in {doctor['specialty']}"
        ]
        return doc_result

recommendation_engine = RecommendationEngine()
