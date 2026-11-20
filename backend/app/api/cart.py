from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel

from app.database import get_db
from app.utils.security import get_current_user_payload
from app.services.cart_service import CartService

router = APIRouter(prefix="/cart", tags=["Online Pharmacy Cart"])

class AddToCartRequest(BaseModel):
    medicine_id: int
    quantity: int = 1
    pharmacy_id: Optional[int] = 1

class UpdateCartItemRequest(BaseModel):
    quantity: int

def resolve_auth_and_session(
    authorization: Optional[str] = Header(None),
    x_session_id: Optional[str] = Header(None)
):
    user_id = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
        try:
            from app.utils.security import decode_access_token
            payload = decode_access_token(token)
            if payload:
                user_id = int(payload.get("sub"))
        except Exception:
            pass
    session_id = x_session_id or ("guest-session-default" if not user_id else None)
    return user_id, session_id

@router.get("")
def get_cart(
    destination_pincode: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    auth_info = Depends(resolve_auth_and_session)
):
    user_id, session_id = auth_info
    return CartService.get_cart_details(
        db,
        user_id=user_id,
        session_id=session_id,
        destination_pincode=destination_pincode
    )

@router.post("/items")
def add_item_to_cart(
    req: AddToCartRequest,
    db: Session = Depends(get_db),
    auth_info = Depends(resolve_auth_and_session)
):
    user_id, session_id = auth_info
    return CartService.add_to_cart(
        db,
        user_id=user_id,
        session_id=session_id,
        medicine_id=req.medicine_id,
        quantity=req.quantity,
        pharmacy_id=req.pharmacy_id
    )

@router.put("/items/{item_id}")
def update_cart_item(
    item_id: int,
    req: UpdateCartItemRequest,
    db: Session = Depends(get_db),
    auth_info = Depends(resolve_auth_and_session)
):
    user_id, session_id = auth_info
    return CartService.update_item_quantity(
        db,
        user_id=user_id,
        session_id=session_id,
        cart_item_id=item_id,
        quantity=req.quantity
    )

@router.delete("/items/{item_id}")
def remove_cart_item(
    item_id: int,
    db: Session = Depends(get_db),
    auth_info = Depends(resolve_auth_and_session)
):
    user_id, session_id = auth_info
    return CartService.remove_item(
        db,
        user_id=user_id,
        session_id=session_id,
        cart_item_id=item_id
    )

@router.delete("")
def clear_cart(
    db: Session = Depends(get_db),
    auth_info = Depends(resolve_auth_and_session)
):
    user_id, session_id = auth_info
    return CartService.clear_cart(
        db,
        user_id=user_id,
        session_id=session_id
    )
