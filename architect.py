import streamlit as st
import os
import shutil
import re
import time
from datetime import datetime
try:
    from groq import Groq
    from streamlit_mic_recorder import mic_recorder
except ImportError:
    st.error("⚠️ Λείπουν βιβλιοθήκες. Τρέξε: pip install groq streamlit-mic-recorder")
    st.stop()

# --- 1. ΡΥΘΜΙΣΕΙΣ ΣΥΣΤΗΜΑΤΟΣ ---
st.set_page_config(page_title="Architect AI v38 (Self-Aware)", page_icon="🏗️", layout="wide")

def get_project_context():
    """Διαβάζει όλο το project, συμπεριλαμβανομένου και του ίδιου του Αρχιτέκτονα!"""
    root_dir = os.path.dirname(os.path.abspath(__file__))
    file_contents = {}
    # Αφαιρέσαμε τον περιορισμό για να μπορεί να βλέπει και τον εαυτό του
    ignore = {'.git', '__pycache__', 'venv', '.streamlit', 'backups'} 
    
    for dirpath, dirnames, filenames in os.walk(root_dir):
        dirnames[:] = [d for d in dirnames if d not in ignore]
        for f in filenames:
            # Διαβάζουμε μόνο κώδικα και ρυθμίσεις
            if f.endswith(('.py', '.json', '.txt', '.md', '.css')):
                try:
                    rel_path = os.path.relpath(os.path.join(dirpath, f), root_dir)
                    with open(os.path.join(dirpath, f), 'r', encoding='utf-8', errors='ignore') as file:
                        file_contents[rel_path] = file.read()
                except: pass
    return file_contents

def apply_code_changes(response_text):
    """Εφαρμόζει τις αλλαγές και κρατάει backup."""
    pattern = r"### FILE: (.+?)\n.*?```(?:python|json|css)?\n(.*?)```"
    matches = re.findall(pattern, response_text, re.DOTALL)
    log = []
    if not matches: return "ℹ️ Δεν εντοπίστηκε κώδικας προς αποθήκευση."
    
    for filename, code in matches:
        filename = filename.strip().replace("\\", "/")
        full_path = os.path.abspath(filename)
        
        # Backup πριν την αλλαγή
        if os.path.exists(full_path):
            b_dir = os.path.join(os.path.dirname(full_path), "backups")
            os.makedirs(b_dir, exist_ok=True)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            shutil.copy2(full_path, os.path.join(b_dir, f"{os.path.basename(full_path)}_{ts}.bak"))
            
        try:
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(code.strip())
            log.append(f"✅ ΕΝΗΜΕΡΩΘΗΚΕ: {filename}")
        except Exception as e:
            log.append(f"❌ ΣΦΑΛΜΑ: {filename} ({e})")
    return "\n".join(log)

# --- 2. Η ΜΗΧΑΝΗ ΤΟΥ AI (MENTOR PROMPT) ---
def run_ai_logic(prompt_text, api_key, context_data):
    if not api_key: return "❌ Παρακαλώ εισάγετε το Groq API Key."
    client = Groq(api_key=api_key)
    
    # Κατασκευή του Context
    context_str = "PROJECT FILES (Current State):\n"
    for name, content in context_data.items():
        context_str += f"\n--- FILE: {name} ---\n{content[:5000]}\n"

    # Το Mentor Prompt που ζήτησες
    system_prompt = """
    ΕΙΣΑΙ: Ο Mastro Nek, ένας Senior AI Architect & Μέντορας.
    ΓΛΩΣΣΑ: Ελληνικά (Φιλικά, Επαγγελματικά, Επεξηγηματικά).
    
    ΚΑΝΟΝΕΣ:
    1. Μην δίνεις ποτέ μόνο κώδικα. Εξήγησε πρώτα τι πρόκειται να κάνεις και γιατί.
    2. Αν σου ζητηθεί αναβάθμιση στον δικό σου κώδικα (architect.py), κάνε την προσεκτικά.
    3. Χρησιμοποίησε ΠΑΝΤΑ το format: ### FILE: filename.py ακολουθούμενο από block κώδικα.
    4. Μίλα στον χρήστη σαν συνεργάτης.
    """

    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"CONTEXT:\n{context_str}\n\nUSER REQUEST: {prompt_text}"}
            ],
            temperature=0.3,
            max_tokens=8192
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"❌ Σφάλμα AI: {str(e)}"

# --- 3. UI ---
def main():
    st.title("🏗️ Mastro Nek: Architect v38")
    st.subheader("Self-Aware AI & Project Mentor")

    with st.sidebar:
        st.header("Ρυθμίσεις")
        api_key = st.text_input("Groq API Key", type="password")
        st.divider()
        st.write("🎤 **Φωνητική Εντολή**")
        audio = mic_recorder(start_prompt="Ξεκίνα", stop_prompt="Τέλος", key='mic_v38')
        
        st.divider()
        strategy = st.selectbox("Στρατηγική", ["Αναβάθμιση Κώδικα", "Διόρθωση Bug", "Νέα Λειτουργία"])
        if st.button("🔄 Refresh Project Data"):
            st.rerun()

    # Chat History
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # User Input
    user_input = st.chat_input("Πες μου τι θέλεις να αλλάξουμε...")
    
    if (user_input or audio) and api_key:
        prompt = user_input if user_input else "Επεξεργασία φωνητικής εντολής..."
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)

        # Get Full Project Context (including itself)
        project_data = get_project_context()

        with st.chat_message("assistant"):
            with st.spinner("Ο Αρχιτέκτονας σκέφτεται..."):
                response = run_ai_logic(prompt, api_key, project_data)
                st.markdown(response)
                st.session_state.chat_history.append({"role": "assistant", "content": response})
                
                if "### FILE:" in response:
                    if st.button("💾 Εφαρμογή Αλλαγών στο Project"):
                        result = apply_code_changes(response)
                        st.info(result)
                        time.sleep(1)
                        st.rerun()

if __name__ == "__main__":
    main()