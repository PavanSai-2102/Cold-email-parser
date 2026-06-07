"""
tests/test_data_loader.py — Unit Tests for data_loader.py
"""

import os
from pathlib import Path

import pytest

from data.data_loader import (
    load_contacts,
    validate_contact,
    load_opt_out_list,
    filter_opt_outs,
)
from core.exceptions import ValidationError
from core.models import ContactRecord


# ── Helpers ──────────────────────────────────────────────────────────────────

def _write_file(path: str, content: str) -> str:
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path


# ── Tests: validate_contact ──────────────────────────────────────────────────

def test_validate_contact_valid():
    """Valid record parses correctly."""
    data = {
        "recipient_email": "test@example.com",
        "company": "TestCo",
        "role": "Engineer",
        "candidate_name": "Alice",
        "candidate_background": "Dev",
        "recipient_name": "Bob",
    }
    contact = validate_contact(data)
    assert contact.recipient_email == "test@example.com"
    assert contact.company == "TestCo"
    assert contact.recipient_name == "Bob"
    assert contact.job_url is None

def test_missing_required_field():
    """Missing required field raises ValidationError."""
    data = {
        "company": "TestCo",
        "role": "Engineer",
        "candidate_name": "Alice",
        "candidate_background": "Dev",
    }
    with pytest.raises(ValidationError, match="Missing required field: 'recipient_email'"):
        validate_contact(data)

def test_empty_required_field():
    """Empty required field raises ValidationError."""
    data = {
        "recipient_email": "  ",
        "company": "TestCo",
        "role": "Engineer",
        "candidate_name": "Alice",
        "candidate_background": "Dev",
    }
    with pytest.raises(ValidationError, match="Missing required field: 'recipient_email'"):
        validate_contact(data)

def test_invalid_email_format():
    """Invalid email raises ValidationError."""
    data = {
        "recipient_email": "not-an-email",
        "company": "TestCo",
        "role": "Engineer",
        "candidate_name": "Alice",
        "candidate_background": "Dev",
    }
    with pytest.raises(ValidationError, match="Invalid email format"):
        validate_contact(data)

def test_optional_fields_default_none():
    """Missing optional fields become None."""
    data = {
        "recipient_email": "a@b.com",
        "company": "C",
        "role": "R",
        "candidate_name": "N",
        "candidate_background": "B",
    }
    contact = validate_contact(data)
    assert contact.recipient_name is None
    assert contact.job_url is None

def test_unknown_fields_ignored():
    """Extra fields do not cause errors."""
    data = {
        "recipient_email": "a@b.com",
        "company": "C",
        "role": "R",
        "candidate_name": "N",
        "candidate_background": "B",
        "extra_field": "ignore me",
    }
    contact = validate_contact(data)
    assert not hasattr(contact, "extra_field")


# ── Tests: load_contacts ─────────────────────────────────────────────────────

def test_load_valid_json(tmp_path):
    """Loading valid JSON returns records."""
    json_path = _write_file(str(tmp_path / "data.json"), '''
    [
      {
        "recipient_email": "a@example.com",
        "company": "A",
        "role": "R",
        "candidate_name": "N",
        "candidate_background": "B"
      }
    ]
    ''')
    contacts = load_contacts(json_path)
    assert len(contacts) == 1
    assert contacts[0].recipient_email == "a@example.com"

def test_load_malformed_json(tmp_path):
    """Malformed JSON raises ValidationError."""
    json_path = _write_file(str(tmp_path / "data.json"), '[{ "bad": "json"')
    with pytest.raises(ValidationError, match="Malformed JSON"):
        load_contacts(json_path)

def test_load_json_not_array(tmp_path):
    """JSON that is an object instead of array raises ValidationError."""
    json_path = _write_file(str(tmp_path / "data.json"), '{"email": "a@b.com"}')
    with pytest.raises(ValidationError, match="Expected a JSON array"):
        load_contacts(json_path)

def test_load_valid_csv(tmp_path):
    """Loading valid CSV returns records."""
    csv_path = _write_file(str(tmp_path / "data.csv"),
        "recipient_email,company,role,candidate_name,candidate_background\n"
        "a@example.com,A,R,N,B\n"
    )
    contacts = load_contacts(csv_path)
    assert len(contacts) == 1
    assert contacts[0].recipient_email == "a@example.com"

def test_load_empty_csv(tmp_path):
    """Empty CSV returns empty list."""
    csv_path = _write_file(str(tmp_path / "data.csv"), "")
    contacts = load_contacts(csv_path)
    assert contacts == []

def test_load_hardcoded():
    """Hardcoded source returns non-empty list."""
    contacts = load_contacts("hardcoded")
    assert len(contacts) > 0

def test_unsupported_source():
    """Unsupported extension raises ValueError."""
    with pytest.raises(ValueError, match="Unsupported data source"):
        load_contacts("data.xml")

def test_file_not_found():
    """Missing file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        load_contacts("does_not_exist.json")

def test_skip_invalid_records_in_file(tmp_path, capsys):
    """Invalid records in a file are skipped, valid ones are loaded."""
    json_path = _write_file(str(tmp_path / "data.json"), '''
    [
      {
        "recipient_email": "a@example.com",
        "company": "A",
        "role": "R",
        "candidate_name": "N",
        "candidate_background": "B"
      },
      {
        "recipient_email": "not-an-email",
        "company": "A",
        "role": "R",
        "candidate_name": "N",
        "candidate_background": "B"
      }
    ]
    ''')
    contacts = load_contacts(json_path)
    assert len(contacts) == 1
    
    stderr = capsys.readouterr().out
    assert "Skipping invalid record" in stderr


# ── Tests: Opt-out Filtering ─────────────────────────────────────────────────

def test_load_opt_out_valid(tmp_path):
    """Loads opt-out list ignoring comments and blank lines."""
    path = _write_file(str(tmp_path / "opt.txt"),
        "# Some comment\n"
        "A@EXAMPLE.COM\n"
        "\n"
        "b@example.com  \n"
    )
    opts = load_opt_out_list(path)
    assert opts == {"a@example.com", "b@example.com"}

def test_load_opt_out_missing():
    """Missing opt-out file returns empty set."""
    opts = load_opt_out_list("does_not_exist.txt")
    assert opts == set()

def test_filter_opt_outs(capsys):
    """Contacts in the opt-out list are removed case-insensitively."""
    contacts = [
        ContactRecord("a@example.com", "A", "R", "N", "B"),
        ContactRecord("KEEP@example.com", "A", "R", "N", "B"),
        ContactRecord("C@EXAMPLE.COM", "A", "R", "N", "B"),
    ]
    opts = {"a@example.com", "c@example.com"}
    
    filtered = filter_opt_outs(contacts, opts)
    
    assert len(filtered) == 1
    assert filtered[0].recipient_email == "KEEP@example.com"
    
    stdout = capsys.readouterr().out
    assert "Skipping a@example.com" in stdout
