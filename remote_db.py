# Αρχείο: remote_db.py
# ΕΚΔΟΣΗ: 6.0.0 (TITANIUM ARMORED)
# ΡΟΛΟΣ: Διαχείριση Μόνιμης Μνήμης με Στρατιωτικού Τύπου Ασφάλεια και Ανθεκτικότητα

import json
import os
import time
import io
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime

import streamlit as st
from googleapiclient.discovery import build, Resource
from google.oauth2 import service_account
from googleapiclient.http import MediaIoBaseUpload, MediaIoBaseDownload
from googleapiclient.errors import HttpError

# --- ΡΥΘΜΙΣΕΙΣ LOGGING ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger("RemoteDB_Manager")

# --- ΣΤΑΘΕΡΕΣ ---
DB_FILENAME = "mastro_nek_library_db.json"
BACKUP_PREFIX = "backup_"
MAX_RETRIES = 3
RETRY_DELAY = 2  # Δευτερόλεπτα

class DatabaseManager:
    """
    Κλάση διαχείρισης της απομακρυσμένης βάσης δεδομένων.
    Περιλαμβάνει μηχανισμούς επαναπροσπάθειας (retry), logging και validation.
    """

    def __init__(self):
        self.service: Optional[Resource] = None
        self._initialize_service()

    def _initialize_service(self) -> None:
        """Εσωτερική μέθοδος για την ασφαλή εκκίνηση του Drive Service."""
        try:
            if "gcp_service_account" in st.secrets:
                creds_dict = dict(st.secrets["gcp_service_account"])
                creds = service_account.Credentials.from_service_account_info(
                    creds_dict,
                    scopes=["https://www.googleapis.com/auth/drive"]
                )
                self.service = build("drive", "v3", credentials=creds)
                logger.info("✅ Google Drive Service initialized successfully.")
            else:
                logger.warning("⚠️ No Service Account secrets found.")
        except Exception as e:
            logger.critical(f"❌ CRITICAL: Failed to initialize Drive Service: {str(e)}")
            st.error(f"System Error: {e}")

    def _validate_data_structure(self, data: List[Dict[str, Any]]) -> bool:
        """
        Ελέγχει αν η δομή των δεδομένων είναι σωστή πριν την αποθήκευση.
        Αποτρέπει την καταστροφή της βάσης από "σκουπίδια".
        """
        if not isinstance(data, list):
            logger.error("❌ Validation Failed: Data is not a list.")
            return False
        
        # Έλεγχος των πρώτων 5 στοιχείων για βασικά κλειδιά
        required_keys = ["name", "file_id"]
        for index, item in enumerate(data[:5]):
            if not isinstance(item, dict):
                logger.error(f"❌ Validation Failed: Item at index {index} is not a dict.")
                return False
            for key in required_keys:
                if key not in item:
                    logger.error(f"❌ Validation Failed: Missing key '{key}' in item {index}.")
                    return False
        
        logger.info("✅ Data structure validation passed.")
        return True

    def save_db_to_drive(self, data: List[Dict[str, Any]], folder_id: str) -> bool:
        """
        Αποθηκεύει τη βάση στο Drive με μηχανισμό Retry και δημιουργία Backup.
        """
        if not self.service:
            logger.error("❌ Cannot save: Service not initialized.")
            return False

        if not self._validate_data_structure(data):
            st.error("Data Integrity Error: Aborting save.")
            return False

        # Μετατροπή σε JSON Stream
        try:
            json_str = json.dumps(data, indent=2, ensure_ascii=False)
            fh = io.BytesIO(json_str.encode('utf-8'))
            media = MediaIoBaseUpload(fh, mimetype='application/json', resumable=True)
        except TypeError as e:
            logger.error(f"❌ JSON Serialization Error: {e}")
            return False

        # Λογική Retry
        for attempt in range(MAX_RETRIES):
            try:
                # 1. Αναζήτηση υπάρχοντος αρχείου
                query = f"name = '{DB_FILENAME}' and '{folder_id}' in parents and trashed = false"
                results = self.service.files().list(q=query, fields="files(id)").execute()
                files = results.get("files", [])

                if files:
                    file_id = files[0]['id']
                    # Πριν το overwrite, προαιρετικά θα μπορούσαμε να κάνουμε rename το παλιό σε backup
                    # Για τώρα κάνουμε update
                    self.service.files().update(
                        fileId=file_id,
                        media_body=media
                    ).execute()
                    logger.info(f"✅ Database Updated (Attempt {attempt+1})")
                else:
                    file_metadata = {
                        'name': DB_FILENAME,
                        'parents': [folder_id],
                        'mimeType': 'application/json'
                    }
                    self.service.files().create(
                        body=file_metadata,
                        media_body=media,
                        fields='id'
                    ).execute()
                    logger.info(f"✅ Database Created (Attempt {attempt+1})")
                
                return True

            except HttpError as e:
                logger.warning(f"⚠️ HTTP Error on save (Attempt {attempt+1}/{MAX_RETRIES}): {e}")
                time.sleep(RETRY_DELAY * (attempt + 1)) # Exponential Backoff
            except Exception as e:
                logger.error(f"❌ Unexpected Error on save: {e}")
                return False
        
        st.error("❌ Failed to save database after multiple attempts.")
        return False

    def load_db_from_drive(self, folder_id: str) -> List[Dict[str, Any]]:
        """
        Φορτώνει τη βάση με αυστηρούς ελέγχους και διαχείριση σφαλμάτων.
        """
        if not self.service:
            return []

        for attempt in range(MAX_RETRIES):
            try:
                query = f"name = '{DB_FILENAME}' and '{folder_id}' in parents and trashed = false"
                results = self.service.files().list(q=query, fields="files(id, size)").execute()
                files = results.get("files", [])

                if not files:
                    logger.warning("⚠️ Remote DB file not found.")
                    return []

                file_id = files[0]['id']
                file_size = int(files[0].get('size', 0))

                # Έλεγχος για κατεστραμμένο (άδειο) αρχείο
                if file_size == 0:
                    logger.error("❌ Remote DB file is empty (0 bytes).")
                    return []

                request = self.service.files().get_media(fileId=file_id)
                fh = io.BytesIO()
                downloader = MediaIoBaseDownload(fh, request)
                
                done = False
                while done is False:
                    status, done = downloader.next_chunk()
                    # Αν θέλαμε progress bar, θα έμπαινε εδώ
                
                fh.seek(0)
                data = json.load(fh)
                
                logger.info(f"✅ Successfully loaded {len(data)} items.")
                return data

            except json.JSONDecodeError:
                logger.error("❌ Corrupted JSON file in Drive.")
                return []
            except HttpError as e:
                logger.warning(f"⚠️ Load Error (Attempt {attempt+1}): {e}")
                time.sleep(RETRY_DELAY)
            except Exception as e:
                logger.error(f"❌ Unexpected Load Error: {e}")
                return []

        st.error("Could not load database. Check internet connection.")
        return []

# --- WRAPPER FUNCTIONS (Για συμβατότητα με τον υπόλοιπο κώδικα) ---
# Αυτές οι συναρτήσεις καλούν την κλάση, ώστε να μην χρειαστεί να αλλάξεις ΟΛΟ το main.py

_db_manager = DatabaseManager()

def save_db_to_drive(data: List[Dict[str, Any]], folder_id: str) -> bool:
    """Public wrapper for saving DB."""
    return _db_manager.save_db_to_drive(data, folder_id)

def load_db_from_drive(folder_id: str) -> List[Dict[str, Any]]:
    """Public wrapper for loading DB."""
    return _db_manager.load_db_from_drive(folder_id)

def get_drive_service():
    """Επιστρέφει το service instance."""
    return _db_manager.service