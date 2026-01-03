import json
import os
import logging
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.auth.transport.requests import Request
from google.auth.exceptions import RefreshError
from googleapiclient.http import MediaFileUpload

# Rule 3: Core Module
class AuthManager:
    def __init__(self):
        self.credentials = None
        self.service = None

    def authenticate(self):
        # Rule 4: Logging
        logger = logging.getLogger("AuthManager")
        try:
            self.credentials = service_account.Credentials.from_service_account_file(
                'credentials.json', scopes=['https://www.googleapis.com/auth/drive'])
            self.service = build('drive', 'v3', credentials=self.credentials)
            return self.service
        except HttpError as e:
            logger.error(f"Error authenticating: {e}")
            return None

    def get_service(self):
        return self.service

class DatabaseConnector:
    def __init__(self):
        self.db = None

    def init_local_db(self):
        # Rule 4: Logging
        logger = logging.getLogger("DatabaseConnector")
        try:
            import sqlite3
            self.db = sqlite3.connect('mastro_nek_local.db')
            return True
        except sqlite3.Error as e:
            logger.error(f"Error initializing local DB: {e}")
            return False

    def get_db(self):
        return self.db

class LanguagePack:
    def __init__(self):
        self.lang_pack = {}

    def load_lang_pack(self, lang):
        if lang == 'gr':
            with open('lang_gr.json', 'r') as f:
                self.lang_pack = json.load(f)
        elif lang == 'en':
            with open('lang_en.json', 'r') as f:
                self.lang_pack = json.load(f)

    def get_text(self, key, lang):
        if lang in self.lang_pack:
            return self.lang_pack[lang].get(key, '')
        else:
            return ''

def get_text(key, lang):
    lang_pack = LanguagePack()
    lang_pack.load_lang_pack(lang)
    return lang_pack.get_text(key, lang)

def setup_spy():
    # Rule 4: Logging
    logger = logging.getLogger("setup_spy")
    try:
        # Rule 3: Use Spy Logger
        import logging.handlers
        handler = logging.handlers.RotatingFileHandler('spy.log', maxBytes=1000000, backupCount=1)
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    except Exception as e:
        logger.error(f"Error setting up spy logger: {e}")

def sync_current_spy_logs_to_drive():
    # Rule 4: Logging
    logger = logging.getLogger("sync_current_spy_logs_to_drive")
    try:
        # Rule 3: Use Spy Logger
        import logging.handlers
        handler = logging.handlers.RotatingFileHandler('spy.log', maxBytes=1000000, backupCount=1)
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        # Rule 3: Use Drive API to upload logs
        from googleapiclient.discovery import build
        from googleapiclient.errors import HttpError
        from google.oauth2 import service_account
        from googleapiclient.http import MediaFileUpload
        credentials = service_account.Credentials.from_service_account_file(
            'credentials.json', scopes=['https://www.googleapis.com/auth/drive'])
        service = build('drive', 'v3', credentials=credentials)
        file_metadata = {'name': 'spy.log', 'mimeType': 'text/plain'}
        media = MediaFileUpload('spy.log', mimetype='text/plain')
        file = service.files().create(body=file_metadata,
                                      media_body=media,
                                      fields='id').execute()
    except HttpError as e:
        logger.error(f"Error syncing spy logs to drive: {e}")