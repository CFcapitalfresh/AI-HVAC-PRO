"""
MODULE: UI CHAT (INTENT DRIVEN)
-------------------------------
Description: Streamlit UI module for the AI Chat Assistant.
Integrates text, voice, and file uploads with the core AI service layer,
providing context-aware responses based on selected manuals and user input.

Architectural Notes:
- Adheres to Modularity Rule (Rule 3) by delegating business logic to ChatSessionService.
- Implements Microphone (Rule 1) and PDF Upload (Rule 2) via UI tabs.
- Uses Streamlit State (Rule 6) for chat history and context.
- Uses get_text (Rule 5) for multilingual support.
"""

import streamlit as st
import logging
from typing import List, Dict, Any, Optional

from core.language_pack import get_text
from core.ai_engine import AIEngine # Used here for type hint/info only
from services.chat_session import ChatSessionService
from core.drive_manager import DriveManager # For potential file operations if needed

# Import Speech-to-Text library with graceful error handling (Rule 1)
try:
    from streamlit_mic_recorder import mic_recorder
except ImportError:
    mic_recorder = None

# Ρύθμιση Logger για το Module
logger = logging.getLogger("Module_Chat_UI")

def render(user):
    lang = st.session_state.get('lang', 'gr')
    # Use existing instance if available, otherwise create a new one.
    session_srv = ChatSessionService()

    st.header(get_text('menu_chat', lang))

    # --- DEVICE CONTEXT (SIDEBAR/TOP) ---
    # Κανόνας 5: Χρήση get_text για labels
    # Κανόνας 6: Έλεγχος initialization keys (μέσω των key arguments)
    with st.container(border=True):
        col1, col2, col3 = st.columns([2, 2, 3])
        
        # Get brands from the service layer, which uses the library cache
        # If library_cache not loaded, this will return empty list.
        brands = ["-"] + session_srv.get_brands()

        # Labels από το Language Pack
        lbl_brand = get_text('brand_label', lang) or "Brand"
        lbl_model = get_text('model_label', lang) or "Model"

        # Store selected brand and model in session state for cross-session access
        selected_brand = col1.selectbox(lbl_brand, brands, key="ctx_brand")
        selected_model = col2.text_input(lbl_model, key="ctx_model")

        # 1. Βρες τα manuals για την τρέχουσα επιλογή
        # The result from get_prioritized_manuals is used in the processing logic below,
        # but here we display a summary in the UI based on the selection.
        initial_manuals = []
        if selected_brand != "-":
            try:
                # The service layer prioritizes manuals based on current selection.
                # Do not pass a user query yet, just fetch based on brand/model.
                initial_manuals = session_srv.get_prioritized_manuals(selected_brand, selected_model, user_query="")
                if initial_manuals:
                    msg = get_text('manuals_found', lang) or f"Found {len(initial_manuals)}"
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
    # Rule 5: Translation of tab names
    t_text = get_text('tab_text', lang) or "⌨️ Text"
    t_voice = get_text('tab_voice', lang) or "🎙️ Voice"
    t_upload = get_text('tab_upload', lang) or "📎 Upload"

    # Store uploaded files in session state (Rule 6) or temporary variables
    # We use temporary variables to only process new uploads when a prompt is sent.
    uploaded_pdfs = []
    uploaded_imgs = []

    # Use a container for input elements to keep them organized, or just use tabs directly.
    # We'll use tabs for a cleaner UI separation.
    tab_txt, tab_mic, tab_up = st.tabs([t_text, t_voice, t_upload])

    # 1. Text Input (Standard Chat Input)
    with tab_txt:
        # Placeholder for the chat input (Rule 5)
        ph = get_text('chat_input_placeholder', lang) or "Describe the issue or error code..."
        user_prompt = st.chat_input(ph, key="chat_text_in")

    # 2. Voice Input (Placeholder) (Rule 1: Microphone/Audio)
    with tab_mic:
        st.info(get_text('chat_voice_under_dev', lang))
        # Add mic recorder button placeholder (Rule 1)
        if mic_recorder:
            st.caption(get_text('voice_input_help', lang))
            audio = mic_recorder(start_prompt="🔴 REC", stop_prompt="⏹️ STOP", key='chat_mic_btn')
            if audio:
                st.info(get_text('voice_input_activated', lang))
                # Future logic for Speech-to-Text conversion here
        else:
            st.caption("Missing mic recorder library. Voice functionality disabled.")

    # 3. File Upload (for context) (Rule 2: PDF Upload)
    with tab_up:
        st.info(get_text('upload_manual_help', lang))
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
        if uploaded_pdfs or uploaded_imgs:
            st.success(f"Files ready to send: {len(uploaded_pdfs) + len(uploaded_imgs)}")


    # --- PROCESS INPUT AND GENERATE RESPONSE ---
    # Trigger AI response when user prompt or uploaded files exist.
    if user_prompt:
        # A. Εμφάνιση μηνύματος χρήστη
        display_msg = user_prompt
        if uploaded_pdfs:
            # Rule 5: Use translated labels
            display_msg += f"\n\n📎 *{get_text('chat_uploaded_content_preview', lang)} ({len(uploaded_pdfs)} PDFs)*"
        if uploaded_imgs:
            # Rule 5: Use translated labels
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
                    # Rule 3: Modularity - call service layer
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
                    # Rule 4: Error Handling and Rule 5: Language Support
                    err_lbl = get_text('ai_engine_error', lang) or "AI Error: {error}"
                    response_placeholder.error(err_lbl.format(error=str(e)))
                    logger.error(f"Chat Error during AI processing: {e}", exc_info=True)
                    # Add error message to history as well
                    st.session_state.messages.append({"role": "assistant", "content": err_lbl.format(error=str(e))})

    # Rule 4: Error handling around mic_recorder import (if not installed)
    if not mic_recorder:
        logger.warning("Streamlit mic_recorder library not found. Voice functionality disabled.")