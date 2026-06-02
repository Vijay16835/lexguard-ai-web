import smtplib
import logging
import socket
import os
import time
import httpx
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import settings

logger = logging.getLogger(__name__)

class EmailService:
    @staticmethod
    def validate_configuration() -> bool:
        """Validate SMTP or REST API configuration on startup."""
        provider = (os.getenv("EMAIL_PROVIDER") or getattr(settings, "EMAIL_PROVIDER", "smtp")).lower().strip()
        logger.info(f"[Email Service] Validating email configuration on startup. Provider: {provider}")
        
        if provider == "smtp":
            if not settings.SMTP_SERVER or not settings.SMTP_EMAIL or not settings.SMTP_PASSWORD:
                logger.warning("[Email Service] SMTP configuration is incomplete. SMTP_SERVER, SMTP_EMAIL, or SMTP_PASSWORD is empty.")
                return False
            
            port = int(settings.SMTP_PORT)
            logger.info(f"[Email Service] Attempting connection check to SMTP server {settings.SMTP_SERVER}:{port}...")
            try:
                if port == 465:
                    server = smtplib.SMTP_SSL(settings.SMTP_SERVER, port, timeout=5)
                else:
                    server = smtplib.SMTP(settings.SMTP_SERVER, port, timeout=5)
                    server.ehlo()
                    server.starttls()
                    server.ehlo()
                
                with server:
                    logger.info("[Email Service] SMTP connection validation successful (server is reachable).")
                return True
            except Exception as e:
                logger.error(f"[Email Service] SMTP connection check failed: {type(e).__name__}: {str(e)}")
                return False
                
        elif provider == "resend":
            api_key = os.getenv("RESEND_API_KEY") or getattr(settings, "RESEND_API_KEY", "")
            if not api_key:
                logger.warning("[Email Service] Resend API key (RESEND_API_KEY) is missing.")
                return False
            logger.info("[Email Service] Resend API provider is configured.")
            return True
            
        elif provider == "sendgrid":
            api_key = os.getenv("SENDGRID_API_KEY") or getattr(settings, "SENDGRID_API_KEY", "")
            if not api_key:
                logger.warning("[Email Service] SendGrid API key (SENDGRID_API_KEY) is missing.")
                return False
            logger.info("[Email Service] SendGrid API provider is configured.")
            return True
            
        elif provider == "mailgun":
            api_key = os.getenv("MAILGUN_API_KEY") or getattr(settings, "MAILGUN_API_KEY", "")
            domain = os.getenv("MAILGUN_DOMAIN") or getattr(settings, "MAILGUN_DOMAIN", "")
            if not api_key or not domain:
                logger.warning("[Email Service] Mailgun configuration is incomplete (MAILGUN_API_KEY or MAILGUN_DOMAIN is missing).")
                return False
            logger.info("[Email Service] Mailgun API provider is configured.")
            return True
            
        else:
            logger.error(f"[Email Service] Unknown email provider configured: {provider}")
            return False

    @staticmethod
    def _send_email_helper(email: str, subject: str, text_content: str, html_content: str) -> bool:
        """
        Helper function to send emails via the configured provider (SMTP, Resend, SendGrid, Mailgun)
        with detailed logging and transient failure retry logic (exponential backoff).
        """
        provider = (os.getenv("EMAIL_PROVIDER") or getattr(settings, "EMAIL_PROVIDER", "smtp")).lower().strip()
        max_attempts = 4
        
        logger.info(f"[Email Service] Preparing to dispatch email to '{email}' using provider '{provider}'")
        
        for attempt in range(1, max_attempts + 1):
            try:
                if provider == "smtp":
                    port = int(settings.SMTP_PORT)
                    logger.info(f"[Email Service] Attempt {attempt}/{max_attempts}: Connecting to SMTP Server: {settings.SMTP_SERVER}, Port: {port}")
                    
                    if port == 465:
                        server = smtplib.SMTP_SSL(settings.SMTP_SERVER, port, timeout=10)
                    else:
                        server = smtplib.SMTP(settings.SMTP_SERVER, port, timeout=10)
                        server.ehlo()
                        logger.info("[Email Service] Upgrading SMTP connection with STARTTLS...")
                        server.starttls()
                        server.ehlo()
                        
                    with server:
                        logger.info("[Email Service] SMTP connection established. Logging in...")
                        server.login(settings.SMTP_EMAIL, settings.SMTP_PASSWORD)
                        logger.info("[Email Service] SMTP authentication successful. Dispatching email...")
                        
                        message = MIMEMultipart("alternative")
                        message["Subject"] = subject
                        message["From"] = settings.SMTP_EMAIL
                        message["To"] = email
                        
                        message.attach(MIMEText(text_content, "plain"))
                        message.attach(MIMEText(html_content, "html"))
                        
                        server.sendmail(settings.SMTP_EMAIL, email, message.as_string())
                        logger.info(f"[Email Service] Email successfully sent to '{email}' via SMTP.")
                        return True
                        
                elif provider == "resend":
                    api_key = os.getenv("RESEND_API_KEY") or getattr(settings, "RESEND_API_KEY", "")
                    if not api_key:
                        raise ValueError("Resend API key (RESEND_API_KEY) is not configured.")
                    
                    from_email = settings.SMTP_EMAIL
                    if not from_email or "gmail.com" in from_email or "your_smtp" in from_email:
                        from_email = "onboarding@resend.dev"
                        
                    logger.info(f"[Email Service] Attempt {attempt}/{max_attempts}: Sending via Resend API. Sender: {from_email}")
                    
                    headers = {
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    }
                    payload = {
                        "from": f"LexGuard AI <{from_email}>",
                        "to": [email],
                        "subject": subject,
                        "html": html_content,
                        "text": text_content
                    }
                    
                    with httpx.Client(timeout=10.0) as client:
                        response = client.post("https://api.resend.com/emails", json=payload, headers=headers)
                        response.raise_for_status()
                        logger.info(f"[Email Service] Email successfully sent to '{email}' via Resend REST API.")
                        return True
                        
                elif provider == "sendgrid":
                    api_key = os.getenv("SENDGRID_API_KEY") or getattr(settings, "SENDGRID_API_KEY", "")
                    if not api_key:
                        raise ValueError("SendGrid API key (SENDGRID_API_KEY) is not configured.")
                        
                    from_email = settings.SMTP_EMAIL
                    if not from_email or "your_smtp" in from_email:
                        from_email = "onboarding@resend.dev"
                        
                    logger.info(f"[Email Service] Attempt {attempt}/{max_attempts}: Sending via SendGrid API. Sender: {from_email}")
                    
                    headers = {
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    }
                    payload = {
                        "personalizations": [{"to": [{"email": email}], "subject": subject}],
                        "from": {"email": from_email, "name": "LexGuard AI"},
                        "content": [
                            {"type": "text/plain", "value": text_content},
                            {"type": "text/html", "value": html_content}
                        ]
                    }
                    
                    with httpx.Client(timeout=10.0) as client:
                        response = client.post("https://api.sendgrid.com/v3/mail/send", json=payload, headers=headers)
                        response.raise_for_status()
                        logger.info(f"[Email Service] Email successfully sent to '{email}' via SendGrid REST API.")
                        return True
                        
                elif provider == "mailgun":
                    api_key = os.getenv("MAILGUN_API_KEY") or getattr(settings, "MAILGUN_API_KEY", "")
                    domain = os.getenv("MAILGUN_DOMAIN") or getattr(settings, "MAILGUN_DOMAIN", "")
                    api_url = os.getenv("MAILGUN_API_URL") or getattr(settings, "MAILGUN_API_URL", "https://api.mailgun.net/v3")
                    if not api_key or not domain:
                        raise ValueError("Mailgun configuration is incomplete (MAILGUN_API_KEY or MAILGUN_DOMAIN is missing).")
                        
                    from_email = settings.SMTP_EMAIL
                    if not from_email or "your_smtp" in from_email:
                        from_email = f"postmaster@{domain}"
                        
                    logger.info(f"[Email Service] Attempt {attempt}/{max_attempts}: Sending via Mailgun API. Sender: {from_email}")
                    
                    url = f"{api_url.rstrip('/')}/{domain}/messages"
                    data = {
                        "from": f"LexGuard AI <{from_email}>",
                        "to": email,
                        "subject": subject,
                        "text": text_content,
                        "html": html_content
                    }
                    
                    with httpx.Client(timeout=10.0) as client:
                        response = client.post(url, data=data, auth=("api", api_key))
                        response.raise_for_status()
                        logger.info(f"[Email Service] Email successfully sent to '{email}' via Mailgun REST API.")
                        return True
                else:
                    raise ValueError(f"Unsupported email provider: {provider}")
                    
            except Exception as e:
                is_transient = True
                
                # Check for permanent config / credential issues
                if isinstance(e, smtplib.SMTPAuthenticationError):
                    is_transient = False
                elif isinstance(e, ValueError):
                    is_transient = False
                elif isinstance(e, httpx.HTTPStatusError):
                    if e.response.status_code in (400, 401, 403, 404):
                        is_transient = False
                        
                logger.warning(
                    f"[Email Service] Attempt {attempt}/{max_attempts} failed to send email to '{email}'. "
                    f"Error: {type(e).__name__}: {str(e)}. "
                    f"Transient failure: {is_transient}"
                )
                
                if attempt == max_attempts or not is_transient:
                    logger.error(f"[Email Service] Failed to send email to '{email}' after {attempt} attempts. Final failure.")
                    # Re-raise standard exceptions matching API expected errors
                    if isinstance(e, smtplib.SMTPAuthenticationError):
                        raise RuntimeError("SMTP Authentication Error: The email provider rejected login. Please check SMTP_EMAIL and SMTP_PASSWORD (App Password).") from e
                    elif isinstance(e, (socket.timeout, TimeoutError)):
                        raise TimeoutError(f"SMTP Connection Timeout: Failed to connect to server within timeout limits. Details: {str(e)}") from e
                    else:
                        raise RuntimeError(f"Email delivery failure: {type(e).__name__}: {str(e)}") from e
                        
                sleep_time = 1.0 * (2 ** (attempt - 1))
                logger.info(f"[Email Service] Retrying transient failure in {sleep_time}s...")
                time.sleep(sleep_time)
                
        return False

    @staticmethod
    def send_otp_email(email: str, otp_code: str) -> bool:
        logger.info(f"[Email Service] Generating OTP email content for recipient: {email}")
        subject = f"{otp_code} is your LexGuard AI verification code"
        
        # Professional HTML Template
        html_content = f"""
        <html>
            <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f4f4; padding: 20px;">
                <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 10px; overflow: hidden; border: 1px solid #e0e0e0;">
                    <div style="background-color: #001f3f; padding: 20px; text-align: center;">
                        <h1 style="color: #FFD700; margin: 0; font-size: 24px;">LexGuard AI</h1>
                    </div>
                    <div style="padding: 30px; text-align: center;">
                        <h2 style="color: #333333;">Verification Code</h2>
                        <p style="color: #666666; font-size: 16px;">Please use the following 6-digit code to complete your login/signup process.</p>
                        <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0; border: 1px dashed #001f3f;">
                            <span style="font-size: 32px; font-weight: bold; letter-spacing: 5px; color: #001f3f;">{otp_code}</span>
                        </div>
                        <p style="color: #e74c3c; font-size: 14px; font-weight: bold;">This code expires in 5 minutes.</p>
                        <hr style="border: 0; border-top: 1px solid #eeeeee; margin: 20px 0;">
                        <p style="color: #999999; font-size: 12px;">If you did not request this code, please ignore this email or contact support if you have concerns.</p>
                        <p style="color: #999999; font-size: 12px;">&copy; 2024 LexGuard AI. All rights reserved.</p>
                    </div>
                </div>
            </body>
        </html>
        """
        text_content = f"Your LexGuard AI verification code is {otp_code}. This code expires in 5 minutes."
        
        return EmailService._send_email_helper(email, subject, text_content, html_content)

    @staticmethod
    def send_password_reset_email(email: str, otp_code: str) -> bool:
        logger.info(f"[Email Service] Generating Password Reset email content for recipient: {email}")
        subject = "LexGuard AI Password Reset OTP"
        
        html_content = f"""
        <html>
            <body style="font-family: 'Inter', sans-serif; background-color: #f8f9fa; padding: 40px 20px;">
                <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 12px; overflow: hidden; border: 1px solid #e9ecef; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);">
                    <div style="background-color: #001f3f; padding: 30px; text-align: center;">
                        <h1 style="color: #FFD700; margin: 0; font-size: 28px; letter-spacing: 1px;">LexGuard AI</h1>
                    </div>
                    <div style="padding: 40px; text-align: center;">
                        <h2 style="color: #1a1a1a; margin-top: 0; font-size: 24px;">Password Reset Request</h2>
                        <p style="color: #4a4a4a; font-size: 16px; line-height: 1.6;">Your 6-digit verification code for password reset is:</p>
                        
                        <div style="margin: 35px 0; background-color: #f1f3f5; padding: 20px; border-radius: 8px; letter-spacing: 8px; font-size: 32px; font-weight: 800; color: #001f3f;">
                            {otp_code}
                        </div>
                        
                        <p style="color: #e74c3c; font-size: 14px; font-weight: 600; margin-bottom: 25px;">This code will expire in 5 minutes.</p>
                        
                        <div style="padding-top: 30px; border-top: 1px solid #eeeeee;">
                            <p style="color: #888888; font-size: 13px; margin-bottom: 5px;">If you did not request this, you can safely ignore this email.</p>
                            <p style="color: #888888; font-size: 12px;">&copy; 2024 LexGuard AI. Professional Legal Intelligence.</p>
                        </div>
                    </div>
                </div>
            </body>
        </html>
        """
        text_content = f"Your LexGuard AI password reset OTP is: {otp_code}"
        
        return EmailService._send_email_helper(email, subject, text_content, html_content)

email_service = EmailService()
