import logging
import os
import time
import httpx
from app.core.config import settings

logger = logging.getLogger(__name__)

class BrevoEmailService:
    @staticmethod
    def validate_configuration() -> bool:
        """Validate email configuration on startup."""
        provider = (os.getenv("EMAIL_PROVIDER") or getattr(settings, "EMAIL_PROVIDER", "brevo_api")).lower().strip()
        smtp_server = os.getenv("SMTP_SERVER") or getattr(settings, "SMTP_SERVER", "")
        smtp_port = os.getenv("SMTP_PORT") or getattr(settings, "SMTP_PORT", "")
        smtp_email = os.getenv("SMTP_EMAIL") or getattr(settings, "SMTP_EMAIL", "")
        email_from = os.getenv("EMAIL_FROM") or getattr(settings, "EMAIL_FROM", "")
        
        smtp_password_configured = bool(os.getenv("SMTP_PASSWORD") or getattr(settings, "SMTP_PASSWORD", ""))
        brevo_api_key_configured = bool(os.getenv("BREVO_API_KEY") or getattr(settings, "BREVO_API_KEY", ""))
        
        logger.info("[Email Service] Startup configuration validation values:")
        print("[Email Service] Startup configuration validation values:")
        logger.info(f"  EMAIL_PROVIDER: {provider}")
        print(f"  EMAIL_PROVIDER: {provider}")
        logger.info(f"  SMTP_SERVER: {smtp_server}")
        print(f"  SMTP_SERVER: {smtp_server}")
        logger.info(f"  SMTP_PORT: {smtp_port}")
        print(f"  SMTP_PORT: {smtp_port}")
        logger.info(f"  SMTP_EMAIL: {smtp_email}")
        print(f"  SMTP_EMAIL: {smtp_email}")
        logger.info(f"  EMAIL_FROM: {email_from}")
        print(f"  EMAIL_FROM: {email_from}")
        logger.info(f"  SMTP_PASSWORD configured: {smtp_password_configured}")
        print(f"  SMTP_PASSWORD configured: {smtp_password_configured}")
        logger.info(f"  BREVO_API_KEY configured: {brevo_api_key_configured}")
        print(f"  BREVO_API_KEY configured: {brevo_api_key_configured}")
        
        if provider == "console":
            logger.info("[Email Service] Startup validation successful: Console Email Logger is configured.")
            return True
            
        if provider == "smtp":
            if not smtp_server or not smtp_email or not smtp_password_configured:
                logger.critical("[Email Service] Startup validation failed: SMTP settings are not fully configured!")
                return False
            logger.info(f"[Email Service] Startup validation successful: SMTP is configured. Server: {smtp_server}")
            return True
        
        if provider == "brevo_api":
            if not brevo_api_key_configured:
                logger.critical("[Email Service] Startup validation failed: BREVO_API_KEY is not configured!")
                return False
            if not email_from:
                logger.critical("[Email Service] Startup validation failed: EMAIL_FROM (verified sender) is not configured!")
                return False
            logger.info(f"[Email Service] Startup validation successful: Brevo REST API is configured. Sender: {email_from}")
            return True
            
        logger.critical(f"[Email Service] Startup validation failed: Unknown provider '{provider}'!")
        return False

    @staticmethod
    def _send_email_via_smtp(email: str, subject: str, text_content: str, html_content: str) -> bool:
        """Sends transactional email using SMTP with TLS/STARTTLS, auth, and timeout."""
        smtp_server = os.getenv("SMTP_SERVER") or getattr(settings, "SMTP_SERVER", "")
        smtp_port_str = os.getenv("SMTP_PORT") or getattr(settings, "SMTP_PORT", "587")
        smtp_port = int(smtp_port_str) if smtp_port_str else 587
        smtp_email = os.getenv("SMTP_EMAIL") or getattr(settings, "SMTP_EMAIL", "")
        smtp_password = os.getenv("SMTP_PASSWORD") or getattr(settings, "SMTP_PASSWORD", "")
        from_email = os.getenv("EMAIL_FROM") or getattr(settings, "EMAIL_FROM", "")

        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart

        logger.info(f"SMTP Connection: Connecting to {smtp_server}:{smtp_port}...")
        print(f"SMTP Connection: Connecting to {smtp_server}:{smtp_port}...")

        msg = MIMEMultipart("alternative")
        msg["From"] = from_email
        msg["To"] = email
        msg["Subject"] = subject

        part1 = MIMEText(text_content, "plain")
        part2 = MIMEText(html_content, "html")
        msg.attach(part1)
        msg.attach(part2)

        try:
            # Connect
            server = smtplib.SMTP(smtp_server, smtp_port, timeout=10.0)
            logger.info("SMTP Connection: Connected successfully.")
            print("SMTP Connection: Connected successfully.")
            
            # STARTTLS
            logger.info("TLS Started: Initiating STARTTLS...")
            print("TLS Started: Initiating STARTTLS...")
            server.starttls()
            logger.info("TLS Started: STARTTLS handshake complete.")
            print("TLS Started: STARTTLS handshake complete.")
            
            # Login
            logger.info(f"Login: Attempting login for {smtp_email}...")
            print(f"Login: Attempting login for {smtp_email}...")
            server.login(smtp_email, smtp_password)
            logger.info("Login Success: SMTP Authenticated successfully.")
            print("Login Success: SMTP Authenticated successfully.")

            # Sendmail
            logger.info(f"Sending Email: From {from_email} to {email}...")
            print(f"Sending Email: From {from_email} to {email}...")
            response = server.sendmail(from_email, [email], msg.as_string())
            logger.info(f"Sendmail Response: {response}")
            print(f"Sendmail Response: {response}")

            # Quit
            logger.info("Quit: Closing SMTP connection...")
            print("Quit: Closing SMTP connection...")
            quit_status = server.quit()
            logger.info(f"Quit Status: {quit_status}")
            print(f"Quit Status: {quit_status}")
            
            logger.info("Email Sent Successfully")
            print("Email Sent Successfully")
            return True
        except Exception as e:
            logger.error("Email Failed")
            print("Email Failed")
            logger.error("Exception Stacktrace:", exc_info=True)
            print("Exception Stacktrace:")
            import traceback
            traceback.print_exc()
            raise e

    @staticmethod
    def _send_brevo_api_request(email: str, subject: str, text_content: str, html_content: str) -> bool:
        """
        Sends transactional email using Brevo's REST API endpoint:
        https://api.brevo.com/v3/smtp/email
        """
        api_key = os.getenv("BREVO_API_KEY") or getattr(settings, "BREVO_API_KEY", "")
        from_email = os.getenv("EMAIL_FROM") or getattr(settings, "EMAIL_FROM", "")
        
        if not api_key:
            logger.error("[Brevo API] Cannot send email. BREVO_API_KEY is missing.")
            print("[Brevo API] Cannot send email. BREVO_API_KEY is missing.")
            raise ValueError("BREVO_API_KEY is missing.")
            
        url = "https://api.brevo.com/v3/smtp/email"
        headers = {
            "api-key": api_key,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        payload = {
            "sender": {"email": from_email, "name": "LexGuard AI"},
            "to": [{"email": email}],
            "subject": subject,
            "htmlContent": html_content,
            "textContent": text_content
        }
        
        logger.info("[Brevo API] Request started.")
        print("[Brevo API] Request started.")
        logger.info(f"API request payload: {payload}")
        print(f"API request payload: {payload}")
        
        # Mask API key in headers output for logging
        logged_headers = headers.copy()
        logged_headers["api-key"] = "********"
        logger.info(f"API request headers: {logged_headers}")
        print(f"API request headers: {logged_headers}")
        
        max_attempts = 4
        for attempt in range(1, max_attempts + 1):
            try:
                logger.info(f"[Brevo API] Sending email (Attempt {attempt}/{max_attempts}) to '{email}'...")
                print(f"[Brevo API] Sending email (Attempt {attempt}/{max_attempts}) to '{email}'...")
                print("Sending request to Brevo...")
                
                with httpx.Client(timeout=10.0) as client:
                    response = client.post(url, json=payload, headers=headers)
                    
                    print(f"Brevo Response: {response.status_code} {response.reason_phrase}")
                    print(response.text)
                    
                    logger.info(f"HTTP Status Code: {response.status_code}")
                    logger.info(f"Response Body: {response.text}")
                    
                    if response.status_code in (200, 201, 202):
                        logger.info(f"[Brevo API] Email successfully dispatched to '{email}' via Brevo REST API.")
                        print(f"[Brevo API] Email successfully dispatched to '{email}' via Brevo REST API.")
                        return True
                    else:
                        logger.error(f"Error Message: API Error Response: {response.status_code} - {response.text}")
                        print(f"Error Message: API Error Response: {response.status_code} - {response.text}")
                        if response.status_code in (400, 401, 403):
                            raise RuntimeError(f"Brevo API Permanent Error: {response.status_code} - {response.text}")
                        response.raise_for_status()
            except Exception as e:
                logger.error(f"[Brevo API] Exception during request (Attempt {attempt}/{max_attempts}): {type(e).__name__}: {str(e)}", exc_info=True)
                print(f"[Brevo API] Exception during request (Attempt {attempt}/{max_attempts}): {type(e).__name__}: {str(e)}")
                
                if "Permanent Error" in str(e):
                    raise e
                    
                if attempt == max_attempts:
                    logger.critical(f"[Brevo API] Failed to send email to '{email}' after {attempt} attempts. Final failure.")
                    print(f"[Brevo API] Failed to send email to '{email}' after {attempt} attempts. Final failure.")
                    raise RuntimeError(f"Brevo API connection failure: {type(e).__name__}: {str(e)}") from e
                
                sleep_time = 1.0 * (2 ** (attempt - 1))
                logger.info(f"[Brevo API] Retrying transient failure in {sleep_time}s...")
                print(f"[Brevo API] Retrying transient failure in {sleep_time}s...")
                time.sleep(sleep_time)
                
        return False

    @staticmethod
    def _send_email_via_console(email: str, subject: str, text_content: str, html_content: str) -> bool:
        logger.info("\n" + "="*50)
        logger.info(f" [CONSOLE EMAIL LOGGER] SENDING EMAIL")
        logger.info(f" To: {email}")
        logger.info(f" Subject: {subject}")
        logger.info(f" Text Content: {text_content}")
        logger.info("="*50 + "\n")
        
        print("\n" + "="*50)
        print(f" [CONSOLE EMAIL LOGGER] SENDING EMAIL")
        print(f" To: {email}")
        print(f" Subject: {subject}")
        print(f" Text Content: {text_content}")
        print("="*50 + "\n")
        return True

    @staticmethod
    def send_otp_email(email: str, otp_code: str) -> bool:
        logger.info(f"[Email Service] Generating OTP email content for recipient: {email}")
        subject = "LexGuard AI Verification Code"
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
                        <p style="color: #999999; font-size: 12px;">&copy; 2026 LexGuard AI. All rights reserved.</p>
                    </div>
                </div>
            </body>
        </html>
        """
        text_content = f"Your LexGuard AI verification code is {otp_code}. This code expires in 5 minutes."
        
        provider = (os.getenv("EMAIL_PROVIDER") or getattr(settings, "EMAIL_PROVIDER", "brevo_api")).lower().strip()
        if provider == "smtp":
            return BrevoEmailService._send_email_via_smtp(email, subject, text_content, html_content)
        elif provider == "brevo_api":
            return BrevoEmailService._send_brevo_api_request(email, subject, text_content, html_content)
        elif provider == "console":
            return BrevoEmailService._send_email_via_console(email, subject, text_content, html_content)
        else:
            raise ValueError(f"Unknown or unsupported email provider: '{provider}'")

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
                            <p style="color: #888888; font-size: 12px;">&copy; 2026 LexGuard AI. Professional Legal Intelligence.</p>
                        </div>
                    </div>
                </div>
            </body>
        </html>
        """
        text_content = f"Your LexGuard AI password reset OTP is: {otp_code}"
        
        provider = (os.getenv("EMAIL_PROVIDER") or getattr(settings, "EMAIL_PROVIDER", "brevo_api")).lower().strip()
        if provider == "smtp":
            return BrevoEmailService._send_email_via_smtp(email, subject, text_content, html_content)
        elif provider == "brevo_api":
            return BrevoEmailService._send_brevo_api_request(email, subject, text_content, html_content)
        elif provider == "console":
            return BrevoEmailService._send_email_via_console(email, subject, text_content, html_content)
        else:
            raise ValueError(f"Unknown or unsupported email provider: '{provider}'")

    @staticmethod
    def run_smtp_diagnostics(recipient_email: str) -> dict:
        """Runs diagnostics for configured email provider (SMTP or Brevo API)."""
        import socket
        provider = (os.getenv("EMAIL_PROVIDER") or getattr(settings, "EMAIL_PROVIDER", "brevo_api")).lower().strip()
        
        if provider == "smtp":
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            smtp_server = os.getenv("SMTP_SERVER") or getattr(settings, "SMTP_SERVER", "")
            smtp_port_str = os.getenv("SMTP_PORT") or getattr(settings, "SMTP_PORT", "587")
            smtp_port = int(smtp_port_str) if smtp_port_str else 587
            smtp_email = os.getenv("SMTP_EMAIL") or getattr(settings, "SMTP_EMAIL", "")
            smtp_password = os.getenv("SMTP_PASSWORD") or getattr(settings, "SMTP_PASSWORD", "")
            from_email = os.getenv("EMAIL_FROM") or getattr(settings, "EMAIL_FROM", "")
            
            logger.info("[SMTP DIAGNOSTICS] Starting SMTP connectivity audit:")
            logger.info(f"  Server: {smtp_server}")
            logger.info(f"  Port: {smtp_port}")
            logger.info(f"  Sender: {from_email}")
            
            dns_resolved = False
            tcp_connected = False
            smtp_authenticated = False
            email_sent = False
            provider_response = ""
            
            # DNS resolution
            try:
                ip_list = socket.getaddrinfo(smtp_server, smtp_port, socket.AF_INET, socket.SOCK_STREAM)
                dns_resolved = True
                logger.info(f"[SMTP DIAGNOSTICS] DNS lookup succeeded: {smtp_server} resolved to {[ip[4][0] for ip in ip_list]}")
            except Exception as e:
                logger.error(f"[SMTP DIAGNOSTICS] DNS failure: {str(e)}", exc_info=True)
                raise RuntimeError(f"DNS failure resolving {smtp_server}: {str(e)}") from e
                
            # TCP connection
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5.0)
                sock.connect((smtp_server, smtp_port))
                sock.close()
                tcp_connected = True
                logger.info(f"[SMTP DIAGNOSTICS] TCP handshake to {smtp_server}:{smtp_port} successful.")
            except Exception as e:
                logger.error(f"[SMTP DIAGNOSTICS] TCP connection failure: {str(e)}", exc_info=True)
                raise ConnectionError(f"Network failure: TCP connection to {smtp_server}:{smtp_port} failed: {str(e)}") from e
                
            # SMTP authentication and sending
            try:
                server = smtplib.SMTP(smtp_server, smtp_port, timeout=10.0)
                server.starttls()
                server.login(smtp_email, smtp_password)
                smtp_authenticated = True
                logger.info("[SMTP DIAGNOSTICS] SMTP Authentication successful.")
                
                # Send test email
                msg = MIMEMultipart()
                msg["From"] = from_email
                msg["To"] = recipient_email
                msg["Subject"] = "LexGuard SMTP Diagnostic Test"
                msg.attach(MIMEText("This is a diagnostic connection test email sent from the LexGuard AI backend SMTP diagnostics suite.", "plain"))
                
                send_resp = server.sendmail(from_email, [recipient_email], msg.as_string())
                provider_response = str(send_resp)
                email_sent = True
                logger.info(f"[SMTP DIAGNOSTICS] Diagnostic email successfully sent. Response: {send_resp}")
                server.quit()
            except Exception as e:
                logger.error(f"[SMTP DIAGNOSTICS] Exception during SMTP diagnosis: {str(e)}", exc_info=True)
                raise e
                
            # Log formatted as requested
            logger.info(
                f"\n[SMTP TEST]\n"
                f"Server: {smtp_server}\n"
                f"Port: {smtp_port}\n"
                f"Username: {smtp_email}\n"
                f"Connection Successful: {tcp_connected}\n"
                f"Authentication Successful: {smtp_authenticated}"
            )
            
            return {
                "smtp_connected": tcp_connected,
                "smtp_authenticated": smtp_authenticated,
                "email_sent": email_sent,
                "provider_response": provider_response
            }
        
        # Default: Brevo API Diagnostics
        url = "https://api.brevo.com/v3/smtp/email"
        api_key = os.getenv("BREVO_API_KEY") or getattr(settings, "BREVO_API_KEY", "")
        from_email = os.getenv("EMAIL_FROM") or getattr(settings, "EMAIL_FROM", "")
        
        logger.info("[BREVO REST API DIAGNOSTICS] Starting connectivity audit:")
        logger.info(f"  URL: {url}")
        logger.info(f"  Sender Email: {from_email}")
        logger.info(f"  API Key configured: {bool(api_key)}")
        
        dns_resolved = False
        tcp_connected = False
        api_connected = False
        email_sent = False
        provider_response = ""
        
        # Test DNS for api.brevo.com
        try:
            ip_list = socket.getaddrinfo("api.brevo.com", 443, socket.AF_INET, socket.SOCK_STREAM)
            dns_resolved = True
            logger.info(f"[BREVO REST API DIAGNOSTICS] DNS lookup succeeded: api.brevo.com resolved to {[ip[4][0] for ip in ip_list]}")
        except socket.gaierror as e:
            logger.error(f"[BREVO REST API DIAGNOSTICS] DNS failure: {str(e)}", exc_info=True)
            logger.info(
                f"\n[SMTP TEST]\n"
                f"Server: api.brevo.com\n"
                f"Port: 443\n"
                f"Username: {from_email}\n"
                f"Connection Successful: False\n"
                f"Authentication Successful: False"
            )
            raise RuntimeError(f"DNS failure resolving api.brevo.com: {str(e)}") from e
            
        # Test TCP connection to api.brevo.com:443
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5.0)
            sock.connect(("api.brevo.com", 443))
            sock.close()
            tcp_connected = True
            logger.info("[BREVO REST API DIAGNOSTICS] TCP handshake to api.brevo.com:443 successful.")
        except Exception as e:
            logger.error(f"[BREVO REST API DIAGNOSTICS] TCP connection failure: {str(e)}", exc_info=True)
            logger.info(
                f"\n[SMTP TEST]\n"
                f"Server: api.brevo.com\n"
                f"Port: 443\n"
                f"Username: {from_email}\n"
                f"Connection Successful: False\n"
                f"Authentication Successful: False"
            )
            raise ConnectionError(f"Network failure: TCP connection to api.brevo.com:443 failed: {str(e)}") from e
            
        # Try calling Brevo API senders endpoint to verify authorization
        try:
            headers = {
                "api-key": api_key,
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            logger.info("[BREVO REST API DIAGNOSTICS] Testing API authentication...")
            with httpx.Client(timeout=10.0) as client:
                response = client.get("https://api.brevo.com/v3/senders", headers=headers)
                logger.info(f"[BREVO REST API DIAGNOSTICS] Response status code: {response.status_code}")
                logger.info(f"[BREVO REST API DIAGNOSTICS] Response body: {response.text}")
                
                if response.status_code == 200:
                    api_connected = True
                    logger.info("[BREVO REST API DIAGNOSTICS] API Authentication verified successfully!")
                    
                    # Send test email
                    payload = {
                        "sender": {"email": from_email, "name": "LexGuard AI Diagnostics"},
                        "to": [{"email": recipient_email}],
                        "subject": "LexGuard Brevo REST API Diagnostic Test",
                        "htmlContent": "<p>This is a diagnostic connection test email sent from the LexGuard AI backend diagnostics suite using the Brevo REST API.</p>",
                        "textContent": "This is a diagnostic connection test email sent from the LexGuard AI backend diagnostics suite using the Brevo REST API."
                    }
                    send_resp = client.post(url, json=payload, headers=headers)
                    provider_response = send_resp.text
                    if send_resp.status_code in (200, 201, 202):
                        email_sent = True
                        logger.info("[BREVO REST API DIAGNOSTICS] Diagnostic email successfully sent.")
                    else:
                        logger.error(f"[BREVO REST API DIAGNOSTICS] Email sending failed: {send_resp.status_code} - {send_resp.text}")
                        raise RuntimeError(f"Email send failure: {send_resp.status_code} - {send_resp.text}")
                else:
                    logger.error(f"[BREVO REST API DIAGNOSTICS] Authentication failed: {response.status_code} - {response.text}")
                    raise RuntimeError(f"Authentication failure: {response.status_code} - {response.text}")
        except Exception as e:
            logger.error(f"[BREVO REST API DIAGNOSTICS] Exception during API diagnosis: {str(e)}", exc_info=True)
            raise e
            
        # Log formatted as requested
        logger.info(
            f"\n[SMTP TEST]\n"
            f"Server: api.brevo.com\n"
            f"Port: 443\n"
            f"Username: {from_email}\n"
            f"Connection Successful: {tcp_connected}\n"
            f"Authentication Successful: {api_connected}"
        )
        
        return {
            "smtp_connected": tcp_connected,
            "smtp_authenticated": api_connected,
            "email_sent": email_sent,
            "provider_response": provider_response
        }

# Aliases to preserve application compatibility
EmailService = BrevoEmailService
email_service = BrevoEmailService()

