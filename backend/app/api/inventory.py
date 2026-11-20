from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from app.database import get_db
from app.utils.security import get_current_user_payload, require_role
from app.services.inventory_service import InventoryService
from app.schemas.inventory import BatchCreate, StockAdjustmentRequest
from app.models.inventory import StockAuditLog
from app.models.user import Pharmacist

router = APIRouter(prefix="/inventory", tags=["Inventory Management"])

@router.get("/{pharmacy_id}")
def get_inventory(
    pharmacy_id: int,
    db: Session = Depends(get_db),
    user_payload: dict = Depends(require_role(["pharmacist", "pharmacy_admin", "platform_admin"]))
):
    return InventoryService.get_pharmacy_inventory(db, pharmacy_id)

@router.post("/{pharmacy_id}/medicines/{medicine_id}/batches")
def add_medicine_batch(
    pharmacy_id: int,
    medicine_id: int,
    batch_data: BatchCreate,
    db: Session = Depends(get_db),
    user_payload: dict = Depends(require_role(["pharmacist", "pharmacy_admin", "platform_admin"]))
):
    user_id = int(user_payload.get("sub"))
    return InventoryService.add_batch(db, pharmacy_id, medicine_id, batch_data, user_id)

@router.post("/{pharmacy_id}/medicines/{medicine_id}/adjust")
def adjust_inventory_stock(
    pharmacy_id: int,
    medicine_id: int,
    req: StockAdjustmentRequest,
    db: Session = Depends(get_db),
    user_payload: dict = Depends(require_role(["pharmacist", "pharmacy_admin", "platform_admin"]))
):
    user_id = int(user_payload.get("sub"))
    return InventoryService.adjust_stock(db, pharmacy_id, medicine_id, req, user_id)

@router.get("/{pharmacy_id}/audit-logs")
def get_stock_audit_logs(
    pharmacy_id: int,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    user_payload: dict = Depends(require_role(["pharmacist", "pharmacy_admin", "platform_admin"]))
):
    logs = db.query(StockAuditLog).filter(
        StockAuditLog.pharmacy_id == pharmacy_id
    ).order_by(StockAuditLog.timestamp.desc()).limit(limit).all()
    return logs
