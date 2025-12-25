# Αρχείο: smart_library.py
# ΕΚΔΟΣΗ: "PERSISTENT AI + SELF HEAL" (ΕΠΙΜΟΝΗ ΑΝΑΛΥΣΗ & ΑΥΤΟ-ΙΑΣΗ)

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
import pandas as pd  # <--- Προστέθηκε για τη βάση δεδομένων

# Ρυθμίσεις
UNSORTED_FOLDER_NAME = "!_UNSORTED_REVIEW"
INDEX_FILE = "drive_index.json"

# --- 1. ΝΕΑ ΛΕΙΤΟΥΡΓΙΑ: AUTO-FIX DATABASE (Αυτό έλειπε) ---
def auto_fix_database(json_file):
    """
    Ελέγχει αν το αρχείο βάσης (json) υπάρχει και αν έχει τις σωστές στήλες.
    Αν κάτι λείπει, το διορθώνει αυτόματα χωρίς να κρασάρει το πρόγραμμα.
    """
    # Αυτές είναι οι στήλες που ΑΠΑΙΤΟΥΜΕ να υπάρχουν
    required_columns = ['name', 'brand', 'model', 'meta_type', 'file_id', 'error_codes']
    
    # Περίπτωση 1: Δεν υπάρχει καθόλου το αρχείο
    if not os.path.exists(json_file):
        # print(f"⚠️ Το αρχείο {json_file} δεν βρέθηκε. Δημιουργείται νέο...") # Debug
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
            # print(f"🔧 Βρέθηκαν ελλείψεις στη βάση: {missing_cols}. Διορθώνονται...") # Debug
            
            # Προσθέτουμε τις κενές στήλες που λείπουν
            for col in missing_cols:
                df[col] = "Unknown" 
                
            # Αποθηκεύουμε τη διορθωμένη έκδοση
            df.to_json(json_file, orient='records', indent=4)
            
        return df
        
    except Exception as e:
        # print(f"❌ Υπήρξε πρόβλημα με το αρχείο: {e}")
        return pd.DataFrame(columns=required_columns)

# --- 2. ΥΠΑΡΧΟΥΣΕΣ ΛΕΙΤΟΥΡΓΙΕΣ (AI & DRIVE) ---

def find_best_model():
    """Επιλέγει αυτόματα το καλύτερο διαθέσιμο μοντέλο."""
    try:
        available = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        for pref in ['models/gemini-1.5-flash', 'models/gemini-1.5-pro', 'models/gemini-pro']:
            if pref in available: return pref
        return available[0]
    except: return 'gemini-pro'

def analyze_document_deeply(text, filename, attempt=1):
    """Επίμονη ανάλυση με πολλαπλές προσπάθειες."""
    api_key = st.secrets.get("GEMINI_KEY")
    if not api_key: return {"brand": "Unknown", "type": "GENERAL", "model": "-"}

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(find_best_model())
        
        # Διαφορετικό prompt ανάλογα με την προσπάθεια
        if attempt == 1:
            # 1η Προσπάθεια: Γενική ανάλυση κειμένου
            instruction = f"Analyze this HVAC manual text: '{text[:2500]}'. Filename: '{filename}'."
        else:
            # 2η Προσπάθεια: Εστίαση στο όνομα αρχείου και συσχετισμό μοντέλων
            instruction = f"CRITICAL SEARCH: The previous text analysis was unclear. Use your expert knowledge to identify the BRAND from this FILENAME: '{filename}'. Even if the brand name isn't there, infer it from the model code (e.g., MSZ -> Mitsubishi, VAM -> Daikin)."

        prompt = f"""
        {instruction}
        Return a JSON object: {{"brand": "Name", "model": "Code", "type": "SERVICE MANUAL/USER MANUAL/INSTALLATION/PARTS/GENERAL"}}
        If absolutely unknown, use "Unknown". 
        Brand must be a single word (e.g. Daikin, LG, Midea, Mitsubishi, Fujitsu, Gree, Toshiba, Carrier, Samsung).
        """
        
        response = model.generate_content(prompt)
        clean_text = response.text.replace("```json", "").replace("```", "").strip()
        json_match = re.search(r'\{.*\}', clean_text, re.DOTALL)
        
        if json_match:
            data = json.loads(json_match.group())
            brand = str(data.get("brand", "Unknown")).strip().title()
            
            # Αν αποτύχει η 1η φορά, δοκίμασε 2η με εστίαση στο filename
            if (brand == "Unknown" or brand == "-") and attempt == 1:
                return analyze_document_deeply(text, filename, attempt=2)
            
            return {
                "brand": brand if brand not in ["-", "", "None"] else "Unknown",
                "model": str(data.get("model", "-")).strip(),
                "type": str(data.get("type", "GENERAL")).upper()
            }
    except:
        if attempt == 1: return analyze_document_deeply(text, filename, attempt=2)
    
    return {"brand": "Unknown", "type": "GENERAL", "model": "-"}

def run_full_maintenance(root_folder_id):
    """Κύρια λειτουργία ταξινόμησης."""
    if not root_folder_id: return 0
    status_box = st.status("🧠 Έξυπνη Ταξινόμηση σε εξέλιξη (Persistent Mode)...", expanded=True)
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
                
                # Αν είναι ήδη ταξινομημένο, προσπέρασέ το
                if file_id in known_files and known_files[file_id].get("brand") != "Unknown":
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
                
                # ΕΔΩ ΓΙΝΕΤΑΙ Η ΔΙΠΛΗ/ΤΡΙΠΛΗ ΠΡΟΣΠΑΘΕΙΑ
                metadata = analyze_document_deeply(extracted_text, file_name)
                brand = metadata["brand"]
                
                # Επιλογή Φακέλου
                if brand not in folder_cache:
                    q = f"name = '{brand}' and '{root_folder_id}' in parents and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
                    res_b = service.files().list(q=q).execute()
                    if res_b.get('files'): folder_cache[brand] = res_b.get('files')[0]['id']
                    else:
                        meta = {'name': brand, 'mimeType': 'application/vnd.google-apps.folder', 'parents': [root_folder_id]}
                        folder_cache[brand] = service.files().create(body=meta, fields='id').execute().get('id')
                
                target_id = folder_cache.get(brand, review_folder_id)
                
                # Μετακίνηση αρχείου
                if target_id and target_id not in f.get('parents', []):
                    try:
                        service.files().update(fileId=file_id, addParents=target_id, removeParents=",".join(f.get('parents'))).execute()
                    except: pass
                
                new_index_data.append({
                    "id": file_id, "name": file_name, "brand": brand,
                    "model": metadata["model"], "meta_type": metadata["type"],
                    "status": "auto_verified" if brand != "Unknown" else "needs_review"
                })
                processed_count += 1
                time.sleep(0.3)
            
            subs = service.files().list(q=f"'{current_id}' in parents and mimeType = 'application/vnd.google-apps.folder' and trashed = false", fields="files(id, name)").execute()
            for s in subs.get('files', []):
                if s['id'] != review_folder_id: folders_to_scan.append(s['id'])
        except: pass

    with open(INDEX_FILE, "w", encoding="utf-8") as f: json.dump(new_index_data, f, indent=4)
    status_box.update(label=f"🏁 Η συντήρηση ολοκληρώθηκε! Επεξεργάστηκαν: {processed_count}", state="complete")
    return len(new_index_data)

def get_stats_dataframe():
    try:
        # Χρησιμοποιούμε το pd που κάναμε import στην αρχή
        with open(INDEX_FILE, "r", encoding="utf-8") as f:
            return pd.DataFrame(json.load(f))
    except: return None