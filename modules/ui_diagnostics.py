import streamlit as st
import logging
import time

# NEW Imports for AI System Status checks
import google.generativeai as genai # Still needed for list_models and GenerativeModel
import pypdf # For PDF engine check, mirroring diagnose.py
from io import BytesIO

from services.diagnostics_logic import DiagnosticsService # IMPORT THIS (Rule 3)
from core.language_pack import get_text # Rule 5
from core.config_loader import ConfigLoader # For direct API Key lookup when AIEngine is not yet ready


logger = logging.getLogger("Module_Diagnostics_UI") # Αρχικοποίηση Logger (Rule 4)

def status_write(msg_container: Any, msg: str, state: str = "loading"):
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
    lang = st.session_state.get('lang', 'gr') # Rule 6, 5

    st.header(get_text('diag_title', lang)) # Rule 5
    st.subheader(get_text('diag_subtitle', lang)) # Rule 5
    st.divider()

    # --- ΒΑΘΙΑ ΑΝΑΛΥΣΗ: Ενότητα Ελέγχου Κατάστασης Συστήματος AI ---
    st.subheader(get_text('diag_ai_section_title', lang)) # Rule 5

    # ΒΕΛΤΙΩΣΗ: Αρχικοποίηση του DiagnosticsService μία φορά ανά περίοδο λειτουργίας
    # και αξιοποίηση του AIEngine που έχει ήδη ρυθμιστεί. (Rule 6)
    if 'diagnostics_service_instance' not in st.session_state:
        st.session_state.diagnostics_service_instance = DiagnosticsService()
    
    diag_service = st.session_state.diagnostics_service_instance # Rule 3
    ai_engine = diag_service.ai_engine # Ανάκτηση της ρυθμισμένης παρουσίας του AI Engine (Rule 3)

    # --- ΕΛΕΓΧΟΣ 1: Gemini API Key ---
    st.markdown(f"**{get_text('diag_api_key_check', lang)}**") # Rule 5
    api_key_placeholder = st.empty() # Placeholder για δυναμική ενημέρωση μηνύματος
    
    # Attempt to get API key from ConfigLoader directly in case AIEngine failed to init
    api_key = ConfigLoader.get_gemini_key() 

    if api_key:
        mask = api_key[:5] + "..." + api_key[-4:]
        status_write(api_key_placeholder, get_text('diag_api_key_found', lang).format(masked_key=mask), "success") # Rule 5
    else:
        status_write(api_key_placeholder, get_text('diag_api_key_not_found', lang), "error") # Rule 5
        st.info(get_text('diag_api_key_info', lang)) # Rule 5
    
    # --- ΕΛΕΓΧΟΣ 2: Σύνδεση με Google AI (Ping Test) ---
    st.markdown(f"**{get_text('diag_ai_conn_test', lang)}**") # Rule 5
    conn_placeholder = st.empty()
    if api_key:
        # ΒΕΛΤΙΩΣΗ: Αντί να προσπαθούμε να συνδεθούμε ξανά, ελέγχουμε αν το AIEngine έχει μοντέλο.
        # Αν έχει, σημαίνει ότι η αρχική σύνδεση κατά το setup ήταν επιτυχής.
        if ai_engine.model:
            try: # Rule 4: Error Handling
                # Χρησιμοποιούμε ακόμα το genai.list_models για να πάρουμε τον αριθμό,
                # αλλά βασιζόμαστε στην προηγούμενη επιτυχή ρύθμιση του ai_engine.
                genai.configure(api_key=api_key) # Εξασφάλιση ότι το genai είναι ρυθμισμένο
                models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                count = len(models)
                status_write(conn_placeholder, get_text('diag_ai_conn_success', lang).format(count=count), "success") # Rule 5
                st.info(get_text('diag_selected_model', lang).format(model_name=ai_engine.model.model_name)) # Rule 5
            except Exception as e:
                # Σφάλμα κατά την καταγραφή μοντέλων (αλλά το AI Engine μπορεί να έχει λειτουργήσει αρχικά)
                status_write(conn_placeholder, get_text('diag_ai_conn_fail', lang).format(error=str(e)), "error") # Rule 5
                logger.error(f"UI Diagnostics: Google AI connection failed during model listing: {e}", exc_info=True) # Rule 4
        else: 
            # Η αρχικοποίηση του AIEngine απέτυχε
            status_write(conn_placeholder, get_text('diag_ai_conn_fail', lang).format(error=ai_engine.last_error or 'Unknown AI setup error'), "error") # Rule 5
            logger.error(f"UI Diagnostics: Google AI connection failed during AIEngine setup: {ai_engine.last_error}", exc_info=True) # Rule 4
    else:
        status_write(conn_placeholder, get_text('diag_ai_conn_fail', lang).format(error=get_text('diag_api_key_not_found', lang)), "error") # Rule 5

    # --- ΕΛΕΓΧΟΣ 3: PDF Engine (pypdf) ---
    st.markdown(f"**{get_text('diag_pdf_test', lang)}**") # Rule 5
    pdf_placeholder = st.empty()
    try: # Rule 4: Error Handling
        # Δοκιμή ανάγνωσης ενός μικρού, κενού PDF για να ελέγξουμε το pypdf
        reader = pypdf.PdfReader(BytesIO(b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n2 0 obj<</Type/Pages/Count 0>>endobj\nxref\n0 3\n0000000000 65535 f\n0000000009 00000 n\n0000000055 00000 n\ntrailer<</Size 3/Root 1 0 R>>startxref\n104\n%%EOF"))
        # Αν δεν σκάσει, είναι επιτυχία
        status_write(pdf_placeholder, get_text('diag_pdf_success', lang), "success") # Rule 5
    except Exception as e:
        status_write(pdf_placeholder, get_text('diag_pdf_fail', lang).format(error=str(e)), "error") # Rule 5
        logger.error(f"UI Diagnostics: PDF engine check failed: {e}", exc_info=True) # Rule 4

    # --- ΕΛΕΓΧΟΣ 4: Δοκιμαστική εκτέλεση AI (Generation) ---
    st.markdown(f"**{get_text('diag_ai_test_run', lang)}**") # Rule 5
    gen_placeholder = st.empty()
    if api_key and ai_engine.model:
        status_write(gen_placeholder, get_text('diag_ai_test_query', lang).format(model_name=ai_engine.model.model_name)) # Rule 5
        gen_check_result = diag_service.test_ai_generation() # Rule 3
        if gen_check_result["status"] == "success":
            status_write(gen_placeholder, get_text('diag_ai_test_success', lang).format(response=gen_check_result['message']), "success") # Rule 5
        elif gen_check_result["status"] == "warning":
            status_write(gen_placeholder, get_text('diag_ai_test_empty_response', lang), "warning") # Rule 5
        else: # error
            status_write(gen_placeholder, get_text('diag_ai_test_error', lang).format(error=gen_check_result['message']), "error") # Rule 5
            if "Quota Exceeded" in gen_check_result['message']:
                st.error(get_text('diag_ai_quota_exceeded', lang)) # Rule 5
            elif "Invalid API Key" in gen_check_result['message']:
                st.error(get_text('diag_ai_key_invalid', lang)) # Rule 5
            elif "Model not found" in gen_check_result['message']:
                st.error(get_text('diag_ai_model_not_found', lang)) # Rule 5
            else:
                st.error(get_text('diag_ai_unknown_error', lang)) # Rule 5
            logger.error(f"UI Diagnostics: AI generation test failed: {gen_check_result['message']}", exc_info=True) # Rule 4
    else:
        status_write(gen_placeholder, get_text('diag_ai_test_error', lang).format(error="AI not configured or model not selected."), "error") # Rule 5

    st.divider()

    # --- WIZARD: Δυναμικός Οδηγός Διάγνωσης (AI-powered) ---
    st.subheader(get_text('diag_plan_title', lang)) # Rule 5

    # Initialize session state for the wizard (Rule 6)
    if 'diag_wizard_active' not in st.session_state: st.session_state.diag_wizard_active = False
    if 'diag_current_step' not in st.session_state: st.session_state.diag_current_step = 0
    if 'diag_checklist' not in st.session_state: st.session_state.diag_checklist = []
    if 'diag_problem_description' not in st.session_state: st.session_state.diag_problem_description = ""
    if 'diag_manual_context' not in st.session_state: st.session_state.diag_manual_context = "" # From UI Chat's selected manual


    if not st.session_state.diag_wizard_active:
        # Initial input for problem description
        problem_description = st.text_input(get_text('diag_input_ph', lang), key="diag_problem_input") # Rule 5
        
        if st.button(get_text('diag_btn_create', lang), type="primary", use_container_width=True): # Rule 5
            if problem_description:
                st.session_state.diag_problem_description = problem_description
                with st.spinner(get_text('diag_spinner', lang)): # Rule 5
                    try: # Rule 4: Error Handling
                        # Assuming the ChatSessionService has access to current selected manuals for context
                        # For simplicity here, we'll just pass the problem description.
                        # For advanced, would fetch manual content dynamically here based on chat context.
                        checklist = diag_service.generate_checklist(problem_description, lang=lang) # Rule 3
                        if checklist and checklist['checklist']:
                            st.session_state.diag_checklist = checklist['checklist']
                            st.session_state.diag_current_step = 0
                            st.session_state.diag_wizard_active = True
                            st.rerun()
                        else:
                            st.error(get_text('diag_fail', lang)) # Rule 5
                            logger.error(f"AI failed to generate a valid checklist for: {problem_description}") # Rule 4
                    except Exception as e:
                        st.error(f"{get_text('diag_fail', lang)}: {e}") # Rule 5
                        logger.error(f"Error generating checklist for '{problem_description}': {e}", exc_info=True) # Rule 4
            else:
                st.warning(get_text('diag_input_ph', lang)) # Rule 5
    else:
        # Display current step of the checklist
        current_step_idx = st.session_state.diag_current_step
        total_steps = len(st.session_state.diag_checklist)
        
        if current_step_idx < total_steps:
            current_step = st.session_state.diag_checklist[current_step_idx]
            
            st.markdown(f"### {get_text('diag_step', lang)} {current_step_idx + 1} {get_text('diag_of', lang)} {total_steps}: {current_step['title']}") # Rule 5
            st.info(f"**{get_text('diag_action', lang)}** {current_step['action']}") # Rule 5
            st.markdown(f"**{get_text('diag_question', lang)}** {current_step['question']}") # Rule 5
            if 'tip' in current_step and current_step['tip']:
                st.caption(f"💡 *{current_step['tip']}*")

            col_yes, col_no, col_cancel = st.columns(3)
            with col_yes:
                if st.button(get_text('diag_yes', lang), use_container_width=True, type="success"): # Rule 5
                    st.success(get_text('diag_solved_msg', lang)) # Rule 5
                    st.session_state.diag_wizard_active = False
                    st.session_state.diag_checklist = []
                    st.session_state.diag_current_step = 0
                    logger.info("Diagnostic wizard completed successfully.") # Rule 4
            with col_no:
                if st.button(get_text('diag_no', lang), use_container_width=True, type="secondary"): # Rule 5
                    st.session_state.diag_current_step += 1
                    logger.info(f"Diagnostic wizard moving to step {st.session_state.diag_current_step + 1}.") # Rule 4
                    st.rerun()
            with col_cancel:
                if st.button(get_text('diag_cancel', lang), use_container_width=True, type="danger"): # Rule 5
                    st.warning(get_text('diag_wizard_cancelled', lang) if 'diag_wizard_cancelled' in LANGUAGE_PACK else "Διαγνωστικός οδηγός ακυρώθηκε.") # Rule 5
                    st.session_state.diag_wizard_active = False
                    st.session_state.diag_checklist = []
                    st.session_state.diag_current_step = 0
                    logger.info("Diagnostic wizard cancelled by user.") # Rule 4
        else:
            st.info(get_text('diag_done', lang)) # Rule 5
            if st.button(get_text('diag_btn_new', lang), use_container_width=True): # Rule 5
                st.session_state.diag_wizard_active = False
                st.session_state.diag_checklist = []
                st.session_state.diag_current_step = 0
                st.rerun()