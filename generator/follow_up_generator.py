"""
follow_up_generator.py — Follow-Up Email Generator

Reads the outreach_log.csv, finds emails sent > 3 days ago,
and generates a short follow-up referencing the original.
"""

import csv
import os
from datetime import datetime, timedelta
from typing import List, Dict

from core.models import ContactRecord, GeneratedEmail, AppConfig
from generator.email_generator import generate_email


def get_contacts_needing_follow_up(log_file: str, days_ago: int = 3) -> List[Dict]:
    """Reads the log file and returns a list of log entries that need a follow up."""
    if not os.path.exists(log_file):
        return []

    needs_follow_up = []
    cutoff_date = datetime.now() - timedelta(days=days_ago)

    with open(log_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("status") in ["sent", "drafted"]:
                try:
                    # ISO format parse
                    sent_date = datetime.fromisoformat(row["timestamp"])
                    if sent_date < cutoff_date:
                        needs_follow_up.append(row)
                except ValueError:
                    continue
                    
    return needs_follow_up


def generate_follow_up(log_entry: Dict, config: AppConfig) -> GeneratedEmail:
    """Generates a follow-up email based on a log entry."""
    
    # Reconstruct a ContactRecord from the log entry (partial)
    contact = ContactRecord(
        recipient_email=log_entry["recipient_email"],
        company=log_entry["company"],
        role=log_entry["role"],
        candidate_name=config.sender_name or "Me",
        candidate_background="" # We don't have this in the log, but we keep it short
    )
    
    if config.llm_enabled and config.llm_api_key:
        prompt = f"""Write a very short, polite follow-up email (2-3 sentences).
        Recipient Company: {contact.company}
        Role: {contact.role}
        My Name: {contact.candidate_name}
        Original Subject: {log_entry.get('subject', 'My previous email')}
        
        It should reference that I emailed them a few days ago and just wanted to bubble this up to the top of their inbox.
        
        Return format:
        SUBJECT: Re: <original subject>
        BODY:
        <email body>
        """
        
        try:
            from groq import Groq
            client = Groq(api_key=config.llm_api_key)
            chat_completion = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=config.llm_model,
            )
            response = chat_completion.choices[0].message.content
            
            # Simple parse
            lines = response.strip().split("\n")
            subject = lines[0].replace("SUBJECT:", "").strip() if "SUBJECT:" in lines[0] else f"Re: {log_entry.get('subject', '')}"
            body_lines = [l for l in lines[1:] if not l.startswith("BODY:")]
            body = "\n".join(body_lines).strip()
            
            return GeneratedEmail(subject=subject, body=body, contact=contact, template_used="llm_follow_up")
        except Exception:
            pass # Fallback to template

    # Template fallback
    subject = f"Re: {log_entry.get('subject', 'Following up')}"
    body = f"Hi there,\n\nI wanted to quickly follow up on my previous note regarding the {contact.role} role at {contact.company}. I know things can get busy, so I just wanted to bubble this up to the top of your inbox.\n\nBest,\n{contact.candidate_name}"
    
    return GeneratedEmail(subject=subject, body=body, contact=contact, template_used="template_follow_up")
