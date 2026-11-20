import json
from datetime import datetime
from app.database import SessionLocal
from app.models.medicine import Medicine, DrugInteraction
from app.utils.global_medicine_dataset import VERIFIED_GLOBAL_MEDICINES, VERIFIED_ADDITIONAL_INTERACTIONS

def ingest_global_medicines():
    db = SessionLocal()
    print("Ingesting verified global and Indian medicine dataset into PHARMINTEL...")

    added_meds = 0
    updated_meds = 0

    for m in VERIFIED_GLOBAL_MEDICINES:
        # Check by code or brand
        existing = db.query(Medicine).filter(
            (Medicine.medicine_code == m["code"]) | 
            (Medicine.brand_name.ilike(m["brand"]))
        ).first()

        if existing:
            # Update fields
            existing.generic_name = m["generic"]
            existing.brand_name = m["brand"]
            existing.active_ingredients = m["ingredients"]
            existing.composition = m["composition"]
            existing.strength = m["strength"]
            existing.dosage_form = m["dosage_form"]
            existing.route_of_administration = m["route"]
            existing.manufacturer = m["manufacturer"]
            existing.therapeutic_category = m["category"]
            existing.drug_classification = m["classification"]
            existing.atc_code = m.get("atc_code")
            existing.is_combination = m.get("is_combination", False)
            existing.active_substances_json = json.dumps(m.get("active_substances", []))
            existing.aliases_json = json.dumps(m.get("aliases", []))
            existing.approved_indications = m["indications"]
            existing.contraindications = m["contraindications"]
            existing.known_adverse_effects = m["adverse_effects"]
            existing.storage_information = m["storage"]
            existing.prescription_classification = m["prescription"]
            existing.requires_prescription = m["requires_rx"]
            existing.drugbank_id = m.get("drugbank_id")
            existing.pubchem_cid = m.get("pubchem_cid")
            existing.smiles = m.get("smiles")
            existing.source = m["source"]
            existing.last_verified_date = datetime.now().strftime("%Y-%m-%d")
            existing.base_mrp = m["base_mrp"]
            existing.completeness_score = 1.0
            existing.verification_status = "VERIFIED_REGULATORY"
            existing.external_reference_id = m.get("ref_id")
            updated_meds += 1
        else:
            new_med = Medicine(
                medicine_code=m["code"],
                generic_name=m["generic"],
                brand_name=m["brand"],
                active_ingredients=m["ingredients"],
                composition=m["composition"],
                strength=m["strength"],
                dosage_form=m["dosage_form"],
                route_of_administration=m["route"],
                manufacturer=m["manufacturer"],
                therapeutic_category=m["category"],
                drug_classification=m["classification"],
                atc_code=m.get("atc_code"),
                is_combination=m.get("is_combination", False),
                active_substances_json=json.dumps(m.get("active_substances", [])),
                aliases_json=json.dumps(m.get("aliases", [])),
                approved_indications=m["indications"],
                contraindications=m["contraindications"],
                known_adverse_effects=m["adverse_effects"],
                storage_information=m["storage"],
                prescription_classification=m["prescription"],
                requires_prescription=m["requires_rx"],
                drugbank_id=m.get("drugbank_id"),
                pubchem_cid=m.get("pubchem_cid"),
                smiles=m.get("smiles"),
                source=m["source"],
                last_verified_date=datetime.now().strftime("%Y-%m-%d"),
                base_mrp=m["base_mrp"],
                completeness_score=1.0,
                verification_status="VERIFIED_REGULATORY",
                external_reference_id=m.get("ref_id")
            )
            db.add(new_med)
            added_meds += 1

    db.commit()
    print(f"Medicines ingested: {added_meds} added, {updated_meds} updated. Total medicines now: {db.query(Medicine).count()}")

    # Ingest Drug Interactions
    added_interactions = 0
    for inter in VERIFIED_ADDITIONAL_INTERACTIONS:
        existing_rule = db.query(DrugInteraction).filter(
            ((DrugInteraction.drug_a_generic.ilike(f"%{inter['drug_a']}%")) & (DrugInteraction.drug_b_generic.ilike(f"%{inter['drug_b']}%"))) |
            ((DrugInteraction.drug_a_generic.ilike(f"%{inter['drug_b']}%")) & (DrugInteraction.drug_b_generic.ilike(f"%{inter['drug_a']}%")))
        ).first()

        if not existing_rule:
            new_rule = DrugInteraction(
                drug_a_generic=inter["drug_a"],
                drug_b_generic=inter["drug_b"],
                severity_category=inter["severity"],
                mechanism=inter["mechanism"],
                clinical_consequences=inter["consequences"],
                evidence_source=inter["source"],
                source_reference=inter["reference"],
                last_verified_date=datetime.now().strftime("%Y-%m-%d")
            )
            db.add(new_rule)
            added_interactions += 1

    db.commit()
    print(f"Interactions ingested: {added_interactions} added. Total interaction rules: {db.query(DrugInteraction).count()}")
    db.close()

if __name__ == "__main__":
    ingest_global_medicines()
