"""
tests/test_follow_up.py — Unit tests for follow_up_generator.py
"""

import os
import csv
from datetime import datetime, timedelta
from core.config import AppConfig
from generator.follow_up_generator import get_contacts_needing_follow_up, generate_follow_up

def test_get_contacts_needing_follow_up(tmp_path):
    log_file = os.path.join(str(tmp_path), "test_log.csv")
    
    old_date = (datetime.now() - timedelta(days=4)).isoformat()
    new_date = (datetime.now() - timedelta(days=1)).isoformat()
    
    with open(log_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["timestamp", "recipient_email", "company", "role", "subject", "status", "error_message"])
        writer.writeheader()
        writer.writerow({
            "timestamp": old_date, "recipient_email": "old@test.com", 
            "company": "Acme", "role": "Dev", "subject": "Test 1", "status": "sent"
        })
        writer.writerow({
            "timestamp": new_date, "recipient_email": "new@test.com", 
            "company": "Beta", "role": "PM", "subject": "Test 2", "status": "sent"
        })
        writer.writerow({
            "timestamp": old_date, "recipient_email": "fail@test.com", 
            "company": "Gamma", "role": "QA", "subject": "Test 3", "status": "failed"
        })
        
    needs_follow_up = get_contacts_needing_follow_up(log_file, days_ago=3)
    
    # Should only return the old@test.com entry, since new@test.com is too recent and fail@test.com was not sent/drafted
    assert len(needs_follow_up) == 1
    assert needs_follow_up[0]["recipient_email"] == "old@test.com"


def test_generate_follow_up_template():
    log_entry = {
        "recipient_email": "test@test.com",
        "company": "Acme",
        "role": "Dev",
        "subject": "My Subject"
    }
    
    config = AppConfig(dry_run=True, llm_enabled=False, sender_name="Alex")
    
    email = generate_follow_up(log_entry, config)
    
    assert email.subject == "Re: My Subject"
    assert "follow up" in email.body.lower()
    assert "Acme" in email.body
    assert "Alex" in email.body
    assert email.template_used == "template_follow_up"
