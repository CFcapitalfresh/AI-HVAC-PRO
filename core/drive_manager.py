"""
CORE MODULE: DRIVE MANAGER
--------------------------
Handles direct API calls to Google Drive v3.
Includes Upload/Update capabilities for Persistence.
"""

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload
import io
import json
import logging
from core.config_loader import ConfigLoader

logger = logging.getLogger("Core.Drive")
SCOPES = ['https://www.googleapis.com/auth/drive']

class DriveManager:
    def __init__(self):
        self.service = self._authenticate()

    def _authenticate(self):
        creds_info = ConfigLoader.get_service_account_info()
        if not creds_info: return None
        try:
            creds = service_account.Credentials.from_service_account_info(
                creds_info, scopes=SCOPES
            )
            return build('drive', 'v3', credentials=creds)
        except Exception as e:
            logger.critical(f"Drive Auth Failed: {e}")
            return None

    def list_files_in_folder(self, folder_id):
        if not self.service: return []
        query = f"'{folder_id}' in parents and trashed = false"
        try:
            results = self.service.files().list(
                q=query, fields="files(id, name, mimeType, webViewLink, parents)"
            ).execute()
            return results.get('files', [])
        except Exception as e:
            logger.error(f"List Files Error: {e}")
            return []

    def create_folder(self, name, parent_id):
        if not self.service: return None
        query = f"name = '{name}' and '{parent_id}' in parents and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
        try:
            existing = self.service.files().list(q=query, fields="files(id)").execute()
            files = existing.get('files', [])
            if files: return files[0]['id']
            
            metadata = {'name': name, 'mimeType': 'application/vnd.google-apps.folder', 'parents': [parent_id]}
            folder = self.service.files().create(body=metadata, fields='id').execute()
            return folder.get('id')
        except Exception as e:
            logger.error(f"Create Folder Error: {e}")
            return None

    def move_file(self, file_id, target_folder_id):
        if not self.service: return False
        try:
            file = self.service.files().get(fileId=file_id, fields='parents').execute()
            previous_parents = ",".join(file.get('parents'))
            self.service.files().update(
                fileId=file_id, addParents=target_folder_id, removeParents=previous_parents
            ).execute()
            return True
        except Exception as e:
            logger.error(f"Move File Error: {e}")
            return False

    def download_file_content(self, file_id):
        if not self.service: return None
        try:
            request = self.service.files().get_media(fileId=file_id)
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while done is False: status, done = downloader.next_chunk()
            fh.seek(0)
            return fh
        except Exception as e:
            logger.error(f"Download Error: {e}")
            return None

    # --- ΝΕΕΣ ΛΕΙΤΟΥΡΓΙΕΣ ΓΙΑ CLOUD PERSISTENCE ---
    def upload_json_file(self, filename, json_data, parent_id):
        """Ανεβάζει (ή ενημερώνει) ένα αρχείο JSON στο Drive."""
        if not self.service: return None
        try:
            # 1. Έλεγχος αν υπάρχει ήδη το αρχείο
            query = f"name = '{filename}' and '{parent_id}' in parents and trashed = false"
            existing = self.service.files().list(q=query, fields="files(id)").execute()
            files = existing.get('files', [])
            
            # Ετοιμασία δεδομένων
            file_content = json.dumps(json_data, ensure_ascii=False, indent=2)
            media = MediaIoBaseUpload(io.BytesIO(file_content.encode('utf-8')), mimetype='application/json')

            if files:
                # UPDATE
                file_id = files[0]['id']
                self.service.files().update(fileId=file_id, media_body=media).execute()
                return file_id
            else:
                # CREATE
                metadata = {'name': filename, 'parents': [parent_id]}
                new_file = self.service.files().create(body=metadata, media_body=media, fields='id').execute()
                return new_file.get('id')
        except Exception as e:
            logger.error(f"Upload JSON Error: {e}")
            return None

    def find_file_by_name(self, filename, parent_id):
        """Βρίσκει ID αρχείου βάσει ονόματος."""
        if not self.service: return None
        query = f"name = '{filename}' and '{parent_id}' in parents and trashed = false"
        try:
            results = self.service.files().list(q=query, fields="files(id)").execute()
            files = results.get('files', [])
            return files[0]['id'] if files else None
        except: return None