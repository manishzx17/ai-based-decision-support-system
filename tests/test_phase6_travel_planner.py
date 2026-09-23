"""
Tests for Phase 6: Personalized Medical Travel Planning & A* Graph Navigation.

Covers:
1. Spatial Graph & Genuine A* Navigation Engine:
   - Node and edge graph structure.
   - Valid continuous path construction along real edges.
   - Turn-by-turn waypoints and distance/time estimates.
   - Admissibility of Haversine heuristic (h <= d*).
   - Path cost optimality verified against uniform-cost search (Dijkstra baseline).
2. Content-Based Accommodation Recommendation Engine:
   - Proximity decay, budget tier alignment, and medical accessibility matching.
   - Transparent, explainable clinical match rationales.
3. Personalized Itinerary Generator & Clinical Safety Governance:
   - Integration of authenticated patient profile, allergies, and medical report findings.
   - Grounding through Phase 3 RAG for pre/post-treatment guidance.
   - Requirement for clinician confirmation and inclusion of verified citations.
   - Prohibition against independent prescriptions, medication stops, fasting rules, or flight clearances.
   - Prominence of mandatory medical safety disclaimer.
4. End-to-End API Integration via TestClient:
   - /travel/plan (POST & GET)
   - /travel/navigate (GET)
   - /travel/accommodations (GET)
"""

