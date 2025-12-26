"""
MODULE: Admin Dashboard
VERSION: 3.0.0 (TITANIUM)
DESCRIPTION: Κέντρο ελέγχου διαχειριστή. Περιλαμβάνει Logs, Users, Sync και Updates.
"""

import streamlit as st
import subprocess
import time
import logging
from typing import Any

logger = logging.getLogger("Module_Admin")

def _run_git_pull() -> str:
    """Εκτελεί git pull για updates."""
    try:
        result = subprocess.run(["git", "pull"], capture_output=True, text=True)
        return result.stdout
    except Exception as e:
        return f"Error: {e}"

def render_admin_panel(data_manager: Any, smart_lib_module: Any, drive_module: Any) -> None:
    """
    Κύρια συνάρτηση Admin Panel.
    Args:
        data_manager: Το DataManager class από το main.py
        smart_lib_module: Το module smart_library.py
        drive_module: Το module drive.py
    """
    st.title("⚙️ Admin Control Center")
    st.markdown("---")

    tab1, tab2, tab3, tab4 = st.tabs(["📊 System Logs", "👥 User Management", "☁️ Library Sync", "🔄 Maintenance"])

    # --- TAB 1: LOGS ---
    with tab1:
        st.subheader("Audit Logs (Security & Usage)")
        try:
            df_logs = data_manager.fetch_sheet_data("Logs")
            if not df_logs.empty:
                st.dataframe(df_logs.sort_values(by="timestamp", ascending=False if 'timestamp' in df_logs.columns else True), use_container_width=True)
            else:
                st.info("No logs found.")
        except Exception as e:
            st.error(f"Failed to load logs: {e}")

    # --- TAB 2: USERS ---
    with tab2:
        st.subheader("Registered Users")
        try:
            df_users = data_manager.fetch_sheet_data("Users")
            st.dataframe(df_users, use_container_width=True)
        except Exception as e:
            st.error(f"Failed to load users: {e}")

    # --- TAB 3: SYNC ---
    with tab3:
        st.subheader("Google Drive Synchronization")
        st.write("Χρησιμοποιήστε αυτό το εργαλείο αν η βιβλιοθήκη φαίνεται άδεια ή αν προσθέσατε νέα manuals.")
        
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"Τρέχοντα Αρχεία στη Μνήμη: **{len(st.session_state.get('library_cache', []))}**")
        
        with col2:
            if st.button("🚀 FORCE FULL SYNC", type="primary"):
                if not (smart_lib_module and drive_module):
                    st.error("Missing Modules (smart_library or drive). Cannot sync.")
                else:
                    try:
                        # 1. Load Config (Folder ID)
                        folder_id = drive_module.load_config()
                        if not folder_id:
                            st.error("Drive Config missing (Folder ID).")
                        else:
                            with st.spinner("⏳ Scanning Google Drive (This may take time)..."):
                                count = smart_lib_module.run_full_maintenance(folder_id)
                                st.success(f"Sync Complete! Indexed {count} files.")
                                time.sleep(2)
                                st.rerun()
                    except Exception as e:
                        st.error(f"Sync Failed: {e}")
                        logger.error(f"Manual Sync Error: {e}")

    # --- TAB 4: UPDATES ---
    with tab4:
        st.subheader("Software Updates")
        if st.button("Check GitHub for Updates"):
            with st.spinner("Pulling from repository..."):
                output = _run_git_pull()
                st.code(output)
                if "Already up to date" not in output:
                    st.warning("⚠️ New code pulled. Please restart the app.")