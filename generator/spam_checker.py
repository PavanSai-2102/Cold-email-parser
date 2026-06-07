"""
spam_checker.py — Spam Risk Checker

Analyzes a GeneratedEmail for common spam triggers:
too many links, ALL CAPS words, spam keywords, short bodies.
Returns a Risk Level (LOW, MEDIUM, HIGH) and specific flags.
"""

from typing import List, Tuple
import re

from core.models import GeneratedEmail

SPAM_WORDS = {
    "free", "guarantee", "urgent", "100%", "act now", "limited time",
    "risk-free", "winner", "prize", "cash", "credit"
}


def check_spam_risk(email: GeneratedEmail) -> Tuple[str, List[str]]:
    """Evaluates the email and returns (risk_level, list_of_flags)."""
    flags = []
    body = email.body
    body_lower = body.lower()
    
    # 1. Links Count
    links_count = body_lower.count("http://") + body_lower.count("https://")
    if links_count > 2:
        flags.append(f"Too many links ({links_count})")
        
    # 2. ALL CAPS words (excluding valid acronyms if possible, simple heuristic)
    words = re.findall(r'\b[A-Z]{3,}\b', body)
    if len(words) > 3:
        flags.append(f"Multiple ALL CAPS words found: {', '.join(words[:3])}...")
        
    # 3. Spam trigger words
    found_spam_words = [w for w in SPAM_WORDS if w in body_lower]
    if found_spam_words:
        flags.append(f"Spam trigger words detected: {', '.join(found_spam_words)}")
        
    # 4. Short body
    word_count = len(body.split())
    if word_count < 30:
        flags.append(f"Body is suspiciously short ({word_count} words)")
        
    # 5. Missing personalization
    if email.contact.company.lower() not in body_lower:
        flags.append("Company name missing from body")
        
    # Determine risk level
    if len(flags) == 0:
        risk_level = "LOW"
    elif len(flags) <= 2:
        risk_level = "MEDIUM"
    else:
        risk_level = "HIGH"
        
    # If spam words are detected, automatically elevate to HIGH
    if found_spam_words:
        risk_level = "HIGH"
        
    return risk_level, flags
