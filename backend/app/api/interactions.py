from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from app.database import get_db
from app.utils.security import security_bearer, decode_access_token
from app.schemas.interaction import (
    InteractionCheckRequest, DDIResponse,
    CheckRegimenCompatibilityRequest, CompatibilityReportResponse,
    PatientProfileSaveRequest, AssessmentHistoryItem,
    MultiMedicineCheckRequest, MultiMedicineReportResponse
)
from app.services.ddi_layer2_service import DDILayer2Service
from app.services.patient_safety_service import PatientSafetyIntelligenceService
from app.services.print_service import A4PrintService

router = APIRouter(prefix="/interactions", tags=["Drug Interactions & Patient Safety"])

@router.post("/check", response_model=DDIResponse)
def check_interactions(req: InteractionCheckRequest, db: Session = Depends(get_db)):
    """
    Existing Quick Pair & Multi-Medicine Interaction Checker.
    Evaluates pairwise drug-drug interactions using Layer 1 (Curated BNF/FDA) + Layer 2 (HYBRIDGNN).
    """
    if not req.medicine_ids or len(req.medicine_ids) < 2:
        raise HTTPException(
            status_code=400,
            detail="At least 2 medicines must be selected to evaluate pairwise drug-drug interactions."
        )
    return DDILayer2Service.check_interaction_network(db, req.medicine_ids, req.enable_ml_prediction)

@router.post("/patient-safety/check", response_model=CompatibilityReportResponse)
def check_regimen_compatibility(
    req: CheckRegimenCompatibilityRequest,
    db: Session = Depends(get_db),
    credentials = Depends(security_bearer)
):
    """
    Whole-regimen medication compatibility analysis for a proposed medicine against
    the patient's medical conditions, allergies, existing medicines, and organ status.
    """
    user_id = None
    if credentials and credentials.credentials:
        payload = decode_access_token(credentials.credentials)
        if payload:
            user_id = int(payload.get("sub"))

    if not req.proposed_medicine.medicine_name.strip():
        raise HTTPException(status_code=400, detail="Proposed medicine name is required.")

    return PatientSafetyIntelligenceService.analyze_regimen_compatibility(db, req, user_id=user_id)

@router.post("/multi-check", response_model=MultiMedicineReportResponse)
def check_multiple_medicines_compatibility(
    req: MultiMedicineCheckRequest,
    db: Session = Depends(get_db)
):
    """
    Multiple Medicine Compatibility Engine.
    Evaluates every pair across N medicines, multi-drug combinations (Triple Whammy, etc.),
    duplicate active ingredients, drug-disease contraindications, and drug-allergy warnings.
    Supports English, Kannada, Hindi, Malayalam, Tamil, Telugu, and Marathi.
    """
    return PatientSafetyIntelligenceService.analyze_multiple_medicines_compatibility(db, req)


@router.get("/patient-safety/profile")
def get_patient_profile(
    db: Session = Depends(get_db),
    credentials = Depends(security_bearer)
):
    """
    Retrieves the authenticated patient's saved medical conditions, allergies, and current medications.
    """
    if not credentials or not credentials.credentials:
        return {"health_profile": {"medical_conditions": [], "allergies": []}, "existing_medicines": []}

    payload = decode_access_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    user_id = int(payload.get("sub"))
    return PatientSafetyIntelligenceService.get_patient_profile(db, user_id)

@router.post("/patient-safety/profile")
def save_patient_profile(
    req: PatientProfileSaveRequest,
    db: Session = Depends(get_db),
    credentials = Depends(security_bearer)
):
    """
    Saves the confirmed patient medical conditions, allergies, and current medication list.
    """
    if not credentials or not credentials.credentials:
        raise HTTPException(status_code=401, detail="Authentication required to save health profile.")

    payload = decode_access_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    user_id = int(payload.get("sub"))
    PatientSafetyIntelligenceService.save_patient_profile(db, user_id, req.health_profile, req.existing_medicines)
    return {"message": "Patient health profile and medication list saved successfully."}

@router.get("/patient-safety/history", response_model=List[AssessmentHistoryItem])
def get_assessment_history(
    db: Session = Depends(get_db),
    credentials = Depends(security_bearer)
):
    """
    Retrieves past patient compatibility assessments.
    """
    if not credentials or not credentials.credentials:
        return []

    payload = decode_access_token(credentials.credentials)
    if not payload:
        return []

    user_id = int(payload.get("sub"))
    return PatientSafetyIntelligenceService.get_assessment_history(db, user_id)

@router.post("/patient-safety/pdf")
def download_patient_safety_pdf(
    report_data: Dict[str, Any]
):
    """
    Generates a professional ISO 216 A4 Patient Medication Safety Report PDF.
    """
    try:
        pdf_buffer = A4PrintService.generate_patient_safety_report_pdf(report_data)
        if "medicines_analyzed" in report_data or "interaction_table" in report_data:
            med_count = len(report_data.get("medicines_analyzed", []))
            filename = f"PharmIntel_Compatibility_Report_{med_count}_Medicines.pdf"
        else:
            proposed = report_data.get("proposed_medicine") or {}
            proposed_name = proposed.get("medicine_name", "Medication")
            clean_name = "".join(c for c in proposed_name if c.isalnum() or c in (' ', '_', '-')).strip() or "Medication"
            filename = f"PharmIntel_Safety_Report_{clean_name}.pdf"

        return Response(
            content=pdf_buffer.getvalue(),
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")
