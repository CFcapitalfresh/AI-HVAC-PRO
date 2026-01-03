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
except ImportError as e:
    st.error("🛑 ΛΕΙΠΟΥΝ ΒΙΒΛΙΟΘΗΚΕΣ!")
    st.info("Τρέξε στο τερματικό: pip install google-generativeai streamlit-mic-recorder")
    st.stop()

# --- 2. ΡΥΘΜΙΣΕΙΣ ---
st.set_page_config(page_title="Architect AI", page_icon="🏗️", layout="wide")

PROTECTED_FEATURES = [
    "1. MICROPHONE/AUDIO: Πάντα κουμπί για φωνητική εντολή στο UI.",
    "2. PDF UPLOAD: Πάντα υποστήριξη PDF/Images.",
    "3. MODULARITY: Χρήση imports (core/modules), όχι μονολιθικός κώδικας.",
    "4. ERROR HANDLING: Πάντα try/except blocks.",
    "5. LANGUAGE: Υποστήριξη GR/EN.",
    "6. STREAMLIT STATE: Έλεγχος initialization keys.",
    "7. DRIVE MANAGER: Προσοχή στο core/drive_manager.py."
]

# --- 3. PROJECT SCANNING ---
def get_project_structure():
    """Σαρώνει το project αναδρομικά."""
    root_dir = os.path.dirname(os.path.abspath(__file__))
    structure = ""
    file_contents = {}
    
    ignore_dirs = {"__pycache__", ".git", ".streamlit", "venv", ".vscode", ".idea", "env", "build", "dist"}
    ignore_files = {"architect.py", "requirements.txt", "README.md", ".DS_Store", ".gitignore", "LICENSE"}
    
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
                except Exception as e:
                    print(f"Error reading {rel_path}: {e}")
                    
    return structure, file_contents, root_dir

