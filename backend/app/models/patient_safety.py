from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class PatientHealthProfile(Base):
    __tablename__ = "patient_health_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    patient_name = Column(String(255), nullable=True)
    medical_conditions_json = Column(Text, default="[]", nullable=False) # e.g. ["Diabetes Type 2", "High blood pressure"]
    allergies_json = Column(Text, default="[]", nullable=False)          # e.g. ["Penicillin", "Aspirin / NSAIDs"]
    age = Column(Integer, nullable=True)
    gender = Column(String(20), nullable=True)
    kidney_function = Column(String(50), default="Normal", nullable=True)
    liver_function = Column(String(50), default="Normal", nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User")

class PatientCurrentMedication(Base):
    __tablename__ = "patient_current_medications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    medicine_id = Column(Integer, ForeignKey("medicines.id", ondelete="SET NULL"), nullable=True)
    medicine_name = Column(String(255), nullable=False)
    brand_name = Column(String(255), nullable=True)
    generic_name = Column(String(255), nullable=True)
    active_ingredients = Column(Text, nullable=True)
    strength = Column(String(100), nullable=True)
    dosage = Column(String(100), nullable=True)
    frequency = Column(String(100), nullable=True)
    administration_route = Column(String(100), default="Oral", nullable=True)
    timing = Column(String(100), nullable=True)
    start_date = Column(String(50), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")
    medicine = relationship("Medicine")

class PatientSafetyAssessmentRecord(Base):
    __tablename__ = "patient_safety_assessment_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    patient_name = Column(String(255), nullable=True)
    assessment_date = Column(String(50), nullable=False)
    proposed_medicine_name = Column(String(255), nullable=False)
    proposed_medicine_id = Column(Integer, nullable=True)
    overall_status = Column(String(20), nullable=False) # GREEN, YELLOW, RED, GREY
    summary_headline = Column(String(255), nullable=False)
    patient_conditions_json = Column(Text, default="[]", nullable=False)
    patient_allergies_json = Column(Text, default="[]", nullable=False)
    existing_medicines_json = Column(Text, default="[]", nullable=False)
    findings_json = Column(Text, default="[]", nullable=False)
    personalized_explanation_json = Column(Text, default="{}", nullable=False)
    knowledge_base_version = Column(String(50), default="CDSCO/BNF-2026.1", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")
