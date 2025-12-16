# Αρχείο: drive.py (v11 - Streamlit Cloud Ready)
import os
import json
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import tempfile
import streamlit as st
import pypdf
import google.generativeai as genai
import time

SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
TOKEN_FILE = "token.json"
CREDENTIALS_FILE = "credentials.json"
INDEX_FILE = "drive_index.json"
CONFIG_FILE = "drive_config.json"

def get_service():
    creds = None
    
    # 1. ΠΡΩΤΟΣ ΕΛΕΓΧΟΣ: Είμαστε στο Cloud; (Ψάχνουμε στα Secrets)
    if "token_json" in st.secrets:
        try:
            # Διαβάζουμε το Token από τα Secrets του Streamlit
            token_info = json.loads(st.secrets["token_json"])
            creds = Credentials.from_authorized_user_info(token_info, SCOPES)
            print("✅ Cloud Mode: Token loaded from Secrets.")
        except Exception as e:
            st.error(f"Error reading token from secrets: {e}")

    # 2. ΔΕΥΤΕΡΟΣ ΕΛΕΓΧΟΣ: Είμαστε στον Υπολογιστή; (Ψάχνουμε τοπικό αρχείο)
    if not creds and os.path.exists(TOKEN_FILE):
        try:
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
            print("✅ Local Mode: Token loaded from file.")
        except:
            creds = None

    # 3. Ανανέωση Token αν έχει λήξει
    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            print("🔄 Token Refreshed.")
        except:
            st.warning("Το Token έληξε. Χρειάζεται ανανέωση.")
            creds = None

    # 4. Αν δεν βρέθηκε τίποτα, επιστρέφουμε κενό (ή ζητάμε login αν είμαστε local)
    if not creds or not creds.valid:
        if "token_json" in st.secrets:
             st.error("⚠️ Σφάλμα πιστοποίησης στο Cloud.")
             return None
        # Κώδικας για Local Login (αν χρειαστεί ποτέ ξανά)
        if os.path.exists(CREDENTIALS_FILE):
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
            with open(TOKEN_FILE, 'w') as token:
                token.write(creds.to_json())
        else:
            return None

    return build('drive', 'v3', credentials=creds)

def save_config(folder_id):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump({"folder_id": folder_id}, f)

def load_config():
    if not os.path.exists(CONFIG_FILE): return ""
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f).get("folder_id", "")
    except: return ""

def get_files_list():
    if not os.path.exists(INDEX_FILE): return []
    try:
        with open(INDEX_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except: return []

# --- AI TAGGING LOGIC ---
def extract_preview_text(filepath):
    try:
        reader = pypdf.PdfReader(filepath)
        text = ""
        for i, page in enumerate(reader.pages):
            if i > 8: break
            text += page.extract_text() + "\n"
        return text
    except: return ""

def analyze_with_ai(text, filename):
    if "GEMINI_KEY" not in st.secrets: return "UNKNOWN", "GENERAL", "No API Key"
    genai.configure(api_key=st.secrets["GEMINI_KEY"])
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = f"""
    ANALYZE THIS MANUAL HEADER.
    Filename: {filename}
    Text content: {text[:2000]}
    
    RETURN ONLY A JSON STRING like this (No markdown):
    {{
        "model": "Exact Model Name (e.g. Ariston Clas One)",
        "type": "Category (SERVICE_MANUAL, USER_MANUAL, or GENERAL)",
        "topics": "Keywords"
    }}
    """
    try:
        resp = model.generate_content(prompt)
        clean_json = resp.text.replace("```json", "").replace("```", "").strip()
        data = json.loads(clean_json)
        return data.get("model", "Unknown"), data.get("type", "GENERAL"), data.get("topics", "")
    except:
        return filename, "GENERAL", "AI Error"

def sync_drive_folder(root_folder_id):
    if not root_folder_id or root_folder_id.strip() == "":
        st.error("⚠️ Το Folder ID είναι κενό!")
        return None

    service = get_service()
    if not service: 
        st.error("❌ Αδυναμία σύνδεσης με το Google Drive. Ελέγξτε τα Secrets.")
        return None
    
    save_config(root_folder_id)
    existing_index = {item['id']: item for item in get_files_list()}
    new_data = []
    folders_to_search = [root_folder_id]
    
    status_box = st.status("🧠 AI Indexing...", expanded=True)
    
    while folders_to_search:
        current_id = folders_to_search.pop(0)
        try:
            results = service.files().list(
                q=f"'{current_id}' in parents and mimeType = 'application/pdf' and trashed = false",
                fields="files(id, name)"
            ).execute()
            
            for f in results.get('files', []):
                file_id = f['id']
                if file_id in existing_index and existing_index[file_id].get("ai_analyzed", False):
                    new_data.append(existing_index[file_id])
                    status_box.write(f"✅ Γνωστό: {existing_index[file_id]['real_model']}")
                else:
                    status_box.write(f"🧐 Ανάλυση: {f['name']}...")
                    try:
                        request = service.files().get_media(fileId=file_id)
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                            downloader = MediaIoBaseDownload(tmp, request)
                            done = False
                            while done is False: status, done = downloader.next_chunk()
                            tmp.close()
                            
                            preview_text = extract_preview_text(tmp.name)
                            real_model, manual_type, topics = analyze_with_ai(preview_text, f['name'])
                            
                            entry = {
                                "id": file_id,
                                "name": f['name'],
                                "real_model": real_model,
                                "type": manual_type,
                                "topics": topics,
                                "search_terms": f"{real_model} {topics} {f['name']}".lower(),
                                "ai_analyzed": True
                            }
                            new_data.append(entry)
                            status_box.write(f"💾 Αποθηκεύτηκε: {real_model}")
                            with open(INDEX_FILE, "w", encoding="utf-8") as f:
                                json.dump(new_data, f, indent=4)
                            time.sleep(1)
                    except Exception as e:
                        status_box.warning(f"Σφάλμα στο {f['name']}: {e}")

            subfolders = service.files().list(
                q=f"'{current_id}' in parents and mimeType = 'application/vnd.google-apps.folder' and trashed = false",
                fields="files(id)"
            ).execute()
            for sub in subfolders.get('files', []): folders_to_search.append(sub['id'])
                
        except Exception as e:
            st.error(f"Error accessing folder: {e}")
            return None
            
    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(new_data, f, indent=4)
    status_box.update(label="✅ Ολοκληρώθηκε!", state="complete")
    return len(new_data)

def get_file_path(file_id):
    service = get_service()
    if not service: return None
    request = service.files().get_media(fileId=file_id)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        downloader = MediaIoBaseDownload(tmp, request)
        done = False
        while done is False: status, done = downloader.next_chunk()
        return tmp.name