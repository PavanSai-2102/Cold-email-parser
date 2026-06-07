"""
tests/test_sender_logger.py — Unit tests for Phase 5 components.
"""

import os
from unittest.mock import patch, MagicMock

import pytest

from core.models import ContactRecord, GeneratedEmail, AppConfig, OutreachStatus, LogEntry
from core.exceptions import DeliveryError
from sender.email_sender import _build_mime_message, _send_via_smtp, send_email
from sender.logger import log_outreach, get_summary


# ── Helpers ──────────────────────────────────────────────────────────────────

def _create_test_email() -> GeneratedEmail:
    contact = ContactRecord(
        recipient_email="test@example.com",
        company="Acme AI",
        role="Backend Engineer",
        candidate_name="Alex",
        candidate_background="Python dev"
    )
    return GeneratedEmail(
        subject="Hello from Alex",
        body="Test body",
        contact=contact,
        template_used="default"
    )


# ── Tests: Email Sender ──────────────────────────────────────────────────────

def test_build_mime_message():
    email = _create_test_email()
    config = AppConfig(smtp_user="me@gmail.com", sender_name="My Name")
    
    msg = _build_mime_message(email, config)
    
    assert msg['To'] == "test@example.com"
    assert msg['From'] == "My Name <me@gmail.com>"
    assert msg['Subject'] == "Hello from Alex"
    assert msg['Reply-To'] == "me@gmail.com"
    
    payload = msg.get_payload()[0].get_payload(decode=True).decode('utf-8')
    assert "Test body" in payload

def test_send_dry_run():
    email = _create_test_email()
    config = AppConfig(dry_run=True)
    
    result = send_email(email, config)
    
    assert result.success is True
    assert result.status == OutreachStatus.DRAFTED

@patch("smtplib.SMTP")
def test_send_live_success(mock_smtp):
    email = _create_test_email()
    config = AppConfig(dry_run=False, smtp_user="u", smtp_password="p")
    
    # Setup mock
    mock_server = MagicMock()
    mock_smtp.return_value.__enter__.return_value = mock_server
    
    result = send_email(email, config)
    
    assert result.success is True
    assert result.status == OutreachStatus.SENT
    
    mock_server.starttls.assert_called_once()
    mock_server.login.assert_called_once_with("u", "p")
    mock_server.sendmail.assert_called_once()

@patch("smtplib.SMTP")
def test_send_live_auth_error(mock_smtp):
    import smtplib
    email = _create_test_email()
    config = AppConfig(dry_run=False, smtp_user="u", smtp_password="p")
    
    mock_server = MagicMock()
    mock_smtp.return_value.__enter__.return_value = mock_server
    mock_server.login.side_effect = smtplib.SMTPAuthenticationError(535, b"Auth failed")
    
    with pytest.raises(DeliveryError, match="Authentication failed"):
        send_email(email, config)


# ── Tests: Logger ────────────────────────────────────────────────────────────

def test_log_outreach_creates_file(tmp_path):
    log_file = str(tmp_path / "test_log.csv")
    email = _create_test_email()
    
    entry = LogEntry(
        timestamp="2026-06-01T12:00:00",
        recipient_email=email.contact.recipient_email,
        company=email.contact.company,
        role=email.contact.role,
        subject=email.subject,
        status=OutreachStatus.SENT,
        error_message=""
    )
    
    log_outreach(entry, log_file)
    
    assert os.path.exists(log_file)
    with open(log_file, "r") as f:
        content = f.read()
        assert "timestamp,recipient_email,company,role,subject,status,error_message" in content
        assert "test@example.com,Acme AI,Backend Engineer,Hello from Alex,sent" in content

def test_get_summary(tmp_path):
    log_file = str(tmp_path / "test_log.csv")
    email = _create_test_email()
    
    # Write 2 sent, 1 drafted
    log_outreach(LogEntry("T1", "a", "A", "R", "S", OutreachStatus.SENT), log_file)
    log_outreach(LogEntry("T2", "b", "A", "R", "S", OutreachStatus.SENT), log_file)
    log_outreach(LogEntry("T3", "c", "A", "R", "S", OutreachStatus.DRAFTED), log_file)
    
    summary = get_summary(log_file)
    
    assert summary["sent"] == 2
    assert summary["drafted"] == 1
    assert summary["skipped"] == 0
    assert summary["failed"] == 0
