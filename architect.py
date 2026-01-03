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

# --- 2. ΡΥΘΜΙΣΕΙΣ & CONSTANTS ---
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

# --- 3. ΒΟΗΘΗΤΙΚΕΣ ΣΥΝΑΡΤΗΣΕΙΣ ---
def get_project_structure():
    """Σαρώνει το project αναδρομικά (Deep Scan)."""
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
    """Αποθηκεύει τον κώδικα (Δημιουργεί και φακέλους αν χρειαστεί)."""
    try:
        root_dir = os.path.dirname(os.path.abspath(__file__))
        clean_path = rel_path.replace("/", os.sep).replace("\\", os.sep)
        full_path = os.path.join(root_dir, clean_path)
        
        # Δημιουργία φακέλου αν δεν υπάρχει
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        # Backup αν υπάρχει ήδη
        if os.path.exists(full_path):
            shutil.copy(full_path, f"{full_path}.bak")
            
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(new_code)
        return True, f"✅ Saved: {rel_path}"
    except Exception as e:
        return False, str(e)

# --- 4. DYNAMIC MODEL SELECTOR ---
def get_optimal_model_name(api_key):
    genai.configure(api_key=api_key)
    try:
        models = list(genai.list_models())
        available_names = [m.name for m in models if 'generateContent' in m.supported_generation_methods]
        
        priority_list = [
            "models/gemini-1.5-flash", 
            "models/gemini-1.5-flash-latest",
            "models/gemini-1.5-pro",
            "models/gemini-pro"
        ]

        for priority in priority_list:
            if priority in available_names: return priority

        for name in available_names:
            if "gemini" in name and "vision" not in name: return name
                
        return "models/gemini-1.5-flash"
    except Exception as e:
        st.error(f"Google API Error: {e}")
        return None

# --- 5. MAIN APPLICATION ---
def main():
    st.title("🏗️ The Architect (Autonomous)")
    
    # --- Sidebar ---
    with st.sidebar:
        api_key = None
        try:
            api_key = st.secrets.get("GEMINI_KEY") or st.secrets.get("general", {}).get("GEMINI_KEY")
        except: pass
            
        if not api_key:
            api_key = st.text_input("🔑 API Key", type="password")
            if not api_key:
                st.warning("Input API Key to start.")
                st.stop()
        else:
            st.success("✅ API Key: Active")
        
        st.divider()
        if st.button("🔄 Reload Files"): st.rerun()
        if st.button("🗑️ Reset All"): 
            st.session_state.messages = []
            st.session_state.pending_changes = [] 
            st.session_state.last_processed_audio = None
            st.rerun()

    # --- Initialization ---
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "Γεια! Είμαι σε κατάσταση αναμονής. Δώσε εντολή ή ξεκίνα τον αυτόματο έλεγχο."}]
    if "pending_changes" not in st.session_state: st.session_state.pending_changes = []
    if "last_processed_audio" not in st.session_state: st.session_state.last_processed_audio = None
    
    # --- Load Files ---
    structure, file_contents, root_path = get_project_structure()
    files = sorted(list(file_contents.keys()))
    
    # --- UI Layout ---
    tab_chat, tab_auto = st.tabs(["💬 Εντολές & Chat", "🛡️ Αυτόματος Έλεγχος & Προσομοίωση"])

    # ---------------------------------------------------------
    # TAB 1: ΚΛΑΣΙΚΗ ΣΥΖΗΤΗΣΗ (CHAT)
    # ---------------------------------------------------------
    with tab_chat:
        c1, c2 = st.columns([1, 2])
        
        with c1:
            st.subheader("🔭 Scope")
            scope_mode = st.radio("Focus:", ["📂 Ένα Αρχείο", "🌍 Όλο το Project"], index=0)
            
            target_file_context = None
            
            if scope_mode == "📂 Ένα Αρχείο":
                def_idx = 0
                for i, f in enumerate(files):
                    if "ui_chat.py" in f: def_idx = i; break
                
                selected_existing = st.selectbox("Επιλογή:", files, index=def_idx)
                with st.expander("Code Preview"):
                    st.code(file_contents.get(selected_existing, ""), language="python")
                target_file_context = f"FILE: {selected_existing}\nCODE:\n{file_contents.get(selected_existing, '')}"
            else:
                st.info(f"Scanning {len(files)} files.")
                target_file_context = "FULL PROJECT:\n"
                for f, c in file_contents.items():
                    target_file_context += f"\n--- FILE: {f} ---\n{c}\n"

        with c2:
            chat_container = st.container(height=400)
            with chat_container:
                for msg in st.session_state.messages:
                    with st.chat_message(msg["role"]):
                        st.markdown(msg["content"])
            
            # Inputs
            sub_mic, sub_txt = st.tabs(["🎙️", "⌨️"])
            user_in = None
            is_aud = False
            
            with sub_mic:
                ad = mic_recorder(start_prompt="🔴", stop_prompt="⏹️", key='chat_mic_rec')
                if ad and ad['id'] != st.session_state.last_processed_audio:
                    user_in = ad['bytes']
                    is_aud = True
                    st.session_state.last_processed_audio = ad['id']
            with sub_txt:
                txt = st.chat_input("Εντολή...")
                if txt: user_in = txt

            if user_in:
                process_ai_request(api_key, user_in, is_aud, target_file_context, structure)

    # ---------------------------------------------------------
    # TAB 2: ΑΥΤΟΜΑΤΟΣ ΕΛΕΓΧΟΣ (AUTONOMOUS MODE)
    # ---------------------------------------------------------
    with tab_auto:
        st.header("🛡️ Autonomous Self-Improvement")
        st.markdown("""
        Σε αυτή τη λειτουργία, ο Αρχιτέκτονας:
        1. **Σαρώνει** όλο τον κώδικα.
        2. **Προσομοιώνει** σενάρια χρήσης για να βρει αδυναμίες.
        3. **Προτείνει** αυτόματα βελτιώσεις χωρίς δική σου εντολή.
        """)
        
        if st.button("🚀 ΕΚΤΕΛΕΣΗ ΔΙΑΓΝΩΣΤΙΚΟΥ & ΠΡΟΤΑΣΗ ΑΝΑΒΑΘΜΙΣΗΣ", type="primary", use_container_width=True):
            with st.spinner("🕵️ Ο Αρχιτέκτονας μελετάει τον κώδικα..."):
                # Ετοιμάζουμε το Global Context
                full_context = "FULL PROJECT:\n"
                for f, c in file_contents.items():
                    full_context += f"\n--- FILE: {f} ---\n{c}\n"
                
                # Αυτόνομο Prompt
                auto_prompt = """
                ACT AS AN AUTONOMOUS CODE AUDITOR.
                1. ANALYZE the entire project code provided in Context.
                2. SIMULATE user scenarios (e.g. uploading wrong files, network errors, clicking buttons rapidly).
                3. IDENTIFY the single most critical weakness, bug, or missing feature based on "Protected Rules".
                4. WRITE the complete fixed code for the specific file that needs upgrade.
                5. Explain your reasoning briefly.
                
                OUTPUT FORMAT:
                REASONING: ...
                ### FILE: path/to/file.py
                ```python
                ... code ...
                ```
                """
                
                process_ai_request(api_key, auto_prompt, False, full_context, structure, is_autonomous=True)

    # --- SAVE SECTION ---
    if st.session_state.pending_changes:
        st.divider()
        st.success(f"✅ Ο Αρχιτέκτονας ετοίμασε {len(st.session_state.pending_changes)} αρχεία!")
        
        for idx, change in enumerate(st.session_state.pending_changes):
            with st.expander(f"📄 {change['filename']}", expanded=True):
                st.code(change['code'], language="python")
        
        col_s, col_c = st.columns([1, 4])
        if col_s.button("💾 ΑΠΟΘΗΚΕΥΣΗ ΟΛΩΝ", type="primary"):
            cnt = 0
            for change in st.session_state.pending_changes:
                ok, msg = save_code_to_file(change['filename'], change['code'])
                if ok: cnt += 1
                else: st.error(msg)
            
            if cnt == len(st.session_state.pending_changes):
                st.balloons()
                st.success("✅ Όλα αποθηκεύτηκαν!")
                st.session_state.pending_changes = []
                time.sleep(2)
                st.rerun()
        
        if col_c.button("Ακύρωση"):
            st.session_state.pending_changes = []
            st.rerun()