def save_code_to_file(rel_path, new_code):
    try:
        root_dir = os.path.dirname(os.path.abspath(__file__))
        clean_path = rel_path.replace("/", os.sep).replace("\\", os.sep)
        full_path = os.path.join(root_dir, clean_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        if os.path.exists(full_path):
            shutil.copy(full_path, f"{full_path}.bak")
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(new_code)
        return True, f"✅ Saved: {rel_path}"
    except Exception as e:
        return False, str(e)

# --- 4. GOOGLE MODELS (LIVE FETCH) ---
@st.cache_data(ttl=600)
def get_available_models(api_key):
    """Ρωτάει την Google τι έχει διαθέσιμο."""
    if not api_key: return []
    genai.configure(api_key=api_key)
    try:
        models = list(genai.list_models())
        names = [m.name for m in models if 'generateContent' in m.supported_generation_methods]
        # Φιλτράρισμα μόνο για Gemini
        names = [n for n in names if "gemini" in n.lower()]
        return sorted(names, reverse=True) # Τα νεότερα πρώτα
    except:
        return []

# --- 5. MAIN APP ---
def main():
    st.title("🏗️ The Architect (Control Mode)")
    
    # --- Sidebar ---
    with st.sidebar:
        # API Key Logic
        api_key = None
        try:
            api_key = st.secrets.get("GEMINI_KEY") or st.secrets.get("general", {}).get("GEMINI_KEY")
        except: pass
            
        if not api_key:
            api_key = st.text_input("🔑 API Key", type="password")
            if not api_key: 
                st.warning("Βάλε κλειδί για να ξεκινήσω.")
                st.stop()
        else:
            st.success("API Key: OK")
        
        # --- MODEL SELECTOR (Η ΛΥΣΗ ΣΟΥ) ---
        st.divider()
        st.subheader("🎛️ Επιλογή Μοντέλου")
        
        with st.spinner("Ρωτάω την Google..."):
            available_models = get_available_models(api_key)
        
        if available_models:
            # Προσπαθούμε να βρούμε το 1.5 Flash ως default
            default_idx = 0
            for i, m in enumerate(available_models):
                if "1.5-flash" in m and "001" in m: # Προτίμηση στο stable 001
                    default_idx = i
                    break
                elif "1.5-flash" in m:
                    default_idx = i
                    break
            
            selected_model = st.selectbox("Διάλεξε Μοντέλο:", available_models, index=default_idx)
            st.info(f"Ενεργό: **{selected_model}**")
        else:
            st.error("Δεν βρέθηκαν μοντέλα. Ίσως το κλειδί έχει θέμα ή η Google είναι πεσμένη.")
            st.stop()

        st.divider()
        if st.button("🔄 Reload Files"): st.rerun()
        if st.button("🗑️ Reset Chat"): 
            st.session_state.messages = []
            st.session_state.pending_changes = [] 
            st.session_state.last_processed_audio = None
            st.rerun()

    # --- Initialization ---
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": f"Γεια! Είμαι συνδεδεμένος με το **{selected_model}**. Πες μου τι να κάνω."}]
    if "pending_changes" not in st.session_state: st.session_state.pending_changes = []
    if "last_processed_audio" not in st.session_state: st.session_state.last_processed_audio = None
    
    # --- Load Files ---
    structure, file_contents, root_path = get_project_structure()
    
    # --- UI ---
    c1, c2 = st.columns([1, 2])
    
    with c1:
        st.subheader("🔎 Σάρωση")
        st.caption(f"Path: `{os.path.basename(root_path)}/`")
        files = sorted(list(file_contents.keys()))
        
        # Smart Select
        def_idx = 0
        for i, f in enumerate(files):
            if "ui_chat.py" in f: def_idx = i; break
        
        target_file = st.selectbox("Εστίαση σε:", files, index=def_idx)
        with st.expander("Προβολή Κώδικα", expanded=True):
            st.code(file_contents.get(target_file, ""), language="python")

    with c2:
        st.subheader("💬 Εντολές")
        chat_container = st.container(height=500)
        with chat_container:
            for msg in st.session_state.messages:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])
        
        # Inputs
        t_mic, t_txt = st.tabs(["🎙️", "⌨️"])
        user_in = None
        is_audio = False
        
        with t_mic:
            ad = mic_recorder(start_prompt="🔴 REC", stop_prompt="⏹️ STOP", key='main_rec')
            if ad and ad['id'] != st.session_state.last_processed_audio:
                user_in = ad['bytes']
                is_audio = True
                st.session_state.last_processed_audio = ad['id']
        with t_txt:
            tx = st.chat_input("Εντολή...")
            if tx: user_in = tx

        # --- PROCESS ---
        if user_in:
            if is_audio: st.session_state.messages.append({"role": "user", "content": "🎤 *(Audio)*"})
            else: st.session_state.messages.append({"role": "user", "content": user_in})
            
            with st.spinner(f"Εκτέλεση με {selected_model}..."):
                try:
                    # Χρησιμοποιούμε το μοντέλο που ΔΙΑΛΕΞΕ Ο ΧΡΗΣΤΗΣ
                    model = genai.GenerativeModel(selected_model)
                    
                    full_context = "PROJECT:\n"
                    for f, c in file_contents.items():
                        full_context += f"\n--- FILE: {f} ---\n{c}\n"
                    
                    prompt = f"""
                    ROLE: Expert Python Dev. LANGUAGE: GREEK.
                    MODEL: {selected_model}
                    RULES: {PROTECTED_FEATURES}
                    CONTEXT: {full_context}
                    FOCUS FILE: {target_file}
                    
                    INSTRUCTION:
                    1. If AUDIO input: Start response with **🎧 Άκουσα:** "...".
                    2. Output code blocks with: ### FILE: filename.py
                    """
                    
                    parts = [prompt]
                    if is_audio: parts.append({"mime_type": "audio/wav", "data": user_in})
                    else: parts.append(f"USER REQUEST: {user_in}")

                    resp = model.generate_content(parts).text
                    st.session_state.messages.append({"role": "assistant", "content": resp})
                    
                    # Parse
                    changes = []
                    for f, c in re.findall(r"### FILE: (.+?)\n.*?```python(.*?)```", resp, re.DOTALL):
                        changes.append({"filename": f.strip(), "code": c.strip()})
                    
                    if changes: st.session_state.pending_changes = changes
                    st.rerun()

                except Exception as e:
                    st.error(f"AI Error ({selected_model}): {e}")

    # --- SAVE ---
    if st.session_state.pending_changes:
        st.divider()
        st.success(f"✅ Έτοιμα {len(st.session_state.pending_changes)} αρχεία!")
        
        for idx, change in enumerate(st.session_state.pending_changes):
            with st.expander(f"📄 {change['filename']}", expanded=True):
                st.code(change['code'], language="python")
        
        if st.button("💾 ΑΠΟΘΗΚΕΥΣΗ ΟΛΩΝ", type="primary"):
            for ch in st.session_state.pending_changes:
                save_code_to_file(ch['filename'], ch['code'])
            st.success("Saved!")
            st.session_state.pending_changes = []
            time.sleep(1)
            st.rerun()

if __name__ == "__main__":
    try: main()
    except: st.error(traceback.format_exc())