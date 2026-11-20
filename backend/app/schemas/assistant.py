from pydantic import BaseModel
from typing import List, Optional, Any

class ChatQueryRequest(BaseModel):
    session_id: str
    message: str
    language: Optional[str] = "en"  # "en", "kn", "hi", "ml", "ta", "te", "mr"
    mode: Optional[str] = "ai_assistant"  # "ai_assistant" or "live_support"
    patient_name: Optional[str] = None

class SourceCitation(BaseModel):
    title: str
    category: str
    reference_source: str
    verification_date: str

class ChatQueryResponse(BaseModel):
    session_id: str
    response: str
    language: str
    category: str
    is_emergency: bool
    guardrail_flag: str
    sources: List[SourceCitation]
    disclaimer: str
    pharmacist_escalation_available: Optional[bool] = False

class ClearSessionRequest(BaseModel):
    session_id: str

class EscalatePharmacistRequest(BaseModel):
    session_id: str
    patient_name: Optional[str] = None
    notes: Optional[str] = None

class EscalatePharmacistResponse(BaseModel):
    success: bool
    ticket_id: str
    assigned_pharmacist: str
    license_no: str
    status: str
    message: str
    contact_phone: str
