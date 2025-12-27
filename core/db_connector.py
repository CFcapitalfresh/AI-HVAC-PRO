import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

class DatabaseConnector:
    @staticmethod
    def _get_conn():
        return st.connection("gsheets", type=GSheetsConnection)

    @staticmethod
    def fetch_data(sheet_name, ttl=0):
        try:
            conn = DatabaseConnector._get_conn()
            df = conn.read(worksheet=sheet_name, ttl=ttl)
            return df.dropna(how="all")
        except:
            return pd.DataFrame()

    @staticmethod
    def append_data(sheet_name, row_data):
        """Προσθέτει νέα γραμμή στο Excel"""
        try:
            conn = DatabaseConnector._get_conn()
            existing_df = conn.read(worksheet=sheet_name, ttl=0).dropna(how="all")
            
            # Δημιουργία νέας γραμμής
            new_row = pd.DataFrame([row_data], columns=existing_df.columns)
            updated_df = pd.concat([existing_df, new_row], ignore_index=True)
            
            conn.update(worksheet=sheet_name, data=updated_df)
            return True
        except Exception as e:
            st.error(f"Save Error: {e}")
            return False

    @staticmethod
    def update_all_data(sheet_name, dataframe):
        """Ενημερώνει όλο το φύλλο (για edits/delete από το Admin Panel)"""
        try:
            conn = DatabaseConnector._get_conn()
            conn.update(worksheet=sheet_name, data=dataframe)
            return True
        except Exception as e:
            st.error(f"Update Error: {e}")
            return False