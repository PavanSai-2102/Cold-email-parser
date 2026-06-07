"""
scorer.py — Email Quality Scoring

Grades an email on a 0-100 scale based on:
Word count (20), Personalization (30), Clear ask (20),
Sign-off links (15), Subject relevance (15).
"""

from typing import Dict, Tuple

from core.models import GeneratedEmail


def score_email(email: GeneratedEmail) -> Tuple[int, Dict[str, int]]:
    """Calculates the quality score of a GeneratedEmail."""
    score = 0
    breakdown = {}
    
    body = email.body.lower()
    subject = email.subject.lower()
    contact = email.contact
    
    # 1. Word Count (max 20)
    word_count = len(body.split())
    if 50 <= word_count <= 150:
        breakdown["word_count"] = 20
    elif word_count < 50:
        breakdown["word_count"] = 10
    else:
        # Penalize long emails
        breakdown["word_count"] = max(0, 20 - ((word_count - 150) // 5))
    score += breakdown["word_count"]
    
    # 2. Personalization (max 30)
    pers_score = 0
    if contact.company.lower() in body:
        pers_score += 15
    # For role, handle multi-word roles safely
    if any(word.lower() in body for word in contact.role.split()):
        pers_score += 15
    breakdown["personalization"] = pers_score
    score += pers_score
    
    # 3. Clear Ask (max 20)
    # Check for question marks or action words
    if "?" in body or "chat" in body or "discuss" in body or "connect" in body:
        breakdown["clear_ask"] = 20
    else:
        breakdown["clear_ask"] = 0
    score += breakdown["clear_ask"]
    
    # 4. Sign-off Links (max 15)
    # Check for http or https
    if "http://" in body or "https://" in body:
        breakdown["links"] = 15
    else:
        breakdown["links"] = 0
    score += breakdown["links"]
    
    # 5. Subject Relevance (max 15)
    subj_score = 0
    if contact.company.lower() in subject:
        subj_score += 7
    if any(word.lower() in subject for word in contact.role.split()):
        subj_score += 8
    breakdown["subject_relevance"] = subj_score
    score += subj_score
    
    return score, breakdown


def get_score_label(score: int) -> str:
    """Returns a string label based on the score."""
    if score >= 90:
        return "EXCELLENT"
    elif score >= 75:
        return "GOOD"
    elif score >= 60:
        return "FAIR"
    else:
        return "POOR"
