"""
logger.py — CSV Audit Logger for The Closer

Appends a row to outreach_log.csv for every email processed,
ensuring a full audit trail of all actions (sent, drafted, skipped, failed).
"""

import csv
import os
from datetime import datetime
from typing import Dict

from core.models import LogEntry, GeneratedEmail, OutreachStatus


def make_log_entry(email: GeneratedEmail, status: OutreachStatus, error_message: str = "") -> LogEntry:
    return LogEntry(
        timestamp=datetime.now().isoformat(),
        recipient_email=email.contact.recipient_email,
        company=email.contact.company,
        role=email.contact.role,
        subject=email.subject,
        status=status,
        error_message=error_message or None
    )


def log_outreach(entry: LogEntry, log_file: str = "outreach_log.csv") -> None:
    """Appends one row to the CSV log. Creates file with headers if it doesn't exist."""
    file_exists = os.path.exists(log_file)
    
    fieldnames = [
        "timestamp", 
        "recipient_email", 
        "company", 
        "role", 
        "subject", 
        "status", 
        "error_message"
    ]
    
    try:
        with open(log_file, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            
            if not file_exists:
                writer.writeheader()
                
            writer.writerow({
                "timestamp": entry.timestamp,
                "recipient_email": entry.recipient_email,
                "company": entry.company,
                "role": entry.role,
                "subject": entry.subject,
                "status": entry.status.value,
                "error_message": entry.error_message or ""
            })
    except OSError as e:
        import sys
        print(f"⚠️  Warning: Failed to write to log file ({e}).", file=sys.stderr)


def get_summary(log_file: str = "outreach_log.csv") -> Dict[str, int]:
    """Reads the CSV log and returns a count of each status."""
    summary = {
        "sent": 0,
        "drafted": 0,
        "skipped": 0,
        "failed": 0,
        "generated": 0
    }
    
    if not os.path.exists(log_file):
        return summary
        
    try:
        with open(log_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                status = row.get("status")
                if status in summary:
                    summary[status] += 1
    except Exception:
        # If the file is locked or malformed, return partial or zero summary
        pass
        
    return summary
