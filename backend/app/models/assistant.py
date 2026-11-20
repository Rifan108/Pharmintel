from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    title = Column(String(255), default="Medical Consultation")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    messages = relationship("ChatMessage", back_populates="conversation", cascade="all, delete-orphan")

class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(20), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    sources_json = Column(Text, nullable=True)   # JSON string of cited medical references
    guardrail_flag = Column(String(50), nullable=True) # NONE, EMERGENCY, PRESCRIBE_BLOCKED, DIAGNOSE_BLOCKED
    timestamp = Column(DateTime, default=datetime.utcnow)

    conversation = relationship("Conversation", back_populates="messages")

class AIKnowledgeSource(Base):
    """
    Verified Medical Knowledge Repository for RAG Retrieval
    """
    __tablename__ = "ai_knowledge_sources"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    category = Column(String(100), nullable=False, index=True) # Pharmacology, Disease, Drug Safety, Dosage Guideline
    content = Column(Text, nullable=False)
    reference_source = Column(String(255), nullable=False) # CDSCO, BNF, WHO, FDA, PubMed
    verification_date = Column(String(50), default="2026-03-15")
    embedding_vector_json = Column(Text, nullable=True) # JSON array of dense vector floats
    created_at = Column(DateTime, default=datetime.utcnow)
