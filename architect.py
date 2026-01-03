import streamlit as st
import os
import shutil
import traceback
import time
import re

# --- 1. SETUP ---
try:
    import google.generativeai as genai
    from streamlit_mic_recorder import mic_recorder
except ImportError:
    st.error("Missing libraries. Run: pip install google-generativeai streamlit-mic-recorder")
    st.stop()

st.set_page_config(page_title="Architect AI v13", page_icon="🏗️", layout="wide")

# --- 2. PROTECTED RULES ---
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

# --- 4. SMART AUTO-PILOT LOGIC (v13 NEW) ---
@st.cache_data(ttl=600)
def get_available_models(api_key):
    """Φέρνει τα μοντέλα αλλά προσθέτει και την επιλογή Auto-Pilot."""
    if not api_key: return []
    genai.configure(api_key=api_key)
    
    base_options = ["✨ Auto-Pilot (Smart Switch)"] # Default επιλογή
    
    try:
        models = list(genai.list_models())
        fetched = [m.name for m in models if 'generateContent' in m.supported_generation_methods and "gemini" in m.name.lower()]
        fetched.sort(key=lambda x: (0 if "flash" in x else 1 if "pro" in x else 2))
        return base_options + fetched
    except: 
        return base_options + ["models/gemini-1.5-flash", "models/gemini-1.5-pro"]

def generate_with_auto_pilot(selected_option, prompt_parts):
    """
    Η καρδιά του v13:
    Αν ο χρήστης διάλεξε 'Auto-Pilot', δοκιμάζει Flash -> Αν αποτύχει -> Pro -> Αν αποτύχει -> Wait.
    Αν ο χρήστης διάλεξε συγκεκριμένο μοντέλο, σέβεται την επιλογή του.
    """
    # 1. Καθορισμός στρατηγικής
    if "Auto-Pilot" in selected_option:
        # Σειρά προτεραιότητας: Flash (Γρήγορο) -> Pro (Δυνατό) -> Flash Legacy
        strategy = ["models/gemini-1.5-flash", "models/gemini-1.5-pro", "models/gemini-1.0-pro"]
    else:
        # Χειροκίνητη επιλογή
        strategy = [selected_option]

    last_error = None
    
    # 2. Εκτέλεση με Failover
    for model_name in strategy:
        model = genai.GenerativeModel(model_name)
        try:
            # Δοκιμή χωρίς αναμονή πρώτα
            return model.generate_content(prompt_parts).text
        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "Quota" in error_str:
                st.warning(f"⚠️ Το {model_name} είναι γεμάτο (429). Δοκιμάζω το επόμενο...")
                last_error = e
                continue # Πάμε στο επόμενο μοντέλο της λίστας
            else:
                raise e # Αν είναι άλλο λάθος (π.χ. λάθος prompt), σταματάμε

    # 3. Αν αποτύχουν όλα, τότε περιμένουμε (Backoff) στο Flash
    st.warning("⚠️ Όλα τα μοντέλα είναι φορτωμένα. Ενεργοποίηση Αναμονής (Auto-Retry)...")
    fallback_model = genai.GenerativeModel("models/gemini-1.5-flash")
    
    for i in range(3):
        try:
            time.sleep(5 * (i + 1))
            return fallback_model.generate_content(prompt_parts).text
        except Exception as e:
            last_error = e
            
    raise Exception(f"Ο Auto-Pilot απέτυχε μετά από πολλαπλές προσπάθειες. Τελευταίο λάθος: {last_error}")

# --- 5. MAIN LOGIC ---
def main():
    st.title("🏗️ The Architect v13 (Auto-Pilot)")
    
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
            
        # Model Selector (v13 Update)
        models = get_available_models(api_key)
        sel_model = st.selectbox("Model Strategy:", models, index=0) # Default: Auto-Pilot

        if st.button("🗑️ Reset"): 
            st.session_state.messages = []
            st.session_state.pending_changes = []
            st.session_state.last_audio = None
            st.rerun()

    # Session
    if "messages" not in st.session_state: st.session_state.messages = [{"role":"assistant", "content": "Auto-Pilot Active. Πες μου τι να κάνω."}]
    if "pending_changes" not in st.session_state: st.session_state.pending_changes = []
    if "last_audio" not in st.session_state: st.session_state.last_audio = None

    # Load Files
    structure, file_contents, root = get_project_structure()
    
    # --- TABS ---
    tab_chat, tab_auto = st.tabs(["💬 Chat", "🛡️ Market Audit"])

    # --- TAB 1: Chat ---
    with tab_chat:
        c1, c2 = st.columns([1, 2])
        with c1:
            st.caption(f"Scanning: `{os.path.basename(root)}/`")
            scope_mode = st.radio("🔭 Scope:", ["📂 Ένα Αρχείο", "🌍 Όλο το Project"])
            
            focus_context = ""
            focus_file_name = "GLOBAL"
            
            if scope_mode == "📂 Ένα Αρχείο":
                all_files = sorted(list(file_contents.keys()))
                def_ix = 0
                for i, f in enumerate(all_files): 
                    if "ui_chat.py" in f: def_ix = i
                
                focus_file_name = st.selectbox("Select:", all_files, index=def_ix)
                with st.expander("Code"):
                    st.code(file_contents.get(focus_file_name, ""), language="python")
                focus_context = f"FILE ({focus_file_name}):\n```python\n{file_contents.get(focus_file_name, '')}\n```"
            else:
                focus_context = "GLOBAL CONTEXT (All Files)"

        with c2:
            for m in st.session_state.messages:
                with st.chat_message(m["role"]): st.markdown(m["content"])
            
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

    # --- TAB 2: Audit ---
    with tab_auto:
        st.header("🛡️ Commercial Audit")
        if st.button("🚀 FULL AUDIT", type="primary"):
            auto_prompt = "ACT AS CTO. Analyze for Commercial/SaaS Value. Identify Bugs. Fix the most critical one."
            process_request(sel_model, auto_prompt, False, file_contents, structure, "GLOBAL", True)

    # --- SAVE ---
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

def process_request(strategy_name, user_in, is_audio, files, structure, focus_file, is_auto):
    if is_audio: st.session_state.messages.append({"role":"user", "content":"🎤 Audio"})
    elif not is_auto: st.session_state.messages.append({"role":"user", "content":user_in})
    
    with st.spinner(f"Auto-Pilot ({strategy_name})..."):
        try:
            full_context = "PROJECT:\n" + "\n".join([f"--- {k} ---\n{v}" for k,v in files.items()])
            
            prompt = f"""
            ROLE: Senior Python Architect. LANG: GREEK.
            MISSION: Build a Commercial SaaS HVAC App.
            RULES: {PROTECTED_FEATURES}
            CONTEXT: {full_context}
            FOCUS: {focus_file}
            REQUEST: {user_in if not is_audio else "Transcribe & Execute"}
            OUTPUT: 
            ### FILE: filename.py
            ```python
            code
            ```
            """
            
            parts = [prompt]
            if is_audio: parts.append({"mime_type": "audio/wav", "data": user_in})
            
            # CALL v13 SMART LOGIC
            resp = generate_with_auto_pilot(strategy_name, parts)
            
            st.session_state.messages.append({"role":"assistant", "content":resp})
            
            changes = []
            for f, c in re.findall(r"### FILE: (.+?)\n.*?```python(.*?)```", resp, re.DOTALL):
                changes.append({"file": f.strip(), "code": c.strip()})
            
            if changes: st.session_state.pending_changes = changes
            st.rerun()
        except Exception as e:
            st.error(f"Critical Error: {e}")

if __name__ == "__main__":
    main()