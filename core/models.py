"""
models.py — Shared Data Models for The Closer

Defines all data classes and enums used across the pipeline:
- ContactRecord: Input contact/job target
- GeneratedEmail: Output of email generation
- LogEntry: Single row in the outreach log CSV
- AppConfig: Typed representation of .env configuration
- SendResult: Return type from email delivery
- OutreachStatus: Enum for email lifecycle states
- UserDecision: Enum for human review decisions
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class OutreachStatus(Enum):
    """Lifecycle status of an outreach email."""

    GENERATED = "generated"
    DRAFTED = "drafted"
    SENT = "sent"
    SKIPPED = "skipped"
    FAILED = "failed"


class UserDecision(Enum):
    """User's decision during the preview/confirmation step."""

    SEND = "send"       # Proceed to send or draft
    SKIP = "skip"       # Skip this contact, continue to next
    QUIT = "quit"       # Stop processing all remaining contacts
    EDIT = "edit"       # (Stretch) Allow inline editing before send


# ── Input Model ──────────────────────────────────────────────────────────────


@dataclass
class ContactRecord:
    """Represents a single outreach target (job listing / recruiter / company).

    Required fields must be present for every contact.
    Optional fields enhance personalization but are not mandatory.
    """

    # ── Required fields ──
    recipient_email: str
    company: str
    role: str
    candidate_name: str
    candidate_background: str

    # ── Optional fields ──
    recipient_name: Optional[str] = None
    job_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    personalization_note: Optional[str] = None
    linkedin_url: Optional[str] = None
    resume_link: Optional[str] = None


# ── Internal Model ───────────────────────────────────────────────────────────


@dataclass
class GeneratedEmail:
    """Output of the email generation stage.

    Contains the subject line, body text, and a back-reference
    to the contact that produced this email.
    """

    subject: str
    body: str
    contact: ContactRecord
    template_used: str = "default"


# ── Output Model ─────────────────────────────────────────────────────────────


@dataclass
class LogEntry:
    """Single row in outreach_log.csv.

    Captures the full context of each outreach attempt
    for auditing and debugging.
    """

    timestamp: str                          # ISO 8601 format
    recipient_email: str
    company: str
    role: str
    subject: str
    status: OutreachStatus
    error_message: Optional[str] = None


# ── Configuration Model ──────────────────────────────────────────────────────


@dataclass
class AppConfig:
    """Typed representation of .env configuration.

    All fields have safe defaults. Secrets (SMTP password, API keys)
    default to empty strings and are validated at runtime based on
    the current operating mode.
    """

    # ── SMTP settings ──
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    sender_name: str = ""

    # ── Runtime behavior ──
    dry_run: bool = True                    # Safe default: never send without opt-in
    send_mode: str = "smtp"                 # smtp | gmail_api | sendgrid | resend

    # ── File paths ──
    input_file: str = "contacts.json"
    log_file: str = "outreach_log.csv"

    # ── LLM via Groq (optional) ──
    llm_enabled: bool = False
    llm_api_key: Optional[str] = None       # Groq API key (gsk_...)
    llm_provider: str = "groq"              # LLM provider
    llm_model: str = "llama-3.3-70b-versatile"  # Groq model name


# ── Delivery Result Model ────────────────────────────────────────────────────


@dataclass
class SendResult:
    """Return type from the email sender.

    Encapsulates whether the send succeeded, the resulting status,
    and any error details or message ID for tracking.
    """

    success: bool
    status: OutreachStatus
    error_message: Optional[str] = None
    message_id: Optional[str] = None
