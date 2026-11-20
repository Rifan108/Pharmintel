from sqlalchemy.orm import Session
from fastapi import HTTPException
from typing import Optional, Dict, Any, List
from datetime import datetime

from app.models.cart import Cart, CartItem
from app.models.medicine import Medicine
from app.models.pharmacy import Pharmacy
from app.models.inventory import PharmacyInventory, MedicineBatch

class CartService:
    @classmethod
    def get_or_create_cart(cls, db: Session, user_id: Optional[int] = None, session_id: Optional[str] = None) -> Cart:
        if not user_id and not session_id:
            raise HTTPException(status_code=400, detail="Either user authentication or session identifier is required")

        cart = None
        if user_id:
            cart = db.query(Cart).filter(Cart.user_id == user_id).first()
            # If guest cart existed with session_id, merge it to user cart
            if session_id:
                guest_cart = db.query(Cart).filter(Cart.session_id == session_id, Cart.user_id == None).first()
                if guest_cart and guest_cart.items:
                    if not cart:
                        cart = guest_cart
                        cart.user_id = user_id
                        cart.session_id = None
                        db.commit()
                        db.refresh(cart)
                        return cart
                    else:
                        for g_item in guest_cart.items:
                            existing = db.query(CartItem).filter(
                                CartItem.cart_id == cart.id,
                                CartItem.medicine_id == g_item.medicine_id
                            ).first()
                            if existing:
                                existing.quantity += g_item.quantity
                            else:
                                g_item.cart_id = cart.id
                        db.delete(guest_cart)
                        db.commit()
        elif session_id:
            cart = db.query(Cart).filter(Cart.session_id == session_id).first()

        if not cart:
            cart = Cart(
                user_id=user_id,
                session_id=session_id if not user_id else None,
                created_at=datetime.utcnow()
            )
            db.add(cart)
            db.commit()
            db.refresh(cart)

        return cart

    @classmethod
    def get_cart_details(
        cls,
        db: Session,
        user_id: Optional[int] = None,
        session_id: Optional[str] = None,
        destination_pincode: Optional[str] = None
    ) -> Dict[str, Any]:
        cart = cls.get_or_create_cart(db, user_id=user_id, session_id=session_id)
        
        items_result = []
        subtotal = 0.0
        total_mrp = 0.0
        tax_total = 0.0
        has_rx_items = False
        requires_prescriptions = []

        for item in cart.items:
            med = item.medicine
            if not med:
                continue

            # Pharmacy and batch lookup
            pharm_id = item.pharmacy_id or 1
            pharm = db.query(Pharmacy).filter(Pharmacy.id == pharm_id).first()
            pharm_name = pharm.name if pharm else "Apollo Care Community Pharmacy"

            inv = db.query(PharmacyInventory).filter(
                PharmacyInventory.pharmacy_id == pharm_id,
                PharmacyInventory.medicine_id == med.id
            ).first()

            available_qty = inv.stock_quantity if inv else 0
            batch = None
            if inv:
                batch = db.query(MedicineBatch).filter(
                    MedicineBatch.inventory_id == inv.id,
                    MedicineBatch.is_recalled == False
                ).first()

            mrp = float(batch.mrp) if batch and batch.mrp else float(med.base_mrp)
            selling_price = float(batch.selling_price) if batch and batch.selling_price else round(mrp * 0.90, 2)
            
            # Life saving / critical medicines (e.g., insulin, oncology, cardiac) get 5% GST; other pharmaceuticals get 12%
            is_critical = any(cat in (med.therapeutic_category or "").lower() for cat in ["cardiology", "diabetes", "oncology", "immuno"])
            gst_rate = 5.0 if is_critical else 12.0

            item_subtotal = round(selling_price * item.quantity, 2)
            item_tax = round(item_subtotal * (gst_rate / 100.0), 2)
            discount_pct = round(((mrp - selling_price) / mrp) * 100, 1) if mrp > selling_price else 0.0

            is_rx = bool(med.requires_prescription or med.prescription_classification in ["Rx", "Schedule H", "Schedule H1", "Schedule X"])
            if is_rx:
                has_rx_items = True
                requires_prescriptions.append({
                    "medicine_id": med.id,
                    "brand_name": med.brand_name,
                    "schedule": med.prescription_classification
                })

            subtotal += item_subtotal
            total_mrp += (mrp * item.quantity)
            tax_total += item_tax

            items_result.append({
                "id": item.id,
                "medicine_id": med.id,
                "brand_name": med.brand_name,
                "generic_name": med.generic_name,
                "strength": med.strength,
                "dosage_form": med.dosage_form,
                "route_of_administration": med.route_of_administration,
                "manufacturer": med.manufacturer,
                "therapeutic_category": med.therapeutic_category,
                "prescription_classification": med.prescription_classification,
                "requires_prescription": is_rx,
                "quantity": item.quantity,
                "unit_price": selling_price,
                "mrp": mrp,
                "discount_percent": discount_pct,
                "total_price": item_subtotal,
                "available_stock": available_qty,
                "is_in_stock": available_qty >= item.quantity,
                "pharmacy_id": pharm_id,
                "pharmacy_name": pharm_name,
                "batch_number": batch.batch_number if batch else f"BAT-{med.id:03d}-01",
                "expiry_date": batch.expiry_date if batch else "2027-12-31"
            })

        # Calculate delivery fee: Free for orders >= ₹500, else ₹40
        delivery_fee = 0.0
        if subtotal > 0:
            if subtotal >= 500.0:
                delivery_fee = 0.0
            else:
                delivery_fee = 40.0

        savings_amount = round(total_mrp - subtotal, 2) if total_mrp > subtotal else 0.0
        total_payable = round(subtotal + tax_total + delivery_fee, 2)

        return {
            "cart_id": cart.id,
            "items": items_result,
            "items_count": sum(i["quantity"] for i in items_result),
            "distinct_count": len(items_result),
            "subtotal": round(subtotal, 2),
            "total_mrp": round(total_mrp, 2),
            "savings_amount": savings_amount,
            "tax_amount": round(tax_total, 2),
            "delivery_fee": delivery_fee,
            "free_delivery_threshold": 500.0,
            "amount_needed_for_free_delivery": max(0.0, round(500.0 - subtotal, 2)) if subtotal < 500 else 0.0,
            "total_payable": total_payable,
            "has_rx_items": has_rx_items,
            "requires_prescription_items": requires_prescriptions
        }

    @classmethod
    def add_to_cart(
        cls,
        db: Session,
        user_id: Optional[int],
        session_id: Optional[str],
        medicine_id: int,
        quantity: int = 1,
        pharmacy_id: Optional[int] = 1
    ) -> Dict[str, Any]:
        if quantity <= 0:
            raise HTTPException(status_code=400, detail="Quantity must be greater than zero")

        med = db.query(Medicine).filter(Medicine.id == medicine_id).first()
        if not med:
            raise HTTPException(status_code=404, detail="Medicine not found in catalog")

        cart = cls.get_or_create_cart(db, user_id=user_id, session_id=session_id)

        # Check inventory stock
        pharm_id = pharmacy_id or 1
        inv = db.query(PharmacyInventory).filter(
            PharmacyInventory.pharmacy_id == pharm_id,
            PharmacyInventory.medicine_id == medicine_id
        ).first()

        available_qty = inv.stock_quantity if inv else 100

        existing = db.query(CartItem).filter(
            CartItem.cart_id == cart.id,
            CartItem.medicine_id == medicine_id
        ).first()

        if existing:
            new_qty = existing.quantity + quantity
            if new_qty > available_qty:
                new_qty = available_qty
            existing.quantity = new_qty
            existing.updated_at = datetime.utcnow()
        else:
            final_qty = min(quantity, available_qty) if available_qty > 0 else quantity
            new_item = CartItem(
                cart_id=cart.id,
                medicine_id=medicine_id,
                pharmacy_id=pharm_id,
                quantity=final_qty,
                created_at=datetime.utcnow()
            )
            db.add(new_item)

        cart.updated_at = datetime.utcnow()
        db.commit()
        return cls.get_cart_details(db, user_id=user_id, session_id=session_id)

    @classmethod
    def update_item_quantity(
        cls,
        db: Session,
        user_id: Optional[int],
        session_id: Optional[str],
        cart_item_id: int,
        quantity: int
    ) -> Dict[str, Any]:
        cart = cls.get_or_create_cart(db, user_id=user_id, session_id=session_id)
        item = db.query(CartItem).filter(CartItem.id == cart_item_id, CartItem.cart_id == cart.id).first()
        if not item:
            raise HTTPException(status_code=404, detail="Item not found in your cart")

        if quantity <= 0:
            db.delete(item)
        else:
            # Check stock
            inv = db.query(PharmacyInventory).filter(
                PharmacyInventory.pharmacy_id == (item.pharmacy_id or 1),
                PharmacyInventory.medicine_id == item.medicine_id
            ).first()
            avail = inv.stock_quantity if inv else 100
            item.quantity = min(quantity, avail) if avail > 0 else quantity
            item.updated_at = datetime.utcnow()

        cart.updated_at = datetime.utcnow()
        db.commit()
        return cls.get_cart_details(db, user_id=user_id, session_id=session_id)

    @classmethod
    def remove_item(
        cls,
        db: Session,
        user_id: Optional[int],
        session_id: Optional[str],
        cart_item_id: int
    ) -> Dict[str, Any]:
        cart = cls.get_or_create_cart(db, user_id=user_id, session_id=session_id)
        item = db.query(CartItem).filter(CartItem.id == cart_item_id, CartItem.cart_id == cart.id).first()
        if item:
            db.delete(item)
            cart.updated_at = datetime.utcnow()
            db.commit()
        return cls.get_cart_details(db, user_id=user_id, session_id=session_id)

    @classmethod
    def clear_cart(
        cls,
        db: Session,
        user_id: Optional[int],
        session_id: Optional[str]
    ) -> Dict[str, Any]:
        cart = cls.get_or_create_cart(db, user_id=user_id, session_id=session_id)
        for itm in cart.items:
            db.delete(itm)
        cart.updated_at = datetime.utcnow()
        db.commit()
        return cls.get_cart_details(db, user_id=user_id, session_id=session_id)
