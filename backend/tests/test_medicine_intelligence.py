"""
Automated Validation Test Suite for PHARMINTEL Global Medicine Intelligence
and Multi-Drug Safety Architecture.
"""

import sys
import os
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import SessionLocal
from app.models.medicine import Medicine, DrugInteraction
from app.schemas.interaction import MultiMedicineCheckRequest, MultiMedicineItem, HealthProfileInput
from app.services.medicine_intelligence_service import MedicineIntelligenceService, DIAGNOSTIC_CODES
from app.services.patient_safety_service import PatientSafetyIntelligenceService


@pytest.fixture(scope="module")
def db_session():
    session = SessionLocal()
    yield session
    session.close()


class TestMedicineIntelligenceCoverage:
    """Verifies that the database compendium meets maximum coverage requirements."""

    def test_total_medicine_coverage(self, db_session):
        count = db_session.query(Medicine).count()
        assert count >= 100, f"Expected at least 100 medicines, found {count}"

    def test_curated_interaction_rules_coverage(self, db_session):
        count = db_session.query(DrugInteraction).count()
        assert count >= 40, f"Expected at least 40 clinical interaction rules, found {count}"

    def test_top_indian_brands_presence(self, db_session):
        top_brands = [
            "Glycomet 500", "Dolo 650", "Pan-D", "Combiflam", "Zerodol-P",
            "Januvia 100", "Lipaglyn 4", "Shelcal 500", "Becosules Capsules",
            "Foracort 200 Inhaler", "Ceftum 500", "Allegra 120", "Aciloc 150"
        ]
        for brand in top_brands:
            med = db_session.query(Medicine).filter(Medicine.brand_name.ilike(f"%{brand}%")).first()
            assert med is not None, f"Expected Indian brand '{brand}' in database"

    def test_completeness_scores(self, db_session):
        meds = db_session.query(Medicine).all()
        for m in meds:
            score, checks = MedicineIntelligenceService.calculate_completeness(m)
            assert score >= 0.8, f"Medicine {m.brand_name} completeness score {score} is below 0.8"


class TestIntelligentMatchingAndTypos:
    """Verifies typo tolerance, prefix matching, and ambiguity detection."""

    def test_typo_tolerance_paracetamol(self, db_session):
        res = MedicineIntelligenceService.search_medicines(db_session, "paracetmol")
        assert len(res["items"]) > 0
        top_item = res["items"][0]
        assert "paracetamol" in top_item.generic_name.lower() or "dolo" in top_item.brand_name.lower()

    def test_typo_tolerance_dolo(self, db_session):
        res = MedicineIntelligenceService.search_medicines(db_session, "dollo 650")
        assert len(res["items"]) > 0
        top_item = res["items"][0]
        assert "dolo" in top_item.brand_name.lower() or "paracetamol" in top_item.generic_name.lower()

    def test_combination_ingredient_parsing(self):
        parts = MedicineIntelligenceService.parse_combination_ingredients("Ibuprofen + Paracetamol")
        assert "Ibuprofen" in parts
        assert "Paracetamol" in parts

    def test_ambiguity_detection_multiple_strengths(self, db_session):
        res = MedicineIntelligenceService.search_medicines(db_session, "Glycomet")
        assert res["total"] >= 2
        # Should detect multiple variants or strengths
        strengths = [m.strength for m in res["items"]]
        assert len(set(strengths)) >= 2


