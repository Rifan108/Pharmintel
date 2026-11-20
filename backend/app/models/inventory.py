from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class PharmacyInventory(Base):
    __tablename__ = "pharmacy_inventory"

    id = Column(Integer, primary_key=True, index=True)
    pharmacy_id = Column(Integer, ForeignKey("pharmacies.id", ondelete="CASCADE"), nullable=False, index=True)
    medicine_id = Column(Integer, ForeignKey("medicines.id", ondelete="CASCADE"), nullable=False, index=True)
    stock_quantity = Column(Integer, default=0, nullable=False)
    low_stock_threshold = Column(Integer, default=15, nullable=False)
    is_available = Column(Boolean, default=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    pharmacy = relationship("Pharmacy", back_populates="inventory_items")
    medicine = relationship("Medicine", back_populates="inventory_entries")
    batches = relationship("MedicineBatch", back_populates="inventory", cascade="all, delete-orphan")

class MedicineBatch(Base):
    __tablename__ = "medicine_batches"

    id = Column(Integer, primary_key=True, index=True)
    inventory_id = Column(Integer, ForeignKey("pharmacy_inventory.id", ondelete="CASCADE"), nullable=False, index=True)
    batch_number = Column(String(100), nullable=False, index=True)
    expiry_date = Column(String(50), nullable=False, index=True)  # YYYY-MM-DD
    purchase_price = Column(Float, nullable=False)
    selling_price = Column(Float, nullable=False)
    mrp = Column(Float, nullable=False)
    quantity = Column(Integer, default=0, nullable=False)
    is_recalled = Column(Boolean, default=False)
    recall_reason = Column(Text, nullable=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    inventory = relationship("PharmacyInventory", back_populates="batches")
    supplier = relationship("Supplier", back_populates="batches")

class Purchase(Base):
    __tablename__ = "purchases"

    id = Column(Integer, primary_key=True, index=True)
    pharmacy_id = Column(Integer, ForeignKey("pharmacies.id", ondelete="CASCADE"), nullable=False)
    supplier_id = Column(Integer, ForeignKey("suppliers.id", ondelete="RESTRICT"), nullable=False)
    invoice_number = Column(String(100), unique=True, nullable=False)
    purchase_date = Column(String(50), nullable=False)
    total_amount = Column(Float, nullable=False)
    tax_amount = Column(Float, default=0.0)
    payment_status = Column(String(50), default="Paid")  # Paid, Pending, Partial
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    pharmacy = relationship("Pharmacy", back_populates="purchases")
    supplier = relationship("Supplier", back_populates="purchases")
    items = relationship("PurchaseItem", back_populates="purchase", cascade="all, delete-orphan")

class PurchaseItem(Base):
    __tablename__ = "purchase_items"

    id = Column(Integer, primary_key=True, index=True)
    purchase_id = Column(Integer, ForeignKey("purchases.id", ondelete="CASCADE"), nullable=False)
    medicine_name = Column(String(255), nullable=False)
    batch_number = Column(String(100), nullable=False)
    expiry_date = Column(String(50), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_cost = Column(Float, nullable=False)
    total_cost = Column(Float, nullable=False)

    purchase = relationship("Purchase", back_populates="items")

class StockAuditLog(Base):
    __tablename__ = "stock_audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    pharmacy_id = Column(Integer, nullable=False)
    medicine_id = Column(Integer, nullable=False)
    batch_id = Column(Integer, nullable=True)
    action = Column(String(100), nullable=False)  # STOCK_IN, STOCK_OUT_SALE, RECALL, EXPIRY_REMOVAL, ADJUSTMENT
    quantity_changed = Column(Integer, nullable=False)
    balance_quantity = Column(Integer, nullable=False)
    performed_by_user_id = Column(Integer, nullable=False)
    reason = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
