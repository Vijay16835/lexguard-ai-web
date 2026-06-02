import smtplib
import logging
import socket
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import settings

logger = logging.getLogger(__name__)

class EmailService:
    @staticmethod
    def send_otp_email(email: str, otp_code: str) -> bool:
        logger.info(f"[Email Service] Beginning OTP email generation for recipient: {email}")
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

        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = settings.SMTP_EMAIL
        message["To"] = email

        part1 = MIMEText(f"Your LexGuard AI verification code is {otp_code}. This code expires in 5 minutes.", "plain")
        part2 = MIMEText(html_content, "html")

        message.attach(part1)
        message.attach(part2)

        port = int(settings.SMTP_PORT)
        logger.info(f"[Email Service] SMTP send initiated. Host: {settings.SMTP_SERVER}, Port: {port}, Sender: {settings.SMTP_EMAIL}, Recipient: {email}")

        try:
            # Use SSL for port 465, TLS for others (like 587)
            if port == 465:
                logger.info("[Email Service] Connecting via SMTP_SSL (Port 465)...")
                server = smtplib.SMTP_SSL(settings.SMTP_SERVER, port, timeout=10)
            else:
                logger.info(f"[Email Service] Connecting via SMTP (Port {port})...")
                server = smtplib.SMTP(settings.SMTP_SERVER, port, timeout=10)
                logger.info("[Email Service] Upgrading connection with starttls...")
                server.ehlo()
                server.starttls()
                server.ehlo()
            
            with server:
                logger.info("[Email Service] Connected to SMTP server. Attempting login...")
                server.login(settings.SMTP_EMAIL, settings.SMTP_PASSWORD)
                logger.info("[Email Service] Login successful. Sending mail message...")
                server.sendmail(settings.SMTP_EMAIL, email, message.as_string())
            
            logger.info(f"[Email Service] OTP email successfully sent to {email}")
            return True
        except smtplib.SMTPAuthenticationError as auth_err:
            error_msg = "SMTP Authentication Error: The email provider rejected login. Please check SMTP_EMAIL and SMTP_PASSWORD (App Password)."
            logger.error(f"[Email Service] {error_msg} Details: {auth_err}")
            raise RuntimeError(error_msg) from auth_err
        except (socket.timeout, TimeoutError) as timeout_err:
            error_msg = f"SMTP Connection Timeout: Failed to connect to {settings.SMTP_SERVER}:{port} within 10 seconds. Note: Render Free tier blocks outbound SMTP ports (25, 465, 587)."
            logger.error(f"[Email Service] {error_msg} Details: {timeout_err}")
            raise TimeoutError(error_msg) from timeout_err
        except Exception as e:
            error_msg = f"SMTP Error sending email: {type(e).__name__}: {str(e)}"
            logger.error(f"[Email Service] {error_msg}")
            raise RuntimeError(error_msg) from e

    @staticmethod
    def send_password_reset_email(email: str, otp_code: str) -> bool:
        logger.info(f"[Email Service] Beginning Password Reset email generation for recipient: {email}")
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

        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = settings.SMTP_EMAIL
        message["To"] = email

        part1 = MIMEText(f"Your LexGuard AI password reset OTP is: {otp_code}", "plain")
        part2 = MIMEText(html_content, "html")

        message.attach(part1)
        message.attach(part2)

        port = int(settings.SMTP_PORT)
        logger.info(f"[Email Service] SMTP send initiated for password reset. Host: {settings.SMTP_SERVER}, Port: {port}, Sender: {settings.SMTP_EMAIL}, Recipient: {email}")

        try:
            if port == 465:
                logger.info("[Email Service] Connecting via SMTP_SSL (Port 465)...")
                server = smtplib.SMTP_SSL(settings.SMTP_SERVER, port, timeout=10)
            else:
                logger.info(f"[Email Service] Connecting via SMTP (Port {port})...")
                server = smtplib.SMTP(settings.SMTP_SERVER, port, timeout=10)
                logger.info("[Email Service] Upgrading connection with starttls...")
                server.ehlo()
                server.starttls()
                server.ehlo()
            
            with server:
                logger.info("[Email Service] Connected to SMTP server. Attempting login...")
                server.login(settings.SMTP_EMAIL, settings.SMTP_PASSWORD)
                logger.info("[Email Service] Login successful. Sending mail message...")
                server.sendmail(settings.SMTP_EMAIL, email, message.as_string())
            
            logger.info(f"[Email Service] Password Reset email successfully sent to {email}")
            return True
        except smtplib.SMTPAuthenticationError as auth_err:
            error_msg = "SMTP Authentication Error: The email provider rejected login. Please check SMTP_EMAIL and SMTP_PASSWORD (App Password)."
            logger.error(f"[Email Service] {error_msg} Details: {auth_err}")
            raise RuntimeError(error_msg) from auth_err
        except (socket.timeout, TimeoutError) as timeout_err:
            error_msg = f"SMTP Connection Timeout: Failed to connect to {settings.SMTP_SERVER}:{port} within 10 seconds. Note: Render Free tier blocks outbound SMTP ports (25, 465, 587)."
            logger.error(f"[Email Service] {error_msg} Details: {timeout_err}")
            raise TimeoutError(error_msg) from timeout_err
        except Exception as e:
            error_msg = f"SMTP Error sending email: {type(e).__name__}: {str(e)}"
            logger.error(f"[Email Service] {error_msg}")
            raise RuntimeError(error_msg) from e

email_service = EmailService()
