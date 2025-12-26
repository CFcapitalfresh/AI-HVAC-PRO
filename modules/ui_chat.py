import streamlit as st
from core.language_pack import get_text
from core.ai_engine import AIEngine
from services.sync_service import SyncService

def render(user):
    # --- HEADER & RESET BUTTON ---
    col1, col2 = st.columns([4, 1])
    with col1:
        st.header(get_text('menu_chat', st.session_state.lang))
    with col2:
        # Κουμπί καθαρισμού ιστορικού
        if st.button("🧹 New", help="Καθαρισμός Μνήμης / New Problem"):
            st.session_state.messages = []
            st.session_state.current_context_files = [] 
            st.rerun()

    # --- INIT ---
    brain = AIEngine()
    
    # Φόρτωση βιβλιοθήκης στη μνήμη (αν δεν υπάρχει)
    if 'library_cache' not in st.session_state or not st.session_state.library_cache:
        try:
            syncer = SyncService()
            st.session_state.library_cache = syncer.scan_library()
        except:
            st.session_state.library_cache = []

    # Init History
    if "messages" not in st.session_state: st.session_state.messages = []
    if "current_context_files" not in st.session_state: st.session_state.current_context_files = []

    # --- DISPLAY CHAT ---
    # Εμφάνιση παλιών μηνυμάτων
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            
            # Εμφάνιση πηγών (αν υπάρχουν στο ιστορικό)
            if msg["role"] == "assistant" and "sources" in msg:
                with st.expander("📚 Σχετικά Manuals & Πηγές"):
                    for src in msg["sources"]:
                        if src.get('link'):
                            st.markdown(f"📄 **[{src['name']}]({src['link']})**")
                        else:
                            st.markdown(f"📄 **{src['name']}**")

    # --- INPUT AREA ---
    prompt = st.chat_input("Περιγράψτε τη βλάβη ή το μοντέλο...")
    
    if prompt:
        # 1. Εμφάνιση ερώτησης χρήστη
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
        
        # 2. ΑΥΤΟΜΑΤΗ ΑΝΑΖΗΤΗΣΗ MANUAL (Context Search)
        found_files = []
        keywords = prompt.lower().split()
        library = st.session_state.library_cache
        
        # Ψάχνουμε αν οι λέξεις του χρήστη ταιριάζουν με ονόματα αρχείων
        if library:
            for item in library:
                # Ψάχνουμε αν υπάρχει έστω και μία λέξη-κλειδί στο όνομα του αρχείου (με πάνω από 2 γράμματα)
                matches = sum(1 for word in keywords if word in item['name'].lower() and len(word) > 2)
                if matches >= 1: 
                    found_files.append(item)
        
        # Κρατάμε τα top 3
        relevant_files = found_files[:3]
        
        # Φτιάχνουμε string με τα ονόματα για να τα δει το AI
        file_names_str = ", ".join([f['name'] for f in relevant_files])

        # 3. Κλήση AI με ΙΣΤΟΡΙΚΟ και FILES
        with st.chat_message("assistant"):
            with st.spinner("🤔 Ο Mastro Nek σκέφτεται..."):
                response_text = brain.get_chat_response(
                    st.session_state.messages, 
                    context_files=file_names_str,
                    lang=st.session_state.lang
                )
                st.markdown(response_text)
                
                # 4. Εμφάνιση Links αν βρήκαμε σχετικά αρχεία ΤΩΡΑ
                if relevant_files:
                    with st.expander("📚 Βρέθηκαν στη Βιβλιοθήκη:"):
                        for f in relevant_files:
                            if f.get('link'):
                                st.markdown(f"📄 **[{f['name']}]({f['link']})**")
                            else:
                                st.markdown(f"📄 **{f['name']}**")

        # 5. Αποθήκευση στο ιστορικό
        st.session_state.messages.append({
            "role": "assistant", 
            "content": response_text,
            "sources": relevant_files 
        })