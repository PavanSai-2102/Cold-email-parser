"""
data_loader.py — Contact Ingestion for The Closer

Responsible for loading, parsing, validating, and filtering contact records.
Supported data sources:
- .json (array of objects)
- .csv (with header row)
- "hardcoded" (built-in sample list)
"""

import csv
import json
import re
from typing import List, Set

from core.exceptions import ValidationError
from core.models import ContactRecord


# Basic email regex validation
EMAIL_REGEX = re.compile(r"^[^@]+@[^@]+\.[^@]+$")


def validate_contact(data: dict) -> ContactRecord:
    """Validate raw dictionary data and return a typed ContactRecord.

    Args:
        data: Raw dictionary from JSON or CSV.

    Returns:
        ContactRecord instance.

    Raises:
        ValidationError: If required fields are missing/empty or email is invalid.
    """
    # ── 1. Check required fields ──
    required_fields = [
        "recipient_email",
        "company",
        "role",
        "candidate_name",
        "candidate_background",
    ]

    for field in required_fields:
        val = data.get(field)
        if val is None or not str(val).strip():
            raise ValidationError(f"Missing required field: '{field}'")

    email = str(data["recipient_email"]).strip()
    
    # ── 2. Validate email format ──
    if not EMAIL_REGEX.match(email):
        raise ValidationError(f"Invalid email format: '{email}'")

    # ── 3. Construct record ──
    # Safely get optional fields, defaulting to None if missing or empty string
    def _get_opt(key: str):
        val = data.get(key)
        if val is None:
            return None
        val_str = str(val).strip()
        return val_str if val_str else None

    return ContactRecord(
        recipient_email=email,
        company=str(data["company"]).strip(),
        role=str(data["role"]).strip(),
        candidate_name=str(data["candidate_name"]).strip(),
        candidate_background=str(data["candidate_background"]).strip(),
        recipient_name=_get_opt("recipient_name"),
        job_url=_get_opt("job_url"),
        portfolio_url=_get_opt("portfolio_url"),
        personalization_note=_get_opt("personalization_note"),
        linkedin_url=_get_opt("linkedin_url"),
        resume_link=_get_opt("resume_link"),
    )


def _load_from_json(path: str) -> List[dict]:
    """Load raw contacts from a JSON file."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, list):
                raise ValidationError("Expected a JSON array of contact objects.")
            return data
    except json.JSONDecodeError as e:
        raise ValidationError(f"Malformed JSON in '{path}': {e}")


def _load_from_csv(path: str) -> List[dict]:
    """Load raw contacts from a CSV file."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            # Check if file is empty
            content = f.read(1)
            if not content:
                return []
            f.seek(0)
            
            # Using DictReader automatically uses the first row as headers
            reader = csv.DictReader(f)
            if not reader.fieldnames:
                raise ValidationError("CSV file must have a header row.")
            
            return list(reader)
    except UnicodeDecodeError:
        # Fallback for some common encoding issues, though UTF-8 is expected
        with open(path, "r", encoding="latin-1") as f:
            reader = csv.DictReader(f)
            return list(reader)


def _load_hardcoded() -> List[dict]:
    """Return built-in sample data for testing without files."""
    return [
        {
            "recipient_name": "Priya Sharma",
            "recipient_email": "priya@example.com",
            "company": "Acme AI",
            "role": "Backend Engineering Intern",
            "candidate_name": "Test User",
            "candidate_background": "Python developer",
        },
        {
            "recipient_email": "hr@example.org",
            "company": "Startup.org",
            "role": "Full Stack Dev",
            "candidate_name": "Test User",
            "candidate_background": "React & Node",
        },
        {
            "recipient_name": "Bob Smith",
            "recipient_email": "bob@example.net",
            "company": "Enterprise LLC",
            "role": "Data Engineer",
            "candidate_name": "Test User",
            "candidate_background": "SQL and pipelines",
        },
    ]


def load_contacts(source: str) -> List[ContactRecord]:
    """Load and validate contacts from a data source.

    Args:
        source: Path to a .json or .csv file, or the string "hardcoded".

    Returns:
        List of validated ContactRecord objects.

    Raises:
        ValueError: If source type is unsupported.
        FileNotFoundError: If the source file doesn't exist.
        ValidationError: If file format is invalid.
    """
    if not source:
        raise ValueError("No data source specified.")

    source_lower = source.lower()
    raw_data = []

    if source_lower == "hardcoded":
        raw_data = _load_hardcoded()
    elif source_lower.endswith(".json"):
        raw_data = _load_from_json(source)
    elif source_lower.endswith(".csv"):
        raw_data = _load_from_csv(source)
    else:
        raise ValueError(f"Unsupported data source: '{source}'. Use .json, .csv, or 'hardcoded'.")

    valid_contacts = []
    for i, data in enumerate(raw_data):
        try:
            contact = validate_contact(data)
            valid_contacts.append(contact)
        except ValidationError as e:
            print(f"⚠️  Skipping invalid record at index {i}: {e}")

    return valid_contacts


def load_opt_out_list(path: str = "data/opt_out.txt") -> Set[str]:
    """Read opt-out file and return a set of lowercased emails.
    
    Ignores blank lines and comments starting with '#'.
    If the file doesn't exist, returns an empty set.
    """
    opt_outs = set()
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    opt_outs.add(line.lower())
    except FileNotFoundError:
        pass  # Opt-out file is optional
    return opt_outs


def filter_opt_outs(contacts: List[ContactRecord], opt_outs: Set[str]) -> List[ContactRecord]:
    """Remove contacts whose email is in the opt-out list."""
    if not opt_outs:
        return contacts
    
    filtered = []
    for c in contacts:
        if c.recipient_email.lower() in opt_outs:
            print(f"⏭️  Skipping {c.recipient_email} (in opt-out list)")
        else:
            filtered.append(c)
            
    return filtered
