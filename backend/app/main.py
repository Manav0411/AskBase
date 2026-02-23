import logging
from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.core.dependencies import get_settings
from app.core.config import Settings, settings
from app.core.database import init_db
from app.vector.store import load_vector_store
from app.api import documents
from app.api import auth
from app.api import chat

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('askbase.log')
    ]
)

logger = logging.getLogger(__name__)

limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="AskBase API", version="2.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5174", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_event():
    logger.info("Starting application...")
    init_db()
    logger.info("Database initialized successfully")
    
    load_vector_store()
    logger.info("Vector store initialization complete")
    logger.info("Application startup complete")

@app.get("/health")
def health_check(settings: Settings = Depends(get_settings)):
    from app.core.database import engine
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
