import streamlit as st
from core.language_pack import get_text
from core.ai_engine import AIEngine
from services.sync_service import SyncService

def render(user):
    # --- 1. HEADER ---
    # Πρόσθεσα το "v2.0" για να επιβεβαιώσουμε ότι πήρε το νέο αρχείο
    st.header(f"{get_text('menu_chat', st.session_state.lang)} v2.0")

    # --- 2. SIDEBAR CONTROLS ---
    with st.sidebar:
        st.divider()
        st.markdown("### 🛠️ Εργαλεία")
        if st.button("🧹 Νέο Πρόβλημα / Reset", use_container_width=True):
            st.session_state.messages = []
            st.session_state.current_context_files = [] 
            st.rerun()

    # --- 3. INIT ENGINE ---
    brain = AIEngine()
    
    # Φόρτωση βιβλιοθήκης (Ασφαλής έλεγχος)
    if 'library_cache' not in st.session_state or not st.session_state.library_cache:
        try:
            syncer = SyncService()
            st.session_state.library_cache = syncer.scan_library()
        except:
            st.session_state.library_cache = []

    # Init History
    if "messages" not in st.session_state: st.session_state.messages = []
    
    # --- 4. DISPLAY HISTORY ---
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            
            if msg["role"] == "assistant" and "sources" in msg:
                with st.expander("📚 Πηγές"):
                    for src in msg["sources"]:
                        if src.get('link'):
                            st.markdown(f"📄 **[{src['name']}]({src['link']})**")
                        else:
                            st.markdown(f"📄 **{src['name']}**")

    # --- 5. INPUT AREA (Η Μπάρα) ---
    # Αυτό είναι το κρίσιμο σημείο. Πρέπει να είναι εκτός if/else.
    prompt = st.chat_input("Γράψε εδώ τη βλάβη...")
    
    if prompt:
        # A. User Message
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
            with st.spinner("🤔 Ο Mastro Nek αναλύει..."):
                response_text = brain.get_chat_response(
                    st.session_state.messages, 
                    context_files=file_names_str,
                    lang=st.session_state.lang
                )
                st.markdown(response_text)
                
                if relevant_files:
                    with st.expander("📚 Βρέθηκαν στη Βιβλιοθήκη:"):
                        for f in relevant_files:
                            if f.get('link'):
                                st.markdown(f"📄 **[{f['name']}]({f['link']})**")
                            else:
                                st.markdown(f"📄 **{f['name']}**")

        # D. Save History
        st.session_state.messages.append({
            "role": "assistant", 
            "content": response_text,
            "sources": relevant_files 
        })