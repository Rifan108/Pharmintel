from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from app.database import get_db
from app.utils.security import security_bearer, decode_access_token
from app.schemas.assistant import (
    ChatQueryRequest,
    ChatQueryResponse,
    ClearSessionRequest,
    EscalatePharmacistRequest,
    EscalatePharmacistResponse
)
from app.services.rag_assistant_service import RAGAssistantService

router = APIRouter(prefix="/assistant", tags=["AI Health Assistant"])

@router.post("/chat", response_model=ChatQueryResponse)
async def chat_with_assistant(
    req: ChatQueryRequest,
    db: Session = Depends(get_db),
    credentials = Depends(security_bearer)
):
    user_id = None
    if credentials and credentials.credentials:
        payload = decode_access_token(credentials.credentials)
        if payload:
            user_id = int(payload.get("sub"))

    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    return await RAGAssistantService.process_chat_message(
        db=db,
        session_id=req.session_id,
        message=req.message,
        user_id=user_id,
        language=req.language or "en",
        mode=req.mode or "ai_assistant",
        patient_name=req.patient_name
    )

@router.post("/clear-session")
def clear_session(
    req: ClearSessionRequest,
    db: Session = Depends(get_db)
):
    return RAGAssistantService.clear_session(db, req.session_id)

@router.post("/escalate-pharmacist", response_model=EscalatePharmacistResponse)
def escalate_to_pharmacist(
    req: EscalatePharmacistRequest,
    db: Session = Depends(get_db)
):
    return RAGAssistantService.escalate_to_pharmacist(
        db, req.session_id, req.patient_name, req.notes
    )

@router.get("/history/{session_id}")
def get_session_history(
    session_id: str,
    db: Session = Depends(get_db)
):
    return RAGAssistantService.get_session_history(db, session_id)
