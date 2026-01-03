import streamlit as st
import logging
import time

# NEW Imports for AI System Status checks
import google.generativeai as genai # Still needed for list_models and GenerativeModel
import pypdf # For PDF engine check, mirroring diagnose.py
from io import BytesIO

from services.diagnostics_logic import DiagnosticsService # IMPORT THIS
from core.language_pack import get_text
from core.config_loader import ConfigLoader # For direct API Key lookup when AIEngine is not yet ready


logger = logging.getLogger("Module_Diagnostics_UI") # Αρχικοποίηση Logger

def status_write(msg_container, msg, state="loading"):
    """
    Helper function for consistent status messages.
    Accepts a Streamlit container (e.g., st.empty()) and updates it.
    """
    if state == "loading":
        msg_container.info(f"⏳ {msg}...")
    elif state == "success":
        msg_container.success(f"✅ {msg}")
    elif state == "error":
        msg_container.error(f"❌ {msg}")
    elif state == "warning":
        msg_container.warning(f"⚠️ {msg}")
    # Return the same container for chaining if needed, or None for non-loading states.
    return msg_container


def render(user):
    lang = st.session_state.get('lang', 'gr')

    st.header(get_text('diag_title', lang))
    st.subheader(get_text('diag_subtitle', lang)) # Μεταφρασμένο υποτίτλο
    st.divider()

    # --- ΒΑΘΙΑ ΑΝΑΛΥΣΗ: Ενότητα Ελέγχου Κατάστασης Συστήματος AI ---
    st.subheader(get_text('diag_ai_section_title', lang))

    # ΒΕΛΤΙΩΣΗ: Αρχικοποίηση του DiagnosticsService μία φορά ανά περίοδο λειτουργίας
    # και αξιοποίηση του AIEngine που έχει ήδη ρυθμιστεί.
    if 'diagnostics_service_instance' not in st.session_state:
        st.session_state.diagnostics_service_instance = DiagnosticsService()
    
    diag_service = st.session_state.diagnostics_service_instance
    ai_engine = diag_service.ai_engine # Ανάκτηση της ρυθμισμένης παρουσίας του AI Engine

    # --- ΕΛΕΓΧΟΣ 1: Gemini API Key ---
    st.markdown(f"**{get_text('diag_api_key_check', lang)}**")
    api_key_placeholder = st.empty() # Placeholder για δυναμική ενημέρωση μηνύματος
    
    # Attempt to get API key from ConfigLoader directly in case AIEngine failed to init
    api_key = ConfigLoader.get_gemini_key() 

    if api_key:
        mask = api_key[:5] + "..." + api_key[-4:]
        status_write(api_key_placeholder, get_text('diag_api_key_found', lang).format(masked_key=mask), "success")
    else:
        status_write(api_key_placeholder, get_text('diag_api_key_not_found', lang), "error")
        st.info(get_text('diag_api_key_info', lang))
    
    # --- ΕΛΕΓΧΟΣ 2: Σύνδεση με Google AI (Ping Test) ---
    st.markdown(f"**{get_text('diag_ai_conn_test', lang)}**")
    conn_placeholder = st.empty()
    if api_key:
        # ΒΕΛΤΙΩΣΗ: Αντί να προσπαθούμε να συνδεθούμε ξανά, ελέγχουμε αν το AIEngine έχει μοντέλο.
        # Αν έχει, σημαίνει ότι η αρχική σύνδεση κατά το setup ήταν επιτυχής.
        if ai_engine.model:
            try:
                # Χρησιμοποιούμε ακόμα το genai.list_models για να πάρουμε τον αριθμό,
                # αλλά βασιζόμαστε στην προηγούμενη επιτυχή ρύθμιση του ai_engine.
                genai.configure(api_key=api_key) # Εξασφάλιση ότι το genai είναι ρυθμισμένο
                models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                count = len(models)
                status_write(conn_placeholder, get_text('diag_ai_conn_success', lang).format(count=count), "success")
                st.info(get_text('diag_selected_model', lang).format(model_name=ai_engine.model.model_name))
            except Exception as e:
                # Σφάλμα κατά την καταγραφή μοντέλων (αλλά το AI Engine μπορεί να έχει λειτουργήσει αρχικά)
                status_write(conn_placeholder, get_text('diag_ai_conn_fail', lang).format(error=str(e)), "error")
                logger.error(f"UI Diagnostics: Google AI connection failed during model listing: {e}", exc_info=True)
        else: 
            # Η αρχικοποίηση του AIEngine απέτυχε
            status_write(conn_placeholder, get_text('diag_ai_conn_fail', lang).format(error=ai_engine.last_error or 'Unknown AI setup error'), "error")
            logger.error(f"UI Diagnostics: Google AI connection failed during AIEngine setup: {ai_engine.last_error}", exc_info=True)
    else:
        status_write(conn_placeholder, get_text('diag_ai_conn_fail', lang).format(error=get_text('diag_api_key_not_found', lang)), "error")

    # --- ΕΛΕΓΧΟΣ 3: PDF Engine (pypdf) ---
    st.markdown(f"**{get_text('diag_pdf_test', lang)}**")
    pdf_placeholder = st.empty()
    try:
        # Δοκιμή ανάγνωσης ενός μικρού, κενού PDF για να ελέγξουμε το pypdf
        reader = pypdf.PdfReader(BytesIO(b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n2 0 obj<</Type/Pages/Count 0>>endobj\nxref\n0 3\n0000000000 65535 f\n0000000009 00000 n\n0000000055 00000 n\ntrailer<</Size 3/Root 1 0 R>>startxref\n104\n%%EOF"))
        # Αν δεν σκάσει, είναι ΟΚ
        status_write(pdf_placeholder, get_text('diag_pdf_read_success', lang), "success")
    except Exception as e:
        status_write(pdf_placeholder, get_text('diag_pdf_read_fail', lang).format(error=str(e)), "error")
        logger.error(f"UI Diagnostics: pypdf check failed: {e}", exc_info=True)

    # --- ΕΛΕΓΧΟΣ 4: SIMULATION (GENERATION) ---
    st.markdown(f"**{get_text('diag_ai_test_run', lang)}**")
    sim_placeholder = st.empty()
    if api_key and ai_engine.model:
        status_write(sim_placeholder, get_text('diag_ai_test_query', lang).format(model_name=ai_engine.model.model_name))
        try:
            # Re-use the ai_engine instance
            response_text = ai_engine.get_chat_response(content_parts=[{"text": "Γράψε τη λέξη 'OK'."}])
            
            if response_text and "OK" in response_text: # Check for the expected "OK" or part of it
                status_write(sim_placeholder, get_text('diag_ai_test_success', lang).format(response=response_text.strip()), "success")
            elif response_text:
                status_write(sim_placeholder, get_text('diag_ai_test_empty', lang), "warning")
                logger.warning(f"UI Diagnostics: AI test run returned non-empty but unexpected response: {response_text[:100]}")
            else:
                status_write(sim_placeholder, get_text('diag_ai_test_empty', lang), "warning")
                logger.warning("UI Diagnostics: AI test run returned empty response.")
        except Exception as e:
            error_message = str(e)
            status_write(sim_placeholder, get_text('diag_ai_critical_error', lang).format(error=error_message), "error")
            if "429" in error_message:
                st.error(f"👉 {get_text('diag_ai_quota_error', lang)}")
            elif "403" in error_message or "API_KEY_INVALID" in error_message:
                st.error(f"👉 {get_text('diag_ai_key_invalid', lang)}")
            elif "404" in error_message:
                 st.error(f"👉 {get_text('diag_ai_model_not_found', lang)}")
            else:
                 st.error(f"👉 {get_text('diag_ai_unknown_error', lang)}")
            logger.error(f"UI Diagnostics: AI test run failed: {e}", exc_info=True)
    else:
        status_write(sim_placeholder, get_text('diag_ai_test_run', lang), "warning")
        st.info(get_text('diag_api_key_info', lang))

    st.markdown("---")

    # --- WIZARD LOGIC ---
    if 'diag_plan' not in st.session_state:
        st.session_state.diag_plan = None
        st.session_state.diag_current_step = 0
        st.session_state.diag_solved = False

    if st.session_state.diag_solved:
        st.success(get_text('diag_solved_msg', lang))
        if st.button(get_text('diag_btn_new', lang)):
            st.session_state.diag_plan = None
            st.session_state.diag_current_step = 0
            st.session_state.diag_solved = False
            st.rerun()

    if st.session_state.diag_plan is None and not st.session_state.diag_solved:
        with st.form("diagnosis_form"):
            problem_description = st.text_input(get_text('diag_input_ph', lang), key="diag_problem_input")
            # Optionally add context from chat if available
            # context_manual = st.session_state.get('chat_context_manual_content', '')
            submitted = st.form_submit_button(get_text('diag_btn_create', lang))

            if submitted and problem_description:
                with st.spinner(get_text('diag_spinner', lang)):
                    try:
                        # Use DiagnosticsService to generate the checklist
                        # For now, without specific manual context
                        checklist = diag_service.generate_checklist(
                            problem_description, 
                            lang=lang
                        )
                        if checklist:
                            st.session_state.diag_plan = checklist
                            st.session_state.diag_current_step = 0
                            st.session_state.diag_solved = False
                            logger.info(f"Generated diagnosis plan for: {problem_description}")
                            st.rerun()
                        else:
                            st.error(get_text('diag_fail', lang))
                            logger.error(f"Failed to generate diagnosis plan for: {problem_description}")
                    except Exception as e:
                        st.error(f"{get_text('diag_fail', lang)}: {e}")
                        logger.critical(f"Critical error during diagnosis plan generation: {e}", exc_info=True)
            elif submitted:
                st.warning(get_text('diag_input_ph', lang))

    elif st.session_state.diag_plan and not st.session_state.diag_solved:
        plan = st.session_state.diag_plan
        current_step_idx = st.session_state.diag_current_step

        st.subheader(plan.get('title', get_text('diag_plan_title', lang)))

        if current_step_idx < len(plan['steps']):
            step = plan['steps'][current_step_idx]
            st.markdown(f"### {get_text('diag_step', lang)} {current_step_idx + 1} {get_text('diag_of', lang)} {len(plan['steps'])}")
            
            with st.container(border=True):
                st.markdown(f"**{get_text('diag_action', lang)}** {step.get('action', '')}")
                if step.get('tip'):
                    st.info(f"💡 {step['tip']}")
                st.markdown(f"**{get_text('diag_question', lang)}** {step.get('question', '')}")

                col_yes, col_no, col_cancel = st.columns(3)
                if col_yes.button(get_text('diag_yes', lang), key=f"diag_yes_{current_step_idx}", use_container_width=True):
                    st.session_state.diag_solved = True
                    logger.info(f"Diagnosis solved at step {current_step_idx + 1}")
                    st.rerun()
                if col_no.button(get_text('diag_no', lang), key=f"diag_no_{current_step_idx}", use_container_width=True):
                    st.session_state.diag_current_step += 1
                    logger.info(f"Diagnosis continued to step {current_step_idx + 2}")
                    st.rerun()
                if col_cancel.button(get_text('diag_cancel', lang), key=f"diag_cancel_{current_step_idx}", use_container_width=True):
                    st.session_state.diag_plan = None
                    st.session_state.diag_current_step = 0
                    st.session_state.diag_solved = False
                    logger.info("Diagnosis cancelled.")
                    st.rerun()
        else:
            st.info(get_text('diag_done', lang))
            st.warning("⚠️ Δεν βρέθηκαν άλλες λύσεις στον οδηγό.")
            if st.button(get_text('diag_btn_new', lang), key="diag_restart_end"):
                st.session_state.diag_plan = None
                st.session_state.diag_current_step = 0
                st.session_state.diag_solved = False
                st.rerun()