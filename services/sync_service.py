"""
SERVICE: SYNC SERVICE
---------------------
Scans Google Drive recursively and builds the library index.
"""
import streamlit as st
from core.drive_manager import DriveManager
from core.config_loader import ConfigLoader
import logging

logger = logging.getLogger("Service.Sync")

class SyncService:
    def __init__(self):
        self.drive = DriveManager()
        self.root_id = ConfigLoader.get_drive_folder_id()

    def scan_library(self):
        """Σαρώνει όλο το Drive και επιστρέφει λίστα αρχείων (Metadata)."""
        if not self.root_id: return []
        
        all_files = []
        folders_to_scan = [self.root_id]
        scanned_folders = set()

        # Iterative scanning (για να μην κολλήσει σε recursive loop)
        while folders_to_scan:
            current_id = folders_to_scan.pop(0)
            if current_id in scanned_folders: continue
            
            items = self.drive.list_files_in_folder(current_id)
            scanned_folders.add(current_id)

            for item in items:
                if item['mimeType'] == 'application/vnd.google-apps.folder':
                    folders_to_scan.append(item['id'])
                elif item['mimeType'] == 'application/pdf':
                    # Εξαγωγή Metadata από το όνομα
                    # Υποθέτουμε ότι ο Organizer τα έχει ονομάσει σωστά ή είναι σε φακέλους
                    meta = self._parse_metadata(item)
                    all_files.append(meta)
        
        return all_files

    def _parse_metadata(self, item):
        """Εξάγει πληροφορίες από το αρχείο."""
        # Εδώ θα μπορούσαμε να πάρουμε και το path των γονέων για να βρούμε μάρκα
        return {
            'file_id': item['id'],
            'name': item['name'],
            'link': item.get('webViewLink', ''),
            'mime': item['mimeType']
        }