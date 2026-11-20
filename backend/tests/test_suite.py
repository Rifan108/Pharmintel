import sys
import os
import pytest
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_root_status():
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.json()["status"] == "Operational"

def test_auth_login():
    resp = client.post("/api/auth/login", json={
        "email": "patient@example.com",
        "password": "Customer@Pass2026"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["user"]["role"] == "customer"

def test_search_medicines():
    resp = client.get("/api/medicines?q=metformin")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] > 0
    assert any("Metformin" in m["generic_name"] for m in data["items"])

def test_autocomplete():
    resp = client.get("/api/medicines/autocomplete?prefix=asp")
    assert resp.status_code == 200
    results = resp.json()
    assert len(results) > 0
    assert any("Aspirin" in r["generic_name"] for r in results)

def test_clinical_ddi_contraindicated():
    # Warfarin (ID 9) + Aspirin (ID 8) -> Contraindicated in Layer 1
    resp = client.post("/api/interactions/check", json={
        "medicine_ids": [8, 9],
        "enable_ml_prediction": True
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["summary"]["highest_severity"] == "Contraindicated"
    assert data["summary"]["has_risk"] == True
    assert len(data["interactions"]) >= 1
    assert data["interactions"][0]["layer_detected"] == "LAYER_1_CLINICAL_RULE"

def test_ml_metrics_endpoint():
    resp = client.get("/api/ml/metrics")
    assert resp.status_code == 200
    data = resp.json()
    assert data["model_name"] == "PHARMINTEL-HYBRIDGNN"
    assert "performance_summary" in data
    assert "ablation_study" in data
    assert "model_comparison" in data
    assert data["performance_summary"]["accuracy"] > 0.50

def test_assistant_emergency_guardrail():
    resp = client.post("/api/assistant/chat", json={
        "session_id": "test_emergency",
        "message": "I am experiencing acute chest pain radiating to my arm and cannot breathe"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_emergency"] == True
    assert data["guardrail_flag"] == "EMERGENCY"
    assert "112" in data["response"]

def test_assistant_prescribe_guardrail():
    resp = client.post("/api/assistant/chat", json={
        "session_id": "test_prescribe",
        "message": "Can you prescribe me a 500mg antibiotic tablet?"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["guardrail_flag"] == "PRESCRIBE_BLOCKED"

def test_pharmacy_finder():
    resp = client.get("/api/pharmacies?lat=12.9279&lng=77.6771")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 3
    assert data[0]["distance_km"] is not None

def test_multilingual_assistant_kannada():
    resp = client.post("/api/assistant/chat", json={
        "session_id": "test_kn_session",
        "message": "Metformin side effects and kidney cautions",
        "language": "kn"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["language"] == "kn"
    assert "ಔಷಧೀಯ" in data["response"]

def test_multilingual_assistant_hindi_emergency():
    resp = client.post("/api/assistant/chat", json={
        "session_id": "test_hi_emer",
        "message": "मुझे सीने में बहुत तेज दर्द हो रहा है",
        "language": "hi"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_emergency"] == True
    assert data["guardrail_flag"] == "EMERGENCY"
    assert "आपातकालीन" in data["response"]

def test_multilingual_assistant_tamil_guardrail():
    resp = client.post("/api/assistant/chat", json={
        "session_id": "test_ta_guard",
        "message": "எனக்கு என்ன நோய் என்று சொல் (diagnose me)",
        "language": "ta"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["guardrail_flag"] == "DIAGNOSE_BLOCKED"
    assert "பாதுகாப்பு" in data["response"]

def test_qr_samples_endpoint():
    resp = client.get("/api/qr/samples")
    assert resp.status_code == 200
    samples = resp.json()
    assert len(samples) >= 3
    categories = [s["category"] for s in samples]
    assert "AUTHENTIC" in categories
    assert "RECALLED" in categories
    assert "UNVERIFIED" in categories

def test_qr_verify_authentic_batch():
    resp = client.post("/api/qr/verify", json={
        "raw_qr_content": "BT-101-1",
        "source_type": "camera_scan"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_verified_authentic"] == True
    assert data["authoritative_source_connected"] == True
    assert "CDSCO" in data["authenticity_badge"]
    assert data["medicine_name"] == "Glycomet 500"
    assert data["batch_number"] == "BT-101-1"
    assert data["safety_information"]["approved_indications"] != ""

def test_qr_verify_unregistered_third_party():
    resp = client.post("/api/qr/verify", json={
        "raw_qr_content": "UNKNOWN-BARCODE-999-FAKE",
        "source_type": "camera_scan"
    })
    assert resp.status_code == 200
    data = resp.json()
    # Strict regulatory requirement:
    # "Only claim authenticity verification when connected to an authoritative verification source."
    assert data["is_verified_authentic"] == False
    assert data["authoritative_source_connected"] == False
    assert "Not Verified" in data["authenticity_badge"]
    assert "Only claim authenticity verification" in data["authenticity_statement"]

def test_qr_generate_batch_label():
    resp = client.get("/api/qr/generate-batch/1")
    assert resp.status_code == 200
    data = resp.json()
    assert data["batch_id"] == 1
    assert "data:image/png;base64," in data["qr_data_url"]
    assert data["batch_number"] == "BT-101-1"

# ==============================================================================
# PATIENT-SPECIFIC MULTI-DRUG SAFETY INTELLIGENCE TESTS
# ==============================================================================

def test_patient_safety_red_contraindication_and_ddi():
    # Patient with Heart Disease & Type 2 Diabetes checking Ibuprofen
    payload = {
        "proposed_medicine": {
            "medicine_name": "Brufen 400",
            "generic_name": "Ibuprofen",
            "strength": "400mg"
        },
        "health_profile": {
            "medical_conditions": ["Heart disease", "Diabetes Type 2", "High blood pressure"],
            "allergies": [],
            "age": 60,
            "kidney_function": "Normal"
        },
        "existing_medicines": [
            {
                "medicine_name": "Glycomet 500",
                "generic_name": "Metformin",
                "strength": "500mg",
                "dosage": "1 tablet",
                "frequency": "Twice daily"
            },
            {
                "medicine_name": "Telma 40",
                "generic_name": "Telmisartan",
                "strength": "40mg",
                "dosage": "1 tablet",
                "frequency": "Once daily"
            }
        ],
        "enable_ml_prediction": True
    }
    resp = client.post("/api/interactions/patient-safety/check", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["overall_status"] == "RED"
    assert data["findings_count"]["serious_red"] >= 1
    assert "Heart disease" in data["personalized_guidance"]["what_this_means_for_you"]
    assert len(data["personalized_guidance"]["questions_for_doctor"]) >= 2

def test_patient_safety_duplicate_medicine():
    # Patient taking Glycomet (Metformin) proposes Cetapin (Metformin) -> Accidental double dose!
    payload = {
        "proposed_medicine": {
            "medicine_name": "Cetapin 500",
            "generic_name": "Metformin",
            "active_ingredients": "Metformin Hydrochloride",
            "strength": "500mg"
        },
        "health_profile": {
            "medical_conditions": ["Diabetes Type 2"],
            "allergies": []
        },
        "existing_medicines": [
            {
                "medicine_name": "Glycomet 500",
                "generic_name": "Metformin",
                "active_ingredients": "Metformin Hydrochloride",
                "strength": "500mg"
            }
        ]
    }
    resp = client.post("/api/interactions/patient-safety/check", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["overall_status"] == "RED"
    duplicate_findings = [f for f in data["findings"] if f["finding_type"] == "DUPLICATE_MEDICINE"]
    assert len(duplicate_findings) >= 1
    assert "DUPLICATE INGREDIENT" in duplicate_findings[0]["plain_language_explanation"]

def test_patient_safety_allergy_conflict():
    # Patient with Penicillin allergy proposes Amoxicillin
    payload = {
        "proposed_medicine": {
            "medicine_name": "Mox 500",
            "generic_name": "Amoxicillin",
            "active_ingredients": "Amoxicillin Trihydrate",
            "strength": "500mg"
        },
        "health_profile": {
            "medical_conditions": ["Asthma"],
            "allergies": ["Penicillin / Beta-lactams"]
        },
        "existing_medicines": []
    }
    resp = client.post("/api/interactions/patient-safety/check", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["overall_status"] == "RED"
    allergy_findings = [f for f in data["findings"] if f["finding_type"] == "DRUG_TO_ALLERGY"]
    assert len(allergy_findings) >= 1
    assert "Penicillin" in allergy_findings[0]["plain_language_explanation"]

def test_patient_safety_green_scenario():
    # Patient with High blood pressure taking Amlodipine proposes Paracetamol (safe)
    payload = {
        "proposed_medicine": {
            "medicine_name": "Dolo 650",
            "generic_name": "Paracetamol",
            "active_ingredients": "Paracetamol",
            "strength": "650mg"
        },
        "health_profile": {
            "medical_conditions": ["High blood pressure"],
            "allergies": []
        },
        "existing_medicines": [
            {
                "medicine_name": "Amlong 5",
                "generic_name": "Amlodipine",
                "strength": "5mg"
            }
        ]
    }
    resp = client.post("/api/interactions/patient-safety/check", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["overall_status"] == "GREEN"
    assert "No Known Interaction" in data["overall_status_label"]
    assert "does not guarantee" in data["personalized_guidance"]["what_this_means_for_you"]

def test_patient_safety_pdf_download():
    # Generate compatibility report then download PDF
    payload = {
        "proposed_medicine": {
            "medicine_name": "Telma 40",
            "generic_name": "Telmisartan",
            "strength": "40mg"
        },
        "health_profile": {
            "medical_conditions": ["High blood pressure"],
            "allergies": []
        },
        "existing_medicines": [
            {
                "medicine_name": "Amlong 5",
                "generic_name": "Amlodipine",
                "strength": "5mg"
            }
        ]
    }
    resp1 = client.post("/api/interactions/patient-safety/check", json=payload)
    assert resp1.status_code == 200
    report_data = resp1.json()

    resp2 = client.post("/api/interactions/patient-safety/pdf", json=report_data)
    assert resp2.status_code == 200
    assert resp2.headers["Content-Type"] == "application/pdf"
    assert resp2.content.startswith(b"%PDF-")

def test_multi_medicine_compatibility_losartan_amlodipine():
    payload = {
        "medicines": [
            {"medicine_name": "Losartan 50mg"},
            {"medicine_name": "Amlodipine 5mg"}
        ],
        "health_profile": {
            "medical_conditions": ["High blood pressure"],
            "allergies": []
        },
        "language": "en"
    }
    resp = client.post("/api/interactions/multi-check", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_medicines_analyzed"] == 2
    assert data["overall_status"] == "RED"
    assert len(data["interaction_table"]) >= 1
    assert any(
        any("Amlodipine" in med for med in row["medicines_involved"]) and
        any("Losartan" in med for med in row["medicines_involved"])
        for row in data["interaction_table"]
    )

def test_multi_medicine_triple_whammy_syndrome():
    payload = {
        "medicines": [
            {"medicine_name": "Losartan 50mg"},
            {"medicine_name": "Furosemide 40mg"},
            {"medicine_name": "Ibuprofen 400mg"}
        ],
        "health_profile": {
            "medical_conditions": ["Hypertension"],
            "allergies": []
        },
        "language": "en"
    }
    resp = client.post("/api/interactions/multi-check", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_medicines_analyzed"] == 3
    assert data["overall_status"] == "RED"
    assert any("Triple Whammy" in row["interaction_title"] for row in data["interaction_table"])

def test_multi_medicine_multilingual_kannada_and_hindi():
    # Test Kannada
    payload_kn = {
        "medicines": [
            {"medicine_name": "Losartan 50mg"},
            {"medicine_name": "Amlodipine 5mg"}
        ],
        "language": "kn"
    }
    resp_kn = client.post("/api/interactions/multi-check", json=payload_kn)
    assert resp_kn.status_code == 200
    data_kn = resp_kn.json()
    assert data_kn["language"] == "kn"
    assert "ಔಷಧ" in data_kn["what_does_this_mean"]

    # Test Hindi
    payload_hi = {
        "medicines": [
            {"medicine_name": "Losartan 50mg"},
            {"medicine_name": "Amlodipine 5mg"}
        ],
        "language": "hi"
    }
    resp_hi = client.post("/api/interactions/multi-check", json=payload_hi)
    assert resp_hi.status_code == 200
    data_hi = resp_hi.json()
    assert data_hi["language"] == "hi"
    assert "दवा" in data_hi["what_does_this_mean"]

def test_nearby_pharmacies_discovery():
    # Test GPS / distance based pharmacy search
    resp = client.get("/api/pharmacies/nearby?lat=12.9279&lng=77.6771&radius_km=10")
    assert resp.status_code == 200
    data = resp.json()
    assert "pharmacies" in data
    assert data["total_found"] >= 1
    first_pharm = data["pharmacies"][0]
    assert "name" in first_pharm
    assert "distance_km" in first_pharm
    assert "operating_hours" in first_pharm
    assert "is_open_now" in first_pharm
    assert "available_services" in first_pharm
    assert isinstance(first_pharm["available_services"], list)

def test_nearby_pharmacies_with_medicine_stock():
    # Test connected inventory search for Metformin
    resp = client.get("/api/pharmacies/nearby?lat=12.9279&lng=77.6771&medicine_name=Metformin&radius_km=15")
    assert resp.status_code == 200
    data = resp.json()
    assert data["target_medicine"] is not None
    assert "Metformin" in data["target_medicine"]["generic"] or "Glycomet" in data["target_medicine"]["name"]
    # Check that network pharmacies report verified inventory
    network_pharms = [p for p in data["pharmacies"] if p["is_network_pharmacy"]]
    assert len(network_pharms) >= 1
    assert network_pharms[0]["medicine_stock"] is not None
    assert "In Stock" in network_pharms[0]["medicine_stock_status"]
    assert network_pharms[0]["medicine_price"] is not None

def test_pharmacies_geocoding_endpoints():
    # Test forward geocode
    geo_resp = client.get("/api/pharmacies/geocode?q=Bengaluru")
    if geo_resp.status_code == 200:
        geo_data = geo_resp.json()
        assert "latitude" in geo_data
        assert "longitude" in geo_data

    # Test reverse geocode
    rev_resp = client.get("/api/pharmacies/reverse-geocode?lat=12.9279&lng=77.6771")
    assert rev_resp.status_code == 200
    rev_data = rev_resp.json()
    assert "locality" in rev_data

def test_assistant_pharmacy_intent():
    # Test voice/assistant inquiry about nearby 24-hour pharmacies
    resp = client.post("/api/assistant/chat", json={
        "session_id": "test-assistant-pharmacy-session",
        "message": "Find nearby pharmacies or 24-hour medical shops",
        "language": "en"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["category"] == "PHARMACY_LOCATOR"
    assert "Nearby Medical Shops" in data["response"]
    assert "Apollo Care" in data["response"]

def test_multi_medicine_single_safe_medicine():
    resp = client.post("/api/interactions/multi-check", json={
        "medicines": [{"medicine_name": "Paracetamol 650mg"}],
        "health_profile": {
            "medical_conditions": ["High blood pressure"],
            "allergies": []
        },
        "language": "en"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_medicines_analyzed"] == 1
    assert data["overall_status"] == "GREEN"
    assert "Compatible" in data["summary_headline"]
    assert len(data["interaction_table"]) == 0

def test_multi_medicine_single_disease_contraindication():
    resp = client.post("/api/interactions/multi-check", json={
        "medicines": [{"medicine_name": "Propranolol 40mg"}],
        "health_profile": {
            "medical_conditions": ["Asthma"],
            "allergies": []
        },
        "language": "en"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_medicines_analyzed"] == 1
    assert data["overall_status"] == "RED"
    assert len(data["interaction_table"]) >= 1
    assert "Contraindication" in data["interaction_table"][0]["interaction_title"]

def test_multi_medicine_empty_input():
    resp = client.post("/api/interactions/multi-check", json={
        "medicines": [],
        "health_profile": {"medical_conditions": [], "allergies": []},
        "language": "en"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_medicines_analyzed"] == 0
    assert data["overall_status"] == "GREY"
    assert "Please Enter at Least One Medicine" in data["summary_headline"]

def test_multi_medicine_unidentified_drug():
    resp = client.post("/api/interactions/multi-check", json={
        "medicines": [{"medicine_name": "InvalidXYZPharma999"}],
        "health_profile": {"medical_conditions": [], "allergies": []},
        "language": "en"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_medicines_analyzed"] == 1
    assert data["overall_status"] == "GREY"
    assert "InvalidXYZPharma999" in data["unidentified_medicines"]
    assert len(data["missing_information"]) >= 1

def test_multi_medicine_five_regimen_check():
    resp = client.post("/api/interactions/multi-check", json={
        "medicines": [
            {"medicine_name": "Metformin 500mg"},
            {"medicine_name": "Atorvastatin 10mg"},
            {"medicine_name": "Amlodipine 5mg"},
            {"medicine_name": "Losartan 50mg"},
            {"medicine_name": "Omeprazole 20mg"}
        ],
        "health_profile": {
            "medical_conditions": ["Type 2 Diabetes", "High blood pressure"],
            "allergies": []
        },
        "language": "en"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_medicines_analyzed"] == 5
    assert data["overall_status"] in ["RED", "YELLOW"]
    assert len(data["interaction_table"]) >= 1

def test_multi_medicine_pdf_download():
    multi_resp = client.post("/api/interactions/multi-check", json={
        "medicines": [
            {"medicine_name": "Losartan 50mg"},
            {"medicine_name": "Amlodipine 5mg"}
        ],
        "language": "en"
    })
    assert multi_resp.status_code == 200
    report_data = multi_resp.json()

    pdf_resp = client.post("/api/interactions/patient-safety/pdf", json=report_data)
    assert pdf_resp.status_code == 200
    assert pdf_resp.headers["Content-Type"] == "application/pdf"
    assert pdf_resp.content.startswith(b"%PDF-")
