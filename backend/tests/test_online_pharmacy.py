import pytest
import os
import sys
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

# Add backend to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app
from app.database import SessionLocal
from app.models.medicine import Medicine
from app.models.pharmacy import Pharmacy
from app.models.inventory import PharmacyInventory, MedicineBatch, StockAuditLog
from app.models.order import Order, OrderItem, Payment, Delivery
from app.models.user import User
from app.models.address import SavedAddress
from app.models.prescription import Prescription
from app.utils.security import create_access_token

client = TestClient(app)

@pytest.fixture(scope="module")
def db_session():
    session = SessionLocal()
    yield session
    session.close()

@pytest.fixture(scope="module")
def auth_headers(db_session: Session):
    user = db_session.query(User).filter(User.role == "customer").first()
    if not user:
        user = User(
            email="test_pharmacy_customer@pharmintel.in",
            hashed_password="hashed_test_password",
            full_name="Rajesh Nambiar",
            phone="+91 98450 77112",
            role="customer"
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
    
    token = create_access_token({"sub": str(user.id), "role": user.role, "email": user.email})
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture(scope="module")
def pharmacist_headers(db_session: Session):
    ph_user = db_session.query(User).filter(User.role == "pharmacist").first()
    if not ph_user:
        ph_user = User(
            email="test_chief_pharmacist@pharmintel.in",
            hashed_password="hashed_test_password",
            full_name="Dr. Archana Rao, M.Pharm",
            phone="+91 98450 99887",
            role="pharmacist"
        )
        db_session.add(ph_user)
        db_session.commit()
        db_session.refresh(ph_user)
    
    token = create_access_token({"sub": str(ph_user.id), "role": ph_user.role, "email": ph_user.email})
    return {"Authorization": f"Bearer {token}"}

# =========================================================================
# 1. CATALOG & INVENTORY COVERAGE TESTS
# =========================================================================
def test_all_medicines_have_inventory_and_batches(db_session: Session):
    """Ensure every catalog medicine has inventory and batch records across licensed pharmacies."""
    medicines = db_session.query(Medicine).all()
    assert len(medicines) >= 100, f"Expected at least 100 medicines, found {len(medicines)}"
    
    for med in medicines[:10]: # Sample check top 10
        inv = db_session.query(PharmacyInventory).filter(PharmacyInventory.medicine_id == med.id).first()
        assert inv is not None, f"Medicine {med.brand_name} (ID: {med.id}) lacks inventory entry"
        assert inv.stock_quantity > 0, f"Medicine {med.brand_name} has zero stock"
        
        batch = db_session.query(MedicineBatch).filter(MedicineBatch.inventory_id == inv.id).first()
        assert batch is not None, f"Medicine {med.brand_name} lacks batch entry"
        assert batch.batch_number is not None
        assert batch.selling_price > 0
        assert batch.mrp >= batch.selling_price

def test_search_medicines_and_categories():
    """Verify medicine search, category filter, and autocomplete APIs."""
    # Search by brand
    res = client.get("/api/medicines?q=metformin")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] > 0
    assert any("metformin" in m["generic_name"].lower() or "metformin" in m["brand_name"].lower() for m in data["items"])

    # Search categories
    cat_res = client.get("/api/medicines/categories")
    assert cat_res.status_code == 200
    cats = cat_res.json()
    assert len(cats) >= 5
    assert any("cardio" in c.lower() or "diabet" in c.lower() for c in cats)

    # Autocomplete
    ac_res = client.get("/api/medicines/autocomplete?prefix=dolo")
    assert ac_res.status_code == 200
    ac_data = ac_res.json()
    assert len(ac_data) > 0
    assert any("dolo" in s["brand_name"].lower() for s in ac_data)

# =========================================================================
# 2. CART OPERATIONS & TAX / DELIVERY CALCULATIONS
# =========================================================================
def test_cart_operations_and_financials(auth_headers, db_session: Session):
    """Test full cart lifecycle: add, update, calculate GST, calculate free delivery threshold, remove, clear."""
    # Clear cart first
    client.delete("/api/cart", headers=auth_headers)

    # Find a medicine
    med = db_session.query(Medicine).filter(Medicine.requires_prescription == False).first()
    if not med:
        med = db_session.query(Medicine).first()

    # Add item
    add_res = client.post(
        "/api/cart/items",
        json={"medicine_id": med.id, "quantity": 2, "pharmacy_id": 1},
        headers=auth_headers
    )
    assert add_res.status_code == 200
    cart = add_res.json()
    assert cart["items_count"] == 2
    assert cart["subtotal"] > 0
    assert cart["tax_amount"] > 0
    assert cart["total_payable"] > cart["subtotal"]

    # If subtotal < 500, delivery fee should be 40
    if cart["subtotal"] < 500:
        assert cart["delivery_fee"] == 40.0
    else:
        assert cart["delivery_fee"] == 0.0

    cart_item_id = cart["items"][0]["id"]

    # Update quantity to 4
    up_res = client.put(
        f"/api/cart/items/{cart_item_id}",
        json={"quantity": 4},
        headers=auth_headers
    )
    assert up_res.status_code == 200
    up_cart = up_res.json()
    assert up_cart["items_count"] == 4

    # Remove item
    del_res = client.delete(f"/api/cart/items/{cart_item_id}", headers=auth_headers)
    assert del_res.status_code == 200
    assert del_res.json()["items_count"] == 0

