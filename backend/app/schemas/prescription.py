from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class PrescriptionItemDetail(BaseModel):
    id: int
    medicine_name_raw: str
    matched_medicine_id: Optional[int] = None
    matched_medicine_name: Optional[str] = None
    strength: Optional[str] = None
    dosage_form: Optional[str] = None
    frequency: Optional[str] = None
    duration: Optional[str] = None
    instructions: Optional[str] = None
    confidence_score: float
    pharmacist_confirmed: bool
    pharmacist_corrected_name: Optional[str] = None

class PrescriptionResponse(BaseModel):
    id: int
    customer_id: int
    customer_name: Optional[str] = None
    file_name: str
    file_type: str
    ocr_status: str
    overall_confidence: float
    raw_extracted_text: Optional[str] = None
    verification_status: str
    verified_by_pharmacist_id: Optional[int] = None
    pharmacist_notes: Optional[str] = None
    doctor_name: Optional[str] = None
    patient_name: Optional[str] = None
    prescription_date: Optional[str] = None
    uploaded_at: datetime
    items: List[PrescriptionItemDetail]

class PharmacistVerificationRequest(BaseModel):
    status: str # VERIFIED, REJECTED
    notes: Optional[str] = None
    confirmed_items: List[dict] # [{item_id: int, matched_medicine_id: int, strength: str, frequency: str, duration: str, confirmed: bool}]
