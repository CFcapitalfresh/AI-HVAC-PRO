import streamlit as st
from core.language_pack import get_text
from core.ai_engine import AIEngine

def render(user):
    lang = st.session_state.get('lang', 'gr')

    st.header(f"{get_text('menu_chat', lang)}")

    # Αρχικοποίηση Μηχανής (Χωρίς σκανάρισμα Drive!)
    brain = AIEngine()
    
    # Αν δεν υπάρχει λίστα, βάζουμε κενή για να μην κολλάει
    if 'library_cache' not in st.session_state:
        st.session_state.library_cache = []

    if "messages" not in st.session_state: 
        st.session_state.messages = []
    
    # Εμφάνιση Ιστορικού
    if not st.session_state.messages:
        st.info(get_text('chat_intro', lang))

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg["role"] == "assistant" and "sources" in msg:
                with st.expander("📚 Sources"):
                    for src in msg["sources"]:
                        link = src.get('link', '')
                        if link: st.markdown(f"📄 **[{src['name']}]({link})**")
                        else: st.markdown(f"📄 **{src['name']}**")

    # INPUT AREA (Τώρα θα εμφανίζεται αμέσως)
    prompt = st.chat_input(get_text('chat_placeholder', lang))
    
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
        
        # Γρήγορη αναζήτηση στη μνήμη (αν υπάρχει κάτι)
        found_files = []
        keywords = prompt.lower().split()
        library = st.session_state.library_cache
        
        if library:
            for item in library:
                matches = sum(1 for word in keywords if word in item['name'].lower() and len(word) > 2)
                if matches >= 1: found_files.append(item)
        
        relevant_files = found_files[:3]
        file_names_str = ", ".join([f['name'] for f in relevant_files])

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
                            if link: st.markdown(f"📄 **[{f['name']}]({link})**")
                            else: st.markdown(f"📄 **{f['name']}**")

        st.session_state.messages.append({
            "role": "assistant", 
            "content": response_text,
            "sources": relevant_files 
        })