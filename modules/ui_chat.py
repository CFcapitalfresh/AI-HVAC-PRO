import streamlit as st
from core.language_pack import get_text
from core.ai_engine import AIEngine
from services.sync_service import SyncService

def render(user):
    lang = st.session_state.get('lang', 'gr')

    # --- 1. HEADER & NEW CHAT BUTTON ---
    # Χρησιμοποιούμε κολώνες για να βάλουμε το κουμπί δίπλα στον τίτλο
    col_head, col_btn = st.columns([3, 1])
    
    with col_head:
        st.header(f"{get_text('menu_chat', lang)}")
    
    with col_btn:
        # Το κουμπί ΝΕΑ ΣΥΝΟΜΙΛΙΑ ψηλά και καθαρά
        if st.button(f"➕ {get_text('chat_new_btn', lang)}", type="primary", use_container_width=True):
            st.session_state.messages = []
            st.session_state.current_context_files = [] 
            st.rerun()

    # --- 2. INIT ENGINE & LIBRARY ---
    brain = AIEngine()
    
    if 'library_cache' not in st.session_state or not st.session_state.library_cache:
        try:
            syncer = SyncService()
            st.session_state.library_cache = syncer.scan_library()
        except:
            st.session_state.library_cache = []

    if "messages" not in st.session_state: 
        st.session_state.messages = []
    
    # --- 3. DISPLAY HISTORY ---
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg["role"] == "assistant" and "sources" in msg:
                with st.expander("📚 Sources"):
                    for src in msg["sources"]:
                        link = src.get('link', '')
                        if link:
                            st.markdown(f"📄 **[{src['name']}]({link})**")
                        else:
                            st.markdown(f"📄 **{src['name']}**")

    # --- 4. INPUT AREA ---
    prompt = st.chat_input(get_text('chat_placeholder', lang))
    
    if prompt:
        # A. User Msg
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
        
        # B. Context Search
        found_files = []
        keywords = prompt.lower().split()
        library = st.session_state.library_cache
        
        if library:
            for item in library:
                matches = sum(1 for word in keywords if word in item['name'].lower() and len(word) > 2)
                if matches >= 1: found_files.append(item)
        
        relevant_files = found_files[:3]
        file_names_str = ", ".join([f['name'] for f in relevant_files])

        # C. AI Response
        with st.chat_message("assistant"):
            with st.spinner(get_text('chat_thinking', lang)):
                response_text = brain.get_chat_response(
                    st.session_state.messages, 
                    context_files=file_names_str,
                    lang=lang
                )
                st.markdown(response_text)
                
                if relevant_files:
                    with st.expander("📚 Context Files"):
                        for f in relevant_files:
                            link = f.get('link', '')
                            if link:
                                st.markdown(f"📄 **[{f['name']}]({link})**")
                            else:
                                st.markdown(f"📄 **{f['name']}**")

        # D. Save
        st.session_state.messages.append({
            "role": "assistant", 
            "content": response_text,
            "sources": relevant_files 
        })