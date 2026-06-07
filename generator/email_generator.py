"""
email_generator.py — Email Composition for The Closer

Converts a ContactRecord into a GeneratedEmail using either
a deterministic f-string template or an LLM (Groq) rewriter.
"""

import sys
from typing import Optional

from core.models import ContactRecord, GeneratedEmail, AppConfig


def _validate_word_count(body: str, limit: int = 150) -> bool:
    """Check if the body is under the word limit.
    
    Logs a warning to stderr if exceeded but does not block.
    """
    word_count = len(body.split())
    if word_count > limit:
        print(f"⚠️  Warning: Email body exceeds {limit} words ({word_count} words).", file=sys.stderr)
        return False
    return True


def _generate_from_template(contact: ContactRecord) -> GeneratedEmail:
    """Generate email using a deterministic f-string template."""
    
    # ── Greeting ──
    if contact.recipient_name:
        greeting = f"Hi {contact.recipient_name},"
    else:
        greeting = "Hi there,"

    # ── Hook ──
    if contact.personalization_note:
        hook = f"I noticed {contact.company} is hiring for the {contact.role} position. {contact.personalization_note}"
    else:
        hook = f"I came across the {contact.role} position at {contact.company} and it caught my attention."

    # ── Introduction & Value ──
    intro = f"I'm {contact.candidate_name}, and I've been building projects around {contact.candidate_background}."
    value = "The role stood out because it connects closely with my interest in practical automation and product-focused engineering."
    
    # ── Ask ──
    ask = "Would you be open to a quick look at my profile or pointing me to the right person?"

    # ── Sign-off ──
    sign_off = f"Best,\n{contact.candidate_name}"
    
    links = []
    if contact.portfolio_url:
        links.append(f"Portfolio: {contact.portfolio_url}")
    if contact.linkedin_url:
        links.append(f"LinkedIn: {contact.linkedin_url}")
    if contact.resume_link:
        links.append(f"Resume: {contact.resume_link}")
        
    if links:
        sign_off += "\n" + "\n".join(links)

    # ── Assemble ──
    subject = f"Quick note on the {contact.role} role"
    body = f"{greeting}\n\n{hook}\n\n{intro}\n{value}\n\n{ask}\n\n{sign_off}"
    
    _validate_word_count(body)

    return GeneratedEmail(
        subject=subject,
        body=body,
        contact=contact,
        template_used="default"
    )


def _generate_with_llm(contact: ContactRecord, config: AppConfig) -> GeneratedEmail:
    """Use Groq (Llama 3.3 / Mixtral) to generate a polished cold email."""
    try:
        from groq import Groq
    except ImportError:
        print("⚠️  Warning: groq package not installed. Falling back to template.", file=sys.stderr)
        return _generate_from_template(contact)

    if not config.llm_api_key:
        print("⚠️  Warning: LLM_API_KEY missing. Falling back to template.", file=sys.stderr)
        return _generate_from_template(contact)

    prompt = f"""Write a cold outreach email for a job opportunity.

    Recipient: {contact.recipient_name or 'Hiring Manager'} at {contact.company}
    Role: {contact.role}
    About the company: {contact.personalization_note or 'N/A'}
    
    Candidate: {contact.candidate_name}
    Background: {contact.candidate_background}
    Portfolio: {contact.portfolio_url or 'N/A'}
    
    Requirements:
    - Under 150 words
    - Include a personalization hook about the company
    - One clear ask (quick chat or referral)
    - Professional but natural tone
    - No exaggerated claims
    
    Return EXACTLY in this format:
    SUBJECT: <subject line>
    BODY:
    <email body>
    """
    
    try:
        client = Groq(api_key=config.llm_api_key)
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=config.llm_model,
        )
        response = chat_completion.choices[0].message.content
        
        # Parse response into subject + body
        subject = f"Application: {contact.role}"  # fallback
        body = response
        
        lines = response.split('\n')
        for i, line in enumerate(lines):
            if line.startswith("SUBJECT:"):
                subject = line.replace("SUBJECT:", "").strip()
            elif line.startswith("BODY:"):
                body = "\n".join(lines[i+1:]).strip()
                break
                
        _validate_word_count(body)
                
        return GeneratedEmail(
            subject=subject,
            body=body,
            contact=contact,
            template_used="groq_llm"
        )
    except Exception as e:
        print(f"⚠️  LLM Generation failed: {e}. Falling back to template.", file=sys.stderr)
        return _generate_from_template(contact)


def generate_email(contact: ContactRecord, config: AppConfig) -> GeneratedEmail:
    """Main entry point; routes to template or LLM based on config."""
    if config.llm_enabled:
        return _generate_with_llm(contact, config)
    else:
        return _generate_from_template(contact)
