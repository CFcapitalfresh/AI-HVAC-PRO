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

st.set_page_config(page_title="Architect AI v16 (Self-Healing)", page_icon="❤️‍🩹", layout="wide")

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

def fix_code_with_ai(file_path, bad_code, error_msg, api_key):
    """
    SELF-HEALING MODULE:
    Καλεί το Gemini να διορθώσει το λάθος σύνταξης που έκανε.
    """
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("models/gemini-1.5-flash")
    
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
    VERSION 16 - SELF HEALING:
    1. Βρίσκει τον κώδικα.
    2. Syntax Check.
    3. ΑΝ ΑΠΟΤΥΧΕΙ -> Καλεί fix_code_with_ai (μέχρι 2 φορές).
    4. Σώζει μόνο αν περάσει το τεστ.
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

        # --- LOOP ΑΥΤΟ-ΘΕΡΑΠΕΙΑΣ (MAX 2 RETRIES) ---
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
                    break # Όλα καλά, βγαίνουμε από το loop
                except SyntaxError as e:
                    error_details = f"{e.msg} (Line {e.lineno})"
                    attempts += 1
                    
                    if attempts <= max_retries:
                        print(f"⚠️ Syntax Error in {file_path}. Attempting Self-Heal {attempts}/{max_retries}...")
                        # Κλήση στο Γιατρό (AI)
                        healed_response = fix_code_with_ai(file_path, final_code, error_details, api_key)
                        
                        if healed_response:
                            # Εξαγωγή του νέου κώδικα από την απάντηση θεραπείας
                            new_matches = re.findall(pattern, healed_response, re.DOTALL)
                            if new_matches:
                                _, final_code = new_matches[0] # Παίρνουμε τον νέο κώδικα
                            else:
                                break # Το AI δεν επέστρεψε σωστό format
                        else:
                            break # Απέτυχε η σύνδεση
                    else:
                        break # Τέλος προσπαθειών

        # --- ΤΕΛΙΚΗ ΕΤΥΜΗΓΟΡΙΑ ---
        if success:
            try:
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                backup_file(full_path)
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(final_code.strip())
                
                if attempts == 0:
                    results.append(f"✅ UPDATED: {file_path}")
                else:
                    results.append(f"❤️‍🩹 HEALED & UPDATED: {file_path} (Μετά από {attempts} διορθώσεις)")
            except Exception as e:
                results.append(f"❌ ERROR writing {file_path}: {str(e)}")
        else:
             results.append(f"💀 DEAD CODE: {file_path} - Το AI απέτυχε να διορθώσει το Syntax Error: {error_details}")
            
    return "\n".join(results)

def generate_with_auto_pilot(strategy_name, parts, api_key):
    """
    GEMINI 1.5 FLASH (ΜΟΝΟΔΡΟΜΟΣ)
    """
    if not api_key: return "ERROR: Missing API Key."
    genai.configure(api_key=api_key)

    preferred_models = ["gemini-1.5-flash", "models/gemini-1.5-flash", "gemini-1.5-pro"]
    selected_model_name = "models/gemini-1.5-flash"

    try:
        available = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        for p in preferred_models:
            match = next((m for m in available if p in m), None)
            if match:
                selected_model_name = match
                break
    except: pass

    try:
        model = genai.GenerativeModel(selected_model_name)
        safety = [{"category": c, "threshold": "BLOCK_NONE"} for c in 
                  ["HARM_CATEGORY_HARASSMENT", "HARM_CATEGORY_HATE_SPEECH", "HARM_CATEGORY_SEXUALLY_EXPLICIT", "HARM_CATEGORY_DANGEROUS_CONTENT"]]
        response = model.generate_content(parts, safety_settings=safety)
        return response.text
    except Exception as e:
        return f"CRITICAL AI ERROR: {str(e)}"

# --- 4. MAIN APPLICATION ---

def main():
    st.title("❤️‍🩹 Architect AI v16 (Self-Healing)")
    
    with st.sidebar:
        st.header("Settings")
        api_key = st.text_input("Gemini API Key", type="password")
        if not api_key and "GEMINI_API_KEY" in st.secrets:
            api_key = st.secrets["GEMINI_API_KEY"]
            st.success("Key loaded from secrets")
        
        # Επιλογή λειτουργίας
        auto_apply = st.checkbox("Auto-Apply Changes", value=False, help="Ενεργοποιεί την αυτόματη εφαρμογή και το Self-Healing.")
        
        st.markdown("---")
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

        files = get_project_structure()
        full_context = "PROJECT FILES:\n" + "\n".join([f"--- {k} ---\n{v[:3000]}..." for k, v in files.items()])
        
        prompt_text = f"""
        ROLE: Senior Python Architect (Mastro Nek). LANG: GREEK.
        MISSION: Maintain and upgrade the HVAC Streamlit App.
        RULES: {PROTECTED_FEATURES}
        
        INSTRUCTIONS:
        1. Analyze the request.
        2. Provide FULL COMPLETE CODE for the files that need changing.
        3. Use the format below EXACTLY.
        
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
            with st.spinner("O Αρχιτέκτονας ελέγχει τα σχέδια (Gemini 1.5 Flash)..."):
                response_text = generate_with_auto_pilot("Auto", parts, api_key)
                st.markdown(response_text)
                st.session_state.messages.append({"role": "assistant", "content": response_text})
                
                # --- AUTO APPLY LOGIC (WITH SELF HEALING) ---
                if auto_apply:
                    with st.status("Έλεγχος & Εφαρμογή Αλλαγών...", expanded=True) as status:
                        st.write("🔍 Έλεγχος Σύνταξης & Self-Healing...")
                        # Περνάμε και το api_key για να μπορεί να κάνει healing
                        result_log = apply_changes_from_response(response_text, api_key)
                        
                        st.code(result_log)
                        
                        if "UPDATED" in result_log:
                            status.update(label="Επιτυχία! Ο κώδικας ενημερώθηκε.", state="complete", expanded=False)
                            time.sleep(1)
                            st.rerun()
                        elif "DEAD CODE" in result_log:
                            status.update(label="⛔ Αποτυχία: Το Self-Healing δεν μπόρεσε να φτιάξει το λάθος.", state="error", expanded=True)
                        else:
                            status.update(label="Δεν βρέθηκαν αλλαγές προς εφαρμογή.", state="complete")

if __name__ == "__main__":
    main()