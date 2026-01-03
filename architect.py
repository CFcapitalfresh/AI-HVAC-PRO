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

# --- 1. ΡΥΘΜΙΣΕΙΣ INTERFACE ---
st.set_page_config(page_title="Architect AI v40", page_icon="🏗️", layout="wide")

# --- 2. ΣΥΝΑΡΤΗΣΕΙΣ ΔΙΑΧΕΙΡΙΣΗΣ ΑΡΧΕΙΩΝ ---
def get_project_context():
    """Διαβάζει τα αρχεία του project με ασφάλεια για τα tokens."""
    root_dir = os.path.dirname(os.path.abspath(__file__))
    file_contents = {}
    ignore = {'.git', '__pycache__', 'venv', '.streamlit', 'backups', 'data'} 
    
    for dirpath, dirnames, filenames in os.walk(root_dir):
        dirnames[:] = [d for d in dirnames if d not in ignore]
        for f in filenames:
            # Διαβάζουμε μόνο αρχεία κώδικα και ρυθμίσεων
            if f.endswith(('.py', '.json', '.css', '.txt')):
                try:
                    rel_path = os.path.relpath(os.path.join(dirpath, f), root_dir)
                    with open(os.path.join(dirpath, f), 'r', encoding='utf-8', errors='ignore') as file:
                        content = file.read()
                        # Αν το αρχείο είναι πολύ μεγάλο, παίρνουμε ένα σημαντικό μέρος του
                        if len(content) > 8000:
                            content = content[:4000] + "\n... [Περικοπή για λόγους χωρητικότητας] ...\n" + content[-4000:]
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
        
        # Backup
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

# --- 3. Η ΜΗΧΑΝΗ ΤΟΥ AI (META LLAMA 3.3) ---
def run_ai_logic(prompt_text, api_key):
    if not api_key: return "❌ Παρακαλώ βάλε το Groq API Key στο sidebar."
    client = Groq(api_key=api_key)
    
    # Φόρτωση του context
    project_data = get_project_context()
    context_str = "PROJECT FILES:\n"
    for name, content in project_data.items():
        context_str += f"\n--- FILE: {name} ---\n{content}\n"

    system_prompt = """
    ΕΙΣΑΙ: Ο Mastro Nek, Senior AI Architect. 
    ΓΛΩΣΣΑ: Ελληνικά.
    ΚΑΘΗΚΟΝ: Βοήθησε τον χρήστη να αναπτύξει το HVAC SaaS project του.
    
    ΚΑΝΟΝΕΣ:
    1. Εξήγησε σύντομα στα Ελληνικά τι θα κάνεις.
    2. Δώσε ΠΛΗΡΗ κώδικα για τα αρχεία που αλλάζεις.
    3. Format: ### FILE: filename.py ακολουθούμενο από block κώδικα.
    """

    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"CONTEXT:\n{context_str}\n\nUSER REQUEST: {prompt_text}"}
            ],
            temperature=0.2,
            max_tokens=8192
        )
        return completion.choices[0].message.content
    except Exception as e:
        if "rate_limit_exceeded" in str(e):
            return "⏳ ΣΦΑΛΜΑ: Το project είναι πολύ μεγάλο για το δωρεάν όριο της Groq. Δοκίμασε να σβήσεις κάποια παλιά logs ή μεγάλα αρχεία κειμένου."
        return f"❌ AI ERROR: {str(e)}"

# --- 4. UI ---
def main():
    st.title("🏗️ Mastro Nek v40")
    st.caption("Stable & Self-Aware Edition (Llama 3.3)")

    with st.sidebar:
        st.header("Ρυθμίσεις")
        api_key = st.text_input("Groq API Key", type="password")
        st.divider()
        audio = mic_recorder(start_prompt="🎤 Rec", stop_prompt="⏹ Stop", key='mic_v40')
        st.divider()
        if st.button("🗑️ Clear Chat"):
            st.session_state.chat_history = []
            st.rerun()

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # Προβολή ιστορικού
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Είσοδος χρήστη
    user_input = st.chat_input("Πώς προχωράμε σήμερα;")
    
    if (user_input or audio) and api_key:
        prompt = user_input if user_input else "Επεξεργασία φωνητικής εντολής..."
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Ο Αρχιτέκτονας εργάζεται..."):
                response = run_ai_logic(prompt, api_key)
                st.markdown(response)
                st.session_state.chat_history.append({"role": "assistant", "content": response})
                
                if "### FILE:" in response:
                    if st.button("💾 Apply Changes"):
                        log = apply_code_changes(response)
                        st.info(log)
                        time.sleep(1)
                        st.rerun()

if __name__ == "__main__":
    main()