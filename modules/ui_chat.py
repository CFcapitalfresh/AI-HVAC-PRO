import streamlit as st
import json
import os
from core.language_pack import get_text
from core.ai_engine import AIEngine
from PIL import Image

def load_cached_library():
    """Φορτώνει τη βιβλιοθήκη από το αρχείο JSON."""
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
    
    # 1. ΦΟΡΤΩΣΗ ΒΙΒΛΙΟΘΗΚΗΣ
    if 'library_cache' not in st.session_state or not st.session_state.library_cache:
        st.session_state.library_cache = load_cached_library()

    # 2. ΑΡΧΙΚΟΠΟΙΗΣΗ ΙΣΤΟΡΙΚΟΥ
    if "messages" not in st.session_state: st.session_state.messages = []
    
    # 3. ΜΝΗΜΗ "STICKY CONTEXT" (Για να θυμάται το manual στη 2η ερώτηση)
    if "active_manuals" not in st.session_state:
        st.session_state.active_manuals = [] 

    # Εμφάνιση Μηνυμάτων
    if not st.session_state.messages:
        st.info(get_text('chat_intro', lang))

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    st.divider()
    
    # --- ΖΩΝΗ ΠΟΛΥΜΕΣΩΝ (Κάμερα, Μικρόφωνο, Αρχεία) ---
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
            uploaded_files = st.file_uploader("Manuals/Photos", type=['pdf', 'png', 'jpg', 'jpeg'], accept_multiple_files=True)
            if uploaded_files: st.success(f"📎 {len(uploaded_files)} files.")

    # --- INPUT AREA ---
    prompt_placeholder = get_text('chat_placeholder', lang)
    if captured_audio or captured_image or uploaded_files:
        prompt_placeholder = "Press Enter to send..."

    prompt = st.chat_input(prompt_placeholder)
    
    if prompt or captured_audio or captured_image or uploaded_files:
        
        final_prompt = prompt if prompt else "(Sent Media)"

        st.session_state.messages.append({"role": "user", "content": final_prompt})
        with st.chat_message("user"): 
            st.markdown(final_prompt)
            if captured_image: st.image(captured_image, width=250)
            if captured_audio: st.audio(captured_audio)
            if uploaded_files: 
                for f in uploaded_files: st.caption(f"📎 {f.name}")

        # ---------------------------------------------------------
        # 🟢 ΒΕΛΤΙΩΣΗ: RANKING SYSTEM (Βαθμολογία Ταιριάσματος)
        # ---------------------------------------------------------
        found_files_names = ""
        
        if prompt:
            # Αφαίρεση κοινών λέξεων (Stopwords) για καλύτερη στόχευση
            stopwords = ["και", "το", "τη", "με", "για", "error", "βλαβη", "code", "problem", "not", "working", "σφαλμα", "of", "the"]
            raw_keywords = prompt.lower().split()
            keywords = [w for w in raw_keywords if w not in stopwords and len(w) > 1]
            
            library = st.session_state.library_cache
            scored_results = [] # Λίστα μορφής: (Score, Item)
            
            if library:
                for item in library:
                    # Ενώνουμε όνομα και metadata
                    target_text = (item.get('name', '') + " " + item.get('search_terms', '')).lower()
                    
                    matches = 0
                    for word in keywords:
                        if word in target_text:
                            matches += 1
                    
                    # Αν έχει έστω και ένα σημαντικό ταίριασμα
                    if matches > 0:
                        scored_results.append((matches, item))
            
            # Ταξινόμηση: Πρώτα αυτά με τα περισσότερα matches (π.χ. 4/4)
            scored_results.sort(key=lambda x: x[0], reverse=True)
            
            # Παίρνουμε τα top 3
            top_matches = [item for score, item in scored_results[:3]]

            # 🟢 ΛΟΓΙΚΗ STICKY MEMORY
            if top_matches:
                # Βρήκαμε νέα; Ανανεώνουμε τη μνήμη.
                st.session_state.active_manuals = top_matches
            else:
                # Δεν βρήκαμε; Κρατάμε τα παλιά (δεν κάνουμε τίποτα).
                pass
            
            found_files_names = ", ".join([f['name'] for f in st.session_state.active_manuals])

        # ---------------------------------------------------------

        # --- AI GENERATION ---
        with st.chat_message("assistant"):
            with st.spinner(get_text('chat_thinking', lang)):
                images_to_send = [captured_image] if captured_image else []
                pdfs_to_process = []
                for f in uploaded_files:
                    if f.type == "application/pdf": pdfs_to_process.append(f)
                    elif f.type.startswith("image/"): images_to_send.append(Image.open(f))

                response_text = brain.get_chat_response(
                    st.session_state.messages, 
                    context_files=found_files_names, # Στέλνουμε τα "Persistent" manuals
                    lang=lang,
                    images=images_to_send,
                    audio=captured_audio,
                    pdf_files=pdfs_to_process
                )
                st.markdown(response_text)
                
                # Εμφάνιση των Manuals που "βλέπει" το AI
                if st.session_state.active_manuals:
                    with st.expander("📚 Active Context (Manuals Used)"):
                        for f in st.session_state.active_manuals:
                            link = f.get('link') or f.get('webViewLink')
                            if link: st.markdown(f"📄 **[{f['name']}]({link})**")
                            else: st.markdown(f"📄 **{f['name']}**")

        st.session_state.messages.append({
            "role": "assistant", 
            "content": response_text, 
            "sources": st.session_state.active_manuals 
        })