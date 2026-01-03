import streamlit as st
import os
import shutil
import traceback
import time
import re

# --- 1. ΑΣΦΑΛΗ IMPORTS ---
try:
    import google.generativeai as genai
    from streamlit_mic_recorder import mic_recorder
except ImportError:
    st.error("Missing libraries. Run: pip install google-generativeai streamlit-mic-recorder")
    st.stop()

st.set_page_config(page_title="Architect AI v10", page_icon="🏗️", layout="wide")

# --- 2. ΡΥΘΜΙΣΕΙΣ (Protected Rules) ---
PROTECTED_FEATURES = [
    "1. MICROPHONE/AUDIO: Πάντα κουμπί για φωνητική εντολή στο UI.",
    "2. PDF UPLOAD: Πάντα υποστήριξη PDF/Images.",
    "3. MODULARITY: Χρήση imports (core/modules), όχι μονολιθικός κώδικας.",
    "4. ERROR HANDLING: Πάντα try/except blocks και logging.",
    "5. LANGUAGE: Υποστήριξη GR/EN (get_text).",
    "6. STREAMLIT STATE: Έλεγχος initialization keys.",
    "7. DRIVE MANAGER: Προσοχή στο core/drive_manager.py."
]

# --- 3. HELPER FUNCTIONS ---
def get_project_structure():
    """Deep Scan: Βλέπει τα πάντα."""
    root_dir = os.path.dirname(os.path.abspath(__file__))
    structure = ""
    file_contents = {}
    ignore_dirs = {"__pycache__", ".git", ".streamlit", "venv", ".vscode", "env", "build", "dist"}
    ignore_files = {"architect.py", "requirements.txt", "README.md", ".gitignore", "LICENSE", ".DS_Store"}
    
    for path, subdirs, files in os.walk(root_dir):
        subdirs[:] = [d for d in subdirs if d not in ignore_dirs]
        for name in files:
            if name.endswith(".py") and name not in ignore_files:
                full_path = os.path.join(path, name)
                rel_path = os.path.relpath(full_path, root_dir).replace("\\", "/")
                structure += f"- {rel_path}\n"
                try:
                    with open(full_path, "r", encoding="utf-8") as f:
                        file_contents[rel_path] = f.read()
                except: pass
    return structure, file_contents, root_dir

def save_code_to_file(rel_path, new_code):
    try:
        root_dir = os.path.dirname(os.path.abspath(__file__))
        full_path = os.path.join(root_dir, rel_path.replace("/", os.sep))
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        if os.path.exists(full_path): shutil.copy(full_path, f"{full_path}.bak")
        with open(full_path, "w", encoding="utf-8") as f: f.write(new_code)
        return True, f"✅ Saved: {rel_path}"
    except Exception as e: return False, str(e)

# --- 4. SMART MODEL HANDLING (v9 Feature) ---
@st.cache_data(ttl=600)
def get_available_models(api_key):
    if not api_key: return []
    genai.configure(api_key=api_key)
    try:
        models = list(genai.list_models())
        names = [m.name for m in models if 'generateContent' in m.supported_generation_methods and "gemini" in m.name.lower()]
        return sorted(names, reverse=True)
    except: return []

def generate_with_retry(model_name, prompt_parts):
    """v10 Feature: Επιμονή αν η Google ρίξει πόρτα (429)."""
    model = genai.GenerativeModel(model_name)
    max_retries = 3
    for attempt in range(max_retries):
        try:
            return model.generate_content(prompt_parts).text
        except Exception as e:
            if "429" in str(e):
                time.sleep(5 * (attempt + 1)) # Backoff
                continue
            raise e
    raise Exception("Google API Overloaded (429). Try again later.")

