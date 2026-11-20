from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.utils.security import get_current_user_payload, require_role
from app.services.order_service import OrderService
from app.models.order import Order, OrderItem
from app.schemas.order import OrderCreateRequest, OrderResponse, OrderStatusUpdate

router = APIRouter(prefix="/orders", tags=["Orders & Delivery"])

@router.post("", response_model=dict)
def create_order(
    req: OrderCreateRequest,
    db: Session = Depends(get_db),
    user_payload: dict = Depends(get_current_user_payload)
):
    user_id = int(user_payload.get("sub"))
    order = OrderService.create_order(db, user_id, req)
    return {
        "message": "Order placed successfully",
        "order_id": order.id,
        "order_number": order.order_number,
        "status": order.status,
        "total_amount": order.total_amount,
        "requires_prescription_verification": (order.status == "Prescription Verification")
    }

@router.get("/my-orders")
def get_user_orders(
    db: Session = Depends(get_db),
    user_payload: dict = Depends(get_current_user_payload)
):
    user_id = int(user_payload.get("sub"))
    orders = db.query(Order).filter(Order.customer_id == user_id).order_by(Order.created_at.desc()).all()
    results = []
    for ord in orders:
        items = [{
            "id": itm.id,
            "medicine_name": itm.medicine.brand_name,
            "strength": itm.medicine.strength,
            "dosage_form": itm.medicine.dosage_form,
            "quantity": itm.quantity,
            "unit_price": itm.unit_price,
            "total_price": itm.total_price
        } for itm in ord.items]

        delivery_info = {
            "tracking_number": ord.delivery.tracking_number,
            "courier": ord.delivery.courier_name,
            "current_status": ord.delivery.current_status,
            "driver_name": ord.delivery.driver_name,
            "driver_phone": ord.delivery.driver_phone,
            "estimated_time": ord.delivery.estimated_delivery_time
        } if ord.delivery else None

        results.append({
            "id": ord.id,
            "order_number": ord.order_number,
            "pharmacy_id": ord.pharmacy_id,
            "pharmacy_name": ord.pharmacy.name,
            "prescription_id": ord.prescription_id,
            "status": ord.status,
            "subtotal": ord.subtotal,
            "tax_amount": ord.tax_amount,
            "delivery_fee": ord.delivery_fee,
            "total_amount": ord.total_amount,
            "payment_method": ord.payment_method,
            "payment_status": ord.payment_status,
            "patient_name": ord.patient_name,
            "delivery_address": ord.delivery_address,
            "created_at": ord.created_at,
            "items": items,
            "delivery": delivery_info
        })
    return results

@router.get("/pharmacy/{pharmacy_id}")
def get_pharmacy_orders(
    pharmacy_id: int,
    status_filter: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    user_payload: dict = Depends(require_role(["pharmacist", "pharmacy_admin", "platform_admin"]))
):
    q = db.query(Order).filter(Order.pharmacy_id == pharmacy_id)
    if status_filter:
        q = q.filter(Order.status == status_filter)

    orders = q.order_by(Order.created_at.desc()).all()
    results = []
    for ord in orders:
        results.append({
            "id": ord.id,
            "order_number": ord.order_number,
            "customer_name": ord.customer.full_name,
            "customer_phone": ord.contact_phone,
            "delivery_address": ord.delivery_address,
            "status": ord.status,
            "total_amount": ord.total_amount,
            "payment_status": ord.payment_status,
            "payment_method": ord.payment_method,
            "prescription_id": ord.prescription_id,
            "created_at": ord.created_at,
            "items_count": len(ord.items),
            "items": [{
                "name": itm.medicine.brand_name,
                "generic": itm.medicine.generic_name,
                "quantity": itm.quantity,
                "total": itm.total_price
            } for itm in ord.items]
        })
    return results

@router.patch("/{order_id}/status")
def update_order_status(
    order_id: int,
    req: OrderStatusUpdate,
    db: Session = Depends(get_db),
    user_payload: dict = Depends(require_role(["pharmacist", "pharmacy_admin", "platform_admin"]))
):
    order = OrderService.update_order_status(db, order_id, req.status, req.notes)
    return {
        "message": f"Order status updated to {order.status}",
        "order_id": order.id,
        "new_status": order.status
    }

