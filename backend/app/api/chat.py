import uuid
import logging
from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.dependencies import get_current_user
from app.core.database import get_db
from app.core.config import settings
from app.models.document import DocumentDB, DocumentPermissionDB, PermissionType
from app.models.conversation import (
    ConversationDB,
    MessageDB,
    ConversationCreate,
    ConversationResponse,
    ChatMessageRequest,
    ChatMessageResponse,
    MessageResponse
)
from app.models.common import PaginatedResponse, create_pagination_meta
from app.vector.store import retrieve, retrieve_first_chunks
from app.llm.groq import generate_answer, generate_document_summary, generate_suggested_questions, LLMError

logger = logging.getLogger(__name__)
limiter = Limiter(key_func=get_remote_address)


def is_summary_request(message: str) -> bool:
    """Detect if user is asking for a summary or overview of the document."""
    message_lower = message.lower().strip()
    summary_keywords = [
        'summary', 'summarize', 'summarise', 'overview', 'main points',
        'key points', 'tldr', 'tl;dr', 'brief', 'what is this about',
        'what does this document', 'what\'s this document', 'tell me about this',
        'describe this', 'explain this document', 'what is in this'
    ]
    return any(keyword in message_lower for keyword in summary_keywords)

router = APIRouter(prefix="/conversations", tags=["conversations"])


def check_document_access(document: DocumentDB, user_id: int, user_role: str, db: Session) -> bool:
    """
    Check if a user has access to a document.
    Returns True if user has access, False otherwise.
    
    Access is granted if:
    1. User is the document uploader
    2. User is an admin
    3. Explicit permission granted to user
    4. Explicit permission granted to user's role
    """
    if document.uploaded_by == user_id:
        return True
    
    if user_role == "admin":
        return True
    
    permissions = db.query(DocumentPermissionDB).filter(
        DocumentPermissionDB.document_id == document.id
    ).all()
    
    for perm in permissions:
        if perm.permission_type == PermissionType.user and perm.granted_to == str(user_id):
            return True
        if perm.permission_type == PermissionType.role and perm.granted_to == user_role:
            return True
    
    return False