class TestMultiMedicineCompatibilityEngine:
    """Verifies multi-constituent combination evaluation, syndromes, and duplicates."""

    def test_duplicate_active_ingredient_combiflam_dolo(self, db_session):
        req = MultiMedicineCheckRequest(
            medicines=[
                MultiMedicineItem(medicine_name="Combiflam"),
                MultiMedicineItem(medicine_name="Dolo 650")
            ]
        )
        report = PatientSafetyIntelligenceService.analyze_multiple_medicines_compatibility(db_session, req)
        assert report.overall_status == "RED"
        assert report.duplicate_medicines_count >= 1
        dup_rows = [r for r in report.interaction_table if "Duplicate" in r.interaction_title]
        assert len(dup_rows) > 0
        assert "Paracetamol" in dup_rows[0].interaction_title

    def test_triple_whammy_syndrome(self, db_session):
        # ACEi/ARB (Losartan) + Diuretic (Lasix/Furosemide) + NSAID (Brufen/Ibuprofen)
        req = MultiMedicineCheckRequest(
            medicines=[
                MultiMedicineItem(medicine_name="Losartan 50mg"),
                MultiMedicineItem(medicine_name="Lasix 40mg"),
                MultiMedicineItem(medicine_name="Brufen 400mg")
            ]
        )
        report = PatientSafetyIntelligenceService.analyze_multiple_medicines_compatibility(db_session, req)
        assert report.overall_status == "RED"
        tw_rows = [r for r in report.interaction_table if "Triple Whammy" in r.interaction_title]
        assert len(tw_rows) >= 1
        assert "Acute kidney failure" in tw_rows[0].clinical_consequences

    def test_serotonin_syndrome(self, db_session):
        # SSRI (Sertraline / Sertima) + Opioid (Tramadol / Tramazac)
        req = MultiMedicineCheckRequest(
            medicines=[
                MultiMedicineItem(medicine_name="Sertima 50"),
                MultiMedicineItem(medicine_name="Tramazac 50")
            ]
        )
        report = PatientSafetyIntelligenceService.analyze_multiple_medicines_compatibility(db_session, req)
        assert report.overall_status == "RED"
        ss_found = any("serotonin" in (r.interaction_title + " " + r.clinical_mechanism + " " + r.clinical_consequences).lower() for r in report.interaction_table)
        assert ss_found, "Expected Serotonin Syndrome warning"

    def test_additive_qt_prolongation(self, db_session):
        # Azithral (Azithromycin) + Ciplox (Ciprofloxacin) + Emset (Ondansetron)
        req = MultiMedicineCheckRequest(
            medicines=[
                MultiMedicineItem(medicine_name="Azithral 500"),
                MultiMedicineItem(medicine_name="Ciplox 500"),
                MultiMedicineItem(medicine_name="Emset 4")
            ]
        )
        report = PatientSafetyIntelligenceService.analyze_multiple_medicines_compatibility(db_session, req)
        assert report.overall_status == "RED"
        qt_rows = [r for r in report.interaction_table if "QT" in r.interaction_title or "Torsades" in r.clinical_consequences]
        assert len(qt_rows) >= 1

    def test_therapeutic_duplication(self, db_session):
        # Pan 40 (Pantoprazole) + Omez 20 (Omeprazole)
        req = MultiMedicineCheckRequest(
            medicines=[
                MultiMedicineItem(medicine_name="Pan 40"),
                MultiMedicineItem(medicine_name="Omez 20")
            ]
        )
        report = PatientSafetyIntelligenceService.analyze_multiple_medicines_compatibility(db_session, req)
        assert report.therapeutic_duplications_count >= 1
        tdup_rows = [r for r in report.interaction_table if "Therapeutic Duplication" in r.interaction_title]
        assert len(tdup_rows) >= 1

    def test_multilingual_localization_kannada(self, db_session):
        req = MultiMedicineCheckRequest(
            medicines=[
                MultiMedicineItem(medicine_name="Combiflam"),
                MultiMedicineItem(medicine_name="Dolo 650")
            ],
            language="kn"
        )
        report = PatientSafetyIntelligenceService.analyze_multiple_medicines_compatibility(db_session, req)
        assert "ನಕಲಿ" in report.interaction_table[0].explanation or "ಔಷಧ" in report.what_does_this_mean

    def test_multilingual_localization_hindi(self, db_session):
        req = MultiMedicineCheckRequest(
            medicines=[
                MultiMedicineItem(medicine_name="Combiflam"),
                MultiMedicineItem(medicine_name="Dolo 650")
            ],
            language="hi"
        )
        report = PatientSafetyIntelligenceService.analyze_multiple_medicines_compatibility(db_session, req)
        assert "दवा" in report.what_does_this_mean or "समान सक्रिय घटक" in report.interaction_table[0].explanation


class TestSafetyGuardrailsAndUncertainty:
    """Verifies that unidentified or missing information is never forced to GREEN."""

    def test_unidentified_medicine_yields_grey(self, db_session):
        req = MultiMedicineCheckRequest(
            medicines=[
                MultiMedicineItem(medicine_name="NonExistentDrug123Xyz")
            ]
        )
        report = PatientSafetyIntelligenceService.analyze_multiple_medicines_compatibility(db_session, req)
        assert report.overall_status == "GREY", "Unidentified medicine must yield GREY status"
        assert len(report.unidentified_medicines) == 1
        assert report.diagnostics_summary[0]["diagnostic_code"] == "MEDICINE_NOT_IDENTIFIED"

    def test_diagnostic_codes_coverage(self):
        expected_codes = [
            "MEDICINE_NOT_IDENTIFIED",
            "MULTIPLE_POSSIBLE_MATCHES",
            "ACTIVE_INGREDIENT_NOT_VERIFIED",
            "STRENGTH_UNAVAILABLE",
            "FORMULATION_UNCLEAR",
            "CLINICAL_INFO_INCOMPLETE",
            "INTERACTION_EVIDENCE_UNAVAILABLE",
            "PATIENT_INFO_UNAVAILABLE",
            "EXTERNAL_SOURCE_UNAVAILABLE",
            "DATA_SYNC_FAILED",
            "TECHNICAL_RETRIEVAL_ERROR"
        ]
        for code in expected_codes:
            assert code in DIAGNOSTIC_CODES, f"Expected diagnostic code {code} in DIAGNOSTIC_CODES"
