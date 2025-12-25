# Αρχείο: smart_library.py
# ΕΚΔΟΣΗ: 1.5.0 - MASTER ANALYTICAL VERSION
# ΠΕΡΙΛΑΜΒΑΝΕΙ: Adaptive Scan, Smart Categories, Excel Links, Persistent AI

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

# --- ΓΕΝΙΚΕΣ ΡΥΘΜΙΣΕΙΣ ---
UNSORTED_FOLDER_NAME = "!_UNSORTED_REVIEW"
INDEX_FILE = "drive_index.json"
INITIAL_PAGES = 5      # Πόσες σελίδες διαβάζει στην αρχή
DEEP_SCAN_PAGES = 50   # Πόσες σελίδες διαβάζει αν δυσκολευτεί

# --- ΛΙΣΤΕΣ ΛΕΞΕΩΝ-ΚΛΕΙΔΙΩΝ (KEYWORDS) ---
BOILER_KEYWORDS = [
    "BOILER", "GAS", "ΛΕΒΗΤΑΣ", "ΦΥΣΙΚΟ ΑΕΡΙΟ", "CONDENSING", "HEATING", 
    "GENUS", "CLAS", "CARES", "ALTEAS", "FAST EVO", "NIMBUS", "LYDOS", 
    "BAXI", "BUDERUS", "VIESSMANN", "IMMERGAS", "VAILLANT", "CHAFFOTEAUX", "RIELLO", "SENSYS"
]

TRAINING_KEYWORDS = [
    "TRAINING", "SEMINAR", "ACADEMY", "COURSE", "ΕΚΠΑΙΔΕΥΣΗ", "ΣΕΜΙΝΑΡΙΟ", 
    "PRESENTATION", "ΠΑΡΟΥΣΙΑΣΗ", "WEBINAR", "WORKSHOP", "MANUAL TRAINING"
]

# --- 1. ΛΕΙΤΟΥΡΓΙΑ ΑΥΤΟ-ΔΙΟΡΘΩΣΗΣ ΒΑΣΗΣ (SELF-HEAL) ---
def auto_fix_database(json_file):
    """Εξασφαλίζει ότι η βάση δεδομένων έχει όλες τις απαραίτητες στήλες."""
    required_columns = ['name', 'brand', 'model', 'meta_type', 'file_id', 'error_codes']
    
    if not os.path.exists(json_file):
        df = pd.DataFrame(columns=required_columns)
        try:
            df.to_json(json_file, orient='records', indent=4)
        except Exception as e:
            st.error(f"Σφάλμα δημιουργίας βάσης: {e}")
        return df

    try:
        df = pd.read_json(json_file)
        missing_cols = [col for col in required_columns if col not in df.columns]
        if missing_cols:
            for col in missing_cols:
                df[col] = "Unknown" 
            df.to_json(json_file, orient='records', indent=4)
        return df
    except Exception as e:
        st.error(f"Σφάλμα επιδιόρθωσης βάσης: {e}")
        return pd.DataFrame(columns=required_columns)

# --- 2. ΛΕΙΤΟΥΡΓΙΕΣ ΑΝΑΓΝΩΣΗΣ ΚΑΙ AI ---

def find_best_model():
    """Βρίσκει το καλύτερο διαθέσιμο μοντέλο Gemini."""
    try:
        available = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        for pref in ['models/gemini-1.5-flash', 'models/gemini-1.5-pro', 'models/gemini-pro']:
            if pref in available:
                return pref
        return available[0]
    except Exception:
        return 'gemini-pro'

def extract_text_from_pdf_bytes(fh, max_pages):
    """Εξάγει κείμενο από συγκεκριμένο αριθμό σελίδων ενός PDF."""
    text = ""
    try:
        fh.seek(0)
        reader = pypdf.PdfReader(fh)
        total_pages = len(reader.pages)
        # Διαβάζουμε μέχρι το όριο που θέλουμε
        limit = min(max_pages, total_pages)
        for i in range(limit):
            page_text = reader.pages[i].extract_text()
            if page_text:
                text += page_text + "\n"
    except Exception as e:
        print(f"Σφάλμα ανάγνωσης PDF: {e}")
    return text

