import streamlit as st
import os
import sys
import subprocess
import time
import re
import shutil
import ast
from datetime import datetime

# --- 0. NUCLEAR FIX: AUTO-INSTALLER ---
# Αυτό το κομμάτι τρέχει ΠΡΙΝ φορτώσει οτιδήποτε άλλο.
# Ελέγχει και αναβαθμίζει τη βιβλιοθήκη στην ΤΡΕΧΟΥΣΑ Python που χρησιμοποιεί το Streamlit.
try:
    import google.generativeai as genai
    # Έλεγχος έκδοσης (θέλουμε > 0.7.0 για να βλέπει το Flash)
    version = getattr(genai, '__version__', '0.0.0')
    if version < '0.7.0':
        raise ImportError("Old version detected")
except ImportError:
    st.warning("🔄 Εντοπίστηκε παλιά βιβλιοθήκη AI. Γίνεται Αυτόματη Αναβάθμιση... (Περιμένετε)")
    try:
        # Εγκατάσταση στη συγκεκριμένη python που τρέχει τώρα
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "google-generativeai"])
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "streamlit-mic-recorder"])
        st.success("✅ Η αναβάθμιση ολοκληρώθηκε! Το πρόγραμμα θα επανεκκινήσει σε 2 δευτερόλεπτα.")
        time.sleep(2)
        st.rerun() # Επανεκκίνηση για να φορτώσει τις νέες βιβλιοθήκες
    except Exception as e:
        st.error(f"❌ Η αυτόματη αναβάθμιση απέτυχε. Παρακαλώ τρέξτε στο τερματικό: pip install --upgrade google-generativeai")
        st.stop()

# --- 1. SETUP & IMPORTS (Τώρα είμαστε σίγουροι ότι είναι νέα) ---
import google.generativeai as genai
from streamlit_mic_recorder import mic_recorder

st.set_page_config(page_title="Architect AI v32 (Auto-Fixer)", page_icon="🛠️", layout="wide")

# --- 2. PROTECTED RULES ---
PROTECTED_FEATURES = [
    "1. AUTO-INSTALL: Ο κώδικας αναβαθμίζει μόνος του τις βιβλιοθήκες.",
    "2. DYNAMIC DISCOVERY: Δεν μαντεύει ονόματα, διαβάζει τι έχει το API.",
    "3. FULL MEDIA: Voice & Vision.",
    "4. SAFETY: Syntax Check & Backups.",
]

# --- 3. HELPER FUNCTIONS ---

def get_project_structure():
    """Διαβάζει όλο το project context."""
    root_dir = os.path.dirname(os.path.abspath(__file__))
    file_contents = {}
    ignore_dirs = {'.git', '__pycache__', 'venv', '.streamlit', 'backups'} 
    ignore_files = {'.DS_Store', 'token.json', 'credentials.json', 'secrets.toml'} 

    for dirpath, dirnames, filenames in os.walk(root_dir):
        dirnames[:] = [d for d in dirnames if d not in ignore_dirs]
        for f in filenames:
            if f in ignore_files or f.endswith(('.pyc', '.png', '.jpg', '.jpeg', '.pdf', '.mp3')): continue 
            try:
                full_path = os.path.join(dirpath, f)
                rel_path = os.path.relpath(full_path, root_dir)
                with open(full_path, 'r', encoding='utf-8', errors='ignore') as file:
                    file_contents[rel_path] = file.read()
            except: pass
    return file_contents

