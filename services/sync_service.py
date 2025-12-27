"""
SERVICE: SYNC SERVICE (CLOUD ENHANCED)
--------------------------------------
Scans Google Drive and syncs index to Cloud for persistence.
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
        """Σαρώνει το Drive, φτιάχνει index και το σώζει ΤΟΠΙΚΑ και στο CLOUD."""
        if not self.root_id: return []
        
        # 1. Σάρωση (υπάρχων κώδικας)
        all_files = []
        folders_to_scan = [self.root_id]
        scanned_folders = set()

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
        
        # 2. Αποθήκευση Τοπικά (Backup)
        try:
            with open(INDEX_FILENAME, "w", encoding="utf-8") as f:
                json.dump(all_files, f, ensure_ascii=False, indent=2)
        except: pass

        # 3. Αποθήκευση στο Cloud (Persistence)
        try:
            self.drive.upload_json_file(INDEX_FILENAME, all_files, self.root_id)
        except Exception as e:
            logger.error(f"Cloud Save Failed: {e}")

        return all_files

    def load_index(self):
        """Προσπαθεί να φορτώσει το Index (Μνήμη -> Τοπικά -> Cloud)."""
        
        # A. Τοπικό Αρχείο
        if os.path.exists(INDEX_FILENAME):
            try:
                with open(INDEX_FILENAME, "r", encoding="utf-8") as f:
                    return json.load(f)
            except: pass
        
        # B. Αν δεν υπάρχει τοπικά, ψάξε στο Cloud (Drive)
        if self.root_id:
            cloud_id = self.drive.find_file_by_name(INDEX_FILENAME, self.root_id)
            if cloud_id:
                stream = self.drive.download_file_content(cloud_id)
                if stream:
                    try:
                        data = json.load(stream)
                        # Σώσε το και τοπικά για την επόμενη φορά
                        with open(INDEX_FILENAME, "w", encoding="utf-8") as f:
                            json.dump(data, f, ensure_ascii=False, indent=2)
                        return data
                    except: pass
        
        return []

    def _parse_metadata(self, item):
        return {
            'file_id': item['id'],
            'name': item['name'],
            'link': item.get('webViewLink', ''),
            'mime': item['mimeType']
        }