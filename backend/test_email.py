import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__)))

from dotenv import load_dotenv
load_dotenv()

from app.services.email_service import email_service
print("Original Provider from env:", os.getenv("EMAIL_PROVIDER"))
print("Brevo API Key:", os.getenv("BREVO_API_KEY"))
print("Email From:", os.getenv("EMAIL_FROM"))
print("SMTP Server:", os.getenv("SMTP_SERVER"))
print("SMTP Email:", os.getenv("SMTP_EMAIL"))

recipient = "tvijay1098@gmail.com"

# 1. Run SMTP Diagnostics
print("\n=== Testing SMTP Diagnostics ===")
os.environ["EMAIL_PROVIDER"] = "smtp"
try:
    res = email_service.run_smtp_diagnostics(recipient)
    print("SMTP Diagnostics result:", res)
except Exception as e:
    print("SMTP Diagnostics failed as expected:", e)

# 2. Run Brevo API Diagnostics
print("\n=== Testing Brevo API Diagnostics ===")
os.environ["EMAIL_PROVIDER"] = "brevo_api"
try:
    res = email_service.run_smtp_diagnostics(recipient)
    print("Brevo API Diagnostics result:", res)
except Exception as e:
    print("Brevo API Diagnostics failed as expected:", e)

# 3. Test Actual send_password_reset_email with SMTP
print("\n=== Testing send_password_reset_email with SMTP ===")
os.environ["EMAIL_PROVIDER"] = "smtp"
try:
    res = email_service.send_password_reset_email(recipient, "123456")
    print("send_password_reset_email result:", res)
except Exception as e:
    print("send_password_reset_email failed:", e)
