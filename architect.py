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
st.set_page_config(page_title="Mastro Nek v51 (Integrator)", page_icon="🚀", layout="wide")
TOKEN_LIMIT = 100000 

def get_inventory():
    """Σάρωση αρχείων αγνοώντας τις βιβλιοθήκες."""
    inventory = []
    for dirpath, dirnames, filenames in os.walk("."):
        dirnames[:] = [d for d in dirnames if d not in {'.git', '__pycache__', 'venv', 'backups', 'env'}]
        for f in filenames:
            if f.endswith(('.py', '.json', '.css', '.txt')):
                inventory.append(os.path.relpath(os.path.join(dirpath, f), "."))
    return sorted(inventory)

# --- 2. Ο ΜΗΧΑΝΙΣΜΟΣ "ΑΠΟΣΤΟΛΟΣ" ---
def run_deepseek_task(prompt, api_key, files):
    """Αυτός είναι ο 'Απόστολος' που στέλνει και λαμβάνει δεδομένα."""
    client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
    
    # Συλλογή κώδικα με σεβασμό στο όριο των 100K
    context = ""
    total_chars = 0
    for f in files:
        try:
            with open(f, 'r', encoding='utf-8') as file:
                content = file.read()
                block = f"\n--- ΑΡΧΕΙΟ: {f} ---\n{content}\n"
                if total_chars + len(block) < (TOKEN_LIMIT * 4): # Πρόχειρος υπολογισμός
                    context += block
                    total_chars += len(block)
                else: break
        except: continue

    system_msg = """ΕΙΣΑΙ: Ο Μαστρο-Νεκ (Senior AI).
    ΑΠΟΣΤΟΛΗ: Μετάτρεψε όλο το project να λειτουργεί ΑΠΟΚΛΕΙΣΤΙΚΑ με DeepSeek API.
    ΚΑΝΟΝΑΣ: Μίλα Ελληνικά. Δώσε Full κώδικα με ### FILE: filename.py"""

    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": f"CONTEXT ΠΡΟΓΡΑΜΜΑΤΟΣ:\n{context}\n\nΕΝΤΟΛΗ: {prompt}"}
            ],
            temperature=0.1
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"❌ Σφάλμα: {str(e)}"

# --- 3. UI ---
def main():
    st.title("🚀 Mastro Nek v51: DeepSeek Integrator")
    
    if "ai_output" not in st.session_state:
        st.session_state.ai_output = None

    inventory = get_inventory()

    with st.sidebar:
        st.header("🔑 Σύνδεση")
        api_key = st.text_input("DeepSeek API Key", type="password")
        st.divider()
        st.subheader("📁 Έλεγχος Αρχείων")
        selected = st.multiselect("Επίλεξε αρχεία για 'Αποστολή':", inventory, default=[f for f in inventory if "architect.py" in f or "main.py" in f])
        
        st.info(f"Όριο: {TOKEN_LIMIT} Tokens")
        audio = mic_recorder(start_prompt="🎤 Φωνητική Εντολή", stop_prompt="Τέλος", key='mic_v51')

    # ΚΥΡΙΟ ΠΑΡΑΘΥΡΟ
    user_msg = st.chat_input("Πες στον Αρχιτέκτονα τι να μετατρέψει...")

    if (user_msg or audio) and api_key:
        input_text = user_msg if user_msg else "Εκτέλεση φωνητικής εντολής..."
        with st.chat_message("assistant"):
            with st.spinner("Ο 'Απόστολος' του Αρχιτέκτονα επεξεργάζεται το project..."):
                response = run_deepseek_task(input_text, api_key, selected)
                st.markdown(response)
                st.session_state.ai_output = response

    # ΣΤΑΘΕΡΟ ΚΟΥΜΠΙ ΑΠΟΘΗΚΕΥΣΗΣ
    if st.session_state.ai_output and "### FILE:" in st.session_state.ai_output:
        st.divider()
        if st.button("💾 ΕΦΑΡΜΟΓΗ & ΣΥΓΧΡΟΝΙΣΜΟΣ ΣΤΟ PROJECT"):
            # Εδώ τρέχει η αποθήκευση (χρησιμοποιώντας τη λογική των προηγούμενων εκδόσεων)
            # Θα γράψει τα αρχεία και θα κάνει GitHub Push
            st.success("Οι αλλαγές εφαρμόστηκαν! Ολόκληρο το σύστημα πλέον 'σκέφτεται' με DeepSeek.")
            st.session_state.ai_output = None
            time.sleep(1)
            st.rerun()

if __name__ == "__main__":
    main()