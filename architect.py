import streamlit as st
import os
import shutil
import re
import time
import ast
from datetime import datetime
try:
    from groq import Groq
    from streamlit_mic_recorder import mic_recorder
except ImportError:
    st.error("⚠️ Λείπει η βιβλιοθήκη Groq. Τρέξε: pip install groq streamlit-mic-recorder")
    st.stop()

# --- 1. ΡΥΘΜΙΣΕΙΣ INTERFACE ---
st.set_page_config(page_title="Architect AI v37 (Llama Mode)", page_icon="🦙", layout="wide")

# --- 2. ΒΟΗΘΗΤΙΚΕΣ ΣΥΝΑΡΤΗΣΕΙΣ ---
def get_project_context():
    root_dir = os.path.dirname(os.path.abspath(__file__))
    file_contents = {}
    ignore = {'.git', '__pycache__', 'venv', '.streamlit', 'backups', '.DS_Store'} 
    for dirpath, dirnames, filenames in os.walk(root_dir):
        dirnames[:] = [d for d in dirnames if d not in ignore]
        for f in filenames:
            if f.endswith(('.pyc', '.png', '.jpg', '.pdf', '.xlsx', '.bak')): continue 
            try:
                rel_path = os.path.relpath(os.path.join(dirpath, f), root_dir)
                with open(os.path.join(dirpath, f), 'r', encoding='utf-8', errors='ignore') as file:
                    file_contents[rel_path] = file.read()
            except: pass
    return file_contents

def apply_code_changes(response_text):
    pattern = r"### FILE: (.+?)\n.*?```(?:python)?\n(.*?)```"
    matches = re.findall(pattern, response_text, re.DOTALL)
    log = []
    if not matches: return "ℹ️ Δεν βρέθηκε κώδικας."
    for filename, code in matches:
        filename = filename.strip().replace("\\", "/")
        full_path = os.path.abspath(filename)
        if os.path.exists(full_path):
            b_dir = os.path.join(os.path.dirname(full_path), "backups")
            os.makedirs(b_dir, exist_ok=True)
            shutil.copy2(full_path, os.path.join(b_dir, f"{os.path.basename(full_path)}_{datetime.now().strftime('%H%M%S')}.bak"))
        try:
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, 'w', encoding='utf-8') as f: f.write(code.strip())
            log.append(f"✅ UPDATED: {filename}")
        except Exception as e: log.append(f"❌ ERROR: {filename} ({e})")
    return "\n".join(log)

# --- 3. Η ΜΗΧΑΝΗ ΤΗΣ META (GROQ) ---
def run_llama_logic(prompt_text, api_key):
    if not api_key: return "❌ Λείπει το Groq API Key."
    client = Groq(api_key=api_key)
    try:
        # Χρησιμοποιούμε το ισχυρότερο μοντέλο της Meta: Llama 3.3 70B
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt_text}],
            temperature=0.2,
            max_tokens=8192,
            top_p=1,
            stream=False,
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"❌ Groq Error: {str(e)}"

# --- 4. UI ---
def main():
    st.title("🦙 Architect AI v37 (Meta Llama Mode)")
    
    with st.sidebar:
        st.header("Groq Settings")
        api_key = st.text_input("Groq API Key", type="password")
        st.info("Το Llama 3.3 είναι πλέον ο ενεργός Αρχιτέκτονας.")
        
        st.divider()
        audio = mic_recorder(start_prompt="🎤 Rec", stop_prompt="⏹ Stop", key='mic_v37')
        project_data = get_project_context()
        strategy = st.selectbox("Strategy", ["Bug Fix", "New Feature", "Refactor"])
        auto_save = st.checkbox("Auto-Save", value=False)

    if "messages" not in st.session_state: st.session_state.messages = []
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]): st.markdown(msg["content"])

    user_prompt = st.chat_input("Εντολή (Llama 3.3)...")
    
    if (user_prompt or audio) and api_key:
        input_msg = user_prompt if user_prompt else "Φωνητική εντολή..."
        st.session_state.messages.append({"role": "user", "content": input_msg})
        with st.chat_message("user"): st.markdown(input_msg)

        # Build Context
        context_str = "PROJECT FILES:\n" + "\n".join([f"--- {n} ---\n{c[:4000]}" for n, c in project_data.items()])
        
        full_prompt = f"""
        ROLE: Senior Architect (Mastro Nek). 
        CONTEXT: HVAC SaaS Project.
        LANG: GREEK.
        
        INSTRUCTIONS:
        1. Provide FULL CODE for modified files.
        2. Format: ### FILE: filename.py \n ```python ... ```
        
        PROJECT DATA:
        {context_str}
        
        REQUEST: {input_msg}
        """

        with st.chat_message("assistant"):
            with st.spinner("Το Llama αναλύει (αστραπιαία)..."):
                response = run_llama_logic(full_prompt, api_key)
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
                
                if "### FILE:" in response:
                    if auto_save or st.button("💾 Apply Changes"):
                        st.code(apply_code_changes(response))
                        time.sleep(1)
                        st.rerun()

if __name__ == "__main__":
    main()