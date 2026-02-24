import sys
import logging
from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.core.dependencies import get_settings
from app.core.config import Settings, settings
from app.core.database import init_db
from app.api import documents
from app.api import auth
from app.api import chat

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="AskBase API", version="2.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS configuration - supports multiple origins separated by commas
origins = [origin.strip() for origin in settings.cors_origins.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    logger.info("==> Application starting...")
    logger.info("==> Skipping database initialization - will initialize on first request")
    logger.info("==> Application startup complete - ready to accept connections")

@app.get("/")
def root():
    return {"message": "AskBase API is running", "status": "ok"}

@app.get("/seed-admin")
def seed_admin_user(force: bool = False):
    """
    Endpoint to create default demo users.
    Visit /seed-admin to create users or /seed-admin?force=true to recreate them.
    """
    from app.core.database import get_session_local, init_db
    from app.models.user import UserDB, UserRole
    from app.core.security import hash_password
    
    try:
        init_db()
        SessionLocal = get_session_local()
        db = SessionLocal()
        
        # Check if users already exist
        existing_users = db.query(UserDB).count()
        
        if existing_users > 0 and not force:
            db.close()
            return {
                "status": "skipped",
                "message": f"Database already has {existing_users} user(s)",
                "note": "Use /seed-admin?force=true to recreate all users"
            }
        
        # If force=true, delete existing users
        if force and existing_users > 0:
            db.query(UserDB).delete()
            db.commit()
        
        # Create default users for each role
        default_users = [
            {
                "email": "admin@example.com",
                "password": "admin123",
                "role": UserRole.admin
            },
            {
                "email": "hr@example.com",
                "password": "hr123",
                "role": UserRole.hr
            },
            {
                "email": "engineer@example.com",
                "password": "engineer123",
                "role": UserRole.engineer
            },
            {
                "email": "intern@example.com",
                "password": "intern123",
                "role": UserRole.intern
            }
        ]
        
        created_users = []
        for user_data in default_users:
            user = UserDB(
                email=user_data["email"],
                hashed_password=hash_password(user_data["password"]),
                role=user_data["role"],
                is_active=1
            )
            db.add(user)
            created_users.append({
                "email": user_data["email"],
                "password": user_data["password"],
                "role": user_data["role"].value
            })
        
        db.commit()
        db.close()
        
        return {
            "status": "success",
            "message": f"Created {len(created_users)} demo users successfully!",
            "credentials": created_users,
            "note": "Please change these passwords after first login"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to create users: {str(e)}"
        }

@app.get("/health")
def health_check(settings: Settings = Depends(get_settings)):
    from app.core.database import get_engine
    from sqlalchemy import text
    from app.vector.store import vector_store, get_cache_stats
    
    health_status = {
        "status": "ok",
        "environment": settings.env,
        "app": settings.app_name,
        "version": "2.0 - Chat enabled",
        "dependencies": {},
        "cache": {}
    }
    
    try:
        engine = get_engine()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        health_status["dependencies"]["database"] = "ok"
    except Exception as e:
        health_status["status"] = "degraded"
        health_status["dependencies"]["database"] = f"error: {str(e)}"
    
    if vector_store is not None:
        health_status["dependencies"]["vector_store"] = "ok"
        health_status["cache"] = get_cache_stats()
    else:
        health_status["dependencies"]["vector_store"] = "not_loaded"
        health_status["cache"] = {"is_loaded": False}
    
    if settings.groq_api_key:
        health_status["dependencies"]["groq_api"] = "configured"
    else:
        health_status["status"] = "degraded"
        health_status["dependencies"]["groq_api"] = "not_configured"
    
    return health_status
    
app.include_router(documents.router)
app.include_router(auth.router)
app.include_router(chat.router)
