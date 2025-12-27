import streamlit as st
import json
import os
from core.language_pack import get_text
from core.ai_engine import AIEngine
from PIL import Image

def load_cached_library():
    """Φορτώνει τη βιβλιοθήκη από το αρχείο JSON (γρήγορα)."""
    try:
        if os.path.exists("drive_index.json"):
            with open("drive_index.json", "r", encoding="utf-8") as f:
                return json.load(f)
    except: pass
    return []

def render(user):
    lang = st.session_state.get('lang', 'gr')

    st.header(f"{get_text('menu_chat', lang)}")

    brain = AIEngine()
    
    # ΔΙΟΡΘΩΣΗ: Φόρτωση δεδομένων από το JSON αν η μνήμη είναι άδεια
    if 'library_cache' not in st.session_state or not st.session_state.library_cache:
        st.session_state.library_cache = load_cached_library()

    if "messages" not in st.session_state: st.session_state.messages = []
    
    # Εμφάνιση Ιστορικού
    if not st.session_state.messages:
        st.info(get_text('chat_intro', lang))

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # --- ΖΩΝΗ ΠΟΛΥΜΕΣΩΝ & ΑΡΧΕΙΩΝ ---
    st.divider()
    captured_image = None
    captured_audio = None
    uploaded_files = []

    with st.expander(f"📎 {get_text('media_expander', lang)} / Uploads", expanded=False):
        t1, t2, t3 = st.tabs(["📸 Camera", "🎙️ Voice", "📂 Files (PDF/Img)"])
        
        with t1:
            img_input = st.camera_input(get_text('camera_label', lang))
            if img_input:
                captured_image = Image.open(img_input)
                st.success("📸 Image Ready!")
        
        with t2:
            audio_val = st.audio_input(get_text('audio_label', lang))
            if audio_val:
                captured_audio = audio_val
                st.success("🎙️ Audio Recorded!")

        with t3:
            uploaded_files = st.file_uploader(
                "Manuals (PDF) / Photos", 
                type=['pdf', 'png', 'jpg', 'jpeg'], 
                accept_multiple_files=True
            )
            if uploaded_files:
                st.success(f"📎 {len(uploaded_files)} files ready.")

    # --- INPUT AREA ---
    prompt_placeholder = get_text('chat_placeholder', lang)
    if captured_audio or captured_image or uploaded_files:
        prompt_placeholder = "Press Enter to send..."

    prompt = st.chat_input(prompt_placeholder)
    
    if prompt or captured_audio or captured_image or uploaded_files:
        
        final_prompt = prompt if prompt else "(Sent Media)"

        # 1. User Message
        st.session_state.messages.append({"role": "user", "content": final_prompt})
        with st.chat_message("user"): 
            st.markdown(final_prompt)
            if captured_image: st.image(captured_image, width=250)
            if captured_audio: st.audio(captured_audio)
            if uploaded_files: 
                for f in uploaded_files: st.caption(f"📎 {f.name}")

        # 2. Context Logic (Εύρεση Manuals)
        # Τώρα που έχουμε τη λίστα, αυτό θα λειτουργήσει!
        found_files_names = ""
        relevant_files = []
        
        if prompt:
            keywords = prompt.lower().split()
            library = st.session_state.library_cache # Τώρα δεν είναι κενό!
            found = []
            
            if library:
                for item in library:
                    # Απλή αναζήτηση keyword στο όνομα ή στα search_terms
                    searchable = (item.get('name', '') + " " + item.get('search_terms', '')).lower()
                    if sum(1 for w in keywords if w in searchable and len(w) > 2) >= 1:
                        found.append(item)
            
            relevant_files = found[:3] # Κρατάμε τα 3 καλύτερα
            # Στέλνουμε τα ονόματα στο AI για να ξέρει τι βρήκαμε
            found_files_names = ", ".join([f['name'] for f in relevant_files])

        # 3. AI Response
        with st.chat_message("assistant"):
            with st.spinner(get_text('chat_thinking', lang)):
                
                images_to_send = [captured_image] if captured_image else []
                pdfs_to_process = []
                for f in uploaded_files:
                    if f.type == "application/pdf": pdfs_to_process.append(f)
                    elif f.type.startswith("image/"): images_to_send.append(Image.open(f))

                response_text = brain.get_chat_response(
                    st.session_state.messages, 
                    context_files=found_files_names, # Τώρα θα έχει τιμές!
                    lang=lang,
                    images=images_to_send,
                    audio=captured_audio,
                    pdf_files=pdfs_to_process
                )
                st.markdown(response_text)
                
                # Δείχνουμε τα manuals που χρησιμοποιήθηκαν
                if relevant_files:
                    with st.expander("📚 Related Manuals found in Library"):
                        for f in relevant_files:
                            link = f.get('link') or f.get('webViewLink')
                            if link: st.markdown(f"📄 **[{f['name']}]({link})**")
                            else: st.markdown(f"📄 **{f['name']}**")

        st.session_state.messages.append({
            "role": "assistant", 
            "content": response_text,
            "sources": relevant_files 
        })