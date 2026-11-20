from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.user import User, Customer, Pharmacist
from app.schemas.auth import UserRegister, UserLogin, TokenResponse
from app.utils.security import hash_password, verify_password, create_access_token
from datetime import timedelta

class AuthService:
    @staticmethod
    def register_user(db: Session, reg_data: UserRegister) -> TokenResponse:
        existing = db.query(User).filter(User.email == reg_data.email).first()
        if existing:
            raise HTTPException(status_code=400, detail="A user with this email address already exists")

        new_user = User(
            email=reg_data.email,
            hashed_password=hash_password(reg_data.password),
            full_name=reg_data.full_name,
            phone=reg_data.phone,
            role=reg_data.role if reg_data.role in ["customer", "pharmacist", "pharmacy_admin"] else "customer",
            is_active=True
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        # Create role specific profile
        if new_user.role == "customer":
            cust = Customer(
                user_id=new_user.id,
                address=reg_data.address,
                city=reg_data.city,
                state=reg_data.state,
                postal_code=reg_data.postal_code
            )
            db.add(cust)
        elif new_user.role == "pharmacist":
            pharm = Pharmacist(
                user_id=new_user.id,
                pharmacy_id=reg_data.pharmacy_id,
                license_number=reg_data.license_number or f"KSPC-REG-{new_user.id}992",
                qualification=reg_data.qualification or "B.Pharm / M.Pharm",
                is_verified=False
            )
            db.add(pharm)
        db.commit()

        token_data = {
            "sub": str(new_user.id),
            "email": new_user.email,
            "role": new_user.role,
            "name": new_user.full_name
        }
        token = create_access_token(token_data)
        return TokenResponse(
            access_token=token,
            token_type="bearer",
            user={
                "id": new_user.id,
                "email": new_user.email,
                "name": new_user.full_name,
                "role": new_user.role,
                "phone": new_user.phone
            }
        )

    @staticmethod
    def login_user(db: Session, creds: UserLogin) -> TokenResponse:
        user = db.query(User).filter(User.email == creds.email).first()
        if not user or not verify_password(creds.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is deactivated"
            )

        token_data = {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role,
            "name": user.full_name
        }
        token = create_access_token(token_data)
        return TokenResponse(
            access_token=token,
            token_type="bearer",
            user={
                "id": user.id,
                "email": user.email,
                "name": user.full_name,
                "role": user.role,
                "phone": user.phone
            }
        )
