import os
import uuid
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, UploadFile, File, HTTPException, Depends, Request
from sqlalchemy.orm import Session
from pypdf import PdfReader
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.dependencies import get_current_user, require_role
from app.core.database import get_db
from app.core.config import settings
from app.models.document import (
    DocumentDB, 
    DocumentResponse, 
    DocumentPermissionDB,
    DocumentPermissionResponse,
    GrantAccessRequest,
    RevokeAccessRequest,
    PermissionType
)
from app.models.common import PaginatedResponse, create_pagination_meta
from app.vector.store import ingest_text, delete_document_vectors

logger = logging.getLogger(__name__)
limiter = Limiter(key_func=get_remote_address)

router = APIRouter(prefix="/documents", tags=["documents"])

UPLOAD_DIR = "uploads"
MAX_FILE_SIZE = settings.max_file_size_mb * 1024 * 1024
ALLOWED_TYPES = ["application/pdf"]

os.makedirs(UPLOAD_DIR, exist_ok=True)


def ingest_file(document_id: str, file_path: str, db_session):
    """Background task to process PDF and ingest into vector store"""
    try:
        logger.info(f"Starting ingestion for document {document_id}")
        reader = PdfReader(file_path)
        full_text = ""

        for page in reader.pages:
            text = page.extract_text()
            if text:
                full_text += text + "\n"

        if full_text.strip():
            ingest_text(document_id, full_text)
            logger.info(f"Vector ingestion completed for document {document_id}")
            
            try:
                document = db_session.query(DocumentDB).filter(DocumentDB.id == document_id).first()
                if document:
                    document.status = "completed"
                    db_session.commit()
                    logger.info(f"Document {document_id} status updated to completed")
                else:
                    logger.error(f"Document {document_id} not found in database")
            except Exception as db_error:
                db_session.rollback()
                logger.error(f"Database error updating document {document_id}: {str(db_error)}")
                raise
        else:
            logger.warning(f"No text extracted from document {document_id}")
            try:
                document = db_session.query(DocumentDB).filter(DocumentDB.id == document_id).first()
                if document:
                    document.status = "failed"
                    db_session.commit()
                    logger.info(f"Document {document_id} status updated to failed")
            except Exception as db_error:
                db_session.rollback()
                logger.error(f"Database error updating failed status for {document_id}: {str(db_error)}")
                
    except Exception as e:
        logger.error(f"Error ingesting document {document_id}: {str(e)}", exc_info=True)
        try:
            db_session.rollback()
            document = db_session.query(DocumentDB).filter(DocumentDB.id == document_id).first()
            if document:
                document.status = "failed"
                db_session.commit()
                logger.info(f"Document {document_id} marked as failed after exception")
        except Exception as db_error:
            logger.error(f"Failed to update document status to failed for {document_id}: {str(db_error)}")
    finally:
        try:
            db_session.close()
            logger.debug(f"Database session closed for document {document_id}")
        except Exception as close_error:
            logger.error(f"Error closing database session for {document_id}: {str(close_error)}")


@router.post("/upload", response_model=DocumentResponse)
@limiter.limit("10/hour")
async def upload_document(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are allowed."
        )

    file_extension = os.path.splitext(file.filename)[1]
    safe_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = os.path.join(UPLOAD_DIR, safe_filename)

    total_size = 0

    with open(file_path, "wb") as buffer:
        while True:
            chunk = await file.read(1024)
            if not chunk:
                break

            total_size += len(chunk)

            if total_size > MAX_FILE_SIZE:
                buffer.close()
                os.remove(file_path)
                raise HTTPException(
                    status_code=400,
                    detail="File too large. Max size is 10MB."
                )

            buffer.write(chunk)

    document_id = str(uuid.uuid4())

    document = DocumentDB(
        id=document_id,
        original_filename=file.filename,
        stored_filename=safe_filename,
        file_path=file_path,
        uploaded_by=current_user["id"],
        uploaded_at=datetime.now(timezone.utc),
        status="processing"
    )

    db.add(document)
    db.commit()
    db.refresh(document)

    from app.core.database import SessionLocal
    bg_db = SessionLocal()
    background_tasks.add_task(ingest_file, document_id, file_path, bg_db)

    return document