@router.post("/", response_model=ConversationResponse)
def create_conversation(
    data: ConversationCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new conversation for a specific document.
    """
    document = db.query(DocumentDB).filter(DocumentDB.id == data.document_id).first()
    if not document:
        logger.warning(f"Conversation creation failed - document not found: {data.document_id}")
        raise HTTPException(status_code=404, detail="Document not found")
    
    if document.status != "completed":
        logger.warning(
            f"Conversation creation failed - document {data.document_id} status: {document.status}"
        )
        raise HTTPException(
            status_code=400, 
            detail=f"Document is not ready. Status: {document.status}"
        )
    
    if not check_document_access(document, current_user["id"], current_user["role"], db):
        raise HTTPException(status_code=403, detail="Access denied to this document")
    
    conversation_id = str(uuid.uuid4())
    conversation = ConversationDB(
        id=conversation_id,
        user_id=current_user["id"],
        document_id=data.document_id,
        title=data.title or f"Chat about {document.original_filename}"
    )
    
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    
    # Generate welcome message with document summary and suggested questions
    suggested_questions = []
    try:
        # Get initial chunks from document for context
        context_docs = retrieve_first_chunks(data.document_id, k=10)
        context = "\n\n".join([doc.page_content for doc in context_docs])
        
        # Generate document summary
        summary = generate_document_summary(context)
        logger.info(f"Generated summary for conversation {conversation_id}")
        
        # Generate suggested questions
        suggested_questions = generate_suggested_questions(context, document.original_filename)
        logger.info(f"Generated {len(suggested_questions)} suggested questions")
        
        # Create welcome message with the summary
        welcome_message = MessageDB(
            conversation_id=conversation_id,
            role="assistant",
            content=summary,
            timestamp=datetime.now(timezone.utc),
            confidence_score=1.0
        )
        
        db.add(welcome_message)
        db.commit()
        db.refresh(welcome_message)
        
        # Return conversation with welcome message and suggested questions
        conversation_response = ConversationResponse.from_orm(conversation)
        conversation_response.messages = [MessageResponse.from_orm(welcome_message)]
        conversation_response.suggested_questions = suggested_questions
        
        return conversation_response
        
    except Exception as e:
        logger.error(f"Error generating welcome content: {str(e)}")
        # Return conversation without welcome message if generation fails
        conversation_response = ConversationResponse.from_orm(conversation)
        conversation_response.messages = []
        conversation_response.suggested_questions = []
        return conversation_response


@router.get("/", response_model=PaginatedResponse[ConversationResponse])
def list_conversations(
    skip: int = 0,
    limit: int = None,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all conversations for the current user with pagination.
    
    - skip: Number of records to skip (default: 0)
    - limit: Maximum number of records to return (default: 20, max: 100)
    """
    if limit is None:
        limit = settings.default_page_size
    
    limit = min(limit, settings.max_page_size)
    
    total = db.query(ConversationDB).filter(
        ConversationDB.user_id == current_user["id"]
    ).count()
    
    conversations = db.query(ConversationDB).filter(
        ConversationDB.user_id == current_user["id"]
    ).order_by(ConversationDB.updated_at.desc()).offset(skip).limit(limit).all()
    
    return PaginatedResponse(
        items=conversations,
        pagination=create_pagination_meta(total, skip, limit)
    )


@router.get("/{conversation_id}", response_model=ConversationResponse)
def get_conversation(
    conversation_id: str,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific conversation with all its messages.
    """
    conversation = db.query(ConversationDB).filter(
        ConversationDB.id == conversation_id
    ).first()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    if conversation.user_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    document = db.query(DocumentDB).filter(
        DocumentDB.id == conversation.document_id
    ).first()
    
    response_dict = {
        "id": conversation.id,
        "user_id": conversation.user_id,
        "document_id": conversation.document_id,
        "title": conversation.title,
        "created_at": conversation.created_at,
        "updated_at": conversation.updated_at,
        "messages": conversation.messages,
        "document": document
    }
    
    # Generate suggested questions if this is a new conversation (only has welcome message)
    if len(conversation.messages) == 1:
        try:
            context_docs = retrieve_first_chunks(conversation.document_id, k=10)
            context = "\n\n".join([doc.page_content for doc in context_docs])
            suggested_questions = generate_suggested_questions(context, document.original_filename if document else "document")
            response_dict["suggested_questions"] = suggested_questions
            logger.info(f"Generated {len(suggested_questions)} suggested questions for conversation {conversation_id}")
        except Exception as e:
            logger.error(f"Error generating suggested questions: {str(e)}")
            response_dict["suggested_questions"] = []
    else:
        response_dict["suggested_questions"] = []
    
    return ConversationResponse(**response_dict)


@router.post("/{conversation_id}/messages", response_model=ChatMessageResponse)
@limiter.limit("20/minute")
def send_message(
    request: Request,
    conversation_id: str,
    data: ChatMessageRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Send a message in a conversation and get AI response.
    This is the main chat endpoint.
    """
    conversation = db.query(ConversationDB).filter(
        ConversationDB.id == conversation_id
    ).first()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    if conversation.user_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    document = db.query(DocumentDB).filter(DocumentDB.id == conversation.document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document no longer exists")
    
    if not check_document_access(document, current_user["id"], current_user["role"], db):
        raise HTTPException(status_code=403, detail="Access denied to document")
    
    try:
        user_message = MessageDB(
            conversation_id=conversation_id,
            role="user",
            content=data.message,
            timestamp=datetime.now(timezone.utc)
        )
        db.add(user_message)
        db.commit()
        db.refresh(user_message)
        
        previous_messages = db.query(MessageDB).filter(
            MessageDB.conversation_id == conversation_id,
            MessageDB.id < user_message.id
        ).order_by(MessageDB.timestamp.desc()).limit(9).all()
        
        previous_messages.reverse()
        
        message_history = [
            {"role": msg.role, "content": msg.content}
            for msg in previous_messages
        ]
        
        message_history.append({"role": "user", "content": data.message})
        
        if is_summary_request(data.message):
            logger.info(f"Summary request detected for conversation {conversation_id}")
            results = retrieve_first_chunks(
                document_id=conversation.document_id,
                k=settings.retrieval_k
            )
        else:
            results = retrieve(
                query=data.message,
                document_id=conversation.document_id,
                k=settings.retrieval_k
            )
        
        retrieved_texts = [doc.page_content for doc in results]
        
        if not retrieved_texts:
            context = "No relevant information found in the document."
        else:
            context = "\n\n".join(retrieved_texts)
        
        try:
            answer, confidence_score = generate_answer(
                messages=message_history,
                context=context
            )
        except LLMError as llm_error:
            logger.error(f"LLM Error for conversation {conversation_id}: {str(llm_error)}")
            answer = "I apologize, but I'm having trouble generating a response right now. Please try again in a moment."
            confidence_score = None
        
        assistant_message = MessageDB(
            conversation_id=conversation_id,
            role="assistant",
            content=answer,
            timestamp=datetime.now(timezone.utc),
            confidence_score=confidence_score
        )
        db.add(assistant_message)
        
        conversation.updated_at = datetime.now(timezone.utc)
        
        db.commit()
        db.refresh(assistant_message)
        
        return ChatMessageResponse(
            conversation_id=conversation_id,
            message=MessageResponse.from_orm(user_message),
            assistant_reply=MessageResponse.from_orm(assistant_message)
        )
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error in send_message for conversation {conversation_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while processing your message. Please try again."
        )


@router.delete("/{conversation_id}")
def delete_conversation(
    conversation_id: str,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a conversation and all its messages.
    """
    conversation = db.query(ConversationDB).filter(
        ConversationDB.id == conversation_id
    ).first()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    if conversation.user_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    db.delete(conversation)
    db.commit()
    
    return {"status": "deleted", "conversation_id": conversation_id}
