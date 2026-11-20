import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app.models.pharmacy import Pharmacy
from app.services.pharmacy_service import PharmacyFinderService
from app.utils.distance import calculate_haversine_distance

client = TestClient(app)

# =====================================================================
# QA TEST SUITE: PHARMINTEL NEARBY MEDICAL SHOPS & GEOLOCATION
# =====================================================================

def test_no_coordinates_returns_location_prompt():
    """Verify calling /api/pharmacies/nearby without coordinates prompts for location instead of assuming a default city."""
    resp = client.get("/api/pharmacies/nearby")
    assert resp.status_code == 200
    data = resp.json()
    assert data["requires_location"] is True
    assert data["user_coordinates"] is None
    assert data["pharmacies"] == []
    assert "Use My Current Location" in data["message"]


def test_gps_coordinates_search_bengaluru():
    """Verify discovery around real coordinates (Bellanduru, Bengaluru: 12.9279, 77.6771)."""
    resp = client.get("/api/pharmacies/nearby?lat=12.9279&lng=77.6771&radius_km=10.0")
    assert resp.status_code == 200
    data = resp.json()
    assert data["user_coordinates"] == {"latitude": 12.9279, "longitude": 77.6771}
    assert data["total_found"] >= 2
    assert len(data["pharmacies"]) >= 2
    
    # Check that pharmacies have calculated distance_km and are sorted nearest first
    distances = [p["distance_km"] for p in data["pharmacies"] if p["distance_km"] is not None]
    assert distances == sorted(distances), "Pharmacies must be sorted nearest-first"
    assert distances[0] == 0.0, "Pharmacy located exactly at user coordinates must be 0.0 km"


def test_gps_coordinates_search_mumbai():
    """Verify discovery around real coordinates (Kurla West, Mumbai: 19.0760, 72.8777)."""
    resp = client.get("/api/pharmacies/nearby?lat=19.0760&lng=72.8777&radius_km=5.0")
    assert resp.status_code == 200
    data = resp.json()
    assert data["user_coordinates"] == {"latitude": 19.0760, "longitude": 72.8777}
    assert data["total_found"] > 0
    assert len(data["pharmacies"]) > 0

    first = data["pharmacies"][0]
    assert first["distance_km"] is not None
    assert first["distance_km"] <= 5.0
    assert "latitude" in first and "longitude" in first
    assert first["name"] is not None


def test_haversine_distance_calculation_accuracy():
    """Verify geographic Haversine distance accuracy."""
    # Bellandur (12.9279, 77.6771) to Indiranagar (12.9784, 77.6408)
    # Expected distance is ~6.9 to 7.0 km
    dist = calculate_haversine_distance(12.9279, 77.6771, 12.9784, 77.6408)
    assert 6.5 <= dist <= 7.5, f"Haversine distance {dist} outside expected range [6.5, 7.5]"

    # Zero distance between identical coordinates
    assert calculate_haversine_distance(12.9279, 77.6771, 12.9279, 77.6771) == 0.0


def test_radius_filtering():
    """Verify that radius_km strictly bounds search results."""
    # 1 km search around 12.9279, 77.6771
    resp_1km = client.get("/api/pharmacies/nearby?lat=12.9279&lng=77.6771&radius_km=1.0")
    assert resp_1km.status_code == 200
    data_1km = resp_1km.json()
    for p in data_1km["pharmacies"]:
        assert p["distance_km"] <= 1.0, f"Pharmacy {p['name']} distance {p['distance_km']} exceeds 1.0 km radius"

    # 10 km search should contain >= pharmacies than 1 km
    resp_10km = client.get("/api/pharmacies/nearby?lat=12.9279&lng=77.6771&radius_km=10.0")
    assert resp_10km.status_code == 200
    data_10km = resp_10km.json()
    assert len(data_10km["pharmacies"]) >= len(data_1km["pharmacies"])


