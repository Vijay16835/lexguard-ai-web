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
        
    # 2. Email/SMTP configuration check
    from app.services.email_service import email_service
    email_ok = email_service.validate_configuration()
    if not email_ok:
        logger.warning("[Startup] Email/SMTP configuration check failed! OTP features might be unavailable.")

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

@debug_router.get("/tess-diag")
async def tesseract_diagnostics():
    import subprocess
    import shutil
    import os
    import pytesseract
    
    results = {}
    
    # 1. which tesseract
    which_tess = shutil.which("tesseract")
    results["which_tesseract"] = which_tess
    
    # 2. tesseract version
    try:
        tess_ver_process = subprocess.run(["tesseract", "--version"], capture_output=True, text=True)
        results["tesseract_version_stdout"] = tess_ver_process.stdout
        results["tesseract_version_stderr"] = tess_ver_process.stderr
        results["tesseract_version_code"] = tess_ver_process.returncode
    except Exception as e:
        results["tesseract_version_error"] = str(e)
        
    # 3. settings / env
    results["env_tesseract_cmd"] = os.environ.get("TESSERACT_CMD")
    results["settings_tesseract_cmd"] = getattr(settings, "TESSERACT_CMD", None)
    
    # 4. pytesseract info
    results["pytesseract_cmd"] = pytesseract.pytesseract.tesseract_cmd
    
    # 5. system path and other info
    results["path"] = os.environ.get("PATH")
    
    # 6. check python path execution
    try:
        tess_path = results["settings_tesseract_cmd"] or which_tess or "tesseract"
        cmd_ver = subprocess.run([tess_path, "--version"], capture_output=True, text=True)
        results["tess_path_version_stdout"] = cmd_ver.stdout
        results["tess_path_version_stderr"] = cmd_ver.stderr
    except Exception as e:
        results["tess_path_version_error"] = str(e)
        
    return results

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
