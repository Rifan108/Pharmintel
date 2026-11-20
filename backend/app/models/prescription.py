from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class Prescription(Base):
    __tablename__ = "prescriptions"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    file_path = Column(String(500), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)  # image/jpeg, image/png, application/pdf
    ocr_status = Column(String(50), default="COMPLETED")  # PENDING, PROCESSING, COMPLETED, FAILED
    overall_confidence = Column(Float, default=0.0)
    raw_extracted_text = Column(Text, nullable=True)
    
    # Pharmacist verification lifecycle
    # Statuses: PENDING_REVIEW, VERIFIED, REJECTED
    verification_status = Column(String(50), default="PENDING_REVIEW", index=True)
    verified_by_pharmacist_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    pharmacist_notes = Column(Text, nullable=True)
    doctor_name = Column(String(255), nullable=True)
    patient_name = Column(String(255), nullable=True)
    prescription_date = Column(String(50), nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    verified_at = Column(DateTime, nullable=True)

    # Relationships
    customer = relationship("User", foreign_keys=[customer_id], back_populates="prescriptions")
    verified_by = relationship("User", foreign_keys=[verified_by_pharmacist_id])
    items = relationship("PrescriptionItem", back_populates="prescription", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="prescription")

class PrescriptionItem(Base):
    __tablename__ = "prescription_items"

    id = Column(Integer, primary_key=True, index=True)
    prescription_id = Column(Integer, ForeignKey("prescriptions.id", ondelete="CASCADE"), nullable=False, index=True)
    medicine_name_raw = Column(String(255), nullable=False)
    matched_medicine_id = Column(Integer, ForeignKey("medicines.id", ondelete="SET NULL"), nullable=True)
    strength = Column(String(100), nullable=True)
    dosage_form = Column(String(100), nullable=True)
    frequency = Column(String(100), nullable=True)     # e.g., Once daily, BID, TID, PRN
    duration = Column(String(100), nullable=True)      # e.g., 5 days, 1 month
    instructions = Column(Text, nullable=True)        # e.g., After food
    confidence_score = Column(Float, default=0.0)
    pharmacist_confirmed = Column(Boolean, default=False)
    pharmacist_corrected_name = Column(String(255), nullable=True)

    prescription = relationship("Prescription", back_populates="items")
    matched_medicine = relationship("Medicine")
