"""
tests/test_email_generator.py — Unit Tests for email_generator.py
"""

import pytest

from core.models import ContactRecord, AppConfig
from generator.email_generator import (
    generate_email,
    _generate_from_template,
    _validate_word_count
)
from data.data_loader import load_contacts


# ── Helpers ──────────────────────────────────────────────────────────────────

def _create_minimal_contact():
    return ContactRecord(
        recipient_email="test@example.com",
        company="Acme AI",
        role="Backend Engineer",
        candidate_name="Alex",
        candidate_background="Python dev"
    )

def _create_full_contact():
    return ContactRecord(
        recipient_email="test@example.com",
        company="Acme AI",
        role="Backend Engineer",
        candidate_name="Alex",
        candidate_background="Python dev",
        recipient_name="Priya",
        personalization_note="Saw your new product.",
        portfolio_url="https://alex.dev",
        linkedin_url="https://linkedin.com/in/alex",
        resume_link="https://alex.dev/resume.pdf"
    )


# ── Tests ────────────────────────────────────────────────────────────────────

def test_generates_subject_with_role():
    c = _create_minimal_contact()
    email = _generate_from_template(c)
    assert "Backend Engineer" in email.subject

def test_generates_body_with_company():
    c = _create_minimal_contact()
    email = _generate_from_template(c)
    assert "Acme AI" in email.body

def test_body_under_150_words():
    c = _create_full_contact()
    email = _generate_from_template(c)
    word_count = len(email.body.split())
    assert word_count <= 150

def test_personalization_note_included():
    c = _create_full_contact()
    email = _generate_from_template(c)
    assert "Saw your new product." in email.body

def test_fallback_when_no_personalization_note():
    c = _create_minimal_contact()
    email = _generate_from_template(c)
    assert "caught my attention" in email.body

def test_recipient_name_greeting():
    c = _create_full_contact()
    email = _generate_from_template(c)
    assert "Hi Priya," in email.body

def test_fallback_greeting():
    c = _create_minimal_contact()
    email = _generate_from_template(c)
    assert "Hi there," in email.body

def test_portfolio_url_in_signoff():
    c = _create_full_contact()
    email = _generate_from_template(c)
    assert "Portfolio: https://alex.dev" in email.body
    assert "LinkedIn: https://linkedin.com/in/alex" in email.body
    assert "Resume: https://alex.dev/resume.pdf" in email.body

def test_no_portfolio_url():
    c = _create_minimal_contact()
    email = _generate_from_template(c)
    assert "Portfolio:" not in email.body

def test_template_used_field():
    c = _create_minimal_contact()
    email = _generate_from_template(c)
    assert email.template_used == "default"

def test_contact_reference_preserved():
    c = _create_minimal_contact()
    email = _generate_from_template(c)
    assert email.contact is c

def test_validate_word_count(capsys):
    assert _validate_word_count("hello " * 10, limit=20) is True
    # Should not block, but should log a warning
    assert _validate_word_count("hello " * 30, limit=20) is False
    stderr = capsys.readouterr().err
    assert "Warning: Email body exceeds 20 words" in stderr

def test_full_generation_pipeline():
    """Integration test: Load -> Generate"""
    # Assuming contacts.json exists from Phase 2
    contacts = load_contacts("data/contacts.json")
    config = AppConfig(llm_enabled=False)
    
    for contact in contacts:
        email = generate_email(contact, config)
        assert email.subject
        assert email.body
        assert email.template_used == "default"

def test_llm_fallback_without_groq(capsys):
    """Test that setting llm_enabled without groq installed/configured falls back cleanly."""
    c = _create_minimal_contact()
    config = AppConfig(llm_enabled=True, llm_api_key="")
    
    email = generate_email(c, config)
    assert email.template_used == "default"
    
    stderr = capsys.readouterr().err
    assert "Warning:" in stderr
