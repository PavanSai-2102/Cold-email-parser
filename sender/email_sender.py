"""
email_sender.py — Email Delivery for The Closer

Handles constructing MIME messages and sending them via SMTP.
Respects the DRY_RUN flag by returning a DRAFTED status instead of sending.
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from core.models import GeneratedEmail, AppConfig, SendResult, OutreachStatus
from core.exceptions import DeliveryError


def _build_mime_message(email: GeneratedEmail, config: AppConfig) -> MIMEMultipart:
    """Constructs the email MIME object."""
    msg = MIMEMultipart()
    
    sender_display = f"{config.sender_name} <{config.smtp_user}>" if config.sender_name else config.smtp_user
    
    msg['From'] = sender_display
    msg['To'] = email.contact.recipient_email
    msg['Subject'] = email.subject
    
    if config.smtp_user:
        msg['Reply-To'] = config.smtp_user
        
    msg.attach(MIMEText(email.body, 'plain', 'utf-8'))
    
    return msg


def _send_via_smtp(email: GeneratedEmail, config: AppConfig) -> SendResult:
    """Builds MIME message, connects via TLS, and sends via SMTP."""
    msg = _build_mime_message(email, config)
    
    # Check dry-run mode
    if config.dry_run:
        return SendResult(success=True, status=OutreachStatus.DRAFTED)
        
    # Connect and send
    try:
        with smtplib.SMTP(config.smtp_host, config.smtp_port, timeout=10) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(config.smtp_user, config.smtp_password)
            server.sendmail(
                config.smtp_user,
                email.contact.recipient_email,
                msg.as_string()
            )
        return SendResult(success=True, status=OutreachStatus.SENT)
        
    except smtplib.SMTPAuthenticationError as e:
        # Fatal error - wrong credentials
        raise DeliveryError(f"Authentication failed: {e}")
        
    except smtplib.SMTPRecipientsRefused as e:
        # Non-fatal - bad recipient email
        return SendResult(success=False, status=OutreachStatus.FAILED, error_message=f"Recipient refused: {e}")
        
    except smtplib.SMTPException as e:
        # Other SMTP errors (e.g. connection issues)
        return SendResult(success=False, status=OutreachStatus.FAILED, error_message=str(e))
        
    except Exception as e:
        # General exceptions (e.g. socket.gaierror, Timeout)
        return SendResult(success=False, status=OutreachStatus.FAILED, error_message=f"Connection error: {e}")


def send_email(email: GeneratedEmail, config: AppConfig) -> SendResult:
    """Main entry point; routes based on config.send_mode and config.dry_run."""
    if config.send_mode == "smtp":
        return _send_via_smtp(email, config)
    else:
        # For now, only SMTP is implemented. 
        # Future stretch goals can add gmail_api, sendgrid, resend.
        return SendResult(
            success=False, 
            status=OutreachStatus.FAILED, 
            error_message=f"Send mode '{config.send_mode}' is not yet implemented."
        )
