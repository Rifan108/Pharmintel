from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class InteractionCheckRequest(BaseModel):
    medicine_ids: List[int]
    enable_ml_prediction: bool = True

class InteractionDetail(BaseModel):
    drug_a: str
    drug_b: str
    severity: str  # Contraindicated, Major, Moderate, Minor, Unknown / Insufficient evidence
    mechanism: str
    clinical_consequences: str
    source: str
    source_reference: str
    last_verified_date: str
    layer_detected: str  # LAYER_1_CLINICAL_RULE or LAYER_2_HYBRIDGNN
    ml_confidence: Optional[float] = None
    class_probabilities: Optional[Dict[str, float]] = None

class InteractionSummary(BaseModel):
    total_pairs_checked: int
    contraindicated_count: int
    major_count: int
    moderate_count: int
    minor_count: int
    safe_or_unknown_count: int
    highest_severity: str
    has_risk: bool

class DDIResponse(BaseModel):
    medicines_checked: List[dict]
    summary: InteractionSummary
    interactions: List[InteractionDetail]
    disclaimer: str

# ==============================================================================
# PATIENT-SPECIFIC MULTI-DRUG SAFETY INTELLIGENCE SCHEMAS
# ==============================================================================

class HealthProfileInput(BaseModel):
    patient_name: Optional[str] = None
    medical_conditions: List[str] = []
    allergies: List[str] = []
    age: Optional[int] = None
    gender: Optional[str] = None
    kidney_function: Optional[str] = "Normal"  # Normal, Mild, Moderate, Severe
    liver_function: Optional[str] = "Normal"   # Normal, Mild, Moderate, Severe

class CurrentMedicationInput(BaseModel):
    id: Optional[int] = None
    medicine_id: Optional[int] = None
    medicine_name: str
    brand_name: Optional[str] = None
    generic_name: Optional[str] = None
    active_ingredients: Optional[str] = None
    strength: Optional[str] = None
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    administration_route: Optional[str] = "Oral"
    timing: Optional[str] = None
    start_date: Optional[str] = None

class ProposedMedicineInput(BaseModel):
    medicine_id: Optional[int] = None
    medicine_name: str
    brand_name: Optional[str] = None
    generic_name: Optional[str] = None
    active_ingredients: Optional[str] = None
    strength: Optional[str] = None
    dosage_form: Optional[str] = None
    manufacturer: Optional[str] = None

class CheckRegimenCompatibilityRequest(BaseModel):
    patient_name: Optional[str] = None
    proposed_medicine: ProposedMedicineInput
    health_profile: HealthProfileInput
    existing_medicines: List[CurrentMedicationInput]
    enable_ml_prediction: bool = True
    save_profile: bool = False

class InteractionFindingDetail(BaseModel):
    id: str
    finding_type: str  # "DRUG_TO_DRUG", "DRUG_TO_DISEASE", "DRUG_TO_ALLERGY", "DUPLICATE_MEDICINE", "MULTIPLE_REGIMEN_RISK", "PATIENT_SPECIFIC_RISK"
    severity: str      # "RED", "YELLOW", "GREEN", "GREY"
    severity_label: str # "Serious Risk", "Caution Required", "No Known Interaction", "Insufficient Info"
    headline: str
    medicines_involved: List[str]
    medical_condition_involved: Optional[str] = None
    allergy_involved: Optional[str] = None
    plain_language_explanation: str
    clinical_mechanism: str
    clinical_consequences: str
    recommended_action: str
    evidence_source: str
    source_update_date: str
    ml_predicted: bool = False
    ml_confidence: Optional[float] = None

class PersonalizedExplanation(BaseModel):
    should_take_assessment: str
    what_this_means_for_you: str
    why_this_applies_to_you: str
    action_summary: List[str]
    questions_for_doctor: List[str]
    missing_information: List[str]

class FindingsCount(BaseModel):
    total: int
    serious_red: int
    caution_yellow: int
    info_green: int
    insufficient_grey: int

