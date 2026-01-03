import streamlit as st
import os
import re
import shutil
import time
import traceback
import ast
from datetime import datetime

# --- 1. SETUP & IMPORTS ---
try:
    import google.generativeai as genai
    from streamlit_mic_recorder import mic_recorder
except ImportError:
    st.error("Missing libraries. Please run: pip install google-generativeai streamlit-mic-recorder")
    st.stop()

st.set_page_config(page_title="Architect AI v18 (Auto-Discovery)", page_icon="🧭", layout="wide")

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
    """Διαβάζει τη δομή του φακέλου."""
    root_dir = os.path.dirname(os.path.abspath(__file__))
    file_contents = {}
    ignore_dirs = {'.git', '__pycache__', 'venv', '.streamlit', 'backups'} 
    ignore_files = {'.DS_Store', 'token.json', 'credentials.json', 'architect.py', 'secrets.toml'} 

    for dirpath, dirnames, filenames in os.walk(root_dir):
        dirnames[:] = [d for d in dirnames if d not in ignore_dirs]
        for f in filenames:
            if f in ignore_files or f.endswith(('.pyc', '.png', '.jpg', '.pdf', '.mp3')): 
                continue
            
            full_path = os.path.join(dirpath, f)
            rel_path = os.path.relpath(full_path, root_dir)
            
            try:
                with open(full_path, 'r', encoding='utf-8', errors='ignore') as file:
                    file_contents[rel_path] = file.read()
            except Exception as e:
                print(f"Error reading {rel_path}: {e}")

    return file_contents

