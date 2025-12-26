"""
CORE MODULE: DATABASE CONNECTOR
-------------------------------
Handles low-level connections to Google Sheets via streamlit-gsheets.
Implements Singleton pattern principles for efficiency.
"""

import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import logging

# Setup Logger
logger = logging.getLogger("Core.DB")

class DatabaseConnector:
    """
    Διαχειριστής Συνδέσεων Βάσης Δεδομένων (Google Sheets).
    """
    
    @staticmethod
    def get_connection():
        """Returns the raw connection object."""
        try:
            return st.connection("gsheets", type=GSheetsConnection)
        except Exception as e:
            logger.critical(f"Database Connection Failed: {e}")
            return None

    @staticmethod
    def fetch_data(sheet_name: str, ttl: int = 0) -> pd.DataFrame:
        """
        Ανακτά δεδομένα από ένα συγκεκριμένο φύλλο.
        Args:
            sheet_name: Το όνομα του Tab (π.χ. 'Users', 'Clients')
            ttl: Time To Live cache (0 = πάντα φρέσκα)
        """
        conn = DatabaseConnector.get_connection()
        if not conn:
            return pd.DataFrame()

        try:
            df = conn.read(worksheet=sheet_name, ttl=ttl)
            # Καθαρισμός κενών γραμμών αν υπάρχουν (Robustness)
            df = df.dropna(how='all')
            return df
        except Exception as e:
            logger.error(f"Failed to fetch data from '{sheet_name}': {e}")
            return pd.DataFrame()

    @staticmethod
    def append_row(sheet_name: str, row_data: pd.DataFrame):
        """Προσθέτει μια γραμμή στο τέλος του φύλλου."""
        conn = DatabaseConnector.get_connection()
        if not conn: return False

        try:
            # 1. Διαβάζουμε τα υπάρχοντα
            existing_data = conn.read(worksheet=sheet_name, ttl=0)
            # 2. Ενώνουμε
            updated_data = pd.concat([existing_data, row_data], ignore_index=True)
            # 3. Ενημερώνουμε
            conn.update(worksheet=sheet_name, data=updated_data)
            return True
        except Exception as e:
            logger.error(f"Failed to append row to '{sheet_name}': {e}")
            return False