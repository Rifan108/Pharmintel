import hmac
import hashlib
import random
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from pydantic import BaseModel
from typing import Optional

from app.database import get_db
from app.utils.security import get_current_user_payload
from app.models.order import Order, Payment
from app.services.order_service import OrderService

router = APIRouter(prefix="/payments", tags=["Payment Gateway & Transactions"])

class CreatePaymentOrderRequest(BaseModel):
    order_id: int
    payment_method: str = "UPI / Online" # UPI, Card, Net Banking, COD

class VerifyPaymentRequest(BaseModel):
    order_id: int
    gateway_payment_id: str
    gateway_order_id: Optional[str] = None
    gateway_signature: Optional[str] = None
    payment_method: Optional[str] = "UPI / Online"

@router.post("/create-order")
def create_payment_order(
    req: CreatePaymentOrderRequest,
    db: Session = Depends(get_db),
    user_payload: dict = Depends(get_current_user_payload)
):
    user_id = int(user_payload.get("sub"))
    order = db.query(Order).filter(Order.id == req.order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.customer_id != user_id:
        raise HTTPException(status_code=403, detail="Unauthorized access to this order")

    # Generate gateway order details
    amount_in_paise = int(round(order.total_amount * 100))
    gateway_order_id = f"order_pi_{order.id}_{random.randint(100000, 999999)}"

    # Check if payment record already exists
    payment = db.query(Payment).filter(Payment.order_id == order.id).first()
    if not payment:
        payment = Payment(
            order_id=order.id,
            transaction_id=f"TXN-PI-{random.randint(10000000, 99999999)}",
            amount=order.total_amount,
            payment_method=req.payment_method,
            payment_status="Pending",
            paid_at=datetime.utcnow()
        )
        db.add(payment)
        db.commit()
        db.refresh(payment)

    return {
        "success": True,
        "gateway_order_id": gateway_order_id,
        "amount": amount_in_paise,
        "amount_in_rupees": order.total_amount,
        "currency": "INR",
        "key_id": "rzp_live_pharmintel_secure",
        "order_number": order.order_number,
        "payment_id": payment.id,
        "transaction_id": payment.transaction_id,
        "payment_method": req.payment_method,
        "customer": {
            "name": order.patient_name or order.customer.full_name,
            "email": order.customer.email,
            "contact": order.contact_phone
        }
    }

@router.post("/verify")
def verify_payment(
    req: VerifyPaymentRequest,
    db: Session = Depends(get_db),
    user_payload: dict = Depends(get_current_user_payload)
):
    user_id = int(user_payload.get("sub"))
    order = db.query(Order).filter(Order.id == req.order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.customer_id != user_id:
        raise HTTPException(status_code=403, detail="Unauthorized")

    payment = db.query(Payment).filter(Payment.order_id == order.id).first()
    if not payment:
        payment = Payment(
            order_id=order.id,
            transaction_id=req.gateway_payment_id or f"TXN-{random.randint(10000000, 99999999)}",
            amount=order.total_amount,
            payment_method=req.payment_method or "UPI / Online",
            payment_status="Completed",
            paid_at=datetime.utcnow()
        )
        db.add(payment)
    else:
        payment.payment_status = "Completed"
        payment.paid_at = datetime.utcnow()
        if req.gateway_payment_id:
            payment.transaction_id = req.gateway_payment_id

    order.payment_status = "Completed"
    order.payment_method = req.payment_method or order.payment_method

    # If the order does NOT require prescription verification and was pending, advance to Preparing
    if order.status == "Pending":
        OrderService.update_order_status(db, order.id, "Preparing", "Payment completed successfully; order queued for dispensing.")
    elif order.status == "Prescription Verification":
        # Keep under review until pharmacist approves
        pass

    db.commit()
    return {
        "success": True,
        "message": "Payment verified and processed successfully",
        "order_id": order.id,
        "order_number": order.order_number,
        "payment_status": order.payment_status,
        "order_status": order.status,
        "transaction_id": payment.transaction_id
    }

@router.get("/order/{order_id}")
def get_payment_details(
    order_id: int,
    db: Session = Depends(get_db),
    user_payload: dict = Depends(get_current_user_payload)
):
    payment = db.query(Payment).filter(Payment.order_id == order_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment record not found")
    return {
        "id": payment.id,
        "order_id": payment.order_id,
        "transaction_id": payment.transaction_id,
        "amount": payment.amount,
        "payment_method": payment.payment_method,
        "payment_status": payment.payment_status,
        "paid_at": payment.paid_at
    }
