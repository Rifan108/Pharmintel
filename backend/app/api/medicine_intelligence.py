from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from app.database import get_db
from app.models.medicine import Medicine
from app.services.medicine_intelligence_service import MedicineIntelligenceService, DIAGNOSTIC_CODES

router = APIRouter(prefix="/medicine-intelligence", tags=["Medicine Intelligence & Maximum Coverage"])

@router.get("/search")
def search_medicines(
    q: str = Query(..., min_length=1, description="Medicine query (brand, generic, salt, formulation, or typo)"),
    limit: int = Query(15, ge=1, le=50),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """
    Intelligent multi-tier medicine search supporting:
    - Exact and case-insensitive matching
    - Generic, brand, and constituent active ingredients
    - Combination product recognition
    - Strength & formulation ranking
    - Typographical tolerance
    - Ambiguity detection
    """
    res = MedicineIntelligenceService.search_medicines(db, q, limit=limit, offset=offset)
    
    # Format items for clean JSON output
    formatted_items = []
    for m in res["items"]:
        completeness_score, checks = MedicineIntelligenceService.calculate_completeness(m)
        formatted_items.append({
            "id": m.id,
            "medicine_code": m.medicine_code,
            "brand_name": m.brand_name,
            "generic_name": m.generic_name,
            "active_ingredients": m.active_ingredients,
            "composition": m.composition,
            "strength": m.strength,
            "dosage_form": m.dosage_form,
            "route_of_administration": m.route_of_administration,
            "manufacturer": m.manufacturer,
            "therapeutic_category": m.therapeutic_category,
            "drug_classification": m.drug_classification,
            "atc_code": m.atc_code,
            "is_combination": m.is_combination,
            "requires_prescription": m.requires_prescription,
            "prescription_classification": m.prescription_classification,
            "base_mrp": m.base_mrp,
            "source": m.source,
            "completeness_score": completeness_score,
            "completeness_checks": checks,
            "verification_status": m.verification_status
        })

    return {
        "query": q,
        "total": res["total"],
        "ambiguity": res["ambiguity"],
        "candidates": res["candidates"],
        "items": formatted_items
    }

@router.get("/resolve")
def resolve_medicine(
    name: str = Query(..., min_length=1, description="Raw medicine name or brand"),
    session_id: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Resolves a medicine string into a verified clinical record, active ingredients,
    and detailed incomplete-information diagnostic status.
    """
    res = MedicineIntelligenceService.resolve_medicine(db, name, session_id=session_id)
    
    med = res.get("medicine")
    med_data = None
    if med:
        score, checks = MedicineIntelligenceService.calculate_completeness(med)
        med_data = {
            "id": med.id,
            "medicine_code": med.medicine_code,
            "brand_name": med.brand_name,
            "generic_name": med.generic_name,
            "active_ingredients": med.active_ingredients,
            "composition": med.composition,
            "strength": med.strength,
            "dosage_form": med.dosage_form,
            "route_of_administration": med.route_of_administration,
            "manufacturer": med.manufacturer,
            "therapeutic_category": med.therapeutic_category,
            "drug_classification": med.drug_classification,
            "atc_code": med.atc_code,
            "is_combination": med.is_combination,
            "requires_prescription": med.requires_prescription,
            "prescription_classification": med.prescription_classification,
            "source": med.source,
            "completeness_score": score,
            "completeness_checks": checks,
            "verification_status": med.verification_status
        }

    return {
        "status": res["status"],
        "diagnostic_code": res["diagnostic_code"],
        "diagnostic": res["diagnostic"],
        "raw_input": res.get("raw_input", name),
        "medicine": med_data,
        "active_substances": res.get("active_substances", []),
        "is_combination": res.get("is_combination", False),
        "candidate_matches": res.get("candidate_matches", []),
        "completeness_score": res.get("completeness_score", 0.0)
    }

@router.post("/discover")
def trigger_continuous_discovery(
    name: str = Query(..., min_length=2),
    session_id: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Executes live discovery against external official registries (RxNorm NLM)
    for medicines not yet in the local database.
    """
    res = MedicineIntelligenceService.discover_external_medicine(db, name, session_id=session_id)
    if res["discovered"]:
        med = res["medicine"]
        score, checks = MedicineIntelligenceService.calculate_completeness(med)
        return {
            "discovered": True,
            "diagnostic_code": "VERIFIED_COMPLETE",
            "medicine": {
                "id": med.id,
                "medicine_code": med.medicine_code,
                "brand_name": med.brand_name,
                "generic_name": med.generic_name,
                "active_ingredients": med.active_ingredients,
                "strength": med.strength,
                "dosage_form": med.dosage_form,
                "source": med.source,
                "completeness_score": score,
                "verification_status": med.verification_status,
                "external_reference_id": med.external_reference_id
            }
        }
    return {
        "discovered": False,
        "diagnostic_code": res.get("diagnostic_code", "MEDICINE_NOT_IDENTIFIED"),
        "diagnostic": DIAGNOSTIC_CODES.get(res.get("diagnostic_code", "MEDICINE_NOT_IDENTIFIED"))
    }

@router.get("/diagnostic-codes")
def list_diagnostic_codes():
    """
    Returns the comprehensive list of 10 precise diagnostic statuses.
    """
    return list(DIAGNOSTIC_CODES.values())

@router.get("/admin/metrics")
def get_admin_metrics(db: Session = Depends(get_db)):
    """
    Returns administrative metrics regarding total medicine coverage, Indian brands,
    generics, combination products, clinical completeness, and audit trails.
    """
    return MedicineIntelligenceService.get_administration_metrics(db)

@router.get("/admin/medicines")
def list_admin_medicines(
    q: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """
    Paginated administrative list of medicines with filtering by category and verification status.
    """
    query = db.query(Medicine)
    if q and q.strip():
        term = f"%{q.strip()}%"
        query = query.filter(
            or_(
                Medicine.brand_name.ilike(term),
                Medicine.generic_name.ilike(term),
                Medicine.active_ingredients.ilike(term),
                Medicine.manufacturer.ilike(term)
            )
        )
    if category and category.strip():
        query = query.filter(Medicine.therapeutic_category.ilike(f"%{category.strip()}%"))
    if status and status.strip():
        query = query.filter(Medicine.verification_status == status.strip())

    total = query.count()
    items = query.order_by(Medicine.id.desc()).offset(offset).limit(limit).all()

    formatted = []
    for m in items:
        score, checks = MedicineIntelligenceService.calculate_completeness(m)
        formatted.append({
            "id": m.id,
            "medicine_code": m.medicine_code,
            "brand_name": m.brand_name,
            "generic_name": m.generic_name,
            "active_ingredients": m.active_ingredients,
            "strength": m.strength,
            "dosage_form": m.dosage_form,
            "route_of_administration": m.route_of_administration,
            "manufacturer": m.manufacturer,
            "therapeutic_category": m.therapeutic_category,
            "drug_classification": m.drug_classification,
            "atc_code": m.atc_code,
            "is_combination": m.is_combination,
            "source": m.source,
            "verification_status": m.verification_status,
            "completeness_score": score,
            "base_mrp": m.base_mrp
        })

    return {"total": total, "items": formatted, "limit": limit, "offset": offset}