def analyze_document_deeply(text, filename, attempt=1):
    """Στέλνει το κείμενο στο AI για αναγνώριση μάρκας, μοντέλου και τύπου."""
    api_key = st.secrets.get("GEMINI_KEY")
    if not api_key:
        return {"brand": "Unknown", "type": "GENERAL", "model": "-"}

    try:
        genai.configure(api_key=api_key)
        model_name = find_best_model()
        model = genai.GenerativeModel(model_name)
        
        # Προσαρμογή οδηγιών ανάλογα με την προσπάθεια (Adaptive)
        if attempt == 1:
            instruction = f"Analyze this HVAC manual text: '{text[:5000]}'. Filename: '{filename}'."
        else:
            instruction = f"CRITICAL DEEP ANALYSIS: Previous attempt failed. Search deep into the text and filename: '{filename}' to find the manufacturer and machine type."

        prompt = f"""
        {instruction}
        Return a JSON object: {{"brand": "Name", "model": "Code", "type": "SERVICE/USER/INSTALLATION/TRAINING/BOILER"}}
        
        IMPORTANT RULES:
        1. Brand must be a single word (e.g. Daikin, Ariston, LG).
        2. If it's a Seminar, Academy or Presentation, type = 'TRAINING'.
        3. If it's a Gas Boiler or Heating Unit, type = 'BOILER'.
        4. If you really can't find the brand, return "Unknown".
        """
        
        response = model.generate_content(prompt)
        clean_text = response.text.replace("```json", "").replace("```", "").strip()
        json_match = re.search(r'\{.*\}', clean_text, re.DOTALL)
        
        if json_match:
            data = json.loads(json_match.group())
            brand = str(data.get("brand", "Unknown")).strip().title()
            doc_type = str(data.get("type", "GENERAL")).upper()
            
            # --- ΕΠΙΒΕΒΑΙΩΣΗ ΜΕ PYTHON KEYWORDS ---
            full_content = (filename + " " + text[:1000]).upper()
            if any(k in full_content for k in TRAINING_KEYWORDS):
                doc_type = "TRAINING"
            elif any(k in full_content for k in BOILER_KEYWORDS):
                doc_type = "BOILER"

            # Αν στην πρώτη προσπάθεια δεν βρήκαμε μάρκα, επιστρέφουμε Unknown για να προκαλέσουμε Deep Scan
            if (brand == "Unknown" or brand == "-") and attempt == 1:
                return {"brand": "Unknown", "type": doc_type, "model": "-"}
            
            return {
                "brand": brand if brand not in ["-", "", "None"] else "Unknown",
                "model": str(data.get("model", "-")).strip(),
                "type": doc_type
            }
    except Exception as e:
        print(f"Σφάλμα AI (Attempt {attempt}): {e}")
    
    return {"brand": "Unknown", "type": "GENERAL", "model": "-"}

# --- 3. ΚΥΡΙΑ ΛΕΙΤΟΥΡΓΙΑ ΣΥΝΤΗΡΗΣΗΣ (CRAWLER) ---

