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
    
    # Εμφάνιση Ιστορικού (Πάνω-Πάνω)
    if not st.session_state.messages:
        st.info(get_text('chat_intro', lang))

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # --- ΖΩΝΗ ΠΟΛΥΜΕΣΩΝ (ΧΑΜΗΛΑ) ---
    st.divider()
    
    # Χρησιμοποιούμε Expander για να μην πιάνει χώρο, αλλά το βάζουμε ΤΩΡΑ (πριν το input)
    captured_image = None
    captured_audio = None

    with st.expander(get_text('media_expander', lang), expanded=False):
        c1, c2 = st.columns(2)
        
        with c1:
            # Κάμερα
            img_input = st.camera_input(get_text('camera_label', lang))
            if img_input:
                captured_image = Image.open(img_input)
                st.success("📸 Image Ready!")
        
        with c2:
            # ΝΕΟ: Ζωντανή Ηχογράφηση (Live Mic)
            audio_val = st.audio_input(get_text('audio_label', lang))
            if audio_val:
                captured_audio = audio_val
                st.success("🎙️ Audio Recorded!")

    # --- INPUT AREA ---
    # Προτροπή: Αν έχει ηχογραφήσει, μπορεί να πατήσει απλά Enter ή να γράψει κάτι
    prompt_placeholder = get_text('chat_placeholder', lang)
    if captured_audio or captured_image:
        prompt_placeholder = "Press Enter to send media (or add text)..."

    prompt = st.chat_input(prompt_placeholder)
    
    # Λογική Αποστολής: Αν υπάρχει κείμενο Ή πολυμέσα
    if prompt or captured_audio or captured_image:
        
        # Αν δεν έγραψε κείμενο αλλά έστειλε media, βάζουμε ένα αυτόματο κείμενο
        final_prompt = prompt if prompt else "(Media Sent)"

        # 1. Εμφάνιση μηνύματος Χρήστη
        st.session_state.messages.append({"role": "user", "content": final_prompt})
        with st.chat_message("user"): 
            st.markdown(final_prompt)
            if captured_image: st.image(captured_image, width=250)
            if captured_audio: st.audio(captured_audio)

        # 2. Context Logic (Αναζήτηση Manuals με βάση το κείμενο)
        found_files = []
        if prompt:
            keywords = prompt.lower().split()
            library = st.session_state.library_cache
            if library:
                for item in library:
                    matches = sum(1 for word in keywords if word in item['name'].lower() and len(word) > 2)
                    if matches >= 1: found_files.append(item)
        relevant_files = found_files[:3]
        file_names_str = ", ".join([f['name'] for f in relevant_files])

        # 3. AI Response
        with st.chat_message("assistant"):
            with st.spinner(get_text('chat_thinking', lang)):
                
                images_to_send = [captured_image] if captured_image else []
                
                response_text = brain.get_chat_response(
                    st.session_state.messages, 
                    context_files=file_names_str,
                    lang=lang,
                    images=images_to_send,
                    audio=captured_audio
                )
                st.markdown(response_text)
                
                if relevant_files:
                    with st.expander("📚 Context Files"):
                        for f in relevant_files:
                            st.caption(f"📄 {f['name']}")

        st.session_state.messages.append({"role": "assistant", "content": response_text})