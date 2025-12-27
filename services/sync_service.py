"""
SERVICE: SYNC SERVICE (STRICT PERSISTENCE)
------------------------------------------
Scans Google Drive and syncs index to Cloud.
THROWS ERROR if Cloud Upload fails.
"""
import streamlit as st
import json
import os
from core.drive_manager import DriveManager
from core.config_loader import ConfigLoader
import logging

logger = logging.getLogger("Service.Sync")
INDEX_FILENAME = "drive_index.json"

class SyncService:
    def __init__(self):
        self.drive = DriveManager()
        self.root_id = ConfigLoader.get_drive_folder_id()

    def scan_library(self):
        """Σαρώνει το Drive και σώζει ΤΟΠΙΚΑ και στο CLOUD (Αυστηρά)."""
        if not self.root_id: 
            raise Exception("Δεν βρέθηκε Folder ID στις ρυθμίσεις.")
        
        # 1. Σάρωση (Scanning)
        all_files = []
        folders_to_scan = [self.root_id]
        scanned_folders = set()

        # UI Progress Bar (γιατί μπορεί να αργήσει)
        progress_text = "Σάρωση φακέλων..."
        my_bar = st.progress(0, text=progress_text)
        
        while folders_to_scan:
            current_id = folders_to_scan.pop(0)
            if current_id in scanned_folders: continue
            
            items = self.drive.list_files_in_folder(current_id)
            scanned_folders.add(current_id)

            for item in items:
                if item['mimeType'] == 'application/vnd.google-apps.folder':
                    folders_to_scan.append(item['id'])
                elif item['mimeType'] == 'application/pdf':
                    meta = self._parse_metadata(item)
                    all_files.append(meta)
            
            # Μικρή ενημέρωση μπάρας (εικονική)
            if len(all_files) > 0:
                my_bar.progress(min(len(all_files) % 100, 90), text=f"Βρέθηκαν {len(all_files)} αρχεία...")
        
        my_bar.empty()

        # 2. Αποθήκευση Τοπικά (Backup)
        try:
            with open(INDEX_FILENAME, "w", encoding="utf-8") as f:
                json.dump(all_files, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"Local save failed (minor): {e}")

        # 3. Αποθήκευση στο Cloud (CRITICAL CHECK)
        # Εδώ κάνουμε τον αυστηρό έλεγχο
        cloud_file_id = self.drive.upload_json_file(INDEX_FILENAME, all_files, self.root_id)
        
        if not cloud_file_id:
            # ΑΝ ΑΠΟΤΥΧΕΙ, ΠΕΤΑΕΙ ERROR ΓΙΑ ΝΑ ΤΟ ΔΕΙΣ
            raise Exception("❌ Η αποθήκευση στο Cloud απέτυχε! Ελέγξτε αν το Bot είναι 'Editor' στο Google Drive.")

        return all_files

    def load_index(self):
        """Προσπαθεί να φορτώσει το Index (Cloud -> Local)."""
        
        # A. Πρώτα ψάχνουμε στο CLOUD (Πιο αξιόπιστο για persistence)
        if self.root_id:
            try:
                cloud_id = self.drive.find_file_by_name(INDEX_FILENAME, self.root_id)
                if cloud_id:
                    stream = self.drive.download_file_content(cloud_id)
                    if stream:
                        data = json.load(stream)
                        # Ενημερώνουμε και το τοπικό για cache
                        with open(INDEX_FILENAME, "w", encoding="utf-8") as f:
                            json.dump(data, f, ensure_ascii=False, indent=2)
                        return data
            except Exception as e:
                logger.error(f"Cloud load error: {e}")

        # B. Fallback σε Τοπικό Αρχείο
        if os.path.exists(INDEX_FILENAME):
            try:
                with open(INDEX_FILENAME, "r", encoding="utf-8") as f:
                    return json.load(f)
            except: pass
        
        return []

    def _parse_metadata(self, item):
        return {
            'file_id': item['id'],
            'name': item['name'],
            'link': item.get('webViewLink', ''),
            'mime': item['mimeType']
        }