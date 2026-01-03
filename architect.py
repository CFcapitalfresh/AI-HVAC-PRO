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

# --- 4. DYNAMIC MODEL SELECTOR (ΕΔΩ ΕΙΝΑΙ Η "ΕΞΥΠΝΑΔΑ") ---
def get_optimal_model_name(api_key):
    genai.configure(api_key=api_key)
    try:
        # Βήμα 1: Ρωτάμε την Google τι έχει διαθέσιμο
        models = list(genai.list_models())
        available_names = [m.name for m in models if 'generateContent' in m.supported_generation_methods]
        
        # Η λίστα προτίμησής μας (από το καλύτερο στο χειρότερο)
        priority_list = [
            "models/gemini-1.5-flash", 
            "models/gemini-1.5-flash-latest",
            "models/gemini-1.5-pro",
            "models/gemini-pro"
        ]

        # Βήμα 2: Ψάχνουμε αν υπάρχει το αγαπημένο μας στα διαθέσιμα
        for priority in priority_list:
            if priority in available_names: return priority

        # Βήμα 3: Αν δεν βρούμε τα γνωστά, παίρνουμε όποιο gemini βρούμε
        for name in available_names:
            if "gemini" in name and "vision" not in name: return name
        
        # Fallback (Ασφάλεια)
        return "models/gemini-1.5-flash"
    except Exception as e:
        st.error(f"Google API Error: {e}")
        return None

