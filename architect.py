import streamlit as st
import os
import shutil
import re
import time
import base64
from datetime import datetime

try:
    from openai import OpenAI
    from streamlit_mic_recorder import mic_recorder
except ImportError:
    st.error("⚠️ Τρέξε: pip install openai streamlit-mic-recorder")
    st.stop()

# --- 1. ΡΥΘΜΙΣΕΙΣ ---
st.set_page_config(page_title="Mastro Nek v47 (Human Style)", page_icon="🏗️", layout="wide")

def get_project_inventory():
    """Επιστρέφει όλα τα αρχεία του τρέχοντος φακέλου και υποφακέλων"""
    inventory = []
    ignore = {'.git', '__pycache__', 'venv', 'backups', '.streamlit', 'data', '.env', '.vscode'}

    for dirpath, dirnames, filenames in os.walk("."):
        # Αφαίρεση ignored φακέλων
        dirnames[:] = [d for d in dirnames if d not in ignore]

        for f in filenames:
            # Συμπερίληψη περισσότερων τύπων αρχείων
            if f.endswith(('.py', '.json', '.css', '.txt', '.md', '.html', '.js', '.yaml', '.yml', '.env', '.sql')):
                rel_path = os.path.relpath(os.path.join(dirpath, f), ".")
                # Αποφυγή backup αρχείων
                if not rel_path.startswith('backups/'):
                    inventory.append(rel_path)

    return sorted(inventory)

def read_files(paths):
    """Διαβάζει τα περιεχόμενα πολλαπλών αρχείων"""
    context = ""
    for path in paths:
        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                context += f"\n--- ΑΡΧΕΙΟ: {path} ---\n{f.read()}\n"
        except Exception as e:
            context += f"\n--- ΑΡΧΕΙΟ: {path} ---\n[Δεν μπόρεσα να διαβάσω αυτό το αρχείο: {e}]\n"
    return context

def transcribe_audio(audio_bytes, api_key):
    """Μετατρέπει audio bytes σε κείμενο χρησιμοποιώντας DeepSeek Whisper"""
    if not audio_bytes:
        return None

    try:
        client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")

        # Αποθήκευση προσωρινά του audio
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        # Μετατροπή με Whisper
        with open(tmp_path, "rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="el"  # Ελληνικά
            )

        # Καθαρισμός προσωρινού αρχείου
        os.unlink(tmp_path)

        return transcription.text
    except Exception as e:
        st.error(f"Σφάλμα μετατροπής ομιλίας: {e}")
        return None

def apply_updates(text):
    """Εφαρμόζει τις αλλαγές από την απάντηση του AI"""
    pattern = r"### FILE: (.+?)\n.*?```(?:python|json|css|html|javascript|sql)?\n(.*?)```"
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
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_name = f"backups/{os.path.basename(filename)}_{timestamp}.bak"
            shutil.copy2(full_path, backup_name)
            results.append(f"📦 Δημιουργήθηκε backup: {backup_name}")

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
    st.title("🏗️ Μαστρο-Νεκ v47")
    st.subheader("Συνεργάτης Προγραμματισμού (DeepSeek Native)")

    inventory = get_project_inventory()

    with st.sidebar:
        st.header("⚙️ Ρυθμίσεις")
        api_key = st.text_input("DeepSeek API Key", type="password", 
                               help="Χρειάζεσαι API key από https://platform.deepseek.com/")

        st.divider()

        st.header("🎤 Φωνητική Εισαγωγή")
        audio = mic_recorder(
            start_prompt="🎤 Ξεκίνα ηχογράφηση",
            stop_prompt="⏹ Σταμάτημα",
            key='mic_v47',
            format="wav"
        )

        st.divider()

        st.header("📁 Επιλογή Αρχείων")
        st.write(f"**Βρέθηκαν {len(inventory)} αρχεία**")

        # Κουμπιά για γρήγορη επιλογή
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📂 Όλα τα αρχεία", use_container_width=True):
                st.session_state.selected_all = True
        with col2:
            if st.button("🗑️ Καθαρισμός", use_container_width=True):
                if 'selected_files' in st.session_state:
                    st.session_state.selected_files = []
                st.rerun()

        # Πολυεπιλογή αρχείων
        if 'selected_all' in st.session_state and st.session_state.selected_all:
            selected_files = st.multiselect(
                "Επίλεξε αρχεία:",
                inventory,
                default=inventory,
                key="file_selector"
            )
            st.session_state.selected_all = False
        else:
            selected_files = st.multiselect(
                "Επίλεξε αρχεία:",
                inventory,
                default=[f for f in inventory if "architect.py" in f],
                key="file_selector"
            )

        st.divider()

        if st.button("🗑️ Καθαρισμός Συνομιλίας", use_container_width=True):
            st.session_state.messages = []
            st.rerun()

    # Αρχικοποίηση session state
    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "selected_files" not in st.session_state:
        st.session_state.selected_files = selected_files

    # Εμφάνιση ιστορικού συνομιλίας
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Επεξεργασία φωνητικής εισόδου
    user_input = ""
    if audio and api_key:
        with st.spinner("🔊 Μετατροπή ομιλίας σε κείμενο..."):
            transcribed_text = transcribe_audio(audio['bytes'], api_key)
            if transcribed_text:
                user_input = transcribed_text
                st.success(f"🎤 Μετατράπηκε: {transcribed_text}")
            else:
                st.error("Δεν μπόρεσα να μετατρέψω την ομιλία")

    # Κείμενη είσοδος
    if not user_input:
        user_input = st.chat_input("Πες μου τι θέλεις να φτιάξουμε...")

    # Επεξεργασία εισόδου
    if user_input and api_key:
        # Προσθήκη στο ιστορικό
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        # Διάβασμα context από επιλεγμένα αρχεία
        files_to_read = selected_files if selected_files else st.session_state.selected_files
        context = read_files(files_to_read)

        # Απάντηση από AI
        with st.chat_message("assistant"):
            with st.spinner("🧠 Ο Μαστρο-Νεκ σκέφτεται..."):
                response = run_deepseek(user_input, api_key, context)
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})

                # Εμφάνιση κουμπιού αποθήκευσης ΜΟΝΟ αν υπάρχει κώδικας
                if "### FILE:" in response:
                    st.divider()
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.info("📝 Βρέθηκε κώδικας στην απάντηση")
                    with col2:
                        if st.button("💾 Αποθήκευση Αλλαγών", type="primary", use_container_width=True):
                            result = apply_updates(response)
                            st.success(result)
                            time.sleep(2)
                            st.rerun()

    # Πληροφορίες για το project
    with st.expander("📊 Πληροφορίες Project"):
        st.write(f"**Συνολικά αρχεία:** {len(inventory)}")
        st.write(f"**Επιλεγμένα αρχεία:** {len(selected_files) if selected_files else 0}")

        if inventory:
            st.write("**Λίστα αρχείων:**")
            for file in inventory[:20]:  # Δείξε τα πρώτα 20
                st.write(f"• `{file}`")
            if len(inventory) > 20:
                st.write(f"... και άλλα {len(inventory) - 20} αρχεία")

if __name__ == "__main__":
    main()