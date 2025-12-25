# Αρχείο: smart_library.py
# ΕΚΔΟΣΗ: ULTIMATE (Adaptive Scan + Smart Folders + Excel Links + Safe Mode)

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

# --- ΡΥΘΜΙΣΕΙΣ ---
UNSORTED_FOLDER_NAME = "!_UNSORTED_REVIEW"
INDEX_FILE = "drive_index.json"
INITIAL_PAGES = 5      # Γρήγορη σάρωση
DEEP_SCAN_PAGES = 50   # Βαθιά σάρωση (αν χρειαστεί)

# --- ΛΕΞΕΙΣ-ΚΛΕΙΔΙΑ (KEYWORDS) ---
BOILER_KEYWORDS = [
    "BOILER", "GAS", "ΛΕΒΗΤΑΣ", "ΦΥΣΙΚΟ ΑΕΡΙΟ", "CONDENSING", "HEATING", 
    "GENUS", "CLAS", "CARES", "ALTEAS", "FAST EVO", "NIMBUS", "LYDOS", 
    "BAXI", "BUDERUS", "VIESSMANN", "IMMERGAS", "VAILLANT", "CHAFFOTEAUX", "RIELLO", "SENSYS"
]

TRAINING_KEYWORDS = [
    "TRAINING", "SEMINAR", "ACADEMY", "COURSE", "ΕΚΠΑΙΔΕΥΣΗ", "ΣΕΜΙΝΑΡΙΟ", 
    "PRESENTATION", "ΠΑΡΟΥΣΙΑΣΗ", "WEBINAR", "WORKSHOP", "MANUAL TRAINING"
]

# --- 1. ΛΕΙΤΟΥΡΓΙΑ AUTO-FIX DATABASE ---
def auto_fix_database(json_file):
    """Διορθώνει τη βάση δεδομένων αν λείπουν στήλες."""
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

# --- 2. AI & TEXT LOGIC ---

def find_best_model():
    """Επιλέγει το καλύτερο διαθέσιμο μοντέλο."""
    try:
        available = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        for pref in ['models/gemini-1.5-flash', 'models/gemini-1.5-pro', 'models/gemini-pro']:
            if pref in available: return pref
        return available[0]
    except: return 'gemini-pro'

def extract_text_from_pdf_bytes(fh, max_pages):
    """Βοηθητική συνάρτηση για να διαβάζει συγκεκριμένο αριθμό σελίδων."""
    text = ""
    try:
        fh.seek(0)
        reader = pypdf.PdfReader(fh)
        count = len(reader.pages)
        limit = count if max_pages is None else min(max_pages, count)
        for i in range(limit):
            text += reader.pages[i].extract_text() + "\n"
    except: pass
    return text

def analyze_document_deeply(text, filename, attempt=1):
    """
    Αναλύει το κείμενο με το AI.
    """
    api_key = st.secrets.get("GEMINI_KEY")
    if not api_key: return {"brand": "Unknown", "type": "GENERAL", "model": "-"}

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(find_best_model())
        
        # Προσαρμογή εντολής ανάλογα με την προσπάθεια
        instruction = f"Analyze this HVAC manual text: '{text[:5000]}'. Filename: '{filename}'."
        if attempt > 1:
            instruction = f"CRITICAL SEARCH: Previous attempt failed. Identify BRAND and TYPE from FILENAME: '{filename}' and text."

        prompt = f"""
        {instruction}
        Return a JSON object: {{"brand": "Name", "model": "Code", "type": "SERVICE/USER/INSTALLATION/TRAINING/BOILER"}}
        RULES:
        1. If text implies training/seminar, type='TRAINING'.
        2. If Gas Boiler/Heating, type='BOILER'.
        3. Brand must be a single word.
        If unknown, return "Unknown".
        """
        
        response = model.generate_content(prompt)
        clean_text = response.text.replace("```json", "").replace("```", "").strip()
        json_match = re.search(r'\{.*\}', clean_text, re.DOTALL)
        
        if json_match:
            data = json.loads(json_match.group())
            brand = str(data.get("brand", "Unknown")).strip().title()
            doc_type = str(data.get("type", "GENERAL")).upper()
            
            # --- PYTHON KEYWORD CHECK (Διόρθωση τύπου) ---
            full_str = (filename + " " + text[:1000]).upper()
            if any(k in full_str for k in TRAINING_KEYWORDS):
                doc_type = "TRAINING"
            elif any(k in full_str for k in BOILER_KEYWORDS):
                doc_type = "BOILER"

            # Αν αποτύχει η 1η φορά, επιστρέφουμε Unknown για να ενεργοποιηθεί το Deep Scan
            if (brand == "Unknown" or brand == "-") and attempt == 1:
                return {"brand": "Unknown", "type": doc_type, "model": "-"}
            
            return {
                "brand": brand if brand not in ["-", "", "None"] else "Unknown",
                "model": str(data.get("model", "-")).strip(),
                "type": doc_type
            }
    except:
        # Σε περίπτωση σφάλματος API, επιστρέφουμε Unknown για retry
        pass
    
    return {"brand": "Unknown", "type": "GENERAL", "model": "-"}