# --- 5. MAIN LOGIC ---
def main():
    st.title("🏗️ The Architect v10 (Ultimate)")
    
    # --- Sidebar ---
    with st.sidebar:
        api_key = None
        try:
            api_key = st.secrets.get("GEMINI_KEY") or st.secrets.get("general", {}).get("GEMINI_KEY")
        except: pass
        
        if not api_key:
            api_key = st.text_input("🔑 API Key", type="password")
            if not api_key: st.stop()
        else:
            st.success("API Key Found")
            
        # Model Selector (v9)
        models = get_available_models(api_key)
        if models:
            def_ix = 0
            for i, m in enumerate(models):
                if "1.5-flash" in m: def_ix = i; break
            sel_model = st.selectbox("Model:", models, index=def_ix)
        else:
            st.error("No models found.")
            st.stop()

        if st.button("🗑️ Reset"): 
            st.session_state.messages = []
            st.session_state.pending_changes = []
            st.session_state.last_audio = None
            st.rerun()

    # Session
    if "messages" not in st.session_state: st.session_state.messages = [{"role":"assistant", "content": "Ready."}]
    if "pending_changes" not in st.session_state: st.session_state.pending_changes = []
    if "last_audio" not in st.session_state: st.session_state.last_audio = None

    # Load Files (v8 Deep Scan)
    structure, file_contents, root = get_project_structure()
    
    # --- TABS: Chat vs Auto (v8 Feature is BACK) ---
    tab_chat, tab_auto = st.tabs(["💬 Chat & Εντολές", "🛡️ Αυτόματος Έλεγχος"])

    # --- TAB 1: Chat ---
    with tab_chat:
        c1, c2 = st.columns([1, 2])
        with c1:
            st.caption(f"Scanning: `{os.path.basename(root)}/`")
            all_files = sorted(list(file_contents.keys()))
            
            # Smart Select
            def_ix = 0
            for i, f in enumerate(all_files): 
                if "ui_chat.py" in f: def_ix = i
            
            focus_file = st.selectbox("Focus:", all_files, index=def_ix)
            with st.expander("Code View"):
                st.code(file_contents.get(focus_file, ""), language="python")

        with c2:
            for m in st.session_state.messages:
                with st.chat_message(m["role"]): st.markdown(m["content"])
            
            # Input
            t1, t2 = st.tabs(["Mic", "Text"])
            user_in = None
            is_audio = False
            
            with t1:
                aud = mic_recorder(start_prompt="🔴", stop_prompt="⏹️", key='mic')
                if aud and aud['id'] != st.session_state.last_audio:
                    user_in = aud['bytes']
                    is_audio = True
                    st.session_state.last_audio = aud['id']
            with t2:
                txt = st.chat_input("Type...")
                if txt: user_in = txt
            
            if user_in:
                process_request(sel_model, user_in, is_audio, file_contents, structure, focus_file, False)

    # --- TAB 2: Autonomous (v8 Feature) ---
    with tab_auto:
        st.info("Ο Αρχιτέκτονας θα σκανάρει όλο το project και θα προτείνει διορθώσεις.")
        if st.button("🚀 ΕΚΤΕΛΕΣΗ ΑΥΤΟΜΑΤΟΥ ΕΛΕΓΧΟΥ", type="primary"):
            auto_prompt = "ACT AS AN AUTONOMOUS AUDITOR. Scan all files. Identify the biggest bug or missing feature based on Protected Rules. Write the fix."
            process_request(sel_model, auto_prompt, False, file_contents, structure, focus_file, True)

    # --- SAVE SECTION (v7.7 Feature) ---
    if st.session_state.pending_changes:
        st.divider()
        st.success(f"Generated {len(st.session_state.pending_changes)} files.")
        for ch in st.session_state.pending_changes:
            with st.expander(f"📄 {ch['file']}"):
                st.code(ch['code'], language="python")

        if st.button("💾 SAVE ALL", type="primary"):
            for ch in st.session_state.pending_changes:
                save_code_to_file(ch["file"], ch["code"])
            st.success("Saved!")
            st.session_state.pending_changes = []
            time.sleep(1)
            st.rerun()

def process_request(model_name, user_in, is_audio, files, structure, focus_file, is_auto):
    if is_audio: st.session_state.messages.append({"role":"user", "content":"🎤 Audio"})
    elif not is_auto: st.session_state.messages.append({"role":"user", "content":user_in})
    
    with st.spinner("Thinking..."):
        try:
            full_context = "PROJECT:\n" + "\n".join([f"--- {k} ---\n{v}" for k,v in files.items()])
            
            prompt = f"""
            ROLE: Senior Python Architect. Lang: GREEK.
            RULES: {PROTECTED_FEATURES}
            CONTEXT: {full_context}
            FOCUS: {focus_file}
            REQUEST: {user_in if not is_audio else "Transcribe and execute."}
            
            OUTPUT FORMAT:
            Explain plan.
            ### FILE: filename.py
            ```python
            code
            ```
            """
            
            parts = [prompt]
            if is_audio: parts.append({"mime_type": "audio/wav", "data": user_in})
            
            # Use Retry Logic
            resp = generate_with_retry(model_name, parts)
            
            st.session_state.messages.append({"role":"assistant", "content":resp})
            
            changes = []
            for f, c in re.findall(r"### FILE: (.+?)\n.*?```python(.*?)```", resp, re.DOTALL):
                changes.append({"file": f.strip(), "code": c.strip()})
            
            if changes: st.session_state.pending_changes = changes
            st.rerun()
        except Exception as e:
            st.error(f"Error: {e}")

if __name__ == "__main__":
    main()