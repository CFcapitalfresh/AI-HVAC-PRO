"""
MODULE: UI CHAT (INTENT DRIVEN)
-------------------------------
Re-sorts manuals on the fly based on user prompt.
FIXED VERSION: Handles None types, adapts list to single-file AI Engine,
and includes Microphone/Upload buttons.
"""
import streamlit as st
import logging
from core.language_pack import get_text
from core.ai_engine import AIEngine
from services.chat_session import ChatSessionService
from core.drive_manager import DriveManager
from core.spy_logger import SpyLogger

# Ασφαλής εισαγωγή για το μικρόφωνο
try:
    from streamlit_mic_recorder import mic_recorder
except ImportError:
    mic_recorder = None

# Ρύθμιση Logger
logger = logging.getLogger(__name__)

def render(user):
    lang = st.session_state.get('lang', 'gr')
    session_srv = ChatSessionService()
    drive = DriveManager()
    spy_logger = SpyLogger()

    # --- DEVICE CONTEXT (SIDEBAR/TOP) ---
    with st.container(border=True):
        c1, c2, c3 = st.columns([2, 2, 3])
        brands = ["-"] + session_srv.get_brands()
        
        # Labels από το Language Pack (με fallback)
        lbl_brand = get_text('brand_label', lang) or "Brand"
        lbl_model = get_text('model_label', lang) or "Model"
        
        selected_brand = c1.selectbox(lbl_brand, brands, key="ctx_brand")
        selected_model = c2.text_input(lbl_model, key="ctx_model")
        
        # Αρχική λίστα (χωρίς ερώτηση ακόμα)
        initial_manuals = []
        if selected_brand != "-":
            try:
                initial_manuals = session_srv.get_prioritized_manuals(selected_brand, selected_model, user_query="")
                if initial_manuals:
                    msg = get_text('manuals_found', lang) or f"Found {len(initial_manuals)}"
                    # Αν το msg έχει placeholder, το κάνουμε format
                    if "{count}" in msg:
                        c3.success(f"✅ {msg.format(count=len(initial_manuals))}")
                    else:
                        c3.success(f"✅ {msg}")
                else:
                    msg = get_text('no_manuals', lang) or "No manuals"
                    c3.warning(msg)
            except Exception as e:
                logger.error(f"Error retrieving manuals: {e}")
                c3.error("Error loading manuals")
        else:
            msg = get_text('select_brand_for_search', lang) or "Select Brand"
            c3.info(msg)

    st.divider()
    
    # Init Chat History
    if "messages" not in st.session_state: st.session_state.messages = []
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # --- INPUT AREA (TABS) ---
    # Δημιουργία Tabs για Κείμενο, Φωνή, Upload
    t_text = get_text('tab_text', lang) or "⌨️ Text"
    t_voice = get_text('tab_voice', lang) or "🎙️ Voice"
    t_upload = get_text('tab_upload', lang) or "📎 Upload"
    
    tab_txt, tab_mic, tab_up = st.tabs([t_text, t_voice, t_upload])
    
    user_input = None
    uploaded_context = None

    # 1. Text Input
    with tab_txt:
        ph = get_text('chat_input_placeholder', lang) or "Describe the issue..."
        prompt = st.chat_input(ph, key="chat_text_in")
        if prompt: user_input = prompt

    # 2. Voice Input
    with tab_mic:
        if mic_recorder:
            st.write(get_text('voice_input_help', lang) or "Click to record:")
            audio = mic_recorder(start_prompt="🔴 REC", stop_prompt="⏹️ STOP", key='chat_mic_btn')
            if audio:
                st.info(get_text('voice_input_activated', lang) or "Audio received.")
                # Εδώ μελλοντικά θα μπει το Speech-to-Text
        else:
            st.warning("Mic recorder library missing.")

    # 3. File Upload
    with tab_up:
        lbl_up = get_text('upload_manual_label', lang) or "Upload File"
        upl = st.file_uploader(
            lbl_up, 
            type=["pdf", "png", "jpg", "jpeg"],
            key="chat_file_up"
        )
        if upl: 
            uploaded_context = upl
            st.success(f"📎 {upl.name}")

    # --- PROCESS INPUT ---
    if user_input:
        # Εμφάνιση μηνύματος χρήστη
        display_msg = user_input
        if uploaded_context:
            proc_msg = get_text('processing_uploaded_file', lang) or "File: {name}"
            display_msg += f"\n\n📎 *{proc_msg.format(name=uploaded_context.name)}*"
        
        st.session_state.messages.append({"role": "user", "content": display_msg})
        with st.chat_message("user"): st.markdown(display_msg)

        with st.chat_message("assistant"):
            brain = AIEngine()
            
            # Α. Ανάκτηση Manuals από βάση
            final_manuals = []
            if selected_brand != "-":
                try:
                    final_manuals = session_srv.get_prioritized_manuals(selected_brand, selected_model, user_query=user_input)
                except Exception as e:
                    logger.error(f"Manual sort error: {e}")
            
            # Β. Προετοιμασία Δεδομένων (FIXED)
            primary_data = None
            primary_name = ""
            
            # Περίπτωση 1: Upload χρήστη (Έχει προτεραιότητα)
            if uploaded_context:
                try:
                    primary_data = uploaded_context.getvalue()
                    primary_name = f"Upload: {uploaded_context.name}"
                except: pass
            
            # Περίπτωση 2: Manual συστήματος (Αν δεν υπάρχει upload)
            elif final_manuals:
                top_doc = final_manuals[0] # Παίρνουμε το 1ο (καλύτερο)
                lbl_study = get_text('studying_sources', lang) or "Studying..."
                if "{count}" in lbl_study: lbl_study = lbl_study.format(count=1)
                
                with st.spinner(lbl_study):
                    try:
                        stream = drive.download_file_content(top_doc['file_id'])
                        if stream:
                            primary_data = stream.read()
                            primary_name = top_doc['name']
                    except Exception as e:
                        logger.error(f"Download error: {e}")

            # Γ. Κλήση AI (Fixed Args: manual_file instead of list)
            lbl_analyzing = get_text('analyzing', lang) or "Analyzing..."
            with st.spinner(lbl_analyzing):
                try:
                    resp = brain.get_chat_response(
                        st.session_state.messages,
                        manual_file=primary_data,  # <--- Η ΣΗΜΑΝΤΙΚΗ ΑΛΛΑΓΗ (Bytes)
                        manual_name=primary_name,
                        lang=lang
                    )
                    st.markdown(resp)
                    st.session_state.messages.append({"role": "assistant", "content": resp})
                except Exception as e:
                    err_lbl = get_text('ai_engine_error', lang) or "AI Error: {error}"
                    st.error(err_lbl.format(error=str(e)))
                    spy_logger.log_error(f"AI Error: {e}", component="UI_CHAT")