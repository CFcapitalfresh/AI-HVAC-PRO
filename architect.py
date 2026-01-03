import streamlit as st
import os
import shutil
import ast
from datetime import datetime
import google.generativeai as genai
from streamlit_mic_recorder import mic_recorder
from PIL import Image
import io

# --- 1. ΡΥΘΜΙΣΕΙΣ (Dictator Mode) ---
st.set_page_config(page_title="Architect AI v34 (Final)", page_icon="🏗️", layout="wide")

# ΑΠΑΓΟΡΕΥΕΤΑΙ να αλλάξει αυτό. Είναι το μόνο μοντέλο που δουλεύει δωρεάν και γρήγορα.
TARGET_MODEL = "models/gemini-1.5-flash"

# --- 2. WORKSPACE MANAGER ---
def get_project_context():
    """Διαβάζει όλα τα αρχεία του project για να ξέρει τι να διορθώσει."""
    root_dir = os.path.dirname(os.path.abspath(__file__))
    file_contents = {}
    ignore = {'.git', '__pycache__', 'venv', '.streamlit', 'backups', '.DS_Store', 'requirements.txt'} 
    
    for dirpath, dirnames, filenames in os.walk(root_dir):
        dirnames[:] = [d for d in dirnames if d not in ignore]
        for f in filenames:
            if f in ignore or f.endswith(('.pyc', '.png', '.jpg', '.pdf', '.mp3', '.xlsx')): continue 
            try:
                path = os.path.join(dirpath, f)
                rel_path = os.path.relpath(path, root_dir)
                with open(path, 'r', encoding='utf-8', errors='ignore') as file:
                    file_contents[rel_path] = file.read()
            except: pass
    return file_contents

def save_code_changes(response_text):
    """Εντοπίζει κώδικα στην απάντηση και τον σώζει."""
    import re
    # Ψάχνουμε το μοτίβο: ### FILE: όνομα.py ...κώδικας...
    pattern = r"### FILE: (.+?)\n.*?```(?:python)?\n(.*?)```"
    matches = re.findall(pattern, response_text, re.DOTALL)
    log = []
    
    if not matches: return "ℹ️ Δεν βρέθηκαν αλλαγές για αποθήκευση."

    for filename, code in matches:
        filename = filename.strip().replace("\\", "/")
        if filename.startswith("./"): filename = filename[2:]
        
        full_path = os.path.abspath(filename)
        
        # Backup
        if os.path.exists(full_path):
            backup_dir = os.path.join(os.path.dirname(full_path), "backups")
            os.makedirs(backup_dir, exist_ok=True)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            shutil.copy2(full_path, os.path.join(backup_dir, f"{os.path.basename(full_path)}_{ts}.bak"))

        # Save
        try:
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(code.strip())
            log.append(f"✅ SAVED: {filename}")
        except Exception as e:
            log.append(f"❌ ERROR: {filename} ({e})")
            
    return "\n".join(log)

# --- 3. THE AI ENGINE ---
def ask_the_architect(strategy, parts, api_key):
    if not api_key: return "❌ Error: Missing API Key"
    
    genai.configure(api_key=api_key)
    
    try:
        # Χρησιμοποιούμε το 1.5 Flash που υποστηρίζει η έκδοση 0.8.0
        model = genai.GenerativeModel(TARGET_MODEL)
        
        # Ρυθμίσεις
        config = genai.types.GenerationConfig(temperature=0.2, max_output_tokens=8192)
        
        response = model.generate_content(parts, generation_config=config)
        return response.text
    except Exception as e:
        err = str(e)
        if "429" in err: return "⏳ QUOTA ERROR: Πολλά αιτήματα. Περίμενε 1 λεπτό."
        if "404" in err: return f"❌ ERROR: Δεν βρέθηκε το μοντέλο {TARGET_MODEL}. (Απίθανο με την έκδοση 0.8.0)"
        return f"❌ AI ERROR: {err}"

# --- 4. UI INTERFACE ---
def main():
    st.title("🏗️ Architect AI v34 (Final Integration)")
    
    # Sidebar
    with st.sidebar:
        api_key = st.text_input("Gemini API Key", type="password")
        if not api_key and "GEMINI_API_KEY" in st.secrets:
            api_key = st.secrets["GEMINI_API_KEY"]
            st.success("API Key Loaded")

        st.divider()
        st.caption("Inputs")
        audio = mic_recorder(start_prompt="🎤 Start", stop_prompt="⏹ Stop", key='mic')
        uploaded = st.file_uploader("Image/PDF", type=['png','jpg','pdf'], label_visibility="collapsed")
        
        st.divider()
        project_data = get_project_context()
        files = ["Global Context"] + list(project_data.keys())
        strategy = st.selectbox("Strategy", ["Feature", "Bug Fix", "Refactor"])
        focus = st.selectbox("Focus File", files)
        auto_save = st.checkbox("Auto-Save", value=False)

    # Chat History
    if "chat" not in st.session_state: st.session_state.chat = []
    for msg in st.session_state.chat:
        with st.chat_message(msg["role"]): st.markdown(msg["text"])

    # Input Handling
    user_text = st.chat_input("Εντολή...")
    
    final_input = None
    if user_text: final_input = user_text
    elif audio: final_input = "🎤 Audio Command"

    if (final_input or uploaded) and api_key:
        # Show User Message
        display = final_input if final_input else "📂 Media Uploaded"
        st.session_state.chat.append({"role": "user", "text": display})
        with st.chat_message("user"): 
            st.markdown(display)
            if uploaded: st.caption(f"📎 {uploaded.name}")

        # Prepare Prompt
        context_str = "PROJECT FILES:\n" + "\n".join([f"--- {k} ---\n{v[:6000]}" for k,v in project_data.items()])
        
        prompt = f"""
        ROLE: Senior Python Architect. LANG: GREEK.
        TASK: {strategy} on {focus}.
        USER REQUEST: {user_text if user_text else 'Analyze media'}
        
        INSTRUCTIONS:
        1. Return FULL CODE blocks.
        2. Format: ### FILE: filename.py \n ```python ... ```
        
        CONTEXT:
        {context_str}
        """
        
        parts = [prompt]
        if audio and audio['bytes']: parts.append({"mime_type": "audio/wav", "data": audio['bytes']})
        if uploaded: 
            parts.append({"mime_type": uploaded.type, "data": uploaded.getvalue()})

        # Run AI
        with st.chat_message("assistant"):
            with st.spinner("Processing..."):
                reply = ask_the_architect(strategy, parts, api_key)
                st.markdown(reply)
                st.session_state.chat.append({"role": "assistant", "text": reply})
                
                # Save
                if "### FILE:" in reply:
                    if auto_save:
                        with st.status("Saving..."):
                            st.code(save_code_changes(reply))
                            time.sleep(1)
                            st.rerun()
                    else:
                        if st.button("💾 SAVE CHANGES"):
                            st.code(save_code_changes(reply))
                            st.success("Saved!")
                            time.sleep(1)
                            st.rerun()

if __name__ == "__main__":
    main()