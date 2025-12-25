# Αρχείο: organizer.py (SAFE MODE - NO LOOPS)
import streamlit as st
import google.generativeai as genai
from googleapiclient.http import MediaIoBaseDownload
import io
import time
import drive

def analyze_file_category(text, filename):
    try:
        api_key = st.secrets.get("GEMINI_KEY")
        if not api_key: return "Unsorted"

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"""
        Identify the MANUFACTURER (Brand) from this file header.
        File: {filename}
        Text: {text[:500]}
        
        Rules:
        1. Return ONLY the Brand Name (e.g. "Daikin", "Toyotomi").
        2. If generic, return "Unsorted".
        3. Output ONE word.
        """
        response = model.generate_content(prompt)
        brand = response.text.strip().replace("\n", "").replace(".", "").replace('"', "").title()
        if len(brand) > 15: return "Unsorted"
        return brand
    except: return "Unsorted"

def create_folder_if_not_exists(service, folder_name, parent_id):
    try:
        query = f"name = '{folder_name}' and '{parent_id}' in parents and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
        results = service.files().list(q=query, fields="files(id)").execute()
        files = results.get('files', [])
        if files: return files[0]['id']
        
        file_metadata = {'name': folder_name, 'mimeType': 'application/vnd.google-apps.folder', 'parents': [parent_id]}
        folder = service.files().create(body=file_metadata, fields='id').execute()
        return folder.get('id')
    except: return None

def move_file_to_folder(service, file_id, new_parent_id):
    try:
        file = service.files().get(fileId=file_id, fields='parents').execute()
        previous_parents = ",".join(file.get('parents'))
        service.files().update(fileId=file_id, addParents=new_parent_id, removeParents=previous_parents).execute()
        return True
    except: return False

def organize_drive_library(root_folder_id):
    if not root_folder_id:
        st.error("❌ Λείπει το ID φακέλου.")
        return

    status_box = st.status("🛡️ Safe Organizer: Ξεκινάει...", expanded=True)
    service = drive.get_service()
    if not service:
        status_box.error("❌ Πρόβλημα σύνδεσης.")
        return
    
    # Λίστα αναζήτησης
    folders_to_search = [root_folder_id]
    
    # 🛑 BLACKLIST: Εδώ βάζουμε τους φακέλους Μάρκας για να ΜΗΝ μπούμε μέσα τους
    do_not_scan_ids = set() 
    
    # Cache για να μην ψάχνουμε συνέχεια τα ID των μαρκών
    brand_folders_cache = {} 

    processed_count = 0
    
    while folders_to_search:
        current_id = folders_to_search.pop(0)
        
        # Αν αυτός ο φάκελος είναι στη μαύρη λίστα, τον προσπερνάμε!
        if current_id in do_not_scan_ids:
            continue

        status_box.write(f"📂 Έλεγχος φακέλου...")
        
        try:
            # 1. Βρες PDF
            results = service.files().list(
                q=f"'{current_id}' in parents and mimeType = 'application/pdf' and trashed = false",
                fields="files(id, name, parents)"
            ).execute()
            
            for f in results.get('files', []):
                # Γρήγορος έλεγχος: Μήπως είναι ήδη τακτοποιημένο;
                # Αν το όνομα του γονικού φακέλου είναι ήδη γνωστή μάρκα, το αγνοούμε.
                # (Για απλότητα, προχωράμε στην ανάλυση)
                
                request = service.files().get_media(fileId=f['id'])
                fh = io.BytesIO()
                downloader = MediaIoBaseDownload(fh, request); downloader.next_chunk()
                fh.seek(0)
                
                # Προσπάθεια ανάγνωσης κειμένου
                text_content = f['name']
                try:
                    import pypdf
                    reader = pypdf.PdfReader(fh)
                    if len(reader.pages)>0: text_content = reader.pages[0].extract_text()
                except: pass
                
                brand = analyze_file_category(text_content, f['name'])
                
                if brand != "Unsorted":
                    # Δημιουργία/Εύρεση φακέλου Μάρκας (ΠΑΝΤΑ ΣΤΟΝ ΚΕΝΤΡΙΚΟ ΦΑΚΕΛΟ)
                    if brand not in brand_folders_cache:
                        b_id = create_folder_if_not_exists(service, brand, root_folder_id)
                        brand_folders_cache[brand] = b_id
                        # 🛑 ΣΗΜΑΝΤΙΚΟ: Βάζουμε τον νέο φάκελο στη μαύρη λίστα για να μην ψάξουμε μέσα του!
                        do_not_scan_ids.add(b_id) 
                    
                    target_id = brand_folders_cache[brand]
                    
                    # Μετακίνηση μόνο αν δεν είναι ήδη εκεί
                    if target_id and target_id not in f['parents']:
                        move_file_to_folder(service, f['id'], target_id)
                        status_box.write(f"✅ {f['name']} -> {brand}")
                        processed_count += 1
                        time.sleep(0.5)

            # 2. Βρες Υποφακέλους (για να συνεχίσει το ψάξιμο)
            subfolders = service.files().list(
                q=f"'{current_id}' in parents and mimeType = 'application/vnd.google-apps.folder' and trashed = false",
                fields="files(id, name)"
            ).execute()
            
            for sub in subfolders.get('files', []):
                # Προσθέτουμε για ψάξιμο ΜΟΝΟ αν δεν είναι στη μαύρη λίστα
                if sub['id'] not in do_not_scan_ids and sub['name'] not in brand_folders_cache:
                    folders_to_search.append(sub['id'])

        except Exception as e:
            pass

    status_box.update(label=f"🏁 Τέλος! Τακτοποιήθηκαν {processed_count} αρχεία.", state="complete")