@router.get("/", response_model=PaginatedResponse[DocumentResponse])
def list_all_documents(
    skip: int = 0,
    limit: int = None,
    current_user = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    """
    List all documents (admin only) with pagination.
    
    - skip: Number of records to skip (default: 0)
    - limit: Maximum number of records to return (default: 20, max: 100)
    """
    if limit is None:
        limit = settings.default_page_size
    
    limit = min(limit, settings.max_page_size)
    
    total = db.query(DocumentDB).count()
    
    documents = db.query(DocumentDB).order_by(
        DocumentDB.uploaded_at.desc()
    ).offset(skip).limit(limit).all()
    
    return PaginatedResponse(
        items=documents,
        pagination=create_pagination_meta(total, skip, limit)
    )


@router.post("/{document_id}/share", response_model=DocumentPermissionResponse)
def grant_document_access(
    document_id: str,
    data: GrantAccessRequest,
    current_user = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    """
    Grant access to a document for a specific user or role.
    Admin only.
    
    Examples:
    - Grant to user: {"permission_type": "user", "granted_to": "2"}
    - Grant to role: {"permission_type": "role", "granted_to": "engineer"}
    """
    document = db.query(DocumentDB).filter(DocumentDB.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    existing = db.query(DocumentPermissionDB).filter(
        DocumentPermissionDB.document_id == document_id,
        DocumentPermissionDB.permission_type == data.permission_type,
        DocumentPermissionDB.granted_to == data.granted_to
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=400, 
            detail=f"Permission already exists: {data.permission_type} '{data.granted_to}' already has access to this document"
        )
    
    permission = DocumentPermissionDB(
        document_id=document_id,
        permission_type=data.permission_type,
        granted_to=data.granted_to
    )
    
    db.add(permission)
    db.commit()
    db.refresh(permission)
    
    return permission


@router.delete("/{document_id}/share/{permission_id}")
def revoke_document_access(
    document_id: str,
    permission_id: int,
    current_user = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    """
    Revoke document access permission.
    Admin only.
    """
    document = db.query(DocumentDB).filter(DocumentDB.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    permission = db.query(DocumentPermissionDB).filter(
        DocumentPermissionDB.id == permission_id,
        DocumentPermissionDB.document_id == document_id
    ).first()
    
    if not permission:
        raise HTTPException(status_code=404, detail="Permission not found")
    
    db.delete(permission)
    db.commit()
    
    return {"status": "revoked", "permission_id": permission_id}


@router.get("/accessible", response_model=PaginatedResponse[DocumentResponse])
def list_accessible_documents(
    skip: int = 0,
    limit: int = None,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all documents the current user has access to with pagination.
    
    - skip: Number of records to skip (default: 0)
    - limit: Maximum number of records to return (default: 20, max: 100)
    """
    if limit is None:
        limit = settings.default_page_size
    
    limit = min(limit, settings.max_page_size)
    
    user_id = current_user["id"]
    user_role = current_user["role"]
    
    if user_role == "admin":
        total = db.query(DocumentDB).filter(
            DocumentDB.status == "completed"
        ).count()
        documents = db.query(DocumentDB).filter(
            DocumentDB.status == "completed"
        ).order_by(DocumentDB.uploaded_at.desc()).offset(skip).limit(limit).all()
        return PaginatedResponse(
            items=documents,
            pagination=create_pagination_meta(total, skip, limit)
        )
    
    user_documents = db.query(DocumentDB).filter(
        DocumentDB.uploaded_by == user_id,
        DocumentDB.status == "completed"
    ).all()
    
    user_permissions = db.query(DocumentPermissionDB).filter(
        DocumentPermissionDB.permission_type == PermissionType.user,
        DocumentPermissionDB.granted_to == str(user_id)
    ).all()
    
    role_permissions = db.query(DocumentPermissionDB).filter(
        DocumentPermissionDB.permission_type == PermissionType.role,
        DocumentPermissionDB.granted_to == user_role
    ).all()
    
    accessible_doc_ids = set([doc.id for doc in user_documents])
    accessible_doc_ids.update([perm.document_id for perm in user_permissions])
    accessible_doc_ids.update([perm.document_id for perm in role_permissions])
    
    total = db.query(DocumentDB).filter(
        DocumentDB.id.in_(accessible_doc_ids),
        DocumentDB.status == "completed"
    ).count()
    
    documents = db.query(DocumentDB).filter(
        DocumentDB.id.in_(accessible_doc_ids),
        DocumentDB.status == "completed"
    ).order_by(DocumentDB.uploaded_at.desc()).offset(skip).limit(limit).all()
    
    return PaginatedResponse(
        items=documents,
        pagination=create_pagination_meta(total, skip, limit)
    )


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(
    document_id: str,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific document by ID.
    Returns the document if the user has access to it.
    """
    document = db.query(DocumentDB).filter(DocumentDB.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    user_id = current_user["id"]
    user_role = current_user["role"]
    
    if document.uploaded_by == user_id:
        return document
    
    if user_role == "admin":
        return document
    
    permissions = db.query(DocumentPermissionDB).filter(
        DocumentPermissionDB.document_id == document.id
    ).all()
    
    for perm in permissions:
        if perm.permission_type == PermissionType.user and perm.granted_to == str(user_id):
            return document
        if perm.permission_type == PermissionType.role and perm.granted_to == user_role:
            return document
    
    raise HTTPException(status_code=403, detail="Access denied to this document")


@router.get("/{document_id}/permissions", response_model=list[DocumentPermissionResponse])
def list_document_permissions(
    document_id: str,
    current_user = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    """
    List all permissions for a document.
    Admin only.
    """
    document = db.query(DocumentDB).filter(DocumentDB.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    permissions = db.query(DocumentPermissionDB).filter(
        DocumentPermissionDB.document_id == document_id
    ).all()
    
    return permissions


@router.delete("/{document_id}")
def delete_document(
    document_id: str,
    current_user = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    """
    Delete a document, its file, permissions, and vector embeddings.
    Admin only.
    """
    document = db.query(DocumentDB).filter(DocumentDB.id == document_id).first()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    try:
        if os.path.exists(document.file_path):
            os.remove(document.file_path)
            logger.info(f"Deleted file: {document.file_path}")
        
        delete_document_vectors(document_id)
        logger.info(f"Deleted vectors for document: {document_id}")
        
        db.delete(document)
        db.commit()
        logger.info(f"Deleted document from database: {document_id}")
        
        return {
            "status": "deleted",
            "document_id": document_id,
            "filename": document.original_filename
        }
    
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting document {document_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete document: {str(e)}"
        )
