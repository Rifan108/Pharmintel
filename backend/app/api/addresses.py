from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from app.database import get_db
from app.utils.security import get_current_user_payload
from app.models.address import SavedAddress
from app.models.pharmacy import Pharmacy

router = APIRouter(prefix="/addresses", tags=["Delivery Addresses & Serviceability"])

class AddressCreateRequest(BaseModel):
    recipient_name: str
    phone: str
    address_line1: str
    address_line2: Optional[str] = None
    city: str = "Bengaluru"
    state: str = "Karnataka"
    pincode: str
    address_type: str = "Home" # Home, Work, Other
    is_default: bool = False

class AddressUpdateRequest(BaseModel):
    recipient_name: Optional[str] = None
    phone: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    address_type: Optional[str] = None
    is_default: Optional[bool] = None

@router.get("")
def list_addresses(
    db: Session = Depends(get_db),
    user_payload: dict = Depends(get_current_user_payload)
):
    user_id = int(user_payload.get("sub"))
    addresses = db.query(SavedAddress).filter(SavedAddress.user_id == user_id).order_by(SavedAddress.is_default.desc(), SavedAddress.created_at.desc()).all()
    return [{
        "id": a.id,
        "recipient_name": a.recipient_name,
        "phone": a.phone,
        "address_line1": a.address_line1,
        "address_line2": a.address_line2,
        "city": a.city,
        "state": a.state,
        "pincode": a.pincode,
        "address_type": a.address_type,
        "is_default": a.is_default,
        "created_at": a.created_at
    } for a in addresses]

@router.post("")
def create_address(
    req: AddressCreateRequest,
    db: Session = Depends(get_db),
    user_payload: dict = Depends(get_current_user_payload)
):
    user_id = int(user_payload.get("sub"))

    # Strict compliance: recipient_name must be manually entered, not dummy placeholder
    cleaned_name = req.recipient_name.strip()
    if not cleaned_name or cleaned_name.lower() in ["string", "dummy", "patient", "test", "john doe"]:
        raise HTTPException(
            status_code=400,
            detail="A valid recipient/patient name must be manually entered."
        )

    # Clean pincode
    pin = req.pincode.strip().replace(" ", "")
    if len(pin) != 6 or not pin.isdigit():
        raise HTTPException(
            status_code=400,
            detail="Please provide a valid 6-digit Indian PIN code."
        )

    # If is_default, unmark others
    if req.is_default:
        db.query(SavedAddress).filter(SavedAddress.user_id == user_id).update({"is_default": False})

    addr = SavedAddress(
        user_id=user_id,
        recipient_name=cleaned_name,
        phone=req.phone.strip(),
        address_line1=req.address_line1.strip(),
        address_line2=req.address_line2.strip() if req.address_line2 else None,
        city=req.city.strip(),
        state=req.state.strip(),
        pincode=pin,
        address_type=req.address_type,
        is_default=req.is_default,
        created_at=datetime.utcnow()
    )
    db.add(addr)
    db.commit()
    db.refresh(addr)

    return {
        "message": "Address saved successfully",
        "id": addr.id,
        "recipient_name": addr.recipient_name,
        "pincode": addr.pincode,
        "is_default": addr.is_default
    }

@router.delete("/{address_id}")
def delete_address(
    address_id: int,
    db: Session = Depends(get_db),
    user_payload: dict = Depends(get_current_user_payload)
):
    user_id = int(user_payload.get("sub"))
    addr = db.query(SavedAddress).filter(SavedAddress.id == address_id, SavedAddress.user_id == user_id).first()
    if not addr:
        raise HTTPException(status_code=404, detail="Address not found")
    db.delete(addr)
    db.commit()
    return {"message": "Address removed successfully"}

@router.get("/serviceability")
def check_pincode_serviceability(
    pincode: str = Query(..., description="6-digit Indian postal code"),
    db: Session = Depends(get_db)
):
    pin = pincode.strip().replace(" ", "")
    if len(pin) != 6 or not pin.isdigit():
        return {
            "serviceable": False,
            "pincode": pin,
            "reason": "Invalid postal code format. Must be a 6-digit Indian PIN code."
        }

    # Bengaluru Express Zone (560xxx)
    if pin.startswith("560"):
        # Match nearest pharmacy
        nearest = db.query(Pharmacy).first()
        pharmacy_name = nearest.name if nearest else "Apollo Care Community Pharmacy (Bellandur Hub)"
        return {
            "serviceable": True,
            "pincode": pin,
            "region": "Bengaluru Metropolitan Region",
            "tier": "Express Zone (Same-Day / 2 Hours)",
            "estimated_delivery_time": "Within 2 Hours (Hyperlocal Express)",
            "delivery_fee": 40.0,
            "free_delivery_threshold": 500.0,
            "cash_on_delivery_available": True,
            "fulfilling_pharmacy": pharmacy_name,
            "licensing_authority": "Drugs Control Department, Karnataka"
        }
    
    # Karnataka / Major Metro Hubs
    first_two = pin[:2]
    if first_two in ["56", "57", "58", "59"]: # Karnataka
        region = "Karnataka Regional Hub"
        delivery_time = "Next-Day Delivery (24 Hours)"
    elif first_two in ["11", "12"]: # Delhi NCR
        region = "Delhi NCR Region"
        delivery_time = "1-2 Business Days"
    elif first_two in ["40", "41", "42"]: # Mumbai / Maharashtra
        region = "Mumbai Metropolitan Region"
        delivery_time = "1-2 Business Days"
    elif first_two in ["50"]: # Hyderabad
        region = "Hyderabad Metropolitan Area"
        delivery_time = "Next-Day Delivery"
    elif first_two in ["60"]: # Chennai
        region = "Chennai Metropolitan Area"
        delivery_time = "Next-Day Delivery"
    elif first_two in ["70"]: # Kolkata
        region = "Kolkata Region"
        delivery_time = "2 Business Days"
    else:
        region = "All-India Standard Delivery Network"
        delivery_time = "2-3 Business Days"

    return {
        "serviceable": True,
        "pincode": pin,
        "region": region,
        "tier": "Standard Secured Pharma Courier",
        "estimated_delivery_time": delivery_time,
        "delivery_fee": 40.0,
        "free_delivery_threshold": 500.0,
        "cash_on_delivery_available": True,
        "fulfilling_pharmacy": "PharmIntel Central Medical Fulfillment Center",
        "licensing_authority": "Central Drugs Standard Control Organisation (CDSCO)"
    }
