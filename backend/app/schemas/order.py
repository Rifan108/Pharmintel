from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class OrderItemInput(BaseModel):
    medicine_id: int
    quantity: int

class OrderCreateRequest(BaseModel):
    pharmacy_id: int
    items: List[OrderItemInput]
    prescription_id: Optional[int] = None
    patient_name: Optional[str] = None # Manually provided patient name
    delivery_address: str
    contact_phone: str
    delivery_type: str = "Home Delivery" # Home Delivery, In-Store Pickup
    payment_method: str = "UPI / Online"
    special_instructions: Optional[str] = None

class OrderItemDetail(BaseModel):
    id: int
    medicine_id: int
    medicine_name: str
    strength: str
    dosage_form: str
    quantity: int
    unit_price: float
    mrp: float
    discount: float
    gst_rate: float
    total_price: float

class DeliveryDetail(BaseModel):
    tracking_number: str
    courier_name: str
    current_status: str
    driver_name: str
    driver_phone: str
    estimated_delivery_time: Optional[str] = None

class OrderResponse(BaseModel):
    id: int
    order_number: str
    customer_id: int
    pharmacy_id: int
    pharmacy_name: str
    prescription_id: Optional[int] = None
    status: str
    subtotal: float
    tax_amount: float
    delivery_fee: float
    total_amount: float
    payment_method: str
    payment_status: str
    patient_name: Optional[str] = None
    delivery_address: str
    contact_phone: str
    delivery_type: str
    created_at: datetime
    items: List[OrderItemDetail]
    delivery: Optional[DeliveryDetail] = None

class OrderStatusUpdate(BaseModel):
    status: str
    notes: Optional[str] = None
