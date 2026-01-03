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

st.set_page_config(page_title="Architect AI v12", page_icon="🏗️", layout="wide")

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

# --- 4. SMART MODEL HANDLING ---
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
    """Επιμονή αν η Google ρίξει πόρτα (429)."""
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
    st.title("🏗️ The Architect v12 (Commercial CEO)")
    
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
            
        # Model Selector
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
    if "messages" not in st.session_state: st.session_state.messages = [{"role":"assistant", "content": "Γεια! Γνωρίζω ότι χτίζουμε ένα Commercial SaaS Product. Ποιο είναι το επόμενο βήμα;"}]
    if "pending_changes" not in st.session_state: st.session_state.pending_changes = []
    if "last_audio" not in st.session_state: st.session_state.last_audio = None

    # Load Files
    structure, file_contents, root = get_project_structure()
    
    # --- TABS ---
    tab_chat, tab_auto = st.tabs(["💬 Chat & Development", "🛡️ Market & Code Audit"])

    # --- TAB 1: Chat ---
    with tab_chat:
        c1, c2 = st.columns([1, 2])
        with c1:
            st.caption(f"Scanning: `{os.path.basename(root)}/`")
            
            # SCOPE SELECTOR
            scope_mode = st.radio("🔭 Εστίαση:", ["📂 Ένα Αρχείο", "🌍 Όλο το Project (Global)"])
            
            focus_context = ""
            focus_file_name = "GLOBAL_CONTEXT"
            
            if scope_mode == "📂 Ένα Αρχείο":
                all_files = sorted(list(file_contents.keys()))
                def_ix = 0
                for i, f in enumerate(all_files): 
                    if "ui_chat.py" in f: def_ix = i
                
                focus_file_name = st.selectbox("Επιλογή Αρχείου:", all_files, index=def_ix)
                with st.expander("Code View"):
                    st.code(file_contents.get(focus_file_name, ""), language="python")
                focus_context = f"CURRENT FILE ({focus_file_name}):\n```python\n{file_contents.get(focus_file_name, '')}\n```"
            else:
                st.info("Ο Αρχιτέκτονας βλέπει όλο το project για συνολικές αλλαγές.")
                focus_context = "GLOBAL PROJECT CONTEXT (All Files Provided in System Prompt)"

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
                process_request(sel_model, user_in, is_audio, file_contents, structure, focus_file_name, False)

    # --- TAB 2: Autonomous Market/Code Audit ---
    with tab_auto:
        st.header("🛡️ Commercial Audit")
        st.markdown("""
        Ο Αρχιτέκτονας θα σκανάρει το project με τη ματιά ενός **CTO & Product Owner**.
        Στόχος: **Πώληση & Συνδρομητικό Μοντέλο (SaaS)**.
        Θα ψάξει για:
        1. **Scalability:** Αντέχει πολλούς χρήστες;
        2. **Mobile Readiness:** Θα παίξει σε Android/iOS wrapper;
        3. **Value Props:** Είναι αρκετά καλό για να πληρώσει κάποιος;
        """)
        
        if st.button("🚀 ΕΚΤΕΛΕΣΗ ΕΜΠΟΡΙΚΟΥ ΔΙΑΓΝΩΣΤΙΚΟΥ", type="primary"):
            auto_prompt = """
            ACT AS A CTO & PRODUCT OWNER.
            MISSION: This project will be sold as a Subscription SaaS (Android/iOS/Windows).
            1. ANALYZE the entire project code.
            2. IDENTIFY critical bugs or violations of Protected Rules.
            3. PROPOSE features that increase COMMERCIAL VALUE.
            4. IMPLEMENT the most important technical fix immediately.
            
            OUTPUT FORMAT:
            **COMMERCIAL INSIGHT:** (Why this helps selling the app)
            **TECHNICAL FIX:** (The code change)
            ### FILE: path/to/file.py
            ```python
            ... code ...
            ```
            """
            process_request(sel_model, auto_prompt, False, file_contents, structure, "GLOBAL", True)

    # --- SAVE SECTION ---
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
    
    with st.spinner("Thinking (Commercial Strategy & Code)..."):
        try:
            full_context = "PROJECT:\n" + "\n".join([f"--- {k} ---\n{v}" for k,v in files.items()])
            
            # --- COMMERCIAL CEO PROMPT (v12) ---
            prompt = f"""
            ROLE: Senior Python Architect AND Product CEO.
            LANGUAGE: GREEK (Ελληνικά).
            
            MISSION STATEMENT:
            This software is NOT a hobby project. It is a COMMERCIAL PRODUCT to be sold via SUBSCRIPTION (SaaS).
            TARGET PLATFORMS: Web, Android, iOS, Windows (Cross-platform capability is key).
            KEY VALUES: Reliability, Speed, Professional UI, High Perceived Value.
            
            RULES: {PROTECTED_FEATURES}
            
            CONTEXT:
            {full_context}
            
            FOCUS TARGET: {focus_file}
            
            REQUEST: {user_in if not is_audio else "Transcribe and execute."}
            
            INSTRUCTIONS:
            1. If audio, transcribe first.
            2. ALWAYS think about the end-paying customer.
            3. RETURN CODE BLOCKS:
            ### FILE: filename.py
            ```python
            code
            ```
            """
            
            parts = [prompt]
            if is_audio: parts.append({"mime_type": "audio/wav", "data": user_in})
            
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