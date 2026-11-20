from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session
from datetime import datetime
from app.database import get_db
from app.models.order import Order
from app.models.prescription import Prescription
from app.services.print_service import A4PrintService

router = APIRouter(prefix="/printing", tags=["Professional A4 Printing Engine"])

@router.get("/invoice/{order_id}/pdf")
def download_tax_invoice_pdf(order_id: int, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    pharmacy = order.pharmacy
    customer = order.customer

    invoice_data = {
        "pharmacy_name": pharmacy.name,
        "pharmacy_address": pharmacy.address,
        "pharmacy_phone": pharmacy.phone,
        "pharmacy_email": pharmacy.email,
        "pharmacy_license": pharmacy.license_number,
        "pharmacy_gst": pharmacy.gst_number or "29AAACA1234B1Z5",
        "invoice_number": f"INV-{order.order_number.replace('PI-ORD-', '')}",
        "invoice_date": order.created_at.strftime("%d-%m-%Y"),
        "order_number": order.order_number,
        "customer": {
            "name": customer.full_name,
            "phone": order.contact_phone,
            "address": order.delivery_address
        },
        "pharmacist_name": "Rajesh Nambiar, M.Pharm",
        "pharmacist_reg": "KSPC-REG-2015-88391",
        "subtotal": order.subtotal,
        "tax_amount": order.tax_amount,
        "delivery_fee": order.delivery_fee,
        "total_amount": order.total_amount,
        "items": [
            {
                "name": itm.medicine.brand_name,
                "composition": itm.medicine.composition,
                "batch_number": itm.batch.batch_number if itm.batch else "BT-88910",
                "expiry_date": itm.batch.expiry_date if itm.batch else "2027-08-30",
                "quantity": itm.quantity,
                "mrp": itm.mrp,
                "unit_price": itm.unit_price,
                "gst_rate": itm.gst_rate,
                "total_price": itm.total_price
            }
            for itm in order.items
        ]
    }

    pdf_buffer = A4PrintService.generate_tax_invoice_pdf(invoice_data)
    headers = {
        "Content-Disposition": f"attachment; filename=Pharmacy_Tax_Invoice_{order.order_number}.pdf"
    }
    return Response(content=pdf_buffer.getvalue(), media_type="application/pdf", headers=headers)

@router.get("/invoice/{order_id}/data")
def get_invoice_print_data(order_id: int, db: Session = Depends(get_db)):
    """
    Returns structured data for the dedicated React A4 print template.
    """
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    pharmacy = order.pharmacy
    customer = order.customer

    return {
        "pharmacy_name": pharmacy.name,
        "pharmacy_address": pharmacy.address,
        "pharmacy_phone": pharmacy.phone,
        "pharmacy_email": pharmacy.email,
        "pharmacy_license": pharmacy.license_number,
        "pharmacy_gst": pharmacy.gst_number or "29AAACA1234B1Z5",
        "invoice_number": f"INV-{order.order_number.replace('PI-ORD-', '')}",
        "invoice_date": order.created_at.strftime("%d-%m-%Y"),
        "order_number": order.order_number,
        "customer": {
            "name": customer.full_name,
            "phone": order.contact_phone,
            "address": order.delivery_address
        },
        "pharmacist_name": "Rajesh Nambiar, M.Pharm",
        "pharmacist_reg": "KSPC-REG-2015-88391",
        "subtotal": order.subtotal,
        "tax_amount": order.tax_amount,
        "delivery_fee": order.delivery_fee,
        "total_amount": order.total_amount,
        "payment_method": order.payment_method,
        "payment_status": order.payment_status,
        "items": [
            {
                "name": itm.medicine.brand_name,
                "generic": itm.medicine.generic_name,
                "composition": itm.medicine.composition,
                "batch_number": itm.batch.batch_number if itm.batch else "BT-88910",
                "expiry_date": itm.batch.expiry_date if itm.batch else "2027-08-30",
                "quantity": itm.quantity,
                "mrp": itm.mrp,
                "unit_price": itm.unit_price,
                "gst_rate": itm.gst_rate,
                "total_price": itm.total_price
            }
            for itm in order.items
        ]
    }
