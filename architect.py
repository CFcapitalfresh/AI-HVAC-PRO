import streamlit as st
import os
import shutil
import re
import time
import json
from datetime import datetime

# Χρησιμοποιούμε το OpenAI SDK καθώς το DeepSeek API είναι πλήρως συμβατό
try:
    from openai import OpenAI
    from streamlit_mic_recorder import mic_recorder
except ImportError:
    st.error("⚠️ Λείπουν βιβλιοθήκες. Τρέξε: pip install openai streamlit-mic-recorder")
    st.stop()

# --- 1. ΡΥΘΜΙΣΕΙΣ ΣΥΣΤΗΜΑΤΟΣ ---
st.set_page_config(page_title="Mastro Nek AI v44 (DeepSeek)", page_icon="🧠", layout="wide")

def get_full_project_context():
    """Διαβάζει όλο τον κώδικα του project για το AI."""
    root_dir = os.path.dirname(os.path.abspath(__file__))
    context_data = ""
    ignore = {'.git', '__pycache__', 'venv', 'backups', '.streamlit', 'data'}
    
    for dirpath, dirnames, filenames in os.walk(root_dir):
        dirnames[:] = [d for d in dirnames if d not in ignore]
        for f in filenames:
            if f.endswith(('.py', '.json', '.css', '.txt')):
                try:
                    rel_path = os.path.relpath(os.path.join(dirpath, f), root_dir)
                    with open(os.path.join(dirpath, f), 'r', encoding='utf-8', errors='ignore') as file:
                        context_data += f"\n--- FILE: {rel_path} ---\n{file.read()}\n"
                except: pass
    return context_data

def apply_code_updates(response_text):
    """Εντοπίζει και αποθηκεύει τον κώδικα."""
    pattern = r"### FILE: (.+?)\n.*?```(?:python|json|css)?\n(.*?)```"
    matches = re.findall(pattern, response_text, re.DOTALL)
    log = []
    if not matches: return "ℹ️ Δεν βρέθηκαν αλλαγές."
    
    for filename, code in matches:
        filename = filename.strip().replace("\\", "/")
        full_path = os.path.abspath(filename)
        
        # Backup συστήματος
        if os.path.exists(full_path):
            os.makedirs("backups", exist_ok=True)
            ts = datetime.now().strftime("%H%M%S")
            shutil.copy2(full_path, f"backups/{os.path.basename(filename)}_{ts}.bak")
            
        try:
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(code.strip())
            log.append(f"✅ ΕΝΗΜΕΡΩΘΗΚΕ: {filename}")
        except Exception as e:
            log.append(f"❌ ΣΦΑΛΜΑ στο {filename}: {e}")
    return "\n".join(log)

# --- 2. DEEPSEEK DIRECT ENGINE ---
def run_deepseek_logic(user_prompt, api_key, context):
    if not api_key: return "❌ Παρακαλώ εισάγετε το DeepSeek API Key."
    
    # Σύνδεση απευθείας με το DeepSeek API
    client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
    
    try:
        response = client.chat.completions.create(
            model="deepseek-chat", # Χρήση του DeepSeek-V3
            messages=[
                {
                    "role": "system", 
                    "content": "Είσαι ο Mastro Nek, Senior AI Architect. Μίλα Ελληνικά. Εξήγησε το πλάνο σου και δώσε FULL κώδικα με ### FILE: filename.py"
                },
                {"role": "user", "content": f"CONTEXT:\n{context}\n\nUSER REQUEST: {user_prompt}"}
            ],
            stream=False,
            temperature=0.2 # Χαμηλή θερμοκρασία για ακρίβεια στον κώδικα
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"❌ DeepSeek API Error: {str(e)}"

# --- 3. UI ---
def main():
    st.title("🧠 Mastro Nek v44 (DeepSeek Native)")
    st.subheader("Direct Professional Connection")

    with st.sidebar:
        st.header("DeepSeek API")
        # Πηγαίνεις στο https://platform.deepseek.com/ για το κλειδί
        api_key = st.text_input("DeepSeek API Key", type="password")
        st.info("Status: Direct Connected")
        st.divider()
        audio = mic_recorder(start_prompt="🎤 Rec", stop_prompt="⏹ Stop", key='mic_v44')
        if st.button("🗑️ Clear History"):
            st.session_state.chat_history = []
            st.rerun()

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]): st.markdown(msg["content"])

    user_input = st.chat_input("Πώς θα αναβαθμίσουμε το HVAC SaaS;")
    
    if (user_input or audio) and api_key:
        prompt = user_input if user_input else "Φωνητική εντολή..."
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Ο DeepSeek μελετά το project..."):
                full_project = get_full_project_context()
                response = run_deepseek_logic(prompt, api_key, full_project)
                st.markdown(response)
                st.session_state.chat_history.append({"role": "assistant", "content": response})
                
                if "### FILE:" in response:
                    if st.button("💾 Εφαρμογή Αλλαγών"):
                        res = apply_code_updates(response)
                        st.success(res)
                        time.sleep(1.5)
                        st.rerun()

if __name__ == "__main__":
    main()