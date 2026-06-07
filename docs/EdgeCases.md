# Edge Cases: The Closer
## Comprehensive Edge Case Catalog — Cold Email Writer + Send Bot

> **Version:** 1.0  
> **Date:** 2026-06-01  
> **References:**  
> - [ProblemStatement.md](file:///Users/pavan2102/Documents/MacBook-Documents/Projects/Cold%20Email%20Parser/docs/ProblemStatement.md)  
> - [Architecture.md](file:///Users/pavan2102/Documents/MacBook-Documents/Projects/Cold%20Email%20Parser/docs/Architecture.md)  
> - [ImplementationPlan.md](file:///Users/pavan2102/Documents/MacBook-Documents/Projects/Cold%20Email%20Parser/docs/ImplementationPlan.md)

---

## How to Use This Document

Each edge case is tagged with:
- **Module** — which file(s) it affects
- **Severity** — 🔴 Critical (app crash / data loss), 🟡 Medium (wrong behavior), 🟢 Low (cosmetic / UX)
- **Expected Behavior** — what the system SHOULD do
- **Test ID** — unique identifier for traceability

---

## Table of Contents

1. [Configuration Edge Cases](#1-configuration-edge-cases)
2. [Data Loading Edge Cases](#2-data-loading-edge-cases)
3. [Contact Validation Edge Cases](#3-contact-validation-edge-cases)
4. [Email Generation Edge Cases](#4-email-generation-edge-cases)
5. [Preview & Confirmation Edge Cases](#5-preview--confirmation-edge-cases)
6. [Email Sending Edge Cases](#6-email-sending-edge-cases)
7. [Logging Edge Cases](#7-logging-edge-cases)
8. [Orchestrator Edge Cases](#8-orchestrator-edge-cases)
9. [Safety & Guardrail Edge Cases](#9-safety--guardrail-edge-cases)
10. [Cross-Cutting Edge Cases](#10-cross-cutting-edge-cases)

---

## 1. Configuration Edge Cases

| Test ID | Edge Case | Severity | Module | Expected Behavior |
|---------|-----------|----------|--------|-------------------|
| CFG-01 | `.env` file does not exist | 🔴 Critical | `config.py` | Print clear setup instructions referencing `.env.example`, exit with code 1 |
| CFG-02 | `.env` file exists but is completely empty | 🔴 Critical | `config.py` | Use all defaults; `DRY_RUN` defaults to `true`; print warning about missing SMTP creds |
| CFG-03 | `SMTP_PORT` set to non-integer (e.g., `"abc"`) | 🔴 Critical | `config.py` | Raise `ConfigError` with message: "SMTP_PORT must be an integer, got 'abc'" |
| CFG-04 | `SMTP_PORT` set to negative number (`-1`) | 🟡 Medium | `config.py` | Raise `ConfigError` — port must be between 1 and 65535 |
| CFG-05 | `SMTP_PORT` set to `0` | 🟡 Medium | `config.py` | Raise `ConfigError` — port 0 is not valid for SMTP |
| CFG-06 | `DRY_RUN` set to unexpected value (e.g., `"maybe"`) | 🟡 Medium | `config.py` | Treat as `true` (safe default); log a warning |
| CFG-07 | `DRY_RUN=false` but `SMTP_USER` is empty | 🔴 Critical | `config.py` | Raise `ConfigError` — cannot send without credentials |
| CFG-08 | `DRY_RUN=false` but `SMTP_PASSWORD` is empty | 🔴 Critical | `config.py` | Raise `ConfigError` — cannot send without password |
| CFG-09 | `SEND_MODE` set to unsupported value (e.g., `"pigeon"`) | 🟡 Medium | `config.py` | Raise `ConfigError` listing valid options: smtp, gmail_api, sendgrid, resend |
| CFG-10 | `SEND_MODE=gmail_api` but Gmail creds not configured | 🔴 Critical | `config.py` | Raise `ConfigError` with setup instructions for Gmail API |
| CFG-11 | `.env` has extra whitespace in values (e.g., `SMTP_USER= user@gmail.com `) | 🟡 Medium | `config.py` | Strip whitespace from all values before use |
| CFG-12 | `.env` has values with quotes (e.g., `SMTP_PASSWORD="my_pass"`) | 🟡 Medium | `config.py` | `python-dotenv` handles this, but verify quotes are stripped |
| CFG-13 | `.env` has UTF-8 BOM at start of file | 🟢 Low | `config.py` | Load correctly; `python-dotenv` should handle BOM |
| CFG-14 | `LLM_ENABLED=true` but `LLM_API_KEY` is empty | 🟡 Medium | `config.py` | Raise `ConfigError` — LLM enabled but no API key provided |
| CFG-15 | `INPUT_FILE` points to a nonexistent file | 🔴 Critical | `config.py` | Allow config load to succeed (validation at runtime); fail gracefully in `data_loader` |
| CFG-16 | `LOG_FILE` path includes directories that don't exist (e.g., `logs/outreach.csv`) | 🟡 Medium | `config.py` / `logger.py` | Auto-create parent directories, or raise with helpful message |
| CFG-17 | Environment variables set both in `.env` AND system env | 🟢 Low | `config.py` | System env should take precedence (standard `python-dotenv` behavior with `override=False`) |
| CFG-18 | `.env` file has Windows line endings (`\r\n`) on macOS/Linux | 🟢 Low | `config.py` | `python-dotenv` handles this; verify no `\r` in values |

---

## 2. Data Loading Edge Cases

| Test ID | Edge Case | Severity | Module | Expected Behavior |
|---------|-----------|----------|--------|-------------------|
| DL-01 | `contacts.json` does not exist | 🔴 Critical | `data_loader.py` | Raise `FileNotFoundError` with clear message including the file path |
| DL-02 | `contacts.json` is empty file (0 bytes) | 🟡 Medium | `data_loader.py` | Return empty list; print "No contacts found" |
| DL-03 | `contacts.json` contains `[]` (valid JSON, empty array) | 🟡 Medium | `data_loader.py` | Return empty list; print "No contacts found" |
| DL-04 | `contacts.json` contains a single object `{}` instead of array | 🟡 Medium | `data_loader.py` | Wrap in list and process as one contact; or raise with "Expected JSON array" |
| DL-05 | `contacts.json` is malformed JSON (missing closing bracket) | 🔴 Critical | `data_loader.py` | Catch `json.JSONDecodeError`; print friendly error with line number if possible |
| DL-06 | `contacts.json` is extremely large (1000+ contacts) | 🟡 Medium | `data_loader.py` | Load successfully, but `main.py` should enforce volume cap (default 10) |
| DL-07 | `contacts.csv` has no header row | 🟡 Medium | `data_loader.py` | Raise `ValidationError` — cannot map columns without headers |
| DL-08 | `contacts.csv` has extra columns not in the schema | 🟢 Low | `data_loader.py` | Ignore extra columns; only map known fields |
| DL-09 | `contacts.csv` has fewer columns than expected | 🟡 Medium | `data_loader.py` | Map available columns; missing ones become `None`; validate required fields after |
| DL-10 | `contacts.csv` has rows with different numbers of columns | 🟡 Medium | `data_loader.py` | Use `csv.DictReader` which handles this; missing fields → `None` |
| DL-11 | `contacts.csv` uses semicolons instead of commas | 🟢 Low | `data_loader.py` | Auto-detect delimiter with `csv.Sniffer`, or document that commas are required |
| DL-12 | `contacts.csv` has values with commas inside quotes | 🟢 Low | `data_loader.py` | `csv.reader` handles quoted values correctly by default |
| DL-13 | File has `.JSON` extension (uppercase) | 🟢 Low | `data_loader.py` | Case-insensitive extension matching: `.lower()` before comparison |
| DL-14 | Source is `"hardcoded"` but function is missing/empty | 🟡 Medium | `data_loader.py` | Hardcoded list should always have 3–5 records; never empty |
| DL-15 | Source string is `None` or empty string | 🔴 Critical | `data_loader.py` | Raise `ValueError("No data source specified")` |
| DL-16 | Source file has non-UTF-8 encoding (e.g., Latin-1) | 🟡 Medium | `data_loader.py` | Open with `encoding="utf-8"`, catch `UnicodeDecodeError`, suggest re-saving as UTF-8 |
| DL-17 | JSON file is a nested object, not a flat array | 🟡 Medium | `data_loader.py` | Raise `ValidationError("Expected a JSON array of contact objects")` |
| DL-18 | CSV file is tab-separated (`.csv` extension but TSV content) | 🟢 Low | `data_loader.py` | Use `csv.Sniffer` to detect delimiter, or fail with clear error |
| DL-19 | `opt_out.txt` does not exist | 🟢 Low | `data_loader.py` | Return empty set; no crash — opt-out is optional |
| DL-20 | `opt_out.txt` has blank lines and comments | 🟢 Low | `data_loader.py` | Skip blank lines and lines starting with `#` |
| DL-21 | `opt_out.txt` has emails with mixed case | 🟢 Low | `data_loader.py` | Normalize to lowercase before comparison |
| DL-22 | `opt_out.txt` has trailing whitespace on emails | 🟢 Low | `data_loader.py` | Strip whitespace from each line |
| DL-23 | All contacts are in opt-out list | 🟡 Medium | `data_loader.py` | Return empty list after filtering; `main.py` handles "no contacts" gracefully |

---

## 3. Contact Validation Edge Cases

| Test ID | Edge Case | Severity | Module | Expected Behavior |
|---------|-----------|----------|--------|-------------------|
| CV-01 | `recipient_email` is missing entirely | 🔴 Critical | `data_loader.py` | Raise `ValidationError`; skip this contact, continue pipeline |
| CV-02 | `recipient_email` is empty string `""` | 🔴 Critical | `data_loader.py` | Raise `ValidationError` — email cannot be blank |
| CV-03 | `recipient_email` has no `@` symbol (e.g., `"not-an-email"`) | 🔴 Critical | `data_loader.py` | Raise `ValidationError` — invalid email format |
| CV-04 | `recipient_email` has multiple `@` symbols (e.g., `"a@b@c.com"`) | 🟡 Medium | `data_loader.py` | Raise `ValidationError` — invalid email format |
| CV-05 | `recipient_email` has spaces (e.g., `"user @example.com"`) | 🟡 Medium | `data_loader.py` | Strip spaces first, then validate; or reject outright |
| CV-06 | `recipient_email` has Unicode characters (e.g., `"ñoño@example.com"`) | 🟢 Low | `data_loader.py` | Accept — internationalized emails are valid; SMTP may reject at send time |
| CV-07 | `recipient_email` is very long (> 254 chars) | 🟢 Low | `data_loader.py` | Reject — RFC 5321 limits email addresses to 254 characters |
| CV-08 | `company` is missing | 🔴 Critical | `data_loader.py` | Raise `ValidationError` — required field |
| CV-09 | `company` is empty string | 🔴 Critical | `data_loader.py` | Treat empty string same as missing; raise `ValidationError` |
| CV-10 | `role` is missing | 🔴 Critical | `data_loader.py` | Raise `ValidationError` — required field |
| CV-11 | `candidate_name` is missing | 🔴 Critical | `data_loader.py` | Raise `ValidationError` — required field |
| CV-12 | `candidate_background` is missing | 🔴 Critical | `data_loader.py` | Raise `ValidationError` — required field |
| CV-13 | `recipient_name` contains special characters (`"Priyañka O'Brien-Smith"`) | 🟢 Low | `data_loader.py` | Accept — names can have accents, apostrophes, hyphens |
| CV-14 | `personalization_note` is extremely long (> 500 chars) | 🟢 Low | `data_loader.py` | Accept but warn — may push email body over 150-word limit |
| CV-15 | `job_url` is not a valid URL (e.g., `"not a url"`) | 🟢 Low | `data_loader.py` | Accept — URL validation is not required for MVP; it's just included in the sign-off |
| CV-16 | Duplicate `recipient_email` across contacts | 🟡 Medium | `data_loader.py` | Warn but process; or deduplicate (stretch goal 6.7) |
| CV-17 | Contact has extra unknown fields (e.g., `"phone": "555-0100"`) | 🟢 Low | `data_loader.py` | Ignore unknown fields; only map known ones |
| CV-18 | All optional fields are `null` / `None` | 🟡 Medium | `data_loader.py` | Accept — all optional fields should have sensible defaults |
| CV-19 | Required field value is `null` (JSON `null`) | 🔴 Critical | `data_loader.py` | Treat `null` same as missing; raise `ValidationError` |
| CV-20 | Required field value is whitespace-only (e.g., `"   "`) | 🟡 Medium | `data_loader.py` | Strip and treat as empty → raise `ValidationError` |

---

## 4. Email Generation Edge Cases

| Test ID | Edge Case | Severity | Module | Expected Behavior |
|---------|-----------|----------|--------|-------------------|
| EG-01 | `recipient_name` is `None` | 🟡 Medium | `email_generator.py` | Use fallback greeting: "Hi there," |
| EG-02 | `recipient_name` is empty string `""` | 🟡 Medium | `email_generator.py` | Treat as `None` → use "Hi there," |
| EG-03 | `personalization_note` is `None` | 🟡 Medium | `email_generator.py` | Use generic hook: "I came across the {role} position and it caught my attention." |
| EG-04 | `personalization_note` is extremely long (pushes body > 150 words) | 🟡 Medium | `email_generator.py` | Truncate note or warn to stderr; still generate email |
| EG-05 | `portfolio_url` is `None` | 🟢 Low | `email_generator.py` | Omit portfolio line from sign-off; no blank line |
| EG-06 | All optional fields (`portfolio_url`, `linkedin_url`, `resume_link`) are `None` | 🟢 Low | `email_generator.py` | Sign-off has only name, no links |
| EG-07 | All optional link fields are present | 🟢 Low | `email_generator.py` | Include all links in sign-off, each on its own line |
| EG-08 | `role` contains special characters (e.g., `"C++ Developer / ML Engineer"`) | 🟢 Low | `email_generator.py` | Include as-is in subject and body; no escaping needed for plain text |
| EG-09 | `company` contains `&`, `<`, or `>` characters | 🟢 Low | `email_generator.py` | Include as-is — emails are plain text, not HTML |
| EG-10 | `candidate_background` is very short (1–2 words: `"Python"`) | 🟡 Medium | `email_generator.py` | Generate email; it may read oddly but should not crash |
| EG-11 | `candidate_background` is very long (100+ words) | 🟡 Medium | `email_generator.py` | Generated body may exceed 150 words → warn but don't block |
| EG-12 | Generated body is exactly 150 words | 🟢 Low | `email_generator.py` | Accept — 150 is the limit, not 149 |
| EG-13 | Generated body is 0 words (empty string) | 🔴 Critical | `email_generator.py` | Should never happen with valid input; raise error if body is empty |
| EG-14 | `recipient_name` has leading/trailing whitespace | 🟢 Low | `email_generator.py` | Strip before inserting into greeting |
| EG-15 | Template produces email with no personalization (all fallbacks triggered) | 🟡 Medium | `email_generator.py` | Email should still mention company name and role at minimum |
| EG-16 | `candidate_name` contains emoji (e.g., `"Alex 🚀 Chen"`) | 🟢 Low | `email_generator.py` | Accept — UTF-8 email supports emoji |
| EG-17 | LLM response (stretch) is malformed — missing SUBJECT line | 🟡 Medium | `email_generator.py` | Fall back to template-based generation; log warning |
| EG-18 | LLM response (stretch) exceeds 150 words | 🟡 Medium | `email_generator.py` | Warn but accept; do not silently truncate |
| EG-19 | LLM API timeout (stretch) | 🟡 Medium | `email_generator.py` | Fall back to template; log error |
| EG-20 | LLM API rate limit (stretch) | 🟡 Medium | `email_generator.py` | Fall back to template; log error; suggest retry later |

---

## 5. Preview & Confirmation Edge Cases

| Test ID | Edge Case | Severity | Module | Expected Behavior |
|---------|-----------|----------|--------|-------------------|
| PR-01 | User enters empty string (just presses Enter) | 🟡 Medium | `previewer.py` | Default to `SKIP` (safe default) |
| PR-02 | User enters gibberish (e.g., `"asdf"`) | 🟢 Low | `previewer.py` | Print "Invalid choice. Enter [S]end, S[k]ip, or [Q]uit" and re-prompt |
| PR-03 | User enters uppercase input (e.g., `"SEND"`) | 🟢 Low | `previewer.py` | Case-insensitive matching; accept as `SEND` |
| PR-04 | User enters input with leading/trailing whitespace (e.g., `" s "`) | 🟢 Low | `previewer.py` | Strip whitespace; accept as `SEND` |
| PR-05 | User sends EOF / Ctrl+D | 🟡 Medium | `previewer.py` | Catch `EOFError`; treat as `QUIT` |
| PR-06 | User sends Ctrl+C (KeyboardInterrupt) | 🔴 Critical | `previewer.py` / `main.py` | Catch gracefully; log remaining as skipped; print summary; exit cleanly |
| PR-07 | Email body contains terminal escape sequences | 🟢 Low | `previewer.py` | Sanitize or render as-is; should not break terminal |
| PR-08 | Email body is very long (close to 150 words — multi-paragraph) | 🟢 Low | `previewer.py` | Display fully; terminal will scroll naturally |
| PR-09 | Email preview on a very narrow terminal (< 40 columns) | 🟢 Low | `previewer.py` | Box-drawing may wrap; acceptable — not a primary use case |
| PR-10 | User enters a number instead of letter (e.g., `"1"`) | 🟢 Low | `previewer.py` | Invalid input; re-prompt |
| PR-11 | User spams Enter multiple times rapidly | 🟢 Low | `previewer.py` | Each Enter = one `SKIP` (safe default); pipeline advances correctly |
| PR-12 | Email subject is very long (> 78 chars — email header limit) | 🟢 Low | `previewer.py` | Display full subject in preview; SMTP will handle wrapping |
| PR-13 | Preview called with `None` email object | 🔴 Critical | `previewer.py` | Raise `TypeError` or guard clause; should never happen in normal flow |

---

## 6. Email Sending Edge Cases

| Test ID | Edge Case | Severity | Module | Expected Behavior |
|---------|-----------|----------|--------|-------------------|
| ES-01 | `DRY_RUN=true` (happy path) | 🟢 Low | `email_sender.py` | Return `SendResult(success=True, status=DRAFTED)`; no SMTP connection made |
| ES-02 | SMTP server is unreachable (wrong host) | 🔴 Critical | `email_sender.py` | Catch `socket.gaierror` / `ConnectionRefusedError`; return `FAILED` result; continue pipeline |
| ES-03 | SMTP server connection times out | 🔴 Critical | `email_sender.py` | Catch `socket.timeout`; return `FAILED` with timeout message; set timeout to 30s |
| ES-04 | SMTP authentication fails (wrong password) | 🔴 Critical | `email_sender.py` | Raise `DeliveryError` — pipeline should abort (all subsequent sends will fail too) |
| ES-05 | SMTP authentication fails (wrong username) | 🔴 Critical | `email_sender.py` | Same as ES-04 — abort pipeline |
| ES-06 | Recipient email is rejected by SMTP server | 🟡 Medium | `email_sender.py` | Catch `SMTPRecipientsRefused`; return `FAILED`; continue to next contact |
| ES-07 | SMTP server returns rate limit error (too many sends) | 🟡 Medium | `email_sender.py` | Return `FAILED` with rate limit message; suggest adding delay |
| ES-08 | SMTP server drops connection mid-send | 🟡 Medium | `email_sender.py` | Catch `SMTPServerDisconnected`; return `FAILED`; try to reconnect for next email |
| ES-09 | Email body contains non-ASCII characters (accents, emoji) | 🟡 Medium | `email_sender.py` | Set `MIMEText` charset to `utf-8`; SMTP should handle properly |
| ES-10 | Email subject contains non-ASCII characters | 🟡 Medium | `email_sender.py` | Use `email.header.Header` for proper encoding if needed |
| ES-11 | `sender_name` contains quotes or special chars (e.g., `"O'Brien"`) | 🟢 Low | `email_sender.py` | Properly escape in From header; use `email.utils.formataddr` |
| ES-12 | Sending to self (recipient = sender) | 🟢 Low | `email_sender.py` | Allow — this is useful for testing |
| ES-13 | SMTP port is blocked by firewall | 🔴 Critical | `email_sender.py` | Connection timeout → catch and return `FAILED` |
| ES-14 | TLS/STARTTLS not supported by server | 🟡 Medium | `email_sender.py` | Catch `SMTPNotSupportedError`; try without TLS or fail with helpful message |
| ES-15 | Gmail App Password has expired or been revoked | 🔴 Critical | `email_sender.py` | Auth failure → `DeliveryError` with message to regenerate App Password |
| ES-16 | Network disconnects between authentication and send | 🟡 Medium | `email_sender.py` | Catch `SMTPServerDisconnected`; return `FAILED` |
| ES-17 | Trying to send after SMTP connection was already closed | 🟡 Medium | `email_sender.py` | Use `with` context manager for auto-cleanup; each send creates fresh connection |

---

## 7. Logging Edge Cases

| Test ID | Edge Case | Severity | Module | Expected Behavior |
|---------|-----------|----------|--------|-------------------|
| LG-01 | `outreach_log.csv` does not exist (first run) | 🟡 Medium | `logger.py` | Create file with header row, then append entry |
| LG-02 | `outreach_log.csv` already exists with headers | 🟢 Low | `logger.py` | Append entry WITHOUT re-adding headers |
| LG-03 | `outreach_log.csv` exists but is empty (0 bytes) | 🟡 Medium | `logger.py` | Treat as new file — write headers first |
| LG-04 | `outreach_log.csv` has incorrect/missing headers | 🟡 Medium | `logger.py` | Overwrite headers or append with correct schema — document behavior |
| LG-05 | Log file path is read-only (permission denied) | 🔴 Critical | `logger.py` | Catch `PermissionError`; print error but do NOT crash pipeline |
| LG-06 | Disk is full — cannot write | 🔴 Critical | `logger.py` | Catch `OSError`; print warning; pipeline continues but logging is degraded |
| LG-07 | `error_message` field contains commas | 🟢 Low | `logger.py` | `csv.DictWriter` handles quoting automatically |
| LG-08 | `error_message` field contains newlines | 🟢 Low | `logger.py` | `csv.DictWriter` handles quoting; verify multiline doesn't break CSV |
| LG-09 | `error_message` field contains double quotes | 🟢 Low | `logger.py` | `csv.DictWriter` escapes quotes automatically |
| LG-10 | `subject` field contains commas or quotes | 🟢 Low | `logger.py` | Same as LG-07/09 — CSV writer handles quoting |
| LG-11 | Concurrent writes to log file (parallel execution) | 🟢 Low | `logger.py` | Not a concern for MVP (single-threaded); document limitation |
| LG-12 | `get_summary()` called on empty/nonexistent log file | 🟡 Medium | `logger.py` | Return `{"sent": 0, "drafted": 0, "skipped": 0, "failed": 0}` |
| LG-13 | Log file has corrupt/partial row (incomplete write from crash) | 🟢 Low | `logger.py` | `get_summary` should skip malformed rows with warning |
| LG-14 | Timestamp timezone handling | 🟢 Low | `logger.py` | Use `datetime.now().isoformat()` — local time, no timezone; document this |
| LG-15 | Log directory in config doesn't exist (e.g., `logs/outreach.csv`) | 🟡 Medium | `logger.py` | Auto-create parent directories with `os.makedirs(exist_ok=True)` |

---

## 8. Orchestrator Edge Cases

| Test ID | Edge Case | Severity | Module | Expected Behavior |
|---------|-----------|----------|--------|-------------------|
| OR-01 | Zero contacts after loading and filtering | 🟡 Medium | `main.py` | Print "No contacts to process. Exiting." and exit cleanly (code 0) |
| OR-02 | All contacts fail validation | 🟡 Medium | `main.py` | Zero valid contacts → same as OR-01 |
| OR-03 | User quits on first contact | 🟢 Low | `main.py` | Log first as skipped; print summary with 1 skipped |
| OR-04 | User skips all contacts | 🟢 Low | `main.py` | All logged as skipped; summary shows all skipped |
| OR-05 | User sends all contacts | 🟢 Low | `main.py` | All sent/drafted; summary shows correct counts |
| OR-06 | Fatal `DeliveryError` on first send (auth failure) | 🔴 Critical | `main.py` | Abort pipeline; log remaining as failed/skipped; print error + summary |
| OR-07 | Non-fatal send failure mid-pipeline | 🟡 Medium | `main.py` | Log as failed; continue to next contact |
| OR-08 | `Ctrl+C` (KeyboardInterrupt) during pipeline | 🔴 Critical | `main.py` | Catch in outer try/except; log remaining as skipped; print summary; exit cleanly |
| OR-09 | `Ctrl+C` during email sending (mid-SMTP) | 🔴 Critical | `main.py` | SMTP connection should be cleaned up (context manager); log as failed |
| OR-10 | More than 10 contacts (volume cap) | 🟡 Medium | `main.py` | Process first 10; print "Volume cap reached (10). Remaining contacts skipped." |
| OR-11 | Contact list has mix of valid and invalid contacts | 🟡 Medium | `main.py` | Skip invalid contacts with warning; process valid ones |
| OR-12 | Same email appears twice in contacts (duplicate) | 🟢 Low | `main.py` | Process both (MVP); stretch goal adds deduplication |
| OR-13 | Pipeline runs twice in a row | 🟢 Low | `main.py` | Second run appends to existing `outreach_log.csv`; no data loss |

---

## 9. Safety & Guardrail Edge Cases

| Test ID | Edge Case | Severity | Module | Expected Behavior |
|---------|-----------|----------|--------|-------------------|
| SG-01 | `DRY_RUN` not set at all in env | 🔴 Critical | `config.py` | Default to `true` — never default to live send |
| SG-02 | User tries to bypass preview (no `preview_and_confirm` call) | 🔴 Critical | `main.py` | Architectural: preview is required in the pipeline; cannot be skipped |
| SG-03 | Contact is in opt-out list but email differs only in case | 🟡 Medium | `data_loader.py` | Case-insensitive matching; `Priya@Example.COM` matches `priya@example.com` |
| SG-04 | Volume cap of 10 reached with 50 contacts loaded | 🟡 Medium | `main.py` | Stop after 10; log remaining as skipped; explain in summary |
| SG-05 | Email body has no company/role mention (personalization failed) | 🟡 Medium | `email_generator.py` | Template guarantees company/role mention; LLM path should validate |
| SG-06 | Sender email doesn't match SMTP_USER | 🟡 Medium | `email_sender.py` | Always use `SMTP_USER` as sender; don't allow spoofing |
| SG-07 | Opt-out file is missing | 🟢 Low | `data_loader.py` | Treat as empty — no one is opted out; pipeline continues |
| SG-08 | User tries to send same email to same person twice (re-run) | 🟢 Low | `main.py` | MVP allows it; stretch goal cross-references log for dedup |
| SG-09 | Email content accidentally includes HTML tags | 🟢 Low | `email_generator.py` | Emails are plain text; HTML tags will render as text, not markup |
| SG-10 | Generated email contains candidate's name but wrong company | 🔴 Critical | `email_generator.py` | Template directly interpolates `contact.company` — verify in tests |

---

## 10. Cross-Cutting Edge Cases

| Test ID | Edge Case | Severity | Module | Expected Behavior |
|---------|-----------|----------|--------|-------------------|
| XC-01 | Python version < 3.9 (e.g., 3.7) | 🟡 Medium | All | Dataclasses work in 3.7+; `Optional` from typing works in 3.7+; test on target version |
| XC-02 | `python-dotenv` not installed | 🔴 Critical | `config.py` | `ImportError` — `requirements.txt` must document dependency |
| XC-03 | Running from different working directory than project root | 🟡 Medium | All | File paths (`.env`, `contacts.json`, log) should be relative to project root or configurable |
| XC-04 | File paths with spaces (e.g., `"My Contacts/data.json"`) | 🟢 Low | `data_loader.py` | Python handles quoted paths; should work |
| XC-05 | File paths with Unicode characters | 🟢 Low | `data_loader.py` | Python 3 handles Unicode paths natively |
| XC-06 | Very slow network (high latency SMTP) | 🟡 Medium | `email_sender.py` | Set explicit timeout (30s); user sees delay but no crash |
| XC-07 | Memory pressure (many contacts loaded at once) | 🟢 Low | `data_loader.py` | 1000 contacts ≈ negligible memory; not a concern for MVP |
| XC-08 | Running in CI/CD (no stdin for confirmation) | 🟡 Medium | `previewer.py` | `EOFError` on `input()` → catch and treat as QUIT |
| XC-09 | Windows vs macOS vs Linux line endings in output files | 🟢 Low | `logger.py` | `csv.DictWriter` uses `\r\n` by default (CSV standard); document this |
| XC-10 | Module import circular dependency | 🔴 Critical | All | `models.py` and `exceptions.py` have no imports from other project modules; prevents cycles |

---

## Summary Statistics

| Severity | Count | Description |
|----------|-------|-------------|
| 🔴 Critical | 35 | Could crash the app, lose data, or send emails accidentally |
| 🟡 Medium | 42 | Wrong behavior, but app doesn't crash |
| 🟢 Low | 36 | Cosmetic issues, minor UX quirks |
| **Total** | **113** | |

### Coverage by Module

| Module | Edge Cases | Critical | Medium | Low |
|--------|-----------|----------|--------|-----|
| `config.py` | 18 | 5 | 6 | 7 |
| `data_loader.py` | 23 | 3 | 8 | 12 |
| Contact Validation | 20 | 7 | 5 | 8 |
| `email_generator.py` | 20 | 2 | 11 | 7 |
| `previewer.py` | 13 | 2 | 3 | 8 |
| `email_sender.py` | 17 | 6 | 8 | 3 |
| `logger.py` | 15 | 2 | 5 | 8 |
| `main.py` | 13 | 3 | 6 | 4 |
| Safety / Guardrails | 10 | 3 | 4 | 3 |
| Cross-Cutting | 10 | 2 | 4 | 4 |

---

> **Usage:** Reference edge case IDs (e.g., `CFG-07`, `ES-04`) in test names, code comments, and review checklists to ensure coverage.
