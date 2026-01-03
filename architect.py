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
    st.error("⚠️ ΛΕΙΠΟΥΝ ΒΙΒΛΙΟΘΗΚΕΣ. Τρέξε στο τερματικό: pip install --upgrade google-generativeai streamlit-mic-recorder")
    st.stop()

st.set_page_config(page_title="Architect AI v29 (Sniper Mode)", page_icon="🎯", layout="wide")

# --- 2. PROTECTED RULES ---
PROTECTED_FEATURES = [
    "1. SNIPER MODE: Απαγόρευση χρήσης Gemini 2.5 (Low Quota). Κλείδωμα σε 1.5 Flash.",
    "2. FULL MEDIA: Voice & Vision.",
    "3. SELF-EVOLUTION: Πλήρης πρόσβαση στον κώδικα (architect.py).",
    "4. SAFETY: Syntax Check & Backups.",
]

# --- 3. HELPER FUNCTIONS ---

def get_project_structure():
    """Διαβάζει τη δομή του φακέλου."""
    root_dir = os.path.dirname(os.path.abspath(__file__))
    file_contents = {}
    ignore_dirs = {'.git', '__pycache__', 'venv', '.streamlit', 'backups'} 
    ignore_files = {'.DS_Store', 'token.json', 'credentials.json', 'secrets.toml'} 

    for dirpath, dirnames, filenames in os.walk(root_dir):
        dirnames[:] = [d for d in dirnames if d not in ignore_dirs]
        for f in filenames:
            if f in ignore_files or f.endswith(('.pyc', '.png', '.jpg', '.jpeg', '.pdf', '.mp3')): 
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
    """Backup πριν την εγγραφή."""
    try:
        if os.path.exists(file_path):
            backup_dir = os.path.join(os.path.dirname(file_path), "backups")
            os.makedirs(backup_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.basename(file_path)
            shutil.copy2(file_path, os.path.join(backup_dir, f"{filename}_{timestamp}.bak"))
            return True
    except: pass
    return False

# --- THE SNIPER ENGINE (BLACKLIST 2.5) ---

def get_safe_model(api_key):
    """
    Ψάχνει τα μοντέλα, αλλά ΑΠΑΓΟΡΕΥΕΙ το '2.5' και το 'experimental'.
    """
    genai.configure(api_key=api_key)
    try:
        # 1. Ζητάμε τη λίστα
        all_models = list(genai.list_models())
        available_names = [m.name for m in all_models if 'generateContent' in m.supported_generation_methods]
        
        # 2. ΦΙΛΤΡΟ BLACKLIST: Πετάμε έξω οτιδήποτε λέει "2.5"
        safe_list = [name for name in available_names if "2.5" not in name]
        
        # 3. ΕΠΙΛΟΓΗ SNIPER: Ψάχνουμε συγκεκριμένα το 1.5 Flash
        for name in safe_list:
            if "flash" in name and "1.5" in name:
                return name, "✅ Locked on 1.5 Flash"
        
        # 4. Αν δεν βρούμε Flash, ψάχνουμε Pro 1.5
        for name in safe_list:
            if "pro" in name and "1.5" in name:
                return name, "⚠️ Fallback to 1.5 Pro"

        # 5. Αν δεν βρούμε τίποτα από τα παραπάνω, επιστρέφουμε το πρώτο ασφαλές
        if safe_list:
            return safe_list[0], f"⚠️ Fallback to {safe_list[0]}"
            
        return None, "❌ No safe models found."
        
    except Exception as e:
        # Αν αποτύχει η λίστα, πάμε καρφωτά στο Flash (αφού κάνατε update, θα δουλέψει)
        return "models/gemini-1.5-flash", "⚠️ Blind Force Flash"

def generate_with_sniper_logic(strategy_name, parts, api_key):
    """
    Εκτελεί με το ασφαλές μοντέλο.
    """
    if not api_key: return "ERROR: Missing API Key."
    
    # Βρες το σωστό μοντέλο
    model_name, status_msg = get_safe_model(api_key)
    
    # Debug info στο terminal
    print(f"🎯 Sniper Target: {model_name} | {status_msg}")
    
    if not model_name:
        return f"CRITICAL ERROR: {status_msg}"

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name)
        
        # Αυστηρό config
        config = genai.types.GenerationConfig(temperature=0.2, top_p=0.95, top_k=64, max_output_tokens=8192)
        safety = [{"category": c, "threshold": "BLOCK_NONE"} for c in 
                  ["HARM_CATEGORY_HARASSMENT", "HARM_CATEGORY_HATE_SPEECH", "HARM_CATEGORY_SEXUALLY_EXPLICIT", "HARM_CATEGORY_DANGEROUS_CONTENT"]]
        
        response = model.generate_content(parts, safety_settings=safety, generation_config=config)
        return response.text
        
    except Exception as e:
        err = str(e)
        if "429" in err:
            return f"QUOTA ERROR ({model_name}): Ξεπεράσατε τα όρια. Περιμένετε λίγο. (Προσπαθήσαμε να αποφύγουμε το 2.5, αλλά ίσως το 1.5 είναι φορτωμένο)."
        return f"CRITICAL AI ERROR ({model_name}): {err}"

