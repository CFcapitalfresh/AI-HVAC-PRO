# Αρχείο: smart_library.py
# ΡΟΛΟΣ: Σάρωση και Ταξινόμηση (Indexing)
# Συνεργάζεται με το remote_db για μόνιμη αποθήκευση.

import os
import json
import pandas as pd
from googleapiclient.discovery import build
from google.oauth2 import service_account
import streamlit as st
import remote_db  # <--- Η ΝΕΑ ΜΑΣ ΠΡΟΣΘΗΚΗ

# Ρυθμίσεις
SCOPES = ['https://www.googleapis.com/auth/drive']

def get_drive_service():
    """Σύνδεση με Drive API."""
    if "gcp_service_account" in st.secrets:
        creds_dict = dict(st.secrets["gcp_service_account"])
        creds = service_account.Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
        return build('drive', 'v3', credentials=creds)
    return None

def determine_meta_type(filename):
    """Μαντεύει τον τύπο του αρχείου από το όνομα."""
    name = filename.upper()
    if "SERVICE" in name: return "SERVICE MANUAL"
    if "USER" in name: return "USER MANUAL"
    if "INSTALL" in name: return "INSTALLATION MANUAL"
    if "SPARE" in name or "PARTS" in name: return "SPARE PARTS"
    if "ERROR" in name or "CODE" in name: return "ERROR CODES"
    if "TRAINING" in name: return "TRAINING"
    if "BOILER" in name: return "BOILER DATA"
    return "UNKNOWN"

def run_full_maintenance(folder_id):
    """
    Η κύρια λειτουργία: Σαρώνει το Drive, φτιάχνει τη λίστα 
    και τη στέλνει στο remote_db για αποθήκευση.
    """
    service = get_drive_service()
    if not service: return 0
    
    all_files = []
    page_token = None

    try:
        while True:
            # Ψάχνουμε ΜΟΝΟ PDF μέσα στον φάκελο
            query = f"'{folder_id}' in parents and mimeType='application/pdf' and trashed=false"
            results = service.files().list(
                q=query,
                pageSize=1000,
                fields="nextPageToken, files(id, name, createdTime, webViewLink)",
                pageToken=page_token
            ).execute()
            
            items = results.get('files', [])
            
            for item in items:
                # Επεξεργασία ονόματος για Brand/Model (απλοϊκή λογική)
                parts = item['name'].replace("-", " ").replace("_", " ").split()
                brand = parts[0] if parts else "Unknown"
                model = parts[1] if len(parts) > 1 else "General"
                
                meta = {
                    "file_id": item['id'],
                    "name": item['name'],
                    "link": item['webViewLink'],
                    "brand": brand,
                    "model": model,
                    "meta_type": determine_meta_type(item['name']),
                    "last_indexed": "NOW"
                }
                all_files.append(meta)

            page_token = results.get('nextPageToken')
            if not page_token: break
        
        # ΕΔΩ ΕΙΝΑΙ Η ΑΛΛΑΓΗ: Σώζουμε στο Cloud, όχι τοπικά
        if all_files:
            remote_db.save_db_to_drive(all_files, folder_id)
            
            # Ενημερώνουμε και το τοπικό session state για να το δει αμέσως ο χρήστης
            st.session_state['library_cache'] = all_files
            
        return len(all_files)

    except Exception as e:
        print(f"Maintenance Error: {e}")
        return 0

def get_stats_dataframe():
    """Επιστρέφει τα δεδομένα ως Pandas DataFrame για προβολή."""
    # Πρώτα κοιτάμε τη μνήμη (Session State)
    if 'library_cache' in st.session_state and st.session_state['library_cache']:
        return pd.DataFrame(st.session_state['library_cache'])
    
    # Αν είναι άδεια, επιστρέφουμε κενό
    return pd.DataFrame()