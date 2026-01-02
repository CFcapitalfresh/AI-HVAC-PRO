"""
MODULE: UI CHAT (CONNECTED)
---------------------------
Description: Streamlit UI wrapper for the core AI chat interface.
"""

import streamlit as st
import logging
import io # NEW
from pypdf import PdfReader # NEW: For reading PDF content
from PIL import Image # NEW: For image processing placeholder
from services.chat_session import ChatSessionService
from core.auth_manager import AuthManager
from app_modules.chat_interface import render_chat_interface as core_render_chat_interface
from core.language_pack import get_text
from core.drive_manager import DriveManager # NEW
from services.sync_service import SyncService # NEW

logger = logging.getLogger("Module_Chat_UI")

def render(user):
    """
    Εμφανίζει το UI του AI Chat.
    Φορτώνει τις απαραίτητες υπηρεσίες και καλεί την κεντρική λογική από το app_modules.
    """
    lang = st.session_state.get('lang', 'gr')

    try:
        # Κανόνας 6: Έλεγχος initialization keys
        if 'chat_session_service_instance' not in st.session_state:
            st.session_state.chat_session_service_instance = ChatSessionService()
            if not st.session_state.chat_session_service_instance.ai_engine.model:
                st.error(f"❌ {get_text('general_ui_error', lang).format(error='AI Engine initialization failed within ChatSessionService: ' + (st.session_state.chat_session_service_instance.ai_engine.last_error or 'Unknown Error'))}")
                logger.critical(f"Chat UI: AI Engine failed to initialize via ChatSessionService: {st.session_state.chat_session_service_instance.ai_engine.last_error}")
                return
            logger.info("ChatSessionService and AI Engine initialized for chat.")
        
        chat_service = st.session_state.chat_session_service_instance
        auth_manager_instance = AuthManager()

        st.header("⚡ Mastro Nek AI Assistant")
        
        # NEW: Tabs for different chat modes
        tab_text, tab_voice, tab_upload = st.tabs([
            get_text('chat_tab_text', lang),
            get_text('chat_tab_voice', lang),
            get_text('chat_tab_upload', lang)
        ])

        with tab_text:
            # The existing chat interface logic goes here
            core_render_chat_interface(
                brain_module=chat_service,
                auth_module=auth_manager_instance,
                user_email=user['email']
            )

        with tab_voice:
            st.subheader(get_text('chat_tab_voice', lang))
            st.write(get_text('chat_voice_under_dev', lang))
            # Protected Rule 1: Microphone/Audio button
            if st.button("🎤 Ξεκίνα Φωνητική Εντολή", use_container_width=True):
                st.info(get_text('chat_voice_under_dev', lang))

        with tab_upload:
            st.subheader(get_text('chat_tab_upload', lang))
            st.markdown(get_text('chat_upload_instructions', lang))
            
            uploaded_file = st.file_uploader(
                "Ανεβάστε PDF ή Εικόνα", 
                type=["pdf", "png", "jpg", "jpeg"], 
                key="manual_file_uploader"
            )

            manual_query_text = st.text_area(
                get_text('chat_manual_query_ph', lang),
                key="manual_query_input"
            )
            
            # --- Logic for processing uploaded/loaded manual ---
            processed_manual_content = st.session_state.get('processed_uploaded_manual', None)
            
            if uploaded_file is not None:
                file_type = uploaded_file.type
                file_name = uploaded_file.name

                if file_type == "application/pdf":
                    try:
                        reader = PdfReader(io.BytesIO(uploaded_file.getvalue()))
                        text = ""
                        # Limit text extraction to first few pages
                        for i in range(min(5, len(reader.pages))):
                            page_text = reader.pages[i].extract_text()
                            if page_text:
                                text += page_text + "\n"
                        st.session_state.processed_uploaded_manual = text[:10000] # Limit to 10k chars
                        st.success(f"PDF '{file_name}' διαβάστηκε.")
                        logger.info(f"Processed PDF upload: {file_name}")
                    except Exception as e:
                        st.error(f"❌ Σφάλμα ανάγνωσης PDF: {e}")
                        st.session_state.processed_uploaded_manual = None
                        logger.error(f"Error reading uploaded PDF: {e}", exc_info=True)
                elif file_type.startswith("image/"):
                    st.warning(get_text('chat_image_ocr_warning', lang))
                    # For images, we just pass a placeholder message and rely on Vision capabilities
                    st.session_state.processed_uploaded_manual = f"Εικόνα '{file_name}' ανέβηκε. Το AI θα αναλύσει την εικόνα."
                    logger.info(f"Processed Image upload: {file_name}")
                else:
                    st.warning("Μη υποστηριζόμενος τύπος αρχείου.")
                    st.session_state.processed_uploaded_manual = None
                
                # Clear uploaded_file to prevent reprocessing on rerun
                uploaded_file = None # This won't clear the widget, but stops further processing

            
            # --- Display Processed Content Preview ---
            if st.session_state.get('processed_uploaded_manual'):
                st.markdown(f"**{get_text('chat_uploaded_content_preview', lang)}**")
                st.code(st.session_state.processed_uploaded_manual[:500] + "..." if len(st.session_state.processed_uploaded_manual) > 500 else st.session_state.processed_uploaded_manual, language="markdown")
                if len(st.session_state.processed_uploaded_manual) > 10000:
                    st.warning(get_text('chat_file_too_large', lang))

            col_send, col_load = st.columns(2)

            with col_send:
                if st.button(get_text('chat_send_manual_to_ai', lang), use_container_width=True, disabled=not st.session_state.get('processed_uploaded_manual')):
                    if st.session_state.get('processed_uploaded_manual'):
                        with st.spinner("Στέλνω manual στο AI..."):
                            # Send the processed content along with the manual-specific query
                            ai_response = chat_service.smart_solve(
                                user_query=manual_query_text if manual_query_text else "Ανάλυσε αυτό το manual.",
                                uploaded_pdfs=[], 
                                uploaded_imgs=[], 
                                history=st.session_state.messages, 
                                lang=lang,
                                manual_file_content=st.session_state.processed_uploaded_manual
                            )
                            # Append to main chat history
                            st.session_state.messages.append({"role": "user", "content": f"Ερώτηση με συνημμένο manual: {manual_query_text or 'Ανάλυση manual'}"})
                            st.session_state.messages.append({"role": "assistant", "content": ai_response})
                            st.success("Manual στάλθηκε στο AI!")
                            st.session_state.processed_uploaded_manual = None # Clear after sending
                            st.session_state.manual_query_input = "" # Clear query
                            st.rerun() # Refresh UI

            with col_load:
                if st.button(get_text('chat_load_first_manual', lang), use_container_width=True, disabled=st.session_state.get('processed_uploaded_manual') is not None):
                    with st.spinner("Φόρτωση πρώτου manual από βιβλιοθήκη..."):
                        library_cache = st.session_state.get('library_cache')
                        if library_cache and len(library_cache) > 0:
                            first_manual = library_cache[0]
                            try:
                                manual_content_text = chat_service.get_manual_content_from_id(first_manual['file_id'])
                                if manual_content_text:
                                    st.session_state.processed_uploaded_manual = manual_content_text[:10000] # Limit to 10k chars
                                    st.success(f"Φορτώθηκε το manual: {first_manual['name']}.")
                                    logger.info(f"Loaded first manual from library: {first_manual['name']}")
                                else:
                                    st.warning(get_text('chat_error_loading_manual', lang))
                            except Exception as e:
                                st.error(f"{get_text('chat_error_loading_manual', lang)}: {e}")
                                logger.error(f"Error loading first manual from library: {e}", exc_info=True)
                        else:
                            st.info(get_text('chat_no_manuals_in_lib', lang))
                    st.rerun() # Refresh UI


    except Exception as e:
        logger.error(f"Chat UI: General rendering error in render function for user {user['email']}: {e}", exc_info=True)
        st.error(f"{get_text('general_ui_error', lang).format(error=e)}")