# Αρχείο: smart_library.py
# ΕΚΔΟΣΗ: FULL MERGED (ΟΛΕΣ ΟΙ ΛΕΙΤΟΥΡΓΙΕΣ + ΚΑΙΝΟΥΡΓΙΑ ΚΑΤΗΓΟΡΙΟΠΟΙΗΣΗ)

import streamlit as st
import google.generativeai as genai
from googleapiclient.http import MediaIoBaseDownload
import io
import time
import json
import pypdf
import drive
import re
import os
import pandas as pd

# Ρυθμίσεις
UNSORTED_FOLDER_NAME = "!_UNSORTED_REVIEW"
INDEX_FILE = "drive_index.json"

# --- 1. ΛΙΣΤΕΣ ΛΕΞΕΩΝ-ΚΛΕΙΔΙΩΝ (ΝΕΑ ΠΡΟΣΘΗΚΗ) ---
BOILER_KEYWORDS = [
    "BOILER", "GAS", "ΛΕΒΗΤΑΣ", "ΦΥΣΙΚΟ ΑΕΡΙΟ", "CONDENSING", "HEATING", 
    "GENUS", "CLAS", "CARES", "ALTEAS", "FAST EVO", "NIMBUS", "LYDOS", 
    "BAXI", "BUDERUS", "VIESSMANN", "IMMERGAS", "VAILLANT", "CHAFFOTEAUX", "RIELLO", "SENSYS"
]

TRAINING_KEYWORDS = [
    "TRAINING", "SEMINAR", "ACADEMY", "COURSE", "ΕΚΠΑΙΔΕΥΣΗ", "ΣΕΜΙΝΑΡΙΟ", 
    "PRESENTATION", "ΠΑΡΟΥΣΙΑΣΗ", "WEBINAR", "WORKSHOP", "MANUAL TRAINING"
]

# --- 2. AUTO-FIX DATABASE (ΔΙΑΤΗΡΗΣΗ ΛΕΙΤΟΥΡΓΙΑΣ) ---
def auto_fix_database(json_file):
    """
    Ελέγχει αν το αρχείο βάσης (json) υπάρχει και αν έχει τις σωστές στήλες.
    """
    required_columns = ['name', 'brand', 'model', 'meta_type', 'file_id', 'error_codes']
    
    if not os.path.exists(json_file):
        df = pd.DataFrame(columns=required_columns)
        try: df.to_json(json_file, orient='records', indent=4)
        except: pass
        return df

    try:
        df = pd.read_json(json_file)
        missing_cols = [col for col in required_columns if col not in df.columns]
        if missing_cols:
            for col in missing_cols: df[col] = "Unknown" 
            df.to_json(json_file, orient='records', indent=4)
        return df
    except:
        return pd.DataFrame(columns=required_columns)

# --- 3. AI LOGIC (ΕΠΙΜΟΝΗ ΑΝΑΛΥΣΗ) ---

def find_best_model():
    """Επιλέγει το καλύτερο μοντέλο Gemini."""
    try:
        available = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        for pref in ['models/gemini-1.5-flash', 'models/gemini-1.5-pro', 'models/gemini-pro']:
            if pref in available: return pref
        return available[0]
    except: return 'gemini-pro'

