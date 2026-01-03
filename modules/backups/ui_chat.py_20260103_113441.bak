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

# Ρύθμιση Logger για το Module (Rule 4)
logger = logging.getLogger("Module_Chat_UI")

def render(user):
    lang = st.session_state.get('lang', 'gr')
    # Use existing instance if available, otherwise create a new one.
    # Rule 3: Modularity - Use service layer for business logic.
    session_srv = ChatSessionService()
    drive_manager = DriveManager() # Instantiate DriveManager for file uploads.

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
        lbl_brand = get_text('brand_label', lang)
        lbl_model = get_text('model_label', lang)

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
                    msg = get_text('manuals_found', lang)
                    # Rule 5: Correct use of format for translations with placeholders
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
    uploaded_files_context = [] # List to hold file-like objects for AI

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
                st.info(get_text('voice_input_activated', lang))
                # Here, integrate Speech-to-Text service. For now, it's a placeholder.
                # Example: recognized_text = speech_to_text_service.convert(audio_bytes)
                # For demo, just use a placeholder text
                user_prompt = f"Από φωνητική εντολή: Το πρόβλημα είναι..." # Placeholder
                st.session_state.messages.append({"role": "user", "content": f"🎤 {user_prompt}"})
                st.rerun() # Trigger a rerun to process the prompt immediately
        else:
            st.warning("🎧 Η βιβλιοθήκη 'streamlit_mic_recorder' δεν βρέθηκε. Εγκαταστήστε την: `pip install streamlit-mic-recorder`.")

    # 3. File Upload (Rule 2)
    with tab_up:
        lbl_up = get_text('upload_files_label', lang)
        help_up = get_text('upload_manual_help', lang)
        uploaded_pdfs = st.file_uploader(lbl_up + " (PDF)", type=["pdf"], accept_multiple_files=True, key="chat_pdf_uploader_tab", help=help_up)
        uploaded_imgs = st.file_uploader(lbl_up + " (Εικόνες)", type=["png", "jpg", "jpeg"], accept_multiple_files=True, key="chat_img_uploader_tab", help=help_up)

        if uploaded_pdfs or uploaded_imgs:
            st.success(f"Έτοιμα για αποστολή: {len(uploaded_pdfs or []) + len(uploaded_imgs or [])} αρχεία")
            # If a prompt is also entered, these files will be processed with it.
            # If only files are uploaded, a default prompt might be needed, or we wait for user to type.
            # For now, we assume user will also type a prompt to go with files or re-rerun.
            
            # Convert uploaded files to file-like objects for AI processing
            for file in (uploaded_pdfs or []):
                uploaded_files_context.append(file)
            for file in (uploaded_imgs or []):
                uploaded_files_context.append(file)

    # --- PROCESS USER INPUT & AI RESPONSE ---
    if user_prompt or uploaded_files_context:
        # Display user message
        st.session_state.messages.append({"role": "user", "content": user_prompt or "Επισύναψη αρχείων."})
        with st.chat_message("user"):
            st.markdown(user_prompt or "Επισύναψη αρχείων.")
            if uploaded_files_context:
                st.markdown(f"*📎 Επισυνάφθηκαν {len(uploaded_files_context)} αρχεία για ανάλυση.*")

        # Prepare context manuals (if brand/model selected)
        context_manuals_text: List[str] = []
        if selected_brand != "-" and (user_prompt or uploaded_files_context): # Only fetch if there's a prompt
            try:
                # Fetch top N manuals based on current context and user query
                prioritized_manual_items = session_srv.get_prioritized_manuals(selected_brand, selected_model, user_prompt or "")
                
                # Limit to top N manuals to avoid exceeding token limits
                MAX_MANUALS_FOR_CONTEXT = 3 
                for i, manual_item in enumerate(prioritized_manual_items[:MAX_MANUALS_FOR_CONTEXT]):
                    manual_file_content = session_srv.get_manual_text_content(manual_item['file_id'])
                    if manual_file_content:
                        context_manuals_text.append(manual_file_content)
                        logger.info(f"Adding manual '{manual_item['original_name']}' to AI context.")
                    else:
                        logger.warning(f"Could not retrieve content for manual: {manual_item['original_name']}")
                if context_manuals_text:
                    st.session_state.messages.append({"role": "assistant", "content": get_text('studying_sources', lang).format(count=len(context_manuals_text))})
                    with st.chat_message("assistant"):
                        st.markdown(get_text('studying_sources', lang).format(count=len(context_manuals_text)))
            except Exception as e:
                logger.error(f"Error preparing manual context: {e}", exc_info=True)
                st.error(get_text('manual_retrieval_error', lang).format(error=str(e)))
        
        # Get AI response
        with st.chat_message("assistant"):
            response_placeholder = st.empty()
            full_response = ""
            try:
                with st.spinner(get_text('analyzing', lang)):
                    # Delegate AI call to ChatSessionService (Rule 3)
                    full_response = session_srv.get_ai_response(
                        user_prompt=user_prompt,
                        uploaded_files=uploaded_files_context,
                        manual_contexts=context_manuals_text,
                        chat_history=st.session_state.messages[:-1], # Exclude current user prompt
                        lang=lang
                    )
                
                response_placeholder.markdown(full_response)
                st.session_state.messages.append({"role": "assistant", "content": full_response})
                logger.info(f"AI responded to '{user['email']}' with: {full_response[:50]}...")

            except Exception as e:
                error_msg = f"⚠️ {get_text('ai_engine_error', lang)} {e}"
                response_placeholder.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})
                logger.error(f"AI response generation failed for user {user['email']}: {e}", exc_info=True)
                
        # Clear uploaded files from session state after processing
        if 'chat_pdf_uploader_tab' in st.session_state:
            del st.session_state['chat_pdf_uploader_tab']
        if 'chat_img_uploader_tab' in st.session_state:
            del st.session_state['chat_img_uploader_tab']
        st.rerun() # Rerun to clear input fields and uploaded file widgets