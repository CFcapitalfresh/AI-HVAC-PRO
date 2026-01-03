import streamlit as st
import os
import shutil
import re
import time
import subprocess
from datetime import datetime

try:
    from openai import OpenAI
    from streamlit_mic_recorder import mic_recorder
except ImportError:
    st.error("⚠️ Λείπουν βιβλιοθήκες! Τρέξε: pip install openai streamlit-mic-recorder")
    st.stop()

# --- 1. ΡΥΘΜΙΣΕΙΣ & ΑΣΦΑΛΕΙΑ ---
st.set_page_config(page_title="Mastro Nek v52 (DeepSeek Titan)", page_icon="🚀", layout="wide")
TOKEN_LIMIT = 100000 

def get_api_key():
    """Ανάκτηση κλειδιού από τα Streamlit Secrets."""
    if "deepseek" in st.secrets:
        return st.secrets["deepseek"]["api_key"]
    return None

def get_project_files():
    """Σάρωση αρχείων κώδικα (Αγνοεί venv, git, κλπ)."""
    files = []
    ignore = {'.git', '__pycache__', 'venv', 'env', 'backups', '.streamlit'}
    for dirpath, dirnames, filenames in os.walk("."):
        dirnames[:] = [d for d in dirnames if d not in ignore]
        for f in filenames:
            if f.endswith(('.py', '.json', '.css', '.txt', '.html')):
                files.append(os.path.relpath(os.path.join(dirpath, f), "."))
    return sorted(files)

def save_and_git_push(response_text):
    """Αποθήκευση αλλαγών και αυτόματο GitHub Sync."""
    pattern = r"### FILE: (.+?)\n.*?```(?:python|json|css)?\n(.*?)```"
    matches = re.findall(pattern, response_text, re.DOTALL)
    if not matches: return "ℹ️ Δεν βρέθηκε κώδικας για ενημέρωση."
    
    log = []
    for filename, code in matches:
        filename = filename.strip().replace("\\", "/")
        path = os.path.abspath(filename)
        if os.path.exists(path):
            os.makedirs("backups", exist_ok=True)
            shutil.copy2(path, f"backups/{os.path.basename(filename)}_{datetime.now().strftime('%H%M%S')}.bak")
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'w', encoding='utf-8') as f:
                f.write(code.strip())
            log.append(f"✅ Saved: {filename}")
        except Exception as e: log.append(f"❌ Error {filename}: {e}")
    
    # Git Sync
    try:
        subprocess.run(["git", "add", "."], check=True)
        subprocess.run(["git", "commit", "-m", f"Mastro Nek v52 Update - {datetime.now()}"], check=True)
        subprocess.run(["git", "push"], check=True)
        log.append("🚀 GitHub Synced Successfully!")
    except: log.append("ℹ️ Τοπική αποθήκευση OK (Git sync skip).")
    return "\n".join(log)

# --- 2. DEEPSEEK CORE (THE APOSTLE) ---
def call_mastro_nek(prompt, api_key, selected_files):
    client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
    
    # Χτίσιμο Context (Max 100K tokens ≈ 400.000 χαρακτήρες)
    context = ""
    for f in selected_files:
        try:
            with open(f, 'r', encoding='utf-8', errors='ignore') as file:
                block = f"\n--- FILE: {f} ---\n{file.read()}\n"
                if len(context) + len(block) < 400000:
                    context += block
                else: break
        except: continue

    sys_msg = """Είσαι ο Μαστρο-Νεκ, ο Senior AI Architect. Μίλα Ελληνικά. 
    Εξήγησε το πλάνο σου και δώσε FULL κώδικα με format: ### FILE: filename.py"""

    try:
        res = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": sys_msg},
                {"role": "user", "content": f"CONTEXT (100K LIMIT):\n{context}\n\nUSER REQUEST: {prompt}"}
            ],
            temperature=0.2
        )
        return res.choices[0].message.content
    except Exception as e: return f"❌ API Error: {str(e)}"

# --- 3. UI INTERFACE ---
def main():
    st.title("🚀 Mastro Nek v52 (DeepSeek Native)")
    
    # Έλεγχος Αυθεντικοποίησης
    api_key = get_api_key()
    
    if "last_ai_res" not in st.session_state: st.session_state.last_ai_res = None
    if "chat_history" not in st.session_state: st.session_state.chat_history = []

    inventory = get_project_files()

    with st.sidebar:
        if api_key:
            st.success("✅ DeepSeek Connected (Secrets)")
        else:
            st.error("⚠️ Το API Key λείπει από τα Secrets!")
            api_key = st.text_input("Enter API Key manually:", type="password")

        st.divider()
        st.subheader("📁 Επιλογή Αρχείων")
        all_code = st.checkbox("Επιλογή ΟΛΩΝ (Code Only)")
        default_files = inventory if all_code else [f for f in inventory if "architect.py" in f]
        selected = st.multiselect("Αρχεία για 'Αποστολή':", inventory, default=default_files)
        
        st.divider()
        audio = mic_recorder(start_prompt="🎤 Πες την εντολή", stop_prompt="⏹ Τέλος", key='mic_v52')
        if st.button("🗑️ Clear"):
            st.session_state.chat_history = []
            st.session_state.last_ai_res = None
            st.rerun()

    # Chat Display
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]): st.markdown(msg["content"])

    user_query = st.chat_input("Τι θα αλλάξουμε στο HVAC SaaS;")

    if (user_query or audio) and api_key:
        input_text = user_query if user_query else "Φωνητική εντολή..."
        st.session_state.chat_history.append({"role": "user", "content": input_text})
        with st.chat_message("user"): st.markdown(input_text)

        with st.chat_message("assistant"):
            with st.spinner("Ο 'Απόστολος' αναλύει τον κώδικα..."):
                response = call_mastro_nek(input_text, api_key, selected)
                st.markdown(response)
                st.session_state.last_ai_res = response
                st.session_state.chat_history.append({"role": "assistant", "content": response})

    # ΣΤΑΘΕΡΟ ΚΟΥΜΠΙ ΑΠΟΘΗΚΕΥΣΗΣ
    if st.session_state.last_ai_res and "### FILE:" in st.session_state.last_ai_res:
        st.divider()
        if st.button("💾 ΕΦΑΡΜΟΓΗ ΑΛΛΑΓΩΝ & GITHUB SYNC", use_container_width=True):
            res_msg = save_and_git_push(st.session_state.last_ai_res)
            st.info(res_msg)
            st.session_state.last_ai_res = None
            time.sleep(2)
            st.rerun()

if __name__ == "__main__":
    main()