# Αρχείο: drive.py (v10 - Auto-Save & Smart Sync)
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
CREDENTIALS_FILE = "credentials.json"
TOKEN_FILE = "token.json"
INDEX_FILE = "drive_index.json"
CONFIG_FILE = "drive_config.json"

def get_service():
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CREDENTIALS_FILE): return None
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, 'w') as token: token.write(creds.to_json())
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

# --- AI TAGGING ---
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
        "topics": "Keywords (e.g. error codes, wiring)"
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
        st.error("⚠️ ΠΡΟΣΟΧΗ: Το πεδίο Folder ID είναι κενό!")
        return None

    service = get_service()
    if not service: return None
    
    save_config(root_folder_id)
    
    # Φορτώνουμε τη μνήμη για να μην κάνουμε διπλή δουλειά
    existing_index = {item['id']: item for item in get_files_list()}
    new_data = []
    
    folders_to_search = [root_folder_id]
    status_box = st.status("🧠 AI Indexing (Auto-Save Ενεργό)...", expanded=True)
    
    processed_count = 0
    
    while folders_to_search:
        current_id = folders_to_search.pop(0)
        try:
            results = service.files().list(
                q=f"'{current_id}' in parents and mimeType = 'application/pdf' and trashed = false",
                fields="files(id, name)"
            ).execute()
            
            for f in results.get('files', []):
                file_id = f['id']
                
                # ΕΛΕΓΧΟΣ: Το έχουμε ξαναδεί;
                if file_id in existing_index and existing_index[file_id].get("ai_analyzed", False):
                    # ΝΑΙ -> Το κρατάμε όπως είναι (Γρήγορο)
                    new_data.append(existing_index[file_id])
                    status_box.write(f"✅ Γνωστό αρχείο: {existing_index[file_id]['real_model']}")
                else:
                    # ΟΧΙ -> Το αναλύουμε (Αργό)
                    status_box.write(f"🧐 Ανάλυση νέου: {f['name']}...")
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
                            
                            # --- ΤΟ ΜΥΣΤΙΚΟ: ΑΠΟΘΗΚΕΥΣΗ ΤΩΡΑ ---
                            # Σώζουμε τη λίστα μετά από κάθε νέο αρχείο!
                            with open(INDEX_FILE, "w", encoding="utf-8") as f:
                                json.dump(new_data, f, indent=4)
                            
                            time.sleep(1)
                    except Exception as e:
                        status_box.warning(f"Σφάλμα στο αρχείο {f['name']}: {e}")

                processed_count += 1

            subfolders = service.files().list(
                q=f"'{current_id}' in parents and mimeType = 'application/vnd.google-apps.folder' and trashed = false",
                fields="files(id)"
            ).execute()
            for sub in subfolders.get('files', []): folders_to_search.append(sub['id'])
                
        except Exception as e:
            st.error(f"Σφάλμα φακέλου: {e}")
            return None
            
    # Τελική αποθήκευση (για να σβηστούν όσα αρχεία αφαιρέθηκαν από το Drive)
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