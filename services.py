import streamlit as st
import logging
from core.language_pack import get_text
from core.config_loader import ConfigLoader
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2 import service_account
from googleapiclient.http import MediaFileUpload

# Rule 3: Services Module
class DiagnosticsService:
    def __init__(self):
        self.api_key = None
        self.model = None
        self.ai_engine = None
        self.config_loader = ConfigLoader()

    def check_gemini_key(self):
        # Rule 4: Logging
        logger = logging.getLogger("DiagnosticsService")
        try:
            self.api_key = self.config_loader.get_config("api_key")
            if self.api_key:
                return {"status": "success", "message": "API key found"}
            else:
                return {"status": "error", "message": "API key not found"}
        except Exception as e:
            logger.error(f"Error checking API key: {e}")
            return {"status": "error", "message": str(e)}

    def test_ai_connection(self):
        # Rule 4: Logging
        logger = logging.getLogger("DiagnosticsService")
        try:
            # Rule 3: Use AI Engine for connection test
            self.ai_engine = build('drive', 'v3', developerKey=self.api_key)
            self.model = self.ai_engine
            return {"status": "success", "message": "Connection successful"}
        except HttpError as e:
            logger.error(f"Error connecting to AI: {e}")
            return {"status": "error", "message": str(e)}

    def test_ai_generation(self):
        # Rule 4: Logging
        logger = logging.getLogger("DiagnosticsService")
        try:
            # Rule 3: Use AI Engine for generation test
            file_metadata = {'name': 'test_file.txt', 'mimeType': 'text/plain'}
            media = MediaFileUpload('test_file.txt', mimetype='text/plain')
            file = self.ai_engine.files().create(body=file_metadata,
                                                media_body=media,
                                                fields='id').execute()
            return {"status": "success", "message": "Generation successful"}
        except HttpError as e:
            logger.error(f"Error generating with AI: {e}")
            return {"status": "error", "message": str(e)}

    def _get_best_model_name_internal(self):
        # Rule 3: Use AI Engine to get best model name
        if self.ai_engine:
            return self.ai_engine.model_name
        else:
            return None