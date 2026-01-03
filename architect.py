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
    st.error("⚠️ Τρέξε στο τερματικό: pip install openai streamlit-mic-recorder")
    st.stop()

# --- 1. ΡΥΘΜΙΣΕΙΣ ---
st.set_page_config(page_title="Mastro Nek v47 (Greek & GitHub)", page_icon="🏗️", layout="wide")

def get_project_inventory():
    inventory = []
    ignore = {'.git', '__pycache__', 'venv', 'backups', '.streamlit', 'data'}
    for dirpath, dirnames, filenames in os.walk("."):
        dirnames[:] = [d for d in dirnames if d not in ignore]
        for f in filenames:
            if f.endswith(('.py', '.json', '.css', '.txt', '.md')):
                inventory.append(os.path.relpath(os.path.join(dirpath, f), "."))
    return inventory

def sync_to_github():
    """Εκτελεί αυτόματα τον συγχρονισμό με το GitHub."""
    try:
        subprocess.run(["git", "add", "."], check=True)
        commit_msg = f"Auto-sync by Mastro Nek: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        subprocess.run(["git", "commit", "-m", commit_msg], check=True)
        subprocess.run(["git", "push"], check=True)
        return "🚀 Συγχρονίστηκε επιτυχώς με το GitHub!"
    except Exception as e:
        return f"⚠️ Σφάλμα GitHub: {str(e)} (Βεβαιώσου ότι έχεις κάνει git init και έχεις ορίσει remote)"

def apply_updates_and_sync(text):
    pattern = r"### FILE: (.+?)\n.*?```(?:python|json|css)?\n(.*?)```"
    matches = re.findall(pattern, text, re.DOTALL)
    if not matches: return "ℹ️ Δεν βρέθηκε κώδικας."
    
    log = []
    for filename, code in matches:
        filename = filename.strip().replace("\\", "/")
        full_path = os.path.abspath(filename)
        # Backup
        if os.path.exists(full_path):
            os.makedirs("backups", exist_ok=True)
            shutil.copy2(full_path, f"backups/{os.path.basename(filename)}_{datetime.now().strftime('%H%M%S')}.bak")
        try:
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(code.strip())
            log.append(f"✅ Το αρχείο {filename} ενημερώθηκε τοπικά.")
        except Exception as e: log.append(f"❌ Σφάλμα στο {filename}: {e}")
    
    # Μετά την αποθήκευση, κάνε Push στο GitHub
    git_status = sync_to_github()
    log.append(git_status)
    return "\n".join(log)

# --- 2. ΤΟ ΜΥΑΛΟ ΤΟΥ ΜΑΣΤΡΟ-ΝΕΚ ---
def run_deepseek(prompt, api_key, context):
    client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
    system_instruction = """
    ΕΙΣΑΙ: Ο Μαστρο-Νεκ, ο έμπειρος Αρχιτέκτονας του project.
    ΓΛΩΣΣΑ: Μίλα ΜΟΝΟ Ελληνικά.
    ΟΔΗΓΙΕΣ: 
    - Μην απαντάς με ακαταλαβίστικα σύμβολα ή μόνο κώδικα. 
    - Εξήγησε πρώτα σαν άνθρωπος τι θα αλλάξεις.
    - Χρησιμοποίησε ΠΑΝΤΑ το format: ### FILE: filename.py ακολουθούμενο από το code block.
    """
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": f"CONTEXT ΠΡΟΓΡΑΜΜΑΤΟΣ:\n{context}\n\nΕΝΤΟΛΗ ΧΡΗΣΤΗ: {prompt}"}
            ],
            temperature=0.3
        )
        return response.choices[0].message.content
    except Exception as e: return f"❌ Σφάλμα AI: {str(e)}"

# --- 3. UI ---
def main():
    st.title("🏗️ Mastro Nek v47 (Greek & GitHub Sync)")
    inventory = get_project_inventory()
    
    with st.sidebar:
        st.header("Ρυθμίσεις")
        api_key = st.text_input("DeepSeek API Key", type="password")
        st.divider()
        st.write("📁 **Επίλεξε αρχεία για επεξεργασία:**")
        selected_files = st.multiselect("Αρχεία:", inventory, default=[f for f in inventory if "architect.py" in f])
        st.divider()
        # ΔΙΟΡΘΩΣΗ ΜΙΚΡΟΦΩΝΟΥ: Ζητάμε Ελληνικά
        st.write("🎤 Φωνητική Εντολή:")
        audio = mic_recorder(start_prompt="Ξεκίνα να μιλάς (GR)", stop_prompt="Τέλος", key='mic_v47')
        if st.button("🗑️ Καθαρισμός Chat"):
            st.session_state.messages = []
            st.rerun()

    if "messages" not in st.session_state: st.session_state.messages = []
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]): st.markdown(msg["content"])

    user_input = st.chat_input("Γράψε εδώ στα Ελληνικά...")
    
    if (user_input or audio) and api_key:
        # Αν έχουμε ήχο, ο mic_recorder επιστρέφει κείμενο (αν έχεις ρυθμίσει το STT)
        # Σημείωση: Ο mic_recorder χρειάζεται σωστή παραμετροποίηση για STT
        prompt = user_input if user_input else "Φωνητική εντολή..."
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)

        context = read_files(selected_files) if 'read_files' in globals() else "" # (χρειάζεται τη συνάρτηση από v46)
        
        with st.chat_message("assistant"):
            with st.spinner("Ο Μαστρο-Νεκ αναλύει..."):
                response = run_deepseek(prompt, api_key, read_files(selected_files))
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
                
                if "### FILE:" in response:
                    if st.button("💾 ΑΠΟΘΗΚΕΥΣΗ & PUSH ΣΤΟ GITHUB"):
                        result = apply_updates_and_sync(response)
                        st.info(result)
                        time.sleep(2)
                        st.rerun()

def read_files(paths):
    context = ""
    for path in paths:
        try:
            with open(path, 'r', encoding='utf-8') as f:
                context += f"\n--- ΑΡΧΕΙΟ: {path} ---\n{f.read()}\n"
        except: pass
    return context

if __name__ == "__main__":
    main()