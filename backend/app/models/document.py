from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from pydantic import BaseModel
import enum

from app.core.database import Base


class DocumentDB(Base):
    __tablename__ = "documents"

    id = Column(String, primary_key=True, index=True)
    original_filename = Column(String, nullable=False)
    stored_filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    uploaded_by = Column(Integer, nullable=False, index=True)
    uploaded_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    status = Column(String, default="processing")

    permissions = relationship("DocumentPermissionDB", back_populates="document", cascade="all, delete-orphan")


class PermissionType(str, enum.Enum):
    user = "user"
    role = "role"


class DocumentPermissionDB(Base):
    __tablename__ = "document_permissions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    document_id = Column(String, ForeignKey("documents.id"), nullable=False, index=True)
    permission_type = Column(SQLEnum(PermissionType), nullable=False)
    granted_to = Column(String, nullable=False, index=True)
    granted_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    document = relationship("DocumentDB", back_populates="permissions")


class DocumentResponse(BaseModel):
    id: str
    original_filename: str
    stored_filename: str
    file_path: str
    uploaded_by: int
    uploaded_at: datetime
    status: str

    class Config:
        from_attributes = True


class DocumentPermissionResponse(BaseModel):
    id: int
    permission_type: str
    granted_to: str
    granted_at: datetime

    class Config:
        from_attributes = True


class GrantAccessRequest(BaseModel):
    permission_type: PermissionType 
    granted_to: str  


class RevokeAccessRequest(BaseModel):
    permission_id: int
