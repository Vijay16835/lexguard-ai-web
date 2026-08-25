from pydantic_settings import BaseSettings
from pydantic import model_validator
import os
import urllib.parse
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    PROJECT_NAME: str = "LexGuard AI"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "your-secret-key-for-jwt-keep-it-safe"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 11520

    POSTGRES_SERVER: str = "aws-1-ap-south-1.pooler.supabase.com"
    POSTGRES_USER: str = "postgres.jrrbplpzqzvvtwyqomdi"
    POSTGRES_PASSWORD: str = "[YOUR-SUPABASE-PASSWORD]"
    POSTGRES_DB: str = "postgres"

    DATABASE_URL: str = "postgresql://postgres.jrrbplpzqzvvtwyqomdi:[YOUR-SUPABASE-PASSWORD]@aws-1-ap-south-1.pooler.supabase.com:6543/postgres"

    @model_validator(mode='after')
    def check_and_assemble_db_config(self) -> 'Settings':
        # 1. Verify and correct POSTGRES_SERVER (Transaction Pooler Host)
        # If it is aws-0-ap-south-1.pooler.supabase.com, change it to aws-1-ap-south-1.pooler.supabase.com
        if self.POSTGRES_SERVER == "aws-0-ap-south-1.pooler.supabase.com":
            self.POSTGRES_SERVER = "aws-1-ap-south-1.pooler.supabase.com"

        # 2. Verify and correct POSTGRES_USER to match the tenant exactly for the pooler
        if self.POSTGRES_SERVER.endswith(".pooler.supabase.com") and not self.POSTGRES_USER.endswith(".jrrbplpzqzvvtwyqomdi"):
            self.POSTGRES_USER = "postgres.jrrbplpzqzvvtwyqomdi"

        # 3. Assemble/sanitize DATABASE_URL
        # Check if DATABASE_URL was overridden by environment or .env (which Pydantic reads into self.DATABASE_URL)
        env_database_url = os.environ.get("DATABASE_URL") or self.DATABASE_URL
        
        # If the URL contains default placeholders or is empty:
        if not env_database_url or "[YOUR-SUPABASE-PASSWORD]" in env_database_url:
            # Construct from individual fields
            pwd = self.POSTGRES_PASSWORD
            # Make sure it's URL-encoded
            encoded_pwd = urllib.parse.quote_plus(urllib.parse.unquote(pwd))
            port = 6543 if "pooler" in self.POSTGRES_SERVER else 5432
            self.DATABASE_URL = f"postgresql://{self.POSTGRES_USER}:{encoded_pwd}@{self.POSTGRES_SERVER}:{port}/{self.POSTGRES_DB}"
        else:
            # Sanitize the provided DATABASE_URL
            self.DATABASE_URL = self.sanitize_db_url(env_database_url)
            
        # 4. Print resolved database host, user, port, and database name (masking password)
        try:
            parsed = urllib.parse.urlparse(self.DATABASE_URL)
            # Mask password
            masked_pwd = "****" if parsed.password else "None"
            print(f"[Database Config] Resolved Database Connection Parameters:")
            print(f"  - Host: {parsed.hostname}")
            print(f"  - User: {parsed.username}")
            print(f"  - Port: {parsed.port or (6543 if 'pooler' in str(parsed.hostname) else 5432)}")
            print(f"  - Database: {parsed.path.lstrip('/')}")
            print(f"  - Password: {masked_pwd}")
        except Exception as print_err:
            print(f"[Database Config] Error printing resolved details: {print_err}")
            
        return self

    def sanitize_db_url(self, db_url: str) -> str:
        try:
            if "://" in db_url:
                scheme, rest = db_url.split("://", 1)
            else:
                scheme = "postgresql"
                rest = db_url

            if "@" in rest:
                userinfo, hostinfo = rest.rsplit("@", 1)
            else:
                userinfo = rest
                hostinfo = ""

            if ":" in userinfo:
                username, password = userinfo.split(":", 1)
            else:
                username = userinfo
                password = self.POSTGRES_PASSWORD

            decoded_password = urllib.parse.unquote(password)
            encoded_password = urllib.parse.quote_plus(decoded_password)

            if "/" in hostinfo:
                host_port, path = hostinfo.split("/", 1)
            else:
                host_port = hostinfo
                path = ""

            if ":" in host_port:
                host, port = host_port.split(":", 1)
            else:
                host = host_port
                port = "6543"

            # Correct pooler prefix
            if host == "aws-0-ap-south-1.pooler.supabase.com":
                host = "aws-1-ap-south-1.pooler.supabase.com"

            # Ensure correct user for pooler
            if host.endswith(".pooler.supabase.com") and not username.endswith(".jrrbplpzqzvvtwyqomdi"):
                username = "postgres.jrrbplpzqzvvtwyqomdi"

            # Update settings fields based on sanitized URL
            self.POSTGRES_SERVER = host
            self.POSTGRES_USER = username
            self.POSTGRES_DB = path

            netloc = f"{username}:{encoded_password}@{host}:{port}"
            return f"{scheme}://{netloc}/{path}"
        except Exception:
            return db_url

    FIREBASE_CREDENTIALS_PATH: str = "/etc/secrets/firebase_credentials.json"
    FIREBASE_STORAGE_BUCKET: str = "lexguard-ai.appspot.com"
    FIREBASE_PROJECT_ID: str = "lexguard-ai-e91b7"
    FIRESTORE_DATABASE_ID: str = "(default)"

    @property
    def clean_firestore_database_id(self) -> str:
        raw_id = os.environ.get("FIRESTORE_DATABASE_ID") or self.FIRESTORE_DATABASE_ID or "(default)"
        db_id = str(raw_id).strip()
        # Safely unquote repeatedly to avoid url-encoded strings like %28default%29 or %2528default%2529
        while "%" in db_id:
            unquoted = urllib.parse.unquote(db_id)
            if unquoted == db_id:
                break
            db_id = unquoted
        return db_id if db_id else "(default)"

    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""

    OPENAI_API_KEY: str = ""
    GOOGLE_API_KEY: str = ""
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"

    SMTP_EMAIL: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_SERVER: str = ""
    SMTP_PORT: int = 587
    EMAIL_FROM: str = ""
    BREVO_API_KEY: str = ""
    
    EMAIL_PROVIDER: str = "brevo_api"
    RESEND_API_KEY: str = ""
    SENDGRID_API_KEY: str = ""
    MAILGUN_API_KEY: str = ""
    MAILGUN_DOMAIN: str = ""
    MAILGUN_API_URL: str = "https://api.mailgun.net/v3"
    
    # OCR Settings
    TESSERACT_CMD: str = os.environ.get("TESSERACT_CMD", "/usr/bin/tesseract")

    UPLOAD_DIR: str = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "uploads")

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()

# Ensure upload directory exists
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)