import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

class DatabaseConnector:
    """
    Κλάση για τη διαχείριση της σύνδεσης με το Google Sheets.
    """

    @staticmethod
    def _get_conn():
        """Εσωτερική μέθοδος για τη σύνδεση."""
        return st.connection("gsheets", type=GSheetsConnection)

    @staticmethod
    def fetch_data(sheet_name, ttl=0):
        """
        Διαβάζει δεδομένα από ένα συγκεκριμένο φύλλο.
        ttl=0 σημαίνει ότι δεν κρατάει μνήμη cache, διαβάζει πάντα φρέσκα.
        """
        try:
            conn = DatabaseConnector._get_conn()
            # Διαβάζουμε το φύλλο
            df = conn.read(worksheet=sheet_name, ttl=ttl)
            # Καθαρισμός από κενές γραμμές που μπορεί να έχουν μείνει
            df = df.dropna(how="all")
            return df
        except Exception as e:
            # Αν δεν βρεθεί το φύλλο ή υπάρχει λάθος, επιστρέφει άδειο πίνακα
            # st.error(f"DB Read Error ({sheet_name}): {e}") # (Προαιρετικό για debugging)
            return pd.DataFrame()

    @staticmethod
    def append_data(sheet_name, row_data):
        """
        Προσθέτει μια νέα γραμμή στο τέλος του φύλλου.
        Το row_data πρέπει να είναι λίστα [val1, val2, ...].
        """
        try:
            conn = DatabaseConnector._get_conn()
            
            # 1. Διαβάζουμε τα υπάρχοντα δεδομένα
            existing_df = conn.read(worksheet=sheet_name, ttl=0)
            existing_df = existing_df.dropna(how="all")
            
            # 2. Ελέγχουμε αν τα στοιχεία ταιριάζουν με τις στήλες
            if len(row_data) != len(existing_df.columns):
                st.error(f"Mismatch: Data has {len(row_data)} items, Sheet has {len(existing_df.columns)} columns.")
                return False
            
            # 3. Δημιουργούμε τη νέα γραμμή
            new_row = pd.DataFrame([row_data], columns=existing_df.columns)
            
            # 4. Ενώνουμε τα παλιά με τη νέα γραμμή
            updated_df = pd.concat([existing_df, new_row], ignore_index=True)
            
            # 5. Ενημερώνουμε το Google Sheet
            conn.update(worksheet=sheet_name, data=updated_df)
            return True
            
        except Exception as e:
            st.error(f"DB Write Error ({sheet_name}): {str(e)}")
            return False