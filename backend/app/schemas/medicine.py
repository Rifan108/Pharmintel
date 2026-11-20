from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class MedicineBase(BaseModel):
    medicine_code: str
    generic_name: str
    brand_name: str
    active_ingredients: str
    composition: str
    strength: str
    dosage_form: str
    manufacturer: str
    therapeutic_category: str
    drug_classification: Optional[str] = None
    approved_indications: str
    contraindications: str
    known_adverse_effects: str
    storage_information: str
    prescription_classification: str = "Rx"
    requires_prescription: bool = True
    drugbank_id: Optional[str] = None
    pubchem_cid: Optional[str] = None
    smiles: Optional[str] = None
    source: str
    last_verified_date: str
    base_mrp: float

class MedicineResponse(MedicineBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class MedicineSearchQuery(BaseModel):
    query: Optional[str] = None
    category: Optional[str] = None
    dosage_form: Optional[str] = None
    requires_prescription: Optional[bool] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    limit: int = 50
    offset: int = 0

class AlternativeItem(BaseModel):
    id: int
    medicine_code: str
    brand_name: str
    generic_name: str
    manufacturer: str
    strength: str
    dosage_form: str
    base_mrp: float
    price_difference: float
    alternative_type: str  # EXACT_GENERIC, BRANDED_EQUIVALENT, THERAPEUTIC_ALTERNATIVE
    requires_prescription: bool
    availability_status: str
    reason: str