class PatientSummarySchema(BaseModel):
    patient_name: Optional[str] = None
    medical_conditions: List[str]
    known_allergies: List[str]
    age: Optional[int] = None
    gender: Optional[str] = None
    kidney_function: Optional[str] = "Normal"
    liver_function: Optional[str] = "Normal"

class CompatibilityReportResponse(BaseModel):
    assessment_id: Optional[int] = None
    assessment_timestamp: str
    patient_name: Optional[str] = None
    overall_status: str        # "RED", "YELLOW", "GREEN", "GREY"
    overall_status_label: str  # e.g. "RED – Serious Potential Interaction"
    summary_headline: str
    patient_summary: PatientSummarySchema
    proposed_medicine: ProposedMedicineInput
    existing_medicines_analysed: List[CurrentMedicationInput]
    findings: List[InteractionFindingDetail]
    findings_count: FindingsCount
    personalized_guidance: PersonalizedExplanation
    knowledge_base_version: str
    disclaimer: str

class PatientProfileSaveRequest(BaseModel):
    health_profile: HealthProfileInput
    existing_medicines: List[CurrentMedicationInput]

class AssessmentHistoryItem(BaseModel):
    id: int
    assessment_date: str
    proposed_medicine_name: str
    overall_status: str
    summary_headline: str
    medicines_count: int
    warnings_count: int
    knowledge_base_version: str

# =========================================================================
# MULTIPLE MEDICINE COMPATIBILITY SCHEMAS
# =========================================================================

class MultiMedicineItem(BaseModel):
    id: Optional[int] = None
    medicine_name: str
    brand_name: Optional[str] = None
    generic_name: Optional[str] = None
    active_ingredients: Optional[str] = None
    strength: Optional[str] = None
    frequency: Optional[str] = None
    timing: Optional[str] = None

class MultiMedicineCheckRequest(BaseModel):
    patient_name: Optional[str] = None
    medicines: List[MultiMedicineItem]
    health_profile: Optional[HealthProfileInput] = None
    language: Optional[str] = "en"
    enable_ml_prediction: Optional[bool] = True

class MultiInteractionTableRow(BaseModel):
    id: str
    medicines_involved: List[str]
    interaction_title: str
    severity: str          # RED, YELLOW, GREEN, GREY
    severity_label: str    # High Risk, Moderate Risk, Safe, Insufficient Info
    explanation: str
    clinical_mechanism: str
    clinical_consequences: str
    recommended_action: str
    evidence_source: str
    ml_predicted: bool = False

class MultiMedicineReportResponse(BaseModel):
    assessment_timestamp: str
    patient_name: Optional[str] = None
    total_medicines_analyzed: int
    overall_status: str         # "RED", "YELLOW", "GREEN", "GREY"
    overall_status_label: str
    summary_headline: str
    language: str

    # Metrics
    total_interactions_identified: int
    serious_potential_interactions: int
    caution_warnings: int
    safe_combinations: int
    duplicate_medicines_count: int
    missing_information_count: int

    # Interaction details table
    interaction_table: List[MultiInteractionTableRow]

    # Simple patient explanation in selected language
    what_does_this_mean: str
    why_they_interact: str
    what_could_happen: str
    how_conditions_affect_risk: str
    what_to_discuss_with_doctor: List[str]

    # Action guidance
    action_guidance: str
    action_bullets: List[str]

    # Missing information list
    missing_information: List[str] = []
    unidentified_medicines: List[str] = []
    patient_conditions_evaluated: List[str] = []
    allergies_evaluated: List[str] = []

    # Diagnostic statuses and candidates for ambiguity resolution
    diagnostics_summary: Optional[List[Dict[str, Any]]] = []
    candidate_selections_needed: Optional[List[Dict[str, Any]]] = []
    therapeutic_duplications_count: Optional[int] = 0

    # Complete analyzed medicine details
    medicines_analyzed: List[MultiMedicineItem]

    disclaimer: str
