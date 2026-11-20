from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class Medicine(Base):
    __tablename__ = "medicines"

    id = Column(Integer, primary_key=True, index=True)
    medicine_code = Column(String(50), unique=True, index=True, nullable=False)  # e.g., MED-00101
    generic_name = Column(String(255), index=True, nullable=False)
    brand_name = Column(String(255), index=True, nullable=False)
    active_ingredients = Column(Text, nullable=False)  # Comma separated
    composition = Column(Text, nullable=False)         # Detailed formulation
    strength = Column(String(100), nullable=False)     # e.g., 500mg, 10mg/5ml
    dosage_form = Column(String(100), nullable=False)  # Tablet, Capsule, Syrup, etc.
    route_of_administration = Column(String(100), default="Oral") # Oral, Inhalation, Topical, IV
    manufacturer = Column(String(255), index=True, nullable=False)
    therapeutic_category = Column(String(255), index=True, nullable=False)
    drug_classification = Column(String(255), nullable=True) # e.g. Biguanide, ACEi, ARB
    atc_code = Column(String(50), nullable=True)             # WHO ATC Code e.g. A10BA02
    is_combination = Column(Boolean, default=False)          # Multi-ingredient combination product
    active_substances_json = Column(Text, nullable=True)     # JSON array of individual ingredients
    aliases_json = Column(Text, nullable=True)               # JSON array of brand synonyms & spellings
    approved_indications = Column(Text, nullable=False)
    contraindications = Column(Text, nullable=False)
    known_adverse_effects = Column(Text, nullable=False)
    storage_information = Column(String(255), nullable=False)
    # Prescription classification: OTC, Rx, Schedule H, Schedule H1, Schedule X
    prescription_classification = Column(String(50), default="Rx", nullable=False)
    requires_prescription = Column(Boolean, default=True)
    drugbank_id = Column(String(50), index=True, nullable=True)
    pubchem_cid = Column(String(50), nullable=True)
    smiles = Column(Text, nullable=True)               # Canonical SMILES for ML molecular fingerprints
    source = Column(String(255), default="Central Drugs Standard Control Organisation (CDSCO) / FDA Compendium")
    last_verified_date = Column(String(50), default="2026-03-15")
    base_mrp = Column(Float, nullable=False)
    completeness_score = Column(Float, default=1.0)
    verification_status = Column(String(50), default="VERIFIED_REGULATORY") # VERIFIED_REGULATORY, DISCOVERED_EXTERNAL, PENDING_REVIEW
    external_reference_id = Column(String(100), nullable=True) # RxCUI or DailyMed Set ID
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    inventory_entries = relationship("PharmacyInventory", back_populates="medicine", cascade="all, delete-orphan")
    order_items = relationship("OrderItem", back_populates="medicine")

class DrugInteraction(Base):
    """
    Safety Layer 1: Verified Curated Clinical Drug-Drug Interaction Rules
    """
    __tablename__ = "drug_interactions"

    id = Column(Integer, primary_key=True, index=True)
    drug_a_generic = Column(String(255), index=True, nullable=False)
    drug_b_generic = Column(String(255), index=True, nullable=False)
    # Categories: Contraindicated, Major, Moderate, Minor, Unknown / Insufficient evidence
    severity_category = Column(String(50), index=True, nullable=False)
    mechanism = Column(Text, nullable=False)
    clinical_consequences = Column(Text, nullable=False)
    evidence_source = Column(String(255), nullable=False)  # e.g. FDA Label, British National Formulary (BNF)
    source_reference = Column(Text, nullable=False)
    last_verified_date = Column(String(50), default="2026-03-20")
    created_at = Column(DateTime, default=datetime.utcnow)

class UnidentifiedMedicineLog(Base):
    """
    Continuous Discovery: Tracks medicine lookup queries that could not be immediately resolved,
    recording diagnostic status, external lookup attempts, and resolution outcomes.
    """
    __tablename__ = "unidentified_medicine_logs"

    id = Column(Integer, primary_key=True, index=True)
    raw_input_name = Column(String(255), nullable=False)
    normalized_input = Column(String(255), nullable=True)
    candidate_matches_json = Column(Text, nullable=True)
    diagnostic_status = Column(String(100), nullable=False)
    requested_at = Column(DateTime, default=datetime.utcnow)
    resolved_status = Column(String(50), default="PENDING")
    resolved_medicine_id = Column(Integer, nullable=True)
    patient_session_id = Column(String(100), nullable=True)

class MedicineAuditLog(Base):
    """
    Clinical Audit Trail: Maintains immutable history of every medicine record modification,
    ingestion, or verification update.
    """
    __tablename__ = "medicine_audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    medicine_id = Column(Integer, nullable=True)
    action = Column(String(50), nullable=False) # CREATE, UPDATE, VERIFY, INGEST_DISCOVERY
    changed_by_user_id = Column(Integer, nullable=True)
    changes_json = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    reason = Column(Text, nullable=True)
