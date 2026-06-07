"""
tests/test_previewer.py — Unit Tests for previewer.py
"""

from unittest.mock import patch

from core.models import ContactRecord, GeneratedEmail, UserDecision
from preview.previewer import _format_preview, _get_user_input


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
        body="This is a test body.\nIt has multiple lines.\nTotal 11 words.",
        contact=contact,
        template_used="default"
    )


# ── Tests: Formatting ────────────────────────────────────────────────────────

def test_format_preview_contains_recipient():
    email = _create_test_email()
    preview = _format_preview(email)
    assert "To:      test@example.com" in preview

def test_format_preview_contains_subject():
    email = _create_test_email()
    preview = _format_preview(email)
    assert "Subject: Hello from Alex" in preview

def test_format_preview_contains_body():
    email = _create_test_email()
    preview = _format_preview(email)
    assert "  This is a test body." in preview
    assert "  It has multiple lines." in preview

def test_format_preview_shows_word_count():
    email = _create_test_email()
    preview = _format_preview(email)
    # The body has 12 words (split on whitespace)
    assert "Word count: 12/150" in preview

def test_format_preview_shows_pagination():
    email = _create_test_email()
    preview = _format_preview(email, current=3, total=5)
    assert "EMAIL PREVIEW  [3/5]" in preview


# ── Tests: Input Mapping ─────────────────────────────────────────────────────

@patch('builtins.input')
def test_send_input_mapping(mock_input):
    for choice in ("s", "send", "y", "yes", "S", "SEND"):
        mock_input.return_value = choice
        assert _get_user_input() == UserDecision.SEND

@patch('builtins.input')
def test_skip_input_mapping(mock_input):
    for choice in ("k", "skip", "n", "no", "K", "Skip"):
        mock_input.return_value = choice
        assert _get_user_input() == UserDecision.SKIP

@patch('builtins.input')
def test_quit_input_mapping(mock_input):
    for choice in ("q", "quit", "exit", "Q", "QUIT"):
        mock_input.return_value = choice
        assert _get_user_input() == UserDecision.QUIT

@patch('builtins.input')
def test_empty_input_defaults_skip(mock_input):
    """Empty string (just hitting Enter) should default to SKIP."""
    mock_input.return_value = ""
    assert _get_user_input() == UserDecision.SKIP
    mock_input.return_value = "   "
    assert _get_user_input() == UserDecision.SKIP

@patch('builtins.input', side_effect=["invalid", "s"])
def test_invalid_input_retries(mock_input, capsys):
    """Invalid input should print an error and prompt again."""
    decision = _get_user_input()
    
    assert decision == UserDecision.SEND
    assert mock_input.call_count == 2
    
    stderr = capsys.readouterr().err
    assert "Invalid choice" in stderr

@patch('builtins.input', side_effect=KeyboardInterrupt)
def test_keyboard_interrupt_quits(mock_input, capsys):
    """Ctrl+C should be caught and return QUIT."""
    decision = _get_user_input()
    assert decision == UserDecision.QUIT
    
    stdout = capsys.readouterr().out
    assert "Operation cancelled" in stdout
