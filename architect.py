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
    st.error("⚠️ Τρέξε: pip install openai streamlit-mic-recorder")
    st.stop()

# --- 1. ΡΥΘΜΙΣΕΙΣ ---
st.set_page_config(page_title="Mastro Nek v48 (Smart Select)", page_icon="🏗️", layout="wide")

def get_project_inventory():
    """Σαρώνει το project και επιστρέφει ΜΟΝΟ τον κώδικα, αγνοώντας βιβλιοθήκες."""
    inventory = []
    # Λίστα φακέλων που ΠΡΕΠΕΙ να αγνοούμε (Βιβλιοθήκες, Git, κλπ)
    ignore_list = {'.git', '__pycache__', 'venv', 'env', '.venv', 'node_modules', 'backups', '.streamlit'}
    
    for dirpath, dirnames, filenames in os.walk("."):
        # Αφαιρούμε τους φακέλους ignore από την αναζήτηση
        dirnames[:] = [d for d in dirnames if d not in ignore_list]
        
        for f in filenames:
            # Κρατάμε μόνο αρχεία κώδικα και ρυθμίσεων
            if f.endswith(('.py', '.json', '.css', '.txt', '.md', '.html')):
                rel_path = os.path.relpath(os.path.join(dirpath, f), ".")
                inventory.append(rel_path)
    return sorted(inventory)

def read_files(paths):
    context = ""
    for path in paths:
        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                context += f"\n--- ΑΡΧΕΙΟ: {path} ---\n{f.read()}\n"
        except: pass
    return context

def apply_updates_and_sync(text):
    pattern = r"### FILE: (.+?)\n.*?```(?:python|json|css)?\n(.*?)```"
    matches = re.findall(pattern, text, re.DOTALL)
    if not matches: return "ℹ️ Δεν βρέθηκε κώδικας."
    
    log = []
    for filename, code in matches:
        filename = filename.strip().replace("\\", "/")
        full_path = os.path.abspath(filename)
        if os.path.exists(full_path):
            os.makedirs("backups", exist_ok=True)
            shutil.copy2(full_path, f"backups/{os.path.basename(filename)}_{datetime.now().strftime('%H%M%S')}.bak")
        try:
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(code.strip())
            log.append(f"✅ Ενημερώθηκε το {filename}")
        except Exception as e: log.append(f"❌ Σφάλμα: {e}")
    
    # Αυτόματο Git Sync
    try:
        subprocess.run(["git", "add", "."], check=True)
        subprocess.run(["git", "commit", "-m", "Auto-update by Mastro Nek"], check=True)
        subprocess.run(["git", "push"], check=True)
        log.append("🚀 Συγχρονίστηκε με το GitHub!")
    except:
        log.append("ℹ️ Τοπική αποθήκευση OK (Git sync skip).")
    return "\n".join(log)

# --- 2. ENGINE ---
def run_deepseek(prompt, api_key, context):
    client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
    system_msg = "Είσαι ο Mastro Nek. Μίλα Ελληνικά. Εξήγησε το πλάνο σου και δώσε FULL κώδικα με ### FILE: filename.py"
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": f"CONTEXT:\n{context}\n\nUSER REQUEST: {prompt}"}
            ],
            temperature=0.3
        )
        return response.choices[0].message.content
    except Exception as e: return f"❌ Σφάλμα AI: {str(e)}"

# --- 3. UI ---
def main():
    st.title("🏗️ Mastro Nek v48 (Smart Selection)")
    
    inventory = get_project_inventory()
    
    with st.sidebar:
        st.header("Ρυθμίσεις")
        api_key = st.text_input("DeepSeek API Key", type="password")
        
        st.divider()
        st.subheader("📁 Διαχείριση Αρχείων")
        
        # ΕΥΚΟΛΙΑ: Κουμπί για επιλογή όλων των αρχείων κώδικα
        select_all = st.checkbox("Επιλογή όλων των αρχείων κώδικα (Χωρίς βιβλιοθήκες)")
        
        default_selection = inventory if select_all else [f for f in inventory if "architect.py" in f]
        
        selected_files = st.multiselect(
            "Επίλεξε αρχεία για ανάλυση:", 
            options=inventory, 
            default=default_selection
        )
        
        st.divider()
        st.write("🎤 Φωνητική Εντολή (GR):")
        audio = mic_recorder(start_prompt="Ξεκίνα (Ελληνικά)", stop_prompt="Τέλος", key='mic_v48')
        
        if st.button("🗑️ Καθαρισμός Chat"):
            st.session_state.messages = []
            st.rerun()

    if "messages" not in st.session_state: st.session_state.messages = []
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]): st.markdown(msg["content"])

    user_input = st.chat_input("Τι θα φτιάξουμε σήμερα;")
    
    if (user_input or audio) and api_key:
        prompt = user_input if user_input else "Φωνητική εντολή..."
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)

        context = read_files(selected_files)
        
        with st.chat_message("assistant"):
            with st.spinner("Ο Μαστρο-Νεκ αναλύει τον κώδικα..."):
                response = run_deepseek(prompt, api_key, context)
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
                
                if "### FILE:" in response:
                    st.divider()
                    if st.button("💾 ΑΠΟΘΗΚΕΥΣΗ & GITHUB PUSH"):
                        res = apply_updates_and_sync(response)
                        st.info(res)
                        time.sleep(1)
                        st.rerun()

if __name__ == "__main__":
    main()