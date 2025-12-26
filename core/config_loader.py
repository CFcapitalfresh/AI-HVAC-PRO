"""
CORE MODULE: CONFIG LOADER
--------------------------
Centralized configuration management.
Loads secrets safely for Drive, Sheets, and Gemini.
"""

import streamlit as st
import logging

logger = logging.getLogger("Core.Config")

class ConfigLoader:
    """Διαχειριστής Ρυθμίσεων & Μυστικών Κλειδιών."""

    @staticmethod
    def get_gemini_key():
        """Ανακτά το API Key για το AI."""
        try:
            return st.secrets["general"]["GEMINI_KEY"]
        except Exception:
            logger.error("Gemini Key not found in secrets.")
            return None

    @staticmethod
    def get_drive_folder_id():
        """Ανακτά το ID του κεντρικού φακέλου στο Drive."""
        try:
            return st.secrets["drive_config"]["folder_id"]
        except Exception:
            logger.error("Drive Folder ID not found.")
            return None

    @staticmethod
    def get_service_account_info():
        """Ανακτά τα credentials του Service Account."""
        try:
            # Μετατροπή σε dict γιατί το streamlit το δίνει ως AttrDict
            return dict(st.secrets["gcp_service_account"])
        except Exception:
            logger.critical("GCP Service Account secrets missing.")
            return None