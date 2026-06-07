"""
tests/test_scorer.py — Unit tests for scorer.py
"""

from core.models import ContactRecord, GeneratedEmail
from generator.scorer import score_email, get_score_label

def _create_mock_email(subject="Test", body="Test") -> GeneratedEmail:
    contact = ContactRecord(
        recipient_email="test@example.com",
        company="Acme",
        role="Developer",
        candidate_name="Alex",
        candidate_background="Python"
    )
    return GeneratedEmail(subject=subject, body=body, contact=contact, template_used="default")

def test_perfect_score():
    # >50 words, mentions Acme, mentions Developer, has a ?, has a link, subject mentions both
    body = "Hi there,\n\n" + "I noticed Acme is hiring a Developer. " * 8 + "Would you like to chat? \nhttps://link.com"
    subject = "Acme Developer role"
    email = _create_mock_email(subject, body)
    
    score, breakdown = score_email(email)
    
    assert score == 100
    assert breakdown["word_count"] == 20
    assert breakdown["personalization"] == 30
    assert breakdown["clear_ask"] == 20
    assert breakdown["links"] == 15
    assert breakdown["subject_relevance"] == 15

def test_word_count_penalties():
    # Too short (< 50)
    email_short = _create_mock_email(body="Too short email.")
    _, bk_short = score_email(email_short)
    assert bk_short["word_count"] == 10
    
    # Too long (> 150) - 160 words
    email_long = _create_mock_email(body="word " * 160)
    _, bk_long = score_email(email_long)
    assert bk_long["word_count"] == 18  # 20 - ((160-150)//5) = 18

def test_missing_personalization():
    body = "Hi there, I am a great fit. Do you want to connect? https://link.com"
    subject = "Hello"
    email = _create_mock_email(subject, body)
    
    score, breakdown = score_email(email)
    assert breakdown["personalization"] == 0
    assert breakdown["subject_relevance"] == 0

def test_labels():
    assert get_score_label(95) == "EXCELLENT"
    assert get_score_label(80) == "GOOD"
    assert get_score_label(65) == "FAIR"
    assert get_score_label(40) == "POOR"
