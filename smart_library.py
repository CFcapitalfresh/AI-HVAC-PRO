# Αρχείο: smart_library.py
# ΑΥΤΟ ΤΟ ΑΡΧΕΙΟ ΚΑΝΕΙ ΤΙΣ "ΒΑΡΙΕΣ" ΕΡΓΑΣΙΕΣ ΣΥΝΤΗΡΗΣΗΣ
import streamlit as st
import google.generativeai as genai
from googleapiclient.http import MediaIoBaseDownload
import io
import time
import json
import pypdf
import drive  # Χρησιμοποιούμε το drive.py ΜΟΝΟ για τη σύνδεση

# Ρυθμίσεις
UNSORTED_FOLDER_NAME = "!_UNSORTED_REVIEW"
INDEX_FILE = "drive_index.json"

# --- 1. Η ΝΟΗΜΟΣΥΝΗ (AI BRAIN) ---
def analyze_document_deeply(text, filename):
    """Ρωτάει το Gemini για Μάρκα, Μοντέλο και Τύπο."""
    api_key = st.secrets.get("GEMINI_KEY")
    if not api_key: return {"brand": "Unknown", "type": "General", "model": "-"}

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = f"""
    You are an HVAC Technical Expert. Analyze this manual header.
    
    File Name: "{filename}"
    Content Preview: "{text[:2500]}"
    
    TASK: Return a valid JSON object with these 3 fields:
    1. "brand": The Manufacturer (e.g. Daikin, Midea). If generic part, use "Parts".
    2. "model": The Series/Model (e.g. Altherma 3, Amber). If not found, use "-".
    3. "type": One of [SERVICE MANUAL, USER MANUAL, ERROR CODES, INSTALLATION, PARTS LIST, GENERAL].
    
    EXAMPLE JSON OUTPUT:
    {{"brand": "Daikin", "model": "Altherma 3", "type": "SERVICE MANUAL"}}
    """
    
    try:
        response = model.generate_content(prompt)
        # Καθαρισμός για να πάρουμε μόνο το JSON
        clean_text = response.text.replace("```json", "").replace("```", "").strip()
        # Μερικές φορές το AI βάζει κείμενο πριν/μετά, ψάχνουμε τις αγκύλες
        import re
        json_match = re.search(r'\{.*\}', clean_text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        else:
            return {"brand": "Unknown", "type": "General", "model": "-"}
    except:
        return {"brand": "Unknown", "type": "General", "model": "-"}

# --- 2. H ΔΡΑΣΗ (PROCESS) ---
def run_full_maintenance(root_folder_id):
    """Η Κύρια Συνάρτηση που καλείται από το κουμπί."""
    
    if not root_folder_id: st.error("❌ Λείπει το ID."); return

    # Δημιουργία περιοχής Status
    status_box = st.status("🧠 Έξυπνη Συντήρηση σε εξέλιξη...", expanded=True)
    
    service = drive.get_service() # Παίρνουμε τη σύνδεση από το παλιό καλό drive.py
    if not service: status_box.error("❌ Σφάλμα σύνδεσης."); return

    # Δημιουργία φακέλου 'Unsorted' αν δεν υπάρχει
    try:
        q = f"name = '{UNSORTED_FOLDER_NAME}' and '{root_folder_id}' in parents and trashed = false"
        res = service.files().list(q=q).execute()
        if not res.get('files'):
            service.files().create(body={'name': UNSORTED_FOLDER_NAME, 'mimeType': 'application/vnd.google-apps.folder', 'parents': [root_folder_id]}).execute()
    except: pass

    # Φόρτωση παλιού ευρετηρίου για να μην ξανα-αναλύουμε τα ίδια
    old_index = []
    try: old_index = json.load(open(INDEX_FILE))
    except: pass
    known_files = {x['id']: x for x in old_index}
    
    new_index_data = []
    folders_to_scan = [root_folder_id]
    folder_cache = {} # Cache για να θυμόμαστε τα ID των μαρκών (Daikin -> 1234abcd)
    
    processed_count = 0
    
    # --- ΚΥΡΙΟΣ ΒΡΟΧΟΣ (LOOP) ---
    while folders_to_scan:
        current_id = folders_to_scan.pop(0)
        
        # Έλεγχος αν είναι ο φάκελος Unsorted (τον αγνοούμε)
        try:
            folder_info = service.files().get(fileId=current_id).execute()
            if folder_info['name'] == UNSORTED_FOLDER_NAME: continue
        except: pass

        try:
            # 1. Βρες όλα τα PDF
            results = service.files().list(
                q=f"'{current_id}' in parents and mimeType = 'application/pdf' and trashed = false",
                fields="files(id, name, parents)"
            ).execute()
            
            for f in results.get('files', []):
                file_id = f['id']
                file_name = f['name']
                
                # Α. ΕΛΕΓΧΟΣ: Το ξέρουμε ήδη;
                if file_id in known_files and known_files[file_id].get("meta_type"):
                    # Αν υπάρχει και έχει αναλυθεί πλήρως, το κρατάμε και προχωράμε
                    new_index_data.append(known_files[file_id])
                    # status_box.write(f"⏩ Γνωστό: {file_name}") # Προαιρετικό για ταχύτητα
                    continue
                
                # Β. ΑΝΑΛΥΣΗ: Είναι νέο ή αταξινόμητο
                status_box.write(f"🧐 Ανάλυση: {file_name}...")
                
                # Κατέβασμα κειμένου (5 σελίδες)
                extracted_text = ""
                try:
                    request = service.files().get_media(fileId=file_id)
                    fh = io.BytesIO()
                    downloader = MediaIoBaseDownload(fh, request); downloader.next_chunk()
                    fh.seek(0)
                    reader = pypdf.PdfReader(fh)
                    for i in range(min(5, len(reader.pages))):
                        extracted_text += reader.pages[i].extract_text() + "\n"
                except: pass
                
                # Ερώτηση στο AI
                metadata = analyze_document_deeply(extracted_text, file_name)
                brand = metadata.get("brand", "Unknown")
                
                # Γ. ΤΑΚΤΟΠΟΙΗΣΗ (MOVE)
                target_folder_id = None
                
                if brand != "Unknown":
                    # Βρες ή φτιάξε τον φάκελο μάρκας
                    if brand not in folder_cache:
                        # Ψάχνουμε αν υπάρχει
                        q_brand = f"name = '{brand}' and '{root_folder_id}' in parents and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
                        res_b = service.files().list(q=q_brand).execute()
                        if res_b.get('files'):
                            folder_cache[brand] = res_b.get('files')[0]['id']
                        else:
                            # Δημιουργία
                            meta = {'name': brand, 'mimeType': 'application/vnd.google-apps.folder', 'parents': [root_folder_id]}
                            new_f = service.files().create(body=meta, fields='id').execute()
                            folder_cache[brand] = new_f.get('id')
                    
                    target_folder_id = folder_cache[brand]
                
                # Μετακίνηση (Αν βρήκαμε φάκελο και το αρχείο δεν είναι ήδη εκεί)
                if target_folder_id and target_folder_id not in f['parents']:
                    try:
                        prev_parents = ",".join(f.get('parents'))
                        service.files().update(fileId=file_id, addParents=target_folder_id, removeParents=prev_parents).execute()
                        status_box.write(f"✅ Μετακίνηση: {brand}")
                    except: pass
                
                # Δ. ΕΓΓΡΑΦΗ ΣΤΟ ΕΥΡΕΤΗΡΙΟ
                entry = {
                    "id": file_id,
                    "name": file_name,
                    "brand": brand,
                    "model": metadata.get("model", "-"),
                    "meta_type": metadata.get("type", "General"),
                    "search_terms": f"{brand} {metadata.get('model')} {metadata.get('type')} {file_name}".lower()
                }
                new_index_data.append(entry)
                processed_count += 1
                time.sleep(1) # Ανάσα για το API
            
            # 2. Ψάξε στους Υποφακέλους
            subs = service.files().list(
                q=f"'{current_id}' in parents and mimeType = 'application/vnd.google-apps.folder' and trashed = false",
                fields="files(id, name)"
            ).execute()
            
            for s in subs.get('files', []):
                # Να μην ξαναμπούμε στους φακέλους που μόλις φτιάξαμε ή στο Unsorted
                if s['name'] != UNSORTED_FOLDER_NAME and s['name'] not in folder_cache:
                    folders_to_scan.append(s['id'])
                    
        except Exception as e:
            # status_box.warning(f"Error σε φάκελο: {e}")
            pass

    # Αποθήκευση στο τέλος
    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(new_index_data, f, indent=4)
        
    status_box.update(label=f"🏁 Τέλος! Επεξεργάστηκαν {processed_count} νέα αρχεία. Σύνολο: {len(new_index_data)}", state="complete")
    return len(new_index_data)

# --- 3. ΤΑ ΣΤΑΤΙΣΤΙΚΑ ---
def get_stats_dataframe():
    try:
        with open(INDEX_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        import pandas as pd
        return pd.DataFrame(data)
    except:
        return None