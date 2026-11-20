from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app.database import get_db
from app.schemas.qr import QRVerifyRequest, QRVerifyResponse, QRSampleItem
from app.services.qr_service import MedicineQRService

router = APIRouter(prefix="/qr", tags=["Medicine QR Information System"])

@router.post("/verify", response_model=QRVerifyResponse)
def verify_medicine_qr(
    req: QRVerifyRequest,
    db: Session = Depends(get_db)
):
    """
    Scans and authoritatively verifies a medicine package QR / 2D barcode.
    Strictly enforces:
    'Only claim authenticity verification when connected to an authoritative verification source.'
    """
    if not req.raw_qr_content.strip():
        raise HTTPException(status_code=400, detail="QR content cannot be empty")

    return MedicineQRService.verify_medicine_qr(db, req.raw_qr_content, req.source_type or "camera_scan")

@router.post("/scan-image", response_model=QRVerifyResponse)
async def scan_qr_image(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Decodes a medicine packaging photo containing a 2D QR code or DataMatrix using OpenCV & PIL,
    then authoritatively verifies against CDSCO registries and licensed pharmacy central ledger.
    """
    content = await file.read()
    if not content or len(content) == 0:
        raise HTTPException(status_code=400, detail="Uploaded image file is empty.")

    try:
        return MedicineQRService.scan_qr_image(db, content, file.filename or "upload.jpg")
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image decoding failed: {str(e)}")

@router.get("/samples", response_model=List[QRSampleItem])
def get_sample_test_codes(db: Session = Depends(get_db)):
    """
    Returns authentic, recalled, and unverified sample codes for instantaneous testing.
    """
    return MedicineQRService.get_sample_test_codes(db)

@router.get("/generate-batch/{batch_id}")
def generate_batch_qr(batch_id: int, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Generates a printable GS1 / CDSCO-compliant QR code for an inventory batch.
    """
    try:
        return MedicineQRService.generate_batch_qr_data_url(db, batch_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
