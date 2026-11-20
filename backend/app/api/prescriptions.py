import os
import shutil
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Form
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Optional

from app.database import get_db
from app.config import settings
from app.utils.security import get_current_user_payload, require_role
from app.models.prescription import Prescription, PrescriptionItem
from app.models.user import User
from app.services.ocr_service import PrescriptionOCRService
from app.schemas.prescription import PrescriptionResponse, PharmacistVerificationRequest

router = APIRouter(prefix="/prescriptions", tags=["Prescriptions & OCR"])

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".pdf"}

@router.post("/upload")
async def upload_prescription(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user_payload: dict = Depends(get_current_user_payload)
):
    user_id = int(user_payload.get("sub"))
    ext = os.path.splitext(file.filename)[1].lower()

    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format '{ext}'. Allowed formats: JPG, JPEG, PNG, PDF."
        )

    # Save file safely
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    safe_filename = f"rx_u{user_id}_{timestamp}_{file.filename.replace(' ', '_')}"
    file_path = os.path.join(settings.PRESCRIPTION_DIR, safe_filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Extract OCR Text & Structured Entities
    raw_text, confidence = PrescriptionOCRService.extract_text_from_file(file_path)
    parsed_data = PrescriptionOCRService.parse_prescription_text(db, raw_text)

    # Create Prescription Record
    rx = Prescription(
        customer_id=user_id,
        file_path=file_path,
        file_name=file.filename,
        file_type=file.content_type or "application/octet-stream",
        ocr_status="COMPLETED",
        overall_confidence=confidence,
        raw_extracted_text=raw_text,
        verification_status="PENDING_REVIEW",
        doctor_name=parsed_data.get("doctor_name"),
        patient_name=parsed_data.get("patient_name"),
        prescription_date=parsed_data.get("prescription_date")
    )
    db.add(rx)
    db.commit()
    db.refresh(rx)

    # Add extracted items
    for item in parsed_data.get("items", []):
        pi = PrescriptionItem(
            prescription_id=rx.id,
            medicine_name_raw=item["raw_line"],
            matched_medicine_id=item["matched_medicine_id"],
            strength=item["strength"],
            dosage_form=item["dosage_form"],
            frequency=item["frequency"],
            duration=item["duration"],
            instructions=item["instructions"],
            confidence_score=item["confidence_score"],
            pharmacist_confirmed=False
        )
        db.add(pi)
    db.commit()

    return {
        "message": "Prescription uploaded and processed successfully",
        "prescription_id": rx.id,
        "overall_confidence": confidence,
        "verification_status": rx.verification_status,
        "doctor_name": rx.doctor_name,
        "patient_name": rx.patient_name,
        "prescription_date": rx.prescription_date,
        "extracted_items_count": len(parsed_data.get("items", [])),
        "items": parsed_data.get("items", [])
    }

@router.get("/my-prescriptions")
def get_user_prescriptions(
    db: Session = Depends(get_db),
    user_payload: dict = Depends(get_current_user_payload)
):
    user_id = int(user_payload.get("sub"))
    rxs = db.query(Prescription).filter(Prescription.customer_id == user_id).order_by(Prescription.uploaded_at.desc()).all()
    results = []
    for rx in rxs:
        items = [{
            "id": itm.id,
            "raw": itm.medicine_name_raw,
            "matched_name": itm.matched_medicine.brand_name if itm.matched_medicine else None,
            "strength": itm.strength,
            "frequency": itm.frequency,
            "duration": itm.duration,
            "confidence": itm.confidence_score,
            "confirmed": itm.pharmacist_confirmed
        } for itm in rx.items]

        results.append({
            "id": rx.id,
            "file_name": rx.file_name,
            "uploaded_at": rx.uploaded_at,
            "status": rx.verification_status,
            "confidence": rx.overall_confidence,
            "doctor_name": rx.doctor_name,
            "patient_name": rx.patient_name,
            "items": items
        })
    return results

@router.get("/pending-reviews")
def get_pending_prescriptions_for_pharmacist(
    db: Session = Depends(get_db),
    user_payload: dict = Depends(require_role(["pharmacist", "pharmacy_admin", "platform_admin"]))
):
    rxs = db.query(Prescription).filter(
        Prescription.verification_status == "PENDING_REVIEW"
    ).order_by(Prescription.uploaded_at.desc()).all()

    results = []
    for rx in rxs:
        results.append({
            "id": rx.id,
            "customer_id": rx.customer_id,
            "customer_name": rx.customer.full_name if rx.customer else "Unknown",
            "file_name": rx.file_name,
            "uploaded_at": rx.uploaded_at,
            "confidence": rx.overall_confidence,
            "doctor_name": rx.doctor_name,
            "patient_name": rx.patient_name,
            "raw_text": rx.raw_extracted_text,
            "items": [{
                "id": itm.id,
                "medicine_name_raw": itm.medicine_name_raw,
                "matched_medicine_id": itm.matched_medicine_id,
                "strength": itm.strength,
                "dosage_form": itm.dosage_form,
                "frequency": itm.frequency,
                "duration": itm.duration,
                "instructions": itm.instructions,
                "confidence_score": itm.confidence_score,
                "pharmacist_confirmed": itm.pharmacist_confirmed
            } for itm in rx.items]
        })
    return results

@router.post("/{prescription_id}/verify")
def verify_prescription(
    prescription_id: int,
    req: PharmacistVerificationRequest,
    db: Session = Depends(get_db),
    user_payload: dict = Depends(require_role(["pharmacist", "pharmacy_admin", "platform_admin"]))
):
    rx = db.query(Prescription).filter(Prescription.id == prescription_id).first()
    if not rx:
        raise HTTPException(status_code=404, detail="Prescription not found")

    pharmacist_id = int(user_payload.get("sub"))
    rx.verification_status = req.status
    rx.pharmacist_notes = req.notes
    rx.verified_by_pharmacist_id = pharmacist_id
    rx.verified_at = datetime.utcnow()

    # Update confirmed items
    for c_item in req.confirmed_items:
        item_id = c_item.get("item_id")
        pi = db.query(PrescriptionItem).filter(
            PrescriptionItem.id == item_id,
            PrescriptionItem.prescription_id == prescription_id
        ).first()
        if pi:
            pi.pharmacist_confirmed = c_item.get("confirmed", True)
            if c_item.get("matched_medicine_id"):
                pi.matched_medicine_id = c_item["matched_medicine_id"]
            if c_item.get("corrected_name"):
                pi.pharmacist_corrected_name = c_item["corrected_name"]

    db.commit()
    return {"message": f"Prescription marked as {req.status} successfully", "prescription_id": rx.id}
