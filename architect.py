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

# --- 1. SETTINGS ---
st.set_page_config(page_title="Mastro Nek v50 (100K Limit)", page_icon="🏗️", layout="wide")
MAX_TOKENS_LIMIT = 100000  # Το σκληρό όριο που θέσαμε

def estimate_tokens(text):
    """Πρόχειρη εκτίμηση tokens (1 token ≈ 4 χαρακτήρες για κώδικα)."""
    return len(text) // 4

def get_smart_context(selected_files):
    """
    Διαβάζει τα αρχεία αλλά σταματάει μόλις φτάσει κοντά στο όριο των 100K.
    Δίνει προτεραιότητα στα επιλεγμένα αρχεία.
    """
    context = ""
    current_tokens = 0
    
    # Πρώτα φορτώνουμε τα επιλεγμένα αρχεία (Υψηλή Προτεραιότητα)
    for f in selected_files:
        try:
            with open(f, 'r', encoding='utf-8', errors='ignore') as file:
                content = file.read()
                file_msg = f"\n--- FILE: {f} ---\n{content}\n"
                estimated = estimate_tokens(file_msg)
                
                if current_tokens + estimated < MAX_TOKENS_LIMIT:
                    context += file_msg
                    current_tokens += estimated
                else:
                    context += f"\n--- FILE: {f} (ΠΕΡΙΚΟΠΗ ΛΟΓΩ ΟΡΙΟΥ 100K) ---\n"
                    break
        except: continue
    return context, current_tokens

def save_and_sync(response_text):
    """Αποθήκευση και Git Push."""
    pattern = r"### FILE: (.+?)\n.*?```(?:python|json|css)?\n(.*?)```"
    matches = re.findall(pattern, response_text, re.DOTALL)
    if not matches: return "ℹ️ Δεν βρέθηκε κώδικας."
    
    report = []
    for filename, code in matches:
        filename = filename.strip().replace("\\", "/")
        path = os.path.abspath(filename)
        
        # Backup
        if os.path.exists(path):
            os.makedirs("backups", exist_ok=True)
            shutil.copy2(path, f"backups/{os.path.basename(filename)}_{datetime.now().strftime('%H%M%S')}.bak")
        
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'w', encoding='utf-8') as f:
                f.write(code.strip())
            report.append(f"✅ Αποθηκεύτηκε: {filename}")
        except Exception as e:
            report.append(f"❌ Σφάλμα στο {filename}: {e}")
            
    # GitHub Sync
    try:
        subprocess.run(["git", "add", "."], check=True)
        subprocess.run(["git", "commit", "-m", "Auto-update by Mastro Nek v50"], check=True)
        subprocess.run(["git", "push"], check=True)
        report.append("🚀 GitHub Push: Success!")
    except:
        report.append("ℹ️ Τοπική αποθήκευση OK. (Git Sync skip)")
        
    return "\n".join(report)

# --- 2. DEEPSEEK ENGINE ---
def run_deepseek_v50(prompt, api_key, context):
    client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
    
    system_instruction = """
    ΕΙΣΑΙ: Ο Μαστρο-Νεκ (Senior Architect).
    ΓΛΩΣΣΑ: Ελληνικά.
    ΟΔΗΓΙΑ: Εξήγησε το πλάνο σου και δώσε FULL κώδικα με format: ### FILE: filename.py
    """

    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": f"CONTEXT (LIMIT 100K):\n{context}\n\nUSER REQUEST: {prompt}"}
            ],
            temperature=0.2
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"❌ DeepSeek Error: {str(e)}"

# --- 3. UI ---
def main():
    st.title("🏗️ Mastro Nek v50: Token Master")
    
    # Session State για σταθερότητα κουμπιού αποθήκευσης
    if "pending_response" not in st.session_state:
        st.session_state.pending_response = None
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # Σάρωση αρχείων (ignore venv κλπ)
    inventory = []
    for dirpath, dirnames, filenames in os.walk("."):
        dirnames[:] = [d for d in dirnames if d not in {'.git', '__pycache__', 'venv', 'backups'}]
        for f in filenames:
            if f.endswith(('.py', '.json', '.css', '.txt')):
                inventory.append(os.path.relpath(os.path.join(dirpath, f), "."))

    with st.sidebar:
        st.header("Settings")
        api_key = st.text_input("DeepSeek API Key", type="password")
        st.divider()
        st.subheader("📁 Project Management")
        selected = st.multiselect("Επίλεξε αρχεία για ανάλυση:", sorted(inventory), default=[f for f in inventory if "architect.py" in f])
        st.divider()
        audio = mic_recorder(start_prompt="🎤 Μίλα (GR)", stop_prompt="Τέλος", key='mic_v50')
        if st.button("🗑️ Clear Chat"):
            st.session_state.chat_history = []
            st.session_state.pending_response = None
            st.rerun()

    # Προβολή Chat
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]): st.markdown(msg["content"])

    user_query = st.chat_input("Τι αλλαγές θα κάνουμε;")

    if (user_query or audio) and api_key:
        input_text = user_query if user_query else "Φωνητική εντολή..."
        st.session_state.chat_history.append({"role": "user", "content": input_text})
        with st.chat_message("user"): st.markdown(input_text)

        # Έξυπνη φόρτωση με όριο 100K
        context_data, used_tokens = get_smart_context(selected)
        st.sidebar.write(f"📊 Tokens used: ~{used_tokens} / 100,000")

        with st.chat_message("assistant"):
            with st.spinner("Ο Μαστρο-Νεκ αναλύει..."):
                response = run_deepseek_v50(input_text, api_key, context_data)
                st.markdown(response)
                st.session_state.pending_response = response
                st.session_state.chat_history.append({"role": "assistant", "content": response})

    # ΚΟΥΜΠΙ ΑΠΟΘΗΚΕΥΣΗΣ (Σταθερό)
    if st.session_state.pending_response and "### FILE:" in st.session_state.pending_response:
        st.divider()
        if st.button("💾 ΕΦΑΡΜΟΓΗ ΑΛΛΑΓΩΝ & GITHUB SYNC", use_container_width=True):
            res_msg = save_and_sync(st.session_state.pending_response)
            st.success(res_msg)
            st.session_state.pending_response = None
            time.sleep(2)
            st.rerun()

if __name__ == "__main__":
    main()