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
st.set_page_config(page_title="Architect AI v39 (Optimized)", page_icon="🏗️", layout="wide")

def get_project_context(focus_file=None):
    """
    Διαβάζει το project έξυπνα. Αν υπάρχει focus_file, δίνει όλο τον κώδικα του, 
    αλλιώς δίνει μόνο περιλήψεις για να γλιτώσουμε tokens.
    """
    root_dir = os.path.dirname(os.path.abspath(__file__))
    file_contents = {}
    ignore = {'.git', '__pycache__', 'venv', '.streamlit', 'backups', 'data'} 
    
    for dirpath, dirnames, filenames in os.walk(root_dir):
        dirnames[:] = [d for d in dirnames if d not in ignore]
        for f in filenames:
            if f.endswith(('.py', '.json', '.css')):
                rel_path = os.path.relpath(os.path.join(dirpath, f), root_dir)
                try:
                    with open(os.path.join(dirpath, f), 'r', encoding='utf-8', errors='ignore') as file:
                        content = file.read()
                        # Αν το αρχείο είναι αυτό που θέλουμε να αλλάξουμε, το στέλνουμε όλο.
                        # Αλλιώς, στέλνουμε μόνο τις πρώτες 100 γραμμές για εξοικονόμηση tokens.
                        if focus_file and rel_path == focus_file:
                            file_contents[rel_path] = content
                        elif "architect.py" in rel_path: # Πάντα βλέπει τον εαυτό του
                            file_contents[rel_path] = content
                        else:
                            file_contents[rel_path] = content[:1500] + "\n... [truncated for token limit] ..."
                except: pass
    return file_contents

def apply_code_changes(response_text):
    pattern = r"### FILE: (.+?)\n.*?```(?:python|json|css)?\n(.*?)```"
    matches = re.findall(pattern, response_text, re.DOTALL)
    log = []
    if not matches: return "ℹ️ Δεν εντοπίστηκε κώδικας."
    
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
            log.append(f"✅ ΕΝΗΜΕΡΩΘΗΚΕ: {filename}")
        except Exception as e: log.append(f"❌ ΣΦΑΛΜΑ: {filename} ({e})")
    return "\n".join(log)

# --- 2. Η ΜΗΧΑΝΗ ΤΟΥ AI ---
def run_ai_logic(prompt_text, api_key, context_data):
    if not api_key: return "❌ Εισάγετε το Groq API Key."
    client = Groq(api_key=api_key)
    
    context_str = "PROJECT SNIPPETS (Optimized):\n"
    for name, content in context_data.items():
        context_str += f"\n--- FILE: {name} ---\n{content}\n"

    system_prompt = """
    ΕΙΣΑΙ: Ο Mastro Nek, Senior Architect. 
    ΓΛΩΣΣΑ: Ελληνικά. 
    ΚΑΝΟΝΑΣ: Εξήγησε σύντομα τι θα κάνεις και μετά δώσε τον κώδικα με ### FILE: filename.py
    """

    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"CONTEXT:\n{context_str}\n\nUSER REQUEST: {prompt_text}"}
            ],
            temperature=0.2,
        )
        return completion.choices[0].message.content
    except Exception as e:
        if "rate_limit_exceeded" in str(e):
            return "⏳ ΣΦΑΛΜΑ: Πολύ μεγάλο αίτημα για το δωρεάν πακέτο της Groq. Δοκίμασε να επιλέξεις ένα συγκεκριμένο αρχείο εστίασης."
        return f"❌ Σφάλμα AI: {str(e)}"

# --- 3. UI ---
def main():
    st.title("🏗️ Mastro Nek v39")
    
    # Φόρτωση ονομάτων αρχείων για το dropdown
    all_files = list(get_project_context().keys())

    with st.sidebar:
        api_key = st.text_input("Groq API Key", type="password")
        audio = mic_recorder(start_prompt="🎤 Φωνή", stop_prompt="Τέλος", key='mic_v39')
        st.divider()
        # ΕΠΙΛΟΓΗ ΑΡΧΕΙΟΥ ΕΣΤΙΑΣΗΣ: Πολύ σημαντικό για να μην σκάει το όριο tokens
        focus_file = st.selectbox("Εστίαση σε αρχείο (για εξοικονόμηση tokens):", ["Κανένα"] + all_files)
        auto_save = st.checkbox("Auto-Save", value=False)

    if "chat_history" not in st.session_state: st.session_state.chat_history = []
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]): st.markdown(msg["content"])

    user_input = st.chat_input("Πώς να βοηθήσω;")
    
    if (user_input or audio) and api_key:
        prompt = user_input if user_input else "Φωνητική εντολή..."
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)

        # Διάβασμα context με βάση το αρχείο εστίασης
        selected_focus = None if focus_file == "Κανένα" else focus_file
        project_data = get_project_context(selected_focus)

        with st.chat_message("assistant"):
            with st.spinner("Σκέφτομαι..."):
                response = run_ai_logic(prompt, api_key, project_data)
                st.markdown(response)
                st.session_state.chat_history.append({"role": "assistant", "content": response})
                
                if "### FILE:" in response:
                    if auto_save or st.button("💾 Apply"):
                        st.info(apply_code_changes(response))
                        time.sleep(1)
                        st.rerun()

if __name__ == "__main__":
    main()