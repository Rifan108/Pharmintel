from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    order_number = Column(String(100), unique=True, index=True, nullable=False)  # e.g., PI-ORD-2026-9041
    customer_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    pharmacy_id = Column(Integer, ForeignKey("pharmacies.id", ondelete="RESTRICT"), nullable=False, index=True)
    prescription_id = Column(Integer, ForeignKey("prescriptions.id", ondelete="SET NULL"), nullable=True)

    # Lifecycle Status:
    # Pending, Prescription Verification, Approved, Rejected, Preparing, Ready for Pickup, Dispatched, Delivered, Cancelled
    status = Column(String(50), default="Pending", index=True, nullable=False)
    
    subtotal = Column(Float, nullable=False)
    tax_amount = Column(Float, default=0.0)
    delivery_fee = Column(Float, default=0.0)
    total_amount = Column(Float, nullable=False)
    
    # Payment: Cash on Delivery, UPI / Card, Net Banking
    payment_method = Column(String(50), default="UPI / Online")
    # Payment status: Pending, Completed, Refunded, Failed
    payment_status = Column(String(50), default="Pending")

    delivery_address = Column(Text, nullable=False)
    contact_phone = Column(String(50), nullable=False)
    patient_name = Column(String(255), nullable=True) # Manually entered patient name
    delivery_type = Column(String(50), default="Home Delivery")  # Home Delivery, In-Store Pickup
    special_instructions = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    customer = relationship("User", back_populates="orders")
    pharmacy = relationship("Pharmacy", back_populates="orders")
    prescription = relationship("Prescription", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    delivery = relationship("Delivery", back_populates="order", uselist=False, cascade="all, delete-orphan")
    payment = relationship("Payment", back_populates="order", uselist=False, cascade="all, delete-orphan")

class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    medicine_id = Column(Integer, ForeignKey("medicines.id", ondelete="RESTRICT"), nullable=False)
    batch_id = Column(Integer, ForeignKey("medicine_batches.id", ondelete="SET NULL"), nullable=True)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)
    mrp = Column(Float, nullable=False)
    discount = Column(Float, default=0.0)
    gst_rate = Column(Float, default=12.0)  # Standard pharma GST rate (12% or 5%)
    total_price = Column(Float, nullable=False)

    order = relationship("Order", back_populates="items")
    medicine = relationship("Medicine", back_populates="order_items")
    batch = relationship("MedicineBatch")

class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), unique=True, nullable=False)
    transaction_id = Column(String(100), unique=True, index=True, nullable=False)
    amount = Column(Float, nullable=False)
    payment_method = Column(String(50), nullable=False)
    payment_status = Column(String(50), default="Completed")
    paid_at = Column(DateTime, default=datetime.utcnow)

    order = relationship("Order", back_populates="payment")

class Delivery(Base):
    __tablename__ = "deliveries"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), unique=True, nullable=False)
    tracking_number = Column(String(100), unique=True, index=True, nullable=False)
    courier_name = Column(String(100), default="PharmIntel Express Healthcare Courier")
    current_status = Column(String(50), default="Order Assigned") # Assigned, Picked Up, In Transit, Out for Delivery, Delivered
    estimated_delivery_time = Column(String(100), nullable=True)
    dispatched_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    driver_name = Column(String(100), default="Suresh K.")
    driver_phone = Column(String(50), default="+91 98765 43210")
    current_lat = Column(Float, nullable=True)
    current_lng = Column(Float, nullable=True)

    order = relationship("Order", back_populates="delivery")
