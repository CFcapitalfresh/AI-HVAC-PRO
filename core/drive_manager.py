"""
CORE MODULE: DRIVE MANAGER (Low Level)
--------------------------------------
Handles direct API calls to Google Drive v3.
"""

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io
import logging
from core.config_loader import ConfigLoader

logger = logging.getLogger("Core.Drive")
SCOPES = ['https://www.googleapis.com/auth/drive']

class DriveManager:
    """Χειριστής Google Drive API."""

    def __init__(self):
        self.service = self._authenticate()

    def _authenticate(self):
        """Εσωτερική μέθοδος σύνδεσης."""
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
        """Επιστρέφει λίστα αρχείων μέσα σε φάκελο."""
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
        """Δημιουργεί φάκελο αν δεν υπάρχει."""
        if not self.service: return None

        # 1. Έλεγχος αν υπάρχει ήδη
        query = f"name = '{name}' and '{parent_id}' in parents and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
        try:
            existing = self.service.files().list(q=query, fields="files(id)").execute()
            files = existing.get('files', [])
            if files:
                return files[0]['id'] # Επιστροφή υπάρχοντος
            
            # 2. Δημιουργία νέου
            metadata = {
                'name': name,
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [parent_id]
            }
            folder = self.service.files().create(body=metadata, fields='id').execute()
            logger.info(f"Created folder: {name}")
            return folder.get('id')
        except Exception as e:
            logger.error(f"Create Folder Error: {e}")
            return None

    def move_file(self, file_id, target_folder_id):
        """Μετακινεί ένα αρχείο σε νέο φάκελο."""
        if not self.service: return False
        try:
            # Ανάκτηση τωρινών γονέων
            file = self.service.files().get(fileId=file_id, fields='parents').execute()
            previous_parents = ",".join(file.get('parents'))
            
            # Μετακίνηση
            self.service.files().update(
                fileId=file_id,
                addParents=target_folder_id,
                removeParents=previous_parents
            ).execute()
            return True
        except Exception as e:
            logger.error(f"Move File Error: {e}")
            return False

    def download_file_content(self, file_id):
        """Κατεβάζει το περιεχόμενο ενός αρχείου (π.χ. PDF) στη μνήμη."""
        if not self.service: return None
        try:
            request = self.service.files().get_media(fileId=file_id)
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while done is False:
                status, done = downloader.next_chunk()
            fh.seek(0)
            return fh
        except Exception as e:
            logger.error(f"Download Error: {e}")
            return None