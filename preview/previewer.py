"""
previewer.py — Terminal Preview & Human-in-the-Loop Confirmation

Displays generated emails in the terminal with a polished UI,
enforcing a mandatory human review before anything is sent.
"""

import sys
from typing import Optional

from core.models import GeneratedEmail, UserDecision


def _format_preview(email: GeneratedEmail, current: int = 1, total: int = 1) -> str:
    """Format the email as a decorated string for terminal display."""
    contact = email.contact
    word_count = len(email.body.split())
    
    # ── Borders ──
    thick_border = "══════════════════════════════════════════════════════════"
    thin_border = "──────────────────────────────────────────────────────────"
    
    # ── Header ──
    lines = [
        thick_border,
        f"  📧  EMAIL PREVIEW  [{current}/{total}]",
        thick_border,
        f"  To:      {contact.recipient_email}",
        f"  Company: {contact.company}",
        f"  Role:    {contact.role}"
    ]
    
    # ── Subject ──
    lines.extend([
        thin_border,
        f"  Subject: {email.subject}",
        thin_border,
        ""
    ])
    
    # ── Body (indented) ──
    for line in email.body.splitlines():
        lines.append(f"  {line}")
        
    # ── Footer ──
    lines.extend([
        "",
        thick_border,
        f"  Word count: {word_count}/150",
        thick_border
    ])
    
    return "\n".join(lines)


def _get_user_input() -> UserDecision:
    """Prompt the user for a decision and map it to a UserDecision enum."""
    prompt_text = "  [S]end  |  S[k]ip  |  [Q]uit\n  ❯ "
    
    while True:
        try:
            choice = input(prompt_text).strip().lower()
        except (KeyboardInterrupt, EOFError):
            print("\n  [Operation cancelled]")
            return UserDecision.QUIT
            
        if not choice:
            return UserDecision.SKIP  # Default to safe action on empty Enter
            
        if choice in ("s", "send", "y", "yes"):
            return UserDecision.SEND
        elif choice in ("k", "skip", "n", "no"):
            return UserDecision.SKIP
        elif choice in ("q", "quit", "exit"):
            return UserDecision.QUIT
        else:
            print("  ⚠️  Invalid choice. Please enter s, k, or q.", file=sys.stderr)


def preview_and_confirm(email: GeneratedEmail, current: int = 1, total: int = 1) -> UserDecision:
    """Display the email preview and block until the user makes a decision."""
    preview_str = _format_preview(email, current, total)
    print(f"\n{preview_str}")
    return _get_user_input()
