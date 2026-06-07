"""
exceptions.py — Custom Exception Hierarchy for The Closer

All project-specific exceptions inherit from CloserError,
making it easy to catch any project error with a single
except clause while still allowing granular handling.

Hierarchy:
    CloserError (base)
    ├── ConfigError        — Missing or invalid .env values
    ├── ValidationError    — Bad contact data (missing fields, bad email)
    └── DeliveryError      — SMTP/API send failures
"""


class CloserError(Exception):
    """Base exception for The Closer.

    All project-specific exceptions should inherit from this class
    so callers can catch any Closer error generically.
    """

    pass


class ConfigError(CloserError):
    """Raised when configuration is missing, incomplete, or invalid.

    Examples:
        - .env file not found
        - SMTP credentials missing when DRY_RUN=false
        - SMTP_PORT is not a valid integer
        - SEND_MODE is not a recognized value
    """

    pass


class ValidationError(CloserError):
    """Raised when input contact data fails validation.

    Examples:
        - Required field (recipient_email, company, role) is missing
        - Email address does not match basic format
        - Required field is empty or whitespace-only
    """

    pass


class DeliveryError(CloserError):
    """Raised when email delivery encounters a fatal error.

    This exception signals that the pipeline should abort because
    subsequent sends will likely fail too (e.g., authentication failure).

    Non-fatal delivery errors (e.g., single recipient rejected) should
    be returned as a failed SendResult instead of raising this exception.

    Examples:
        - SMTP authentication failure (wrong password)
        - Gmail API OAuth token expired and cannot refresh
    """

    pass