import sys
import os
import pytest

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(os.path.dirname(CURRENT_DIR), "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from fastapi.testclient import TestClient
from main import app
from ai.astar_navigation import astar_navigator, AStarNavigation
from ai.accommodation_recommender import accommodation_recommender, ContentBasedAccommodationRecommender
from ai.itinerary_generator import itinerary_generator, PersonalizedItineraryGenerator
from datasets.seed_data import SEED_ACCOMMODATIONS


client = TestClient(app)


# =====================================================================
# 1. A* SPATIAL GRAPH ROUTING & OPTIMALITY TESTS
# =====================================================================

def test_spatial_graph_structure_and_connectivity():
    """Verifies that the spatial graph has proper nodes, types, and bidirectional connectivity."""
    summary = astar_navigator.get_graph_summary()
    assert summary["total_nodes"] >= 15
    assert summary["total_directed_edges"] >= 30

    node_types = set(summary["node_types"])
    assert "airport" in node_types
    assert "hospital" in node_types
    assert "accommodation" in node_types
    assert "pharmacy" in node_types
    assert "junction" in node_types


def test_astar_route_validity_and_edge_continuity():
    """
    Tests that A* generates a continuous, physically connected path of adjacent edges
    from Rajiv Gandhi Airport to Apollo Hospitals Jubilee Hills.
    """
    origin = "Airport_HYD"
    destination = "Apollo_Jubilee"

    result = astar_navigator.astar_search(origin, destination, metric="distance")
    assert result is not None
    path_nodes, path_edges, total_cost, nodes_explored = result

    # 1. Start and end nodes match
    assert path_nodes[0] == origin
    assert path_nodes[-1] == destination
    assert len(path_nodes) >= 4  # Must traverse intermediate transit junctions
    assert len(path_edges) == len(path_nodes) - 1

    # 2. Strict edge continuity: each edge connects path_nodes[i] -> path_nodes[i+1]
    for i, edge in enumerate(path_edges):
        assert edge.u == path_nodes[i]
        assert edge.v == path_nodes[i + 1]
        assert edge.distance_km > 0
        assert edge.speed_kmh > 0
        assert len(edge.road_name) > 0

    # 3. Sum of edge distances equals reported total cost
    computed_sum = sum(e.distance_km for e in path_edges)
    assert abs(computed_sum - total_cost) < 1e-4

    # 4. Telemetry verifies nodes were explored efficiently
    assert nodes_explored > 0


def test_astar_heuristic_admissibility():
    """
    Verifies that the Haversine heuristic is strictly admissible (h(u, goal) <= d*(u, goal))
    for all nodes in the graph with respect to a target hospital.
    """
    goal = "Apollo_Jubilee"

    for node_id, node in astar_navigator.nodes.items():
        # True shortest path distance found by uniform-cost search (Dijkstra)
        dijkstra_res = astar_navigator.dijkstra_search(node_id, goal, metric="distance")
        if dijkstra_res is not None:
            _, true_distance, _ = dijkstra_res
            h_val = astar_navigator._heuristic(node_id, goal, metric="distance")

            # Mathematical Admissibility Condition: h(u) <= d*(u)
            assert h_val <= true_distance + 1e-4, (
                f"Heuristic violated admissibility for node {node_id}: h={h_val}, true_dist={true_distance}"
            )


def test_astar_path_cost_optimality_vs_dijkstra():
    """
    Validates that A* search finds the mathematically optimal path identical in cost
    to Dijkstra's uniform-cost search across diverse origin-destination pairs.
    """
    test_pairs = [
        ("Airport_HYD", "Apollo_Jubilee"),
        ("Railway_Secunderabad", "Care_Banjara"),
        ("Taj_Jubilee", "Yashoda_Somajiguda"),
        ("Treebo_Jubilee", "Apollo_Pharmacy_24x7"),
        ("Airport_HYD", "AIG_Gachibowli")
    ]

    for origin, destination in test_pairs:
        # 1. Run A* search
        astar_res = astar_navigator.astar_search(origin, destination, metric="distance")
        assert astar_res is not None
        _, _, astar_cost, astar_explored = astar_res

        # 2. Run baseline Dijkstra search
        dijkstra_res = astar_navigator.dijkstra_search(origin, destination, metric="distance")
        assert dijkstra_res is not None
        _, dijkstra_cost, dijkstra_explored = dijkstra_res

        # 3. Verify exact cost optimality
        assert abs(astar_cost - dijkstra_cost) < 1e-4, (
            f"A* cost ({astar_cost}) differed from Dijkstra baseline ({dijkstra_cost}) for {origin} -> {destination}"
        )

        # 4. Verify A* explores fewer or equal nodes than Dijkstra due to heuristic pruning
        assert astar_explored <= dijkstra_explored


def test_astar_turn_by_turn_plan_route_interface():
    """Verifies high-level plan_route() returns formatted turn-by-turn guidance and coordinates."""
    route = astar_navigator.plan_route("Airport", "Hospital")

    assert route["distance_km"] >= 20.0
    assert route["estimated_travel_time_minutes"] >= 25
    assert len(route["turn_by_turn_waypoints"]) >= 4
    assert "algorithm_telemetry" in route
    assert route["algorithm_telemetry"]["is_optimal"] is True

    # Check waypoints describe actual roads in network
    joined_waypoints = " ".join(route["turn_by_turn_waypoints"])
    assert "Expressway" in joined_waypoints or "Road" in joined_waypoints


# =====================================================================
# 2. CONTENT-BASED ACCOMMODATION RECOMMENDATION TESTS
# =====================================================================

def test_accommodation_recommender_proximity_ranking():
    """
    Tests that accommodation closest to the target hospital receives a higher proximity score.
    """
    recs = accommodation_recommender.recommend(
        accommodations=SEED_ACCOMMODATIONS,
        hospital_id=1,  # Apollo Jubilee Hills
        budget_tier="Standard",
        top_n=5
    )

    assert len(recs) > 0
    top_stay = recs[0]
    # Top match for Apollo should be in Jubilee Hills near Apollo
    assert top_stay["hospital_id"] == 1
    assert top_stay["distance_km"] <= 1.5
    assert top_stay["match_score"] > 0.6
    assert len(top_stay["reasons"]) >= 2


def test_accommodation_recommender_budget_tier_sensitivity():
    """
    Tests that Budget tier prioritizes low-cost options, while Deluxe tier prioritizes premium suites.
    """
    # 1. Query for Budget tier (< 2200/night)
    budget_recs = accommodation_recommender.recommend(
        accommodations=SEED_ACCOMMODATIONS,
        hospital_id=1,
        budget_tier="Budget",
        top_n=3
    )
    # 2. Query for Deluxe tier (> 4000/night)
    deluxe_recs = accommodation_recommender.recommend(
        accommodations=SEED_ACCOMMODATIONS,
        hospital_id=1,
        budget_tier="Deluxe",
        top_n=3
    )

    # Budget top match should have lower price than Deluxe top match
    assert budget_recs[0]["price_per_night"] < deluxe_recs[0]["price_per_night"]
    assert budget_recs[0]["price_per_night"] <= 2500.0
    assert deluxe_recs[0]["price_per_night"] >= 3500.0


def test_accommodation_recommender_accessibility_matching():
    """
    Tests that accommodations with Wheelchair Accessible and Elevator receive higher facility scores.
    """
    recs_with_accessibility = accommodation_recommender.recommend(
        accommodations=SEED_ACCOMMODATIONS,
        hospital_id=1,
        required_facilities=["Wheelchair Accessible", "Elevator", "24/7 Nurse on Call"],
        top_n=5
    )

    top_stay = recs_with_accessibility[0]
    assert "score_breakdown" in top_stay
    assert top_stay["score_breakdown"]["facility_score"] >= 0.6
    assert any("Wheelchair" in f for f in top_stay["matched_facilities"])


# =====================================================================
# 3. PERSONALIZED ITINERARY GENERATOR & CLINICAL SAFETY GOVERNANCE TESTS
# =====================================================================

def test_itinerary_generator_personalization_and_rag_grounding():
    """
    Tests personalized itinerary generation:
    - Integrates patient allergies and chronic conditions
    - Retrieves verified pre/post-treatment guidance via Phase 3 RAG
    - Requires clinician confirmation on all considerations
    - Refuses to issue independent clearance decisions
    - Embeds mandatory clinical safety disclaimer
    """
    patient_profile = {
        "full_name": "Rajesh Verma",
        "age": 48,
        "allergies": ["Penicillin", "Sulfa Drugs"],
        "chronic_conditions": ["Hypertension", "Type 2 Diabetes"]
    }

    medical_report = {
        "findings_summary": "Severe 90% stenosis of Proximal LAD and 85% mid RCA. Stable angina CCS Class II.",
        "recommended_treatment": "Percutaneous Coronary Intervention (PCI) with Drug-Eluting Stents"
    }

    hospital = {
        "id": 1,
        "name": "Apollo Hospitals Jubilee Hills",
        "city": "Hyderabad",
        "address": "Road No 72, Jubilee Hills",
        "estimated_cost_tier": 220000.0
    }

    doctor = {
        "id": 1,
        "name": "Dr. K. Srinivas Rao",
        "specialty": "Cardiology"
    }

    plan = itinerary_generator.generate_plan(
        patient_profile=patient_profile,
        medical_report=medical_report,
        hospital=hospital,
        doctor=doctor,
        preferred_start_date="2026-09-20",
        duration_days=5,
        current_location="Bengaluru",
        budget_tier="Standard",
        available_accommodations=SEED_ACCOMMODATIONS
    )

    # 1. Structure & Patient Context
    assert plan["destination_city"] == "Hyderabad"
    assert plan["hospital_name"] == "Apollo Hospitals Jubilee Hills"
    assert len(plan["itinerary"]) == 5
    assert plan["patient_context"]["allergies"] == ["Penicillin", "Sulfa Drugs"]

    # 2. Allergy Alert integration in itinerary
    consultation_day = plan["itinerary"][1]  # Day 2
    assert "ALLERGY ALERT" in consultation_day["details"]
    assert "Penicillin" in consultation_day["details"]

    # 3. Cost Breakdown
    cost = plan["cost_breakdown"]
    assert cost["estimated_procedure_cost"] >= 180000.0
    assert cost["accommodation_cost"] > 0
    assert cost["local_transportation_cost"] > 0
    assert cost["total"] == cost["estimated_procedure_cost"] + cost["accommodation_cost"] + cost["local_transportation_cost"]

    # 4. CRITICAL CLINICAL GOVERNANCE: Pre- & Post-Treatment Considerations
    pre_items = plan["pre_treatment_considerations"]
    post_items = plan["post_treatment_considerations"]

    assert len(pre_items) > 0
    assert len(post_items) > 0

    # Verify that every guidance item requires clinician confirmation and carries citations
    for item in pre_items + post_items:
        assert item["clinician_confirmation_required"] is True
        assert len(item["clinician_action"]) > 0
        assert "source" in item
        assert len(item["source"]["organization"]) > 0
        assert len(item["source"]["title"]) > 0

        # Safety Check: Must NOT issue unilateral medical clearance or independent medication orders
        text_lower = item["consideration_text"].lower()
        assert "you are cleared to fly" not in text_lower
        assert "stop taking" not in text_lower
        assert "we prescribe" not in text_lower

    # 5. Mandatory Clinical Disclaimer is present and prominent
    assert "CRITICAL CLINICAL NOTICE" in plan["clinical_disclaimer"]
    assert "treating clinician" in plan["clinical_disclaimer"].lower()


# =====================================================================
# 4. END-TO-END FASTAPI INTEGRATION TESTS
# =====================================================================

def test_api_post_and_get_travel_plan():
    """Tests POST /travel/plan and GET /travel/plan endpoints with full schema validation."""
    payload = {
        "medical_condition": "Cardiology / Coronary Stenting",
        "hospital_id": 1,
        "doctor_id": 1,
        "preferred_travel_date": "2026-09-25",
        "current_location": "Bengaluru",
        "budget_range": "Standard",
        "duration_days": 5
    }

    # Authenticate as user 1
    login_res = client.post("/api/auth/login", json={"username": "demo_cardio", "password": "DemoPassword@123"})
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create Travel Plan
    response = client.post("/api/travel/plan?user_id=1", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()

    assert data["destination_city"] == "Hyderabad"
    assert data["hospital_name"] == "Apollo Hospitals Jubilee Hills"
    assert len(data["itinerary"]) == 5
    assert data["total_estimated_cost"] > 0
    assert data["cost_breakdown"] is not None
    assert data["clinical_disclaimer"] is not None
    assert len(data["pre_treatment_considerations"]) > 0

    # 2. Retrieve Saved Plan
    get_res = client.get("/api/travel/plan?user_id=1", headers=headers)
    assert get_res.status_code == 200
    saved = get_res.json()
    assert saved["id"] == data["id"]
    assert saved["hospital_name"] == data["hospital_name"]
    assert len(saved["itinerary"]) == 5


def test_api_astar_navigation_route():
    """Tests GET /api/travel/navigate returns valid A* spatial route and telemetry."""
    res = client.get("/api/travel/navigate?origin=Airport&destination=Hospital&metric=distance")
    assert res.status_code == 200
    data = res.json()

    assert data["distance_km"] > 0
    assert data["estimated_travel_time_minutes"] > 0
    assert len(data["turn_by_turn_waypoints"]) >= 3
    assert "algorithm_telemetry" in data
    assert data["algorithm_telemetry"]["is_optimal"] is True
    assert "path_nodes" in data
    assert len(data["path_nodes"]) >= 2


def test_api_accommodations_ranking():
    """Tests GET /api/travel/accommodations returns content-based ranked accommodations."""
    res = client.get("/api/travel/accommodations?hospital_id=1&budget_tier=Standard")
    assert res.status_code == 200
    stays = res.json()

    assert isinstance(stays, list)
    assert len(stays) > 0

    top_stay = stays[0]
    assert "match_score" in top_stay
    assert "match_percentage" in top_stay
    assert "reasons" in top_stay
    assert len(top_stay["reasons"]) > 0
