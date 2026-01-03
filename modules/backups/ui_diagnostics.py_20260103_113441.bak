import streamlit as st
import logging
import time

# NEW Imports for AI System Status checks
import google.generativeai as genai # Still needed for list_models and GenerativeModel
import pypdf # For PDF engine check, mirroring diagnose.py
from io import BytesIO

from services.diagnostics_logic import DiagnosticsService # IMPORT THIS
from core.language_pack import get_text


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
    api_key = ai_engine.api_key # Λήψη API key απευθείας από το AIEngine

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
        logger.error(f"UI Diagnostics: PDF Engine check failed: {e}", exc_info=True)

    # --- ΕΛΕΓΧΟΣ 4: Προσομοίωση Απάντησης AI ---
    st.markdown(f"**{get_text('diag_simulation_title', lang)}**")
    sim_placeholder = st.empty()
    if ai_engine.model:
        status_write(sim_placeholder, get_text('diag_simulation_prompt', lang), "loading")
        try:
            # Χρησιμοποιούμε μια απλή ερώτηση για δοκιμή
            test_response = ai_engine.get_chat_response(content_parts=[{"text": "Hello, are you online?"}], lang=lang)
            if "offline" in test_response.lower() or ai_engine.last_error: # Check if the AI itself reported offline
                 status_write(sim_placeholder, get_text('diag_simulation_fail', lang).format(error=ai_engine.last_error or test_response), "error")
            else:
                status_write(sim_placeholder, get_text('diag_simulation_success', lang).format(response_start=test_response[:50]), "success")
        except Exception as e:
            status_write(sim_placeholder, get_text('diag_simulation_fail', lang).format(error=str(e)), "error")
            logger.error(f"UI Diagnostics: AI response simulation failed: {e}", exc_info=True)
    else:
        status_write(sim_placeholder, get_text('diag_simulation_fail', lang).format(error=ai_engine.last_error or 'AI model not initialized'), "error")
    
    st.divider()

    # --- AI DIAGNOSTIC WIZARD (EXISTING LOGIC) ---
    st.subheader(get_text('diag_title', lang)) # Re-use the main title for consistency

    if "diag_plan" not in st.session_state:
        st.session_state.diag_plan = None
        st.session_state.current_step = 0

    problem_description = st.text_area(get_text('diag_input_ph', lang), key="diag_input_problem")

    if st.button(get_text('diag_btn_create', lang), type="primary", use_container_width=True):
        if problem_description:
            with st.spinner(get_text('diag_spinner', lang)):
                try:
                    # Use the DiagnosticsService to generate the checklist
                    st.session_state.diag_plan = diag_service.generate_checklist(problem_description, lang=lang)
                    st.session_state.current_step = 0
                except Exception as e:
                    logger.error(f"Error generating diagnosis plan: {e}", exc_info=True)
                    st.error(f"{get_text('diag_fail', lang)}: {e}")
        else:
            st.warning("Παρακαλώ περιγράψτε το πρόβλημα.")

    if st.session_state.diag_plan and st.session_state.diag_plan.get('steps'):
        plan = st.session_state.diag_plan['steps']
        current_step_idx = st.session_state.current_step

        if current_step_idx < len(plan):
            step = plan[current_step_idx]
            st.markdown(f"### {get_text('diag_step', lang)} {current_step_idx + 1} {get_text('diag_of', lang)} {len(plan)}")
            st.markdown(f"**{get_text('diag_action', lang)}** {step.get('action', 'N/A')}")
            st.markdown(f"**{get_text('diag_question', lang)}** {step.get('question', 'N/A')}")
            if step.get('tip'):
                st.info(f"**{get_text('diag_tip', lang)}** {step['tip']}")

            col1, col2 = st.columns(2)
            with col1:
                if st.button(get_text('diag_yes', lang), use_container_width=True, key=f"diag_yes_{current_step_idx}"):
                    st.session_state.current_step += 1
                    st.rerun()
            with col2:
                if st.button(get_text('diag_no', lang), use_container_width=True, key=f"diag_no_{current_step_idx}"):
                    st.session_state.current_step += 1
                    st.rerun()
        else:
            st.success(get_text('diag_done', lang))
            if st.button(get_text('diag_btn_new', lang), use_container_width=True):
                st.session_state.diag_plan = None
                st.session_state.current_step = 0
                st.rerun()