# --- 3. MAIN CRAWLER (ADAPTIVE SCAN) ---

def run_full_maintenance(root_folder_id):
    if not root_folder_id: return 0
    status_box = st.status("🧠 Έξυπνη Ταξινόμηση (Adaptive Mode)...", expanded=True)
    service = drive.get_service()
    if not service: return 0

    # Φάκελος Review
    review_folder_id = None
    try:
        res = service.files().list(q=f"name = '{UNSORTED_FOLDER_NAME}' and '{root_folder_id}' in parents and trashed = false").execute()
        review_folder_id = res.get('files')[0]['id'] if res.get('files') else service.files().create(body={'name': UNSORTED_FOLDER_NAME, 'mimeType': 'application/vnd.google-apps.folder', 'parents': [root_folder_id]}, fields='id').execute().get('id')
    except: pass

    old_index = []
    try: with open(INDEX_FILE, "r", encoding="utf-8") as f: old_index = json.load(f)
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
                
                # Έλεγχος αν πρέπει να το ξαναδούμε (αν είναι "ύποπτο" για λέβητα/εκπαίδευση)
                is_suspect = any(k in file_name.upper() for k in TRAINING_KEYWORDS + BOILER_KEYWORDS)
                
                if file_id in known_files and known_files[file_id].get("brand") != "Unknown" and not is_suspect:
                    new_index_data.append(known_files[file_id])
                    continue
                
                status_box.write(f"🧐 Ανάλυση: {file_name}")
                
                # --- ΒΗΜΑ 1: Γρήγορη Σάρωση (5 σελίδες) ---
                extracted_text = ""
                fh = io.BytesIO()
                try:
                    request = service.files().get_media(fileId=file_id)
                    downloader = MediaIoBaseDownload(fh, request); downloader.next_chunk()
                    extracted_text = extract_text_from_pdf_bytes(fh, INITIAL_PAGES)
                except: pass
                
                meta = analyze_document_deeply(extracted_text, file_name, attempt=1)
                
                # --- ΒΗΜΑ 2: Βαθιά Σάρωση (Αν το Βήμα 1 απέτυχε) ---
                if meta["brand"] == "Unknown":
                    status_box.write(f"⚠️ Δύσκολο αρχείο... Εκτελείται Βαθιά Σάρωση ({DEEP_SCAN_PAGES} σελίδες)...")
                    try:
                        extracted_text = extract_text_from_pdf_bytes(fh, DEEP_SCAN_PAGES)
                        meta = analyze_document_deeply(extracted_text, file_name, attempt=2)
                    except: pass

                brand = meta["brand"]
                doc_type = meta["type"]
                
                # --- ΕΠΙΛΟΓΗ ΦΑΚΕΛΟΥ ---
                target_name = brand
                if brand != "Unknown":
                    if "BOILER" in doc_type or any(k in file_name.upper() for k in BOILER_KEYWORDS):
                        target_name = f"{brand} (Gas-Heating)"
                    elif "TRAINING" in doc_type or any(k in file_name.upper() for k in TRAINING_KEYWORDS):
                        target_name = f"{brand} (Training)"
                
                # Δημιουργία/Εύρεση φακέλου
                if target_name not in folder_cache:
                    q = f"name = '{target_name}' and '{root_folder_id}' in parents and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
                    res = service.files().list(q=q).execute()
                    folder_cache[target_name] = res.get('files')[0]['id'] if res.get('files') else service.files().create(body={'name': target_name, 'mimeType': 'application/vnd.google-apps.folder', 'parents': [root_folder_id]}, fields='id').execute().get('id')
                
                tid = folder_cache.get(target_name, review_folder_id)
                
                # Μετακίνηση
                if tid and tid not in f.get('parents', []):
                    try: service.files().update(fileId=file_id, addParents=tid, removeParents=",".join(f.get('parents'))).execute()
                    except: pass
                
                new_index_data.append({
                    "id": file_id, "name": file_name, "brand": brand, 
                    "model": meta["model"], "meta_type": doc_type, 
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
    status_box.update(label=f"🏁 Ολοκληρώθηκε! ({processed_count} αρχεία)", state="complete")
    return len(new_index_data)

# --- 4. EXCEL EXPORT (SAFE MODE) ---

def get_stats_dataframe():
    """
    Επιστρέφει το DataFrame για το Excel.
    ΠΡΟΣΘΗΚΗ: Στήλη Link.
    ΣΗΜΕΙΩΣΗ: Κρατάμε τα κλειδιά (brand, meta_type) στα Αγγλικά
    για να μην κρασάρει το main.py που τα χρησιμοποιεί.
    """
    try:
        with open(INDEX_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        if not data: return None
        
        df = pd.DataFrame(data)

        # Προσθήκη Clickable Link
        if 'file_id' in df.columns:
            df['Link'] = df['file_id'].apply(lambda x: f'https://drive.google.com/open?id={x}')
            
        return df
    except: return None