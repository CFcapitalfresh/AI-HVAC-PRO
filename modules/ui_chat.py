import streamlit as st
from core.language_pack import get_text
from core.ai_engine import AIEngine
from services.sync_service import SyncService # Για να ψάχνουμε manuals

def render(user):
    # --- HEADER & RESET BUTTON ---
    col1, col2 = st.columns([4, 1])
    with col1:
        st.header(get_text('menu_chat', st.session_state.lang))
    with col2:
        if st.button("🧹 New", help="Καθαρισμός Μνήμης / New Problem"):
            st.session_state.messages = []
            st.session_state.current_context_files = [] # Καθαρισμός πηγών
            st.rerun()

    # --- INIT ---
    brain = AIEngine()
    
    # Φόρτωση βιβλιοθήκης στη μνήμη (αν δεν υπάρχει) για να βρούμε manuals
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
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            
            # Εμφάνιση πηγών αν υπάρχουν σε μήνυμα AI
            if msg["role"] == "assistant" and "sources" in msg:
                with st.expander("📚 Σχετικά Manuals & Πηγές"):
                    for src in msg["sources"]:
                        st.markdown(f"📄 **[{src['name']}]({src['link']})**")

    # --- INPUT ---
    prompt = st.chat_input("Περιγράψτε τη βλάβη ή το μοντέλο...")
    
    if prompt:
        # 1. Εμφάνιση ερώτησης χρήστη
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
        
        # 2. ΑΥΤΟΜΑΤΗ ΑΝΑΖΗΤΗΣΗ MANUAL (Context Search)
        # Ψάχνουμε λέξεις κλειδιά από την ερώτηση μέσα στη βιβλιοθήκη
        found_files = []
        keywords = prompt.lower().split()
        library = st.session_state.library_cache
        
        # Απλή λογική: Αν βρούμε πάνω από 1 λέξη κλειδί στο όνομα αρχείου
        if library:
            for item in library:
                matches = sum(1 for word in keywords if word in item['name'].lower() and len(word) > 2)
                if matches >= 1: # Αν βρει έστω και ένα match (π.χ. "Clas")
                    found_files.append(item)
        
        # Κρατάμε τα top 3 για να μην μπουκώσουμε το AI
        relevant_files = found_files[:3]
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
                
                # 4. Εμφάνιση Links αν βρήκαμε σχετικά αρχεία
                if relevant_files:
                    with st.expander("📚 Βρέθηκαν στη Βιβλιοθήκη:"):
                        for f in relevant_files:
                            st.markdown(f"📄 **[{f['name']}]({f['link']})**")

        # 5. Αποθήκευση στο ιστορικό
        st.session_state.messages.append({
            "role": "assistant", 
            "content": response_text,
            "sources": relevant_files # Αποθηκεύουμε τις πηγές για να φαίνονται και μετά
        })