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

# --- ΛΙΣΤΕΣ ΛΕΞΕΩΝ-ΚΛΕΙΔΙΩΝ (ΓΙΑ ΟΛΕΣ ΤΙΣ ΜΑΡΚΕΣ) ---
# Αυτές οι λέξεις καθορίζουν αν θα μπει σε φάκελο Θέρμανσης ή Εκπαίδευσης
BOILER_KEYWORDS = [
    "BOILER", "GAS", "ΛΕΒΗΤΑΣ", "ΦΥΣΙΚΟ ΑΕΡΙΟ", "CONDENSING", "HEATING", 
    "GENUS", "CLAS", "CARES", "ALTEAS", "FAST EVO", "NIMBUS", "LYDOS", 
    "BAXI", "BUDERUS", "VIESSMANN", "IMMERGAS", "VAILLANT", "CHAFFOTEAUX", "RIELLO"
]

TRAINING_KEYWORDS = [
    "TRAINING", "SEMINAR", "ACADEMY", "COURSE", "ΕΚΠΑΙΔΕΥΣΗ", "ΣΕΜΙΝΑΡΙΟ", 
    "PRESENTATION", "ΠΑΡΟΥΣΙΑΣΗ", "WEBINAR", "WORKSHOP", "MANUAL TRAINING"
]

# --- 1. ΛΕΙΤΟΥΡΓΙΑ AUTO-FIX DATABASE ---
def auto_fix_database(json_file):
    """
    Ελέγχει αν το αρχείο βάσης (json) υπάρχει και αν έχει τις σωστές στήλες.
    Αν κάτι λείπει, το διορθώνει αυτόματα χωρίς να κρασάρει το πρόγραμμα.
    """
    required_columns = ['name', 'brand', 'model', 'meta_type', 'file_id', 'error_codes']
    
    # Περίπτωση 1: Δεν υπάρχει καθόλου το αρχείο
    if not os.path.exists(json_file):
        df = pd.DataFrame(columns=required_columns)
        try:
            df.to_json(json_file, orient='records', indent=4)
        except: pass
        return df

    # Περίπτωση 2: Υπάρχει, αλλά μπορεί να είναι παλιό
    try:
        df = pd.read_json(json_file)
        
        # Ελέγχουμε αν λείπει καμία στήλη
        missing_cols = [col for col in required_columns if col not in df.columns]
        
        if missing_cols:
            # Προσθέτουμε τις κενές στήλες που λείπουν
            for col in missing_cols:
                df[col] = "Unknown" 
                
            # Αποθηκεύουμε τη διορθωμένη έκδοση
            df.to_json(json_file, orient='records', indent=4)
            
        return df
        
    except Exception as e:
        return pd.DataFrame(columns=required_columns)

# --- 2. ΛΕΙΤΟΥΡΓΙΕΣ AI & DRIVE ---

def find_best_model():
    """Επιλέγει αυτόματα το καλύτερο διαθέσιμο μοντέλο."""
    try:
        available = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        for pref in ['models/gemini-1.5-flash', 'models/gemini-1.5-pro', 'models/gemini-pro']:
            if pref in available: return pref
        return available[0]
    except: return 'gemini-pro'

def analyze_document_deeply(text, filename, attempt=1):
    """Επίμονη ανάλυση με πολλαπλές προσπάθειες και έξυπνη κατηγοριοποίηση."""
    api_key = st.secrets.get("GEMINI_KEY")
    if not api_key: return {"brand": "Unknown", "type": "GENERAL", "model": "-"}

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(find_best_model())
        
        # Διαφορετικό prompt ανάλογα με την προσπάθεια
        instruction = f"Analyze this HVAC manual text: '{text[:2500]}'. Filename: '{filename}'."
        if attempt > 1:
            instruction = f"CRITICAL SEARCH: Previous attempt failed. Identify BRAND and TYPE from FILENAME: '{filename}' and text."

        prompt = f"""
        {instruction}
        Return a JSON object: {{"brand": "Name", "model": "Code", "type": "SERVICE/USER/INSTALLATION/TRAINING/BOILER/PARTS"}}
        
        RULES:
        1. If text/filename suggests training material, set type to 'TRAINING'.
        2. If it is a Gas Boiler or Heating unit, set type to 'BOILER'.
        3. Brand must be a single word.
        If absolutely unknown, use "Unknown".
        """
        
        response = model.generate_content(prompt)
        clean_text = response.text.replace("```json", "").replace("```", "").strip()
        json_match = re.search(r'\{.*\}', clean_text, re.DOTALL)
        
        if json_match:
            data = json.loads(json_match.group())
            brand = str(data.get("brand", "Unknown")).strip().title()
            doc_type = str(data.get("type", "GENERAL")).upper()
            
            # --- ΕΞΤΡΑ ΕΛΕΓΧΟΣ ΜΕ KEYWORDS (ΑΥΤΟΜΑΤΗ ΔΙΟΡΘΩΣΗ) ---
            full_str = (filename + " " + text[:500]).upper()
            
            if any(k in full_str for k in TRAINING_KEYWORDS):
                doc_type = "TRAINING"
            elif any(k in full_str for k in BOILER_KEYWORDS):
                doc_type = "BOILER"

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