def backup_file(file_path):
    """Κρατάει backup πριν από κάθε αλλαγή."""
    try:
        if os.path.exists(file_path):
            backup_dir = os.path.join(os.path.dirname(file_path), "backups")
            os.makedirs(backup_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.basename(file_path)
            shutil.copy2(file_path, os.path.join(backup_dir, f"{filename}_{timestamp}.bak"))
            return True
    except Exception as e:
        print(f"Backup failed: {e}")
    return False

def get_best_available_model(api_key):
    """
    🔍 AUTO-DISCOVERY ENGINE
    Ρωτάει την Google τι μοντέλα έχει και διαλέγει το καλύτερο.
    Priority: Flash 1.5 -> Pro 1.5 -> Οτιδήποτε άλλο.
    """
    genai.configure(api_key=api_key)
    try:
        # Λήψη λίστας μοντέλων
        all_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # 1. Ψάχνουμε για FLASH (Το γρήγορο/δωρεάν)
        flash_models = [m for m in all_models if "flash" in m.lower() and "1.5" in m]
        if flash_models: return flash_models[0] # Επιστρέφει π.χ. models/gemini-1.5-flash-latest

        # 2. Αν δεν υπάρχει Flash, ψάχνουμε PRO
        pro_models = [m for m in all_models if "pro" in m.lower() and "1.5" in m]
        if pro_models: return pro_models[0]

        # 3. Αν δεν βρούμε τίποτα από τα παραπάνω, επιστρέφουμε το πρώτο διαθέσιμο
        if all_models: return all_models[0]
        
    except Exception as e:
        print(f"Model Discovery Failed: {e}")
    
    # Fallback (Μαντεψιά αν όλα αποτύχουν)
    return "models/gemini-1.5-flash"

def fix_code_with_ai(file_path, bad_code, error_msg, api_key):
    """SELF-HEALING: Καλεί το AI να διορθώσει το Syntax Error."""
    target_model = get_best_available_model(api_key)
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(target_model)
    
    prompt = f"""
    CRITICAL FIX REQUEST:
    I tried to run the Python code you generated for file '{file_path}', but it failed with a SYNTAX ERROR.
    
    ERROR MESSAGE:
    {error_msg}
    
    THE BAD CODE:
    ```python
    {bad_code}
    ```
    
    MISSION:
    Fix the syntax error. Return ONLY the corrected code block.
    Format:
    ### FILE: {file_path}
    ```python
    # Corrected code here
    ```
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except:
        return None

def apply_changes_from_response(response_text, api_key):
    """
    Εφαρμογή αλλαγών με Syntax Check & Self-Healing Loop.
    """
    pattern = r"### FILE: (.+?)\n.*?```(?:python)?\n(.*?)```"
    matches = re.findall(pattern, response_text, re.DOTALL)
    
    results = []
    
    if not matches:
        return "ℹ️ Δεν βρέθηκαν αλλαγές κώδικα για εφαρμογή."

    for file_path, code_content in matches:
        file_path = file_path.strip()
        file_path = file_path.replace("\\", "/") 
        if file_path.startswith("./"): file_path = file_path[2:]
        
        full_path = os.path.abspath(file_path)
        root_path = os.path.dirname(os.path.abspath(__file__))

        if not full_path.startswith(root_path):
            results.append(f"⛔ SECURITY ALERT: Εκτός φακέλου ({file_path})")
            continue

        # --- SELF HEALING LOOP ---
        attempts = 0
        max_retries = 2
        success = False
        final_code = code_content
        error_details = ""

        while attempts <= max_retries:
            if file_path.endswith(".py"):
                try:
                    ast.parse(final_code)
                    success = True
                    break 
                except SyntaxError as e:
                    error_details = f"{e.msg} (Line {e.lineno})"
                    attempts += 1
                    
                    if attempts <= max_retries:
                        print(f"⚠️ Syntax Error in {file_path}. Healing {attempts}/{max_retries}...")
                        healed_response = fix_code_with_ai(file_path, final_code, error_details, api_key)
                        if healed_response:
                            new_matches = re.findall(pattern, healed_response, re.DOTALL)
                            if new_matches:
                                _, final_code = new_matches[0]
                            else: break 
                        else: break 
                    else: break 

        if success:
            try:
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                backup_file(full_path)
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(final_code.strip())
                
                msg = f"✅ UPDATED: {file_path}"
                if attempts > 0: msg += f" (Healed {attempts} times)"
                results.append(msg)
            except Exception as e:
                results.append(f"❌ ERROR writing {file_path}: {str(e)}")
        else:
             results.append(f"💀 DEAD CODE: {file_path} - Failed to heal: {error_details}")
            
    return "\n".join(results)

def generate_with_auto_pilot(strategy_name, parts, api_key):
    """
    Κύρια μηχανή παραγωγής κώδικα.
    """
    if not api_key: return "ERROR: Missing API Key."
    
    # --- AUTO DISCOVERY ---
    target_model_name = get_best_available_model(api_key)
    
    try:
        # print(f"DEBUG: Using Model -> {target_model_name}") # Ενεργοποίησε για debugging
        model = genai.GenerativeModel(target_model_name)
        
        safety = [{"category": c, "threshold": "BLOCK_NONE"} for c in 
                  ["HARM_CATEGORY_HARASSMENT", "HARM_CATEGORY_HATE_SPEECH", "HARM_CATEGORY_SEXUALLY_EXPLICIT", "HARM_CATEGORY_DANGEROUS_CONTENT"]]
        
        response = model.generate_content(parts, safety_settings=safety)
        return response.text
    except Exception as e:
        return f"CRITICAL AI ERROR: {str(e)} (Tried model: {target_model_name})"

# --- 4. MAIN APPLICATION ---

def main():
    st.title("🧭 Architect AI v18 (Auto-Discovery)")
    
    project_files = get_project_structure()
    file_list = ["None (Global Context)"] + list(project_files.keys())

    with st.sidebar:
        st.header("Settings")
        api_key = st.text_input("Gemini API Key", type="password")
        if not api_key and "GEMINI_API_KEY" in st.secrets:
            api_key = st.secrets["GEMINI_API_KEY"]
            st.success("Key loaded from secrets")
        
        st.markdown("---")
        st.subheader("🛠️ Strategy & Focus")
        
        selected_strategy = st.selectbox(
            "Strategy", 
            ["General Request", "New Feature", "Bug Fix", "Refactoring", "Documentation"]
        )
        
        focus_file = st.selectbox(
            "Focus File (Target)",
            file_list,
            index=0
        )

        st.markdown("---")
        auto_apply = st.checkbox("Auto-Apply & Self-Heal", value=False, help="Ενεργοποιεί την αυτόματη εφαρμογή και το Self-Healing.")
        
        st.caption("Active Rules:")
        for rule in PROTECTED_FEATURES: st.caption(rule)

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    col1, col2 = st.columns([0.85, 0.15])
    with col1: user_in = st.chat_input("Εντολή...")
    with col2: 
        st.write("🎙️")
        audio = mic_recorder(start_prompt="Rec", stop_prompt="Stop", key='recorder')

    final_input = user_in
    is_audio = False
    if audio: 
        final_input = audio['bytes']
        is_audio = True

    if final_input and api_key:
        if not is_audio:
            st.session_state.messages.append({"role": "user", "content": final_input})
            with st.chat_message("user"): st.markdown(final_input)
        else:
            with st.chat_message("user"): st.write("🎤 Audio sent...")

        full_context = "PROJECT FILES:\n" + "\n".join([f"--- {k} ---\n{v[:4000]}..." for k, v in project_files.items()])
        
        prompt_text = f"""
        ROLE: Senior Python Architect (Mastro Nek). LANG: GREEK.
        MISSION: Maintain and upgrade the HVAC Streamlit App.
        STRATEGY: {selected_strategy}
        FOCUS FILE: {focus_file if focus_file != "None (Global Context)" else "ALL"}
        RULES: {PROTECTED_FEATURES}
        
        INSTRUCTIONS:
        1. Analyze the request.
        2. Prioritize changes in FOCUS FILE.
        3. Provide FULL COMPLETE CODE blocks.
        
        FORMAT FOR CHANGES:
        ### FILE: path/to/filename.py
        ```python
        # Full content of the file
        ```
        
        CONTEXT:
        {full_context}
        
        REQUEST: {user_in if not is_audio else "Audio Command"}
        """

        parts = [prompt_text]
        if is_audio: parts.append({"mime_type": "audio/wav", "data": final_input})

        with st.chat_message("assistant"):
            with st.spinner(f"O Αρχιτέκτονας σκανάρει τα μοντέλα & εργάζεται..."):
                response_text = generate_with_auto_pilot(selected_strategy, parts, api_key)
                st.markdown(response_text)
                st.session_state.messages.append({"role": "assistant", "content": response_text})
                
                if auto_apply:
                    with st.status("Έλεγχος & Εφαρμογή Αλλαγών...", expanded=True) as status:
                        st.write("🔍 Έλεγχος Σύνταξης & Self-Healing...")
                        result_log = apply_changes_from_response(response_text, api_key)
                        
                        st.code(result_log)
                        
                        if "UPDATED" in result_log:
                            status.update(label="Επιτυχία! Ο κώδικας ενημερώθηκε.", state="complete", expanded=False)
                            time.sleep(1)
                            st.rerun()
                        elif "DEAD CODE" in result_log:
                            status.update(label="⛔ Αποτυχία Self-Healing.", state="error", expanded=True)
                        else:
                            status.update(label="Δεν βρέθηκαν αλλαγές προς εφαρμογή.", state="complete")

if __name__ == "__main__":
    main()