# =========================================================================
# 3. SAVED ADDRESSES & PINCODE SERVICEABILITY
# =========================================================================
def test_saved_addresses_and_validation(auth_headers):
    """Test address saving, strict rejection of dummy names, and PIN code validation."""
    # Attempt saving with dummy name - MUST FAIL
    bad_res = client.post(
        "/api/addresses",
        json={
            "recipient_name": "dummy",
            "phone": "+91 98450 11223",
            "address_line1": "Flat 101, Test St",
            "pincode": "560103"
        },
        headers=auth_headers
    )
    assert bad_res.status_code == 400
    assert "manually entered" in bad_res.json()["detail"].lower()

    # Save valid address with real manual name
    good_res = client.post(
        "/api/addresses",
        json={
            "recipient_name": "Deepak Venkat",
            "phone": "+91 98450 11223",
            "address_line1": "Flat 402, Green Glen Layout, Outer Ring Road",
            "city": "Bengaluru",
            "state": "Karnataka",
            "pincode": "560103",
            "address_type": "Home",
            "is_default": True
        },
        headers=auth_headers
    )
    assert good_res.status_code == 200
    addr_id = good_res.json()["id"]

    # Check list
    list_res = client.get("/api/addresses", headers=auth_headers)
    assert list_res.status_code == 200
    assert any(a["id"] == addr_id for a in list_res.json())

    # Clean up
    client.delete(f"/api/addresses/{addr_id}", headers=auth_headers)

def test_pincode_serviceability():
    """Verify express vs standard delivery categorization across PIN codes."""
    # Bengaluru Express Pin
    blr_res = client.get("/api/addresses/serviceability?pincode=560103")
    assert blr_res.status_code == 200
    blr_data = blr_res.json()
    assert blr_data["serviceable"] is True
    assert "Express Zone" in blr_data["tier"]

    # Mumbai Metro Pin
    mum_res = client.get("/api/addresses/serviceability?pincode=400001")
    assert mum_res.status_code == 200
    mum_data = mum_res.json()
    assert mum_data["serviceable"] is True
    assert "Mumbai" in mum_data["region"]

    # Invalid PIN
    inv_res = client.get("/api/addresses/serviceability?pincode=123")
    assert inv_res.status_code == 200
    assert inv_res.json()["serviceable"] is False

# =========================================================================
# 4. PRESCRIPTION MANDATE & ORDER CREATION WORKFLOW
# =========================================================================
def test_prescription_mandate_enforcement(auth_headers, db_session: Session):
    """Verify that Schedule H / Rx drugs CANNOT be ordered without an attached prescription."""
    # Find Schedule H medicine
    rx_med = db_session.query(Medicine).filter(Medicine.requires_prescription == True).first()
    assert rx_med is not None

    # Place order without prescription - MUST BE REJECTED WITH 400
    fail_order = client.post(
        "/api/orders",
        json={
            "pharmacy_id": 1,
            "items": [{"medicine_id": rx_med.id, "quantity": 1}],
            "prescription_id": None,
            "patient_name": "Siddharth Verma",
            "delivery_address": "Indiranagar 100ft Road, Bengaluru",
            "contact_phone": "+91 98450 33445",
            "payment_method": "UPI / Online"
        },
        headers=auth_headers
    )
    assert fail_order.status_code == 400
    assert "prescription" in fail_order.json()["detail"].lower()

