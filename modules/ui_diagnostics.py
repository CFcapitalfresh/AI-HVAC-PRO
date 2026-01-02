"""
MODULE: UI DIAGNOSTICS (CONNECTED)
----------------------------------
Description: Interactive Wizard that inherits context from Chat.
ENHANCEMENT: Added AI System Status checks for Gemini API Key, connection, and model.
"""

import streamlit as st
import logging # Κανόνας 4: Χρήση του κανονικού logging
import time

# NEW Imports for AI System Status checks
import google.generativeai as genai
from core.config_loader import ConfigLoader 
import pypdf # For PDF engine check, mirroring diagnose.py
from io import BytesIO

from services.diagnostics_logic import DiagnosticsService
from core.language_pack import get_text


logger = logging.getLogger("Module_Diagnostics_UI") # Αρχικοποίηση Logger

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

# --- ΛΕΙΤΟΥΡΓΙΑ: ΑΥΤΟΜΑΤΟΣ ΕΝΤΟΠΙΣΜΟΣ ΜΟΝΤΕΛΟΥ ---
def get_best_model(api_key_val):
    """Βρίσκει ποιο μοντέλο λειτουργεί αυτή τη στιγμή"""
    if not api_key_val:
        return None
    
    try:
        genai.configure(api_key=api_key_val) # Ensure configured
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        preferred = [
            "gemini-1.5-flash", 
            "models/gemini-1.5-flash",
            "gemini-1.5-flash-latest", 
            "models/gemini-1.5-flash-latest",
            "gemini-1.5-pro", 
            "models/gemini-1.5-pro",
            "gemini-1.5-pro-latest", 
            "models/gemini-1.5-pro-latest",
            "gemini-pro",
            "models/gemini-pro"
        ]
        
        for p in preferred:
            if p in available_models:
                return p
        
        for m in available_models: # Fallback to any gemini model
            if "gemini" in m:
                return m
                
        return "models/gemini-1.5-flash" # Last resort default
    except Exception as e:
        logger.warning(f"Failed to auto-detect best model: {e}")
        return "models/gemini-1.5-flash"

