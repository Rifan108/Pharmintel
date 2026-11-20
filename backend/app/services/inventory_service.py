from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from fastapi import HTTPException
from app.models.inventory import PharmacyInventory, MedicineBatch, StockAuditLog
from app.models.medicine import Medicine
from app.schemas.inventory import BatchCreate, StockAdjustmentRequest

class InventoryService:
    @staticmethod
    def get_pharmacy_inventory(db: Session, pharmacy_id: int) -> List[Dict[str, Any]]:
        items = db.query(PharmacyInventory).filter(PharmacyInventory.pharmacy_id == pharmacy_id).all()
        result = []
        today_str = datetime.utcnow().strftime("%Y-%m-%d")
        sixty_days_str = (datetime.utcnow() + timedelta(days=60)).strftime("%Y-%m-%d")

        for inv in items:
            med = inv.medicine
            batches = inv.batches

            is_low_stock = (inv.stock_quantity <= inv.low_stock_threshold)
            has_expired = any(b.expiry_date <= today_str for b in batches)
            has_near_expiry = any(today_str < b.expiry_date <= sixty_days_str for b in batches)

            batch_list = []
            for b in batches:
                batch_list.append({
                    "id": b.id,
                    "batch_number": b.batch_number,
                    "expiry_date": b.expiry_date,
                    "purchase_price": b.purchase_price,
                    "selling_price": b.selling_price,
                    "mrp": b.mrp,
                    "quantity": b.quantity,
                    "is_recalled": b.is_recalled,
                    "is_expired": (b.expiry_date <= today_str),
                    "is_near_expiry": (today_str < b.expiry_date <= sixty_days_str)
                })

            result.append({
                "id": inv.id,
                "pharmacy_id": inv.pharmacy_id,
                "medicine_id": inv.medicine_id,
                "medicine_name": med.brand_name,
                "generic_name": med.generic_name,
                "medicine_code": med.medicine_code,
                "strength": med.strength,
                "dosage_form": med.dosage_form,
                "stock_quantity": inv.stock_quantity,
                "low_stock_threshold": inv.low_stock_threshold,
                "is_available": inv.is_available,
                "is_low_stock": is_low_stock,
                "has_expired_batches": has_expired,
                "has_near_expiry_batches": has_near_expiry,
                "base_mrp": med.base_mrp,
                "batches": batch_list
            })

        return result

    @staticmethod
    def add_batch(db: Session, pharmacy_id: int, medicine_id: int, batch_data: BatchCreate, user_id: int) -> Dict[str, Any]:
        # Find or create inventory entry
        inv = db.query(PharmacyInventory).filter(
            PharmacyInventory.pharmacy_id == pharmacy_id,
            PharmacyInventory.medicine_id == medicine_id
        ).first()

        if not inv:
            inv = PharmacyInventory(
                pharmacy_id=pharmacy_id,
                medicine_id=medicine_id,
                stock_quantity=0,
                low_stock_threshold=15,
                is_available=True
            )
            db.add(inv)
            db.commit()
            db.refresh(inv)

        # Create batch
        new_batch = MedicineBatch(
            inventory_id=inv.id,
            batch_number=batch_data.batch_number,
            expiry_date=batch_data.expiry_date,
            purchase_price=batch_data.purchase_price,
            selling_price=batch_data.selling_price,
            mrp=batch_data.mrp,
            quantity=batch_data.quantity,
            supplier_id=batch_data.supplier_id,
            is_recalled=False
        )
        db.add(new_batch)

        # Update inventory total stock
        inv.stock_quantity += batch_data.quantity
        inv.is_available = (inv.stock_quantity > 0)
        db.commit()
        db.refresh(new_batch)

        # Audit log
        log = StockAuditLog(
            pharmacy_id=pharmacy_id,
            medicine_id=medicine_id,
            batch_id=new_batch.id,
            action="STOCK_IN",
            quantity_changed=batch_data.quantity,
            balance_quantity=inv.stock_quantity,
            performed_by_user_id=user_id,
            reason=f"New batch received: {batch_data.batch_number}"
        )
        db.add(log)
        db.commit()

        return {"message": "Batch added successfully", "batch_id": new_batch.id, "new_stock": inv.stock_quantity}

    @staticmethod
    def adjust_stock(db: Session, pharmacy_id: int, medicine_id: int, req: StockAdjustmentRequest, user_id: int) -> Dict[str, Any]:
        inv = db.query(PharmacyInventory).filter(
            PharmacyInventory.pharmacy_id == pharmacy_id,
            PharmacyInventory.medicine_id == medicine_id
        ).first()

        if not inv:
            raise HTTPException(status_code=404, detail="Inventory item not found")

        old_stock = inv.stock_quantity
        new_stock = max(0, old_stock + req.quantity_changed)
        inv.stock_quantity = new_stock
        inv.is_available = (new_stock > 0)

        if req.batch_id:
            batch = db.query(MedicineBatch).filter(MedicineBatch.id == req.batch_id).first()
            if batch:
                batch.quantity = max(0, batch.quantity + req.quantity_changed)
                if req.action == "RECALL":
                    batch.is_recalled = True
                    batch.recall_reason = req.reason or "Manufacturer/Regulatory Recall Notice"

        log = StockAuditLog(
            pharmacy_id=pharmacy_id,
            medicine_id=medicine_id,
            batch_id=req.batch_id,
            action=req.action,
            quantity_changed=req.quantity_changed,
            balance_quantity=new_stock,
            performed_by_user_id=user_id,
            reason=req.reason
        )
        db.add(log)
        db.commit()

        return {"message": "Stock adjusted successfully", "new_stock": new_stock}
