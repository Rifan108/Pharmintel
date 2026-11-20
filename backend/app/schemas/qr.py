from pydantic import BaseModel
from typing import Optional, Dict, Any, List

class QRVerifyRequest(BaseModel):
    raw_qr_content: str
    source_type: Optional[str] = "camera_scan"  # "camera_scan", "file_upload", "manual_entry"

class QRSafetyInfo(BaseModel):
    approved_indications: str
    contraindications: str
    known_adverse_effects: str
    storage_information: str

class QRPackagingMetadata(BaseModel):
    gtin: Optional[str] = None
    serial_number: Optional[str] = None
    registered_pharmacy: Optional[str] = None
    pharmacy_license: Optional[str] = None
    tamper_seal_hash: Optional[str] = None
    mrp: Optional[float] = None
    selling_price: Optional[float] = None

class QRVerifyResponse(BaseModel):
    is_verified_authentic: bool
    authenticity_badge: str
    authenticity_statement: str
    authoritative_source_connected: bool
    authoritative_source_name: str
    verification_timestamp: str
    medicine_name: str
    generic_name: str
    manufacturer: str
    batch_number: str
    expiry_date: str
    is_expired: bool
    is_recalled: bool
    recall_reason: Optional[str] = None
    composition: str
    strength: str
    dosage_form: str
    therapeutic_category: str
    prescription_classification: str
    safety_information: QRSafetyInfo
    packaging_metadata: QRPackagingMetadata

class QRSampleItem(BaseModel):
    label: str
    category: str
    raw_payload: str
    brand_name: str
    batch_number: str
    description: str
    is_authentic: bool
