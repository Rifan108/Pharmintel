"""
Test script for verifying advanced clinical intelligence scenarios in PatientSafetyIntelligenceService.
"""

import sys
sys.path.insert(0, 'backend')

from app.database import SessionLocal
from app.schemas.interaction import MultiMedicineCheckRequest, MultiMedicineItem, HealthProfileInput
from app.services.patient_safety_service import PatientSafetyIntelligenceService

def run_tests():
    db = SessionLocal()
    print("=== TEST 1: Duplicate Active Ingredient (Combiflam + Dolo 650) ===")
    req1 = MultiMedicineCheckRequest(
        medicines=[
            MultiMedicineItem(medicine_name="Combiflam"),
            MultiMedicineItem(medicine_name="Dolo 650")
        ]
    )
    rep1 = PatientSafetyIntelligenceService.analyze_multiple_medicines_compatibility(db, req1)
    print("Status:", rep1.overall_status, "Duplicates:", rep1.duplicate_medicines_count)
    for row in rep1.interaction_table:
        print("  - [", row.severity, "]", row.interaction_title)

    print("\n=== TEST 2: Triple Whammy (Losartan + Furosemide + Ibuprofen) ===")
    req2 = MultiMedicineCheckRequest(
        medicines=[
            MultiMedicineItem(medicine_name="Losartan 50mg"),
            MultiMedicineItem(medicine_name="Lasix 40mg"),
            MultiMedicineItem(medicine_name="Brufen 400mg")
        ]
    )
    rep2 = PatientSafetyIntelligenceService.analyze_multiple_medicines_compatibility(db, req2)
    print("Status:", rep2.overall_status, "Interactions:", len(rep2.interaction_table))
    for row in rep2.interaction_table:
        print("  - [", row.severity, "]", row.interaction_title)

    print("\n=== TEST 3: Serotonin Syndrome (Sertima + Tramazac) ===")
    req3 = MultiMedicineCheckRequest(
        medicines=[
            MultiMedicineItem(medicine_name="Sertima 50"),
            MultiMedicineItem(medicine_name="Tramazac 50")
        ]
    )
    rep3 = PatientSafetyIntelligenceService.analyze_multiple_medicines_compatibility(db, req3)
    print("Status:", rep3.overall_status, "Interactions:", len(rep3.interaction_table))
    for row in rep3.interaction_table:
        print("  - [", row.severity, "]", row.interaction_title)

    print("\n=== TEST 4: Therapeutic Duplication (Pantocid + Omez) ===")
    req4 = MultiMedicineCheckRequest(
        medicines=[
            MultiMedicineItem(medicine_name="Pan 40"),
            MultiMedicineItem(medicine_name="Omez 20")
        ]
    )
    rep4 = PatientSafetyIntelligenceService.analyze_multiple_medicines_compatibility(db, req4)
    print("Status:", rep4.overall_status, "Therapeutic Duplications:", rep4.therapeutic_duplications_count)
    for row in rep4.interaction_table:
        print("  - [", row.severity, "]", row.interaction_title)

    print("\n=== TEST 5: Unidentified Medicine Diagnostic Handling ===")
    req5 = MultiMedicineCheckRequest(
        medicines=[
            MultiMedicineItem(medicine_name="CompletelyFakePillXyz123")
        ]
    )
    rep5 = PatientSafetyIntelligenceService.analyze_multiple_medicines_compatibility(db, req5)
    print("Status (Should be GREY):", rep5.overall_status)
    print("Diagnostics Summary:", rep5.diagnostics_summary)

if __name__ == "__main__":
    run_tests()
