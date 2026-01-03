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
st.set_page_config(page_title="Mastro Nek v46 (Human Style)", page_icon="🏗️", layout="wide")

def get_project_inventory():
    inventory = []
    ignore = {'.git', '__pycache__', 'venv', 'backups', '.streamlit', 'data'}
    for dirpath, dirnames, filenames in os.walk("."):
        dirnames[:] = [d for d in dirnames if d not in ignore]
        for f in filenames:
            if f.endswith(('.py', '.json', '.css', '.txt', '.md')):
                rel_path = os.path.relpath(os.path.join(dirpath, f), ".")
                inventory.append(rel_path)
    return inventory

def read_files(paths):
    context = ""
    for path in paths:
        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                context += f"\n--- ΑΡΧΕΙΟ: {path} ---\n{f.read()}\n"
        except: pass
    return context

def apply_updates(text):
    # Εντοπισμός του format ### FILE: filename
    pattern = r"### FILE: (.+?)\n.*?```(?:python|json|css)?\n(.*?)```"
    matches = re.findall(pattern, text, re.DOTALL)
    if not matches:
        return "ℹ️ Δεν βρέθηκε κώδικας προς αποθήκευση."
    
    results = []
    for filename, code in matches:
        filename = filename.strip().replace("\\", "/")
        full_path = os.path.abspath(filename)
        
        # Backup πριν την αλλαγή
        if os.path.exists(full_path):
            os.makedirs("backups", exist_ok=True)
            shutil.copy2(full_path, f"backups/{os.path.basename(filename)}_{datetime.now().strftime('%H%M%S')}.bak")
            
        try:
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(code.strip())
            results.append(f"✅ Αποθηκεύτηκε: {filename}")
        except Exception as e:
            results.append(f"❌ Σφάλμα στο {filename}: {e}")
    return "\n".join(results)

# --- 2. ΤΟ "ΜΥΑΛΟ" ΤΟΥ AI (MENTOR MODE) ---
def run_deepseek(prompt, api_key, context):
    client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
    
    # Εδώ είναι η κρίσιμη αλλαγή για να σου μιλάει κανονικά
    system_instruction = """
    ΕΙΣΑΙ: Ο Μαστρο-Νεκ, ο Senior Architect του project.
    ΣΤΥΛ: Φιλικός, επεξηγηματικός, δάσκαλος.
    ΓΛΩΣΣΑ: Αποκλειστικά Ελληνικά.
    
    ΚΑΝΟΝΕΣ ΕΠΙΚΟΙΝΩΝΙΑΣ:
    1. ΠΟΤΕ μην ξεκινάς απευθείας με κώδικα.
    2. Εξήγησε πρώτα με απλά λόγια τι πρόκειται να κάνεις και γιατί.
    3. Αν ο χρήστης σε ρωτήσει κάτι, απάντησε σαν άνθρωπος, όχι σαν μηχανή.
    4. Όταν δίνεις κώδικα, χρησιμοποίησε ΠΑΝΤΑ το format:
       ### FILE: όνομα_αρχείου.py
       ```python
       (κώδικας εδώ)
       ```
    """
    
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": f"CONTEXT ΠΡΟΓΡΑΜΜΑΤΟΣ:\n{context}\n\nΕΡΩΤΗΣΗ ΧΡΗΣΤΗ: {prompt}"}
            ],
            temperature=0.3
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"❌ Σφάλμα DeepSeek: {str(e)}"

# --- 3. UI ---
def main():
    st.title("🏗️ Μαστρο-Νεκ v46")
    st.subheader("Συνεργάτης Προγραμματισμού (DeepSeek Native)")
    
    inventory = get_project_inventory()
    
    with st.sidebar:
        st.header("Ρυθμίσεις")
        api_key = st.text_input("DeepSeek API Key", type="password")
        st.divider()
        st.write("📁 **Ποια αρχεία να 'διαβάσω';**")
        selected_files = st.multiselect("Επίλεξε αρχεία:", inventory, default=[f for f in inventory if "architect.py" in f])
        st.divider()
        audio = mic_recorder(start_prompt="🎤 Μίλα", stop_prompt="⏹ Τέλος", key='mic_v46')
        if st.button("🗑️ Καθαρισμός Συνομιλίας"):
            st.session_state.messages = []
            st.rerun()

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    user_input = st.chat_input("Πες μου τι θέλεις να φτιάξουμε...")
    
    if (user_input or audio) and api_key:
        prompt = user_input if user_input else "Φωνητική εντολή..."
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Διάβασμα context
        context = read_files(selected_files)
        
        with st.chat_message("assistant"):
            with st.spinner("Ο Μαστρο-Νεκ σκέφτεται..."):
                response = run_deepseek(prompt, api_key, context)
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
                
                # Εμφάνιση κουμπιού αποθήκευσης ΜΟΝΟ αν υπάρχει κώδικας στην απάντηση
                if "### FILE:" in response:
                    st.divider()
                    if st.button("💾 Αποθήκευση όλων των αλλαγών στο Project"):
                        result = apply_updates(response)
                        st.success(result)
                        time.sleep(1)
                        st.rerun()

if __name__ == "__main__":
    main()