import streamlit as st
import os
import shutil
import ast
import re
import time
from datetime import datetime
import google.generativeai as genai
from streamlit_mic_recorder import mic_recorder

# --- 1. ΑΡΧΙΚΕΣ ΡΥΘΜΙΣΕΙΣ ---
st.set_page_config(page_title="Architect AI v35 (Universal)", page_icon="🚀", layout="wide")

# --- 2. ΒΟΗΘΗΤΙΚΕΣ ΣΥΝΑΡΤΗΣΕΙΣ ΣΥΣΤΗΜΑΤΟΣ ---
def get_project_context():
    """Σαρώνει τον φάκελο για να δώσει στο AI εικόνα ολόκληρου του project."""
    root_dir = os.path.dirname(os.path.abspath(__file__))
    file_contents = {}
    ignore = {'.git', '__pycache__', 'venv', '.streamlit', 'backups', '.DS_Store', 'requirements.txt'} 
    
    for dirpath, dirnames, filenames in os.walk(root_dir):
        dirnames[:] = [d for d in dirnames if d not in ignore]
        for f in filenames:
            if f in ignore or f.endswith(('.pyc', '.png', '.jpg', '.pdf', '.mp3', '.xlsx', '.bak')): continue 
            try:
                path = os.path.join(dirpath, f)
                rel_path = os.path.relpath(path, root_dir)
                with open(path, 'r', encoding='utf-8', errors='ignore') as file:
                    file_contents[rel_path] = file.read()
            except: pass
    return file_contents

def apply_code_changes(response_text):
    """Εξάγει τον κώδικα από την απάντηση και ενημερώνει τα αρχεία."""
    pattern = r"### FILE: (.+?)\n.*?```(?:python)?\n(.*?)```"
    matches = re.findall(pattern, response_text, re.DOTALL)
    log = []
    
    if not matches: return "ℹ️ Δεν βρέθηκε κώδικας προς αποθήκευση."

    for filename, code in matches:
        filename = filename.strip().replace("\\", "/")
        if filename.startswith("./"): filename = filename[2:]
        full_path = os.path.abspath(filename)
        
        # Δημιουργία Backup
        if os.path.exists(full_path):
            backup_dir = os.path.join(os.path.dirname(full_path), "backups")
            os.makedirs(backup_dir, exist_ok=True)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            shutil.copy2(full_path, os.path.join(backup_dir, f"{os.path.basename(full_path)}_{ts}.bak"))

        try:
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(code.strip())
            log.append(f"✅ UPDATED: {filename}")
        except Exception as e:
            log.append(f"❌ ERROR: {filename} ({str(e)})")
            
    return "\n".join(log)

# --- 3. Η ΜΗΧΑΝΗ ΤΟΥ AI (Dynamic Seeker) ---
def run_ai_logic(parts, api_key):
    if not api_key: return "❌ Σφάλμα: Λείπει το API Key."
    
    genai.configure(api_key=api_key)
    
    try:
        # Δυναμική αναζήτηση διαθέσιμων μοντέλων
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # Επιλογή μοντέλου με σειρά προτεραιότητας
        selected_model = None
        for target in ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-pro"]:
            for m in models:
                if target in m:
                    selected_model = m
                    break
            if selected_model: break
            
        if not selected_model:
            return f"❌ Δεν βρέθηκε συμβατό μοντέλο. Διαθέσιμα: {str(models)}"

        model = genai.GenerativeModel(selected_model)
        config = genai.types.GenerationConfig(temperature=0.2, max_output_tokens=8192)
        
        response = model.generate_content(parts, generation_config=config)
        return response.text
    except Exception as e:
        return f"❌ AI ERROR: {str(e)}"

# --- 4. ΠΕΡΙΒΑΛΛΟΝ ΧΡΗΣΤΗ (UI) ---
def main():
    st.title("🚀 Architect AI v35 (Universal Seeker)")
    
    with st.sidebar:
        st.header("Ρυθμίσεις")
        api_key = st.text_input("Gemini API Key", type="password")
        if not api_key and "GEMINI_API_KEY" in st.secrets:
            api_key = st.secrets["GEMINI_API_KEY"]
            st.success("Το κλειδί φορτώθηκε!")

        st.divider()
        st.subheader("🎤 Φωνή & 📂 Αρχεία")
        audio = mic_recorder(start_prompt="🎤 Rec", stop_prompt="⏹ Stop", key='mic_v35')
        uploaded = st.file_uploader("Screenshot ή PDF", type=['png','jpg','pdf'], label_visibility="collapsed")
        
        st.divider()
        project_data = get_project_context()
        strategy = st.selectbox("Στρατηγική", ["Νέα Λειτουργία", "Διόρθωση Bug", "Βελτίωση Κώδικα"])
        focus_file = st.selectbox("Αρχείο Εστίασης", ["Ολόκληρο το Project"] + list(project_data.keys()))
        auto_save = st.checkbox("Αυτόματη Αποθήκευση", value=False)

    # Διαχείριση Ιστορικού Chat
    if "messages" not in st.session_state: st.session_state.messages = []
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]): st.markdown(msg["content"])

    # Είσοδος Χρήστη
    user_prompt = st.chat_input("Πώς μπορώ να βοηθήσω στο project σήμερα;")
    
    if (user_prompt or audio or uploaded) and api_key:
        input_msg = user_prompt if user_prompt else "Ανάλυση αρχείου/φωνής..."
        st.session_state.messages.append({"role": "user", "content": input_msg})
        with st.chat_message("user"): st.markdown(input_msg)

        # Κατασκευή Context για το AI
        context_summary = "PROJECT STRUCTURE:\n" + "\n".join([f"--- {name} ---\n{content[:5000]}" for name, content in project_data.items()])
        
        full_prompt = f"""
        Είσαι ο Senior Architect (Mastro Nek). 
        ΠΛΑΙΣΙΟ: Εμπορική εφαρμογή HVAC SaaS.
        ΣΚΟΠΟΣ: {strategy} στο {focus_file}.
        
        ΟΔΗΓΙΕΣ:
        1. Μίλα Ελληνικά.
        2. Δώσε ΟΛΟΚΛΗΡΩΜΕΝΟ κώδικα για κάθε αρχείο που αλλάζεις.
        3. Χρησιμοποίησε ΑΚΡΙΒΩΣ αυτό το format για αρχεία:
        ### FILE: path/to/filename.py
        ```python
        (κώδικας)
        ```
        
        PROJECT CONTEXT:
        {context_summary}
        
        ΕΝΤΟΛΗ ΧΡΗΣΤΗ: {user_prompt if user_prompt else "Δες τα συνημμένα αρχεία/ήχο."}
        """

        parts = [full_prompt]
        if audio and audio['bytes']: parts.append({"mime_type": "audio/wav", "data": audio['bytes']})
        if uploaded: parts.append({"mime_type": uploaded.type, "data": uploaded.getvalue()})

        # Εκτέλεση AI
        with st.chat_message("assistant"):
            with st.spinner("Ο Αρχιτέκτονας αναλύει το project..."):
                response = run_ai_logic(parts, api_key)
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
                
                # Επιλογή Αποθήκευσης
                if "### FILE:" in response:
                    if auto_save:
                        st.code(apply_code_changes(response))
                        time.sleep(1)
                        st.rerun()
                    else:
                        if st.button("💾 Αποθήκευση Αλλαγών στο Project"):
                            log = apply_code_changes(response)
                            st.code(log)
                            st.success("Οι αλλαγές εφαρμόστηκαν!")
                            time.sleep(1)
                            st.rerun()

if __name__ == "__main__":
    main()