# --- 5. MAIN APPLICATION ---
def main():
    st.title("🏗️ The Architect (Safe Secrets Mode)")
    
    # --- Sidebar ---
    with st.sidebar:
        # --- FIXED: Try/Except για να μην κρασάρει αν λείπουν τα secrets ---
        api_key = None
        try:
            # Προσπαθούμε να διαβάσουμε, αλλά αν αποτύχει δεν σκάει η εφαρμογή
            api_key = st.secrets.get("GEMINI_KEY") or st.secrets.get("general", {}).get("GEMINI_KEY")
        except FileNotFoundError:
            pass # Δεν υπάρχει αρχείο secrets.toml, συνεχίζουμε
        except Exception:
            pass # Οποιοδήποτε άλλο λάθος
            
        # Αν δεν βρέθηκε αυτόματα, ζητάμε από τον χρήστη να το δώσει
        if not api_key:
            api_key = st.text_input("🔑 API Key (Επικόλληση εδώ)", type="password")
            if not api_key:
                st.warning("⚠️ Απαιτείται API Key για να ξεκινήσει.")
                st.stop() # Σταματάμε εδώ ήρεμα, χωρίς crash
        else:
            st.success("✅ API Key: Loaded")
        
        st.divider()
        if st.button("🔄 Reload Files"): st.rerun()
        if st.button("🗑️ Reset Chat"): 
            st.session_state.messages = []
            st.session_state.pending_changes = [] 
            st.session_state.last_processed_audio = None
            st.rerun()

    # --- Initialization ---
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "Γεια! Μπορώ να δημιουργήσω ή να τροποποιήσω πολλαπλά αρχεία αυτόματα. Τι χρειάζεσαι;"}]
    if "pending_changes" not in st.session_state: st.session_state.pending_changes = []
    if "last_processed_audio" not in st.session_state: st.session_state.last_processed_audio = None
    
    # --- Load Files ---
    structure, file_contents, root_path = get_project_structure()
    files = sorted(list(file_contents.keys()))
    
    if not files:
        st.error(f"⚠️ Δεν βρέθηκαν αρχεία στο: {root_path}")
        st.stop()

    # --- UI Layout ---
    c1, c2 = st.columns([1, 2])
    
    with c1:
        st.subheader("🔭 Εύρος Όρασης")
        scope_mode = st.radio("Mode:", 
                             ["📂 Ένα Αρχείο (Focus)", "🌍 Όλο το Project (Global)"],
                             index=0)
        
        target_file_context = None
        
        if scope_mode == "📂 Ένα Αρχείο (Focus)":
            def_idx = 0
            for i, f in enumerate(files):
                if "ui_chat.py" in f: def_idx = i; break
            
            selected_existing = st.selectbox("Επιλογή Αρχείου:", files, index=def_idx)
            
            with st.expander("📄 Προβολή Κώδικα", expanded=True):
                st.code(file_contents.get(selected_existing, ""), language="python")
            
            target_file_context = f"FILE: {selected_existing}\nCODE:\n{file_contents.get(selected_existing, '')}"
        else:
            st.info(f"✅ Ο Αρχιτέκτονας βλέπει ΚΑΙ τα {len(files)} αρχεία.")
            # Global Context
            target_file_context = "FULL PROJECT:\n"
            for f, c in file_contents.items():
                target_file_context += f"\n--- FILE: {f} ---\n{c}\n"

    with c2:
        st.subheader("💬 Συζήτηση")
        chat_container = st.container(height=500)
        with chat_container:
            for msg in st.session_state.messages:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])
        
        # Inputs
        tab_mic, tab_txt = st.tabs(["🎙️ Μικρόφωνο", "⌨️ Πληκτρολόγιο"])
        user_input_content = None
        is_audio = False
        
        with tab_mic:
            st.write("Πες την εντολή:")
            audio_data = mic_recorder(start_prompt="🔴 REC", stop_prompt="⏹️ STOP", key='main_rec')
            if audio_data and audio_data['id'] != st.session_state.last_processed_audio:
                user_input_content = audio_data['bytes']
                is_audio = True
                st.session_state.last_processed_audio = audio_data['id']

        with tab_txt:
            txt_in = st.chat_input("Γράψε εδώ...", key="txt_in_widget")
            if txt_in:
                user_input_content = txt_in
                is_audio = False

        # --- AI PROCESSING ---
        if user_input_content:
            if is_audio:
                st.session_state.messages.append({"role": "user", "content": "🎤 *(Φωνητικό Μήνυμα)*"})
            else:
                st.session_state.messages.append({"role": "user", "content": user_input_content})
            
            with st.spinner("🧠 Ανάλυση & Σύνταξη Κώδικα..."):
                try:
                    # ΕΔΩ ΚΑΛΟΥΜΕ ΤΗΝ ΕΞΥΠΝΗ ΣΥΝΑΡΤΗΣΗ
                    model_name = get_optimal_model_name(api_key)
                    if not model_name: st.stop()
                    model = genai.GenerativeModel(model_name)
                    
                    prompt_parts = []
                    system_instructions = f"""
                    ROLE: You are 'The Architect', a Python Expert.
                    LANGUAGE: GREEK.
                    GOAL: Generate code for one or more files based on user request.
                    
                    PROJECT MAP:
                    {structure}
                    
                    PROTECTED RULES:
                    {PROTECTED_FEATURES}
                    
                    CONTEXT:
                    {target_file_context}
                    
                    INSTRUCTIONS:
                    1. If AUDIO input: Start with **🎧 Άκουσα:** "...".
                    2. Explain plan briefly.
                    3. Ask CONFIRMATION before generating code.
                    4. IMPORTANT: If generating code, use this EXACT format for EACH file:
                    
                    ### FILE: path/to/filename.py
                    ```python
                    # ... code here ...
                    ```
                    
                    You can output multiple files if needed (e.g., update main.py AND create new_module.py).
                    If a file is new, just specify the new path.
                    """
                    prompt_parts.append(system_instructions)
                    
                    for m in st.session_state.messages[-6:]:
                        if m["role"] != "system" and "🎤" not in m["content"]:
                            prompt_parts.append(f"{m['role'].upper()}: {m['content']}")
                    
                    if is_audio:
                        prompt_parts.append("USER (AUDIO INPUT):")
                        prompt_parts.append({"mime_type": "audio/wav", "data": user_input_content})
                    else:
                        prompt_parts.append(f"USER: {user_input_content}")

                    response = model.generate_content(prompt_parts)
                    reply = response.text
                    st.session_state.messages.append({"role": "assistant", "content": reply})
                    
                    # --- AUTO-DETECT FILES FROM RESPONSE ---
                    file_pattern = r"### FILE: (.+?)\n.*?```python(.*?)```"
                    matches = re.findall(file_pattern, reply, re.DOTALL)
                    
                    new_changes = []
                    for filename, code in matches:
                        new_changes.append({
                            "filename": filename.strip(),
                            "code": code.strip()
                        })
                    
                    if new_changes:
                        st.session_state.pending_changes = new_changes
                    
                    st.rerun()

                except Exception as e:
                    st.error(f"AI Error: {e}")

    # --- SAVE SECTION (AUTO-DETECTED) ---
    if st.session_state.pending_changes:
        st.divider()
        st.success(f"✅ Ο Αρχιτέκτονας ετοίμασε {len(st.session_state.pending_changes)} αρχεία!")
        
        for idx, change in enumerate(st.session_state.pending_changes):
            with st.expander(f"📄 {change['filename']}", expanded=True):
                st.code(change['code'], language="python")
        
        col_s, col_c = st.columns([1, 4])
        if col_s.button("💾 ΑΠΟΘΗΚΕΥΣΗ ΟΛΩΝ", type="primary"):
            success_count = 0
            for change in st.session_state.pending_changes:
                ok, msg = save_code_to_file(change['filename'], change['code'])
                if ok: success_count += 1
                else: st.error(msg)
            
            if success_count == len(st.session_state.pending_changes):
                st.balloons()
                st.success("✅ Όλα τα αρχεία αποθηκεύτηκαν επιτυχώς!")
                st.session_state.pending_changes = []
                time.sleep(2)
                st.rerun()
        
        if col_c.button("Ακύρωση"):
            st.session_state.pending_changes = []
            st.rerun()

# --- ENTRY POINT ---
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error("💣 CRITICAL ERROR")
        st.code(traceback.format_exc())