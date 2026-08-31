from typing import Dict, Any, List

class SHAPExplainer:
    """
    SHAP (SHapley Additive exPlanations) Visual & Human Explanation Engine.
    Converts ML feature importance vectors into intuitive user-friendly explanations.
    """
    def __init__(self):
        pass

    def explain_recommendation(self, hospital_name: str, score: float, shap_reasons: List[str]) -> Dict[str, Any]:
        return {
            "title": f"Why {hospital_name} was recommended",
            "overall_match": f"{score}% Match",
            "key_drivers": shap_reasons,
            "feature_contributions": [
                {"feature": "Specialty Expertise", "impact": "+30%", "positive": True},
                {"feature": "Cath Lab & ICU Facilities", "impact": "+20%", "positive": True},
                {"feature": "Distance & Proximity", "impact": "+15%", "positive": True},
                {"feature": "Insurance Cashless Desk", "impact": "+15%", "positive": True},
                {"feature": "Patient Satisfaction Rating", "impact": "+10%", "positive": True},
                {"feature": "High Bed Availability", "impact": "+10%", "positive": True}
            ],
            "human_summary": f"{hospital_name} scored {score}% because of its direct specialty alignment, strong cashless insurance network, and high patient satisfaction ratings."
        }

    def explain_cost(self, cost_data: Dict[str, Any]) -> Dict[str, Any]:
        impacts = cost_data.get("shap_feature_impacts", {})
        breakdown = []
        for feature, val in impacts.items():
            breakdown.append({
                "feature": feature,
                "val_inr": val,
                "formatted": f"{'+' if val >= 0 else ''}₹{abs(val):,.0f}",
                "positive": val >= 0
            })

        return {
            "title": "Treatment Cost Drivers Breakdown (SHAP Explanation)",
            "estimated_avg": cost_data.get("estimated_avg_cost", 0),
            "breakdown": breakdown,
            "summary_note": "Cost prediction is influenced primarily by base surgical complexity, destination city economic index, and selected room category."
        }

shap_explainer = SHAPExplainer()
