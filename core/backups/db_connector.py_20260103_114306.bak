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
                return df
            except pd.io.sql.DatabaseError as e:
                logger.warning(f"SQLite table '{sheet_name}' not found or query error: {e}")
                return pd.DataFrame()
            except Exception as e:
                logger.error(f"Error fetching from local SQLite DB '{sheet_name}': {e}")
                return pd.DataFrame()
        else:
            conn = DatabaseConnector._get_gsheets_conn()
            if not conn: return pd.DataFrame()
            try:
                # Cache data for ttl seconds to avoid excessive API calls
                return conn.read(worksheet=sheet_name, ttl=ttl)
            except Exception as e:
                logger.error(f"Error fetching from Google Sheets '{sheet_name}': {e}")
                st.error(f"Αδυναμία φόρτωσης δεδομένων από το φύλλο '{sheet_name}'.")
                return pd.DataFrame()

    @staticmethod
    def append_data(sheet_name: str, data: list, use_local_db: bool = False) -> bool:
        """
        Προσθέτει μια νέα γραμμή δεδομένων στο τέλος ενός φύλλου/πίνακα.
        Args:
            sheet_name (str): Το όνομα του φύλλου (για GSheets) ή του πίνακα (για SQLite).
            data (list): Μια λίστα τιμών που θα προστεθούν.
            use_local_db (bool): Αν είναι True, χρησιμοποιεί την SQLite βάση.
        Returns:
            bool: True αν η προσθήκη ήταν επιτυχής, False διαφορετικά.
        """
        if use_local_db:
            conn = DatabaseConnector._get_sqlite_conn()
            if not conn: return False
            try:
                # Για SQLite, χρειαζόμαστε τα ονόματα των στηλών.
                # Αυτό είναι ένα απλοποιημένο παράδειγμα που υποθέτει τη σειρά.
                # Σε πιο σύνθετα σενάρια, θα περνούσαμε ένα dict και θα κάναμε insert.
                # Για "Users": created_at, email, name, password_hash, role
                # Για "Logs": timestamp, user_email, action, description
                if sheet_name == "Users" and len(data) == 5:
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO Users (created_at, email, name, password_hash, role) VALUES (?, ?, ?, ?, ?)", data)
                    conn.commit()
                    logger.info(f"Data appended to local SQLite table '{sheet_name}'.")
                    return True
                elif sheet_name == "Logs" and len(data) == 4:
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO Logs (timestamp, user_email, action, description) VALUES (?, ?, ?, ?)", data)
                    conn.commit()
                    logger.info(f"Data appended to local SQLite table '{sheet_name}'.")
                    return True
                else:
                    logger.error(f"Unsupported table '{sheet_name}' or data format for SQLite append.")
                    return False
            except Exception as e:
                logger.error(f"Error appending to local SQLite DB '{sheet_name}': {e}")
                return False
        else:
            conn = DatabaseConnector._get_gsheets_conn()
            if not conn: return False
            try:
                conn.append_dataframe(pd.DataFrame([data], columns=[]), worksheet=sheet_name)
                # Clear Streamlit's cache for this sheet
                if f"st_connection_gsheets__{sheet_name}" in st.session_state:
                    del st.session_state[f"st_connection_gsheets__{sheet_name}"]
                logger.info(f"Data appended to Google Sheets '{sheet_name}'.")
                return True
            except Exception as e:
                logger.error(f"Error appending to Google Sheets '{sheet_name}': {e}")
                st.error(f"Αδυναμία προσθήκης δεδομένων στο φύλλο '{sheet_name}'.")
                return False

    @staticmethod
    def update_all_data(sheet_name: str, df: pd.DataFrame, use_local_db: bool = False) -> bool:
        """
        Αντικαθιστά όλα τα δεδομένα σε ένα φύλλο/πίνακα με ένα νέο DataFrame.
        Args:
            sheet_name (str): Το όνομα του φύλλου (για GSheets) ή του πίνακα (για SQLite).
            df (pd.DataFrame): Το DataFrame με τα νέα δεδομένα.
            use_local_db (bool): Αν είναι True, χρησιμοποιεί την SQLite βάση.
        Returns:
            bool: True αν η ενημέρωση ήταν επιτυχής, False διαφορετικά.
        """
        if use_local_db:
            conn = DatabaseConnector._get_sqlite_conn()
            if not conn: return False
            try:
                # Drop existing table and recreate from DataFrame
                # This is a simple overwrite. For more complex updates, use SQL UPDATE/DELETE.
                df.to_sql(sheet_name, conn, if_exists='replace', index=False)
                conn.commit()
                logger.info(f"Local SQLite table '{sheet_name}' updated successfully.")
                return True
            except Exception as e:
                logger.error(f"Error updating local SQLite DB '{sheet_name}': {e}")
                return False
        else:
            conn = DatabaseConnector._get_gsheets_conn()
            if not conn: return False
            try:
                conn.update(dataframe=df, worksheet=sheet_name)
                # Clear Streamlit's cache for this sheet
                if f"st_connection_gsheets__{sheet_name}" in st.session_state:
                    del st.session_state[f"st_connection_gsheets__{sheet_name}"]
                logger.info(f"Google Sheets '{sheet_name}' updated successfully.")
                return True
            except Exception as e:
                logger.error(f"Error updating Google Sheets '{sheet_name}': {e}")
                st.error(f"Αδυναμία ενημέρωσης δεδομένων στο φύλλο '{sheet_name}'.")
                return False

    @staticmethod
    def upload_spy_logs_to_drive(logs_list: list) -> Optional[str]:
        """
        Δημιουργεί ή ενημερώνει ένα αρχείο logs στο Google Drive.
        Αρχικοποιεί το DriveManager εδώ για να διασφαλίσει ότι χρησιμοποιείται σωστά
        και για να διαχειριστεί το folder ID των logs.
        """
        try:
            drive_manager = DriveManager()
            if not drive_manager.service:
                logger.error("Drive service not available for Spy Logs upload.")
                return None

            # Εξασφάλιση ότι υπάρχει ο φάκελος "Spy_Logs"
            if DatabaseConnector._spy_logs_folder_id is None:
                # Αναζήτηση του φάκελου "Spy_Logs" στον root του DriveManager
                spy_logs_folder_name = "Spy_Logs"
                
                # Πρώτα προσπαθούμε να τον βρούμε
                query = f"name = '{spy_logs_folder_name}' and '{drive_manager.root_id}' in parents and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
                results = drive_manager.service.files().list(q=query, fields="files(id)").execute()
                files = results.get('files', [])
                
                if files:
                    DatabaseConnector._spy_logs_folder_id = files[0]['id']
                    logger.info(f"Found existing 'Spy_Logs' folder. ID: {DatabaseConnector._spy_logs_folder_id}")
                else:
                    # Αν δεν υπάρχει, τον δημιουργούμε
                    DatabaseConnector._spy_logs_folder_id = drive_manager.create_folder(spy_logs_folder_name, drive_manager.root_id)
                    if DatabaseConnector._spy_logs_folder_id:
                        logger.info(f"Created 'Spy_Logs' folder. ID: {DatabaseConnector._spy_logs_folder_id}")
                    else:
                        logger.error("Failed to create 'Spy_Logs' folder.")
                        return None
            
            if not DatabaseConnector._spy_logs_folder_id:
                logger.error("Spy Logs folder ID is still not set after creation/lookup.")
                return None

            log_content = "\n".join(logs_list)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_name = f"spy_log_{timestamp}.md" # Save as markdown for readability

            # Ανέβασμα του αρχείου logs
            uploaded_file_id = drive_manager.upload_text(log_content, file_name, DatabaseConnector._spy_logs_folder_id, mime_type='text/markdown')

            if uploaded_file_id:
                file_link = f"https://drive.google.com/file/d/{uploaded_file_id}/view?usp=drivesdk"
                logger.info(f"Spy Logs uploaded to Drive: {file_link}")
                return file_link
            else:
                logger.error("Failed to upload Spy Logs to Drive.")
                return None
        except Exception as e:
            logger.error(f"CRITICAL ERROR uploading Spy Logs to Drive: {e}", exc_info=True)
            return None