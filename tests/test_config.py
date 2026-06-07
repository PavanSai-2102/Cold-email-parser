"""
tests/test_config.py — Unit Tests for config.py

Tests cover:
    - Loading a valid config with all defaults
    - Dry-run defaults to True
    - Missing SMTP credentials in live mode
    - Invalid port values (non-integer, out of range)
    - Invalid send mode
    - Whitespace stripping
    - LLM config validation
    - Boolean parsing edge cases
"""

import os
import tempfile
from pathlib import Path

import pytest

from core.config import load_config, _parse_bool
from core.exceptions import ConfigError
from core.models import AppConfig


# ── Helpers ──────────────────────────────────────────────────────────────────


def _write_env(path: str, lines: list[str]) -> str:
    """Write lines to a .env file and return the path."""
    env_path = os.path.join(path, ".env")
    with open(env_path, "w") as f:
        f.write("\n".join(lines) + "\n")
    return env_path


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    """Remove all Closer-related env vars before each test.

    This prevents env var leakage between tests since python-dotenv
    sets vars on os.environ.
    """
    env_vars = [
        "SMTP_HOST", "SMTP_PORT", "SMTP_USER", "SMTP_PASSWORD",
        "SENDER_NAME", "DRY_RUN", "SEND_MODE", "INPUT_FILE", "LOG_FILE",
        "LLM_ENABLED", "LLM_API_KEY", "LLM_PROVIDER", "LLM_MODEL",
    ]
    for var in env_vars:
        monkeypatch.delenv(var, raising=False)


# ── Tests: Valid Configuration ───────────────────────────────────────────────


def test_load_valid_config(tmp_path):
    """Config loads successfully with all valid settings."""
    env_path = _write_env(str(tmp_path), [
        "SMTP_HOST=smtp.gmail.com",
        "SMTP_PORT=587",
        "SMTP_USER=test@gmail.com",
        "SMTP_PASSWORD=app_password_123",
        "SENDER_NAME=Test User",
        "DRY_RUN=true",
        "SEND_MODE=smtp",
        "INPUT_FILE=data/contacts.json",
        "LOG_FILE=outreach_log.csv",
    ])

    config = load_config(env_path)

    assert isinstance(config, AppConfig)
    assert config.smtp_host == "smtp.gmail.com"
    assert config.smtp_port == 587
    assert config.smtp_user == "test@gmail.com"
    assert config.smtp_password == "app_password_123"
    assert config.sender_name == "Test User"
    assert config.dry_run is True
    assert config.send_mode == "smtp"
    assert config.input_file == "data/contacts.json"
    assert config.log_file == "outreach_log.csv"


def test_dry_run_defaults_true(tmp_path):
    """DRY_RUN defaults to True when not specified."""
    env_path = _write_env(str(tmp_path), [
        "SMTP_HOST=smtp.gmail.com",
        "SMTP_PORT=587",
    ])

    config = load_config(env_path)
    assert config.dry_run is True


def test_sender_name_defaults_to_smtp_user(tmp_path):
    """SENDER_NAME defaults to SMTP_USER when not set."""
    env_path = _write_env(str(tmp_path), [
        "SMTP_USER=alice@gmail.com",
    ])

    config = load_config(env_path)
    assert config.sender_name == "alice@gmail.com"


def test_all_defaults_with_empty_env(tmp_path):
    """Empty .env file produces safe defaults."""
    env_path = _write_env(str(tmp_path), [])

    config = load_config(env_path)

    assert config.smtp_host == "smtp.gmail.com"
    assert config.smtp_port == 587
    assert config.dry_run is True
    assert config.send_mode == "smtp"
    assert config.input_file == "data/contacts.json"
    assert config.log_file == "outreach_log.csv"
    assert config.llm_enabled is False


# ── Tests: Missing .env File ────────────────────────────────────────────────


def test_missing_env_file_uses_defaults(tmp_path):
    """Missing .env raises ConfigError (CFG-01)."""
    fake_path = os.path.join(str(tmp_path), "nonexistent.env")

    with pytest.raises(ConfigError, match="not found. Please copy .env.example to .env"):
        load_config(fake_path)


# ── Tests: SMTP Credentials in Live Mode ────────────────────────────────────


def test_missing_smtp_user_live_mode(tmp_path):
    """ConfigError raised when DRY_RUN=false and SMTP_USER is empty."""
    env_path = _write_env(str(tmp_path), [
        "DRY_RUN=false",
        "SMTP_USER=",
        "SMTP_PASSWORD=some_password",
    ])

    with pytest.raises(ConfigError, match="SMTP_USER is required"):
        load_config(env_path)


def test_missing_smtp_password_live_mode(tmp_path):
    """ConfigError raised when DRY_RUN=false and SMTP_PASSWORD is empty."""
    env_path = _write_env(str(tmp_path), [
        "DRY_RUN=false",
        "SMTP_USER=test@gmail.com",
        "SMTP_PASSWORD=",
    ])

    with pytest.raises(ConfigError, match="SMTP_PASSWORD is required"):
        load_config(env_path)


def test_smtp_creds_not_required_in_dry_run(tmp_path):
    """No error when SMTP creds are missing but DRY_RUN=true."""
    env_path = _write_env(str(tmp_path), [
        "DRY_RUN=true",
        "SMTP_USER=",
        "SMTP_PASSWORD=",
    ])

    config = load_config(env_path)
    assert config.dry_run is True  # No ConfigError raised


