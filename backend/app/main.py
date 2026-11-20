import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import engine, Base, SessionLocal
from app.utils.seed_data import seed_database
from app.api import (
    auth, medicines, interactions, alternatives,
    pharmacies, inventory, prescriptions, orders,
    assistant, ml, printing, analytics, qr,
    medicine_intelligence, cart, addresses, payments
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure database schema and seed verified clinical data
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()
    yield
    # Shutdown logic if any

app = FastAPI(
    title="PharmIntel API",
    description="AI-Powered Smart Pharmacy Network for Drug Safety and Medicine Delivery",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(medicines.router, prefix=settings.API_V1_STR)
app.include_router(interactions.router, prefix=settings.API_V1_STR)
app.include_router(alternatives.router, prefix=settings.API_V1_STR)
app.include_router(pharmacies.router, prefix=settings.API_V1_STR)
app.include_router(inventory.router, prefix=settings.API_V1_STR)
app.include_router(prescriptions.router, prefix=settings.API_V1_STR)
app.include_router(orders.router, prefix=settings.API_V1_STR)
app.include_router(assistant.router, prefix=settings.API_V1_STR)
app.include_router(ml.router, prefix=settings.API_V1_STR)
app.include_router(printing.router, prefix=settings.API_V1_STR)
app.include_router(analytics.router, prefix=settings.API_V1_STR)
app.include_router(qr.router, prefix=settings.API_V1_STR)
app.include_router(medicine_intelligence.router, prefix=settings.API_V1_STR)
app.include_router(cart.router, prefix=settings.API_V1_STR)
app.include_router(addresses.router, prefix=settings.API_V1_STR)
app.include_router(payments.router, prefix=settings.API_V1_STR)

@app.get("/")
def root():
    return {
        "platform": "PharmIntel",
        "description": "AI-Powered Smart Pharmacy Network for Drug Safety and Medicine Delivery",
        "version": "1.0.0",
        "status": "Operational",
        "ai_safety_layer": "Active (Deterministic Clinical Rules + PHARMINTEL-HYBRIDGNN)",
        "docs_url": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
