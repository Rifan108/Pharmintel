from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, List
from app.database import get_db
from app.schemas.medicine import MedicineResponse, MedicineSearchQuery
from app.services.medicine_service import MedicineService
from app.models.medicine import Medicine

router = APIRouter(prefix="/medicines", tags=["Medicines"])

@router.get("")
def search_medicines(
    q: Optional[str] = Query(None, description="Search term for brand, generic, or composition"),
    category: Optional[str] = Query(None, description="Therapeutic category filter"),
    dosage_form: Optional[str] = Query(None, description="Dosage form (Tablet, Capsule, etc.)"),
    requires_prescription: Optional[bool] = Query(None),
    min_price: Optional[float] = Query(None),
    max_price: Optional[float] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    query_params = MedicineSearchQuery(
        query=q,
        category=category,
        dosage_form=dosage_form,
        requires_prescription=requires_prescription,
        min_price=min_price,
        max_price=max_price,
        limit=limit,
        offset=offset
    )
    return MedicineService.search_medicines(db, query_params)

@router.get("/autocomplete")
def autocomplete(
    prefix: str = Query(..., min_length=1),
    limit: int = Query(8, ge=1, le=20),
    db: Session = Depends(get_db)
):
    return MedicineService.get_autocomplete_suggestions(db, prefix, limit)

@router.get("/categories")
def get_categories(db: Session = Depends(get_db)):
    return MedicineService.get_categories(db)

@router.get("/{medicine_id}")
def get_medicine_details(medicine_id: int, db: Session = Depends(get_db)):
    med = MedicineService.get_medicine_by_id(db, medicine_id)
    if not med:
        raise HTTPException(status_code=404, detail="Medicine record not found")
    return med