def backup_file(file_path):
    """Κρατάει backup πριν πειράξει αρχείο."""
    try:
        if os.path.exists(file_path):
            backup_dir = os.path.join(os.path.dirname(file_path), "backups")
            os.makedirs(backup_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            shutil.copy2(file_path, os.path.join(backup_dir, f"{os.path.basename(file_path)}_{timestamp}.bak"))
            return True
    except: pass
    return False

# --- THE REAL MODEL FINDER (The Fix for 404/429) ---

def find_working_model(api_key):
    """
    Ρωτάει το API: 'Τι έχεις;' και επιστρέφει το πρώτο που δουλεύει.
    Αποφεύγει το Gemini 2.5 (που έχει μικρό όριο).
    """
    genai.configure(api_key=api_key)
    try:
        my_models = list(genai.list_models())
        # Κρατάμε μόνο αυτά που παράγουν κείμενο
        valid_models = [m.name for m in my_models if 'generateContent' in m.supported_generation_methods]
        
        if not valid_models:
            return None, "Δεν βρέθηκαν διαθέσιμα μοντέλα στο API Key σου."

        # Λογική Επιλογής (Priority: Flash 1.5 > Pro 1.5 > Legacy)
        # 1. Ψάχνουμε Flash 1.5
        for m in valid_models:
            if "flash" in m and "1.5" in m: return m, "✅ Connected to Gemini 1.5 Flash"
        
        # 2. Αν δεν βρούμε Flash, ψάχνουμε Pro 1.5
        for m in valid_models:
            if "pro" in m and "1.5" in m: return m, "⚠️ Fallback to Gemini 1.5 Pro"
            
        # 3. Αν δεν βρούμε τίποτα, παίρνουμε το πρώτο διαθέσιμο (αλλά όχι το 2.5 αν γίνεται)
        safe_choice = valid_models[0]
        for m in valid_models:
             if "2.5" not in m: # Προσπάθεια αποφυγής του experimental
                 safe_choice = m
                 break
                 
        return safe_choice, f"⚠️ Fallback to {safe_choice}"
        
    except Exception as e:
        return None, f"Connection Error: {str(e)}"

def generate_content_safe(strategy_name, parts, api_key):
    """Εκτελεί το αίτημα με το μοντέλο που βρέθηκε."""
    if not api_key: return "ERROR: Missing API Key."
    
    model_name, status = find_working_model(api_key)
    if not model_name:
        return f"CRITICAL SYSTEM ERROR: {status}"

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name)
        
        # Αυστηρό config για να μην χαλάει τον κώδικα
        config = genai.types.GenerationConfig(temperature=0.2, top_p=0.95, top_k=64, max_output_tokens=8192)
        safety = [{"category": c, "threshold": "BLOCK_NONE"} for c in ["HARM_CATEGORY_HARASSMENT", "HARM_CATEGORY_HATE_SPEECH", "HARM_CATEGORY_SEXUALLY_EXPLICIT", "HARM_CATEGORY_DANGEROUS_CONTENT"]]
        
        response = model.generate_content(parts, safety_settings=safety, generation_config=config)
        return response.text
    except Exception as e:
        return f"AI ERROR ({model_name}): {str(e)}"

# --- SELF HEALING ---

def fix_code_with_ai(file_path, bad_code, error_msg, api_key):
    """Διορθώνει συντακτικά λάθη."""
    prompt = f"FIX SYNTAX ERROR in '{file_path}':\n{error_msg}\nCODE:\n```python\n{bad_code}\n```\nReturn ONLY code."
    return generate_content_safe("Fix", [prompt], api_key)

def apply_changes_from_response(response_text, api_key):
    """Εφαρμόζει τις αλλαγές στα αρχεία."""
    pattern = r"### FILE: (.+?)\n.*?```(?:python)?\n(.*?)```"
    matches = re.findall(pattern, response_text, re.DOTALL)
    results = []
    
    if not matches: return "ℹ️ Δεν βρέθηκαν αλλαγές κώδικα."

    for file_path, code_content in matches:
        file_path = file_path.strip().replace("\\", "/") 
        if file_path.startswith("./"): file_path = file_path[2:]
        full_path = os.path.abspath(file_path)
        
        # Self-Healing Loop
        attempts = 0
        success = False
        final_code = code_content
        
        while attempts <= 2:
            if file_path.endswith(".py"):
                try:
                    ast.parse(final_code) # Check Syntax
                    success = True
                    break 
                except SyntaxError as e:
                    attempts += 1
                    if attempts <= 2:
                        # Ζητάμε διόρθωση
                        raw = fix_code_with_ai(file_path, final_code, f"{e.msg} line {e.lineno}", api_key)
                        nm = re.findall(pattern, raw, re.DOTALL)
                        if nm: _, final_code = nm[0]
                        else: break
                    else: break
            else:
                success = True
                break

        if success:
            try:
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                backup_file(full_path)
                with open(full_path, 'w', encoding='utf-8') as f: f.write(final_code.strip())
                results.append(f"✅ UPDATED: {file_path}")
            except Exception as e: results.append(f"❌ ERROR: {e}")
        else:
             results.append(f"💀 DEAD CODE: {file_path} (Failed to fix syntax)")
            
    return "\n".join(results)

