import sys
print("==> Starting import process...", flush=True)

import logging
print("==> Logging imported", flush=True)

from fastapi import FastAPI, Depends, Request
print("==> FastAPI imported", flush=True)

from fastapi.middleware.cors import CORSMiddleware
print("==> CORS imported", flush=True)

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
print("==> SlowAPI imported", flush=True)

from app.core.dependencies import get_settings
from app.core.config import Settings, settings
print("==> Config imported", flush=True)

from app.core.database import init_db
print("==> Database imported", flush=True)

from app.api import documents
print("==> Documents API imported", flush=True)

from app.api import auth
print("==> Auth API imported", flush=True)

from app.api import chat
print("==> Chat API imported", flush=True)

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
def seed_admin_user():
    """
    One-time endpoint to create default admin user.
    Visit this URL once after deployment to create the admin account.
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
        if existing_users > 0:
            db.close()
            return {
                "status": "skipped",
                "message": f"Database already has {existing_users} user(s)",
                "note": "Admin user may already exist"
            }
        
        # Create admin user
        admin = UserDB(
            email="admin@company.com",
            hashed_password=hash_password("admin123"),
            role=UserRole.admin,
            is_active=1
        )
        db.add(admin)
        db.commit()
        db.close()
        
        return {
            "status": "success",
            "message": "Admin user created successfully!",
            "credentials": {
                "email": "admin@company.com",
                "password": "admin123",
                "note": "Please change this password after first login"
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to create admin user: {str(e)}"
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
