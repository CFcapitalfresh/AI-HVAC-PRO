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
            try: # Rule 4: Error Handling
                DatabaseConnector._gsheets_conn = st.connection("gsheets", type=GSheetsConnection)
                logger.info("GSheets connection established.")
            except Exception as e:
                logger.error(f"Failed to establish GSheets connection: {e}", exc_info=True) # Rule 4
                # st.error(f"Αποτυχία σύνδεσης με Google Sheets: {e}") # Do not show error directly in core, let UI handle it.
                DatabaseConnector._gsheets_conn = False # Σημείωσε την αποτυχία
        return DatabaseConnector._gsheets_conn if DatabaseConnector._gsheets_conn else None

    @staticmethod
    def _get_sqlite_conn():
        """Παρέχει τη σύνδεση για SQLite."""
        if DatabaseConnector._sqlite_conn is None:
            try: # Rule 4: Error Handling
                DatabaseConnector._sqlite_conn = sqlite3.connect(DatabaseConnector._sqlite_db_path)
                logger.info(f"SQLite connection established to {DatabaseConnector._sqlite_db_path}")
            except Exception as e:
                logger.error(f"Failed to establish SQLite connection: {e}", exc_info=True) # Rule 4
                # st.error(f"Αποτυχία σύνδεσης με SQLite: {e}") # Do not show error directly in core, let UI handle it.
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
            try: # Rule 4: Error Handling
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
                conn.commit()
                logger.info("Local SQLite database initialized successfully with Users, Clients, and Logs tables.")
                return True
            except sqlite3.Error as e: # Rule 4: Specific DB error handling
                logger.error(f"SQLite error during table initialization: {e}", exc_info=True)
                return False
            except Exception as e: # Rule 4: General error handling
                logger.error(f"Failed to initialize SQLite tables: {e}", exc_info=True)
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
            try: # Rule 4: Error Handling
                df = pd.read_sql_query(f"SELECT * FROM {sheet_name}", conn)
                return df
            except pd.io.sql.DatabaseError as e: # Rule 4: Specific DB error
                logger.error(f"SQLite query error for table '{sheet_name}': {e}", exc_info=True)
                return pd.DataFrame()
            except Exception as e: # Rule 4: General error
                logger.error(f"Failed to fetch data from SQLite table '{sheet_name}': {e}", exc_info=True)
                return pd.DataFrame()
        else: # Try GSheets
            conn = DatabaseConnector._get_gsheets_conn()
            if not conn: return pd.DataFrame() # No connection, return empty
            try: # Rule 4: Error Handling
                # Caching in Streamlit's @st.cache_data for performance
                @st.cache_data(ttl=ttl, show_spinner=False)
                def _fetch_gsheets_data(sheet: str) -> pd.DataFrame:
                    df = conn.read(worksheet=sheet, usecols=list(range(10)), ttl=ttl)
                    df.columns = df.columns.str.lower() # Normalize column names
                    return df
                
                df = _fetch_gsheets_data(sheet_name)
                return df
            except Exception as e:
                logger.error(f"Failed to fetch data from GSheets '{sheet_name}': {e}", exc_info=True) # Rule 4
                return pd.DataFrame()

    @staticmethod
    def append_data(sheet_name: str, data: list, use_local_db: bool = False) -> bool:
        """
        Προσθέτει μια νέα γραμμή δεδομένων σε ένα φύλλο Google Sheets ή πίνακα SQLite.
        Args:
            sheet_name (str): Το όνομα του φύλλου/πίνακα.
            data (list): Η λίστα των τιμών για τη νέα γραμμή.
            use_local_db (bool): Αν είναι True, προσθέτει στην SQLite βάση.
        Returns:
            bool: True αν η προσθήκη ήταν επιτυχής, αλλιώς False.
        """
        if use_local_db:
            conn = DatabaseConnector._get_sqlite_conn()
            if not conn: return False
            cursor = conn.cursor()
            try: # Rule 4: Error Handling
                # Fetch column names from the table
                cursor.execute(f"PRAGMA table_info({sheet_name})")
                cols_info = cursor.fetchall()
                col_names = [info[1] for info in cols_info]
                
                if not col_names:
                    logger.error(f"No columns found for SQLite table '{sheet_name}'. Cannot append data.")
                    return False

                # Generate placeholders for the SQL query
                placeholders = ', '.join(['?' for _ in data])
                query = f"INSERT INTO {sheet_name} ({', '.join(col_names[:len(data)])}) VALUES ({placeholders})"
                
                cursor.execute(query, data)
                conn.commit()
                logger.info(f"Appended data to SQLite table '{sheet_name}'.")
                return True
            except sqlite3.Error as e:
                logger.error(f"SQLite error appending data to '{sheet_name}': {e}", exc_info=True)
                return False
            except Exception as e:
                logger.error(f"Failed to append data to SQLite table '{sheet_name}': {e}", exc_info=True)
                return False
        else: # Try GSheets
            conn = DatabaseConnector._get_gsheets_conn()
            if not conn: return False
            try: # Rule 4: Error Handling
                conn.append_dataframe(pd.DataFrame([data]), worksheet=sheet_name)
                logger.info(f"Appended data to GSheets '{sheet_name}'.")
                # Invalidate cache for this sheet
                st.cache_data.clear() # Clear all caches for simplicity for now, consider granular clear for performance.
                return True
            except Exception as e:
                logger.error(f"Failed to append data to GSheets '{sheet_name}': {e}", exc_info=True) # Rule 4
                return False

    @staticmethod
    def update_all_data(sheet_name: str, df: pd.DataFrame, use_local_db: bool = False) -> bool:
        """
        Ανανεώνει όλα τα δεδομένα σε ένα φύλλο Google Sheets ή πίνακα SQLite με ένα DataFrame.
        Args:
            sheet_name (str): Το όνομα του φύλλου/πίνακα.
            df (pd.DataFrame): Το DataFrame με τα νέα δεδομένα.
            use_local_db (bool): Αν είναι True, ενημερώνει την SQLite βάση.
        Returns:
            bool: True αν η ενημέρωση ήταν επιτυχής, αλλιώς False.
        """
        if use_local_db:
            conn = DatabaseConnector._get_sqlite_conn()
            if not conn: return False
            cursor = conn.cursor()
            try: # Rule 4: Error Handling
                # Delete existing data and insert new. This is simpler for full DataFrame updates.
                cursor.execute(f"DELETE FROM {sheet_name}")
                
                # Convert DataFrame to records for insertion
                # Ensure column names match
                cols = ", ".join(df.columns)
                placeholders = ", ".join("?" * len(df.columns))
                insert_query = f"INSERT INTO {sheet_name} ({cols}) VALUES ({placeholders})"

                for _, row in df.iterrows():
                    cursor.execute(insert_query, tuple(row))
                
                conn.commit()
                logger.info(f"Updated all data in SQLite table '{sheet_name}'.")
                return True
            except sqlite3.Error as e:
                logger.error(f"SQLite error updating all data in '{sheet_name}': {e}", exc_info=True)
                return False
            except Exception as e:
                logger.error(f"Failed to update all data in SQLite table '{sheet_name}': {e}", exc_info=True)
                return False
        else: # Try GSheets
            conn = DatabaseConnector._get_gsheets_conn()
            if not conn: return False
            try: # Rule 4: Error Handling
                conn.clear(worksheet=sheet_name) # Clear existing data
                conn.append_dataframe(df, worksheet=sheet_name) # Write new data
                logger.info(f"Updated all data in GSheets '{sheet_name}'.")
                # Invalidate cache for this sheet
                st.cache_data.clear() # Clear all caches for simplicity for now, consider granular clear for performance.
                return True
            except Exception as e:
                logger.error(f"Failed to update all data in GSheets '{sheet_name}': {e}", exc_info=True) # Rule 4
                return False

    @staticmethod
    def upload_spy_logs_to_drive(logs_list: list) -> Optional[str]: # Rule 7
        """
        Μεταφορτώνει τα τρέχοντα logs του Spy Logger στο Google Drive ως αρχείο κειμένου.
        Δημιουργεί φάκελο 'SpyLogs' αν δεν υπάρχει.
        """
        try: # Rule 4: Error Handling
            drive_manager = DriveManager() # Rule 3
            root_id = drive_manager.root_id # Rule 7

            if not root_id:
                logger.error("Drive root folder ID is missing. Cannot upload spy logs.")
                return None

            # Δημιουργία ή εύρεση του φακέλου "SpyLogs"
            spy_logs_folder_id = drive_manager.create_folder("SpyLogs", root_id) # Rule 7
            if not spy_logs_folder_id:
                logger.error("Failed to create/find 'SpyLogs' folder in Drive. Cannot upload logs.")
                return None

            # Ετοιμασία του αρχείου log
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            log_filename = f"SpyLog_{timestamp}.md"
            log_content = "\n".join(logs_list)

            # Μεταφόρτωση στο Drive
            file_id = drive_manager.upload_text_file(log_filename, log_content, spy_logs_folder_id) # Rule 7
            if file_id:
                logger.info(f"Spy logs uploaded to Drive: {log_filename}")
                return drive_manager.get_file_link(file_id) # Rule 7
            else:
                logger.error("Failed to upload spy logs to Drive.")
                return None
        except Exception as e:
            logger.error(f"Error uploading spy logs to Drive: {e}", exc_info=True) # Rule 4
            return None