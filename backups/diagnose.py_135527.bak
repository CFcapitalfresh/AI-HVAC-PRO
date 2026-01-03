# -*- coding: utf-8 -*-
"""
STANDALONE SCRIPT: HVAC System Diagnosis
---------------------------------------
Provides a quick diagnostic check of the AI system and its dependencies.
Rule 3: Modularity - Now leverages DiagnosticsService for core checks.
"""

import streamlit as st
import os
import sys
import time
import logging # Rule 4: Logging

# Rule 3: Import DiagnosticsService for shared logic
from services.diagnostics_logic import DiagnosticsService
from core.language_pack import get_text # Rule 5: Multilingual support
from core.config_loader import ConfigLoader # For API Key info message

# Configure logging for this standalone script
logger = logging.getLogger("Standalone_Diagnose")
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


st.set_page_config(page_title="System Diagnosis", page_icon="🩺")
lang = st.session_state.get('lang', 'gr') # Rule 6: Get language from session state if available

st.title(f"🩺 {get_text('diag_title', lang)}")
st.write(get_text('diag_subtitle', lang))
st.divider()

# Initialize DiagnosticsService (Rule 3)
diag_service = DiagnosticsService()

def status_write(msg, state="loading"):
    """Helper function for consistent status messages."""
    if state == "loading":
        st.info(f"⏳ {msg}...")
    elif state == "success":
        st.success(f"✅ {msg}")
    elif state == "error":
        st.error(f"❌ {msg}")
    elif state == "warning":
        st.warning(f"⚠️ {msg}")

# --- AI System Status Section (Rule 3: Use DiagnosticsService for checks) ---
st.subheader(get_text('diag_ai_section_title', lang))

# --- CHECK 1: Gemini API Key ---
st.markdown(f"**{get_text('diag_api_key_check', lang)}**")
key_check_result = diag_service.check_gemini_key()
if key_check_result["status"] == "success":
    status_write(get_text('diag_api_key_found', lang).format(masked_key=key_check_result['message']), "success")
else:
    status_write(get_text('diag_api_key_not_found', lang), "error")
    st.info(get_text('diag_api_key_info', lang))
    logger.error(f"API Key check failed: {key_check_result['message']}") # Rule 4

# --- CHECK 2: Google AI Connection (Ping Test) ---
st.markdown(f"**{get_text('diag_ai_conn_test', lang)}**")
if diag_service.api_key:
    status_write(get_text('diag_ai_conn_attempt', lang))
    conn_check_result = diag_service.test_ai_connection()
    if conn_check_result["status"] == "success":
        status_write(get_text('diag_ai_conn_success', lang).format(count=conn_check_result['message'].split(' ')[0]), "success")
        st.info(get_text('diag_ai_model_selected', lang).format(model_name=diag_service.ai_engine.model.model_name if diag_service.ai_engine.model else "N/A"))
    else:
        status_write(get_text('diag_ai_conn_fail', lang).format(error=conn_check_result['message']), "error")
        st.error(get_text('diag_ai_conn_fail_info', lang))
        logger.error(f"Google AI connection failed: {conn_check_result['message']}") # Rule 4
else:
    status_write(get_text('diag_ai_conn_fail', lang).format(error=get_text('diag_api_key_not_found', lang)), "error")

# --- CHECK 3: Automatic Model Selection ---
st.markdown(f"**{get_text('diag_ai_model_auto_detect', lang)}**")
selected_model_name = diag_service._get_best_model_name_internal() # Use internal method
if selected_model_name:
    st.info(get_text('diag_ai_model_selected', lang).format(model_name=selected_model_name))
else:
    status_write(get_text('diag_ai_model_selection_fail', lang), "error")
    logger.error("Failed to select an AI model.") # Rule 4

# --- CHECK 4: Simulation (Generation) ---
st.markdown(f"**{get_text('diag_ai_test_run', lang)}**")
if diag_service.api_key and diag_service.model:
    status_write(get_text('diag_ai_test_query', lang).format(model_name=diag_service.model.model_name))
    gen_check_result = diag_service.test_ai_generation()
    if gen_check_result["status"] == "success":
        status_write(get_text('diag_ai_test_success', lang).format(response=gen_check_result['message']), "success")
    elif gen_check_result["status"] == "warning":
        status_write(get_text('diag_ai_test_empty_response', lang), "warning")
    else: # error
        status_write(get_text('diag_ai_test_error', lang).format(error=gen_check_result['message']), "error")
        if "Quota Exceeded" in gen_check_result['message']:
            st.error(get_text('diag_ai_quota_exceeded', lang))
        elif "Invalid API Key" in gen_check_result['message']:
            st.error(get_text('diag_ai_key_invalid', lang))
        elif "Model not found" in gen_check_result['message']:
            st.error(get_text('diag_ai_model_not_found', lang))
        else:
            st.error(get_text('diag_ai_unknown_error', lang))
        logger.error(f"AI generation test failed: {gen_check_result['message']}") # Rule 4
else:
    status_write(get_text('diag_ai_test_error', lang).format(error="AI not configured or model not selected."), "error")


# --- CHECK 5: PDF Engine (pypdf) ---
st.markdown(f"**{get_text('diag_pdf_test', lang)}**")
pdf_check_result = diag_service.check_pdf_engine()
if pdf_check_result["status"] == "success":
    status_write(get_text('diag_pdf_read_success', lang), "success")
else:
    status_write(get_text('diag_pdf_read_fail', lang).format(error=pdf_check_result['message']), "error")
    logger.error(f"PDF engine check failed: {pdf_check_result['message']}") # Rule 4

st.write("\n")
st.success(get_text('diag_done', lang)) # Use get_text
st.write(get_text('diag_system_ready_text', lang)) # NEW KEY (if needed)