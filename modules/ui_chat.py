import streamlit as st
import json
import os
from core.language_pack import get_text
from core.ai_engine import AIEngine
from services.sync_service import SyncService # <--- ΝΕΟ IMPORT
from PIL import Image

def render(user):
    lang = st.session_state.get('lang', 'gr')
    st.header(f"{get_text('menu_chat', lang)}")

    brain = AIEngine()
    
    # --- SMART LOAD (CLOUD PERSISTENCE) ---
    if 'library_cache' not in st.session_state or not st.session_state.library_cache:
        srv = SyncService()
        st.session_state.library_cache = srv.load_index()

    # Init Session
    if "messages" not in st.session_state: st.session_state.messages = []
    if "active_manuals" not in st.session_state: st.session_state.active_manuals = [] 

    # History
    if not st.session_state.messages:
        st.info(get_text('chat_intro', lang))

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    st.divider()
    
    # --- MEDIA INPUTS ---
    captured_image = None
    captured_audio = None
    uploaded_files = []

    with st.expander(f"📎 {get_text('media_expander', lang)} / Uploads", expanded=False):
        t1, t2, t3 = st.tabs(["📸 Camera", "🎙️ Voice", "📂 Files"])
        with t1:
            img_input = st.camera_input(get_text('camera_label', lang))
            if img_input: captured_image = Image.open(img_input)
        with t2:
            audio_val = st.audio_input(get_text('audio_label', lang))
            if audio_val: captured_audio = audio_val
        with t3:
            uploaded_files = st.file_uploader("Manuals/Photos", type=['pdf', 'png', 'jpg', 'jpeg'], accept_multiple_files=True)

    # --- INPUT & LOGIC ---
    prompt = st.chat_input(get_text('chat_placeholder', lang))
    
    if prompt or captured_audio or captured_image or uploaded_files:
        final_prompt = prompt if prompt else "(Sent Media)"
        st.session_state.messages.append({"role": "user", "content": final_prompt})
        with st.chat_message("user"): 
            st.markdown(final_prompt)
            if captured_image: st.image(captured_image, width=250)
            if captured_audio: st.audio(captured_audio)
            if uploaded_files: 
                for f in uploaded_files: st.caption(f"📎 {f.name}")

        # --- RANKING SYSTEM ---
        found_files_names = ""
        if prompt:
            stopwords = ["και", "το", "τη", "με", "για", "error", "βλαβη", "code", "problem"]
            keywords = [w for w in prompt.lower().split() if w not in stopwords and len(w) > 1]
            
            library = st.session_state.library_cache
            scored_results = []
            
            if library:
                for item in library:
                    target = (item.get('name', '') + " " + item.get('search_terms', '')).lower()
                    matches = sum(1 for w in keywords if w in target)
                    if matches > 0: scored_results.append((matches, item))
            
            scored_results.sort(key=lambda x: x[0], reverse=True)
            top_matches = [item for score, item in scored_results[:3]]

            if top_matches: st.session_state.active_manuals = top_matches
            
            found_files_names = ", ".join([f['name'] for f in st.session_state.active_manuals])

        # --- AI GENERATION ---
        with st.chat_message("assistant"):
            with st.spinner(get_text('chat_thinking', lang)):
                imgs = [captured_image] if captured_image else []
                pdfs = [f for f in uploaded_files if f.type == "application/pdf"]
                for f in uploaded_files:
                     if f.type.startswith("image/"): imgs.append(Image.open(f))

                resp = brain.get_chat_response(
                    st.session_state.messages, 
                    context_files=found_files_names, 
                    lang=lang,
                    images=imgs, audio=captured_audio, pdf_files=pdfs
                )
                st.markdown(resp)
                
                if st.session_state.active_manuals:
                    with st.expander("📚 Active Context"):
                        for f in st.session_state.active_manuals:
                            l = f.get('link') or f.get('webViewLink')
                            if l: st.markdown(f"📄 **[{f['name']}]({l})**")
                            else: st.markdown(f"📄 **{f['name']}**")

        st.session_state.messages.append({"role": "assistant", "content": resp})