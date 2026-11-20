from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, List
from app.database import get_db
from app.models.pharmacy import Pharmacy
from app.services.pharmacy_service import PharmacyFinderService
from app.utils.distance import calculate_haversine_distance

router = APIRouter(prefix="/pharmacies", tags=["Pharmacies"])

@router.get("/nearby")
def get_nearby_pharmacies(
    lat: Optional[float] = Query(None, description="User current latitude"),
    lng: Optional[float] = Query(None, description="User current longitude"),
    radius_km: float = Query(5.0, description="Search radius in kilometers (1, 3, 5, 10, 20)"),
    search_name: Optional[str] = Query(None, description="Filter pharmacy by name"),
    city: Optional[str] = Query(None, description="Filter by city"),
    postal_code: Optional[str] = Query(None, description="Filter by postal PIN code"),
    medicine_id: Optional[int] = Query(None, description="Filter pharmacies with medicine in stock"),
    medicine_name: Optional[str] = Query(None, description="Search for medicine name in stock"),
    open_now_only: bool = Query(False, description="Filter only pharmacies currently open"),
    sort_by: str = Query("distance", description="Sort by 'distance' or 'rating'"),
    db: Session = Depends(get_db)
):
    """
    Nearby Medical Shops & Pharmacy Discovery Endpoint.
    Combines verified licensed community chemists with OpenStreetMap Overpass live results,
    operating hours calculation, and verified medicine inventory availability.
    """
    return PharmacyFinderService.search_pharmacies(
        db=db,
        lat=lat,
        lng=lng,
        radius_km=radius_km,
        search_name=search_name,
        city=city,
        postal_code=postal_code,
        medicine_id=medicine_id,
        medicine_name=medicine_name,
        open_now_only=open_now_only,
        sort_by=sort_by
    )

@router.get("/geocode")
def geocode_location(
    q: str = Query(..., description="City, locality, area, or PIN code to geocode")
):
    """
    Geocodes area, city, or PIN code into latitude, longitude, and formatted name.
    """
    res = PharmacyFinderService.geocode_query(q)
    if not res:
        raise HTTPException(status_code=404, detail="Location could not be geocoded.")
    return {
        "latitude": res[0],
        "longitude": res[1],
        "display_name": res[2],
        "area": res[3] if len(res) > 3 else "",
        "city": res[4] if len(res) > 4 else "",
        "state": res[5] if len(res) > 5 else "",
        "postal_code": res[6] if len(res) > 6 else ""
    }

@router.get("/reverse-geocode")
def reverse_geocode_location(
    lat: float = Query(..., description="Latitude"),
    lng: float = Query(..., description="Longitude")
):
    """
    Reverse geocodes coordinates into locality/suburb name, area, city, and state.
    """
    return PharmacyFinderService.reverse_geocode_details(lat, lng)

@router.get("")
def list_pharmacies(
    lat: Optional[float] = Query(None, description="Customer latitude for distance calculation"),
    lng: Optional[float] = Query(None, description="Customer longitude for distance calculation"),
    medicine_id: Optional[int] = Query(None, description="Filter pharmacies having this medicine in stock"),
    city: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Existing list endpoint kept for full backwards compatibility.
    """
    res = PharmacyFinderService.search_pharmacies(
        db=db,
        lat=lat,
        lng=lng,
        city=city,
        medicine_id=medicine_id,
        radius_km=25.0
    )
    return res.get("pharmacies", [])

@router.get("/{pharmacy_id}")
def get_pharmacy_profile(pharmacy_id: int, db: Session = Depends(get_db)):
    pharmacy = db.query(Pharmacy).filter(Pharmacy.id == pharmacy_id).first()
    if not pharmacy:
        raise HTTPException(status_code=404, detail="Pharmacy not found")
    return pharmacy
