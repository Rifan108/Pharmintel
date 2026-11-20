from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class Pharmacy(Base):
    __tablename__ = "pharmacies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    registration_number = Column(String(100), unique=True, nullable=False)
    license_number = Column(String(100), unique=True, nullable=False)
    gst_number = Column(String(50), nullable=True)
    address = Column(Text, nullable=False)
    city = Column(String(100), nullable=False, index=True)
    state = Column(String(100), nullable=False)
    postal_code = Column(String(20), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    phone = Column(String(50), nullable=False)
    email = Column(String(255), nullable=False)
    is_verified = Column(Boolean, default=False)
    operating_hours = Column(String(255), default="08:00 AM - 10:00 PM")
    rating = Column(Float, default=4.8)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    pharmacists = relationship("Pharmacist", back_populates="pharmacy")
    inventory_items = relationship("PharmacyInventory", back_populates="pharmacy", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="pharmacy")
    suppliers = relationship("Supplier", back_populates="pharmacy")
    purchases = relationship("Purchase", back_populates="pharmacy")

class Supplier(Base):
    __tablename__ = "suppliers"

    id = Column(Integer, primary_key=True, index=True)
    pharmacy_id = Column(Integer, ForeignKey("pharmacies.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    contact_person = Column(String(100), nullable=True)
    phone = Column(String(50), nullable=False)
    email = Column(String(255), nullable=True)
    address = Column(Text, nullable=True)
    gst_number = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    pharmacy = relationship("Pharmacy", back_populates="suppliers")
    batches = relationship("MedicineBatch", back_populates="supplier")
    purchases = relationship("Purchase", back_populates="supplier")
