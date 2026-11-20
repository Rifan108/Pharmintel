from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app.models.medicine import Medicine
from app.schemas.medicine import AlternativeItem

class AlternativeService:
    @staticmethod
    def find_alternatives(db: Session, medicine_id: int) -> Dict[str, Any]:
        target = db.query(Medicine).filter(Medicine.id == medicine_id).first()
        if not target:
            return {"target_medicine": None, "alternatives": []}

        all_other = db.query(Medicine).filter(Medicine.id != medicine_id).all()
        alternatives: List[AlternativeItem] = []

        target_active = [a.strip().lower() for a in target.active_ingredients.split(",")]
        target_strength = target.strength.strip().lower()
        target_form = target.dosage_form.strip().lower()

        for med in all_other:
            med_active = [a.strip().lower() for a in med.active_ingredients.split(",")]
            med_strength = med.strength.strip().lower()
            med_form = med.dosage_form.strip().lower()

            price_diff = round(med.base_mrp - target.base_mrp, 2)
            
            # Check 1: EXACT GENERIC OR SAME ACTIVE INGREDIENT + SAME STRENGTH + SAME FORM
            if set(target_active) == set(med_active) and target_strength == med_strength and target_form == med_form:
                alt_type = "EXACT_GENERIC" if "generic" in med.brand_name.lower() or med.brand_name.lower() == med.generic_name.lower() else "BRANDED_EQUIVALENT"
                reason = f"Bioequivalent active ingredient ({med.generic_name}) with identical strength ({med.strength}) and pharmaceutical dosage form ({med.dosage_form}). Pharmacist substitution allowed upon patient consent."
                alternatives.append(AlternativeItem(
                    id=med.id,
                    medicine_code=med.medicine_code,
                    brand_name=med.brand_name,
                    generic_name=med.generic_name,
                    manufacturer=med.manufacturer,
                    strength=med.strength,
                    dosage_form=med.dosage_form,
                    base_mrp=med.base_mrp,
                    price_difference=price_diff,
                    alternative_type=alt_type,
                    requires_prescription=med.requires_prescription,
                    availability_status="In Stock",
                    reason=reason
                ))
            # Check 2: SAME THERAPEUTIC CLASS ALTERNATIVE (e.g. Omeprazole vs Pantoprazole, or Atorvastatin vs Simvastatin)
            elif target.therapeutic_category == med.therapeutic_category:
                reason = f"Alternative pharmacological agent within same therapeutic class ({target.therapeutic_category}). Requires physician consultation and pharmacist review before switching."
                alternatives.append(AlternativeItem(
                    id=med.id,
                    medicine_code=med.medicine_code,
                    brand_name=med.brand_name,
                    generic_name=med.generic_name,
                    manufacturer=med.manufacturer,
                    strength=med.strength,
                    dosage_form=med.dosage_form,
                    base_mrp=med.base_mrp,
                    price_difference=price_diff,
                    alternative_type="THERAPEUTIC_ALTERNATIVE",
                    requires_prescription=med.requires_prescription,
                    availability_status="In Stock",
                    reason=reason
                ))

        # Sort: EXACT_GENERIC and BRANDED_EQUIVALENT first, then by absolute price difference
        type_priority = {"EXACT_GENERIC": 1, "BRANDED_EQUIVALENT": 2, "THERAPEUTIC_ALTERNATIVE": 3}
        alternatives.sort(key=lambda x: (type_priority.get(x.alternative_type, 4), abs(x.price_difference)))

        return {
            "target_medicine": {
                "id": target.id,
                "brand_name": target.brand_name,
                "generic_name": target.generic_name,
                "strength": target.strength,
                "dosage_form": target.dosage_form,
                "manufacturer": target.manufacturer,
                "base_mrp": target.base_mrp,
                "category": target.therapeutic_category
            },
            "alternatives": alternatives
        }
