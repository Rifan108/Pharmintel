from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.auth import UserRegister, UserLogin, TokenResponse, UserResponse
from app.services.auth_service import AuthService
from app.utils.security import get_current_user_payload
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=TokenResponse)
def register(user_data: UserRegister, db: Session = Depends(get_db)):
    return AuthService.register_user(db, user_data)

@router.post("/login", response_model=TokenResponse)
def login(creds: UserLogin, db: Session = Depends(get_db)):
    return AuthService.login_user(db, creds)

@router.get("/me")
def get_current_user(payload: dict = Depends(get_current_user_payload), db: Session = Depends(get_db)):
    user_id = int(payload.get("sub"))
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    profile = {}
    if user.role == "customer" and user.customer_profile:
        profile = {
            "address": user.customer_profile.address,
            "city": user.customer_profile.city,
            "state": user.customer_profile.state,
            "postal_code": user.customer_profile.postal_code,
            "allergies": user.customer_profile.allergies,
            "medical_conditions": user.customer_profile.medical_conditions
        }
    elif user.role == "pharmacist" and user.pharmacist_profile:
        profile = {
            "pharmacy_id": user.pharmacist_profile.pharmacy_id,
            "license_number": user.pharmacist_profile.license_number,
            "qualification": user.pharmacist_profile.qualification,
            "is_verified": user.pharmacist_profile.is_verified
        }

    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "phone": user.phone,
        "role": user.role,
        "is_active": user.is_active,
        "profile": profile
    }