def run_full_maintenance(root_folder_id):
    """Κύρια λειτουργία ταξινόμησης με Έξυπνους Φακέλους."""
    if not root_folder_id: return 0
    status_box = st.status("🧠 Έξυπνη Ταξινόμηση (Advanced Folders)...", expanded=True)
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
                
                # --- ΕΞΥΠΝΟΣ ΕΛΕΓΧΟΣ ΥΠΑΡΧΟΝΤΩΝ ---
                # Αν το αρχείο είναι ήδη ταξινομημένο, το προσπερνάμε, ΕΚΤΟΣ αν είναι "ύποπτο" για λέβητα/εκπαίδευση
                # ώστε να το διορθώσουμε τώρα.
                is_suspect = any(k in file_name.upper() for k in TRAINING_KEYWORDS + BOILER_KEYWORDS)
                
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
                
                metadata = analyze_document_deeply(extracted_text, file_name)
                brand = metadata["brand"]
                doc_type = metadata["type"]
                
                # --- ΕΠΙΛΟΓΗ ΦΑΚΕΛΟΥ (SMART FOLDERS) ---
                target_folder_name = brand
                
                if brand != "Unknown":
                    # Κανόνας 1: Θέρμανση / Αέριο (Για ΟΛΕΣ τις μάρκες)
                    if "BOILER" in doc_type or any(k in file_name.upper() for k in BOILER_KEYWORDS):
                        target_folder_name = f"{brand} (Gas-Heating)"
                    # Κανόνας 2: Εκπαίδευση (Για ΟΛΕΣ τις μάρκες)
                    elif "TRAINING" in doc_type or any(k in file_name.upper() for k in TRAINING_KEYWORDS):
                        target_folder_name = f"{brand} (Training)"
                
                # Δημιουργία Φακέλου αν δεν υπάρχει
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
                if s['id'] != review_folder_id and s['name'] not in folder_cache: folders_to_scan.append(s['id'])
        except: pass

    with open(INDEX_FILE, "w", encoding="utf-8") as f: json.dump(new_index_data, f, indent=4)
    status_box.update(label=f"🏁 Ολοκληρώθηκε! Επεξεργάστηκαν: {processed_count}", state="complete")
    return len(new_index_data)

# --- 3. EXCEL CLEANER (TAKTOPOIHMENO) ---
def get_stats_dataframe():
    """Δημιουργεί ένα καθαρό DataFrame για Export με Links."""
    try:
        with open(INDEX_FILE, "r", encoding="utf-8") as f: 
            data = json.load(f)
        
        if not data: return None
        
        df = pd.DataFrame(data)
        
        # Καθαρισμός Στηλών
        cols_to_keep = ['brand', 'model', 'meta_type', 'name', 'file_id']
        df = df[[c for c in cols_to_keep if c in df.columns]]
        
        # Δημιουργία Clickable Link
        if 'file_id' in df.columns:
            df['Link'] = df['file_id'].apply(lambda x: f'https://drive.google.com/open?id={x}')
        
        # Μετονομασία σε Ελληνικά
        df = df.rename(columns={
            'brand': 'Μάρκα',
            'model': 'Μοντέλο',
            'meta_type': 'Τύπος',
            'name': 'Όνομα Αρχείου',
            'file_id': 'Google ID'
        })
        
        # Ταξινόμηση
        if 'Μάρκα' in df.columns:
            df = df.sort_values(by=['Μάρκα', 'Μοντέλο'])
            
        return df

    except Exception as e:
        return None