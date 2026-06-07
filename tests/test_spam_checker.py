"""
tests/test_spam_checker.py — Unit tests for spam_checker.py
"""

from core.models import ContactRecord, GeneratedEmail
from generator.spam_checker import check_spam_risk

def _create_mock_email(body="Test") -> GeneratedEmail:
    contact = ContactRecord(
        recipient_email="test@example.com",
        company="Acme",
        role="Developer",
        candidate_name="Alex",
        candidate_background="Python"
    )
    return GeneratedEmail(subject="Test", body=body, contact=contact, template_used="default")

def test_low_risk():
    body = "Hi there,\n\nI noticed Acme is hiring a Developer. " * 5 + "\n\nWould you like to chat? \nhttps://link.com"
    email = _create_mock_email(body)
    
    risk_level, flags = check_spam_risk(email)
    assert risk_level == "LOW"
    assert len(flags) == 0

def test_spam_words_high_risk():
    body = "Hi there, I noticed Acme is hiring. This is URGENT and 100% FREE! " * 5
    email = _create_mock_email(body)
    
    risk_level, flags = check_spam_risk(email)
    assert risk_level == "HIGH"
    assert any("Spam trigger words" in flag for flag in flags)

def test_too_many_links():
    body = "Hi there, Acme is hiring. " * 5 + "https://1.com https://2.com https://3.com"
    email = _create_mock_email(body)
    
    risk_level, flags = check_spam_risk(email)
    assert risk_level == "MEDIUM"
    assert any("Too many links" in flag for flag in flags)

def test_all_caps():
    body = "Hi there, Acme is hiring. PLEASE READ THIS IMPORTANT MESSAGE. " * 5
    email = _create_mock_email(body)
    
    risk_level, flags = check_spam_risk(email)
    assert risk_level == "MEDIUM"
    assert any("ALL CAPS" in flag for flag in flags)
    
def test_short_body_missing_personalization():
    body = "Hi there. Click here."
    email = _create_mock_email(body)
    
    risk_level, flags = check_spam_risk(email)
    assert risk_level == "MEDIUM" or risk_level == "HIGH"
    assert any("suspiciously short" in flag for flag in flags)
    assert any("Company name missing" in flag for flag in flags)
