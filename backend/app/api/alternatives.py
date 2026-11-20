from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.alternatives_service import AlternativeService

router = APIRouter(prefix="/alternatives", tags=["Medicine Alternatives"])

@router.get("/{medicine_id}")
def get_medicine_alternatives(medicine_id: int, db: Session = Depends(get_db)):
    result = AlternativeService.find_alternatives(db, medicine_id)
    if not result["target_medicine"]:
        raise HTTPException(status_code=404, detail="Target medicine not found")
    return result
