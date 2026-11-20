from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    phone = Column(String(50), nullable=True)
    # Roles: customer, pharmacist, pharmacy_admin, platform_admin
    role = Column(String(50), default="customer", nullable=False, index=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    customer_profile = relationship("Customer", back_populates="user", uselist=False, cascade="all, delete-orphan")
    pharmacist_profile = relationship("Pharmacist", back_populates="user", uselist=False, cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="customer")
    prescriptions = relationship("Prescription", back_populates="customer", foreign_keys="Prescription.customer_id")
    carts = relationship("Cart", back_populates="user", cascade="all, delete-orphan")
    saved_addresses = relationship("SavedAddress", back_populates="user", cascade="all, delete-orphan")

class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    address = Column(Text, nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=True)
    emergency_contact = Column(String(100), nullable=True)
    allergies = Column(Text, nullable=True)  # Comma-separated or text description
    medical_conditions = Column(Text, nullable=True)
    date_of_birth = Column(String(20), nullable=True)

    user = relationship("User", back_populates="customer_profile")

class Pharmacist(Base):
    __tablename__ = "pharmacists"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    pharmacy_id = Column(Integer, ForeignKey("pharmacies.id", ondelete="SET NULL"), nullable=True)
    license_number = Column(String(100), unique=True, nullable=False)
    qualification = Column(String(100), nullable=True)
    is_verified = Column(Boolean, default=False)
    verified_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="pharmacist_profile")
    pharmacy = relationship("Pharmacy", back_populates="pharmacists")
