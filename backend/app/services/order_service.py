import random
import string
from sqlalchemy.orm import Session
from datetime import datetime
from fastapi import HTTPException
from typing import List, Dict, Any, Optional

from app.models.order import Order, OrderItem, Payment, Delivery
from app.models.medicine import Medicine
from app.models.prescription import Prescription
from app.models.pharmacy import Pharmacy
from app.models.inventory import PharmacyInventory, MedicineBatch, StockAuditLog
from app.schemas.order import OrderCreateRequest

class OrderService:
    @staticmethod
    def generate_order_number() -> str:
        random_suffix = ''.join(random.choices(string.digits, k=5))
        return f"PI-ORD-{datetime.utcnow().strftime('%Y%m')}-{random_suffix}"

    @staticmethod
    def generate_tracking_number() -> str:
        random_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        return f"TRK-{random_suffix}"

    @classmethod
    def create_order(cls, db: Session, customer_id: int, order_data: OrderCreateRequest) -> Order:
        pharmacy = db.query(Pharmacy).filter(Pharmacy.id == order_data.pharmacy_id).first()
        if not pharmacy:
            raise HTTPException(status_code=404, detail="Selected pharmacy does not exist")

        # Check prescription requirements for items
        requires_rx = False
        med_ids = [item.medicine_id for item in order_data.items]
        medicines = db.query(Medicine).filter(Medicine.id.in_(med_ids)).all()
        med_dict = {m.id: m for m in medicines}

        for item in order_data.items:
            m = med_dict.get(item.medicine_id)
            if not m:
                raise HTTPException(status_code=400, detail=f"Invalid medicine ID: {item.medicine_id}")
            if m.requires_prescription or m.prescription_classification in ["Rx", "Schedule H", "Schedule H1", "Schedule X"]:
                requires_rx = True

        # Enforcement of Indian Pharmacy Regulations:
        # Schedule H / Rx medicines CANNOT be ordered without an uploaded prescription
        if requires_rx and not order_data.prescription_id:
            raise HTTPException(
                status_code=400,
                detail="One or more selected medicines require a valid doctor prescription (Schedule H / Rx regulations). Please attach an uploaded prescription."
            )

        # Check if attached prescription is valid
        if order_data.prescription_id:
            rx = db.query(Prescription).filter(
                Prescription.id == order_data.prescription_id,
                Prescription.customer_id == customer_id
            ).first()
            if not rx:
                raise HTTPException(status_code=400, detail="Invalid prescription specified")

        # Initial status: if requires_rx and not verified by pharmacist yet -> 'Prescription Verification'
        initial_status = "Prescription Verification" if requires_rx else "Pending"

        # Calculate totals
        subtotal = 0.0
        tax_total = 0.0
        delivery_fee = 40.0 if order_data.delivery_type == "Home Delivery" else 0.0

        order_items_to_create = []
        for item in order_data.items:
            m = med_dict[item.medicine_id]
            price = m.base_mrp
            gst_rate = 12.0
            item_total = price * item.quantity

            # Find valid batch
            inv = db.query(PharmacyInventory).filter(
                PharmacyInventory.pharmacy_id == order_data.pharmacy_id,
                PharmacyInventory.medicine_id == m.id
            ).first()

            batch_id = None
            if inv:
                valid_batch = db.query(MedicineBatch).filter(
                    MedicineBatch.inventory_id == inv.id,
                    MedicineBatch.quantity >= item.quantity,
                    MedicineBatch.is_recalled == False
                ).first()
                if valid_batch:
                    batch_id = valid_batch.id

            order_items_to_create.append({
                "medicine_id": m.id,
                "batch_id": batch_id,
                "quantity": item.quantity,
                "unit_price": price,
                "mrp": price,
                "discount": 0.0,
                "gst_rate": gst_rate,
                "total_price": item_total
            })

            subtotal += item_total
            tax_total += (item_total * gst_rate / 100.0)

        total_amount = round(subtotal + tax_total + delivery_fee, 2)

        order = Order(
            order_number=cls.generate_order_number(),
            customer_id=customer_id,
            pharmacy_id=order_data.pharmacy_id,
            prescription_id=order_data.prescription_id,
            status=initial_status,
            subtotal=round(subtotal, 2),
            tax_amount=round(tax_total, 2),
            delivery_fee=delivery_fee,
            total_amount=total_amount,
            payment_method=order_data.payment_method,
            payment_status="Completed" if order_data.payment_method == "UPI / Online" else "Pending",
            patient_name=order_data.patient_name,
            delivery_address=order_data.delivery_address,
            contact_phone=order_data.contact_phone,
            delivery_type=order_data.delivery_type,
            special_instructions=order_data.special_instructions
        )
        db.add(order)
        db.commit()
        db.refresh(order)

        # Add items
        for oi_data in order_items_to_create:
            oi = OrderItem(
                order_id=order.id,
                **oi_data
            )
            db.add(oi)

        # Create delivery tracking entry
        delivery = Delivery(
            order_id=order.id,
            tracking_number=cls.generate_tracking_number(),
            courier_name="PharmIntel Express Healthcare Logistics",
            current_status="Prescription Under Review" if requires_rx else "Order Assigned",
            estimated_delivery_time="Same Day (Within 2 Hours)" if order_data.delivery_type == "Home Delivery" else "Ready in 30 Mins",
            driver_name="Suresh Kumar (Verified Logistics Partner)",
            driver_phone="+91 98450 12345"
        )
        db.add(delivery)

        # Create payment record
        payment = Payment(
            order_id=order.id,
            transaction_id=f"TXN-{random.randint(10000000, 99999999)}",
            amount=total_amount,
            payment_method=order_data.payment_method,
            payment_status="Completed" if order_data.payment_method == "UPI / Online" else "Pending"
        )
        db.add(payment)

        db.commit()
        db.refresh(order)
        return order

    @classmethod
    def cancel_order(cls, db: Session, order_id: int, user_id: int, reason: Optional[str] = None) -> Order:
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        # Must belong to user (or authorized staff)
        if order.customer_id != user_id:
            # Check if staff
            from app.models.user import User
            user = db.query(User).filter(User.id == user_id).first()
            if not user or user.role not in ["pharmacist", "pharmacy_admin", "platform_admin"]:
                raise HTTPException(status_code=403, detail="Unauthorized to cancel this order")

        if order.status in ["Dispatched", "Delivered"]:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot cancel order #{order.order_number} as it has already been {order.status.lower()}."
            )

        if order.status == "Cancelled":
            return order

        # If inventory was previously deducted in 'Preparing' status, restore it
        if order.status in ["Preparing", "Ready for Pickup", "Approved"]:
            for item in order.items:
                inv = db.query(PharmacyInventory).filter(
                    PharmacyInventory.pharmacy_id == order.pharmacy_id,
                    PharmacyInventory.medicine_id == item.medicine_id
                ).first()
                if inv:
                    inv.stock_quantity += item.quantity
                    if item.batch_id:
                        batch = db.query(MedicineBatch).filter(MedicineBatch.id == item.batch_id).first()
                        if batch:
                            batch.quantity += item.quantity

                    log = StockAuditLog(
                        pharmacy_id=order.pharmacy_id,
                        medicine_id=item.medicine_id,
                        batch_id=item.batch_id,
                        action="STOCK_IN",
                        quantity_changed=item.quantity,
                        balance_quantity=inv.stock_quantity,
                        performed_by_user_id=user_id,
                        reason=f"Restocked from cancelled order: {order.order_number}. Reason: {reason or 'Customer request'}"
                    )
                    db.add(log)

        order.status = "Cancelled"
        if order.payment_status == "Completed":
            order.payment_status = "Refund Initiated"
        else:
            order.payment_status = "Cancelled"

        if order.delivery:
            order.delivery.current_status = "Order Cancelled"

        db.commit()
        db.refresh(order)
        return order

    @classmethod
    def reorder(cls, db: Session, order_id: int, user_id: int) -> Dict[str, Any]:
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        from app.services.cart_service import CartService
        cart = CartService.get_or_create_cart(db, user_id=user_id)

        items_reordered = []
        for itm in order.items:
            CartService.add_to_cart(
                db,
                user_id=user_id,
                session_id=None,
                medicine_id=itm.medicine_id,
                quantity=itm.quantity,
                pharmacy_id=order.pharmacy_id
            )
            items_reordered.append({
                "medicine_id": itm.medicine_id,
                "medicine_name": itm.medicine.brand_name if itm.medicine else "Medicine",
                "quantity": itm.quantity
            })

        return {
            "message": f"Successfully re-added {len(items_reordered)} items to your cart",
            "items": items_reordered,
            "cart": CartService.get_cart_details(db, user_id=user_id)
        }

    @classmethod
    def generate_invoice(cls, db: Session, order_id: int) -> Dict[str, Any]:
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        pharmacy = order.pharmacy or db.query(Pharmacy).filter(Pharmacy.id == order.pharmacy_id).first()
        patient_display = order.patient_name or order.customer.full_name or "Patient name not provided"

        # Build line items
        items_detail = []
        cgst_total = 0.0
        sgst_total = 0.0

        for idx, itm in enumerate(order.items, 1):
            med = itm.medicine
            batch = itm.batch
            half_gst = itm.gst_rate / 2.0
            taxable = round(itm.total_price / (1.0 + (itm.gst_rate / 100.0)), 2)
            gst_amt = round(itm.total_price - taxable, 2)
            cgst = round(gst_amt / 2.0, 2)
            sgst = round(gst_amt / 2.0, 2)
            cgst_total += cgst
            sgst_total += sgst

            items_detail.append({
                "sl_no": idx,
                "brand_name": med.brand_name if med else "Medicine",
                "generic_name": med.generic_name if med else "",
                "dosage_form": med.dosage_form if med else "",
                "strength": med.strength if med else "",
                "hsn_code": "30049099",
                "batch_number": batch.batch_number if batch else f"BAT-{idx:03d}",
                "expiry_date": batch.expiry_date if batch else "2027-12-31",
                "quantity": itm.quantity,
                "mrp": itm.mrp,
                "unit_price": itm.unit_price,
                "discount": itm.discount,
                "taxable_value": taxable,
                "gst_rate": itm.gst_rate,
                "cgst": cgst,
                "sgst": sgst,
                "total_price": itm.total_price,
                "requires_prescription": med.requires_prescription if med else False
            })

        invoice_number = f"INV-PI-{order.created_at.strftime('%Y%m')}-{order.id:04d}"

        # HTML template for printable A4 tax invoice
        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Tax Invoice - {invoice_number}</title>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; margin: 0; padding: 24px; color: #1e293b; background: #fff; font-size: 12px; line-height: 1.5; }}
  .invoice-box {{ max-width: 800px; margin: auto; border: 1px solid #e2e8f0; border-radius: 8px; padding: 28px; }}
  .header {{ display: flex; justify-content: space-between; align-items: flex-start; border-bottom: 2px solid #2166F5; padding-bottom: 16px; margin-bottom: 20px; }}
  .brand {{ font-size: 22px; font-weight: 900; color: #2166F5; letter-spacing: -0.5px; }}
  .brand span {{ color: #10B981; }}
  .badge {{ display: inline-block; background: #EFF6FF; color: #2166F5; font-weight: 700; padding: 3px 8px; border-radius: 4px; font-size: 10px; border: 1px solid #BFDBFE; }}
  .two-col {{ display: flex; justify-content: space-between; margin-bottom: 20px; }}
  .col {{ width: 48%; }}
  .col h4 {{ margin: 0 0 6px 0; font-size: 11px; text-transform: uppercase; color: #64748b; letter-spacing: 0.5px; }}
  .col p {{ margin: 2px 0; color: #334155; }}
  table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; }}
  th {{ background: #f8fafc; color: #475569; font-weight: 700; text-align: left; padding: 8px 10px; border-bottom: 1px solid #cbd5e1; font-size: 11px; }}
  td {{ padding: 8px 10px; border-bottom: 1px solid #f1f5f9; font-size: 11px; }}
  .text-right {{ text-align: right; }}
  .text-center {{ text-align: center; }}
  .totals {{ width: 300px; margin-left: auto; margin-bottom: 24px; }}
  .totals-row {{ display: flex; justify-content: space-between; padding: 4px 0; }}
  .totals-row.grand {{ border-top: 2px solid #e2e8f0; border-bottom: 2px solid #e2e8f0; font-weight: 800; font-size: 14px; color: #0f172a; padding: 8px 0; margin-top: 6px; }}
  .footer {{ border-top: 1px solid #e2e8f0; padding-top: 14px; font-size: 10px; color: #64748b; text-align: center; }}
  @media print {{ body {{ padding: 0; }} .invoice-box {{ border: none; padding: 0; }} }}
</style>
</head>
<body>
<div class="invoice-box">
  <div class="header">
    <div>
      <div class="brand">PHARM<span>INTEL</span></div>
      <div style="font-size: 11px; color: #64748b; margin-top: 2px;">Licensed Online Healthcare Platform & E-Pharmacy</div>
      <div style="font-size: 11px; color: #334155; margin-top: 4px;"><strong>Fulfilling Pharmacy:</strong> {pharmacy.name if pharmacy else "Apollo Care Community Pharmacy"}</div>
      <div style="font-size: 10px; color: #64748b;">License No: {pharmacy.license_number if pharmacy else "DL-20B-KA-45892"} | GSTIN: {getattr(pharmacy, 'gst_number', '29AABCA1234F1Z5')}</div>
      <div style="font-size: 10px; color: #64748b;">{pharmacy.address if pharmacy else "Sarjapur Road, Bellandur"}, {pharmacy.city if pharmacy else "Bengaluru"} - {getattr(pharmacy, 'postal_code', '560103')}</div>
    </div>
    <div style="text-align: right;">
      <div class="badge">OFFICIAL GST TAX INVOICE</div>
      <div style="font-size: 15px; font-weight: 800; color: #0f172a; margin-top: 6px;">{invoice_number}</div>
      <div style="font-size: 11px; color: #64748b;">Date: {order.created_at.strftime('%d-%b-%Y %I:%M %p')}</div>
      <div style="font-size: 11px; color: #64748b;">Order Ref: <strong>{order.order_number}</strong></div>
      <div style="font-size: 11px; color: #059669; font-weight: 700; margin-top: 4px;">Status: {order.status}</div>
    </div>
  </div>

  <div class="two-col">
    <div class="col">
      <h4>Bill To / Patient Details:</h4>
      <p style="font-weight: 700; font-size: 13px; color: #0f172a;">{patient_display}</p>
      <p>Contact Phone: {order.contact_phone}</p>
      <p>Delivery Address: {order.delivery_address}</p>
      <p>Delivery Type: {order.delivery_type}</p>
    </div>
    <div class="col" style="text-align: right;">
      <h4>Payment & Dispatch Details:</h4>
      <p>Payment Mode: <strong>{order.payment_method}</strong></p>
      <p>Payment Status: <strong>{order.payment_status}</strong></p>
      <p>Courier: {order.delivery.courier_name if order.delivery else 'PharmIntel Express Logistics'}</p>
      <p>Tracking AWB: <strong>{order.delivery.tracking_number if order.delivery else 'N/A'}</strong></p>
    </div>
  </div>

  <table>
    <thead>
      <tr>
        <th class="text-center" style="width: 30px;">#</th>
        <th>Medicine & Strength</th>
        <th>Batch / Expiry</th>
        <th class="text-center">HSN</th>
        <th class="text-right">Qty</th>
        <th class="text-right">MRP (₹)</th>
        <th class="text-right">Rate (₹)</th>
        <th class="text-right">GST %</th>
        <th class="text-right">Amount (₹)</th>
      </tr>
    </thead>
    <tbody>
      {''.join(f'''
      <tr>
        <td class="text-center">{itm['sl_no']}</td>
        <td>
          <strong>{itm['brand_name']}</strong>
          <div style="font-size: 10px; color: #64748b;">{itm['generic_name']} • {itm['strength']}</div>
        </td>
        <td style="font-size: 10px; font-family: monospace;">{itm['batch_number']}<br><span style="color:#64748b;">Exp: {itm['expiry_date']}</span></td>
        <td class="text-center" style="font-size: 10px;">{itm['hsn_code']}</td>
        <td class="text-right font-bold">{itm['quantity']}</td>
        <td class="text-right" style="color: #64748b;">{itm['mrp']:.2f}</td>
        <td class="text-right">{itm['unit_price']:.2f}</td>
        <td class="text-right">{itm['gst_rate']:.1f}%</td>
        <td class="text-right" style="font-weight: 700;">{itm['total_price']:.2f}</td>
      </tr>
      ''' for itm in items_detail)}
    </tbody>
  </table>

  <div class="totals">
    <div class="totals-row">
      <span>Subtotal (Medicines):</span>
      <span>₹{order.subtotal:.2f}</span>
    </div>
    <div class="totals-row">
      <span>CGST:</span>
      <span>₹{cgst_total:.2f}</span>
    </div>
    <div class="totals-row">
      <span>SGST:</span>
      <span>₹{sgst_total:.2f}</span>
    </div>
    <div class="totals-row">
      <span>Total Tax (GST):</span>
      <span>₹{order.tax_amount:.2f}</span>
    </div>
    <div class="totals-row">
      <span>Delivery & Handling:</span>
      <span>{'FREE' if order.delivery_fee == 0 else f'₹{order.delivery_fee:.2f}'}</span>
    </div>
    <div class="totals-row grand">
      <span>Total Payable Amount:</span>
      <span style="color: #2166F5;">₹{order.total_amount:.2f}</span>
    </div>
  </div>

  <div class="footer">
    <p><strong>Declaration:</strong> This is an electronically generated tax invoice issued in compliance with the Drugs and Cosmetics Rules, 1945 and the Pharmacy Practice Regulations. All medicines supplied were stored, handled, and verified under regulated conditions by a registered pharmacist.</p>
    <p style="margin-top: 4px;">For clinical assistance or order queries, consult PharmIntel 24x7 Live Support or call toll-free 1800-PHARM-INTEL.</p>
  </div>
</div>
</body>
</html>
"""

        return {
            "invoice_number": invoice_number,
            "order_number": order.order_number,
            "created_at": order.created_at,
            "patient_name": patient_display,
            "pharmacy": {
                "name": pharmacy.name if pharmacy else "Apollo Care Community Pharmacy",
                "license_number": pharmacy.license_number if pharmacy else "DL-20B-KA-45892",
                "address": pharmacy.address if pharmacy else "Sarjapur Road, Bellandur, Bengaluru",
                "phone": pharmacy.phone if pharmacy else "+91 80 2844 1122"
            },
            "items": items_detail,
            "subtotal": order.subtotal,
            "cgst": round(cgst_total, 2),
            "sgst": round(sgst_total, 2),
            "tax_amount": order.tax_amount,
            "delivery_fee": order.delivery_fee,
            "total_amount": order.total_amount,
            "payment_method": order.payment_method,
            "payment_status": order.payment_status,
            "html": html_content
        }


    @classmethod
    def update_order_status(cls, db: Session, order_id: int, new_status: str, notes: Optional[str] = None) -> Order:
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        valid_statuses = [
            "Pending", "Prescription Verification", "Approved", "Rejected",
            "Preparing", "Ready for Pickup", "Dispatched", "Delivered", "Cancelled"
        ]
        if new_status not in valid_statuses:
            raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of {valid_statuses}")

        order.status = new_status
        if order.delivery:
            if new_status == "Approved":
                order.delivery.current_status = "Approved - In Preparation"
            elif new_status == "Preparing":
                order.delivery.current_status = "Dispensing & Packing"
            elif new_status == "Dispatched":
                order.delivery.current_status = "Out for Delivery"
                order.delivery.dispatched_at = datetime.utcnow()
            elif new_status == "Delivered":
                order.delivery.current_status = "Delivered to Customer"
                order.delivery.delivered_at = datetime.utcnow()
                order.payment_status = "Completed"

        # If order approved and preparing, deduct inventory with audit log
        if new_status == "Preparing":
            for item in order.items:
                inv = db.query(PharmacyInventory).filter(
                    PharmacyInventory.pharmacy_id == order.pharmacy_id,
                    PharmacyInventory.medicine_id == item.medicine_id
                ).first()
                if inv and inv.stock_quantity >= item.quantity:
                    inv.stock_quantity -= item.quantity
                    if item.batch_id:
                        batch = db.query(MedicineBatch).filter(MedicineBatch.id == item.batch_id).first()
                        if batch and batch.quantity >= item.quantity:
                            batch.quantity -= item.quantity

                    log = StockAuditLog(
                        pharmacy_id=order.pharmacy_id,
                        medicine_id=item.medicine_id,
                        batch_id=item.batch_id,
                        action="STOCK_OUT_SALE",
                        quantity_changed=-item.quantity,
                        balance_quantity=inv.stock_quantity,
                        performed_by_user_id=order.customer_id,
                        reason=f"Dispensed for order: {order.order_number}"
                    )
                    db.add(log)

        db.commit()
        db.refresh(order)
        return order

    @classmethod
    def cancel_order(cls, db: Session, order_id: int, user_id: int, reason: Optional[str] = None) -> Order:
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        # Must belong to user (or authorized staff)
        if order.customer_id != user_id:
            # Check if staff
            from app.models.user import User
            user = db.query(User).filter(User.id == user_id).first()
            if not user or user.role not in ["pharmacist", "pharmacy_admin", "platform_admin"]:
                raise HTTPException(status_code=403, detail="Unauthorized to cancel this order")

        if order.status in ["Dispatched", "Delivered"]:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot cancel order #{order.order_number} as it has already been {order.status.lower()}."
            )

        if order.status == "Cancelled":
            return order

        # If inventory was previously deducted in 'Preparing' status, restore it
        if order.status in ["Preparing", "Ready for Pickup", "Approved"]:
            for item in order.items:
                inv = db.query(PharmacyInventory).filter(
                    PharmacyInventory.pharmacy_id == order.pharmacy_id,
                    PharmacyInventory.medicine_id == item.medicine_id
                ).first()
                if inv:
                    inv.stock_quantity += item.quantity
                    if item.batch_id:
                        batch = db.query(MedicineBatch).filter(MedicineBatch.id == item.batch_id).first()
                        if batch:
                            batch.quantity += item.quantity

                    log = StockAuditLog(
                        pharmacy_id=order.pharmacy_id,
                        medicine_id=item.medicine_id,
                        batch_id=item.batch_id,
                        action="STOCK_IN",
                        quantity_changed=item.quantity,
                        balance_quantity=inv.stock_quantity,
                        performed_by_user_id=user_id,
                        reason=f"Restocked from cancelled order: {order.order_number}. Reason: {reason or 'Customer request'}"
                    )
                    db.add(log)

        order.status = "Cancelled"
        if order.payment_status == "Completed":
            order.payment_status = "Refund Initiated"
        else:
            order.payment_status = "Cancelled"

        if order.delivery:
            order.delivery.current_status = "Order Cancelled"

        db.commit()
        db.refresh(order)
        return order

    @classmethod
    def reorder(cls, db: Session, order_id: int, user_id: int) -> Dict[str, Any]:
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        from app.services.cart_service import CartService
        cart = CartService.get_or_create_cart(db, user_id=user_id)

        items_reordered = []
        for itm in order.items:
            CartService.add_to_cart(
                db,
                user_id=user_id,
                session_id=None,
                medicine_id=itm.medicine_id,
                quantity=itm.quantity,
                pharmacy_id=order.pharmacy_id
            )
            items_reordered.append({
                "medicine_id": itm.medicine_id,
                "medicine_name": itm.medicine.brand_name if itm.medicine else "Medicine",
                "quantity": itm.quantity
            })

        return {
            "message": f"Successfully re-added {len(items_reordered)} items to your cart",
            "items": items_reordered,
            "cart": CartService.get_cart_details(db, user_id=user_id)
        }

    @classmethod
    def generate_invoice(cls, db: Session, order_id: int) -> Dict[str, Any]:
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        pharmacy = order.pharmacy or db.query(Pharmacy).filter(Pharmacy.id == order.pharmacy_id).first()
        patient_display = order.patient_name or order.customer.full_name or "Patient name not provided"

        # Build line items
        items_detail = []
        cgst_total = 0.0
        sgst_total = 0.0

        for idx, itm in enumerate(order.items, 1):
            med = itm.medicine
            batch = itm.batch
            half_gst = itm.gst_rate / 2.0
            taxable = round(itm.total_price / (1.0 + (itm.gst_rate / 100.0)), 2)
            gst_amt = round(itm.total_price - taxable, 2)
            cgst = round(gst_amt / 2.0, 2)
            sgst = round(gst_amt / 2.0, 2)
            cgst_total += cgst
            sgst_total += sgst

            items_detail.append({
                "sl_no": idx,
                "brand_name": med.brand_name if med else "Medicine",
                "generic_name": med.generic_name if med else "",
                "dosage_form": med.dosage_form if med else "",
                "strength": med.strength if med else "",
                "hsn_code": "30049099",
                "batch_number": batch.batch_number if batch else f"BAT-{idx:03d}",
                "expiry_date": batch.expiry_date if batch else "2027-12-31",
                "quantity": itm.quantity,
                "mrp": itm.mrp,
                "unit_price": itm.unit_price,
                "discount": itm.discount,
                "taxable_value": taxable,
                "gst_rate": itm.gst_rate,
                "cgst": cgst,
                "sgst": sgst,
                "total_price": itm.total_price,
                "requires_prescription": med.requires_prescription if med else False
            })

        invoice_number = f"INV-PI-{order.created_at.strftime('%Y%m')}-{order.id:04d}"

        # HTML template for printable A4 tax invoice
        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Tax Invoice - {invoice_number}</title>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; margin: 0; padding: 24px; color: #1e293b; background: #fff; font-size: 12px; line-height: 1.5; }}
  .invoice-box {{ max-width: 800px; margin: auto; border: 1px solid #e2e8f0; border-radius: 8px; padding: 28px; }}
  .header {{ display: flex; justify-content: space-between; align-items: flex-start; border-bottom: 2px solid #2166F5; padding-bottom: 16px; margin-bottom: 20px; }}
  .brand {{ font-size: 22px; font-weight: 900; color: #2166F5; letter-spacing: -0.5px; }}
  .brand span {{ color: #10B981; }}
  .badge {{ display: inline-block; background: #EFF6FF; color: #2166F5; font-weight: 700; padding: 3px 8px; border-radius: 4px; font-size: 10px; border: 1px solid #BFDBFE; }}
  .two-col {{ display: flex; justify-content: space-between; margin-bottom: 20px; }}
  .col {{ width: 48%; }}
  .col h4 {{ margin: 0 0 6px 0; font-size: 11px; text-transform: uppercase; color: #64748b; letter-spacing: 0.5px; }}
  .col p {{ margin: 2px 0; color: #334155; }}
  table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; }}
  th {{ background: #f8fafc; color: #475569; font-weight: 700; text-align: left; padding: 8px 10px; border-bottom: 1px solid #cbd5e1; font-size: 11px; }}
  td {{ padding: 8px 10px; border-bottom: 1px solid #f1f5f9; font-size: 11px; }}
  .text-right {{ text-align: right; }}
  .text-center {{ text-align: center; }}
  .totals {{ width: 300px; margin-left: auto; margin-bottom: 24px; }}
  .totals-row {{ display: flex; justify-content: space-between; padding: 4px 0; }}
  .totals-row.grand {{ border-top: 2px solid #e2e8f0; border-bottom: 2px solid #e2e8f0; font-weight: 800; font-size: 14px; color: #0f172a; padding: 8px 0; margin-top: 6px; }}
  .footer {{ border-top: 1px solid #e2e8f0; padding-top: 14px; font-size: 10px; color: #64748b; text-align: center; }}
  @media print {{ body {{ padding: 0; }} .invoice-box {{ border: none; padding: 0; }} }}
</style>
</head>
<body>
<div class="invoice-box">
  <div class="header">
    <div>
      <div class="brand">PHARM<span>INTEL</span></div>
      <div style="font-size: 11px; color: #64748b; margin-top: 2px;">Licensed Online Healthcare Platform & E-Pharmacy</div>
      <div style="font-size: 11px; color: #334155; margin-top: 4px;"><strong>Fulfilling Pharmacy:</strong> {pharmacy.name if pharmacy else "Apollo Care Community Pharmacy"}</div>
      <div style="font-size: 10px; color: #64748b;">License No: {pharmacy.license_number if pharmacy else "DL-20B-KA-45892"} | GSTIN: {getattr(pharmacy, 'gst_number', '29AABCA1234F1Z5')}</div>
      <div style="font-size: 10px; color: #64748b;">{pharmacy.address if pharmacy else "Sarjapur Road, Bellandur"}, {pharmacy.city if pharmacy else "Bengaluru"} - {getattr(pharmacy, 'postal_code', '560103')}</div>
    </div>
    <div style="text-align: right;">
      <div class="badge">OFFICIAL GST TAX INVOICE</div>
      <div style="font-size: 15px; font-weight: 800; color: #0f172a; margin-top: 6px;">{invoice_number}</div>
      <div style="font-size: 11px; color: #64748b;">Date: {order.created_at.strftime('%d-%b-%Y %I:%M %p')}</div>
      <div style="font-size: 11px; color: #64748b;">Order Ref: <strong>{order.order_number}</strong></div>
      <div style="font-size: 11px; color: #059669; font-weight: 700; margin-top: 4px;">Status: {order.status}</div>
    </div>
  </div>

  <div class="two-col">
    <div class="col">
      <h4>Bill To / Patient Details:</h4>
      <p style="font-weight: 700; font-size: 13px; color: #0f172a;">{patient_display}</p>
      <p>Contact Phone: {order.contact_phone}</p>
      <p>Delivery Address: {order.delivery_address}</p>
      <p>Delivery Type: {order.delivery_type}</p>
    </div>
    <div class="col" style="text-align: right;">
      <h4>Payment & Dispatch Details:</h4>
      <p>Payment Mode: <strong>{order.payment_method}</strong></p>
      <p>Payment Status: <strong>{order.payment_status}</strong></p>
      <p>Courier: {order.delivery.courier_name if order.delivery else 'PharmIntel Express Logistics'}</p>
      <p>Tracking AWB: <strong>{order.delivery.tracking_number if order.delivery else 'N/A'}</strong></p>
    </div>
  </div>

  <table>
    <thead>
      <tr>
        <th class="text-center" style="width: 30px;">#</th>
        <th>Medicine & Strength</th>
        <th>Batch / Expiry</th>
        <th class="text-center">HSN</th>
        <th class="text-right">Qty</th>
        <th class="text-right">MRP (₹)</th>
        <th class="text-right">Rate (₹)</th>
        <th class="text-right">GST %</th>
        <th class="text-right">Amount (₹)</th>
      </tr>
    </thead>
    <tbody>
      {''.join(f'''
      <tr>
        <td class="text-center">{itm['sl_no']}</td>
        <td>
          <strong>{itm['brand_name']}</strong>
          <div style="font-size: 10px; color: #64748b;">{itm['generic_name']} • {itm['strength']}</div>
        </td>
        <td style="font-size: 10px; font-family: monospace;">{itm['batch_number']}<br><span style="color:#64748b;">Exp: {itm['expiry_date']}</span></td>
        <td class="text-center" style="font-size: 10px;">{itm['hsn_code']}</td>
        <td class="text-right font-bold">{itm['quantity']}</td>
        <td class="text-right" style="color: #64748b;">{itm['mrp']:.2f}</td>
        <td class="text-right">{itm['unit_price']:.2f}</td>
        <td class="text-right">{itm['gst_rate']:.1f}%</td>
        <td class="text-right" style="font-weight: 700;">{itm['total_price']:.2f}</td>
      </tr>
      ''' for itm in items_detail)}
    </tbody>
  </table>

  <div class="totals">
    <div class="totals-row">
      <span>Subtotal (Medicines):</span>
      <span>₹{order.subtotal:.2f}</span>
    </div>
    <div class="totals-row">
      <span>CGST:</span>
      <span>₹{cgst_total:.2f}</span>
    </div>
    <div class="totals-row">
      <span>SGST:</span>
      <span>₹{sgst_total:.2f}</span>
    </div>
    <div class="totals-row">
      <span>Total Tax (GST):</span>
      <span>₹{order.tax_amount:.2f}</span>
    </div>
    <div class="totals-row">
      <span>Delivery & Handling:</span>
      <span>{'FREE' if order.delivery_fee == 0 else f'₹{order.delivery_fee:.2f}'}</span>
    </div>
    <div class="totals-row grand">
      <span>Total Payable Amount:</span>
      <span style="color: #2166F5;">₹{order.total_amount:.2f}</span>
    </div>
  </div>

  <div class="footer">
    <p><strong>Declaration:</strong> This is an electronically generated tax invoice issued in compliance with the Drugs and Cosmetics Rules, 1945 and the Pharmacy Practice Regulations. All medicines supplied were stored, handled, and verified under regulated conditions by a registered pharmacist.</p>
    <p style="margin-top: 4px;">For clinical assistance or order queries, consult PharmIntel 24x7 Live Support or call toll-free 1800-PHARM-INTEL.</p>
  </div>
</div>
</body>
</html>
"""

        return {
            "invoice_number": invoice_number,
            "order_number": order.order_number,
            "created_at": order.created_at,
            "patient_name": patient_display,
            "pharmacy": {
                "name": pharmacy.name if pharmacy else "Apollo Care Community Pharmacy",
                "license_number": pharmacy.license_number if pharmacy else "DL-20B-KA-45892",
                "address": pharmacy.address if pharmacy else "Sarjapur Road, Bellandur, Bengaluru",
                "phone": pharmacy.phone if pharmacy else "+91 80 2844 1122"
            },
            "items": items_detail,
            "subtotal": order.subtotal,
            "cgst": round(cgst_total, 2),
            "sgst": round(sgst_total, 2),
            "tax_amount": order.tax_amount,
            "delivery_fee": order.delivery_fee,
            "total_amount": order.total_amount,
            "payment_method": order.payment_method,
            "payment_status": order.payment_status,
            "html": html_content
        }

