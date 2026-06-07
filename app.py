"""
app.py — Streamlit Frontend for The Closer
"""

import streamlit as st
import pandas as pd
import json
import os

from core.config import load_config
from core.models import ContactRecord, OutreachStatus, AppConfig
from data.data_loader import filter_opt_outs, load_opt_out_list
from generator.email_generator import generate_email
from generator.scorer import score_email, get_score_label
from generator.spam_checker import check_spam_risk
from sender.email_sender import send_email
from sender.logger import make_log_entry, log_outreach


st.set_page_config(page_title="The Closer", page_icon="📧", layout="wide")

@st.cache_data
def load_app_config():
    return load_config()

config = load_app_config()

# ─── UI: Sidebar ───
st.sidebar.title("📧 The Closer")
st.sidebar.markdown("Automated Cold Outreach")

st.sidebar.header("Configuration")
dry_run = st.sidebar.checkbox("DRY_RUN (Draft only)", value=config.dry_run)
llm_enabled = st.sidebar.checkbox("Use Groq LLM", value=config.llm_enabled)
config.dry_run = dry_run
config.llm_enabled = llm_enabled

st.sidebar.header("Data Source")
uploaded_file = st.sidebar.file_uploader("Upload Contacts (JSON/CSV)", type=["json", "csv"])


# ─── UI: Main Area ───
st.title("Outreach Dashboard")

if uploaded_file is not None:
    # Parse uploaded file
    try:
        contacts_raw = []
        if uploaded_file.name.endswith(".json"):
            contacts_raw = json.load(uploaded_file)
        elif uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
            contacts_raw = df.to_dict("records")
            
        # Convert to ContactRecords
        contacts = []
        for row in contacts_raw:
            try:
                c = ContactRecord(**{k: v for k, v in row.items() if pd.notna(v)})
                contacts.append(c)
            except Exception as e:
                st.sidebar.warning(f"Skipped a row: {e}")
                
        # Filter opt-outs
        opt_outs = load_opt_out_list("data/opt_out.txt")
        valid_contacts = filter_opt_outs(contacts, opt_outs)
        
        st.success(f"Loaded {len(valid_contacts)} valid contacts.")
        
        # State management for the current index
        if 'current_idx' not in st.session_state:
            st.session_state.current_idx = 0
            
        if st.session_state.current_idx < len(valid_contacts):
            contact = valid_contacts[st.session_state.current_idx]
            
            st.subheader(f"Contact {st.session_state.current_idx + 1} of {len(valid_contacts)}")
            
            with st.spinner("Generating email..."):
                email = generate_email(contact, config)
                score, breakdown = score_email(email)
                score_label = get_score_label(score)
                spam_risk, spam_flags = check_spam_risk(email)
                
            # Layout the badges
            col1, col2 = st.columns(2)
            with col1:
                color = "green" if score >= 75 else "orange" if score >= 60 else "red"
                st.markdown(f"**Quality Score:** :{color}[{score}/100 ({score_label})]")
                with st.expander("Score Breakdown"):
                    st.json(breakdown)
                    
            with col2:
                color = "green" if spam_risk == "LOW" else "orange" if spam_risk == "MEDIUM" else "red"
                st.markdown(f"**Spam Risk:** :{color}[{spam_risk}]")
                if spam_flags:
                    for flag in spam_flags:
                        st.caption(f"🚩 {flag}")

            # Display email card
            st.divider()
            st.markdown(f"**To:** {contact.recipient_email} ({contact.company} - {contact.role})")
            st.markdown(f"**Subject:** {email.subject}")
            st.text_area("Body", email.body, height=300, disabled=True)
            st.divider()
            
            # Action Buttons
            c1, c2, c3 = st.columns([1, 1, 4])
            if c1.button("✅ Send", type="primary"):
                result = send_email(email, config)
                log_outreach(make_log_entry(email, result.status, result.error_message), config.log_file)
                st.session_state.current_idx += 1
                st.rerun()
                
            if c2.button("⏭️ Skip"):
                log_outreach(make_log_entry(email, OutreachStatus.SKIPPED), config.log_file)
                st.session_state.current_idx += 1
                st.rerun()
                
        else:
            st.info("All contacts processed!")

    except Exception as e:
        st.error(f"Error parsing file: {e}")

else:
    st.info("Upload a contacts file to begin.")

# ─── UI: Log Viewer ───
st.header("Outreach Log")
if os.path.exists(config.log_file):
    try:
        log_df = pd.read_csv(config.log_file)
        st.dataframe(log_df.tail(20), use_container_width=True)
    except Exception:
        st.caption("No log data available.")
else:
    st.caption("No log file found yet.")