def run_full_maintenance(root_folder_id):
    """Ο 'εγκέφαλος' που ταξινομεί τα αρχεία στο Google Drive."""
    if not root_folder_id:
        return 0
    
    status_box = st.status("🚀 Έναρξη Έξυπνης Ταξινόμησης (Master Mode)...", expanded=True)
    service = drive.get_service()
    if not service:
        status_box.update(label="❌ Σφάλμα σύνδεσης με Google Drive", state="error")
        return 0

    # 1. Εξασφάλιση Φακέλου για Χειροκίνητο Έλεγχο
    review_folder_id = None
    try:
        q = f"name = '{UNSORTED_FOLDER_NAME}' and '{root_folder_id}' in parents and trashed = false"
        res = service.files().list(q=q).execute()
        if res.get('files'):
            review_folder_id = res.get('files')[0]['id']
        else:
            meta = {'name': UNSORTED_FOLDER_NAME, 'mimeType': 'application/vnd.google-apps.folder', 'parents': [root_folder_id]}
            review_folder_id = service.files().create(body=meta, fields='id').execute().get('id')
    except Exception as e:
        status_box.write(f"⚠️ Πρόβλημα με τον φάκελο Review: {e}")

    # 2. Φόρτωση Υπάρχουσας Βάσης
    old_index = []
    try:
        with open(INDEX_FILE, "r", encoding="utf-8") as f:
            old_index = json.load(f)
    except Exception:
        pass
    
    known_files = {x['id']: x for x in old_index}
    new_index_data = []
    folders_to_scan = [root_folder_id]
    folder_cache = {"Unknown": review_folder_id}
    processed_count = 0
    
    # 3. Ξεκινάει το Σκανάρισμα
    while folders_to_scan:
        current_folder_id = folders_to_scan.pop(0)
        
        # Μην σκανάρεις τον φάκελο review
        if current_folder_id == review_folder_id:
            continue

        try:
            query = f"'{current_folder_id}' in parents and trashed = false"
            results = service.files().list(q=query, fields="files(id, name, mimeType, parents)").execute()
            
            for f in results.get('files', []):
                file_id = f['id']
                file_name = f['name']
                mime_type = f['mimeType']

                # Αν είναι φάκελος, τον προσθέτουμε στη λίστα για σκανάρισμα αργότερα
                if mime_type == 'application/vnd.google-apps.folder':
                    if file_id != review_folder_id:
                        folders_to_scan.append(file_id)
                    continue

                # Αν είναι PDF, το αναλύουμε
                if mime_type == 'application/pdf':
                    # Εξαίρεση: Αν είναι ήδη γνωστό και σωστό, το προσπερνάμε (εκτός αν είναι "ύποπτο")
                    is_special = any(k in file_name.upper() for k in TRAINING_KEYWORDS + BOILER_KEYWORDS)
                    if file_id in known_files and known_files[file_id].get("brand") != "Unknown" and not is_special:
                        new_index_data.append(known_files[file_id])
                        continue

                    status_box.write(f"🧐 Ανάλυση αρχείου: **{file_name}**")
                    
                    # --- ΒΗΜΑ Α: Γρήγορη Σάρωση (5 σελίδες) ---
                    extracted_text = ""
                    fh = io.BytesIO()
                    try:
                        request = service.files().get_media(fileId=file_id)
                        downloader = MediaIoBaseDownload(fh, request)
                        done = False
                        while not done:
                            _, done = downloader.next_chunk()
                        extracted_text = extract_text_from_pdf_bytes(fh, INITIAL_PAGES)
                    except Exception as e:
                        status_box.write(f"❌ Σφάλμα λήψης {file_name}: {e}")

                    metadata = analyze_document_deeply(extracted_text, file_name, attempt=1)
                    
                    # --- ΒΗΜΑ Β: Βαθιά Σάρωση (Αν η πρώτη απέτυχε) ---
                    if metadata["brand"] == "Unknown":
                        status_box.write(f"🔍 Deep Scan σε εξέλιξη για το {file_name}...")
                        extracted_text = extract_text_from_pdf_bytes(fh, DEEP_SCAN_PAGES)
                        metadata = analyze_document_deeply(extracted_text, file_name, attempt=2)

                    brand = metadata["brand"]
                    doc_type = metadata["type"]
                    
                    # 4. Επιλογή Σωστού Φακέλου (Heating / Training / Brand)
                    target_folder_name = brand
                    if brand != "Unknown":
                        if "BOILER" in doc_type or any(k in file_name.upper() for k in BOILER_KEYWORDS):
                            target_folder_name = f"{brand} (Gas-Heating)"
                        elif "TRAINING" in doc_type or any(k in file_name.upper() for k in TRAINING_KEYWORDS):
                            target_folder_name = f"{brand} (Training)"

                    if target_folder_name not in folder_cache:
                        q_fold = f"name = '{target_folder_name}' and '{root_folder_id}' in parents and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
                        res_fold = service.files().list(q=q_fold).execute()
                        if res_fold.get('files'):
                            folder_cache[target_folder_name] = res_fold.get('files')[0]['id']
                        else:
                            meta_fold = {'name': target_folder_name, 'mimeType': 'application/vnd.google-apps.folder', 'parents': [root_folder_id]}
                            folder_cache[target_folder_name] = service.files().create(body=meta_fold, fields='id').execute().get('id')
                    
                    target_id = folder_cache.get(target_folder_name, review_folder_id)

                    # 5. Μετακίνηση Αρχείου στο Drive
                    if target_id and target_id not in f.get('parents', []):
                        try:
                            service.files().update(
                                fileId=file_id, 
                                addParents=target_id, 
                                removeParents=",".join(f.get('parents', []))
                            ).execute()
                        except Exception:
                            pass

                    # 6. Προσθήκη στη νέα βάση
                    new_index_data.append({
                        "id": file_id,
                        "name": file_name,
                        "brand": brand,
                        "model": metadata["model"],
                        "meta_type": doc_type,
                        "file_id": file_id, # Για το Link
                        "status": "auto_verified" if brand != "Unknown" else "needs_review"
                    })
                    processed_count += 1
                    time.sleep(0.3)

        except Exception as e:
            status_box.write(f"⚠️ Σφάλμα στον φάκελο {current_folder_id}: {e}")

    # 7. Αποθήκευση της νέας βάσης στο drive_index.json
    try:
        with open(INDEX_FILE, "w", encoding="utf-8") as f:
            json.dump(new_index_data, f, indent=4)
    except Exception as e:
        st.error(f"Σφάλμα αποθήκευσης βάσης: {e}")

    status_box.update(label=f"🏁 Η συντήρηση ολοκληρώθηκε! Επεξεργάστηκαν {processed_count} νέα αρχεία.", state="complete")
    return len(new_index_data)

# --- 4. EXCEL EXPORT (ΚΑΘΑΡΟ ΚΑΙ ΜΕ LINKS) ---

def get_stats_dataframe():
    """Επιστρέφει το DataFrame για το Excel, συμπεριλαμβανομένου του Link."""
    try:
        if not os.path.exists(INDEX_FILE):
            return None
            
        with open(INDEX_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        if not data:
            return None
        
        df = pd.DataFrame(data)
        
        # Προσθήκη Clickable Link για το Google Drive
        if 'file_id' in df.columns:
            df['Link'] = df['file_id'].apply(lambda x: f'https://drive.google.com/open?id={x}')
            
        # Επιστρέφουμε το DataFrame (το main.py θα χρησιμοποιήσει το meta_type κλπ)
        return df
    except Exception:
        return None