# --- SELF HEALING ---

def fix_code_with_ai(file_path, bad_code, error_msg, api_key):
    """Καλεί το AI για διόρθωση."""
    prompt = f"FIX SYNTAX ERROR in '{file_path}':\n{error_msg}\nCODE:\n```python\n{bad_code}\n```\nReturn ONLY code."
    return generate_with_sniper_logic("Fix", [prompt], api_key)

def apply_changes_from_response(response_text, api_key):
    """Εφαρμογή αλλαγών με Syntax Check & Self-Healing."""
    pattern = r"### FILE: (.+?)\n.*?```(?:python)?\n(.*?)```"
    matches = re.findall(pattern, response_text, re.DOTALL)
    
    results = []
    if not matches: return "ℹ️ Δεν βρέθηκαν αλλαγές κώδικα."

    for file_path, code_content in matches:
        file_path = file_path.strip().replace("\\", "/") 
        if file_path.startswith("./"): file_path = file_path[2:]
        
        full_path = os.path.abspath(file_path)
        root_path = os.path.dirname(os.path.abspath(__file__))

        if not full_path.startswith(root_path):
            results.append(f"⛔ SECURITY ALERT: Εκτός φακέλου ({file_path})")
            continue

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
                        raw_heal = fix_code_with_ai(file_path, final_code, error_details, api_key)
                        new_matches = re.findall(pattern, raw_heal, re.DOTALL)
                        if new_matches: 
                            _, final_code = new_matches[0]
                        else: break 
                    else: break 
            else: 
                success = True
                break

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
             results.append(f"💀 DEAD CODE: {file_path} - Failed to heal.")
            
    return "\n".join(results)

# --- 4. MAIN APPLICATION ---