def analyze_document_deeply(text, filename, attempt=1):
    """
    Η κύρια συνάρτηση AI.
    Περιλαμβάνει το Loop επανάληψης (Retry logic) και τώρα
    ελέγχει και για Λέβητες/Εκπαίδευση.
    """
    api_key = st.secrets.get("GEMINI_KEY")
    if not api_key: return {"brand": "Unknown", "type": "GENERAL", "model": "-"}

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(find_best_model())
        
        # Διαφορετικό prompt ανάλογα με την προσπάθεια
        if attempt == 1:
            instruction = f"Analyze this HVAC manual text: '{text[:2500]}'. Filename: '{filename}'."
        else:
            instruction = f"CRITICAL SEARCH: The previous text analysis was unclear. Use your expert knowledge to identify the BRAND from this FILENAME: '{filename}'. Even if the brand name isn't there, infer it from the model code."

        prompt = f"""
        {instruction}
        Return a JSON object: {{"brand": "Name", "model": "Code", "type": "SERVICE/USER/INSTALLATION/TRAINING/BOILER"}}
        If absolutely unknown, use "Unknown". 
        Brand must be a single word.
        RULES:
        1. If it's a Training Manual/Seminar, type="TRAINING".
        2. If it's a Gas Boiler/Heating, type="BOILER".
        """
        
        response = model.generate_content(prompt)
        clean_text = response.text.replace("```json", "").replace("```", "").strip()
        json_match = re.search(r'\{.*\}', clean_text, re.DOTALL)
        
        if json_match:
            data = json.loads(json_match.group())
            brand = str(data.get("brand", "Unknown")).strip().title()
            doc_type = str(data.get("type", "GENERAL")).upper()

            # --- ΝΕΑ ΠΡΟΣΘΗΚΗ: Check Keywords (Python Logic) ---
            # Διορθώνουμε το AI αν έκανε λάθος στον τύπο
            full_str = (filename + " " + text[:500]).upper()
            
            if any(k in full_str for k in TRAINING_KEYWORDS):
                doc_type = "TRAINING"
            elif any(k in full_str for k in BOILER_KEYWORDS):
                doc_type = "BOILER"
            # ---------------------------------------------------

            # Αν αποτύχει η 1η φορά, δοκίμασε 2η
            if (brand == "Unknown" or brand == "-") and attempt == 1:
                return analyze_document_deeply(text, filename, attempt=2)
            
            return {
                "brand": brand if brand not in ["-", "", "None"] else "Unknown",
                "model": str(data.get("model", "-")).strip(),
                "type": doc_type
            }
    except:
        if attempt == 1: return analyze_document_deeply(text, filename, attempt=2)
    
    return {"brand": "Unknown", "type": "GENERAL", "model": "-"}

# --- 4. MAINTENANCE LOGIC (CRAWLER) ---

