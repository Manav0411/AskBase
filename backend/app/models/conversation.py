from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Float
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field

from app.core.database import Base
from app.models.document import DocumentResponse


class ConversationDB(Base):
    __tablename__ = "conversations"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    document_id = Column(String, nullable=False, index=True)
    title = Column(String, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    messages = relationship("MessageDB", back_populates="conversation", cascade="all, delete-orphan")


class MessageDB(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=False, index=True)
    role = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    confidence_score = Column(Float, nullable=True)  # LLM self-assessed confidence (0.0-1.0)

    conversation = relationship("ConversationDB", back_populates="messages")


class MessageResponse(BaseModel):
    id: int
    role: str
    content: str
    timestamp: datetime
    confidence_score: Optional[float] = None  # LLM self-assessed confidence (0.0-1.0)

    class Config:
        from_attributes = True


class ConversationCreate(BaseModel):
    document_id: str
    title: Optional[str] = "New Conversation"


class ConversationResponse(BaseModel):
    id: str
    user_id: int
    document_id: str
    title: str
    created_at: datetime
    updated_at: datetime
    messages: Optional[List[MessageResponse]] = None
    document: Optional[DocumentResponse] = None
    suggested_questions: Optional[List[str]] = []  # AI-generated suggested questions

    class Config:
        from_attributes = True


class ChatMessageRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000, description="User message (1-4000 characters)")


class ChatMessageResponse(BaseModel):
    conversation_id: str
    message: MessageResponse
    assistant_reply: MessageResponse
