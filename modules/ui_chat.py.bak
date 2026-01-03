"""
MODULE: UI CHAT (INTENT DRIVEN)
-------------------------------
Re-sorts manuals on the fly based on user prompt.
FIXED VERSION: Handles None types, adapts list to single-file AI Engine,
and includes Microphone/Upload buttons, correcting the call to the service layer.
"""
import streamlit as st
import logging
from core.language_pack import get_text
from core.ai_engine import AIEngine # Used here for type hint/info only, call should be to service.
from services.chat_session import ChatSessionService
from core.drive_manager import DriveManager
from core.spy_logger import setup_spy # Import setup_spy for log initialization if needed here

# Ασφαλής εισαγωγή για το μικρόφωνο
try:
    from streamlit_mic_recorder import mic_recorder
except ImportError:
    mic_recorder = None

# Ρύθμιση Logger
logger = logging.getLogger("Module_Chat_UI")

def render(user):
    lang = st.session_state.get('lang', 'gr')
    # Use existing instance if available, otherwise create a new one.
    # We create it here to ensure the logic below uses the service layer.
    session_srv = ChatSessionService()
    drive = DriveManager()

    st.header(get_text('menu_chat', lang))

    # --- DEVICE CONTEXT (SIDEBAR/TOP) ---
    # Κανόνας 5: Χρήση get_text για labels
    # Κανόνας 6: Έλεγχος initialization keys (μέσω των key arguments)
    with st.container(border=True):
        col1, col2, col3 = st.columns([2, 2, 3])
        # Get brands from the service layer, which uses the library cache
        brands = ["-"] + session_srv.get_brands()

        # Labels από το Language Pack
        lbl_brand = get_text('brand_label', lang) or "Brand"
        lbl_model = get_text('model_label', lang) or "Model"

        selected_brand = col1.selectbox(lbl_brand, brands, key="ctx_brand")
        selected_model = col2.text_input(lbl_model, key="ctx_model")

        # 1. Βρες τα manuals για την τρέχουσα επιλογή
        initial_manuals = []
        if selected_brand != "-":
            try:
                # The service layer prioritizes manuals based on current selection.
                # Do not pass a user query yet, just fetch based on brand/model.
                initial_manuals = session_srv.get_prioritized_manuals(selected_brand, selected_model, user_query="")
                if initial_manuals:
                    msg = get_text('manuals_found', lang) or f"Found {len(initial_manuals)}"
                    # Handle message placeholders
                    if "{count}" in msg:
                        col3.success(f"✅ {msg.format(count=len(initial_manuals))}")
                    else:
                        col3.success(f"✅ {msg}")
                else:
                    msg = get_text('no_manuals', lang) or "No manuals found."
                    col3.warning(msg)
            except Exception as e:
                logger.error(f"Error retrieving manuals: {e}", exc_info=True)
                col3.error(get_text('general_ui_error', lang).format(error=str(e)))
        else:
            msg = get_text('select_brand_for_search', lang) or "Select Brand to enable search."
            col3.info(msg)

    st.divider()

    # Init Chat History (Rule 6: Streamlit State)
    if "messages" not in st.session_state: st.session_state.messages = []
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # --- INPUT AREA (TABS) ---
    # Κανόνας 5: Μετάφραση ονομάτων tabs
    t_text = get_text('chat_tab_text', lang) or "⌨️ Text"
    t_voice = get_text('chat_tab_voice', lang) or "🎙️ Voice"
    t_upload = get_text('chat_tab_upload', lang) or "📎 Upload"

    tab_txt, tab_mic, tab_up = st.tabs([t_text, t_voice, t_upload])

    user_prompt = None
    uploaded_pdfs = [] # New list for uploads from tab
    uploaded_imgs = [] # New list for image uploads

    # 1. Text Input (Standard Chat Input)
    with tab_txt:
        ph = get_text('chat_manual_query_ph', lang) or "Tell the AI what to do..." # Use more general prompt placeholder
        prompt = st.chat_input(ph, key="chat_text_in")
        if prompt: user_prompt = prompt

    # 2. Voice Input (Placeholder) (Rule 1: Microphone/Audio)
    with tab_mic:
        st.info(get_text('chat_voice_under_dev', lang))
        if mic_recorder:
            st.write(get_text('voice_input_help', lang) or "Click to record:")
            audio = mic_recorder(start_prompt="🔴 REC", stop_prompt="⏹️ STOP", key='chat_mic_btn')
            if audio:
                st.info(get_text('voice_input_activated', lang) or "Audio received.")
                # Future logic for Speech-to-Text conversion here
        else:
            st.caption("Missing mic recorder library.") # Placeholder for missing library error handling

    # 3. File Upload (for context) (Rule 2: PDF Upload)
    with tab_up:
        st.info(get_text('chat_upload_instructions', lang))
        uploaded_pdfs = st.file_uploader(
            "Upload PDFs", 
            type=["pdf"],
            accept_multiple_files=True,
            key="chat_pdf_upload"
        )
        uploaded_imgs = st.file_uploader(
            "Upload Images", 
            type=["png", "jpg", "jpeg"],
            accept_multiple_files=True,
            key="chat_img_upload"
        )

    # --- PROCESS INPUT AND GENERATE RESPONSE ---
    if user_prompt:
        # A. Εμφάνιση μηνύματος χρήστη
        display_msg = user_prompt
        # Κανόνας 5: Μετάφραση μηνυμάτων
        if uploaded_pdfs:
            display_msg += f"\n\n📎 *{get_text('chat_uploaded_content_preview', lang)} ({len(uploaded_pdfs)} PDFs)*"
        if uploaded_imgs:
            display_msg += f"\n\n📸 *{get_text('chat_uploaded_content_preview', lang)} ({len(uploaded_imgs)} Images)*"

        st.session_state.messages.append({"role": "user", "content": display_msg})
        with st.chat_message("user"): st.markdown(display_msg)

        # B. AI Processing with potential file context (Rule 4: Error Handling)
        with st.chat_message("assistant"):
            response_placeholder = st.empty()
            lbl_analyzing = get_text('analyzing', lang) or "Analyzing data and manuals..."

            # --- STEP 1: Get prioritized manual content from library (if brand selected) ---
            manual_file_content = None
            if selected_brand != "-":
                final_manuals = session_srv.get_prioritized_manuals(selected_brand, selected_model, user_query=user_prompt)
                if final_manuals:
                    top_doc = final_manuals[0] # Take the most relevant document
                    with st.spinner(f"{lbl_analyzing} (Loading manual: {top_doc.get('name', 'N/A')})..."):
                        try:
                            # Use the service layer method to download and extract text
                            # (Rule 3: Modularity - call service, not core logic directly)
                            manual_file_content = session_srv.get_manual_content_from_id(top_doc['file_id'])
                        except Exception as e:
                            logger.error(f"Error loading manual from library for chat: {e}", exc_info=True)
                            st.error(get_text('chat_error_loading_manual', lang))

            # --- STEP 2: Call service layer with all context ---
            with st.spinner(f"{lbl_analyzing} (AI Generation)..."):
                try:
                    resp = session_srv.smart_solve(
                        user_query=user_prompt,
                        uploaded_pdfs=uploaded_pdfs,
                        uploaded_imgs=uploaded_imgs,
                        history=st.session_state.messages[:-1], # Pass history excluding current message
                        lang=lang,
                        manual_file_content=manual_file_content # Pass content of the top library manual
                    )

                    # C. Display response and save to history
                    response_placeholder.markdown(resp)
                    st.session_state.messages.append({"role": "assistant", "content": resp})

                except Exception as e:
                    err_lbl = get_text('ai_engine_error', lang) or "AI Error: {error}"
                    response_placeholder.error(err_lbl.format(error=str(e)))
                    logger.error(f"Chat Error during AI processing: {e}", exc_info=True)
                    # Add error message to history as well
                    st.session_state.messages.append({"role": "assistant", "content": err_lbl.format(error=str(e))})

    # Rule 4: Error handling around mic_recorder import (if not installed)
    if not mic_recorder:
        logger.warning("Streamlit mic_recorder library not found. Voice functionality disabled.")