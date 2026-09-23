"""
Content-Based Accommodation Recommendation Engine for Medical Travel.

Recommends patient-centric recovery stays and accommodations by evaluating:
1. Hospital Proximity (exponential distance decay from target clinical facility).
2. Budget Alignment (matching user budget tier or max cost per night).
3. Medical Accessibility & Specialized Facility Needs (wheelchair access, elevator,
   patient kitchenette for therapeutic diets, 24/7 nurse on call, sterilized linen).
4. Facility Quality & Guest Patient Rating.

Generates transparent, explainable clinical match rationales for each recommended stay.
"""

import math
from typing import List, Dict, Any, Optional, Set, Tuple


class ContentBasedAccommodationRecommender:
    """
    Ranks accommodations using multi-attribute content matching against patient requirements.
    """

    DEFAULT_WEIGHTS = {
        "proximity": 0.35,
        "budget": 0.25,
        "facilities": 0.25,
        "rating": 0.15
    }

    BUDGET_TIERS = {
        "budget": (0.0, 2200.0),
        "standard": (2000.0, 4200.0),
        "deluxe": (4000.0, 10000.0),
        "luxury": (4000.0, 15000.0)
    }

    def __init__(self, weights: Optional[Dict[str, float]] = None):
        self.weights = weights or self.DEFAULT_WEIGHTS
        # Normalize weights to sum to 1.0
        total_w = sum(self.weights.values())
        self.weights = {k: v / total_w for k, v in self.weights.items()}

    def _score_proximity(self, distance_km: float) -> float:
        """
        Exponential distance decay:
        - 0.3 km -> ~0.86
        - 0.8 km -> ~0.67
        - 1.5 km -> ~0.47
        - 3.0 km -> ~0.22
        """
        clamped_dist = max(0.1, distance_km)
        decay_factor = 0.5
        return math.exp(-decay_factor * clamped_dist)

    def _score_budget(
        self,
        price_per_night: float,
        budget_tier: str = "Standard",
        budget_max_per_night: Optional[float] = None
    ) -> float:
        """Scores alignment with user budget."""
        tier_lower = budget_tier.lower().strip()

        if budget_max_per_night is not None and budget_max_per_night > 0:
            if price_per_night <= budget_max_per_night:
                # Closer to budget without exceeding is rewarded
                return 1.0 - 0.2 * ((budget_max_per_night - price_per_night) / budget_max_per_night)
            else:
                overshoot = (price_per_night - budget_max_per_night) / budget_max_per_night
                return max(0.05, 1.0 - overshoot * 1.5)

        low, high = self.BUDGET_TIERS.get(tier_lower, self.BUDGET_TIERS["standard"])
        if low <= price_per_night <= high:
            return 1.0
        elif price_per_night < low:
            # Below tier (cheaper than expected): still good match with mild discount
            return 0.85
        else:
            # Over budget tier: penalize based on overshoot percentage
            excess_ratio = (price_per_night - high) / high
            return max(0.1, 1.0 - excess_ratio * 1.2)

    def _score_facilities(
        self,
        available_facilities: List[str],
        required_facilities: Optional[List[str]] = None,
        patient_needs: Optional[List[str]] = None
    ) -> Tuple[float, List[str]]:
        """
        Computes facility overlap and accessibility compatibility.
        """
        avail_lower = {f.lower().strip() for f in available_facilities}
        all_required = set()

        if required_facilities:
            all_required.update(f.lower().strip() for f in required_facilities)

        # Derive required facilities from patient clinical conditions if provided
        if patient_needs:
            for need in patient_needs:
                n_low = need.lower()
                if "wheelchair" in n_low or "mobility" in n_low or "ortho" in n_low:
                    all_required.add("wheelchair accessible")
                if "diet" in n_low or "diabetes" in n_low or "cardio" in n_low or "renal" in n_low:
                    all_required.add("patient kitchenette")
                if "elderly" in n_low or "post-op" in n_low or "icu" in n_low:
                    all_required.add("24/7 nurse on call")
                if "stairs" in n_low or "lift" in n_low:
                    all_required.add("elevator")

        matched_facilities = []
        if not all_required:
            # If no specific requirements, evaluate standard high-value medical amenities
            high_value = ["wheelchair accessible", "elevator", "patient kitchenette", "24/7 nurse on call", "free hospital shuttle"]
            matches = [f for f in available_facilities if f.lower().strip() in high_value]
            score = min(1.0, len(matches) / 3.0)
            return (round(score, 3), matches)

        matched_count = 0
        for req in all_required:
            matched = False
            for avail in available_facilities:
                avail_clean = avail.lower().strip()
                if req in avail_clean or avail_clean in req:
                    matched_count += 1
                    matched_facilities.append(avail)
                    matched = True
                    break

        score = matched_count / max(1, len(all_required))
        return (min(1.0, round(score, 3)), matched_facilities)

    def _score_rating(self, rating: float) -> float:
        """Normalizes 5-star rating to [0.0, 1.0]."""
        return min(1.0, max(0.0, rating / 5.0))

    def _generate_reasons(
        self,
        acc_dict: Dict[str, Any],
        proximity_score: float,
        budget_score: float,
        facility_score: float,
        matched_facilities: List[str],
        budget_tier: str
    ) -> List[str]:
        """Generates transparent, explainable recommendations."""
        reasons = []

        # Proximity reason
        dist = acc_dict.get("distance_km", 1.0)
        if dist <= 0.5:
            reasons.append(f"Immediate proximity: only {dist:.2f} km from hospital, ideal for minimal post-procedure transit.")
        elif dist <= 1.2:
            reasons.append(f"Convenient location: {dist:.1f} km from hospital, facilitating quick check-ups and consultations.")
        else:
            reasons.append(f"Located {dist:.1f} km from hospital with accessible transit corridor.")

        # Budget reason
        price = acc_dict.get("price_per_night", 2500.0)
        if budget_score >= 0.95:
            reasons.append(f"Perfect match for '{budget_tier}' budget preference at ₹{price:,.0f} per night.")
        elif budget_score >= 0.8:
            reasons.append(f"Cost-effective medical stay at ₹{price:,.0f} per night.")
        else:
            reasons.append(f"Premium facility offering at ₹{price:,.0f} per night.")

        # Facilities reason
        if matched_facilities:
            unique_matched = list(dict.fromkeys(matched_facilities))
            sample = ", ".join(unique_matched[:3])
            reasons.append(f"Provides critical medical recovery amenities: {sample}.")
        else:
            facilities = acc_dict.get("facilities", [])
            if facilities:
                sample = ", ".join(facilities[:2])
                reasons.append(f"Equipped with key convenience amenities: {sample}.")

        # Rating reason
        rating = acc_dict.get("rating", 4.5)
        if rating >= 4.7:
            reasons.append(f"Exceptional patient satisfaction rating of {rating:.1f}/5.0.")

        return reasons

    def recommend(
        self,
        accommodations: List[Dict[str, Any]],
        hospital_id: Optional[int] = None,
        budget_tier: str = "Standard",
        budget_max_per_night: Optional[float] = None,
        required_facilities: Optional[List[str]] = None,
        patient_needs: Optional[List[str]] = None,
        top_n: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Ranks accommodations based on content similarity and returns top recommendations.
        """
        if not accommodations:
            return []

        scored_list = []

        for acc in accommodations:
            # Distance: if matching hospital_id, prioritize; else apply small penalty for other hospital hubs
            dist_km = float(acc.get("distance_km", 1.5))
            acc_h_id = acc.get("hospital_id")
            if hospital_id is not None and acc_h_id is not None and acc_h_id != hospital_id:
                # Not near the target hospital hub
                dist_km += 5.0

            prox_score = self._score_proximity(dist_km)
            price = float(acc.get("price_per_night", 2500.0))
            budg_score = self._score_budget(price, budget_tier, budget_max_per_night)

            avail_fac = acc.get("facilities", [])
            fac_score, matched_fac = self._score_facilities(avail_fac, required_facilities, patient_needs)

            rating = float(acc.get("rating", 4.5))
            rate_score = self._score_rating(rating)

            total_score = (
                self.weights["proximity"] * prox_score +
                self.weights["budget"] * budg_score +
                self.weights["facilities"] * fac_score +
                self.weights["rating"] * rate_score
            )

            match_pct = round(min(1.0, max(0.0, total_score)) * 100.0, 1)

            reasons = self._generate_reasons(
                acc, prox_score, budg_score, fac_score, matched_fac, budget_tier
            )

            scored_item = dict(acc)
            scored_item.update({
                "match_score": round(total_score, 4),
                "match_percentage": match_pct,
                "reasons": reasons,
                "score_breakdown": {
                    "proximity_score": round(prox_score, 3),
                    "budget_score": round(budg_score, 3),
                    "facility_score": round(fac_score, 3),
                    "rating_score": round(rate_score, 3)
                },
                "matched_facilities": matched_fac
            })
            scored_list.append(scored_item)

        # Sort descending by match_score
        scored_list.sort(key=lambda x: x["match_score"], reverse=True)

        for rank, item in enumerate(scored_list[:top_n], 1):
            item["rank"] = rank

        return scored_list[:top_n]


accommodation_recommender = ContentBasedAccommodationRecommender()
