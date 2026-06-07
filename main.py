"""
main.py — The Closer: Cold Email Writer + Send Bot

Orchestrates the full pipeline:
    1. Load configuration
    2. Load and validate contacts
    3. Generate personalized emails
    4. Preview and get user confirmation
    5. Send or draft emails
    6. Log results
"""

import sys
from datetime import datetime
from typing import Dict

from core.config import load_config
from core.models import AppConfig, GeneratedEmail, OutreachStatus, UserDecision, LogEntry
from core.exceptions import ConfigError, DeliveryError

from data.data_loader import load_contacts, load_opt_out_list, filter_opt_outs
from generator.email_generator import generate_email
from preview.previewer import preview_and_confirm
from sender.email_sender import send_email
from sender.logger import log_outreach, make_log_entry


def print_banner(config: AppConfig, count: int) -> None:
    mode_text = "DRY RUN (no emails sent)" if config.dry_run else "LIVE MODE (emails will be sent!)"
    print(
        "╔══════════════════════════════════════════╗\n"
        "║         🎯 THE CLOSER v1.0              ║\n"
        "║      Cold Email Writer + Send Bot       ║\n"
        "╠══════════════════════════════════════════╣\n"
        f"║  Mode:     {mode_text:<25}║\n"
        f"║  Contacts: {count:<25}║\n"
        f"║  Log file: {config.log_file:<25}║\n"
        "╚══════════════════════════════════════════╝"
    )


def print_summary(stats: Dict[str, int], log_file: str) -> None:
    print(
        "\n══════════════════════════════════════════════\n"
        "  📊 OUTREACH SUMMARY\n"
        "──────────────────────────────────────────────\n"
        f"  📤 Sent:     {stats.get('sent', 0)}\n"
        f"  📝 Drafted:  {stats.get('drafted', 0)}\n"
        f"  ⏭️  Skipped:  {stats.get('skipped', 0)}\n"
        f"  ❌ Failed:   {stats.get('failed', 0)}\n"
        "──────────────────────────────────────────────\n"
        f"  📄 Full log: {log_file}\n"
        "══════════════════════════════════════════════\n"
    )


def main() -> None:
    """The Closer — Cold Email Writer + Send Bot."""
    
    # ── Step 1: Load Config ──
    try:
        config = load_config()
    except ConfigError as e:
        print(f"❌ Configuration error: {e}")
        sys.exit(1)
    
    # ── Step 2: Load Contacts ──
    try:
        contacts = load_contacts(config.input_file)
        opt_outs = load_opt_out_list()
        contacts = filter_opt_outs(contacts, opt_outs)
    except (FileNotFoundError, ValueError) as e:
        print(f"❌ Data error: {e}")
        sys.exit(1)
    
    if not contacts:
        print("No contacts to process. Exiting.")
        sys.exit(0)
        
    MAX_CONTACTS = 10
    if len(contacts) > MAX_CONTACTS:
        print(f"\n⚠️ Volume cap reached ({MAX_CONTACTS}). Remaining {len(contacts) - MAX_CONTACTS} contacts skipped.")
        contacts = contacts[:MAX_CONTACTS]
    
    # ── Step 3: Print Banner ──
    print_banner(config, len(contacts))
    
    # ── Step 4: Pipeline Loop ──
    stats = {"sent": 0, "drafted": 0, "skipped": 0, "failed": 0}
    
    try:
        for i, contact in enumerate(contacts, 1):
            print(f"\n[{i}/{len(contacts)}] Processing: {contact.company} — {contact.role}")
            
            # Generate email
            email = generate_email(contact, config)
            
            # Preview and get confirmation
            decision = preview_and_confirm(email, current=i, total=len(contacts))
            
            if decision == UserDecision.QUIT:
                # Log this as skipped
                log_outreach(make_log_entry(email, OutreachStatus.SKIPPED), config.log_file)
                stats["skipped"] += 1
                print("\n👋 Quitting. Remaining contacts skipped.")
                break
            
            if decision == UserDecision.SKIP:
                log_outreach(make_log_entry(email, OutreachStatus.SKIPPED), config.log_file)
                stats["skipped"] += 1
                continue
            
            # Send / Draft
            try:
                result = send_email(email, config)
                log_outreach(make_log_entry(email, result.status, result.error_message), config.log_file)
                stats[result.status.value] += 1
                
                if result.success:
                    status_icon = "📤" if result.status == OutreachStatus.SENT else "📝"
                    print(f"  {status_icon} {result.status.value.upper()}")
                else:
                    print(f"  ❌ Failed: {result.error_message}")
            
            except DeliveryError as e:
                print(f"\n🚨 Fatal delivery error: {e}")
                print("Aborting pipeline — please check your SMTP credentials.")
                break
    except KeyboardInterrupt:
        print("\n👋 Operation cancelled by user. Remaining contacts skipped.")
    finally:
        # ── Step 5: Summary ──
        print_summary(stats, config.log_file)


if __name__ == "__main__":
    main()