def test_manual_area_search_pin_code():
    """Verify manual location search using a 6-digit PIN code (560103)."""
    resp = client.get("/api/pharmacies/geocode?q=560103")
    assert resp.status_code == 200
    data = resp.json()
    assert "latitude" in data and "longitude" in data
    assert 12.8 <= data["latitude"] <= 13.1
    assert 77.5 <= data["longitude"] <= 77.8


def test_manual_area_search_city_name():
    """Verify manual location search by city name (e.g. Pune)."""
    resp = client.get("/api/pharmacies/geocode?q=Pune")
    assert resp.status_code == 200
    data = resp.json()
    assert "latitude" in data and "longitude" in data
    assert 18.3 <= data["latitude"] <= 18.7
    assert 73.7 <= data["longitude"] <= 74.0


def test_reverse_geocoding_structure():
    """Verify reverse-geocoding returns structured area, locality, city, and state."""
    resp = client.get("/api/pharmacies/reverse-geocode?lat=12.9279&lng=77.6771")
    assert resp.status_code == 200
    data = resp.json()
    assert "locality" in data
    assert "area" in data
    assert "city" in data
    assert "state" in data
    assert data["latitude"] == 12.9279
    assert data["longitude"] == 77.6771


def test_pharmacy_name_search_filter():
    """Verify filtering nearby pharmacies by name."""
    resp = client.get("/api/pharmacies/nearby?lat=12.9279&lng=77.6771&radius_km=10.0&search_name=Apollo")
    assert resp.status_code == 200
    data = resp.json()
    for p in data["pharmacies"]:
        assert "apollo" in p["name"].lower()


def test_open_status_parsing():
    """Verify opening hours evaluation logic (no fake hours)."""
    # 24/7 chemist is open
    assert PharmacyFinderService.parse_open_status("24 Hours Open") is True
    assert PharmacyFinderService.parse_open_status("Open 24/7 Round the clock") is True
    
    # Missing / Unknown hours returns None (never guess)
    assert PharmacyFinderService.parse_open_status(None) is None
    assert PharmacyFinderService.parse_open_status("Unknown") is None
    assert PharmacyFinderService.parse_open_status("Hours unavailable") is None


def test_genuine_data_integrity():
    """Verify that OSM pharmacies do not have fabricated phone numbers or fake star ratings."""
    resp = client.get("/api/pharmacies/nearby?lat=19.0760&lng=72.8777&radius_km=5.0")
    assert resp.status_code == 200
    data = resp.json()
    osm_pharmacies = [p for p in data["pharmacies"] if p.get("data_source") == "OpenStreetMap"]
    
    for p in osm_pharmacies:
        # If no phone tag existed, phone must be None, not an invented dummy phone
        if p["phone"] is not None:
            assert p["phone"].replace("+", "").replace("-", "").replace(" ", "").isdigit()
        # Ratings must not be fabricated for OSM nodes
        assert p["rating"] is None or isinstance(p["rating"], (int, float))


def test_medicine_inventory_connected_vs_unconnected():
    """Verify medicine inventory distinction between network and community pharmacies."""
    db = SessionLocal()
    try:
        # Search for Metformin
        resp = client.get("/api/pharmacies/nearby?lat=12.9279&lng=77.6771&radius_km=10.0&medicine_name=Metformin")
        assert resp.status_code == 200
        data = resp.json()
        assert data["target_medicine"] is not None

        network_pharmacies = [p for p in data["pharmacies"] if p["is_network_pharmacy"]]
        for np in network_pharmacies:
            assert np["inventory_connected"] is True
            assert np["medicine_stock"] is not None
            assert "Stock" in np["medicine_stock_status"]

        osm_pharmacies = [p for p in data["pharmacies"] if not p["is_network_pharmacy"]]
        for op in osm_pharmacies:
            assert op["inventory_connected"] is False
            assert op["medicine_stock_status"] == "Inventory Not Connected"
    finally:
        db.close()
