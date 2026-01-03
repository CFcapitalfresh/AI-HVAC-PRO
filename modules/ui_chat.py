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
from services.chat_session import ChatSessionService # Rule 3: Use service layer for business logic.

# Import Speech-to-Text library with graceful error handling (Rule 1)
try:
    from streamlit_mic_recorder import mic_recorder
    # Placeholder for actual STT service integration
    # from some_stt_service import SpeechToTextService 
    # stt_service = SpeechToTextService()
except ImportError:
    mic_recorder = None
    # stt_service = None

# Ρύθμιση Logger για το Module (Rule 4)
logger = logging.getLogger("Module_Chat_UI")

def render(user):
    lang = st.session_state.get('lang', 'gr')
    # Use existing instance if available, otherwise create a new one. (Rule 6)
    if 'chat_session_service' not in st.session_state:
        st.session_state.chat_session_service = ChatSessionService()
    session_srv = st.session_state.chat_session_service

    st.header(get_text('menu_chat', lang))

    # --- DEVICE CONTEXT (SIDEBAR/TOP) ---
    # Κανόνας 5: Χρήση get_text για labels
    # Κανόνας 6: Έλεγχος initialization keys (μέσω των key arguments)
    with st.container(border=True):
        col1, col2, col3 = st.columns([2, 2, 3])
        
        # Get brands from the service layer, which uses the library cache
        brands = ["-"] + session_srv.get_brands() # Ensures initial list even if empty

        # Labels από το Language Pack
        lbl_brand = get_text('brand_label', lang)
        lbl_model = get_text('model_label', lang)

        # Store selected brand and model in session state for cross-session access
        selected_brand = col1.selectbox(lbl_brand, brands, key="ctx_brand")
        selected_model = col2.text_input(lbl_model, key="ctx_model")

        # 1. Βρες τα manuals για την τρέχουσα επιλογή
        initial_manuals = []
        if selected_brand != "-":
            try:
                # The service layer prioritizes manuals based on current selection.
                initial_manuals = session_srv.get_prioritized_manuals(selected_brand, selected_model, user_query="")
                if initial_manuals:
                    msg = get_text('manuals_found', lang)
                    col3.success(f"✅ {msg.format(count=len(initial_manuals))}")
                else:
                    msg = get_text('no_manuals', lang)
                    col3.warning(msg)
            except Exception as e:
                logger.error(f"Error retrieving manuals in UI: {e}", exc_info=True) # Rule 4: Logging error
                col3.error(get_text('general_ui_error', lang).format(error=str(e)))
        else:
            msg = get_text('select_brand_for_search', lang)
            col3.info(msg)

    st.divider()

    # Init Chat History (Rule 6: Streamlit State)
    if "messages" not in st.session_state: st.session_state.messages = []
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # --- INPUT AREA (TABS) ---
    # Rule 5: Translation of tab names
    t_text = get_text('tab_text', lang)
    t_voice = get_text('tab_voice', lang)
    t_upload = get_text('tab_upload', lang)
    
    tab_txt, tab_mic, tab_up = st.tabs([t_text, t_voice, t_upload])
    
    user_prompt = None
    uploaded_files_for_ai = [] # List to hold file-like objects for AI processing

    # 1. Text Input
    with tab_txt:
        ph = get_text('chat_input_placeholder', lang)
        prompt_from_text = st.chat_input(ph, key="chat_text_in")
        if prompt_from_text: user_prompt = prompt_from_text

    # 2. Voice Input (Rule 1)
    with tab_mic:
        if mic_recorder:
            st.write(get_text('voice_input_help', lang))
            audio_bytes = mic_recorder(start_prompt="🔴 REC", stop_prompt="⏹️ STOP", key='chat_mic_btn')
            if audio_bytes:
                st.info(get_text('voice_stt_processing', lang))
                try:
                    # Placeholder for actual Speech-to-Text integration
                    # For demonstration, we simulate an STT response.
                    simulated_stt_text = "Δεν ψύχει το κλιματιστικό Daikin" # Replace with actual STT output
                    # if stt_service:
                    #    user_prompt = stt_service.convert(audio_bytes)
                    # else:
                    #    user_prompt = simulated_stt_text
                    user_prompt = simulated_stt_text # Assign the recognized text to user_prompt
                    logger.info(f"STT recognized: '{user_prompt}'")
                    # No rerun needed here, the prompt will be processed in the main if user_prompt block
                except Exception as e:
                    st.error(get_text('voice_stt_error', lang).format(error=str(e)))
                    logger.error(f"Error during STT processing in chat: {e}", exc_info=True)
        else:
            st.button("🎤 (STT Unavailable)", key="mic_unavailable_chat")
            st.warning("Speech-to-Text library not installed. Run `pip install streamlit-mic-recorder`.")

    # 3. File Upload (Rule 2)
    with tab_up:
        uploaded_pdfs = st.file_uploader(get_text('upload_manual_label', lang) + " (PDFs)", type=["pdf"], accept_multiple_files=True, key="chat_pdf_uploader")
        uploaded_imgs = st.file_uploader(get_text('upload_manual_label', lang) + " (Images)", type=["png", "jpg", "jpeg"], accept_multiple_files=True, key="chat_img_uploader")
        
        if uploaded_pdfs:
            for uploaded_file in uploaded_pdfs:
                uploaded_files_for_ai.append(uploaded_file)
            st.success(f"📎 Έτοιμα για αποστολή: {len(uploaded_pdfs)} PDF αρχεία")
        if uploaded_imgs:
            for uploaded_file in uploaded_imgs:
                uploaded_files_for_ai.append(uploaded_file)
            st.success(f"📸 Έτοιμα για αποστολή: {len(uploaded_imgs)} Εικόνες")

    # 4. Λογική Επεξεργασίας Μηνύματος (Triggered by any user input)
    if user_prompt or uploaded_files_for_ai:
        display_msg = user_prompt if user_prompt else ""
        if uploaded_files_for_ai:
            file_names = ", ".join([f.name for f in uploaded_files_for_ai])
            display_msg += f"\n\n📎 *{get_text('processing_uploaded_file', lang).format(name=file_names)}*"
        
        st.session_state.messages.append({"role": "user", "content": display_msg})
        with st.chat_message("user"):
            st.markdown(display_msg)
            # You might want to display thumbnails of uploaded files here as well

        with st.chat_message("assistant"):
            response_placeholder = st.empty()
            full_response = ""
            
            try:
                with st.spinner(get_text('analyzing', lang)):
                    # Rule 3: Delegate processing to the ChatSessionService
                    full_response = session_srv.smart_solve(
                        user_query=user_prompt if user_prompt else "", # Pass empty string if no text prompt
                        selected_brand=selected_brand,
                        selected_model=selected_model,
                        uploaded_files=uploaded_files_for_ai, # Pass the list of uploaded files
                        history=st.session_state.messages[:-1], # Pass history without the latest user message
                        lang=lang,
                        user_email=user['email']
                    )

                response_placeholder.markdown(full_response)
                st.session_state.messages.append({"role": "assistant", "content": full_response})

            except Exception as e:
                error_msg = f"⚠️ {get_text('ai_engine_error', lang)} {str(e)}"
                response_placeholder.error(error_msg)
                logger.error(f"Chat AI response generation error: {e}", exc_info=True)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})
        
        # Clear uploaded files after processing to prevent re-upload on rerun
        # This is handled by Streamlit itself for `st.file_uploader` by clearing it on re-run
        # but the prompt might still be active. Re-run to ensure clean state.
        st.rerun()