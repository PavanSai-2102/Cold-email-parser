# 🎯 The Closer — Cold Email Writer + Send Bot

A CLI tool that helps job seekers generate and send personalized cold outreach emails. Built with safety-first design: dry-run by default, human review required, and full audit logging.

## Features

- **Personalized email generation** from templates (or Groq LLM)
- **Human review** — preview every email before sending
- **Dry-run mode** — enabled by default for safe testing
- **Multi-source contacts** — load from JSON, CSV, or hardcoded data
- **Audit logging** — every action logged to `outreach_log.csv`
- **Opt-out support** — respect recipients who ask not to be contacted

## Quick Start

### 1. Clone & Setup

```bash
cd the-closer
python3 -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure

```bash
cp .env.example .env
# Edit .env with your SMTP credentials
```

**Gmail users:** You need an [App Password](https://myaccount.google.com/apppasswords) (requires 2-Step Verification enabled).

### 3. Add Contacts

Edit `contacts.json` with your outreach targets. Each contact needs:
- `recipient_email` (required)
- `company` (required)
- `role` (required)
- `candidate_name` (required)
- `candidate_background` (required)

### 4. Run

```bash
# Dry-run mode (default — no emails actually sent)
python main.py

# Live mode (edit .env: DRY_RUN=false)
python main.py
```

## Project Structure

```
the-closer/
├── main.py              # Pipeline orchestrator
├── core/
│   ├── config.py        # Configuration loader + validator
│   ├── models.py        # Shared data classes and enums
│   └── exceptions.py    # Custom exception hierarchy
├── data/
│   ├── data_loader.py   # Contact ingestion + validation
│   ├── contacts.json    # Sample contact data
│   └── opt_out.txt      # Opt-out list
├── generator/
│   └── email_generator.py # Email composition (Phase 3)
├── preview/
│   └── previewer.py     # Terminal preview (Phase 4)
├── sender/
│   ├── email_sender.py  # Email delivery (Phase 5)
│   └── logger.py        # CSV audit logger (Phase 5)
├── .env.example         # Environment variable template
├── requirements.txt     # Python dependencies
├── tests/               # Unit tests
└── docs/                # Documentation
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SMTP_HOST` | `smtp.gmail.com` | SMTP server |
| `SMTP_PORT` | `587` | SMTP port |
| `SMTP_USER` | — | Your email address |
| `SMTP_PASSWORD` | — | App password |
| `SENDER_NAME` | `SMTP_USER` | Display name |
| `DRY_RUN` | `true` | Simulate sending |
| `SEND_MODE` | `smtp` | `smtp` / `gmail_api` / `sendgrid` / `resend` |
| `INPUT_FILE` | `contacts.json` | Contact data source |
| `LOG_FILE` | `outreach_log.csv` | Audit log path |
| `LLM_ENABLED` | `false` | Use Groq for rewriting |
| `LLM_API_KEY` | — | Groq API key |
| `LLM_MODEL` | `llama-3.3-70b-versatile` | Groq model |

## Sending Method

This project uses **SMTP via `smtplib`** (Python standard library) for email delivery. For Gmail, use an App Password with TLS on port 587.

## Safety Guardrails

1. ✅ **Dry-run by default** — `DRY_RUN=true`
2. ✅ **Human review required** — every email previewed before send
3. ✅ **Volume cap** — max 10 emails per run
4. ✅ **Opt-out support** — respects `opt_out.txt`
5. ✅ **Full audit trail** — every attempt logged to CSV

## License

MIT
