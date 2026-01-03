import streamlit as st
import os
import shutil
import re
import time
import subprocess
import json
from datetime import datetime
from pathlib import Path

try:
    from openai import OpenAI
    from streamlit_mic_recorder import mic_recorder
    import speech_recognition as sr
    from io import BytesIO
except ImportError:
    st.error("⚠️ Τρέξε: pip install openai streamlit-mic-recorder SpeechRecognition")
    st.stop()

# --- 1. ΡΥΘΜΙΣΕΙΣ ---
st.set_page_config(page_title="Mastro Nek v48 (Smart Select)", page_icon="🏗️", layout="wide")

# Αρχικοποίηση session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "file_history" not in st.session_state:
    st.session_state.file_history = []
if "backup_list" not in st.session_state:
    st.session_state.backup_list = []

def get_project_inventory():
    """Σαρώνει το project και επιστρέφει ΜΟΝΟ τον κώδικα, αγνοώντας βιβλιοθήκες."""
    inventory = []
    # Λίστα φακέλων που ΠΡΕΠΕΙ να αγνοούμε (Βιβλιοθήκες, Git, κλπ)
    ignore_list = {'.git', '__pycache__', 'venv', 'env', '.venv', 'node_modules', 'backups', '.streamlit'}

    for dirpath, dirnames, filenames in os.walk("."):
        # Αφαιρούμε τους φακέλους ignore από την αναζήτηση
        dirnames[:] = [d for d in dirnames if d not in ignore_list]

        for f in filenames:
            # Κρατάμε μόνο αρχεία κώδικα και ρυθμίσεων
            if f.endswith(('.py', '.json', '.css', '.txt', '.md', '.html', '.js', '.ts', '.yml', '.yaml')):
                rel_path = os.path.relpath(os.path.join(dirpath, f), ".")
                inventory.append(rel_path)
    return sorted(inventory)

def read_files(paths):
    """Διαβάζει τα επιλεγμένα αρχεία και επιστρέφει το περιεχόμενό τους."""
    context = ""
    for path in paths:
        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                context += f"\n--- ΑΡΧΕΙΟ: {path} ---\n{f.read()}\n"
        except Exception as e:
            context += f"\n--- ΑΡΧΕΙΟ: {path} ---\n[Σφάλμα ανάγνωσης: {str(e)}]\n"
    return context

def preview_file(filepath):
    """Εμφανίζει προεπισκόπηση ενός αρχείου."""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            lines = content.split('\n')
            return "\n".join(lines[:50]) + ("\n..." if len(lines) > 50 else "")
    except:
        return "[Δεν μπορεί να προβληθεί]"

def create_backup(filename):
    """Δημιουργεί backup ενός αρχείου."""
    if not os.path.exists(filename):
        return None

    backup_dir = "backups"
    os.makedirs(backup_dir, exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_name = f"{os.path.basename(filename)}_{timestamp}.bak"
    backup_path = os.path.join(backup_dir, backup_name)

    shutil.copy2(filename, backup_path)

    # Προσθήκη στο ιστορικό
    backup_info = {
        "original": filename,
        "backup": backup_path,
        "timestamp": timestamp,
        "size": os.path.getsize(filename)
    }
    st.session_state.backup_list.append(backup_info)

    return backup_path

def apply_updates_and_sync(text):
    """Εφαρμόζει τις αλλαγές από την AI και κάνει Git sync."""
    pattern = r"### FILE: (.+?)\n.*?```(?:python|json|css|javascript|typescript|html)?\n(.*?)```"
    matches = re.findall(pattern, text, re.DOTALL)

    if not matches:
        # Προσπάθεια με εναλλακτικό pattern
        pattern2 = r"--- ΑΡΧΕΙΟ: (.+?) ---\n(.*?)(?=\n--- ΑΡΧΕΙΟ: |\Z)"
        matches = re.findall(pattern2, text, re.DOTALL)

    if not matches:
        return "ℹ️ Δεν βρέθηκε κώδικας για ενημέρωση."

    log = []
    updated_files = []

    for filename, code in matches:
        filename = filename.strip().replace("\\", "/")

        # Καθαρισμός του κώδικα από επιπλέον κενά
        code = code.strip()

        # Δημιουργία backup πριν την αλλαγή
        if os.path.exists(filename):
            backup_path = create_backup(filename)
            if backup_path:
                log.append(f"📦 Backup δημιουργήθηκε: {os.path.basename(backup_path)}")

        try:
            # Δημιουργία φακέλων αν δεν υπάρχουν
            os.makedirs(os.path.dirname(filename), exist_ok=True)

            # Εγγραφή του νέου κώδικα
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(code)

            log.append(f"✅ Ενημερώθηκε το: {filename}")
            updated_files.append(filename)

            # Προσθήκη στο ιστορικό
            st.session_state.file_history.append({
                "file": filename,
                "action": "update",
                "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "size": len(code)
            })

        except Exception as e:
            log.append(f"❌ Σφάλμα στο {filename}: {str(e)}")

    # Αυτόματο Git Sync
    if updated_files:
        try:
            # Προσθήκη των αρχείων
            subprocess.run(["git", "add", "."], check=True, capture_output=True)

            # Commit
            commit_msg = f"Auto-update by Mastro Nek: {', '.join([os.path.basename(f) for f in updated_files[:3]])}"
            if len(updated_files) > 3:
                commit_msg += f" και άλλα {len(updated_files)-3}"

            result = subprocess.run(["git", "commit", "-m", commit_msg], 
                                  check=True, capture_output=True, text=True)
            log.append(f"📝 Commit: {commit_msg}")

            # Push
            push_result = subprocess.run(["git", "push"], 
                                       check=True, capture_output=True, text=True)
            log.append("🚀 Συγχρονίστηκε με το GitHub!")

        except subprocess.CalledProcessError as e:
            log.append(f"ℹ️ Git error: {e.stderr}")
        except Exception as e:
            log.append(f"ℹ️ Τοπική αποθήκευση OK (Git sync skip: {str(e)})")

    return "\n".join(log)

def process_audio(audio_bytes):
    """Μετατρέπει τον ήχο σε κείμενο."""
    if not audio_bytes:
        return None

    try:
        # Δημιουργία recognizer
        recognizer = sr.Recognizer()

        # Μετατροπή bytes σε AudioData
        audio_data = sr.AudioData(audio_bytes, sample_rate=44100, sample_width=2)

        # Αναγνώριση ομιλίας (Ελληνικά)
        text = recognizer.recognize_google(audio_data, language="el-GR")
        return text
    except sr.UnknownValueError:
        return "Δεν κατάλαβα την ομιλία"
    except sr.RequestError as e:
        return f"Σφάλση στην υπηρεσία αναγνώρισης: {e}"
    except Exception as e:
        return f"Σφάλμα επεξεργασίας ήχου: {str(e)}"

# --- 2. ENGINE ---
def run_deepseek(prompt, api_key, context):
    """Καλεί το DeepSeek API για επεξεργασία."""
    client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")

    system_msg = """Είσαι ο Mastro Nek, ένας έξυπνος βοηθός προγραμματιστή που μιλάει Ελληνικά.

Οδηγίες:
1. Μίλα πάντα Ελληνικά
2. Εξήγησε πρώτα το πλάνο σου
3. Πρότεινε βελτιώσεις
4. Γράψε πλήρη κώδικα με τη μορφή:
### FILE: filename.extension
```language
ο κώδικας εδώ