from datetime import timedelta
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.database import get_db
from app.models.user import UserDB
from app.core.security import verify_password, create_access_token
from app.core.dependencies import get_settings
from app.core.config import Settings

limiter = Limiter(key_func=get_remote_address)

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/login")
@limiter.limit("5/minute")
def login(
    request: Request,
    data: LoginRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings)
):
    user = db.query(UserDB).filter(UserDB.email == data.email).first()

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=401,
            detail="User account is inactive"
        )

    if not verify_password(data.password, user.hashed_password):
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials"
        )

    access_token = create_access_token(
        data={
            "sub": str(user.id),
            "role": user.role
        },
        expires_delta=timedelta(minutes=30)
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }
