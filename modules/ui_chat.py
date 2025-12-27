import streamlit as st
from core.language_pack import get_text
from core.ai_engine import AIEngine
from PIL import Image

def render(user):
    lang = st.session_state.get('lang', 'gr')

    st.header(f"{get_text('menu_chat', lang)}")

    brain = AIEngine()
    
    if 'library_cache' not in st.session_state: st.session_state.library_cache = []
    if "messages" not in st.session_state: st.session_state.messages = []
    
    # Εμφάνιση Ιστορικού
    if not st.session_state.messages:
        st.info(get_text('chat_intro', lang))

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            # (Εδώ θα μπορούσαμε να δείχνουμε και τις φωτό που ανέβασε, αλλά για απλότητα τις κρύβουμε)

    # --- ΠΟΛΥΜΕΣΑ (CAMERA & VOICE) ---
    # Το βάζουμε σε Expander για να μην πιάνει χώρο
    captured_image = None
    captured_audio = None

    with st.expander(get_text('media_expander', lang), expanded=False):
        c1, c2 = st.columns(2)
        
        with c1:
            # Κάμερα
            img_input = st.camera_input(get_text('camera_label', lang))
            if img_input:
                captured_image = Image.open(img_input)
                st.success("📸 Image Captured!")
        
        with c2:
            # Ήχος (Στο κινητό αυτό ανοίγει επιλογή για ηχογράφηση ή αρχεία)
            aud_input = st.file_uploader(get_text('audio_label', lang), type=['wav', 'mp3', 'm4a', 'ogg'])
            if aud_input:
                captured_audio = aud_input
                st.success("🎙️ Audio Ready!")

    # INPUT AREA
    prompt = st.chat_input(get_text('chat_placeholder', lang))
    
    # Λογική: Αν πατήσει Enter (prompt) Ή αν έχει βγάλει φωτό/ήχο και θέλει να τα στείλει
    # Σημείωση: Το chat_input θέλει οπωσδήποτε κείμενο για να ενεργοποιηθεί.
    # Αν ο χρήστης θέλει να στείλει ΜΟΝΟ φωτό, πρέπει να γράψει κάτι τύπου "Δες αυτό".
    
    if prompt:
        # User Msg
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): 
            st.markdown(prompt)
            if captured_image: st.image(captured_image, caption="Uploaded Image", width=200)
            if captured_audio: st.audio(captured_audio)

        # Context Logic
        found_files = []
        keywords = prompt.lower().split()
        library = st.session_state.library_cache
        if library:
            for item in library:
                matches = sum(1 for word in keywords if word in item['name'].lower() and len(word) > 2)
                if matches >= 1: found_files.append(item)
        relevant_files = found_files[:3]
        file_names_str = ", ".join([f['name'] for f in relevant_files])

        # AI Response
        with st.chat_message("assistant"):
            with st.spinner(get_text('chat_thinking', lang)):
                
                # Προετοιμασία λίστας εικόνων (αν υπάρχουν)
                images_to_send = [captured_image] if captured_image else []
                
                response_text = brain.get_chat_response(
                    st.session_state.messages, 
                    context_files=file_names_str,
                    lang=lang,
                    images=images_to_send, # Στέλνουμε την εικόνα
                    audio=captured_audio   # Στέλνουμε τον ήχο
                )
                st.markdown(response_text)
                
                if relevant_files:
                    with st.expander("📚 Context Files"):
                        for f in relevant_files:
                            st.caption(f"📄 {f['name']}")

        st.session_state.messages.append({"role": "assistant", "content": response_text})