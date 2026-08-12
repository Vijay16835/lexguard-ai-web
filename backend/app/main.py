import logging
from fastapi import FastAPI, APIRouter, Depends, HTTPException, status
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
        
    # 3. Pre-initialize OCR engines (Tesseract path & EasyOCR singleton)
    from app.services.ocr_service import ocr_service
    logger.info("[Startup] Pre-initializing OCR engines...")
    try:
        import asyncio
        await asyncio.to_thread(ocr_service.init_easyocr)
        logger.info("[Startup] OCR engines pre-initialized successfully.")
    except Exception as ocr_err:
        logger.warning(f"[Startup] Non-fatal OCR pre-initialization warning: {ocr_err}")

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)

        # 1. Strict-Transport-Security (HSTS)
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        # 2. Content-Security-Policy (CSP)
        response.headers["Content-Security-Policy"] = "default-src 'self'; frame-ancestors 'none'; object-src 'none'"

        # 3. X-Frame-Options
        response.headers["X-Frame-Options"] = "DENY"

        # 4. X-Content-Type-Options
        response.headers["X-Content-Type-Options"] = "nosniff"

        # 5. Referrer-Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # 6. Cache-Control
        if "Cache-Control" not in response.headers:
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"

        return response

# Set all Security Headers middleware
app.add_middleware(SecurityHeadersMiddleware)

# Set all CORS enabled origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://vijay16835.github.io",
        "https://vijay16835.github.io/lexguard-ai-web",
    ],
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
debug_router = APIRouter()

@debug_router.post("/test-email")
async def test_email_endpoint(recipient: str = None):
    from app.services.email_service import email_service
    import smtplib
    import socket
    
    if not recipient:
        recipient = settings.EMAIL_FROM or settings.SMTP_EMAIL
        
    if not recipient:
        raise HTTPException(
            status_code=400,
            detail="No recipient email provided, and EMAIL_FROM / SMTP_EMAIL settings keys are empty."
        )
        
    logger.info(f"[Debug API] test-email called. Target recipient: {recipient}")
    
    try:
        res = email_service.run_smtp_diagnostics(recipient)
        return res
    except Exception as e:
        logger.error(f"[Debug API] Brevo REST API Connection / Diagnostic Failure: {type(e).__name__}: {str(e)}", exc_info=True)
        
        if isinstance(e, socket.gaierror):
            detail = f"DNS failure: Could not resolve Brevo API server. Details: {str(e)}"
        elif isinstance(e, (socket.timeout, TimeoutError)):
            detail = f"Network timeout: Connection to Brevo API server timed out. Details: {str(e)}"
        elif "Authentication failure" in str(e) or "unauthorized" in str(e).lower():
            detail = f"Brevo API Authentication Failure: {str(e)}"
        else:
            detail = f"Diagnostic Failure: {type(e).__name__}: {str(e)}"
            
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail
        )

app.include_router(debug_router, prefix=f"{settings.API_V1_STR}/debug", tags=["debug"])
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