def test_full_order_placement_payment_and_cancellation(auth_headers, pharmacist_headers, db_session: Session):
    """
    Test complete order lifecycle:
    1. Create prescription record.
    2. Place order with Schedule H items.
    3. Initialize payment order & verify signature.
    4. Pharmacist reviews prescription & advances status to Preparing (deducting inventory).
    5. Cancel order and verify inventory is safely restored.
    """
    # 1. Setup user & prescription
    cust = db_session.query(User).filter(User.role == "customer").first()
    med = db_session.query(Medicine).filter(Medicine.requires_prescription == True).first()
    
    rx = Prescription(
        customer_id=cust.id,
        file_path="uploads/prescriptions/test_rx.pdf",
        file_name="test_rx.pdf",
        file_type="application/pdf",
        ocr_status="COMPLETED",
        overall_confidence=0.95,
        verification_status="PENDING_REVIEW",
        doctor_name="Dr. A. K. Banerjee, MBBS MD",
        patient_name="Siddharth Verma"
    )
    db_session.add(rx)
    db_session.commit()
    db_session.refresh(rx)

    # Check initial stock
    inv = db_session.query(PharmacyInventory).filter(
        PharmacyInventory.pharmacy_id == 1,
        PharmacyInventory.medicine_id == med.id
    ).first()
    initial_stock = inv.stock_quantity

    # 2. Place Order
    order_res = client.post(
        "/api/orders",
        json={
            "pharmacy_id": 1,
            "items": [{"medicine_id": med.id, "quantity": 3}],
            "prescription_id": rx.id,
            "patient_name": "Siddharth Verma",
            "delivery_address": "Plot 24, Koramangala 4th Block, Bengaluru",
            "contact_phone": "+91 98450 33445",
            "payment_method": "UPI / Online"
        },
        headers=auth_headers
    )
    assert order_res.status_code == 200
    order_data = order_res.json()
    order_id = order_data["order_id"]
    assert order_data["order_number"].startswith("PI-ORD-")
    assert order_data["requires_prescription_verification"] is True

    # 3. Create Payment Gateway Order & Verify
    pay_create = client.post(
        "/api/payments/create-order",
        json={"order_id": order_id, "payment_method": "UPI / Online"},
        headers=auth_headers
    )
    assert pay_create.status_code == 200
    assert "gateway_order_id" in pay_create.json()

    import random
    pay_verify = client.post(
        "/api/payments/verify",
        json={
            "order_id": order_id,
            "gateway_payment_id": f"PAY-TEST-{random.randint(1000000, 9999999)}",
            "payment_method": "UPI / Online"
        },
        headers=auth_headers
    )
    assert pay_verify.status_code == 200
    assert pay_verify.json()["payment_status"] == "Completed"

    # 4. Pharmacist reviews & advances order to 'Preparing'
    advance_res = client.patch(
        f"/api/orders/{order_id}/status",
        json={"status": "Preparing", "notes": "Prescription verified against dosage guidelines."},
        headers=pharmacist_headers
    )
    assert advance_res.status_code == 200
    assert advance_res.json()["new_status"] == "Preparing"

    # Verify inventory was deducted
    db_session.refresh(inv)
    assert inv.stock_quantity == initial_stock - 3

    # Verify audit log was recorded
    audit_log = db_session.query(StockAuditLog).filter(
        StockAuditLog.pharmacy_id == 1,
        StockAuditLog.medicine_id == med.id,
        StockAuditLog.action == "STOCK_OUT_SALE"
    ).order_by(StockAuditLog.timestamp.desc()).first()
    assert audit_log is not None
    assert audit_log.quantity_changed == -3

    # 5. Check tax invoice endpoint
    invoice_res = client.get(f"/api/orders/{order_id}/invoice", headers=auth_headers)
    assert invoice_res.status_code == 200
    inv_data = invoice_res.json()
    assert inv_data["patient_name"] == "Siddharth Verma"
    assert "Apollo Care" in inv_data["pharmacy"]["name"]
    assert len(inv_data["items"]) == 1
    assert "html" in inv_data

    # 6. Cancel order and verify stock restoration
    cancel_res = client.post(
        f"/api/orders/{order_id}/cancel?reason=Doctor%20adjusted%20dosage",
        headers=auth_headers
    )
    assert cancel_res.status_code == 200
    assert cancel_res.json()["order_status"] == "Cancelled"

    # Verify inventory was RESTORED
    db_session.refresh(inv)
    assert inv.stock_quantity == initial_stock

    # Verify STOCK_IN audit log
    restored_log = db_session.query(StockAuditLog).filter(
        StockAuditLog.pharmacy_id == 1,
        StockAuditLog.medicine_id == med.id,
        StockAuditLog.action == "STOCK_IN"
    ).order_by(StockAuditLog.timestamp.desc()).first()
    assert restored_log is not None
    assert restored_log.quantity_changed == 3
    assert "Restocked from cancelled order" in restored_log.reason

# =========================================================================
# 5. ORDER TRACKING & REORDER TESTS
# =========================================================================
def test_order_tracking_and_reorder(auth_headers, db_session: Session):
    """Test live delivery tracking endpoint and reorder functionality."""
    cust = db_session.query(User).filter(User.role == "customer").first()
    med = db_session.query(Medicine).filter(Medicine.prescription_classification == "OTC").first()
    if not med:
        med = db_session.query(Medicine).filter(Medicine.requires_prescription == False).first()

    # Place simple order
    order_res = client.post(
        "/api/orders",
        json={
            "pharmacy_id": 1,
            "items": [{"medicine_id": med.id, "quantity": 1}],
            "prescription_id": None,
            "patient_name": "Meera Krishnan",
            "delivery_address": "Whitefield Main Road, Bengaluru",
            "contact_phone": "+91 98450 88776",
            "payment_method": "Cash on Delivery"
        },
        headers=auth_headers
    )
    order_id = order_res.json()["order_id"]

    # Test tracking endpoint
    track_res = client.get(f"/api/orders/{order_id}/tracking", headers=auth_headers)
    assert track_res.status_code == 200
    track_data = track_res.json()
    assert "tracking_number" in track_data
    assert "courier_name" in track_data
    assert "driver_name" in track_data

    # Test reorder endpoint
    reorder_res = client.post(f"/api/orders/{order_id}/reorder", headers=auth_headers)
    assert reorder_res.status_code == 200
    reorder_data = reorder_res.json()
    assert "Successfully re-added" in reorder_data["message"]
    assert reorder_data["cart"]["items_count"] >= 1
