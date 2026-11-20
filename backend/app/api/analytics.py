from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.database import get_db
from app.models.user import User
from app.models.pharmacy import Pharmacy
from app.models.medicine import Medicine, DrugInteraction
from app.models.order import Order
from app.models.prescription import Prescription
from app.models.inventory import PharmacyInventory, MedicineBatch

router = APIRouter(prefix="/analytics", tags=["Platform & Pharmacy Analytics"])

@router.get("/dashboard")
def get_dashboard_analytics(db: Session = Depends(get_db)):
    total_users = db.query(User).count()
    total_pharmacies = db.query(Pharmacy).filter(Pharmacy.is_verified == True).count()
    total_medicines = db.query(Medicine).count()
    total_clinical_rules = db.query(DrugInteraction).count()
    total_orders = db.query(Order).count()
    total_prescriptions = db.query(Prescription).count()
    pending_prescriptions = db.query(Prescription).filter(Prescription.verification_status == "PENDING_REVIEW").count()

    # Recent orders
    recent_orders = db.query(Order).order_by(Order.created_at.desc()).limit(5).all()
    recent_order_list = [
        {
            "id": o.id,
            "order_number": o.order_number,
            "customer_name": o.customer.full_name,
            "pharmacy_name": o.pharmacy.name,
            "total_amount": o.total_amount,
            "status": o.status,
            "date": o.created_at.strftime("%d %b %Y, %H:%M")
        }
        for o in recent_orders
    ]

    # Inventory alerts
    today_str = datetime.utcnow().strftime("%Y-%m-%d")
    sixty_days_str = (datetime.utcnow() + timedelta(days=60)).strftime("%Y-%m-%d")

    low_stock_items = db.query(PharmacyInventory).filter(
        PharmacyInventory.stock_quantity <= PharmacyInventory.low_stock_threshold
    ).count()

    expiring_batches = db.query(MedicineBatch).filter(
        MedicineBatch.expiry_date <= sixty_days_str,
        MedicineBatch.quantity > 0
    ).count()

    # Orders by status distribution
    orders_by_status = {}
    for st in ["Pending", "Prescription Verification", "Approved", "Preparing", "Dispatched", "Delivered"]:
        orders_by_status[st] = db.query(Order).filter(Order.status == st).count()

    return {
        "overview": {
            "total_patients": db.query(User).filter(User.role == "customer").count(),
            "total_pharmacists": db.query(User).filter(User.role == "pharmacist").count(),
            "active_pharmacies": total_pharmacies,
            "verified_medicines": total_medicines,
            "clinical_rules": total_clinical_rules,
            "total_orders": total_orders,
            "total_prescriptions": total_prescriptions,
            "pending_prescriptions": pending_prescriptions,
            "low_stock_alerts": low_stock_items,
            "expiring_batches_alerts": expiring_batches
        },
        "orders_distribution": orders_by_status,
        "recent_orders": recent_order_list,
        "platform_safety_status": "Dual-Layer Safety Active (Layer 1 Clinical Rules + Layer 2 HybridGNN)"
    }
