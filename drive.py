# Αρχείο: drive.py (FINAL FULL VERSION)
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

# Πλήρη δικαιώματα (Read/Write/Move/Delete)
SCOPES = ['https://www.googleapis.com/auth/drive']

CREDENTIALS_FILE = "credentials.json"
TOKEN_FILE = "token.json"
INDEX_FILE = "drive_index.json"
CONFIG_FILE = "drive_config.json"

def get_service():
    """Συνδέεται στο Google Drive. ΠΡΟΤΕΡΑΙΟΤΗΤΑ: Τοπικό Αρχείο (Admin)."""
    creds = None
    
    # 1. ΠΡΩΤΟΣ ΕΛΕΓΧΟΣ: Τοπική σύνδεση (Admin/PC)
    if os.path.exists(CREDENTIALS_FILE):
        if os.path.exists(TOKEN_FILE):
            try:
                creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
            except:
                creds = None

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except:
                    creds = None
            
            if not creds:
                # Εδώ ανοίγει ο Browser για Login
                flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
                creds = flow.run_local_server(port=0)
            
            # Αποθήκευση του token για την επόμενη φορά
            with open(TOKEN_FILE, 'w') as token:
                token.write(creds.to_json())
        
        return build('drive', 'v3', credentials=creds)

    # 2. ΔΕΥΤΕΡΟΣ ΕΛΕΓΧΟΣ: Cloud Secrets (Server/Mobile)
    elif "connections" in st.secrets and "gsheets" in st.secrets["connections"]:
        try:
            from google.oauth2 import service_account
            key_dict = dict(st.secrets["connections"]["gsheets"])
            creds = service_account.Credentials.from_service_account_info(key_dict, scopes=SCOPES)
            return build('drive', 'v3', credentials=creds)
        except:
            return None
            
    return None

def save_config(folder_id):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump({"folder_id": folder_id}, f)
    except: pass

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

# --- AI TAGGING & SCANNING ---
def extract_preview_text(filepath):
    try:
        reader = pypdf.PdfReader(filepath)
        text = ""
        for i, page in enumerate(reader.pages):
            if i > 5: break
            extract = page.extract_text()
            if extract: text += extract + "\n"
        return text
    except: return ""

def analyze_with_ai(text, filename):
    api_key = st.secrets.get("GEMINI_KEY")
    if not api_key: return "UNKNOWN", "GENERAL", "No API Key"
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = f"""
    ANALYZE THIS MANUAL HEADER.
    Filename: {filename}
    Text content: {text[:1500]}
    
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
    """Η πλήρης συνάρτηση σάρωσης που ψάχνει παντού."""
    if not root_folder_id: return None
    service = get_service()
    if not service: 
        st.error("❌ Αδυναμία Σύνδεσης με Drive")
        return None
    
    save_config(root_folder_id)
    
    # Φόρτωση παλιού ευρετηρίου για να μην τα ξανακάνουμε όλα από την αρχή
    existing_index = {item['id']: item for item in get_files_list()}
    new_data = []
    
    folders_to_search = [root_folder_id]
    processed_folders = set() # Για να μην μπαίνουμε στους ίδιους κύκλους
    
    status_box = st.status("🧠 AI Indexing (Full Scan)...", expanded=True)
    count = 0
    
    while folders_to_search:
        current_id = folders_to_search.pop(0)
        if current_id in processed_folders: continue
        processed_folders.add(current_id)
        
        try:
            # 1. Βρες PDF
            results = service.files().list(
                q=f"'{current_id}' in parents and mimeType = 'application/pdf' and trashed = false",
                fields="files(id, name)"
            ).execute()
            
            for f in results.get('files', []):
                file_id = f['id']
                
                # Αν το ξέρουμε ήδη, το κρατάμε χωρίς ανάλυση
                if file_id in existing_index and existing_index[file_id].get("ai_analyzed", False):
                    new_data.append(existing_index[file_id])
                    # status_box.write(f"✅ Γνωστό: {f['name']}") # (Προαιρετικό για ταχύτητα)
                    continue

                # Αν είναι νέο -> AI Ανάλυση
                status_box.write(f"🧐 Ανάλυση: {f['name']}...")
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
                    status_box.write(f"🏷️ Νέο: {real_model}")
                    count += 1
                    time.sleep(1) # Ευγένεια προς το API

            # 2. Βρες Υποφακέλους
            subfolders = service.files().list(
                q=f"'{current_id}' in parents and mimeType = 'application/vnd.google-apps.folder' and trashed = false",
                fields="files(id)"
            ).execute()
            for sub in subfolders.get('files', []): 
                if sub['id'] not in processed_folders:
                    folders_to_search.append(sub['id'])
                
        except Exception as e:
            # status_box.warning(f"Error σε φάκελο: {e}")
            pass
            
    # Αποθήκευση στο τέλος
    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(new_data, f, indent=4)
    
    status_box.update(label=f"✅ Τέλος! Βρέθηκαν {len(new_data)} αρχεία.", state="complete")
    return len(new_data)

def get_file_path(file_id):
    service = get_service()
    if not service: return None
    try:
        request = service.files().get_media(fileId=file_id)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            downloader = MediaIoBaseDownload(tmp, request)
            done = False
            while done is False: status, done = downloader.next_chunk()
            return tmp.name
    except: return None