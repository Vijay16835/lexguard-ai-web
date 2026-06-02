import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import auth, documents, user, ai, notifications, chat, multilingual
from app.core.config import settings
from app.db.session import Base
from app import models

# Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database tables creation is handled by Firestore dynamically
Base.metadata.create_all()

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

@app.on_event("startup")
async def startup_event():
    logger.info("[Startup] Running startup validation checks...")
    
    # 1. Database connectivity check
    from app.services.firebase_service import firebase_service
    db_ok = firebase_service.check_connectivity()
    if not db_ok:
        logger.critical("[Startup] Database connectivity check failed! Please verify DATABASE_URL and pooler configuration.")
        
    # 2. Email/SMTP configuration check
    from app.services.email_service import email_service
    email_ok = email_service.validate_configuration()
    if not email_ok:
        logger.warning("[Startup] Email/SMTP configuration check failed! OTP features might be unavailable.")

# Set all CORS enabled origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify real origins for Flutter web or apps
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["authentication"])
app.include_router(documents.router, prefix=f"{settings.API_V1_STR}/documents", tags=["documents"])
app.include_router(user.router, prefix=f"{settings.API_V1_STR}/user", tags=["user"])
app.include_router(ai.router, prefix=f"{settings.API_V1_STR}/ai", tags=["ai"])
app.include_router(chat.router, prefix=f"{settings.API_V1_STR}/chat", tags=["chat"])
app.include_router(multilingual.router, prefix=f"{settings.API_V1_STR}/multilingual", tags=["multilingual"])
app.include_router(notifications.router, prefix=f"{settings.API_V1_STR}/notifications", tags=["notifications"])

@app.get("/")
def root():
    return {"message": "Welcome to LexGuard AI Backend API"}
