import os
import sys

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

import pytest
from fastapi.testclient import TestClient
from main import app
from routes.travel import geocode_address, haversine_distance_km

client = TestClient(app)

def test_haversine_distance_km():
    # Distance between Bangalore (12.9716, 77.5946) and Mysore (12.2958, 76.6394) is ~128-132 km
    dist = haversine_distance_km(12.9716, 77.5946, 12.2958, 76.6394)
    assert 120.0 <= dist <= 140.0

def test_open_medical_route_car_mode():
    payload = {
        "origin": "MG Road, Bangalore",
        "destination": "Apollo Hospital, Bannerghatta Road, Bangalore",
        "travel_mode": "car"
    }
    response = client.post("/api/travel/route", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "origin" in data
    assert "destination" in data
    assert data["origin"]["lat"] > 0
    assert data["destination"]["lat"] > 0
    assert data["distance_km"] > 0.0
    assert data["duration_minutes"] > 0.0
    assert len(data["route_geometry"]) >= 2
    assert "OpenStreetMap" in data["osm_attribution"]
    assert "openstreetmap.org/directions" in data["open_map_url"]
    # Confirm NO Google Maps or paid API URL
    assert "google.com/maps" not in data["open_map_url"]

def test_open_medical_route_modes():
    modes = ["two_wheeler", "walking", "bicycle", "transit"]
    for m in modes:
        payload = {
            "origin": "Cubbon Park, Bangalore",
            "destination": "Fortis Hospital, Cunningham Road, Bangalore",
            "travel_mode": m
        }
        response = client.post("/api/travel/route", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["travel_mode"] == m
        assert data["distance_km"] > 0.0
        assert data["duration_minutes"] > 0.0
        assert "openstreetmap.org" in data["open_map_url"]

def test_open_medical_route_invalid_location():
    # Empty origin
    res1 = client.post("/api/travel/route", json={"origin": "", "destination": "Bangalore", "travel_mode": "car"})
    assert res1.status_code == 400

    # Non-existent gibberish location
    res2 = client.post("/api/travel/route", json={"origin": "xyznonexistentlocation987234123xyz", "destination": "Bangalore", "travel_mode": "car"})
    assert res2.status_code == 404
    assert "Could not locate" in res2.json()["detail"]

def test_nearby_hotels_search():
    res = client.get("/api/travel/nearby?location=Apollo+Hospital+Bangalore&category=hotel&limit=3")
    assert res.status_code == 200
    data = res.json()
    assert data["category"] == "hotel"
    assert data["total_found"] > 0
    assert len(data["items"]) > 0
    item = data["items"][0]
    assert "name" in item
    assert "address" in item
    assert "openstreetmap.org" in item["open_map_url"]
    assert "google.com" not in item["open_map_url"]

def test_nearby_pharmacies_search():
    res = client.get("/api/travel/nearby?location=Apollo+Hospital+Bangalore&category=pharmacy&limit=3")
    assert res.status_code == 200
    data = res.json()
    assert data["category"] == "pharmacy"
    assert data["total_found"] > 0
    item = data["items"][0]
    assert "name" in item
    assert "address" in item
    assert "openstreetmap.org" in item["open_map_url"]

def test_nearby_invalid_query():
    res = client.get("/api/travel/nearby?location=%20%20&category=hotel")
    assert res.status_code == 400

def test_emergency_services_by_hospital_id():
    res = client.get("/api/travel/emergency?hospital_id=1")
    assert res.status_code == 200
    data = res.json()
    assert data["national_emergency_number"] == "112"
    assert data["ambulance_number"] in ["108", "102 / 108"]
    assert len(data["contacts"]) >= 4
    assert data["hospital_emergency_dept"] is not None
    assert data["hospital_emergency_dept"]["emergency_24x7"] is True
    assert data["hospital_emergency_dept"]["icu_beds"] > 0

def test_emergency_services_by_city():
    cities = ["Bangalore", "Hyderabad", "Mumbai", "Delhi"]
    for city in cities:
        res = client.get(f"/api/travel/emergency?city={city}")
        assert res.status_code == 200
        data = res.json()
        assert data["national_emergency_number"] == "112"
        assert len(data["contacts"]) >= 4

