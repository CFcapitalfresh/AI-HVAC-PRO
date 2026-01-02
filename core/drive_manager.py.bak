"""
CORE MODULE: DRIVE MANAGER (Hybrid Stable + PDF Uploads)
--------------------------------------------------------
Handles direct API calls to Google Drive v3.
Features:
- Robust Auth
- JSON Persistence (Update logic)
- Binary Uploads (PDFs from User)
- NEW: File Renaming
- NEW: File Deletion
"""

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload
import io
import json
import logging
import streamlit as st
from core.config_loader import ConfigLoader

logger = logging.getLogger("Core.Drive")
SCOPES = ['https://www.googleapis.com/auth/drive']

class DriveManager:
    """Χειριστής Google Drive API."""

    def __init__(self):
        self.service = self._authenticate()
        # Ensure root_id is loaded only once and correctly, then cached in session_state
        if 'drive_root_folder_id' not in st.session_state:
            st.session_state['drive_root_folder_id'] = ConfigLoader.get_drive_folder_id()
        self._root_id = st.session_state['drive_root_folder_id']

    @property
    def root_id(self):
        return self._root_id

    def _authenticate(self):
        """Εσωτερική μέθοδος σύνδεσης."""
        creds_info = ConfigLoader.get_service_account_info()
        if not creds_info: 
            logger.critical("Drive Auth Failed: GCP Service Account secrets missing.")
            return None
        try:
            creds = service_account.Credentials.from_service_account_info(
                creds_info, scopes=SCOPES
            )
            return build('drive', 'v3', credentials=creds)
        except Exception as e:
            logger.critical(f"Drive Auth Failed: {e}", exc_info=True)
            return None

    def list_files_in_folder(self, folder_id):
        if not self.service: 
            logger.error("Drive service not initialized for list_files_in_folder.")
            return []
        query = f"'{folder_id}' in parents and trashed = false"
        try:
            results = self.service.files().list(
                q=query, fields="files(id, name, mimeType, webViewLink, parents)"
            ).execute()
            return results.get('files', [])
        except Exception as e:
            logger.error(f"List Files Error in folder {folder_id}: {e}", exc_info=True)
            return []

    def download_file_content(self, file_id):
        if not self.service: 
            logger.error("Drive service not initialized for download_file_content.")
            return None
        try:
            request = self.service.files().get_media(fileId=file_id)
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while done is False: status, done = downloader.next_chunk()
            fh.seek(0)
            return fh
        except Exception as e:
            logger.error(f"Download Error for file {file_id}: {e}", exc_info=True)
            return None

    def create_folder(self, name, parent_id):
        """Δημιουργεί φάκελο (με ασφάλεια)."""
        if not self.service: 
            logger.error("Drive service not initialized for create_folder.")
            return None
        query = f"name = '{name}' and '{parent_id}' in parents and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
        try:
            existing = self.service.files().list(q=query, fields="files(id)").execute()
            files = existing.get('files', [])
            if files: 
                logger.info(f"Folder '{name}' already exists in {parent_id}. ID: {files[0]['id']}")
                return files[0]['id']
            
            metadata = {'name': name, 'mimeType': 'application/vnd.google-apps.folder', 'parents': [parent_id]}
            folder = self.service.files().create(body=metadata, fields='id').execute()
            logger.info(f"Created folder '{name}' in {parent_id}. ID: {folder.get('id')}")
            return folder.get('id')
        except Exception as e:
            logger.error(f"Create Folder Error for '{name}' in {parent_id}: {e}", exc_info=True)
            return None

    def move_file(self, file_id, target_folder_id):
        """Μετακινεί αρχείο."""
        if not self.service: 
            logger.error("Drive service not initialized for move_file.")
            return False
        try:
            file = self.service.files().get(fileId=file_id, fields='parents').execute()
            prev_parents = ",".join(file.get('parents', []))
            self.service.files().update(
                fileId=file_id, addParents=target_folder_id, removeParents=prev_parents
            ).execute()
            logger.info(f"Moved file {file_id} to folder {target_folder_id}.")
            return True
        except Exception as e:
            logger.error(f"Move File Error for {file_id} to {target_folder_id}: {e}", exc_info=True)
            return False

    def rename_file(self, file_id, new_name):
        """ΝΕΟ: Μετονομάζει ένα αρχείο στο Google Drive."""
        if not self.service:
            logger.error("Drive service not initialized for rename_file.")
            return False
        try:
            body = {'name': new_name}
            self.service.files().update(fileId=file_id, body=body, fields='name').execute()
            logger.info(f"Renamed file {file_id} to '{new_name}'.")
            return True
        except Exception as e:
            logger.error(f"Rename File Error for {file_id} to '{new_name}': {e}", exc_info=True)
            return False

    def delete_file(self, file_id) -> bool: # NEW
        """Διαγράφει ένα αρχείο από το Google Drive."""
        if not self.service:
            logger.error("Drive service not initialized for delete_file.")
            return False
        try:
            self.service.files().delete(fileId=file_id).execute()
            logger.info(f"Deleted file {file_id} from Drive.")
            return True
        except Exception as e:
            logger.error(f"Delete File Error for {file_id}: {e}", exc_info=True)
            return False

    # --- PERSISTENCE & UPLOADS ---

    def find_file_by_name(self, filename, parent_id):
        """Βρίσκει αρχείο με όνομα (για persistence)."""
        if not self.service: return None
        query = f"name = '{filename}' and '{parent_id}' in parents and trashed = false"
        try:
            results = self.service.files().list(q=query, fields="files(id)").execute()
            files = results.get('files', [])
            return files[0]['id'] if files else None
        except Exception as e:
            logger.warning(f"Error finding file by name '{filename}' in {parent_id}: {e}")
            return None

    def upload_json_file(self, filename, json_data, parent_id):
        """Ανεβάζει/Ενημερώνει αρχείο JSON."""
        if not self.service: return None
        try:
            query = f"name = '{filename}' and '{parent_id}' in parents"
            existing = self.service.files().list(q=query, fields="files(id)").execute()
            files = existing.get('files', [])
            
            file_content = json.dumps(json_data, ensure_ascii=False, indent=2)
            media = MediaIoBaseUpload(io.BytesIO(file_content.encode('utf-8')), mimetype='application/json', resumable=True)

            if files:
                self.service.files().update(fileId=files[0]['id'], media_body=media).execute()
                logger.info(f"Updated JSON file '{filename}' (ID: {files[0]['id']}) in {parent_id}.")
                return files[0]['id']
            else:
                metadata = {'name': filename, 'parents': [parent_id]}
                new_file = self.service.files().create(body=metadata, media_body=media, fields='id').execute()
                logger.info(f"Created JSON file '{filename}' (ID: {new_file.get('id')}) in {parent_id}.")
                return new_file.get('id')
        except Exception as e:
            logger.error(f"JSON Upload Error for '{filename}' in {parent_id}: {e}", exc_info=True)
            return None

    # Modified upload_stream to accept mime_type for generic use (e.g., text/plain for logs)
    def upload_stream(self, file_obj, filename, parent_id, mime_type='application/pdf') -> str: # MODIFIED
        """Ανεβάζει ένα stream (π.χ. PDF, TXT) και επιστρέφει το file ID."""
        if not self.service: return None
        try:
            media = MediaIoBaseUpload(file_obj, mimetype=mime_type, resumable=True) # Use passed mime_type
            metadata = {'name': filename, 'parents': [parent_id]}
            new_file = self.service.files().create(body=metadata, media_body=media, fields='id, webViewLink').execute() # Get webViewLink
            logger.info(f"Uploaded stream '{filename}' (ID: {new_file.get('id')}) to {parent_id}.")
            # Return the webViewLink for direct access as requested
            return new_file.get('webViewLink')
        except Exception as e:
            logger.error(f"Upload Stream Error for '{filename}' to {parent_id}: {e}", exc_info=True)
            st.error(f"Upload Failed: {str(e)}")
            return None