# ── Tests: Port Validation ──────────────────────────────────────────────────


def test_invalid_port_non_integer(tmp_path):
    """ConfigError raised for non-integer SMTP_PORT."""
    env_path = _write_env(str(tmp_path), [
        "SMTP_PORT=abc",
    ])

    with pytest.raises(ConfigError, match="SMTP_PORT must be an integer"):
        load_config(env_path)


def test_invalid_port_negative(tmp_path):
    """ConfigError raised for negative SMTP_PORT."""
    env_path = _write_env(str(tmp_path), [
        "SMTP_PORT=-1",
    ])

    with pytest.raises(ConfigError, match="must be between 1 and 65535"):
        load_config(env_path)


def test_invalid_port_zero(tmp_path):
    """ConfigError raised for SMTP_PORT=0."""
    env_path = _write_env(str(tmp_path), [
        "SMTP_PORT=0",
    ])

    with pytest.raises(ConfigError, match="must be between 1 and 65535"):
        load_config(env_path)


def test_invalid_port_too_high(tmp_path):
    """ConfigError raised for SMTP_PORT > 65535."""
    env_path = _write_env(str(tmp_path), [
        "SMTP_PORT=70000",
    ])

    with pytest.raises(ConfigError, match="must be between 1 and 65535"):
        load_config(env_path)


def test_valid_port_465(tmp_path):
    """Port 465 (SSL) is accepted."""
    env_path = _write_env(str(tmp_path), [
        "SMTP_PORT=465",
    ])

    config = load_config(env_path)
    assert config.smtp_port == 465


# ── Tests: Send Mode Validation ─────────────────────────────────────────────


def test_invalid_send_mode(tmp_path):
    """ConfigError raised for unknown SEND_MODE."""
    env_path = _write_env(str(tmp_path), [
        "SEND_MODE=pigeon",
    ])

    with pytest.raises(ConfigError, match="SEND_MODE must be one of"):
        load_config(env_path)


def test_valid_send_modes(tmp_path):
    """All valid send modes are accepted."""
    for mode in ("smtp", "gmail_api", "sendgrid", "resend"):
        # Clear cached env var from previous iteration
        os.environ.pop("SEND_MODE", None)
        env_path = _write_env(str(tmp_path), [
            f"SEND_MODE={mode}",
        ])
        config = load_config(env_path)
        assert config.send_mode == mode


def test_send_mode_case_insensitive(tmp_path):
    """SEND_MODE is case-insensitive."""
    env_path = _write_env(str(tmp_path), [
        "SEND_MODE=SMTP",
    ])

    config = load_config(env_path)
    assert config.send_mode == "smtp"


# ── Tests: Whitespace Handling ──────────────────────────────────────────────


def test_whitespace_stripped_from_values(tmp_path):
    """Leading and trailing whitespace is stripped from all values."""
    env_path = _write_env(str(tmp_path), [
        "SMTP_HOST=  smtp.gmail.com  ",
        "SMTP_PORT=  587  ",
        "SMTP_USER=  user@gmail.com  ",
        "SEND_MODE=  smtp  ",
    ])

    config = load_config(env_path)
    assert config.smtp_host == "smtp.gmail.com"
    assert config.smtp_port == 587
    assert config.smtp_user == "user@gmail.com"
    assert config.send_mode == "smtp"


# ── Tests: Boolean Parsing ──────────────────────────────────────────────────


def test_parse_bool_true_values():
    """True-like strings parse to True."""
    for val in ("true", "True", "TRUE", "1", "yes", "YES", "on", "ON"):
        assert _parse_bool(val) is True


def test_parse_bool_false_values():
    """False-like strings parse to False."""
    for val in ("false", "False", "FALSE", "0", "no", "NO", "off", "OFF"):
        assert _parse_bool(val) is False


def test_parse_bool_unknown_defaults_true():
    """Unknown values default to True (safe — keeps dry_run enabled)."""
    assert _parse_bool("maybe") is True
    assert _parse_bool("") is True
    assert _parse_bool("abc") is True


# ── Tests: LLM Configuration ────────────────────────────────────────────────


def test_llm_enabled_without_key_raises(tmp_path):
    """ConfigError raised when LLM_ENABLED=true but LLM_API_KEY is empty."""
    env_path = _write_env(str(tmp_path), [
        "LLM_ENABLED=true",
        "LLM_API_KEY=",
    ])

    with pytest.raises(ConfigError, match="LLM_API_KEY is required"):
        load_config(env_path)


def test_llm_enabled_with_key_succeeds(tmp_path):
    """LLM config loads successfully when key is provided."""
    env_path = _write_env(str(tmp_path), [
        "LLM_ENABLED=true",
        "LLM_API_KEY=gsk_test_key_123",
        "LLM_MODEL=llama-3.3-70b-versatile",
    ])

    config = load_config(env_path)
    assert config.llm_enabled is True
    assert config.llm_api_key == "gsk_test_key_123"
    assert config.llm_model == "llama-3.3-70b-versatile"
    assert config.llm_provider == "groq"


def test_llm_disabled_no_key_required(tmp_path):
    """No error when LLM is disabled and key is missing."""
    env_path = _write_env(str(tmp_path), [
        "LLM_ENABLED=false",
    ])

    config = load_config(env_path)
    assert config.llm_enabled is False
    assert config.llm_api_key is None
