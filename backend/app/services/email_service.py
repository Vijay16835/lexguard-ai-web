import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import settings

class EmailService:
    @staticmethod
    def send_otp_email(email: str, otp_code: str):
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

        try:
            # Use SSL for port 465, TLS for others (like 587)
            if int(settings.SMTP_PORT) == 465:
                server = smtplib.SMTP_SSL(settings.SMTP_SERVER, int(settings.SMTP_PORT), timeout=10)
            else:
                server = smtplib.SMTP(settings.SMTP_SERVER, int(settings.SMTP_PORT), timeout=10)
                server.starttls()
            
            with server:
                server.login(settings.SMTP_EMAIL, settings.SMTP_PASSWORD)
                server.sendmail(settings.SMTP_EMAIL, email, message.as_string())
            print(f"OTP Email sent successfully to {email}")
            return True
        except smtplib.SMTPAuthenticationError:
            print(f"SMTP Authentication Error: Please check your App Password.")
            return False
        except Exception as e:
            print(f"Error sending email to {email}: {e}")
            return False

    @staticmethod
    def send_password_reset_email(email: str, otp_code: str):
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

        try:
            if int(settings.SMTP_PORT) == 465:
                server = smtplib.SMTP_SSL(settings.SMTP_SERVER, int(settings.SMTP_PORT), timeout=10)
            else:
                server = smtplib.SMTP(settings.SMTP_SERVER, int(settings.SMTP_PORT), timeout=10)
                server.starttls()
            
            with server:
                server.login(settings.SMTP_EMAIL, settings.SMTP_PASSWORD)
                server.sendmail(settings.SMTP_EMAIL, email, message.as_string())
            return True
        except Exception as e:
            print(f"SMTP Error: {e}")
            return False

email_service = EmailService()