# --- 4. MAIN APPLICATION ---

def main():
    st.title("🛠️ Architect AI v32 (Auto-Fixer)")
    
    project_files = get_project_structure()
    # Φροντίζουμε να μην είναι τεράστια η λίστα
    file_list = ["None (Global Context)", "architect.py"] + [f for f in project_files.keys() if f != "architect.py"]

    with st.sidebar:
        st.header("Settings")
        api_key = st.text_input("Gemini API Key", type="password")
        if not api_key and "GEMINI_API_KEY" in st.secrets:
            api_key = st.secrets["GEMINI_API_KEY"]
            st.success("Key loaded from secrets")
        
        # Διαγνωστικά Σύνδεσης
        if api_key:
            with st.expander("🔍 System Status"):
                m, s = find_working_model(api_key)
                st.info(f"Model: {m}\n\nStatus: {s}")

        st.markdown("---")
        audio = mic_recorder(start_prompt="🎤 Rec", stop_prompt="⏹ Stop", key='recorder_v32')
        uploaded_file = st.file_uploader("Upload Image/PDF", type=['png', 'jpg', 'jpeg', 'pdf'], label_visibility="collapsed")
        
        st.markdown("---")
        selected_strategy = st.selectbox("Type", ["General Request", "New Feature", "Bug Fix", "Refactoring", "Self-Upgrade"])
        focus_file = st.selectbox("Focus File", file_list, index=0)
        auto_apply = st.checkbox("Auto-Apply Changes", value=False)

    if "messages" not in st.session_state: st.session_state.messages = []

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]): st.markdown(msg["content"])

    user_in = st.chat_input("Γράψε εντολή...")
    
    final_input = user_in
    is_audio = False
    if audio: 
        is_audio = True
        final_input = "🎤 Audio Command"

    if (final_input or uploaded_file) and api_key:
        if not is_audio:
            msg = final_input if final_input else "🖼️ File Attached"
            st.session_state.messages.append({"role": "user", "content": msg})
            with st.chat_message("user"): 
                st.markdown(msg)
                if uploaded_file: st.success(f"📎 {uploaded_file.name}")
        else:
            with st.chat_message("user"): st.write("🎤 Audio sent...")

        full_context = "PROJECT FILES:\n" + "\n".join([f"--- {k} ---\n{v[:5000]}..." for k, v in project_files.items()])
        
        prompt = f"""
        ROLE: Elite Senior Python Architect (Mastro Nek). 
        CONTEXT: COMMERCIAL SAAS APPLICATION (HVAC).
        GOAL: Profitability, Scalability, Clean Architecture.
        SELF-AWARENESS: You can see and modify your own source code (architect.py).
        STRICT GREEK LANGUAGE.
        
        STRATEGY: {selected_strategy}
        FOCUS FILE: {focus_file}
        
        REQUEST: {user_in if user_in else "See media"}
        
        CONTEXT:
        {full_context}
        """

        parts = [prompt]
        if is_audio and audio['bytes']: parts.append({"mime_type": "audio/wav", "data": audio['bytes']})
        if uploaded_file: parts.append({"mime_type": uploaded_file.type, "data": uploaded_file.getvalue()})

        with st.chat_message("assistant"):
            with st.spinner("Processing..."):
                resp = generate_content_safe(selected_strategy, parts, api_key)
                st.markdown(resp)
                st.session_state.messages.append({"role": "assistant", "content": resp})
                
                if "### FILE:" in resp:
                    if auto_apply:
                        with st.status("Applying...", expanded=True):
                            st.code(apply_changes_from_response(resp, api_key))
                            time.sleep(1)
                            st.rerun()
                    else:
                        if st.button("💾 SAVE CHANGES", type="primary"):
                            with st.status("Saving...", expanded=True):
                                st.code(apply_changes_from_response(resp, api_key))
                            time.sleep(1)
                            st.rerun()

if __name__ == "__main__":
    main()