def render(user):
    lang = st.session_state.get('lang', 'gr')

    st.header(get_text('diag_title', lang))
    st.subheader(get_text('diag_subtitle', lang)) # Μεταφρασμένο υποτίτλο
    st.divider()

    # --- NEW SECTION: AI System Status Checks ---
    st.subheader(get_text('diag_ai_section_title', lang))

    # --- CHECK 1: GEMINI API KEY ---
    st.markdown(f"**{get_text('diag_api_key_check', lang)}**")
    api_key = None
    try:
        api_key = ConfigLoader.get_gemini_key()
        if api_key:
            mask = api_key[:5] + "..." + api_key[-4:]
            status_write(get_text('diag_api_key_found', lang).format(masked_key=mask), "success")
        else:
            status_write(get_text('diag_api_key_not_found', lang), "error")
            st.info(get_text('diag_api_key_info', lang))
    except Exception as e:
        status_write(f"{get_text('general_ui_error', lang).format(error='API Key check error')}: {e}", "error")
        logger.error(f"UI Diagnostics: API Key check error: {e}", exc_info=True)

    # --- CHECK 2: GOOGLE AI CONNECTION (PING) ---
    st.markdown(f"**{get_text('diag_ai_conn_test', lang)}**")
    if api_key:
        status_write(get_text('diag_ai_conn_attempt', lang))
        try:
            genai.configure(api_key=api_key)
            models = list(genai.list_models())
            count = len(models)
            status_write(get_text('diag_ai_conn_success', lang).format(count=count), "success")
        except Exception as e:
            status_write(get_text('diag_ai_conn_fail', lang).format(error=str(e)), "error")
            logger.error(f"UI Diagnostics: Google AI connection failed: {e}", exc_info=True)
    else:
        status_write(get_text('diag_ai_conn_fail', lang).format(error="No API Key"), "warning")
        st.info(get_text('diag_api_key_info', lang))

    # --- CHECK 3: AUTOMATIC MODEL SELECTION ---
    st.markdown(f"**{get_text('diag_ai_model_auto_detect', lang)}**")
    active_model_name = None
    if api_key:
        active_model_name = get_best_model(api_key)
        if active_model_name:
            st.info(get_text('diag_ai_model_selected', lang).format(model_name=active_model_name))
        else:
            status_write(get_text('diag_ai_model_selection_fail', lang), "error")
            logger.error("UI Diagnostics: Failed to select an AI model.")
    else:
        status_write(get_text('diag_ai_model_selection_fail', lang), "warning")

    # --- CHECK 4: SIMULATION (GENERATION) ---
    st.markdown(f"**{get_text('diag_ai_test_run', lang)}**")
    if api_key and active_model_name:
        status_write(get_text('diag_ai_test_query', lang).format(model_name=active_model_name))
        try:
            model = genai.GenerativeModel(active_model_name)
            response = model.generate_content("Γράψε τη λέξη 'OK'.")
            
            if response.text:
                status_write(get_text('diag_ai_test_resp_success', lang).format(response_text=response.text.strip()), "success")
            else:
                status_write(get_text('diag_ai_test_resp_empty', lang), "warning")
        except Exception as e:
            error_msg = str(e)
            status_write(get_text('diag_ai_critical_error', lang).format(error=error_msg), "error")
            if "429" in error_msg:
                st.error(get_text('diag_ai_error_429', lang))
            elif "403" in error_msg or "API_KEY_INVALID" in error_msg:
                st.error(get_text('diag_ai_error_403', lang))
            elif "404" in error_msg:
                st.error(get_text('diag_ai_error_404', lang))
            else:
                st.error(get_text('diag_ai_error_unknown', lang))
            logger.error(f"UI Diagnostics: AI response simulation failed: {e}", exc_info=True)
    else:
        status_write(get_text('diag_ai_critical_error', lang).format(error="AI model not initialized or API Key missing."), "warning")

    # --- CHECK 5: PDF ENGINE ---
    st.markdown(f"**5. {get_text('menu_library', lang)} Engine**") # Reusing menu_library for PDF context
    try:
        buffer = BytesIO()
        w = pypdf.PdfWriter()
        w.add_blank_page(width=100, height=100)
        w.write(buffer)
        buffer.seek(0)
        
        r = pypdf.PdfReader(buffer)
        if len(r.pages) > 0:
            status_write(f"{get_text('menu_library', lang)} engine works correctly.", "success") # Specific success message
        else:
            status_write(f"Problem with {get_text('menu_library', lang)} engine.", "error") # Specific error message
    except Exception as e:
        status_write(f"PDF engine error: {e}", "error")
        logger.error(f"UI Diagnostics: PDF engine check failed: {e}", exc_info=True)

    st.divider()
    st.info(get_text('diag_complete_summary', lang)) # NEW: Summary message
    st.divider()
    # --- END NEW SECTION ---


    # --- AUTO-FILL LOGIC (Inherit from Chat) ---
    default_error = ""
    if 'diag_prefill_error' in st.session_state:
        default_error = st.session_state.diag_prefill_error
        # Καθαρίζουμε το flag για να μην κολλήσει εκεί για πάντα
        del st.session_state.diag_prefill_error 
        
    context_info = ""
    if 'context_brand' in st.session_state and st.session_state.context_brand != "-":
        context_info = f"Συσκευή: {st.session_state.context_brand}"

    if 'diag_step' not in st.session_state: st.session_state.diag_step = 0
    if 'diag_plan' not in st.session_state: st.session_state.diag_plan = None
    
    try: # Κανόνας 4: Γενικό try/except block
        # 1. Input Section
        if not st.session_state.diag_plan:
            with st.container(border=True):
                st.subheader(get_text('diag_start_new', lang))
                if context_info: st.info(f"🔗 {context_info}")
                
                # Το πεδίο παίρνει τιμή από το Chat (αν υπάρχει)
                error_input = st.text_input(get_text('diag_input_ph', lang), value=default_error)
                
                # Context από Manuals
                manual_context = ""
                if 'active_manuals' in st.session_state and st.session_state.active_manuals:
                    st.caption(f"📚 {get_text('diag_context', lang)} {len(st.session_state.active_manuals)} manuals loaded.")
                    # Προσοχή: Εδώ λαμβάνουμε υπόψη μόνο το πρώτο manual ως context αν υπάρχουν πολλά
                    manual_context = str(st.session_state.active_manuals[0])

                if st.button(get_text('diag_btn_create', lang), type="primary", use_container_width=True):
                    if error_input:
                        with st.spinner(get_text('diag_spinner', lang)):
                            service = DiagnosticsService()
                            plan = service.generate_checklist(error_input, manual_context, lang=lang)
                            
                            if plan:
                                st.session_state.diag_plan = plan
                                st.session_state.diag_step = 0
                                st.rerun()
                            else:
                                st.error(get_text('diag_fail', lang))
                                logger.error(f"Diagnostics: Failed to generate plan for input: {error_input}")
                    else:
                        st.warning(get_text('diag_input_ph', lang)) # Να συμπληρώσει κάτι ο χρήστης
        
        # 2. Active Wizard (Same as before)
        else:
            plan = st.session_state.diag_plan
            steps = plan.get('steps', [])
            current_idx = st.session_state.diag_step
            
            # Ενημέρωση εδώ για μετάφραση του τίτλου του πλάνου
            st.subheader(f"🛡️ {plan.get('title', get_text('diag_plan_title', lang))}") # Μεταφράσιμο fallback
            
            if len(steps) > 0: # Αποφυγή DivisionByZero αν δεν υπάρχουν βήματα
                progress = (current_idx / len(steps))
                st.progress(progress, text=f"{get_text('diag_step', lang)} {current_idx + 1} {get_text('diag_of', lang)} {len(steps)}")
            else:
                st.progress(0, text=f"{get_text('diag_step', lang)} 0 {get_text('diag_of', lang)} 0")


            if current_idx >= len(steps):
                st.success(get_text('diag_done', lang))
                if st.button(get_text('diag_btn_new', lang)):
                    st.session_state.diag_plan = None
                    st.session_state.diag_step = 0
                    st.rerun()
                return

            step = steps[current_idx]
            
            with st.container(border=True):
                st.markdown(f"### {get_text('diag_step', lang)} {step['id']}")
                st.markdown(f"**{get_text('diag_action', lang)}** {step['action']}")
                if 'tip' in step:
                    st.info(f"💡 Tip: {step['tip']}")
                
                st.divider()
                st.markdown(f"**{get_text('diag_question', lang)}** {step['question']}")
                
                c1, c2 = st.columns(2)
                
                if c1.button(get_text('diag_yes', lang), use_container_width=True):
                    st.balloons()
                    st.success(get_text('diag_solved_msg', lang))
                    logger.info(f"Diagnostics: User marked step {step['id']} as solved.")
                    time.sleep(2)
                    st.session_state.diag_plan = None
                    st.rerun()
                    
                if c2.button(get_text('diag_no', lang), use_container_width=True):
                    st.session_state.diag_step += 1
                    logger.info(f"Diagnostics: User continued to step {st.session_state.diag_step}.")
                    st.rerun()
            
            if st.button(get_text('diag_cancel', lang)):
                st.session_state.diag_plan = None
                st.rerun()

    except Exception as e:
        logger.error(f"Diagnostics UI: General rendering error in render function for user {user}: {e}", exc_info=True)
        st.error(f"{get_text('general_ui_error', lang).format(error=e)}") # Κανόνας 5