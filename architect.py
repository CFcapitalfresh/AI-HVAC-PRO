import streamlit as st
import os
import shutil
import re
import time
from datetime import datetime

try:
    from openai import OpenAI
    from streamlit_mic_recorder import mic_recorder
except ImportError:
    st.error("⚠️ Τρέξε: pip install openai streamlit-mic-recorder")
    st.stop()

# --- 1. ΡΥΘΜΙΣΕΙΣ ---
st.set_page_config(page_title="Mastro Nek v45 (Smart Context)", page_icon="🧠", layout="wide")

def get_project_inventory():
    """Επιστρέφει τη λίστα αρχείων και το μέγεθός τους."""
    inventory = []
    ignore = {'.git', '__pycache__', 'venv', 'backups', '.streamlit', 'data', '.db'}
    for dirpath, dirnames, filenames in os.walk("."):
        dirnames[:] = [d for d in dirnames if d not in ignore]
        for f in filenames:
            if f.endswith(('.py', '.json', '.css', '.txt', '.md')):
                rel_path = os.path.relpath(os.path.join(dirpath, f), ".")
                size_kb = os.path.getsize(rel_path) / 1024
                inventory.append({"path": rel_path, "size": size_kb})
    return inventory

def read_selected_files(selected_paths):
    """Διαβάζει μόνο τα επιλεγμένα αρχεία."""
    context = ""
    for path in selected_paths:
        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                context += f"\n--- FILE: {path} ---\n{f.read()}\n"
        except: pass
    return context

def apply_changes(text):
    pattern = r"### FILE: (.+?)\n.*?```(?:python|json|css)?\n(.*?)```"
    matches = re.findall(pattern, text, re.DOTALL)
    log = []
    for filename, code in matches:
        filename = filename.strip().replace("\\", "/")
        full_path = os.path.abspath(filename)
        if os.path.exists(full_path):
            os.makedirs("backups", exist_ok=True)
            shutil.copy2(full_path, f"backups/{os.path.basename(filename)}_{datetime.now().strftime('%H%M%S')}.bak")
        try:
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, 'w', encoding='utf-8') as f: f.write(code.strip())
            log.append(f"✅ ΕΝΗΜΕΡΩΘΗΚΕ: {filename}")
        except Exception as e: log.append(f"❌ ΣΦΑΛΜΑ: {e}")
    return "\n".join(log)

# --- 2. ENGINE ---
def run_deepseek(prompt, api_key, context):
    client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "Είσαι ο Mastro Nek. Μίλα Ελληνικά. Δώσε FULL κώδικα με ### FILE: filename.py"},
                {"role": "user", "content": f"CONTEXT:\n{context}\n\nREQUEST: {prompt}"}
            ],
            temperature=0.2
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"❌ DeepSeek Error: {str(e)}"

# --- 3. UI ---
def main():
    st.title("🧠 Mastro Nek v45 (Smart Context Control)")
    
    inventory = get_project_inventory()
    
    with st.sidebar:
        st.header("DeepSeek API")
        api_key = st.text_input("API Key", type="password")
        st.divider()
        
        # ΕΠΙΛΟΓΗ ΑΡΧΕΙΩΝ (Multi-select)
        st.subheader("📁 Επιλογή Αρχείων για Ανάλυση")
        st.write("Επίλεξε ΜΟΝΟ τα αρχεία που αφορά η ερώτησή σου.")
        all_paths = [i['path'] for i in inventory]
        
        # Προσπάθεια αυτόματης επιλογής του architect.py και main.py
        defaults = [p for p in all_paths if "architect.py" in p or "main.py" in p]
        selected_files = st.multiselect("Files:", all_paths, default=defaults)
        
        st.divider()
        audio = mic_recorder(start_prompt="🎤 Rec", stop_prompt="⏹ Stop", key='mic_v45')
        if st.button("🗑️ Clear Chat"):
            st.session_state.messages = []
            st.rerun()

    if "messages" not in st.session_state: st.session_state.messages = []
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]): st.markdown(msg["content"])

    user_input = st.chat_input("Τι θέλεις να αλλάξουμε;")
    
    if (user_input or audio) and api_key:
        prompt = user_input if user_input else "Φωνητική εντολή..."
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)

        # Διαβάζουμε ΜΟΝΟ τα επιλεγμένα
        context = read_selected_files(selected_files)
        
        with st.chat_message("assistant"):
            with st.spinner(f"Ανάλυση {len(selected_files)} αρχείων..."):
                response = run_deepseek(prompt, api_key, context)
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
                
                if "### FILE:" in response:
                    if st.button("💾 Apply Changes"):
                        st.success(apply_changes(response))
                        time.sleep(1)
                        st.rerun()

if __name__ == "__main__":
    main()