def main():
    st.title("🎯 Architect AI v29 (Sniper Mode)")
    
    project_files = get_project_structure()
    file_list = ["None (Global Context)", "architect.py"] + [f for f in project_files.keys() if f != "architect.py"]

    with st.sidebar:
        st.header("Settings")
        api_key = st.text_input("Gemini API Key", type="password")
        if not api_key and "GEMINI_API_KEY" in st.secrets:
            api_key = st.secrets["GEMINI_API_KEY"]
            st.success("Key loaded from secrets")
        
        # --- DIAGNOSTICS ---
        if api_key:
            with st.expander("🔍 Model Diagnostics"):
                m, status = get_safe_model(api_key)
                st.write(f"**Target Model:** `{m}`")
                st.write(f"**Log:** {status}")

        st.markdown("---")
        st.subheader("🎙️ & 📸 Inputs")
        
        audio = mic_recorder(start_prompt="🎤 Rec", stop_prompt="⏹ Stop", key='recorder_v29')
        uploaded_file = st.file_uploader("Upload Image/PDF", type=['png', 'jpg', 'jpeg', 'pdf'], label_visibility="collapsed")
        
        st.markdown("---")
        st.subheader("🛠️ Tools")
        selected_strategy = st.selectbox("Type", ["General Request", "New Feature", "Bug Fix", "Refactoring", "Self-Upgrade"])
        focus_file = st.selectbox("Focus File", file_list, index=0)
        auto_apply = st.checkbox("Auto-Apply Changes", value=False)
        
        st.caption("Active Rules:")
        for rule in PROTECTED_FEATURES: st.caption(rule)

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # CHAT INPUT
    user_in = st.chat_input("Γράψε εντολή...")

    final_input_text = None
    is_audio = False
    
    if user_in:
        final_input_text = user_in
    elif audio:
        is_audio = True
        final_input_text = "🎤 Audio Command Sent"

    if (final_input_text or uploaded_file) and api_key:
        
        if not is_audio:
            display_text = final_input_text if final_input_text else "🖼️ Image/PDF Request"
            st.session_state.messages.append({"role": "user", "content": display_text})
            with st.chat_message("user"): 
                st.markdown(display_text)
                if uploaded_file: st.success(f"📎 Attached: {uploaded_file.name}")
        else:
            with st.chat_message("user"): st.write("🎤 Audio sent...")

        full_context = "PROJECT FILES:\n" + "\n".join([f"--- {k} ---\n{v[:5000]}..." for k, v in project_files.items()])
        
        prompt_text = f"""
        ROLE: Elite Senior Python Architect (Mastro Nek). 
        CONTEXT: COMMERCIAL SAAS APPLICATION (HVAC).
        GOAL: Profitability, Scalability, Clean Architecture.
        SELF-AWARENESS: You can see and modify your own source code (architect.py).
        STRICT GREEK LANGUAGE.
        
        STRATEGY: {selected_strategy}
        FOCUS FILE: {focus_file if focus_file != "None (Global Context)" else "ALL"}
        
        INSTRUCTIONS:
        1. Analyze the request.
        2. If image provided, analyze it.
        3. Provide FULL COMPLETE CODE blocks.
        
        FORMAT:
        ### FILE: path/to/filename.py
        ```python
        # Full content
        ```
        
        CONTEXT:
        {full_context}
        
        REQUEST TEXT: {user_in if user_in else "See attached media."}
        """

        parts = [prompt_text]
        if is_audio and audio['bytes']: parts.append({"mime_type": "audio/wav", "data": audio['bytes']})
        if uploaded_file: parts.append({"mime_type": uploaded_file.type, "data": uploaded_file.getvalue()})

        with st.chat_message("assistant"):
            with st.spinner(f"O Αρχιτέκτονας συνδέεται (Sniper Mode)..."):
                response_text = generate_with_sniper_logic(selected_strategy, parts, api_key)
                st.markdown(response_text)
                st.session_state.messages.append({"role": "assistant", "content": response_text})
                
                if "### FILE:" in response_text:
                    if auto_apply:
                        with st.status("Αυτόματη Εφαρμογή...", expanded=True) as status:
                            result_log = apply_changes_from_response(response_text, api_key)
                            st.code(result_log)
                            if "UPDATED" in result_log:
                                status.update(label="Επιτυχία!", state="complete", expanded=False)
                                time.sleep(1)
                                st.rerun()
                            else:
                                status.update(label="Πρόβλημα.", state="error")
                    else:
                        st.info("💡 Βρέθηκαν αλλαγές στον κώδικα.")
                        if st.button("💾 ΑΠΟΘΗΚΕΥΣΗ ΑΛΛΑΓΩΝ", type="primary", use_container_width=True):
                            with st.status("Αποθήκευση...", expanded=True):
                                result_log = apply_changes_from_response(response_text, api_key)
                                st.code(result_log)
                            if "UPDATED" in result_log:
                                st.success("✅ Αποθηκεύτηκε!")
                                time.sleep(1.5)
                                st.rerun()

if __name__ == "__main__":
    main()