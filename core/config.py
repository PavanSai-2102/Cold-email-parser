"""
config.py — Configuration Manager for The Closer

Loads environment variables from a .env file, validates them,
and returns a typed AppConfig instance.

Public API:
    load_config(env_path=".env") -> AppConfig

Validation rules:
    - If DRY_RUN=false, SMTP_USER and SMTP_PASSWORD must be set
    - SMTP_PORT must be a valid integer (1–65535)
    - SEND_MODE must be one of: smtp, gmail_api, sendgrid, resend
    - If LLM_ENABLED=true, LLM_API_KEY must be set
"""

import os
from pathlib import Path

from dotenv import load_dotenv

from .exceptions import ConfigError
from .models import AppConfig


# Valid send modes
_VALID_SEND_MODES = {"smtp", "gmail_api", "sendgrid", "resend"}


def _parse_bool(value: str) -> bool:
    """Parse a string to boolean, defaulting to True for unrecognized values.

    Recognized true values:  "true", "1", "yes", "on"
    Recognized false values: "false", "0", "no", "off"
    Anything else defaults to True (safe default — dry run stays on).
    """
    if value.lower().strip() in ("false", "0", "no", "off"):
        return False
    # Safe default: treat unrecognized values as True (dry_run stays enabled)
    return True


def load_config(env_path: str = ".env") -> AppConfig:
    """Load configuration from .env file and validate all settings.

    Args:
        env_path: Path to the .env file. Defaults to ".env" in the
                  current working directory.

    Returns:
        AppConfig with all settings loaded and validated.

    Raises:
        ConfigError: If required settings are missing or values are invalid.
    """
    # Load .env file (system env vars take precedence)
    env_file = Path(env_path)
    if env_file.exists():
        load_dotenv(env_file, override=False)

    # ── Read and strip all values ──
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com").strip()
    smtp_port_str = os.getenv("SMTP_PORT", "587").strip()
    smtp_user = os.getenv("SMTP_USER", "").strip()
    smtp_password = os.getenv("SMTP_PASSWORD", "").strip()
    sender_name = os.getenv("SENDER_NAME", "").strip()
    dry_run_str = os.getenv("DRY_RUN", "true").strip()
    send_mode = os.getenv("SEND_MODE", "smtp").strip().lower()
    input_file = os.getenv("INPUT_FILE", "data/contacts.json").strip()
    log_file = os.getenv("LOG_FILE", "outreach_log.csv").strip()
    llm_enabled_str = os.getenv("LLM_ENABLED", "false").strip()
    llm_api_key = os.getenv("LLM_API_KEY", "").strip()
    llm_provider = os.getenv("LLM_PROVIDER", "groq").strip().lower()
    llm_model = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile").strip()

    # ── Parse booleans ──
    dry_run = _parse_bool(dry_run_str)
    llm_enabled = _parse_bool(llm_enabled_str)

    # ── Validate SMTP_PORT ──
    try:
        smtp_port = int(smtp_port_str)
    except ValueError:
        raise ConfigError(
            f"SMTP_PORT must be an integer, got '{smtp_port_str}'"
        )

    if not (1 <= smtp_port <= 65535):
        raise ConfigError(
            f"SMTP_PORT must be between 1 and 65535, got {smtp_port}"
        )

    # ── Validate SEND_MODE ──
    if send_mode not in _VALID_SEND_MODES:
        raise ConfigError(
            f"SEND_MODE must be one of {sorted(_VALID_SEND_MODES)}, "
            f"got '{send_mode}'"
        )

    # ── Validate SMTP credentials in live mode ──
    if not dry_run:
        if not smtp_user:
            raise ConfigError(
                "SMTP_USER is required when DRY_RUN=false. "
                "Set SMTP_USER in your .env file."
            )
        if not smtp_password:
            raise ConfigError(
                "SMTP_PASSWORD is required when DRY_RUN=false. "
                "Set SMTP_PASSWORD in your .env file. "
                "For Gmail, use an App Password: "
                "https://myaccount.google.com/apppasswords"
            )

    # ── Validate LLM config ──
    if llm_enabled and not llm_api_key:
        raise ConfigError(
            "LLM_API_KEY is required when LLM_ENABLED=true. "
            "Get your Groq API key at: https://console.groq.com/keys"
        )

    # ── Default sender_name to smtp_user if not set ──
    if not sender_name and smtp_user:
        sender_name = smtp_user

    # ── Build and return config ──
    return AppConfig(
        smtp_host=smtp_host,
        smtp_port=smtp_port,
        smtp_user=smtp_user,
        smtp_password=smtp_password,
        sender_name=sender_name,
        dry_run=dry_run,
        send_mode=send_mode,
        input_file=input_file,
        log_file=log_file,
        llm_enabled=llm_enabled,
        llm_api_key=llm_api_key if llm_api_key else None,
        llm_provider=llm_provider,
        llm_model=llm_model,
    )
