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

    # --- ΖΩΝΗ ΠΟΛΥΜΕΣΩΝ & ΑΡΧΕΙΩΝ (Restored & Unified) ---
    st.divider()
    
    # Αποθηκεύουμε τα uploads σε μεταβλητές
    captured_image = None
    captured_audio = None
    uploaded_files = []

    # Ενιαίο Expander για όλα τα εργαλεία (Κάμερα, Μικρόφωνο, Αρχεία)
    with st.expander(f"📎 {get_text('media_expander', lang)} / Uploads", expanded=False):
        t1, t2, t3 = st.tabs(["📸 Camera", "🎙️ Voice", "📂 Files (PDF/Img)"])
        
        with t1:
            img_input = st.camera_input(get_text('camera_label', lang))
            if img_input:
                captured_image = Image.open(img_input)
                st.success("📸 Image Ready!")
        
        with t2:
            # Live Mic
            audio_val = st.audio_input(get_text('audio_label', lang))
            if audio_val:
                captured_audio = audio_val
                st.success("🎙️ Audio Recorded!")

        with t3:
            # ΕΔΩ ΗΤΑΝ Η ΠΑΡΑΛΕΙΨΗ: Επαναφορά του File Uploader για PDF & Εικόνες
            uploaded_files = st.file_uploader(
                "Ανεβάστε Manuals (PDF) ή Φωτογραφίες", 
                type=['pdf', 'png', 'jpg', 'jpeg'], 
                accept_multiple_files=True
            )
            if uploaded_files:
                st.success(f"📎 {len(uploaded_files)} αρχεία έτοιμα για αποστολή.")

    # --- INPUT AREA ---
    prompt_placeholder = get_text('chat_placeholder', lang)
    if captured_audio or captured_image or uploaded_files:
        prompt_placeholder = "Πάτα Enter για αποστολή των αρχείων (ή γράψε σχόλιο)..."

    prompt = st.chat_input(prompt_placeholder)
    
    # Λογική Αποστολής
    if prompt or captured_audio or captured_image or uploaded_files:
        
        final_prompt = prompt if prompt else "(Αποστολή Αρχείων/Πολυμέσων)"

        # 1. Εμφάνιση μηνύματος Χρήστη
        st.session_state.messages.append({"role": "user", "content": final_prompt})
        with st.chat_message("user"): 
            st.markdown(final_prompt)
            if captured_image: st.image(captured_image, width=250)
            if captured_audio: st.audio(captured_audio)
            if uploaded_files: 
                for f in uploaded_files:
                    st.caption(f"📎 {f.name}")

        # 2. Context Logic (Αναζήτηση Manuals από τη μνήμη)
        found_files_names = ""
        if prompt:
            keywords = prompt.lower().split()
            library = st.session_state.library_cache
            found = []
            if library:
                for item in library:
                    if sum(1 for w in keywords if w in item['name'].lower() and len(w) > 2) >= 1:
                        found.append(item)
            # Κρατάμε τα ονόματα για το prompt
            found_files_names = ", ".join([f['name'] for f in found[:3]])

        # 3. AI Response
        with st.chat_message("assistant"):
            with st.spinner(get_text('chat_thinking', lang)):
                
                # Προετοιμασία λίστας εικόνων
                images_to_send = [captured_image] if captured_image else []
                
                # Διαχωρισμός PDF από Εικόνες στα Uploads
                pdfs_to_process = []
                for f in uploaded_files:
                    if f.type == "application/pdf":
                        pdfs_to_process.append(f)
                    elif f.type.startswith("image/"):
                        images_to_send.append(Image.open(f))

                # Κλήση στον Εγκέφαλο (Τώρα δέχεται ΚΑΙ pdfs)
                response_text = brain.get_chat_response(
                    st.session_state.messages, 
                    context_files=found_files_names,
                    lang=lang,
                    images=images_to_send,
                    audio=captured_audio,
                    pdf_files=pdfs_to_process # <--- Στέλνουμε τα PDF!
                )
                st.markdown(response_text)

        st.session_state.messages.append({"role": "assistant", "content": response_text})