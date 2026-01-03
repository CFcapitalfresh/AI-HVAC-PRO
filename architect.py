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
    st.error("⚠️ Λείπουν βιβλιοθήκες. Τρέξε: pip install groq streamlit-mic-recorder")
    st.stop()

# --- 1. ΡΥΘΜΙΣΕΙΣ INTERFACE ---
st.set_page_config(page_title="Architect AI v41 (Mentor Mode)", page_icon="🏗️", layout="wide")

# --- 2. ΒΟΗΘΗΤΙΚΕΣ ΣΥΝΑΡΤΗΣΕΙΣ ---
def get_project_context():
    """Διαβάζει τα αρχεία του project (συμπεριλαμβανομένου του architect.py)."""
    root_dir = os.path.dirname(os.path.abspath(__file__))
    file_contents = {}
    # Αφαιρέσαμε το .streamlit από το ignore αν θες να βλέπει ρυθμίσεις, 
    # αλλά κρατάμε τα backups και τα venv εκτός.
    ignore = {'.git', '__pycache__', 'venv', 'backups', '.DS_Store'} 
    for dirpath, dirnames, filenames in os.walk(root_dir):
        dirnames[:] = [d for d in dirnames if d not in ignore]
        for f in filenames:
            # Διαβάζουμε py, json, css, txt, md
            if f.endswith(('.py', '.json', '.css', '.txt', '.md')):
                try:
                    rel_path = os.path.relpath(os.path.join(dirpath, f), root_dir)
                    with open(os.path.join(dirpath, f), 'r', encoding='utf-8', errors='ignore') as file:
                        # Περιορισμός για να μην σκάει το όριο tokens (Rate Limit)
                        content = file.read()
                        if len(content) > 7000:
                            content = content[:3500] + "\n... [truncated] ...\n" + content[-3500:]
                        file_contents[rel_path] = content
                except: pass
    return file_contents

def apply_code_changes(response_text):
    """Αποθηκεύει τις αλλαγές που προτείνει το AI."""
    pattern = r"### FILE: (.+?)\n.*?```(?:python|json|css)?\n(.*?)```"
    matches = re.findall(pattern, response_text, re.DOTALL)
    log = []
    if not matches: return "ℹ️ Δεν βρέθηκε κώδικας για αποθήκευση."
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
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system", 
                    "content": "Είσαι ο Mastro Nek, Senior AI Architect. Μίλα πάντα Ελληνικά. Εξήγησε αναλυτικά το πλάνο σου πριν δώσεις κώδικα. Μην δίνεις μόνο σύμβολα."
                },
                {"role": "user", "content": prompt_text}
            ],
            temperature=0.3, # Λίγο παραπάνω δημιουργικότητα για την επεξηγήση
            max_tokens=8192,
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"❌ Groq Error: {str(e)}"

# --- 4. UI ---
def main():
    st.title("🏗️ Architect AI v41 (Mentor Mode)")
    
    with st.sidebar:
        st.header("Settings")
        api_key = st.text_input("Groq API Key", type="password")
        st.divider()
        audio = mic_recorder(start_prompt="🎤 Rec (Voice)", stop_prompt="⏹ Stop", key='mic_v41')
        st.divider()
        if st.button("🗑️ Clear Chat History"):
            st.session_state.messages = []
            st.rerun()
        
        strategy = st.selectbox("Strategy", ["Bug Fix", "New Feature", "Refactor", "Self-Upgrade"])
        auto_save = st.checkbox("Auto-Save", value=False)

    if "messages" not in st.session_state: st.session_state.messages = []
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]): st.markdown(msg["content"])

    user_prompt = st.chat_input("Πώς μπορώ να βοηθήσω στο Project σήμερα;")
    
    if (user_prompt or audio) and api_key:
        input_msg = user_prompt if user_prompt else "Φωνητική εντολή..."
        st.session_state.messages.append({"role": "user", "content": input_msg})
        with st.chat_message("user"): st.markdown(input_msg)

        # Build Context
        project_data = get_project_context()
        context_str = "PROJECT FILES:\n" + "\n".join([f"--- {n} ---\n{c}" for n, c in project_data.items()])
        
        full_prompt = f"""
        ΡΟΛΟΣ: Senior Architect (Mastro Nek). 
        CONTEXT: HVAC SaaS Project.
        ΓΛΩΣΣΑ: ΕΛΛΗΝΙΚΑ.
        
        ΟΔΗΓΙΕΣ:
        1. Ξεκίνα με μια σύντομη ανάλυση στα Ελληνικά. Εξήγησε τι θα αλλάξεις.
        2. Μετά την εξήγηση, δώσε τον ΠΛΗΡΗ κώδικα.
        3. Χρησιμοποίησε το format: ### FILE: filename.py \n ```python ... ```
        
        PROJECT DATA:
        {context_str}
        
        REQUEST: {input_msg}
        """

        with st.chat_message("assistant"):
            with st.spinner("Ο Αρχιτέκτονας αναλύει..."):
                response = run_llama_logic(full_prompt, api_key)
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
                
                if "### FILE:" in response:
                    if auto_save or st.button("💾 Apply Changes"):
                        res_log = apply_code_changes(response)
                        st.code(res_log)
                        time.sleep(1)
                        st.rerun()

if __name__ == "__main__":
    main()