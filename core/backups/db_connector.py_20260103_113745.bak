# -*- coding: utf-8 -*-
import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import sqlite3
import os
import logging
from core.drive_manager import DriveManager # NEW
from datetime import datetime # NEW
import io # NEW: For upload_spy_logs_to_drive stream

logger = logging.getLogger("Core.DB")

class DatabaseConnector:
    # Εσωτερικές αναφορές για συνδέσεις, ώστε να είναι Singleton-like
    _gsheets_conn = None
    _sqlite_conn = None
    _sqlite_db_path = "mastro_nek_local.db" # Προεπιλεγμένο όνομα για τοπική βάση
    _spy_logs_folder_id = None # NEW: Cache for SpyLogs folder ID in Drive

    @staticmethod
    def _get_gsheets_conn():
        """Παρέχει τη σύνδεση για Google Sheets."""
        if DatabaseConnector._gsheets_conn is None:
            try:
                DatabaseConnector._gsheets_conn = st.connection("gsheets", type=GSheetsConnection)
            except Exception as e:
                logger.error(f"Failed to establish GSheets connection: {e}")
                st.error(f"Αποτυχία σύνδεσης με Google Sheets: {e}")
                DatabaseConnector._gsheets_conn = False # Σημείωσε την αποτυχία
        return DatabaseConnector._gsheets_conn if DatabaseConnector._gsheets_conn else None

    @staticmethod
    def _get_sqlite_conn():
        """Παρέχει τη σύνδεση για SQLite."""
        if DatabaseConnector._sqlite_conn is None:
            try:
                DatabaseConnector._sqlite_conn = sqlite3.connect(DatabaseConnector._sqlite_db_path)
                logger.info(f"SQLite connection established to {DatabaseConnector._sqlite_db_path}")
            except Exception as e:
                logger.error(f"Failed to establish SQLite connection: {e}")
                st.error(f"Αποτυχία σύνδεσης με SQLite: {e}")
                DatabaseConnector._sqlite_conn = False # Σημείωσε την αποτυχία
        return DatabaseConnector._sqlite_conn if DatabaseConnector._sqlite_conn else None
    
    @staticmethod
    def _get_sqlite_cursor():
        """Παρέχει έναν cursor για την SQLite σύνδεση."""
        conn = DatabaseConnector._get_sqlite_conn()
        return conn.cursor() if conn else None

    @staticmethod
    def init_local_db():
        """
        Αρχικοποιεί την τοπική βάση δεδομένων SQLite, δημιουργώντας τους απαραίτητους πίνακες.
        Πρέπει να καλείται στην αρχή της εφαρμογής για να διασφαλίσει τη διαθεσιμότητα.
        """
        if DatabaseConnector._get_sqlite_conn():
            conn = DatabaseConnector._get_sqlite_conn()
            cursor = conn.cursor()
            try:
                # Δημιουργία πίνακα Users (αν δεν υπάρχει) - ΜΟΝΟ ΓΙΑ OFFLINE / LOCAL
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS Users (
                        created_at TEXT,
                        email TEXT PRIMARY KEY,
                        name TEXT,
                        password_hash TEXT,
                        role TEXT
                    )
                """)
                # Δημιουργία πίνακα Clients (αν δεν υπάρχει)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS Clients (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT,
                        phone TEXT,
                        address TEXT,
                        device TEXT,
                        last_service TEXT
                    )
                """)
                # Δημιουργία πίνακα Logs (αν δεν υπάρχει)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS Logs (
                        timestamp TEXT,
                        user_email TEXT,
                        action TEXT,
                        description TEXT
                    )
                """)
                # REMOVED: Δημιουργία πίνακα SpyLogs (έχει μεταφερθεί στο Google Drive)
                conn.commit()
                logger.info("Local SQLite database initialized successfully with Users, Clients, and Logs tables.")
                return True
            except Exception as e:
                logger.error(f"Failed to initialize SQLite tables: {e}")
                return False
        return False

    @staticmethod
    def fetch_data(sheet_name: str, ttl: int = 0, use_local_db: bool = False) -> pd.DataFrame:
        """
        Ανακτά δεδομένα από Google Sheets ή SQLite.
        Args:
            sheet_name (str): Το όνομα του φύλλου (για GSheets) ή του πίνακα (για SQLite).
            ttl (int): Time-to-live για caching (μόνο για GSheets).
            use_local_db (bool): Αν είναι True, χρησιμοποιεί την SQLite βάση.
        Returns:
            pd.DataFrame: Τα ανακτηθέντα δεδομένα.
        """
        if use_local_db:
            conn = DatabaseConnector._get_sqlite_conn()
            if not conn: return pd.DataFrame()
            try:
                # Προσοχή: Εδώ θα πρέπει να έχουμε προκαθορισμένους πίνακες
                df = pd.read_sql_query(f"SELECT * FROM {sheet_name}", conn)
                return df.dropna(how="all", axis=1) # Αφαιρεί στήλες που είναι όλο NaN
            except pd.io.sql.DatabaseError as e:
                logger.warning(f"SQLite table '{sheet_name}' not found or error: {e}")
                return pd.DataFrame()
            except Exception as e:
                logger.error(f"Error fetching data from SQLite for {sheet_name}: {e}")
                return pd.DataFrame()
        else:
            conn = DatabaseConnector._get_gsheets_conn()
            if not conn: return pd.DataFrame()
            try:
                df = conn.read(worksheet=sheet_name, ttl=ttl)
                return df.dropna(how="all")
            except Exception as e:
                logger.error(f"Error fetching data from GSheets for {sheet_name}: {e}")
                return pd.DataFrame()

    @staticmethod
    def append_data(sheet_name: str, row_data: list, use_local_db: bool = False) -> bool:
        """
        Προσθέτει νέα γραμμή σε Google Sheets ή SQLite.
        Args:
            sheet_name (str): Το όνομα του φύλλου/πίνακα.
            row_data (list): Η λίστα με τα δεδομένα της γραμμής.
            use_local_db (bool): Αν είναι True, χρησιμοποιεί την SQLite βάση.
        Returns:
            bool: True αν η προσθήκη ήταν επιτυχής, False αλλιώς.
        """
        if use_local_db:
            conn = DatabaseConnector._get_sqlite_conn()
            if not conn: return False
            try:
                # Ανακτά τα ονόματα των στηλών
                existing_df = DatabaseConnector.fetch_data(sheet_name, use_local_db=True)
                if existing_df.empty:
                    logger.warning(f"Cannot append to empty SQLite table '{sheet_name}' without column names.")
                    return False
                
                columns = ", ".join(existing_df.columns)
                placeholders = ", ".join(["?"] * len(row_data))
                
                cursor = conn.cursor()
                cursor.execute(f"INSERT INTO {sheet_name} ({columns}) VALUES ({placeholders})", tuple(row_data))
                conn.commit()
                logger.info(f"Appended data to SQLite table '{sheet_name}'.")
                return True
            except Exception as e:
                logger.error(f"SQLite append Error for {sheet_name}: {e}")
                return False
        else:
            conn = DatabaseConnector._get_gsheets_conn()
            if not conn: return False
            try:
                existing_df = conn.read(worksheet=sheet_name, ttl=0).dropna(how="all")
                
                # Δημιουργία νέας γραμμής - πρέπει να ταιριάζουν οι στήλες
                new_row = pd.DataFrame([row_data], columns=existing_df.columns)
                updated_df = pd.concat([existing_df, new_row], ignore_index=True)
                
                conn.update(worksheet=sheet_name, data=updated_df)
                logger.info(f"Appended data to GSheets worksheet '{sheet_name}'.")
                return True
            except Exception as e:
                logger.error(f"GSheets append Error for {sheet_name}: {e}")
                return False

    @staticmethod
    def update_all_data(sheet_name: str, dataframe: pd.DataFrame, use_local_db: bool = False) -> bool:
        """
        Ενημερώνει όλο το φύλλο/πίνακα με ένα νέο DataFrame.
        Χρησιμοποιείται για μαζικές ενημερώσεις (π.χ. από Admin Panel).
        Args:
            sheet_name (str): Το όνομα του φύλλου/πίνακα.
            dataframe (pd.DataFrame): Το DataFrame με τα ενημερωμένα δεδομένα.
            use_local_db (bool): Αν είναι True, χρησιμοποιεί την SQLite βάση.
        Returns:
            bool: True αν η ενημέρωση ήταν επιτυχής, False αλλιώς.
        """
        if use_local_db:
            conn = DatabaseConnector._get_sqlite_conn()
            if not conn: return False
            try:
                dataframe.to_sql(sheet_name, conn, if_exists='replace', index=False)
                conn.commit()
                logger.info(f"Updated all data in SQLite table '{sheet_name}'.")
                return True
            except Exception as e:
                logger.error(f"SQLite update Error for {sheet_name}: {e}")
                return False
        else:
            conn = DatabaseConnector._get_gsheets_conn()
            if not conn: return False
            try:
                conn.update(worksheet=sheet_name, data=dataframe)
                logger.info(f"Updated all data in GSheets worksheet '{sheet_name}'.")
                return True
            except Exception as e:
                logger.error(f"GSheets update Error for {sheet_name}: {e}")
                return False
                
    # REMOVED: Μέθοδοι για την διαχείριση των Spy Logs από SQLite

    # --- NEW: Google Drive SpyLogs Management ---
    @staticmethod
    def _get_spy_logs_folder_id() -> str:
        """Gets or creates the dedicated _SpyLogs folder in Google Drive."""
        if DatabaseConnector._spy_logs_folder_id:
            return DatabaseConnector._spy_logs_folder_id

        drive_manager = DriveManager()
        # Ensure root_id is properly loaded in DriveManager instance
        root_id = drive_manager.root_id 
        
        if not root_id:
            logger.error("Drive Root ID not found (from ConfigLoader) for SpyLogs folder creation.")
            return None
        
        try:
            folder_id = drive_manager.create_folder("_SpyLogs", root_id)
            DatabaseConnector._spy_logs_folder_id = folder_id # Cache it
            return folder_id
        except Exception as e:
            logger.error(f"Failed to create/get _SpyLogs folder in Drive: {e}", exc_info=True)
            return None

    @staticmethod
    def upload_spy_logs_to_drive(logs_content: list) -> str:
        """
        Uploads the current spy logs to a timestamped file in Google Drive.
        Args:
            logs_content (list): A list of log strings from st.session_state.spy_logs.
        Returns:
            str: The webViewLink of the uploaded file, or None on failure.
        """
        folder_id = DatabaseConnector._get_spy_logs_folder_id()
        if not folder_id:
            return None

        drive_manager = DriveManager()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"spy_logs_{timestamp}.txt"
        
        full_log_string = "\n".join(logs_content)
        log_stream = io.BytesIO(full_log_string.encode('utf-8'))

        try:
            # Use DriveManager's upload_stream for generic file upload, returns webViewLink
            link = drive_manager.upload_stream(log_stream, filename, folder_id, mime_type='text/plain')
            if link:
                logger.info(f"Spy logs uploaded to Drive: {filename} (Link: {link})")
                return link
            else:
                logger.error(f"Failed to upload spy logs to Drive: {filename}")
                return None
        except Exception as e:
            logger.error(f"Error uploading spy logs to Drive: {e}", exc_info=True)
            return None

    @staticmethod
    def clear_all_spy_logs_from_drive() -> bool:
        """
        Deletes all spy log files from the _SpyLogs folder in Google Drive.
        Returns:
            bool: True if deletion was successful, False otherwise.
        """
        folder_id = DatabaseConnector._get_spy_logs_folder_id()
        if not folder_id:
            logger.warning("Attempted to clear SpyLogs from Drive, but folder ID not found.")
            return False

        drive_manager = DriveManager()
        try:
            # List files in the _SpyLogs folder
            files = drive_manager.list_files_in_folder(folder_id)
            deleted_count = 0
            for file_item in files:
                # Ensure we only delete files created by the spy logger (spy_logs_*.txt)
                if file_item['name'].startswith("spy_logs_") and file_item['name'].endswith(".txt"):
                    if drive_manager.delete_file(file_item['id']):
                        # Also remove file from the internal cache of uploaded links if present
                        if 'last_uploaded_spy_log_link' in st.session_state and file_item['webViewLink'] == st.session_state['last_uploaded_spy_log_link']:
                            del st.session_state['last_uploaded_spy_log_link']
                        logger.info(f"Deleted SpyLog file from Drive: {file_item['name']} (ID: {file_item['id']})")
                        deleted_count += 1
                    else:
                        logger.warning(f"Failed to delete SpyLog file {file_item['name']} (ID: {file_item['id']}).")
            
            if deleted_count > 0:
                logger.info(f"Cleared {deleted_count} SpyLog files from Google Drive.")
                return True
            else:
                logger.info("No SpyLog files found to clear in Google Drive.")
                return True # Consider successful if no relevant files found to delete
        except Exception as e:
            logger.error(f"Error clearing spy logs from Drive: {e}", exc_info=True)
            return False