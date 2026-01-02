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

def status_write(msg, state="loading"):
    """
    Helper function for consistent status messages.
    Returns the Streamlit container if state is "loading", allowing for dynamic updates.
    """
    if state == "loading":
        return st.empty().info(f"⏳ {msg}...")
    elif state == "success":
        st.success(f"✅ {msg}")
    elif state == "error":
        st.error(f"❌ {msg}")
    elif state == "warning":
        st.warning(f"⚠️ {msg}")
    return None # Ensure something is returned for other states too


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
        api_key_placeholder.success(get_text('diag_api_key_found', lang).format(masked_key=mask))
    else:
        api_key_placeholder.error(get_text('diag_api_key_not_found', lang))
        st.info(get_text('diag_api_key_info', lang))
    
    # --- ΕΛΕΓΧΟΣ 2: Σύνδεση με Google AI (Ping Test) ---
    st.markdown(f"**{get_text('diag_ai_conn_test', lang)}**")
    conn_placeholder = status_write(get_text('diag_ai_conn_attempt', lang), state="loading")
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
                conn_placeholder.success(get_text('diag_ai_conn_success', lang).format(count=count))
            except Exception as e:
                # Σφάλμα κατά την καταγραφή μοντέλων (αλλά το AI Engine μπορεί να έχει λειτουργήσει αρχικά)
                conn_placeholder.error(get_text('diag_ai_conn_fail', lang).format(error=str(e)))
                logger.error(f"UI Diagnostics: Google AI connection failed during model listing: {e}", exc_info=True)
        else: 
            # Η αρχικοποίηση του AIEngine απέτυχε
            conn_placeholder.error(get_text('diag_ai_conn_fail', lang).format(error=ai_engine.last_error or 'Unknown AI setup error'))
            logger.error(f"UI Diagnostics: Google AI connection failed during AIEngine setup: {ai_engine.last_error}", exc_info=True)
    else:
        conn_placeholder.warning(get_text('diag_ai_conn_fail', lang).format(error=get_text('diag_api_key_not_found', lang)))
        st.info(get_text('diag_api_key_info', lang))

    # --- ΕΛΕΓΧΟΣ 3: Αυτόματη Επιλογή Μοντέλου ---
    st.markdown(f"**{get_text('diag_ai_model_auto_detect', lang)}**")
    model_sel_placeholder = st.empty()
    if ai_engine.model:
        model_sel_placeholder.info(get_text('diag_ai_model_selected', lang).format(model_name=ai_engine.model.model_name))
    else:
        model_sel_placeholder.error(get_text('diag_ai_model_selection_fail', lang))
        logger.error(f"UI Diagnostics: Failed to select an AI model. Last AIEngine error: {ai_engine.last_error}")

    # --- ΕΛΕΓΧΟΣ 4: Προσομοίωση Απάντησης (Test Run) ---
    st.markdown(f"**{get_text('diag_ai_test_run', lang)}**")
    sim_placeholder = status_write(get_text('diag_ai_test_query', lang).format(model_name=ai_engine.model.model_name if ai_engine.model else 'N/A'), state="loading")
    if ai_engine.model:
        try:
            # ΒΕΛΤΙΩΣΗ: Χρήση του ai_engine.model απευθείας
            response = ai_engine.model.generate_content("Γράψε τη λέξη 'OK'.", safety_settings={'HARASSMENT': 'BLOCK_NONE', 'HATE_SPEECH': 'BLOCK_NONE', 'SEXUALLY_EXPLICIT': 'BLOCK_NONE', 'DANGEROUS_CONTENT': 'BLOCK_NONE'})
            
            if response.text:
                sim_placeholder.success(get_text('diag_ai_test_resp_success', lang).format(response_text=response.text.strip()))
            else:
                sim_placeholder.warning(get_text('diag_ai_test_resp_empty', lang))
        except Exception as e:
            error_msg = str(e)
            sim_placeholder.error(get_text('diag_ai_critical_error', lang).format(error=error_msg))
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
        sim_placeholder.warning(get_text('diag_ai_critical_error', lang).format(error="AI model not initialized or API Key missing."))

    # --- ΕΛΕΓΧΟΣ 5: PDF Engine ---
    st.markdown(f"**5. {get_text('menu_library', lang)} Engine**") # Επαναχρησιμοποίηση κλειδιού menu_library για το context του PDF
    pdf_placeholder = st.empty()
    try:
        buffer = BytesIO()
        w = pypdf.PdfWriter()
        w.add_blank_page(width=100, height=100)
        w.write(buffer)
        buffer.seek(0)
        
        r = pypdf.PdfReader(buffer)
        if len(r.pages) > 0:
            pdf_placeholder.success(f"{get_text('menu_library', lang)} engine works correctly.") # Συγκεκριμένο μήνυμα επιτυχίας
        else:
            pdf_placeholder.error(f"Problem with {get_text('menu_library', lang)} engine.") # Συγκεκριμένο μήνυμα σφάλματος
    except Exception as e:
        pdf_placeholder.error(f"PDF engine error: {e}")
        logger.error(f"UI Diagnostics: PDF engine check failed: {e}", exc_info=True)

    st.divider()
    st.info(get_text('diag_complete_summary', lang)) # ΝΕΟ: Συνοπτικό μήνυμα
    st.divider()
    # --- ΤΕΛΟΣ ΕΝΟΤΗΤΑΣ ΒΑΘΙΑΣ ΑΝΑΛΥΣΗΣ ---


    # --- Λογική Αυτόματης Συμπλήρωσης (Κληρονομιά από Chat) ---
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
                            # ΒΕΛΤΙΩΣΗ: Χρήση της ήδη αρχικοποιημένης παρουσίας της υπηρεσίας
                            plan = diag_service.generate_checklist(error_input, manual_context, lang=lang)
                            
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