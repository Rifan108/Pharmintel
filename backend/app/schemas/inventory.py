from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class BatchCreate(BaseModel):
    batch_number: str
    expiry_date: str # YYYY-MM-DD
    purchase_price: float
    selling_price: float
    mrp: float
    quantity: int
    supplier_id: Optional[int] = None

class BatchResponse(BatchCreate):
    id: int
    inventory_id: int
    is_recalled: bool
    created_at: datetime

    class Config:
        from_attributes = True

class InventoryItemResponse(BaseModel):
    id: int
    pharmacy_id: int
    medicine_id: int
    medicine_name: str
    medicine_code: str
    strength: str
    dosage_form: str
    stock_quantity: int
    low_stock_threshold: int
    is_available: bool
    is_low_stock: bool
    has_expired_batches: bool
    batches: List[BatchResponse]

class StockAdjustmentRequest(BaseModel):
    batch_id: Optional[int] = None
    action: str # STOCK_IN, ADJUSTMENT, RECALL, EXPIRY_REMOVAL
    quantity_changed: int
    reason: Optional[str] = None