@router.get("/{order_id}")
def get_order_by_id(
    order_id: int,
    db: Session = Depends(get_db),
    user_payload: dict = Depends(get_current_user_payload)
):
    user_id = int(user_payload.get("sub"))
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    items = [{
        "id": itm.id,
        "medicine_id": itm.medicine_id,
        "medicine_name": itm.medicine.brand_name if itm.medicine else "Medicine",
        "generic_name": itm.medicine.generic_name if itm.medicine else "",
        "strength": itm.medicine.strength if itm.medicine else "",
        "dosage_form": itm.medicine.dosage_form if itm.medicine else "",
        "quantity": itm.quantity,
        "unit_price": itm.unit_price,
        "mrp": itm.mrp,
        "gst_rate": itm.gst_rate,
        "total_price": itm.total_price,
        "requires_prescription": itm.medicine.requires_prescription if itm.medicine else False
    } for itm in order.items]

    delivery_info = {
        "tracking_number": order.delivery.tracking_number,
        "courier": order.delivery.courier_name,
        "current_status": order.delivery.current_status,
        "driver_name": order.delivery.driver_name,
        "driver_phone": order.delivery.driver_phone,
        "estimated_time": order.delivery.estimated_delivery_time,
        "dispatched_at": order.delivery.dispatched_at,
        "delivered_at": order.delivery.delivered_at
    } if order.delivery else None

    return {
        "id": order.id,
        "order_number": order.order_number,
        "customer_id": order.customer_id,
        "pharmacy_id": order.pharmacy_id,
        "pharmacy_name": order.pharmacy.name if order.pharmacy else "Apollo Care Community Pharmacy",
        "prescription_id": order.prescription_id,
        "status": order.status,
        "subtotal": order.subtotal,
        "tax_amount": order.tax_amount,
        "delivery_fee": order.delivery_fee,
        "total_amount": order.total_amount,
        "payment_method": order.payment_method,
        "payment_status": order.payment_status,
        "patient_name": order.patient_name,
        "delivery_address": order.delivery_address,
        "contact_phone": order.contact_phone,
        "delivery_type": order.delivery_type,
        "special_instructions": order.special_instructions,
        "created_at": order.created_at,
        "items": items,
        "delivery": delivery_info
    }

@router.post("/{order_id}/cancel")
def cancel_order(
    order_id: int,
    reason: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    user_payload: dict = Depends(get_current_user_payload)
):
    user_id = int(user_payload.get("sub"))
    order = OrderService.cancel_order(db, order_id, user_id, reason)
    return {
        "message": f"Order #{order.order_number} cancelled successfully",
        "order_id": order.id,
        "order_status": order.status,
        "payment_status": order.payment_status
    }

@router.post("/{order_id}/reorder")
def reorder_items(
    order_id: int,
    db: Session = Depends(get_db),
    user_payload: dict = Depends(get_current_user_payload)
):
    user_id = int(user_payload.get("sub"))
    return OrderService.reorder(db, order_id, user_id)

@router.get("/{order_id}/invoice")
def get_order_invoice(
    order_id: int,
    db: Session = Depends(get_db),
    user_payload: dict = Depends(get_current_user_payload)
):
    return OrderService.generate_invoice(db, order_id)

@router.get("/{order_id}/tracking")
def get_order_tracking(
    order_id: int,
    db: Session = Depends(get_db),
    user_payload: dict = Depends(get_current_user_payload)
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order or not order.delivery:
        raise HTTPException(status_code=404, detail="Order or delivery tracking not found")

    return {
        "order_number": order.order_number,
        "tracking_number": order.delivery.tracking_number,
        "courier_name": order.delivery.courier_name,
        "current_status": order.delivery.current_status,
        "order_status": order.status,
        "estimated_delivery_time": order.delivery.estimated_delivery_time,
        "driver_name": order.delivery.driver_name,
        "driver_phone": order.delivery.driver_phone,
        "dispatched_at": order.delivery.dispatched_at,
        "delivered_at": order.delivery.delivered_at
    }