# --- AI LOGIC FUNCTION ---
def process_ai_request(api_key, user_input, is_audio, context, structure, is_autonomous=False):
    try:
        model_name = get_optimal_model_name(api_key)
        model = genai.GenerativeModel(model_name)
        
        if is_audio:
            st.session_state.messages.append({"role": "user", "content": "🎤 *(Audio)*"})
        elif not is_autonomous:
            st.session_state.messages.append({"role": "user", "content": user_input})
            
        prompt_parts = []
        sys_prompt = f"""
        ROLE: Architect AI (Senior Python Dev). Lang: GREEK.
        PROJECT STRUCTURE: {structure}
        RULES: {PROTECTED_FEATURES}
        CONTEXT: {context}
        INSTRUCTIONS:
        - If Audio, start with **🎧 Άκουσα:** ...
        - If Autonomous, explain the logic found.
        - GENERATE CODE FORMAT:
        ### FILE: filename.py
        ```python
        ...
        ```
        """
        prompt_parts.append(sys_prompt)
        
        if is_audio:
            prompt_parts.append({"mime_type": "audio/wav", "data": user_input})
        else:
            prompt_parts.append(f"REQUEST: {user_input}")

        response = model.generate_content(prompt_parts)
        reply = response.text
        
        st.session_state.messages.append({"role": "assistant", "content": reply})
        
        # Parse Code
        file_pattern = r"### FILE: (.+?)\n.*?```python(.*?)```"
        matches = re.findall(file_pattern, reply, re.DOTALL)
        
        new_changes = []
        for fname, code in matches:
            new_changes.append({"filename": fname.strip(), "code": code.strip()})
        
        if new_changes:
            st.session_state.pending_changes = new_changes
        
        st.rerun()
        
    except Exception as e:
        st.error(f"AI Error: {e}")

if __name__ == "__main__":
    try: main()
    except: st.error(traceback.format_exc())