def run_full_maintenance(root_folder_id):
    """
    Σαρώνει το Drive, αναγνωρίζει αρχεία και τα μετακινεί.
    Τώρα υποστηρίζει έξυπνους φακέλους (Heating/Training).
    """
    if not root_folder_id: return 0
    status_box = st.status("🧠 Έξυπνη Ταξινόμηση σε εξέλιξη...", expanded=True)
    service = drive.get_service()
    if not service: return 0

    # Εξασφάλιση φακέλου Review
    review_folder_id = None
    try:
        res = service.files().list(q=f"name = '{UNSORTED_FOLDER_NAME}' and '{root_folder_id}' in parents and trashed = false").execute()
        review_folder_id = res.get('files')[0]['id'] if res.get('files') else service.files().create(body={'name': UNSORTED_FOLDER_NAME, 'mimeType': 'application/vnd.google-apps.folder', 'parents': [root_folder_id]}, fields='id').execute().get('id')
    except: pass

    old_index = []
    try:
        with open(INDEX_FILE, "r", encoding="utf-8") as f: old_index = json.load(f)
    except: pass
    known_files = {x['id']: x for x in old_index}
    
    new_index_data = []
    folders_to_scan = [root_folder_id]
    folder_cache = {"Unknown": review_folder_id}
    processed_count = 0
    
    while folders_to_scan:
        current_id = folders_to_scan.pop(0)
        if current_id == review_folder_id: continue

        try:
            results = service.files().list(q=f"'{current_id}' in parents and mimeType = 'application/pdf' and trashed = false", fields="files(id, name, parents)").execute()
            
            for f in results.get('files', []):
                file_id = f['id']
                file_name = f['name']
                
                # --- ΕΛΕΓΧΟΣ: Μήπως πρέπει να ξανα-ελέγξουμε το αρχείο; ---
                # Αν περιέχει λέξεις κλειδιά αλλά είναι σε λάθος φάκελο, το μαρκάρουμε ως "ύποπτο"
                is_suspect = any(k in file_name.upper() for k in TRAINING_KEYWORDS + BOILER_KEYWORDS)
                
                # Αν είναι γνωστό και ΟΧΙ ύποπτο, το κρατάμε ως έχει
                if file_id in known_files and known_files[file_id].get("brand") != "Unknown" and not is_suspect:
                    new_index_data.append(known_files[file_id])
                    continue
                
                status_box.write(f"🧐 Ανάλυση: {file_name}")
                
                extracted_text = ""
                try:
                    request = service.files().get_media(fileId=file_id)
                    fh = io.BytesIO(); downloader = MediaIoBaseDownload(fh, request); downloader.next_chunk()
                    fh.seek(0); reader = pypdf.PdfReader(fh)
                    for i in range(min(5, len(reader.pages))): extracted_text += reader.pages[i].extract_text() + "\n"
                except: pass
                
                # ΚΑΛΟΥΜΕ ΤΟ AI
                metadata = analyze_document_deeply(extracted_text, file_name)
                brand = metadata["brand"]
                doc_type = metadata["type"]
                
                # --- ΝΕΑ ΛΟΓΙΚΗ ΟΝΟΜΑΣΙΑΣ ΦΑΚΕΛΩΝ ---
                target_folder_name = brand
                
                if brand != "Unknown":
                    # Αν είναι Λέβητας -> (Gas-Heating)
                    if "BOILER" in doc_type or any(k in file_name.upper() for k in BOILER_KEYWORDS):
                        target_folder_name = f"{brand} (Gas-Heating)"
                    # Αν είναι Εκπαίδευση -> (Training)
                    elif "TRAINING" in doc_type or any(k in file_name.upper() for k in TRAINING_KEYWORDS):
                        target_folder_name = f"{brand} (Training)"
                
                # Εύρεση ή Δημιουργία Φακέλου
                if target_folder_name not in folder_cache:
                    q = f"name = '{target_folder_name}' and '{root_folder_id}' in parents and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
                    res_b = service.files().list(q=q).execute()
                    if res_b.get('files'): folder_cache[target_folder_name] = res_b.get('files')[0]['id']
                    else:
                        meta = {'name': target_folder_name, 'mimeType': 'application/vnd.google-apps.folder', 'parents': [root_folder_id]}
                        folder_cache[target_folder_name] = service.files().create(body=meta, fields='id').execute().get('id')
                
                target_id = folder_cache.get(target_folder_name, review_folder_id)
                
                # Μετακίνηση αρχείου
                if target_id and target_id not in f.get('parents', []):
                    try:
                        service.files().update(fileId=file_id, addParents=target_id, removeParents=",".join(f.get('parents'))).execute()
                    except: pass
                
                new_index_data.append({
                    "id": file_id, "name": file_name, "brand": brand,
                    "model": metadata["model"], "meta_type": doc_type,
                    "status": "auto_verified"
                })
                processed_count += 1
                time.sleep(0.3)
            
            subs = service.files().list(q=f"'{current_id}' in parents and mimeType = 'application/vnd.google-apps.folder' and trashed = false", fields="files(id, name)").execute()
            for s in subs.get('files', []):
                if s['id'] != review_folder_id and s['name'] not in folder_cache: 
                    folders_to_scan.append(s['id'])
        except: pass

    with open(INDEX_FILE, "w", encoding="utf-8") as f: json.dump(new_index_data, f, indent=4)
    status_box.update(label=f"🏁 Η συντήρηση ολοκληρώθηκε! Επεξεργάστηκαν: {processed_count}", state="complete")
    return len(new_index_data)

# --- 5. EXCEL EXPORT (ΔΙΟΡΘΩΜΕΝΟ) ---

def get_stats_dataframe():
    """
    Επιστρέφει το DataFrame.
    ΠΡΟΣΟΧΗ: Κρατάμε τα Αγγλικά ονόματα στηλών (brand, meta_type) 
    για να μην σπάσει το main.py, αλλά προσθέτουμε τη στήλη LINK.
    """
    try:
        with open(INDEX_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        if not data: return None
        
        df = pd.DataFrame(data)

        # 1. ΠΡΟΣΘΗΚΗ LINK (Το νέο χαρακτηριστικό)
        if 'file_id' in df.columns:
            df['Link'] = df['file_id'].apply(lambda x: f'https://drive.google.com/open?id={x}')
            
        return df
    except: return None