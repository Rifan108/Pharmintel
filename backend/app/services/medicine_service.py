from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from typing import List, Optional, Dict, Any
from app.models.medicine import Medicine
from app.schemas.medicine import MedicineSearchQuery
import difflib

class MedicineService:
    @staticmethod
    def search_medicines(db: Session, query_params: MedicineSearchQuery) -> Dict[str, Any]:
        q = db.query(Medicine)

        if query_params.category:
            q = q.filter(Medicine.therapeutic_category.ilike(f"%{query_params.category}%"))

        if query_params.dosage_form:
            q = q.filter(Medicine.dosage_form.ilike(f"%{query_params.dosage_form}%"))

        if query_params.requires_prescription is not None:
            q = q.filter(Medicine.requires_prescription == query_params.requires_prescription)

        if query_params.min_price is not None:
            q = q.filter(Medicine.base_mrp >= query_params.min_price)

        if query_params.max_price is not None:
            q = q.filter(Medicine.base_mrp <= query_params.max_price)

        all_meds = q.all()

        # Text search with typo tolerance and fuzzy score ranking
        search_term = query_params.query.strip().lower() if query_params.query else ""
        if search_term:
            scored_results = []
            for med in all_meds:
                # Check exact substring matches in brand, generic, active ingredient, manufacturer, composition
                brand_lower = med.brand_name.lower()
                generic_lower = med.generic_name.lower()
                comp_lower = med.composition.lower()
                manuf_lower = med.manufacturer.lower()

                score = 0.0
                if search_term in brand_lower:
                    score = 1.0 + (len(search_term) / len(brand_lower))
                elif search_term in generic_lower:
                    score = 0.9 + (len(search_term) / len(generic_lower))
                elif search_term in comp_lower:
                    score = 0.8
                elif search_term in manuf_lower:
                    score = 0.7
                else:
                    # Typo tolerance using difflib
                    sim_brand = difflib.SequenceMatcher(None, search_term, brand_lower).ratio()
                    sim_generic = difflib.SequenceMatcher(None, search_term, generic_lower).ratio()
                    best_sim = max(sim_brand, sim_generic)
                    if best_sim >= 0.60: # Typo match threshold
                        score = best_sim

                if score > 0.0:
                    scored_results.append((score, med))

            scored_results.sort(key=lambda x: x[0], reverse=True)
            total = len(scored_results)
            paged_meds = [m for _, m in scored_results[query_params.offset: query_params.offset + query_params.limit]]
        else:
            total = len(all_meds)
            paged_meds = all_meds[query_params.offset: query_params.offset + query_params.limit]

        return {
            "total": total,
            "items": paged_meds,
            "limit": query_params.limit,
            "offset": query_params.offset
        }

    @staticmethod
    def get_autocomplete_suggestions(db: Session, prefix: str, limit: int = 8) -> List[Dict[str, Any]]:
        prefix_clean = prefix.strip().lower()
        if not prefix_clean:
            return []

        from app.services.medicine_intelligence_service import MedicineIntelligenceService
        search_res = MedicineIntelligenceService.search_medicines(db, prefix_clean, limit=limit)
        
        suggestions = []
        for m in search_res["items"]:
            suggestions.append({
                "id": m.id,
                "code": m.medicine_code,
                "brand_name": m.brand_name,
                "generic_name": m.generic_name,
                "active_ingredients": m.active_ingredients,
                "strength": m.strength,
                "dosage_form": m.dosage_form,
                "category": m.therapeutic_category,
                "requires_prescription": m.requires_prescription,
                "base_mrp": m.base_mrp
            })

        return suggestions[:limit]

    @staticmethod
    def get_medicine_by_id(db: Session, medicine_id: int) -> Optional[Medicine]:
        return db.query(Medicine).filter(Medicine.id == medicine_id).first()

    @staticmethod
    def get_categories(db: Session) -> List[str]:
        results = db.query(Medicine.therapeutic_category).distinct().all()
        return sorted([r[0] for r in results if r[0]])
